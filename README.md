# Formex API

Motor de generación masiva de documentos: toma una plantilla DOCX con marcadores
y un Excel con datos, y genera en lote documentos personalizados en PDF de forma
asíncrona, con tolerancia a fallos por fila. Arquitectura hexagonal + CQRS
ligero, multiusuario/multi-tenant desde el inicio. Ver
[`SAD_Formex_Motor_Generacion_Documentos.md`](../SAD_Formex_Motor_Generacion_Documentos.md)
para el diseño completo.

Estado actual: **M1** — dominio `identity` (`Organization`, `User`, `Role`) y
`generation` (`Template`, `GenerationBatch`, `GeneratedDocument`), puertos de
aplicación, 100% de cobertura en `src/domain`.

## Desarrollo

```bash
uv sync
uv run pytest
uv run mypy src
uv run ruff check .
```
