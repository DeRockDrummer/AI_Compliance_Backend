from fpdf import FPDF
from backend.app.reports.report_template import render_report

def generate_pdf_from_compliance(compliance_json: dict) -> bytes:
    report_text = render_report(compliance_json)

    pdf = FPDF()
    pdf.add_page()

    # Load a guaranteed Unicode font (Calibri)
    pdf.add_font("Calibri", "", r"C:\Windows\Fonts\calibri.ttf", uni=True)
    pdf.set_font("Calibri", size=12)

    for line in report_text.split("\n"):
        pdf.multi_cell(0, 10, txt=line)

    return pdf.output(dest="S").encode("utf-8")
