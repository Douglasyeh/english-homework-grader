"""Upload endpoint tests. Does not use PostgreSQL."""

from __future__ import annotations

from io import BytesIO
import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app
from app.services.storage import page_image_path

client = TestClient(app)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _pdf_bytes(page_count: int) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class UploadSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._storage = tempfile.TemporaryDirectory()
        os.environ["EHG_STORAGE_DIR"] = self._storage.name

    def tearDown(self) -> None:
        os.environ.pop("EHG_STORAGE_DIR", None)
        self._storage.cleanup()

    def test_valid_pdf_upload_returns_page_count(self) -> None:
        files = {"file": ("homework.pdf", _pdf_bytes(3), "application/pdf")}
        data = {"textbook_id": "magic-joy-5", "unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "uploaded")
        self.assertEqual(body["textbook_id"], "magic-joy-5")
        self.assertEqual(body["unit_id"], "unit-1")
        self.assertEqual(body["filename"], "homework.pdf")
        self.assertEqual(body["page_count"], 3)

    def test_valid_pdf_returns_ordered_page_records_and_images(self) -> None:
        files = {"file": ("homework.pdf", _pdf_bytes(3), "application/pdf")}
        data = {"textbook_id": "magic-joy-5", "unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        pages = body["pages"]
        self.assertEqual(len(pages), 3)
        submission_id = body["submission_id"]
        for index, page in enumerate(pages):
            self.assertEqual(page["page_index"], index)
            self.assertEqual(page["page_number"], index + 1)
            expected_url = (
                f"/api/submissions/{submission_id}/pages/{index}/image"
            )
            self.assertEqual(page["image_url"], expected_url)
            image_path = page_image_path(submission_id, index)
            self.assertTrue(image_path.is_file(), image_path)
            image_response = client.get(page["image_url"])
            self.assertEqual(image_response.status_code, 200)
            self.assertTrue(image_response.content.startswith(PNG_MAGIC))
            self.assertIn(
                "image/png",
                image_response.headers.get("content-type", ""),
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

    def test_upload_groups_three_pages_for_unit_1(self) -> None:
        files = {"file": ("homework.pdf", _pdf_bytes(3), "application/pdf")}
        data = {"textbook_id": "magic-joy-5", "unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["grouping_status"], "grouped")
        self.assertEqual(body["expected_pages_per_student"], 3)
        self.assertEqual(body["group_count"], 1)
        self.assertEqual(len(body["student_groups"]), 1)
        mapped = body["student_groups"][0]["pages"]
        self.assertEqual(
            [
                (
                    page["page_index"],
                    page["assignment_page_id"],
                    page["workbook_page"],
                    page["alignment_status"],
                )
                for page in mapped
            ],
            [
                (0, "MJ5-U1-P1", 4, "not_aligned"),
                (1, "MJ5-U1-P2", 5, "not_aligned"),
                (2, "MJ5-U1-P3", 6, "not_aligned"),
            ],
        )

    def test_upload_uneven_page_count_needs_manual_review(self) -> None:
        files = {"file": ("homework.pdf", _pdf_bytes(4), "application/pdf")}
        data = {"textbook_id": "magic-joy-5", "unit_id": "unit-1"}
        response = client.post("/api/submissions/upload", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["grouping_status"], "needs_manual_review")
        self.assertEqual(body["page_count"], 4)
        self.assertEqual(body["expected_pages_per_student"], 3)
        self.assertEqual(body["complete_group_count"], 1)
        self.assertEqual(body["remaining_page_count"], 1)
        self.assertEqual(body["student_groups"], [])
        self.assertEqual(len(body["pages"]), 4)
        self.assertEqual(len(body["provisional_groups"]), 1)
        self.assertEqual(len(body["remaining_pages"]), 1)


if __name__ == "__main__":
    unittest.main()
