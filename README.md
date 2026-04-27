# Analizavet V2

Sistema veterinario de análisis de laboratorio - Versión 2.0

## Inicio Rápido

```bash
./iniciar.sh
```
Esto inicia:

- Servidor FastAPI en http://localhost:8000
- Workers de Dramatiq para tareas en background
- Redis (si no está corriendo)
- Abre Firefox automáticamente

## Stack Tecnológico

- **Python 3.11** \+ **uv** (gestor de dependencias)
- **FastAPI** \+ **HTMX** (server-side rendering)
- **SQLModel** \+ **SQLite** (desarrollo) / PostgreSQL (producción)
- **Dramatiq** \+ **Redis** (tareas en background)
- **WeasyPrint** (generación de PDFs)

## Estructura del Proyecto

```
Analizavet-v2/
├── app/
│   ├── core/           # Lógica de negocio (el "cerebro")
│   ├── satellites/     # Adaptadores (los "sentidos")
│   │   ├── api/        # Rutas FastAPI
│   │   └── web/        # Templates HTMX + static/
│   ├── models/         # Entidades SQLModel
│   ├── routers/        # Endpoints HTTP
│   ├── tasks/          # Tareas Dramatiq
│   ├── templates/      # Jinja2 templates
│   └── static/         # CSS, JS, imágenes
├── tests/              # Tests organizados
├── clinical_standards.py  # Estándares veterinarios
├── settings.toml       # Configuración Dynaconf
├── pyproject.toml      # Dependencias (uv)
└── iniciar.sh          # Script de inicio
```
## Comandos Útiles

```bash
# Ejecutar tests
uv run pytest

# Formatear código
uv run black .
uv run ruff check .

# Iniciar solo servidor (sin dramatiq)
uv run uvicorn app.main:app --reload

# Iniciar solo workers dramatiq
uv run dramatiq app.tasks
```
## Licencia

MIT - Huellas Lab

