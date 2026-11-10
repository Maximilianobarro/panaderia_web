# Panadería Zulca

Sistema de gestión para la Panadería y Panificadora Zulca (Práctica Profesional III).
Hecho con Django 6.1 y MySQL 8.4.

## Cómo ejecutarlo en cualquier PC (con Docker)

### Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y abierto.
- Git (opcional). También se puede descargar el proyecto como ZIP desde GitHub.

### Pasos

1. Descargar el proyecto:

   ```
   git clone https://github.com/Maximilianobarro/panaderia_web.git
   cd panaderia_web
   ```

2. Levantar todo:

   ```
   docker compose up -d --build
   ```

   La primera vez tarda unos minutos: descarga las imágenes, instala las dependencias
   y carga la base de datos desde `db/panaderia.sql`.

3. Esperar alrededor de un minuto y abrir en el navegador:

   - Aplicación: http://localhost:8000
   - phpMyAdmin: http://localhost:8080

4. Iniciar sesión con un usuario del sistema. Pedir usuario y contraseña al autor del proyecto.

### Comandos útiles

| Acción | Comando |
|---|---|
| Ver si los servicios están corriendo | `docker compose ps` |
| Ver los mensajes de la aplicación | `docker compose logs web` |
| Detener todo (los datos se conservan) | `docker compose down` |
| Volver a levantar | `docker compose up -d` |
| Actualizar a la última versión | `git pull` y luego `docker compose up -d --build` |

### Si la aplicación no abre

- La base de datos tarda en iniciar la primera vez. Esperar un minuto y recargar la página.
- Si sigue sin abrir: `docker compose restart web`.

### Sobre la base de datos

El archivo `db/panaderia.sql` se carga **solo la primera vez**, cuando la base de datos está vacía.
Si en esa PC ya se había levantado una versión anterior del proyecto, la carga no se repite.
Para forzarla hay que borrar la base de datos local de esa PC:

```
docker compose down -v
docker compose up -d --build
```

**Atención:** `docker compose down -v` borra todos los datos guardados en esa PC.

## Cómo ejecutarlo sin Docker para la aplicación

La base de datos corre en Docker y la aplicación en la PC (Python 3.12 o superior):

```
docker compose up -d db phpmyadmin
pip install -r requirements.txt
python manage.py runserver
```

La aplicación queda en http://127.0.0.1:8000.

## Servicios

| Servicio | Dirección | Descripción |
|---|---|---|
| web | http://localhost:8000 | Aplicación Django |
| db | localhost:3307 | MySQL 8.4, base `panaderia` |
| phpmyadmin | http://localhost:8080 | Administración de la base de datos |
