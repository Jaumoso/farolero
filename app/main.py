from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import yaml, os, glob

# Crear config.yaml de ejemplo si no existe
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.yaml")
EXAMPLE_CONFIG = {
    "stacks": {
        "ejemplo_stack": {
            "path": "/ruta/al/docker-compose.yml",
            "project": "nombre_proyecto"
        }
    }
}

config_path = os.environ.get("FAROLERO_CONFIG", DEFAULT_CONFIG_PATH)
if not os.path.exists(config_path):
    with open(config_path, "w") as f:
        yaml.dump(EXAMPLE_CONFIG, f)

# Permitir override de ruta de config por variable de entorno (útil para desarrollo local)
CONFIG_PATH = config_path
from app.docker_utils import is_stack_running, start_stack


# Permitir override de ruta de config por variable de entorno (útil para desarrollo local)
CONFIG_PATH = os.environ.get("FAROLERO_CONFIG", os.path.join(os.path.dirname(__file__), "../config.yaml"))



app = FastAPI(title="Wake Service", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Utilidad para renderizar solo la tabla de stacks (parcial HTMX)
def render_stacks_table(request, stacks, message=None):
    return templates.TemplateResponse(
        "partials/stacks_table.html",
        {"request": request, "stacks": stacks, "message": message},
    )

# Cargar configuración robusta

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f)
            return data.get("stacks", {}) if data else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error cargando config: {e}")
        return {}

# Buscar el archivo compose válido en el path indicado
def find_compose_file(path):
    import sys
    print(f"[find_compose_file] Buscando archivo compose en: {path}", file=sys.stderr)
    candidates = [
        "docker-compose.yaml", "docker-compose.yml",
        "compose.yaml", "compose.yml"
    ]
    for name in candidates:
        full = os.path.join(path, name)
        print(f"[find_compose_file] Probando: {full}", file=sys.stderr)
        if os.path.isfile(full):
            print(f"[find_compose_file] Encontrado: {full}", file=sys.stderr)
            return full
    # Buscar por glob por si acaso
    files = glob.glob(os.path.join(path, "*compose.y*ml"))
    print(f"[find_compose_file] Resultados glob: {files}", file=sys.stderr)
    return files[0] if files else None

def save_config(data):
    try:
        with open(CONFIG_PATH, "w") as f:
            yaml.dump({"stacks": data}, f)
    except Exception as e:
        print(f"Error guardando config: {e}")


# Dashboard en /dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    stacks = load_config()
    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(
            "partials/stacks_table.html",
            {"request": request, "stacks": stacks, "message": None},
        )
    return templates.TemplateResponse("config.html", {"request": request, "stacks": stacks, "message": None})

@app.post("/add")
async def add_stack(
    request: Request,
    name: str = Form(...),
    path: str = Form(...),
    project: str = Form(...)
):
    stacks = load_config()
    if name in stacks:
        return render_stacks_table(request, stacks, message=f"El stack '{name}' ya existe.")
    stacks[name] = {"path": path, "project": project}
    save_config(stacks)
    stacks = load_config()
    return render_stacks_table(request, stacks, message=f"Stack '{name}' añadido.")

@app.post("/delete/{name}")
async def delete_stack(request: Request, name: str):
    stacks = load_config()
    if name in stacks:
        stacks.pop(name)
        save_config(stacks)
        message = f"Stack '{name}' eliminado."
    else:
        message = f"Stack '{name}' no existe."
    stacks = load_config()
    return render_stacks_table(request, stacks, message=message)

@app.post("/wake/{name}")
async def wake_stack(request: Request, name: str):
    stacks = load_config()
    stack = stacks.get(name)
    if stack and not is_stack_running(stack["project"]):
        start_stack(stack["path"], stack["project"])
        message = f"Stack '{name}' iniciado."
    elif stack:
        message = f"Stack '{name}' ya está en ejecución."
    else:
        message = f"Stack '{name}' no existe."
    stacks = load_config()
    return render_stacks_table(request, stacks, message=message)

# Endpoint catch-all para despertar stack según subdominio

# / despierte stacks según el host
@app.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def wake_any(request: Request):
    host = request.headers.get("host", "").split(".")[0].lower()
    stacks = load_config()
    # Buscar stack ignorando mayúsculas/minúsculas
    stack = None
    for name, data in stacks.items():
        if name.lower() == host:
            stack = data
            break

    if not stack:
        return {"status": "ignored", "message": f"Host {host} no configurado"}

    compose_file = find_compose_file(stack["path"])
    if not compose_file:
        return {"status": "error", "message": f"No se encontró archivo compose en {stack['path']}"}

    try:
        # Usar el nombre del directorio como project
        project = os.path.basename(os.path.normpath(stack["path"]))
        if is_stack_running(project):
            return {"status": "running", "stack": host}
        start_stack(compose_file, project)
        return {"status": "starting", "stack": host}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/edit/{name}")
async def edit_stack(
    request: Request,
    name: str,
    path: str = Form(...),
    project: str = Form(...)
):
    """
    Edita la configuración de un stack existente.

    Args:
        request (Request): La solicitud HTTP.
        name (str): Nombre del stack a editar.
        path (str): Nueva ruta al archivo docker-compose.
        project (str): Nuevo nombre del proyecto Docker Compose.

    Returns:
        TemplateResponse: Respuesta con la tabla de stacks actualizada.
    """
    if not path.strip():
        return render_stacks_table(request, load_config(), message="El campo 'path' no puede estar vacío.")

    if not project.strip():
        return render_stacks_table(request, load_config(), message="El campo 'project' no puede estar vacío.")

    stacks = load_config()
    if name not in stacks:
        return render_stacks_table(request, stacks, message=f"El stack '{name}' no existe.")

    # Actualizar la configuración del stack
    stacks[name] = {"path": path, "project": project}
    save_config(stacks)
    stacks = load_config()
    return render_stacks_table(request, stacks, message=f"Stack '{name}' actualizado correctamente.")
