# Farolero

Farolero es un microservicio FastAPI para gestionar y despertar stacks de Docker Compose bajo demanda, pensado para entornos de desarrollo y automatización.

## Estructura del proyecto

- `app/` - Código fuente principal
  - `main.py` - API FastAPI y lógica de rutas
  - `docker_utils.py` - Utilidades para interactuar con Docker
  - `templates/` - Plantillas HTML (Jinja2)
- `requirements.txt` - Dependencias Python
- `Dockerfile` - Imagen Docker para producción
- `docker-compose.yml` - Orquestación y volúmenes

## Uso rápido

### Requisitos

- Docker y Docker Compose
- Python 3.10+ (para desarrollo local)

### Desarrollo local

python3 -m venv .venv
source .venv/bin/activate

1. Instala dependencias:
   ```sh
   pip install -r requirements.txt
   ```
2. Ejecuta el servidor:
   ```sh
   export FAROLERO_CONFIG=./config.yaml
   uvicorn app.main:app --reload
   ```

### Producción (Docker)

1. Construye la imagen:
   ```sh
   docker build -t farolero .
   ```
2. Lanza con docker-compose:
   ```sh
   docker compose up -d
   ```

> **Nota:** Si quieres asegurarte de que los cambios en el código o dependencias se reflejen en el contenedor, ejecuta:
>
> ```sh
> docker compose up --no-cache
> ```
>
> Esto forzará la reconstrucción de la imagen desde cero.

## Configuración

El archivo `config.yaml` define los stacks disponibles:

```yaml
stacks:
  nombre_stack:
    path: /ruta/al/docker-compose.yml
    project: nombre_proyecto
```

## Endpoints principales

- `/` - Dashboard HTML para gestionar stacks
- `/add` - Añadir stack (POST)
- `/delete/{name}` - Eliminar stack (POST)
- `/wake/{name}` - Despertar stack (POST)
- `/{path:path}` - Catch-all para despertar stack según subdominio

## Notas

- El servicio detecta el stack a despertar según el subdominio recibido en la cabecera `Host`.
- El archivo de configuración puede sobreescribirse con la variable de entorno `FAROLERO_CONFIG`.

## Licencia

MIT
