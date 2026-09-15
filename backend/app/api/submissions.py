from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError

ALLOWED_TEXTBOOK_ID = "magic-joy-5"
ALLOWED_UNIT_ID = "unit-1"

router = APIRouter()


def _is_pdf_upload(file: UploadFile) -> bool:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    if filename.endswith(".pdf"):
        return True
    return content_type in {"application/pdf", "application/x-pdf"}


@router.post("/api/submissions/upload")
async def upload_submission(
    textbook_id: str = Form(...),
    unit_id: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, str | int]:
    textbook = textbook_id.strip()
    unit = unit_id.strip()
    if not textbook:
        raise HTTPException(status_code=400, detail="textbook_id is required")
    if not unit:
        raise HTTPException(status_code=400, detail="unit_id is required")
    if textbook != ALLOWED_TEXTBOOK_ID:
        raise HTTPException(status_code=400, detail="Unknown textbook_id")
    if unit != ALLOWED_UNIT_ID:
        raise HTTPException(status_code=400, detail="Unknown unit_id")

    if not file.filename:
        raise HTTPException(status_code=400, detail="A file is required")
    if not _is_pdf_upload(file):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        reader = PdfReader(BytesIO(content))
        page_count = len(reader.pages)
    except (PdfReadError, ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail="Invalid PDF") from exc

    return {
        "status": "uploaded",
        "textbook_id": textbook,
        "unit_id": unit,
        "filename": file.filename,
        "page_count": page_count,
    }
