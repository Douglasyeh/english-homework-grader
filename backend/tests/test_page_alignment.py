"""Canonical template mapping and alignment failure modes."""

from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image

from app.services.assignment_data import assignment_pages_for, load_assignment
from app.services.page_alignment import (
    STATUS_NOT_ALIGNED,
    STATUS_TEMPLATE_MISSING,
    align_page,
    canonical_template_path,
    unit_dir,
)


class TemplateMappingTests(unittest.TestCase):
    def test_mj5_u1_pages_map_to_workbook_and_template_paths(self) -> None:
        pages = assignment_pages_for("magic-joy-5", "unit-1")
        by_id = {page["assignment_page_id"]: page for page in pages}
        self.assertEqual(by_id["MJ5-U1-P1"]["workbook_page"], 4)
        self.assertEqual(by_id["MJ5-U1-P2"]["workbook_page"], 5)
        self.assertEqual(by_id["MJ5-U1-P3"]["workbook_page"], 6)
        self.assertEqual(by_id["MJ5-U1-P1"]["template_image"], "templates/MJ5-U1-P1.png")
        self.assertEqual(by_id["MJ5-U1-P2"]["template_image"], "templates/MJ5-U1-P2.png")
        self.assertEqual(by_id["MJ5-U1-P3"]["template_image"], "templates/MJ5-U1-P3.png")
        for page in pages:
            path = canonical_template_path(
                "magic-joy-5",
                "unit-1",
                page["template_image"],
            )
            expected = (
                unit_dir("magic-joy-5", "unit-1") / page["template_image"]
            )
            self.assertEqual(path, expected)
            self.assertTrue(path.is_file(), f"missing canonical template {path}")

    def test_configured_regions_map_to_assignment_pages(self) -> None:
        from app.services.regions import iter_answer_regions

        data = load_assignment("magic-joy-5", "unit-1")
        expected_page = {"A": "MJ5-U1-P1", "B": "MJ5-U1-P1", "C": "MJ5-U1-P2", "D": "MJ5-U1-P2", "E": "MJ5-U1-P3", "F": "MJ5-U1-P3"}
        counts = {"MJ5-U1-P1": 0, "MJ5-U1-P2": 0, "MJ5-U1-P3": 0}
        for question, _region, page_id in iter_answer_regions(data):
            self.assertEqual(page_id, expected_page[question["section"]])
            counts[page_id] += 1
        self.assertEqual(counts, {"MJ5-U1-P1": 20, "MJ5-U1-P2": 20, "MJ5-U1-P3": 19})

    def test_golden_dataset_expected_answers_not_altered_by_coordinates(self) -> None:
        from tests.test_assignment_data import GOLDEN_EXPECTED_ANSWERS

        data = load_assignment("magic-joy-5", "unit-1")
        actual = {
            question["question_id"]: question["expected_answer"]
            for question in data["questions"]
        }
        self.assertEqual(actual, GOLDEN_EXPECTED_ANSWERS)

    def test_missing_template_is_not_aligned(self) -> None:
        result = align_page(
            Path("missing-student.png"),
            Path("missing-template.png"),
        )
        self.assertEqual(result["status"], STATUS_TEMPLATE_MISSING)
        self.assertIsNone(result["aligned_image_path"])
        self.assertIsNone(result["transform"])

    def test_existing_files_without_transform_are_not_aligned(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            student = Path(temp_dir) / "student.png"
            template = Path(temp_dir) / "template.png"
            Image.new("RGB", (20, 20), color=(1, 2, 3)).save(student)
            Image.new("RGB", (20, 20), color=(4, 5, 6)).save(template)
            result = align_page(student, template)
            self.assertEqual(result["status"], STATUS_NOT_ALIGNED)
            self.assertIsNone(result["aligned_image_path"])
            self.assertIsNone(result["transform"])


if __name__ == "__main__":
    unittest.main()
