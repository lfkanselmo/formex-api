from __future__ import annotations

from io import BytesIO

from docxtpl import DocxTemplate


class DocxtplRenderEngine:
    def render(self, template: bytes, context: dict[str, object]) -> bytes:
        document = DocxTemplate(BytesIO(template))
        document.render(context)
        output = BytesIO()
        document.save(output)
        return output.getvalue()

    def detect_placeholders(self, template: bytes) -> frozenset[str]:
        document = DocxTemplate(BytesIO(template))
        return frozenset(document.get_undeclared_template_variables())
