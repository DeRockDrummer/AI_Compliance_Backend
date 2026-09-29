from fastapi import APIRouter

router = APIRouter()

@router.get("/pdf")
def generate_pdf_report():
    return {"message": "PDF report placeholder"}

@router.get("/docx")
def generate_docx_report():
    return {"message": "DOCX report placeholder"}
