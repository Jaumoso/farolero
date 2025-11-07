import subprocess
import logging
from typing import Optional
import docker
import yaml

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cliente docker global
client = docker.from_env()

def is_stack_running(project: str) -> bool:
    """
    Comprueba si hay contenedores activos del proyecto.

    Args:
        project (str): Nombre del proyecto Docker Compose.

    Returns:
        bool: True si hay contenedores activos, False en caso contrario.
    """
    try:
        containers = client.containers.list(
            filters={"label": f"com.docker.compose.project={project}"}
        )
        return len(containers) > 0
    except docker.errors.DockerException as e:
        logger.error(f"Error comprobando stack: {e}")
        return False

def find_compose_file(path: str) -> Optional[str]:
    """
    Busca un archivo docker-compose en el directorio especificado.

    Args:
        path (str): Ruta del directorio donde buscar el archivo.

    Returns:
        Optional[str]: Ruta del archivo docker-compose si se encuentra, None en caso contrario.
    """
    # Implementación ficticia para evitar dependencias circulares
    # Reemplazar con la lógica real de `find_compose_file`.
    return None

def start_stack(path: str, project: str):
    """
    Busca el archivo compose dentro del directorio y ejecuta docker compose up -d sin bloquear.

    Args:
        path (str): Ruta del directorio donde se encuentra el archivo docker-compose.
        project (str): Nombre del proyecto Docker Compose.

    Raises:
        FileNotFoundError: Si no se encuentra un archivo docker-compose en el directorio.
        RuntimeError: Si ocurre un error al ejecutar el comando Docker Compose.
    """
    try:
        compose_file = find_compose_file(path)
        if not compose_file:
            raise FileNotFoundError(f"No se encontró archivo compose en {path}")

        subprocess.Popen([
            "docker", "compose", "-f", compose_file, "-p", project, "up", "-d"
        ])
        logger.info(f"Stack '{project}' iniciado correctamente desde {compose_file}.")
    except FileNotFoundError as e:
        logger.error(e)
        raise
    except Exception as e:
        logger.error(f"Error arrancando stack: {e}")
        raise RuntimeError("Error al iniciar el stack") from e

def modify_compose_config(compose_file: str, updates: dict):
    """
    Modifica la configuración de un archivo docker-compose.

    Args:
        compose_file (str): Ruta al archivo docker-compose.
        updates (dict): Diccionario con las claves y valores a actualizar.

    Raises:
        FileNotFoundError: Si el archivo docker-compose no existe.
        yaml.YAMLError: Si ocurre un error al procesar el archivo YAML.
    """
    try:
        # Leer la configuración actual
        with open(compose_file, 'r') as file:
            config = yaml.safe_load(file)

        # Actualizar la configuración
        config.update(updates)

        # Guardar los cambios en el archivo
        with open(compose_file, 'w') as file:
            yaml.safe_dump(config, file)

        logger.info(f"Configuración de {compose_file} actualizada correctamente.")
    except FileNotFoundError:
        logger.error(f"El archivo {compose_file} no existe.")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error procesando el archivo YAML: {e}")
        raise