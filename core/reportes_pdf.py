"""Exportación de los reportes consolidados a PDF con ReportLab.

Cada página lleva el encabezado de la panadería y un pie con los filtros
aplicados, el usuario que generó el reporte, la fecha y hora y el número de
página ("Página X de Y").
"""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

MARRON = colors.HexColor('#3e2a1e')
TRIGO = colors.HexColor('#eadcc8')
TRIGO_CLARO = colors.HexColor('#f7f1e8')
GRIS = colors.HexColor('#6b6b6b')

PAGINA = landscape(A4)
MARGEN_X = 1.5 * cm
MARGEN_SUP = 3.0 * cm
MARGEN_INF = 2.4 * cm

ESTILO_TEXTO = ParagraphStyle('texto', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_LEFT)
ESTILO_NUMERO = ParagraphStyle('numero', parent=ESTILO_TEXTO, alignment=TA_RIGHT)
ESTILO_CABECERA = ParagraphStyle('cabecera', parent=ESTILO_TEXTO, fontName='Helvetica-Bold', textColor=colors.white)
ESTILO_CABECERA_DER = ParagraphStyle('cabecera_der', parent=ESTILO_CABECERA, alignment=TA_RIGHT)
ESTILO_TOTAL = ParagraphStyle('total', parent=ESTILO_TEXTO, fontName='Helvetica-Bold')
ESTILO_TOTAL_DER = ParagraphStyle('total_der', parent=ESTILO_TOTAL, alignment=TA_RIGHT)
ESTILO_DESCRIPCION = ParagraphStyle('descripcion', parent=ESTILO_TEXTO, fontSize=9, leading=12, textColor=GRIS)
ESTILO_PIE = ParagraphStyle('pie', parent=ESTILO_TEXTO, fontSize=7.5, leading=9.5, textColor=GRIS)


def _celda(valor, estilo):
    return Paragraph(escape(str(valor)), estilo)


def _anchos(columnas, disponible):
    """Reparte el ancho: las columnas de texto y de importes reciben más espacio."""
    pesos = []
    for i, (nombre, alineacion) in enumerate(columnas):
        if alineacion == 'izq':
            pesos.append(2.8 if i <= 1 else 1.8)
        elif nombre.startswith('$'):
            pesos.append(1.5)
        else:
            pesos.append(1.0)
    total = sum(pesos)
    return [disponible * p / total for p in pesos]


def _canvas_numerado(dibujar_marco):
    """Canvas que conoce la cantidad total de páginas para escribir "Página X de Y"."""

    class CanvasNumerado(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._paginas = []

        def showPage(self):
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas)
            for estado in self._paginas:
                self.__dict__.update(estado)
                dibujar_marco(self, self._pageNumber, total)
                super().showPage()
            super().save()

    return CanvasNumerado


def _construir(titulo, contenido, filtros, usuario, generado):
    """Arma el PDF con encabezado y pie en cada página y devuelve los bytes."""
    buffer = BytesIO()
    ancho_pagina, alto_pagina = PAGINA
    disponible = ancho_pagina - 2 * MARGEN_X

    texto_filtros = 'Filtros aplicados: ' + ' · '.join(f'{nombre}: {valor}' for nombre, valor in filtros)
    texto_generado = f'Generado por {usuario} el {generado:%d/%m/%Y} a las {generado:%H:%M}'

    def dibujar_marco(c, numero, total):
        c.saveState()
        # Encabezado institucional
        y = alto_pagina - 1.4 * cm
        c.setFillColor(MARRON)
        c.setFont('Helvetica-Bold', 16)
        c.drawString(MARGEN_X, y, 'Panadería Zulca')
        c.setFont('Helvetica', 9)
        c.setFillColor(GRIS)
        c.drawRightString(ancho_pagina - MARGEN_X, y + 2, 'Sistema de gestión · Reporte consolidado')
        c.setFillColor(MARRON)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(MARGEN_X, y - 0.65 * cm, titulo)
        c.setStrokeColor(MARRON)
        c.setLineWidth(1.2)
        c.line(MARGEN_X, y - 0.95 * cm, ancho_pagina - MARGEN_X, y - 0.95 * cm)
        # Pie: filtros, usuario, fecha y hora, página
        c.setLineWidth(0.6)
        c.line(MARGEN_X, MARGEN_INF - 0.35 * cm, ancho_pagina - MARGEN_X, MARGEN_INF - 0.35 * cm)
        pie = Paragraph(escape(texto_filtros), ESTILO_PIE)
        _, alto = pie.wrap(disponible, MARGEN_INF)
        pie.drawOn(c, MARGEN_X, MARGEN_INF - 0.5 * cm - alto)
        c.setFont('Helvetica', 7.5)
        c.setFillColor(GRIS)
        c.drawString(MARGEN_X, 0.8 * cm, texto_generado)
        c.drawRightString(ancho_pagina - MARGEN_X, 0.8 * cm, f'Página {numero} de {total}')
        c.restoreState()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=PAGINA,
        leftMargin=MARGEN_X,
        rightMargin=MARGEN_X,
        topMargin=MARGEN_SUP,
        bottomMargin=MARGEN_INF,
        title=f'{titulo} - Panadería Zulca',
        author=usuario,
    )
    documento.build(contenido, canvasmaker=_canvas_numerado(dibujar_marco))
    return buffer.getvalue()


def generar_pdf(titulo, descripcion, columnas, filas, totales, filtros, usuario, generado):
    disponible = PAGINA[0] - 2 * MARGEN_X

    estilos_fila = [ESTILO_TEXTO if a == 'izq' else ESTILO_NUMERO for _, a in columnas]
    estilos_cabecera = [ESTILO_CABECERA if a == 'izq' else ESTILO_CABECERA_DER for _, a in columnas]
    estilos_total = [ESTILO_TOTAL if a == 'izq' else ESTILO_TOTAL_DER for _, a in columnas]

    datos = [[_celda(nombre, e) for (nombre, _), e in zip(columnas, estilos_cabecera)]]
    for fila in filas:
        datos.append([_celda(v, e) for v, e in zip(fila, estilos_fila)])
    if not filas:
        datos.append([_celda('No hay datos para los filtros elegidos.', ESTILO_TEXTO)] + [''] * (len(columnas) - 1))
    datos.append([_celda(v, e) for v, e in zip(totales, estilos_total)])

    tabla = Table(datos, colWidths=_anchos(columnas, disponible), repeatRows=1)
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), MARRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 0), (-1, -2), 0.25, colors.HexColor('#d9cbb5')),
        ('BACKGROUND', (0, -1), (-1, -1), TRIGO),
        ('LINEABOVE', (0, -1), (-1, -1), 1, MARRON),
    ]
    for i in range(1, len(datos) - 1):
        if i % 2 == 0:
            estilo.append(('BACKGROUND', (0, i), (-1, i), TRIGO_CLARO))
    if not filas:
        estilo.append(('SPAN', (0, 1), (-1, 1)))
    tabla.setStyle(TableStyle(estilo))

    contenido = [Paragraph(escape(descripcion), ESTILO_DESCRIPCION), Spacer(1, 0.35 * cm), tabla]
    return _construir(titulo, contenido, filtros, usuario, generado)


def _imagen(png, ancho_max, alto_max):
    """Imagen escalada para entrar en el espacio disponible sin deformarse."""
    imagen = Image(BytesIO(png))
    escala = min(ancho_max / imagen.imageWidth, alto_max / imagen.imageHeight)
    imagen.drawWidth = imagen.imageWidth * escala
    imagen.drawHeight = imagen.imageHeight * escala
    return imagen


def generar_pdf_graficos(titulo, descripcion, indicadores, imagenes, filtros, usuario, generado):
    """PDF de los gráficos: indicadores en la primera página y un gráfico por página.

    indicadores: lista de (nombre, valor). imagenes: lista de (título, bytes PNG).
    """
    disponible = PAGINA[0] - 2 * MARGEN_X
    alto_util = PAGINA[1] - MARGEN_SUP - MARGEN_INF - 0.6 * cm
    estilo_valor = ParagraphStyle('valor', parent=ESTILO_TOTAL, fontSize=14, leading=17, alignment=1)
    estilo_nombre = ParagraphStyle('nombre', parent=ESTILO_PIE, fontSize=8, alignment=1)
    por_fila = 4
    filas = []
    for inicio in range(0, len(indicadores), por_fila):
        grupo = indicadores[inicio:inicio + por_fila]
        grupo = grupo + [('', '')] * (por_fila - len(grupo))
        filas.append([_celda(valor, estilo_valor) for _, valor in grupo])
        filas.append([_celda(nombre, estilo_nombre) for nombre, _ in grupo])
    tarjetas = Table(filas, colWidths=[disponible / por_fila] * por_fila)
    estilo_tarjetas = [
        ('BACKGROUND', (0, 0), (-1, -1), TRIGO_CLARO),
        ('BOX', (0, 0), (-1, -1), 0.6, TRIGO),
        ('INNERGRID', (0, 0), (-1, -1), 0.6, colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for i in range(2, len(filas), 2):
        estilo_tarjetas.append(('LINEABOVE', (0, i), (-1, i), 1.5, colors.white))
    tarjetas.setStyle(TableStyle(estilo_tarjetas))
    contenido = [Paragraph(escape(descripcion), ESTILO_DESCRIPCION), Spacer(1, 0.35 * cm), tarjetas]
    for i, (_, png) in enumerate(imagenes):
        if i == 0:
            contenido.append(Spacer(1, 0.5 * cm))
            contenido.append(KeepTogether([_imagen(png, disponible, alto_util - 6.0 * cm)]))
        else:
            contenido.append(PageBreak())
            contenido.append(_imagen(png, disponible, alto_util))
    return _construir(titulo, contenido, filtros, usuario, generado)


def generar_pdf_imagen(titulo, png, filtros, usuario, generado):
    """PDF de una sola imagen que ocupa toda la página (por ejemplo, el tablero ejecutivo)."""
    disponible = PAGINA[0] - 2 * MARGEN_X
    alto_util = PAGINA[1] - MARGEN_SUP - MARGEN_INF - 0.6 * cm
    return _construir(titulo, [_imagen(png, disponible, alto_util)], filtros, usuario, generado)
