# Formex API

[![CI](https://github.com/lfkanselmo/formex-api/actions/workflows/ci.yml/badge.svg)](https://github.com/lfkanselmo/formex-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/license-proprietary-lightgrey)

Motor de generación masiva de documentos: toma una plantilla DOCX con marcadores
y un Excel con datos, y genera en lote documentos personalizados en PDF de forma
asíncrona, con tolerancia a fallos por fila. Arquitectura hexagonal + CQRS
ligero, multiusuario/multi-tenant desde el inicio. Ver
[`SAD_Formex_Motor_Generacion_Documentos.md`](../SAD_Formex_Motor_Generacion_Documentos.md)
para el diseño completo.

Estado actual: **M8 (completo)** — hardening final, cerrado tras una revisión
de arquitectura dedicada. Plantillas `.docx` y Excels `.xlsx` inválidos,
corruptos o con un zip subyacente fuera de límites (miembros/tamaño
descomprimido) se traducen a errores de dominio
(`InvalidTemplateFileError`/`InvalidExcelFileError`, HTTP 422 con motivo) en
vez de propagar una excepción de librería sin controlar; el límite de tamaño
de subida se aplica por `Content-Length` en un middleware, antes de bufferear
el cuerpo completo. `POST /auth/register` (10/hora), `POST /auth/login`
(20/minuto) y `POST /auth/refresh` (20/minuto, sin autenticación) tienen rate
limiting (`slowapi`). `update_document` del repositorio de lotes ahora exige
`organization_id` y filtra por él, como el resto del repositorio (RNF-09).
`GET /templates/{id}` (M7, requerido por `formex-web`, que ya consume esta
API completa: registro/login, subir plantilla, lanzar lote, progreso en
vivo, reintento y descarga). Reintento de filas fallidas (`POST
/batches/{id}/retry`) y descarga en ZIP (`GET /batches/{id}/download`) de M6.
`formex-api` y su worker de Celery corren dockerizados (`docker/Dockerfile`)
junto al resto de la infraestructura y la SPA — stack completo verificado de
punta a punta vía `docker compose up`. M2-M5 (auth JWT multi-tenant, render +
validación de Excel, PDF real vía Gotenberg + MinIO, paralelismo real por
fila vía Celery) completos. 100% de cobertura en `src/domain`, 116 tests
(67 unitarios + 49 de integración) en verde.

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
