from docx import Document
from backend.app.reports.report_template import render_report
from io import BytesIO

def generate_docx_from_compliance(compliance_json: dict) -> bytes:
    report_text = render_report(compliance_json)

    doc = Document()
    for line in report_text.split("\n"):
        doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
