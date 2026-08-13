# Formex API

Motor de generación masiva de documentos: toma una plantilla DOCX con marcadores
y un Excel con datos, y genera en lote documentos personalizados en PDF de forma
asíncrona, con tolerancia a fallos por fila. Arquitectura hexagonal + CQRS
ligero, multiusuario/multi-tenant desde el inicio. Ver
[`SAD_Formex_Motor_Generacion_Documentos.md`](../SAD_Formex_Motor_Generacion_Documentos.md)
para el diseño completo.

Estado actual: **M4** — `GotenbergPdfConverter` y `S3DocumentStorage` (MinIO)
reales, con `GenerateDocumentUseCase` orquestando el pipeline síncrono de una
fila completo: render (`DocxtplRenderEngine`) → conversión a PDF (Gotenberg) →
almacenamiento (MinIO), verificado con un PDF real de punta a punta. M2 (auth
JWT + Postgres) y M3 (render + validación de Excel) completos. 100% de
cobertura en `src/domain`.

## Desarrollo

Requiere el stack de infraestructura arriba (`docker compose up -d` desde la
raíz del proyecto — Postgres, MinIO y Gotenberg) y un `.env` local (copiar
`.env.example`, generar `SECRET_KEY` con
`python -c "import secrets; print(secrets.token_hex(32))"`).

```bash
uv sync
uv run alembic upgrade head
uv run pytest                          # unitarios, 100% cobertura de dominio
uv run pytest -m integration --no-cov  # requiere Postgres, MinIO y Gotenberg reales
uv run mypy src
uv run ruff check .
uv run python -m src.main              # levanta la API en :8000
```

**Windows:** `psycopg` (driver async de Postgres) no funciona sobre el
`ProactorEventLoop`, que es la política de asyncio por defecto en Windows —
por eso `src/main.py` fija `WindowsSelectorEventLoopPolicy` y arranca uvicorn
sin pasar por `uvicorn.run()` (que revierte esa política). No aplica en
Docker/Linux, donde este ajuste es un no-op.
