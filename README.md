# Formex API

Motor de generación masiva de documentos: toma una plantilla DOCX con marcadores
y un Excel con datos, y genera en lote documentos personalizados en PDF de forma
asíncrona, con tolerancia a fallos por fila. Arquitectura hexagonal + CQRS
ligero, multiusuario/multi-tenant desde el inicio. Ver
[`SAD_Formex_Motor_Generacion_Documentos.md`](../SAD_Formex_Motor_Generacion_Documentos.md)
para el diseño completo.

Estado actual: **M7** — `GET /templates/{id}` (requerido por `formex-web`,
que ya consume esta API completa: registro/login, subir plantilla, lanzar
lote, progreso en vivo, reintento y descarga). Reintento de filas fallidas
(`POST /batches/{id}/retry`) y descarga en ZIP (`GET /batches/{id}/download`)
de M6. `formex-api` y su worker de Celery corren dockerizados
(`docker/Dockerfile`) junto al resto de la infraestructura y la SPA — stack
completo verificado de punta a punta vía `docker compose up`. M2-M5 (auth JWT
multi-tenant, render + validación de Excel, PDF real vía Gotenberg + MinIO,
paralelismo real por fila vía Celery) completos. 100% de cobertura en
`src/domain`.

## Levantar el stack completo con Docker

Desde la raíz del proyecto (`formex/`, no `formex-api/`):

```bash
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
docker compose up -d --build
```

Levanta Postgres, MinIO, Gotenberg, Redis, la API (`:8000`, corre las
migraciones al iniciar) y el worker de Celery — todos comunicándose por la red
interna de Docker (`postgres`, `redis`, `minio`, `gotenberg` como hostnames,
no `localhost`).

## Desarrollo local (sin Docker para la app)

Requiere el stack de infraestructura arriba (`docker compose up -d postgres
minio minio-init gotenberg redis` desde la raíz del proyecto) y un `.env`
local (copiar `.env.example`, generar `SECRET_KEY` con
`python -c "import secrets; print(secrets.token_hex(32))"`).

```bash
uv sync
uv run alembic upgrade head
uv run pytest                          # unitarios, 100% cobertura de dominio
uv run pytest -m integration --no-cov  # requiere Postgres, MinIO, Gotenberg y Redis reales
uv run mypy src
uv run ruff check .
uv run python -m src.main              # levanta la API en :8000
uv run celery -A src.infrastructure.tasks.celery_app worker --pool=solo --loglevel=info  # worker (Windows: --pool=solo)
```

**Windows:** `psycopg` (driver async de Postgres) no funciona sobre el
`ProactorEventLoop`, que es la política de asyncio por defecto en Windows —
por eso `src/main.py` fija `WindowsSelectorEventLoopPolicy` y arranca uvicorn
sin pasar por `uvicorn.run()` (que revierte esa política). No aplica en
Docker/Linux, donde este ajuste es un no-op — dentro del contenedor el
`Dockerfile` arranca uvicorn directamente por CLI.
