"""Módulo de analítica de Panadería Zulca (Parcial Nº 2, M1).

Lee la base MySQL del sistema, transforma los datos con pandas, calcula
indicadores con numpy y genera gráficos con matplotlib (PNG).

Cada gráfico responde una pregunta de negocio:
  1. Barras agrupadas  - ¿Cómo vendió cada categoría mes a mes?
  2. Dona              - ¿Qué productos concentran la facturación?
  3. Líneas            - ¿La facturación diaria crece o cae? (media móvil + tendencia)
  4. Mapa de calor     - ¿Qué días y horas concentran la operación?
  5. Tablero (extra)   - Los cuatro anteriores y los indicadores clave en una sola imagen.

Uso (desde la carpeta panaderia_web, con el entorno virtual activado):
    python analitica/analitica.py
    python analitica/analitica.py --desde 2026-09-01 --hasta 2026-11-30
    python analitica/analitica.py --categoria Panificados --top 5

La conexión usa las mismas variables que el sistema (DB_HOST, DB_PORT) y, si no
están definidas, los mismos valores por defecto que settings.py.
"""
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use('Agg')  # genera imágenes sin abrir ventanas

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.patches  # noqa: E402,F401
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

# Argentina no usa horario de verano: la hora local es siempre UTC-3.
# La base guarda las fechas en UTC (USE_TZ = True en Django).
DESFASE_ARGENTINA = pd.Timedelta(hours=-3)

DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
COLORES = ['#7b4a2a', '#d39a3a', '#5b7f45', '#a8483a', '#4f7896', '#9c7bb0', '#c9b27c', '#6b6b6b']
MARRON = '#3e2a1e'
GRIS = '#8a8a8a'


# ---------------------------------------------------------------------------
# 1. Lectura de datos (SQL solo trae filas; el análisis lo hace pandas)
# ---------------------------------------------------------------------------

SQL_LINEAS = """
    SELECT 'Mostrador' AS origen, v.id_venta AS operacion, v.fecha_hora AS fecha,
           p.nombre AS producto, c.nombre AS categoria, dv.cantidad AS cantidad, dv.subtotal AS importe
    FROM detalle_venta dv
    JOIN venta v ON v.id_venta = dv.venta_id_venta
    JOIN producto p ON p.id_producto = dv.producto_id_producto
    JOIN categoria c ON c.id_categoria = p.categoria_idcategoria
    WHERE v.estado = 'Confirmada' AND v.fecha_hora >= %s AND v.fecha_hora < %s
    UNION ALL
    SELECT 'Encargo', e.id_encargo, e.fecha_entrega_real,
           p.nombre, c.nombre, de.cantidad, de.subtotal
    FROM detalle_encargo de
    JOIN encargo e ON e.id_encargo = de.encargo_id_encargo
    JOIN producto p ON p.id_producto = de.producto_id_producto
    JOIN categoria c ON c.id_categoria = p.categoria_idcategoria
    WHERE e.estado = 'Entregado' AND e.fecha_entrega_real >= %s AND e.fecha_entrega_real < %s
"""

SQL_OPERACIONES = """
    SELECT 'Venta' AS tipo, fecha_hora AS fecha FROM venta
    WHERE estado = 'Confirmada' AND fecha_hora >= %s AND fecha_hora < %s
    UNION ALL
    SELECT 'Encargo', fecha_hora_registro FROM encargo
    WHERE fecha_hora_registro >= %s AND fecha_hora_registro < %s
"""


def conectar():
    """Conexión con el conector nativo de MySQL que ya usa Django (mysqlclient)."""
    import MySQLdb

    return MySQLdb.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', '3307')),
        user=os.environ.get('DB_USER', 'root'),
        passwd=os.environ.get('DB_PASSWORD', 'root'),
        db=os.environ.get('DB_NAME', 'panaderia'),
        charset='utf8mb4',
    )


def consultar(conexion, sql, parametros):
    """Ejecuta la consulta y devuelve un DataFrame con los nombres de columna."""
    cursor = conexion.cursor()
    cursor.execute(sql, parametros)
    columnas = [d[0] for d in cursor.description]
    filas = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(list(filas), columns=columnas)


def a_hora_local(serie):
    return pd.to_datetime(serie) + DESFASE_ARGENTINA


def leer_datos(conexion, desde, hasta):
    """Trae las líneas vendidas y las operaciones del período (fechas en hora Argentina)."""
    # Límites del período en UTC: [desde 00:00, hasta+1 00:00) hora Argentina.
    inicio = datetime.combine(desde, datetime.min.time()) - DESFASE_ARGENTINA
    fin = datetime.combine(hasta + timedelta(days=1), datetime.min.time()) - DESFASE_ARGENTINA
    lineas = consultar(conexion, SQL_LINEAS, (inicio, fin, inicio, fin))
    operaciones = consultar(conexion, SQL_OPERACIONES, (inicio, fin, inicio, fin))
    if not lineas.empty:
        lineas['fecha'] = a_hora_local(lineas['fecha'])
        lineas['cantidad'] = lineas['cantidad'].astype(int)
        lineas['importe'] = lineas['importe'].astype(float)
    if not operaciones.empty:
        operaciones['fecha'] = a_hora_local(operaciones['fecha'])
    return lineas, operaciones


# ---------------------------------------------------------------------------
# 2. Indicadores con numpy
# ---------------------------------------------------------------------------

def indicadores(lineas, desde, hasta):
    """Calcula los indicadores clave del período."""
    tickets = lineas[lineas['origen'] == 'Mostrador'].groupby('operacion')['importe'].sum().to_numpy()
    diaria = facturacion_diaria(lineas, desde, hasta)
    valores = diaria.to_numpy()
    por_producto = lineas.groupby('producto')['importe'].sum().sort_values(ascending=False)
    facturacion = float(np.sum(lineas['importe'].to_numpy()))
    resultado = {
        'facturacion': facturacion,
        'ventas': int(tickets.size),
        'encargos': int(lineas.loc[lineas['origen'] == 'Encargo', 'operacion'].nunique()),
        'ticket_promedio': float(np.mean(tickets)) if tickets.size else 0.0,
        'ticket_mediana': float(np.median(tickets)) if tickets.size else 0.0,
        'ticket_p90': float(np.percentile(tickets, 90)) if tickets.size else 0.0,
        'ticket_desvio': float(np.std(tickets, ddof=1)) if tickets.size > 1 else 0.0,
        'diaria_promedio': float(np.mean(valores)) if valores.size else 0.0,
        'producto_lider': por_producto.index[0] if not por_producto.empty else '-',
        'producto_lider_pct': float(por_producto.iloc[0] / facturacion * 100) if facturacion else 0.0,
    }
    resultado['operaciones'] = resultado['ventas'] + resultado['encargos']
    # Ventas inusuales: más de 3 desvíos sobre el promedio (misma idea que la alerta del sistema).
    limite = resultado['ticket_promedio'] + 3 * resultado['ticket_desvio']
    resultado['limite_inusual'] = limite
    resultado['ventas_inusuales'] = int(np.sum(tickets > limite)) if tickets.size > 1 else 0
    # Crecimiento: últimos 30 días contra los 30 anteriores.
    if valores.size >= 60:
        ultimos, anteriores = np.sum(valores[-30:]), np.sum(valores[-60:-30])
        resultado['crecimiento'] = float((ultimos - anteriores) / anteriores * 100) if anteriores else None
    else:
        resultado['crecimiento'] = None
    return resultado


def facturacion_diaria(lineas, desde, hasta):
    """Serie diaria de facturación con todos los días del período (0 si no hubo ventas)."""
    dias = pd.date_range(desde, hasta, freq='D')
    serie = lineas.set_index('fecha')['importe'].resample('D').sum()
    serie.index = serie.index.normalize()
    return serie.reindex(dias, fill_value=0.0)


def moneda(valor):
    return f'${valor:,.0f}'


# ---------------------------------------------------------------------------
# 3. Gráficos (cada función dibuja sobre un eje, así se reusan en el tablero)
# ---------------------------------------------------------------------------

# Cada gráfico: archivo, título, pregunta de negocio que responde y tipo de gráfico.
GRAFICOS = [
    ('1_barras_categorias.png', 'Unidades vendidas por categoría y mes',
     '¿Cómo se vendió cada categoría de productos mes a mes?', 'Barras agrupadas'),
    ('2_dona_productos.png', 'Participación en la facturación',
     '¿Qué productos concentran la mayor parte de lo facturado?', 'Dona'),
    ('3_lineas_tendencia.png', 'Evolución de la facturación diaria',
     '¿La facturación crece o cae? ¿Qué día fue el pico?', 'Línea con tendencia'),
    ('4_mapa_calor.png', 'Operaciones por día y hora',
     '¿En qué días y horarios se concentran las ventas y los encargos?', 'Mapa de calor'),
]
DIAS_LARGOS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
CAJA = {'boxstyle': 'round,pad=0.35', 'facecolor': 'white', 'edgecolor': MARRON, 'linewidth': 1}


def titular(ax, titulo, pregunta=None):
    """Título del gráfico y, debajo, la pregunta de negocio que responde."""
    ax.set_title(titulo, fontsize=12, fontweight='bold', color=MARRON, loc='left', pad=24 if pregunta else 10)
    if pregunta:
        ax.text(0, 1.025, pregunta, transform=ax.transAxes, fontsize=9, color=GRIS, va='bottom')


def estilo_eje(ax, titulo, pregunta=None):
    titular(ax, titulo, pregunta)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(colors='#444444', labelsize=9)


def grafico_barras_categorias(ax, lineas, compacto=False):
    """1. Barras agrupadas: unidades vendidas por categoría y mes."""
    datos = lineas.assign(mes=lineas['fecha'].dt.to_period('M'))
    tabla = datos.pivot_table(index='mes', columns='categoria', values='cantidad', aggfunc='sum', fill_value=0)
    tabla = tabla[tabla.sum().sort_values(ascending=False).index]  # categorías de mayor a menor
    meses = [f'{MESES[p.month - 1]} {p.year}' for p in tabla.index]
    x = np.arange(len(tabla.index))
    ancho = 0.8 / max(len(tabla.columns), 1)
    for i, categoria in enumerate(tabla.columns):
        ax.bar(x + i * ancho - 0.4 + ancho / 2, tabla[categoria], ancho, label=categoria,
               color=COLORES[i % len(COLORES)])
    ax.set_xticks(x, meses)
    ax.set_ylabel('Unidades vendidas')
    ax.set_ylim(top=tabla.to_numpy().max() * 1.15 if tabla.size else 1)
    ax.grid(axis='y', alpha=0.3)
    ax.legend(fontsize=8, frameon=False, ncol=1 if compacto else min(len(tabla.columns), 4))
    estilo_eje(ax, GRAFICOS[0][1], None if compacto else GRAFICOS[0][2])


def grafico_dona_productos(ax, lineas, top, compacto=False):
    """2. Dona: participación de cada producto en la facturación."""
    por_producto = lineas.groupby('producto')['importe'].sum().sort_values(ascending=False)
    principales = por_producto.head(top)
    resto = por_producto.iloc[top:].sum()
    if resto > 0:
        principales = pd.concat([principales, pd.Series({'Otros': resto})])
    colores = COLORES[:len(principales) - (1 if resto > 0 else 0)] + (['#cfcfcf'] if resto > 0 else [])
    total = principales.sum()
    cunas, _, porcentajes = ax.pie(
        principales.to_numpy(), colors=colores, startangle=90, counterclock=False,
        autopct=lambda p: f'{p:.1f}%' if p >= 4 else '', pctdistance=0.79,
        wedgeprops={'width': 0.42, 'edgecolor': 'white'}, textprops={'fontsize': 8},
    )
    for t in porcentajes:
        t.set_color('white')
        t.set_fontweight('bold')
    # Los nombres van en la leyenda para que no se encimen las porciones chicas.
    etiquetas = [f'{nombre} ({valor / total * 100:.1f}%)' for nombre, valor in principales.items()]
    ax.legend(cunas, etiquetas, loc='center left', bbox_to_anchor=(1.0, 0.55), frameon=False, fontsize=8)
    ax.text(0, 0.08, moneda(por_producto.sum()), ha='center', va='center', fontsize=13, fontweight='bold', color=MARRON)
    ax.text(0, -0.14, 'facturado', ha='center', va='center', fontsize=9, color=GRIS)
    if not compacto:
        lider = por_producto.index[0]
        ax.text(1.05, 0.06, f'Producto líder\n{lider}\n{por_producto.iloc[0] / total * 100:.1f}% del total',
                transform=ax.transAxes, ha='left', va='bottom', fontsize=9, fontweight='bold', color=MARRON, bbox=CAJA)
    ax.set_aspect('equal')
    titular(ax, f'{GRAFICOS[1][1]} (top {top} productos)', None if compacto else GRAFICOS[1][2])


def grafico_lineas_tendencia(ax, lineas, desde, hasta, compacto=False):
    """3. Líneas: facturación diaria, media móvil de 7 días, promedio, pico y tendencia lineal (numpy.polyfit)."""
    diaria = facturacion_diaria(lineas, desde, hasta)
    valores = diaria.to_numpy()
    movil = diaria.rolling(7, min_periods=1).mean()
    x = np.arange(len(diaria))
    pendiente, ordenada = np.polyfit(x, valores, 1) if len(diaria) > 1 else (0.0, float(valores[0]))
    promedio, maximo = float(np.mean(valores)), float(np.max(valores))
    dia_pico = diaria.index[int(np.argmax(valores))]

    ax.plot(diaria.index, valores, color='#d9c3a5', linewidth=1, label='Facturación diaria')
    ax.plot(movil.index, movil.to_numpy(), color=COLORES[0], linewidth=2.2, label='Media móvil 7 días')
    ax.plot(diaria.index, pendiente * x + ordenada, color=COLORES[3], linestyle='--', linewidth=1.6,
            label=f'Tendencia ({"+" if pendiente >= 0 else "-"}{moneda(abs(pendiente) * 7)} por semana)')
    ax.axhline(promedio, color=COLORES[2], linestyle=':', linewidth=1.4, label=f'Promedio diario ({moneda(promedio)})')
    ax.scatter([dia_pico], [maximo], s=45, color=COLORES[3], zorder=5)
    if not compacto:
        derecha = int(np.argmax(valores)) > len(valores) * 0.7  # si el pico está a la derecha, el texto va a la izquierda
        ax.annotate(f'Pico: {dia_pico:%d/%m}\n{moneda(maximo)}', xy=(dia_pico, maximo),
                    xytext=(-14 if derecha else 14, -4), textcoords='offset points', ha='right' if derecha else 'left',
                    va='top', fontsize=8, fontweight='bold', color=MARRON, bbox=CAJA)
        ax.text(0.99, 0.97,
                f'Total {moneda(float(np.sum(valores)))}   ·   Promedio/día {moneda(promedio)}   ·   Máximo {moneda(maximo)}',
                transform=ax.transAxes, ha='right', va='top', fontsize=8, color=MARRON, bbox=CAJA)
    ax.set_ylim(bottom=0, top=maximo * (1.35 if not compacto else 1.15) if maximo else 1)
    ax.set_ylabel('Pesos por día')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: moneda(v)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.grid(axis='y', alpha=0.3)
    ax.legend(fontsize=8, frameon=False, loc='upper left', ncol=2 if not compacto else 1)
    estilo_eje(ax, GRAFICOS[2][1], None if compacto else GRAFICOS[2][2])


def grafico_mapa_calor(fig, ax, operaciones, compacto=False):
    """4. Mapa de calor: cantidad de operaciones por día de la semana y hora, con el pico marcado."""
    horas = list(range(7, 21))  # horario de atención
    if operaciones.empty:
        matriz = pd.DataFrame(0, index=range(7), columns=horas)
    else:
        datos = operaciones.assign(dia=operaciones['fecha'].dt.dayofweek, hora=operaciones['fecha'].dt.hour)
        # Si hubo operaciones fuera del horario habitual, se amplía el rango de horas.
        horas = list(range(min(horas[0], int(datos['hora'].min())), max(horas[-1], int(datos['hora'].max())) + 1))
        matriz = (datos.pivot_table(index='dia', columns='hora', values='tipo', aggfunc='count', fill_value=0)
                  .reindex(index=range(7), columns=horas, fill_value=0))
    valores = matriz.to_numpy()
    imagen = ax.imshow(valores, cmap='YlOrBr', aspect='auto')
    ax.set_yticks(range(7), DIAS)
    ax.set_xticks(range(len(horas)), [f'{h}h' for h in horas])
    maximo = int(valores.max())
    if not compacto:
        for i in range(matriz.shape[0]):
            for j in range(matriz.shape[1]):
                valor = int(matriz.iat[i, j])
                ax.text(j, i, valor, ha='center', va='center', fontsize=7,
                        color='white' if valor > (maximo or 1) * 0.6 else '#333333')
    if maximo:
        fila, columna = np.unravel_index(int(np.argmax(valores)), valores.shape)
        ax.add_patch(matplotlib.patches.Rectangle((columna - 0.5, fila - 0.5), 1, 1, fill=False,
                                                  edgecolor=MARRON, linewidth=2.4))
        if not compacto:
            ax.text(1.0, 1.025, f'Pico: {DIAS_LARGOS[fila]} {horas[columna]} h · {maximo} operaciones',
                    transform=ax.transAxes, ha='right', va='bottom', fontsize=8, fontweight='bold', color=MARRON,
                    bbox=CAJA)
    barra = fig.colorbar(imagen, ax=ax, fraction=0.03, pad=0.02)
    barra.ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    barra.set_label('Operaciones', fontsize=8)
    ax.tick_params(labelsize=8)
    titular(ax, f'{GRAFICOS[3][1]} (ventas y encargos)', None if compacto else GRAFICOS[3][2])


# ---------------------------------------------------------------------------
# 4. Generación de archivos
# ---------------------------------------------------------------------------

def guardar(fig, carpeta, nombre):
    ruta = carpeta / nombre
    fig.savefig(ruta, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return ruta


def periodo_txt(desde, hasta):
    return f'{desde:%d/%m/%Y} al {hasta:%d/%m/%Y}'


def subtitulo_periodo(desde, hasta, categoria=None):
    return f'Período {periodo_txt(desde, hasta)}' + (f' · Categoría: {categoria}' if categoria else '')


def crear_figuras(lineas, operaciones, desde, hasta, top=6, categoria=None, incluir_tablero=True):
    """Arma los gráficos y devuelve una lista de diccionarios con
    archivo, título, pregunta de negocio, tipo de gráfico y la figura.

    La usan este script (que guarda los PNG) y el sistema web (Reportes).
    """
    subtitulo = subtitulo_periodo(desde, hasta, categoria)
    figuras = []

    def agregar(indice, fig, ax, pie=None):
        archivo, titulo, pregunta, tipo = GRAFICOS[indice]
        ax.text(0, -0.13, pie or subtitulo, transform=ax.transAxes, fontsize=8, color=GRIS, va='top')
        figuras.append({'archivo': archivo, 'titulo': titulo, 'pregunta': pregunta, 'tipo': tipo, 'figura': fig})

    fig, ax = plt.subplots(figsize=(11, 5.5))
    grafico_barras_categorias(ax, lineas)
    agregar(0, fig, ax)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    grafico_dona_productos(ax, lineas, top)
    agregar(1, fig, ax)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    grafico_lineas_tendencia(ax, lineas, desde, hasta)
    agregar(2, fig, ax)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    grafico_mapa_calor(fig, ax, operaciones)
    agregar(3, fig, ax, f'Período {periodo_txt(desde, hasta)} · todas las categorías')

    if incluir_tablero:
        figuras.append({
            'archivo': '5_tablero_ejecutivo.png',
            'titulo': 'Tablero ejecutivo',
            'pregunta': 'Resumen del período en una sola vista: indicadores clave y los cuatro gráficos.',
            'tipo': 'Tablero',
            'figura': crear_tablero(lineas, operaciones, desde, hasta, top, subtitulo),
        })
    return figuras


def figura_png(fig, dpi=150):
    """Devuelve la figura como bytes PNG (sin guardar archivo) y la cierra."""
    from io import BytesIO

    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return buffer.getvalue()


def generar_graficos(lineas, operaciones, desde, hasta, carpeta, top=6, categoria=None):
    carpeta.mkdir(parents=True, exist_ok=True)
    return [
        guardar(g['figura'], carpeta, g['archivo'])
        for g in crear_figuras(lineas, operaciones, desde, hasta, top, categoria)
    ]


def crear_tablero(lineas, operaciones, desde, hasta, top, subtitulo):
    """5. Tablero ejecutivo: indicadores clave y los cuatro gráficos en una sola imagen."""
    datos = indicadores(lineas, desde, hasta)
    fig = plt.figure(figsize=(17, 11))
    grilla = GridSpec(3, 2, figure=fig, height_ratios=[0.2, 1, 1], hspace=0.42, wspace=0.25)
    fig.suptitle('Panadería Zulca · Tablero ejecutivo', fontsize=18, fontweight='bold', color=MARRON, x=0.01,
                 ha='left', y=0.98)
    fig.text(0.01, 0.945, subtitulo, fontsize=10, color=GRIS)

    crecimiento = datos['crecimiento']
    tarjetas = [
        ('Facturación', moneda(datos['facturacion'])),
        ('Ventas de mostrador', f'{datos["ventas"]:,}'),
        ('Encargos entregados', f'{datos["encargos"]:,}'),
        ('Ticket promedio', moneda(datos['ticket_promedio'])),
        ('Últimos 30 días vs. 30 anteriores', 'Sin datos' if crecimiento is None else f'{crecimiento:+.1f}%'),
    ]
    eje_kpi = fig.add_subplot(grilla[0, :])
    eje_kpi.axis('off')
    for i, (titulo, valor) in enumerate(tarjetas):
        x = 0.1 + i * 0.2
        eje_kpi.text(x, 0.7, valor, ha='center', va='center', fontsize=20, fontweight='bold', color=MARRON,
                     transform=eje_kpi.transAxes)
        eje_kpi.text(x, 0.05, titulo, ha='center', va='center', fontsize=10, color=GRIS, transform=eje_kpi.transAxes)

    grafico_barras_categorias(fig.add_subplot(grilla[1, 0]), lineas, compacto=True)
    grafico_dona_productos(fig.add_subplot(grilla[1, 1]), lineas, top, compacto=True)
    grafico_lineas_tendencia(fig.add_subplot(grilla[2, 0]), lineas, desde, hasta, compacto=True)
    grafico_mapa_calor(fig, fig.add_subplot(grilla[2, 1]), operaciones, compacto=True)
    return fig


def imprimir_resumen(lineas, desde, hasta):
    datos = indicadores(lineas, desde, hasta)
    print(f'\nResumen del período {periodo_txt(desde, hasta)} (calculado con numpy)')
    print(f'  Facturación total ............ {moneda(datos["facturacion"])}')
    print(f'  Ventas de mostrador .......... {datos["ventas"]}')
    print(f'  Encargos entregados .......... {datos["encargos"]}')
    print(f'  Ticket promedio .............. {moneda(datos["ticket_promedio"])}')
    print(f'  Ticket mediano ............... {moneda(datos["ticket_mediana"])}')
    print(f'  Percentil 90 del ticket ...... {moneda(datos["ticket_p90"])}')
    print(f'  Desvío estándar del ticket ... {moneda(datos["ticket_desvio"])}')
    print(f'  Facturación diaria promedio .. {moneda(datos["diaria_promedio"])}')
    print(f'  Producto líder ............... {datos["producto_lider"]} ({datos["producto_lider_pct"]:.1f}% de la facturación)')
    print(f'  Ventas inusuales (> promedio + 3 desvíos = {moneda(datos["limite_inusual"])}): {datos["ventas_inusuales"]}')
    if datos['crecimiento'] is not None:
        print(f'  Últimos 30 días vs. 30 anteriores: {datos["crecimiento"]:+.1f}%')


# ---------------------------------------------------------------------------
# 5. Punto de entrada
# ---------------------------------------------------------------------------

def leer_fecha(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(f'Fecha inválida: {texto} (formato aaaa-mm-dd)')


def main():
    hoy = (datetime.now(timezone.utc) + timedelta(hours=-3)).date()
    parser = argparse.ArgumentParser(description='Gráficos de analítica de Panadería Zulca.')
    parser.add_argument('--desde', type=leer_fecha, help='Fecha inicial aaaa-mm-dd (por defecto, 90 días atrás).')
    parser.add_argument('--hasta', type=leer_fecha, default=hoy, help='Fecha final aaaa-mm-dd (por defecto, hoy).')
    parser.add_argument('--categoria', help='Analizar solo esta categoría (nombre exacto).')
    parser.add_argument('--top', type=int, default=6, help='Productos que se muestran en la dona (por defecto 6).')
    parser.add_argument('--salida', type=Path, default=Path(__file__).resolve().parent / 'graficos',
                        help='Carpeta donde se guardan los PNG.')
    args = parser.parse_args()
    desde = args.desde or (args.hasta - timedelta(days=89))
    if desde > args.hasta:
        parser.error('--desde no puede ser posterior a --hasta.')

    print(f'Leyendo la base de datos ({periodo_txt(desde, args.hasta)})...')
    conexion = conectar()
    try:
        lineas, operaciones = leer_datos(conexion, desde, args.hasta)
    finally:
        conexion.close()

    if args.categoria:
        disponibles = sorted(lineas['categoria'].unique()) if not lineas.empty else []
        lineas = lineas[lineas['categoria'].str.lower() == args.categoria.lower()]
        if lineas.empty:
            sys.exit(f'No hay ventas de la categoría «{args.categoria}» en el período. '
                     f'Categorías con ventas: {", ".join(disponibles) or "ninguna"}.')
        args.categoria = lineas['categoria'].iloc[0]
    if lineas.empty:
        sys.exit('No hay ventas ni encargos entregados en el período elegido.')

    rutas = generar_graficos(lineas, operaciones, desde, args.hasta, args.salida, args.top, args.categoria)
    imprimir_resumen(lineas, desde, args.hasta)
    print('\nGráficos generados:')
    for ruta in rutas:
        print(f'  {ruta}')


if __name__ == '__main__':
    main()
