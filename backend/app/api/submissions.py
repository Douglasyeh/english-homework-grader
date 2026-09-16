from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.services.assignment_data import assignment_pages_for
from app.services.page_alignment import attach_alignment_to_groups
from app.services.page_grouping import group_uploaded_pages
from app.services.page_images import render_pdf_pages
from app.services.storage import (
    SUBMISSION_ID_PATTERN,
    page_image_path,
    page_image_url,
)

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
) -> dict:
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

    submission_id = uuid4().hex
    pages_dir = page_image_path(submission_id, 0).parent
    try:
        rendered = render_pdf_pages(content, pages_dir)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid PDF") from exc

    if rendered != page_count:
        page_count = rendered

    pages = [
        {
            "page_index": index,
            "page_number": index + 1,
            "image_url": page_image_url(submission_id, index),
        }
        for index in range(page_count)
    ]

    try:
        assignment_pages = assignment_pages_for(textbook, unit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail="Unknown assignment") from exc

    grouping = group_uploaded_pages(pages, assignment_pages)
    grouping = attach_alignment_to_groups(
        grouping,
        textbook_id=textbook,
        unit_id=unit,
        submission_id=submission_id,
        assignment_pages=assignment_pages,
    )

    return {
        "status": "uploaded",
        "textbook_id": textbook,
        "unit_id": unit,
        "filename": file.filename,
        "page_count": page_count,
        "submission_id": submission_id,
        "pages": pages,
        **grouping,
    }


@router.get("/api/submissions/{submission_id}/pages/{page_index}/image")
def get_page_image(submission_id: str, page_index: int) -> FileResponse:
    if not SUBMISSION_ID_PATTERN.fullmatch(submission_id):
        raise HTTPException(status_code=404, detail="Page image not found")
    if page_index < 0:
        raise HTTPException(status_code=404, detail="Page image not found")
    path = page_image_path(submission_id, page_index)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Page image not found")
    return FileResponse(path, media_type="image/png")
