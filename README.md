# Formex API

Motor de generación masiva de documentos: toma una plantilla DOCX con marcadores
y un Excel con datos, y genera en lote documentos personalizados en PDF de forma
asíncrona, con tolerancia a fallos por fila. Arquitectura hexagonal + CQRS
ligero, multiusuario/multi-tenant desde el inicio. Ver
[`SAD_Formex_Motor_Generacion_Documentos.md`](../SAD_Formex_Motor_Generacion_Documentos.md)
para el diseño completo.

Estado actual: **M3** — `DocxtplRenderEngine` (marcadores simples y tablas
dinámicas), `OpenpyxlRowParser` y `BatchRowValidator` (RNF-04: filas inválidas
se reportan sin abortar la carga completa). M2 (auth JWT + Postgres +
aislamiento por `organization_id`) completo. 100% de cobertura en `src/domain`.

## Desarrollo

Requiere Postgres arriba (`docker compose up -d postgres` desde la raíz del
proyecto) y un `.env` local (copiar `.env.example`, generar `SECRET_KEY` con
`python -c "import secrets; print(secrets.token_hex(32))"`).

```bash
uv sync
uv run alembic upgrade head
uv run pytest                        # unitarios, 100% cobertura de dominio
uv run pytest -m integration --no-cov  # requiere Postgres real
uv run mypy src
uv run ruff check .
uv run python -m src.main            # levanta la API en :8000
```

**Windows:** `psycopg` (driver async de Postgres) no funciona sobre el
`ProactorEventLoop`, que es la política de asyncio por defecto en Windows —
por eso `src/main.py` fija `WindowsSelectorEventLoopPolicy` y arranca uvicorn
sin pasar por `uvicorn.run()` (que revierte esa política). No aplica en
Docker/Linux, donde este ajuste es un no-op.
