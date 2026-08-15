# Formex API

Motor de generación masiva de documentos: toma una plantilla DOCX con marcadores
y un Excel con datos, y genera en lote documentos personalizados en PDF de forma
asíncrona, con tolerancia a fallos por fila. Arquitectura hexagonal + CQRS
ligero, multiusuario/multi-tenant desde el inicio. Ver
[`SAD_Formex_Motor_Generacion_Documentos.md`](../SAD_Formex_Motor_Generacion_Documentos.md)
para el diseño completo.

Estado actual: **M5** — Celery + Redis con paralelismo real por fila (`chord`
de finalización recomputando el estado agregado del lote) y endpoints FastAPI
completos: `POST /templates` (sube y detecta marcadores), `GET /templates`,
`POST /templates/{id}/batches` (valida filas, encola generación),
`GET /batches`, `GET /batches/{id}`, `GET /batches/{id}/documents`. Verificado
de punta a punta con un servidor y un worker reales generando PDFs. M2-M4
(auth JWT + Postgres, render + validación de Excel, PDF real vía Gotenberg +
MinIO) completos. 100% de cobertura en `src/domain`.

## Desarrollo

Requiere el stack de infraestructura arriba (`docker compose up -d` desde la
raíz del proyecto — Postgres, MinIO, Gotenberg y Redis) y un `.env` local
(copiar `.env.example`, generar `SECRET_KEY` con
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
Docker/Linux, donde este ajuste es un no-op.
