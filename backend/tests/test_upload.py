"""Upload endpoint tests. Does not use PostgreSQL."""

from __future__ import annotations

from io import BytesIO
import unittest

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app

client = TestClient(app)


def _pdf_bytes(page_count: int) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class UploadSubmissionTests(unittest.TestCase):
    def test_valid_pdf_upload_returns_page_count(self) -> None:
        files = {"file": ("homework.pdf", _pdf_bytes(3), "application/pdf")}
        data = {"textbook_id": "magic-joy-5", "unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "uploaded",
                "textbook_id": "magic-joy-5",
                "unit_id": "unit-1",
                "filename": "homework.pdf",
                "page_count": 3,
            },
        )

    def test_non_pdf_is_rejected(self) -> None:
        files = {"file": ("notes.txt", b"not a pdf", "text/plain")}
        data = {"textbook_id": "magic-joy-5", "unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data, files=files)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Uploaded file must be a PDF")

    def test_invalid_pdf_bytes_are_rejected(self) -> None:
        files = {"file": ("fake.pdf", b"not really a pdf", "application/pdf")}
        data = {"textbook_id": "magic-joy-5", "unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data, files=files)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid PDF")

    def test_missing_file_is_rejected(self) -> None:
        data = {"textbook_id": "magic-joy-5", "unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data)
        self.assertEqual(response.status_code, 422)

    def test_missing_textbook_id_is_rejected(self) -> None:
        files = {"file": ("homework.pdf", _pdf_bytes(1), "application/pdf")}
        data = {"unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data, files=files)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
