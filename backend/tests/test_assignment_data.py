"""Structural checks for assignment JSON templates. No PostgreSQL required."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSIGNMENT_PATH = (
    REPO_ROOT
    / "data"
    / "textbooks"
    / "magic-joy-5"
    / "units"
    / "unit-1"
    / "assignment.json"
)

ALLOWED_RESPONSE_MODES = frozenset(
    {"circle_selection", "check_selection", "handwriting"}
)

GOLDEN_EXPECTED_ANSWERS = {
    "MJ5-U1-A1": {"selected": ["MJ5-U1-A1-O2"]},
    "MJ5-U1-A2": {"selected": ["MJ5-U1-A2-O2"]},
    "MJ5-U1-A3": {"selected": ["MJ5-U1-A3-O1"]},
    "MJ5-U1-A4": {"selected": ["MJ5-U1-A4-O2"]},
    "MJ5-U1-A5": {"selected": ["MJ5-U1-A5-O1"]},
    "MJ5-U1-A6": {"selected": ["MJ5-U1-A6-O1"]},
    "MJ5-U1-B1": {"selected": ["MJ5-U1-B1-O2"]},
    "MJ5-U1-B2": {"selected": ["MJ5-U1-B2-O1"]},
    "MJ5-U1-B3": {"selected": ["MJ5-U1-B3-O1"]},
    "MJ5-U1-B4": {"selected": ["MJ5-U1-B4-O2"]},
    "MJ5-U1-C1": {"option": "A", "selected": ["MJ5-U1-C1-O1"]},
    "MJ5-U1-C2": {"option": "B", "selected": ["MJ5-U1-C2-O2"]},
    "MJ5-U1-D1": {"selected": ["MJ5-U1-D1-O2"], "text": "don't"},
    "MJ5-U1-D2": {"selected": ["MJ5-U1-D2-O3"], "text": "do"},
    "MJ5-U1-D3": {"selected": ["MJ5-U1-D3-O3"], "text": "want"},
    "MJ5-U1-D4": {"selected": ["MJ5-U1-D4-O2"], "text": "they"},
    "MJ5-U1-E1": ["have"],
    "MJ5-U1-E2": ["What", "you"],
    "MJ5-U1-E3": ["want", "No"],
    "MJ5-U1-E4": ["Do", "don't"],
    "MJ5-U1-F1": ["green", "tea"],
    "MJ5-U1-F2": ["Yes", "we", "like", "milk"],
    "MJ5-U1-F3": ["they", "do", "not", "They", "mango", "juice"],
}

GOLDEN_EXPECTED_SELECTED = {
    "MJ5-U1-A1-O1": False,
    "MJ5-U1-A1-O2": True,
    "MJ5-U1-A2-O1": False,
    "MJ5-U1-A2-O2": True,
    "MJ5-U1-A3-O1": True,
    "MJ5-U1-A3-O2": False,
    "MJ5-U1-A4-O1": False,
    "MJ5-U1-A4-O2": True,
    "MJ5-U1-A5-O1": True,
    "MJ5-U1-A5-O2": False,
    "MJ5-U1-A6-O1": True,
    "MJ5-U1-A6-O2": False,
    "MJ5-U1-B1-O1": False,
    "MJ5-U1-B1-O2": True,
    "MJ5-U1-B2-O1": True,
    "MJ5-U1-B2-O2": False,
    "MJ5-U1-B3-O1": True,
    "MJ5-U1-B3-O2": False,
    "MJ5-U1-B4-O1": False,
    "MJ5-U1-B4-O2": True,
    "MJ5-U1-C1-O1": True,
    "MJ5-U1-C1-O2": False,
    "MJ5-U1-C1-O3": False,
    "MJ5-U1-C2-O1": False,
    "MJ5-U1-C2-O2": True,
    "MJ5-U1-C2-O3": False,
    "MJ5-U1-D1-O1": False,
    "MJ5-U1-D1-O2": True,
    "MJ5-U1-D1-O3": False,
    "MJ5-U1-D2-O1": False,
    "MJ5-U1-D2-O2": False,
    "MJ5-U1-D2-O3": True,
    "MJ5-U1-D3-O1": False,
    "MJ5-U1-D3-O2": False,
    "MJ5-U1-D3-O3": True,
    "MJ5-U1-D4-O1": False,
    "MJ5-U1-D4-O2": True,
    "MJ5-U1-D4-O3": False,
}


def load_assignment(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError("assignment.json must contain a JSON object")
    return data


def require_nonempty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{field} must be a non-empty string")


def section_ids_from_assignment(sections: list[Any]) -> set[str]:
    ids: set[str] = set()
    for item in sections:
        if isinstance(item, str) and item.strip():
            ids.add(item.strip())
        elif isinstance(item, dict):
            section_id = item.get("section_id")
            if isinstance(section_id, str) and section_id.strip():
                ids.add(section_id.strip())
    return ids


def expected_pages_per_student(data: dict[str, Any]) -> int:
    pages = data.get("assignment_pages")
    if not isinstance(pages, list):
        raise AssertionError("assignment_pages must be a list")
    return len(pages)


def validate_assignment_pages(data: dict[str, Any], questions: list[Any]) -> None:
    if "pages_per_student" in data or "assignment_page_count" in data:
        raise AssertionError(
            "Do not store pages_per_student or assignment_page_count; "
            "derive the count from len(assignment_pages)"
        )

    pages = data.get("assignment_pages")
    if questions and (not isinstance(pages, list) or len(pages) == 0):
        raise AssertionError(
            "assignment_pages must be a non-empty list for a populated assignment"
        )
    if pages is None:
        return
    if not isinstance(pages, list):
        raise AssertionError("assignment_pages must be a list")
    if len(pages) == 0:
        raise AssertionError("assignment_pages must not be empty when present")

    known_sections = section_ids_from_assignment(data.get("sections") or [])
    page_ids: set[str] = set()
    sequences: list[int] = []
    workbook_pages: set[int] = set()
    by_workbook: dict[int, dict[str, Any]] = {}

    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise AssertionError(f"assignment_pages[{index}] must be an object")
        page_id = page.get("assignment_page_id")
        require_nonempty_string(page_id, f"assignment_pages[{index}].assignment_page_id")
        if page_id in page_ids:
            raise AssertionError(f"duplicate assignment_page_id: {page_id}")
        page_ids.add(page_id)

        sequence = page.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool):
            raise AssertionError(f"assignment_pages[{index}].sequence must be an integer")
        sequences.append(sequence)

        workbook_page = page.get("workbook_page")
        if not isinstance(workbook_page, int) or isinstance(workbook_page, bool):
            raise AssertionError(
                f"assignment_pages[{index}].workbook_page must be an integer"
            )
        if workbook_page in workbook_pages:
            raise AssertionError(f"duplicate workbook_page: {workbook_page}")
        workbook_pages.add(workbook_page)
        by_workbook[workbook_page] = page

        page_sections = page.get("sections")
        if not isinstance(page_sections, list) or len(page_sections) == 0:
            raise AssertionError(
                f"assignment_pages[{index}].sections must be a non-empty list"
            )
        for section in page_sections:
            if section not in known_sections:
                raise AssertionError(
                    f"assignment_pages[{index}] references unknown section {section!r}"
                )

    if len(sequences) != len(set(sequences)):
        raise AssertionError("assignment_pages sequence values must be unique")
    expected_sequences = list(range(1, len(pages) + 1))
    if sequences != expected_sequences:
        raise AssertionError(
            "assignment_pages sequence values must be ordered and contiguous "
            f"starting at 1; got {sequences}"
        )

    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            continue
        page_number = question.get("page_number")
        if not isinstance(page_number, int) or isinstance(page_number, bool):
            raise AssertionError(
                f"questions[{index}].page_number must be a workbook page integer"
            )
        assignment_page = by_workbook.get(page_number)
        if assignment_page is None:
            raise AssertionError(
                f"questions[{index}] page_number {page_number} does not map to "
                "exactly one assignment_pages workbook_page"
            )
        question_section = question.get("section")
        page_sections = assignment_page.get("sections") or []
        if question_section not in page_sections:
            raise AssertionError(
                f"questions[{index}] section {question_section!r} is not on the "
                f"assignment page for workbook_page {page_number}"
            )


def validate_assignment_structure(data: dict[str, Any]) -> None:
    require_nonempty_string(data.get("assignment_id"), "assignment_id")
    require_nonempty_string(data.get("textbook_id"), "textbook_id")
    require_nonempty_string(data.get("unit_id"), "unit_id")

    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) == 0:
        raise AssertionError("sections must be a non-empty list")

    questions = data.get("questions")
    if not isinstance(questions, list):
        raise AssertionError("questions must be an array/list")

    question_ids: set[str] = set()
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            raise AssertionError(f"questions[{index}] must be an object")

        question_id = question.get("question_id")
        require_nonempty_string(question_id, f"questions[{index}].question_id")
        if question_id in question_ids:
            raise AssertionError(f"duplicate question_id: {question_id}")
        question_ids.add(question_id)

        require_nonempty_string(
            question.get("question_type"),
            f"questions[{index}].question_type",
        )
        response_mode = question.get("response_mode")
        require_nonempty_string(
            response_mode,
            f"questions[{index}].response_mode",
        )
        if response_mode not in ALLOWED_RESPONSE_MODES:
            raise AssertionError(
                f"questions[{index}].response_mode must be one of "
                f"{sorted(ALLOWED_RESPONSE_MODES)}; got {response_mode!r}"
            )
        require_nonempty_string(
            question.get("grading_strategy"),
            f"questions[{index}].grading_strategy",
        )
        if "expected_answer" not in question:
            raise AssertionError(f"questions[{index}].expected_answer is required")
        if question.get("expected_answer") in (None, ""):
            raise AssertionError(
                f"questions[{index}].expected_answer must not be empty"
            )

        regions = question.get("answer_regions", [])
        if regions is None:
            regions = []
        if not isinstance(regions, list):
            raise AssertionError(
                f"questions[{index}].answer_regions must be a list"
            )

        region_ids: set[str] = set()
        for region_index, region in enumerate(regions):
            if not isinstance(region, dict):
                raise AssertionError(
                    f"questions[{index}].answer_regions[{region_index}] "
                    "must be an object"
                )
            region_id = region.get("region_id")
            require_nonempty_string(
                region_id,
                f"questions[{index}].answer_regions[{region_index}].region_id",
            )
            if region_id in region_ids:
                raise AssertionError(
                    f"duplicate region_id in {question_id}: {region_id}"
                )
            region_ids.add(region_id)

    validate_assignment_pages(data, questions)


class AssignmentDataTests(unittest.TestCase):
    def test_magic_joy_5_unit_1_template_structure(self) -> None:
        self.assertTrue(ASSIGNMENT_PATH.is_file(), f"missing {ASSIGNMENT_PATH}")
        data = load_assignment(ASSIGNMENT_PATH)
        validate_assignment_structure(data)
        self.assertEqual(data["assignment_id"], "magic-joy-5-unit-1")
        self.assertEqual(data["textbook_id"], "magic-joy-5")
        self.assertEqual(data["unit_id"], "unit-1")
        self.assertEqual(
            data["source_status"],
            "manually_verified_from_supplied_source",
        )
        self.assertIsInstance(data["questions"], list)

    def test_populated_handwriting_question_rules(self) -> None:
        sample = {
            "assignment_id": "example-only",
            "textbook_id": "example-textbook",
            "unit_id": "unit-1",
            "sections": [{"section_id": "E", "title": "E"}],
            "assignment_pages": [
                {
                    "assignment_page_id": "PLACEHOLDER_P1",
                    "sequence": 1,
                    "workbook_page": 1,
                    "sections": ["E"],
                }
            ],
            "questions": [
                {
                    "question_id": "PLACEHOLDER_NOT_REAL_E4",
                    "section": "E",
                    "question_number": "4",
                    "question_type": "look_and_write",
                    "response_mode": "handwriting",
                    "grading_strategy": "multi_blank",
                    "expected_answer": ["Do", "don't"],
                    "page_number": 1,
                    "answer_regions": [
                        {
                            "region_id": "PLACEHOLDER_NOT_REAL_E4_b1",
                            "blank_number": 1,
                            "x": None,
                            "y": None,
                            "width": None,
                            "height": None,
                        },
                        {
                            "region_id": "PLACEHOLDER_NOT_REAL_E4_b2",
                            "blank_number": 2,
                            "x": None,
                            "y": None,
                            "width": None,
                            "height": None,
                        },
                    ],
                    "notes": "PLACEHOLDER EXAMPLE — not Magic Joy 5 content",
                }
            ],
        }
        validate_assignment_structure(sample)

    def test_populated_selection_question_rules(self) -> None:
        sample = {
            "assignment_id": "example-only",
            "textbook_id": "example-textbook",
            "unit_id": "unit-1",
            "sections": [{"section_id": "A", "title": "A"}],
            "assignment_pages": [
                {
                    "assignment_page_id": "PLACEHOLDER_P1",
                    "sequence": 1,
                    "workbook_page": 1,
                    "sections": ["A"],
                }
            ],
            "questions": [
                {
                    "question_id": "PLACEHOLDER_NOT_REAL_CIRCLE",
                    "section": "A",
                    "question_number": "1",
                    "question_type": "listen_and_circle",
                    "response_mode": "circle_selection",
                    "grading_strategy": "exact_answer",
                    "expected_answer": {"selected": ["option_2"]},
                    "page_number": 1,
                    "answer_regions": [
                        {
                            "region_id": "PLACEHOLDER_NOT_REAL_CIRCLE_opt1",
                            "option_id": "option_1",
                            "label": "ping",
                            "expected_selected": False,
                            "x": None,
                            "y": None,
                            "width": None,
                            "height": None,
                        },
                        {
                            "region_id": "PLACEHOLDER_NOT_REAL_CIRCLE_opt2",
                            "option_id": "option_2",
                            "label": "pink",
                            "expected_selected": True,
                            "x": None,
                            "y": None,
                            "width": None,
                            "height": None,
                        },
                    ],
                    "notes": "PLACEHOLDER EXAMPLE — not Magic Joy 5 content",
                }
            ],
        }
        validate_assignment_structure(sample)

    def test_invalid_response_mode_is_rejected(self) -> None:
        sample = {
            "assignment_id": "example-only",
            "textbook_id": "example-textbook",
            "unit_id": "unit-1",
            "sections": ["A"],
            "questions": [
                {
                    "question_id": "PLACEHOLDER_Q1",
                    "question_type": "fill_in",
                    "response_mode": "not_a_real_mode",
                    "grading_strategy": "exact_answer",
                    "expected_answer": "want",
                    "answer_regions": [],
                }
            ],
        }
        with self.assertRaises(AssertionError):
            validate_assignment_structure(sample)

    def test_duplicate_question_id_is_rejected(self) -> None:
        sample = {
            "assignment_id": "example-only",
            "textbook_id": "example-textbook",
            "unit_id": "unit-1",
            "sections": ["A"],
            "questions": [
                {
                    "question_id": "PLACEHOLDER_DUP",
                    "question_type": "fill_in",
                    "response_mode": "handwriting",
                    "grading_strategy": "exact_answer",
                    "expected_answer": "want",
                    "answer_regions": [],
                },
                {
                    "question_id": "PLACEHOLDER_DUP",
                    "question_type": "fill_in",
                    "response_mode": "handwriting",
                    "grading_strategy": "exact_answer",
                    "expected_answer": "want",
                    "answer_regions": [],
                },
            ],
        }
        with self.assertRaises(AssertionError):
            validate_assignment_structure(sample)

    def test_duplicate_region_id_within_question_is_rejected(self) -> None:
        sample = {
            "assignment_id": "example-only",
            "textbook_id": "example-textbook",
            "unit_id": "unit-1",
            "sections": ["A"],
            "questions": [
                {
                    "question_id": "PLACEHOLDER_Q1",
                    "question_type": "fill_in",
                    "response_mode": "handwriting",
                    "grading_strategy": "multi_blank",
                    "expected_answer": ["a", "b"],
                    "answer_regions": [
                        {"region_id": "SAME_REGION"},
                        {"region_id": "SAME_REGION"},
                    ],
                }
            ],
        }
        with self.assertRaises(AssertionError):
            validate_assignment_structure(sample)


class MagicJoy5Unit1GoldenDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_assignment(ASSIGNMENT_PATH)
        validate_assignment_structure(cls.data)
        cls.questions = cls.data["questions"]
        cls.by_id = {question["question_id"]: question for question in cls.questions}

    def test_total_question_count(self) -> None:
        self.assertEqual(len(self.questions), 23)

    def test_section_counts(self) -> None:
        counts: dict[str, int] = {}
        for question in self.questions:
            section = question["section"]
            counts[section] = counts.get(section, 0) + 1
        self.assertEqual(counts["A"], 6)
        self.assertEqual(counts["B"], 4)
        self.assertEqual(counts["C"], 2)
        self.assertEqual(counts["D"], 4)
        self.assertEqual(counts["E"], 4)
        self.assertEqual(counts["F"], 3)

    def test_question_ids_unique_and_namespaced(self) -> None:
        ids = [question["question_id"] for question in self.questions]
        self.assertEqual(len(ids), len(set(ids)))
        for question_id in ids:
            self.assertTrue(
                question_id.startswith("MJ5-U1-"),
                question_id,
            )

    def test_a1_options_and_correct_pink(self) -> None:
        question = self.by_id["MJ5-U1-A1"]
        labels = [region["label"] for region in question["answer_regions"]]
        self.assertEqual(labels, ["ping", "pink"])
        selected = [
            region["label"]
            for region in question["answer_regions"]
            if region["expected_selected"]
        ]
        self.assertEqual(selected, ["pink"])

    def test_a5_preserves_ming_capitalization(self) -> None:
        question = self.by_id["MJ5-U1-A5"]
        selected = [
            region["label"]
            for region in question["answer_regions"]
            if region["expected_selected"]
        ]
        self.assertEqual(selected, ["Ming"])

    def test_c1_correct_option_a(self) -> None:
        question = self.by_id["MJ5-U1-C1"]
        self.assertEqual(question["expected_answer"]["option"], "A")

    def test_c2_correct_option_b(self) -> None:
        question = self.by_id["MJ5-U1-C2"]
        self.assertEqual(question["expected_answer"]["option"], "B")

    def test_d_correct_answer_text(self) -> None:
        self.assertEqual(self.by_id["MJ5-U1-D1"]["expected_answer"]["text"], "don't")
        self.assertEqual(self.by_id["MJ5-U1-D2"]["expected_answer"]["text"], "do")
        self.assertEqual(self.by_id["MJ5-U1-D3"]["expected_answer"]["text"], "want")
        self.assertEqual(self.by_id["MJ5-U1-D4"]["expected_answer"]["text"], "they")

    def test_e4_blanks_and_regions(self) -> None:
        question = self.by_id["MJ5-U1-E4"]
        self.assertEqual(question["expected_answer"], ["Do", "don't"])
        self.assertEqual(len(question["answer_regions"]), 2)
        self.assertEqual(
            [region["region_id"] for region in question["answer_regions"]],
            ["MJ5-U1-E4-B1", "MJ5-U1-E4-B2"],
        )

    def test_f2_blanks_and_regions(self) -> None:
        question = self.by_id["MJ5-U1-F2"]
        self.assertEqual(question["expected_answer"], ["Yes", "we", "like", "milk"])
        self.assertEqual(len(question["answer_regions"]), 4)

    def test_f3_blanks_and_regions(self) -> None:
        question = self.by_id["MJ5-U1-F3"]
        self.assertEqual(
            question["expected_answer"],
            ["they", "do", "not", "They", "mango", "juice"],
        )
        self.assertEqual(len(question["answer_regions"]), 6)

    def test_selection_questions_have_options(self) -> None:
        for question in self.questions:
            if question["response_mode"] == "handwriting":
                continue
            options = [
                region
                for region in question["answer_regions"]
                if "option_id" in region
            ]
            self.assertGreaterEqual(len(options), 2, question["question_id"])
            for region in options:
                self.assertIn("expected_selected", region, question["question_id"])

    def test_handwriting_blanks_match_region_count(self) -> None:
        for question in self.questions:
            if question["response_mode"] != "handwriting":
                continue
            blanks = question["expected_answer"]
            self.assertIsInstance(blanks, list, question["question_id"])
            self.assertEqual(
                len(blanks),
                len(question["answer_regions"]),
                question["question_id"],
            )

    def test_all_physical_coordinates_are_normalized_and_in_bounds(self) -> None:
        from app.services.regions import region_is_uncalibrated, validate_normalized_region

        for question in self.questions:
            for region in question["answer_regions"]:
                if region_is_uncalibrated(region):
                    self.assertTrue(
                        question["question_id"].startswith("MJ5-U1-C"),
                        region["region_id"],
                    )
                    continue
                validate_normalized_region(region)

    def test_region_ids_are_unique_across_assignment(self) -> None:
        ids = [
            region["region_id"]
            for question in self.questions
            for region in question["answer_regions"]
        ]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 59)

    def test_option_and_blank_relationships_remain_valid(self) -> None:
        for question in self.questions:
            if question["response_mode"] == "handwriting":
                numbers = [region["blank_number"] for region in question["answer_regions"]]
                self.assertEqual(numbers, list(range(1, len(numbers) + 1)))
                for region in question["answer_regions"]:
                    self.assertNotIn("option_id", region)
                    self.assertTrue(region["region_id"].endswith(f"-B{region['blank_number']}"))
            else:
                for region in question["answer_regions"]:
                    if "option_id" not in region:
                        self.assertTrue(
                            str(region.get("region_id", "")).endswith("-INPUT"),
                            region.get("region_id"),
                        )
                        continue
                    self.assertEqual(region["region_id"], region["option_id"])
                    self.assertIn("expected_selected", region)

    def test_c_has_one_physical_input_and_keeps_option_records(self) -> None:
        from app.services.regions import region_is_uncalibrated

        for question_id in ("MJ5-U1-C1", "MJ5-U1-C2"):
            question = self.by_id[question_id]
            physical = [
                region
                for region in question["answer_regions"]
                if not region_is_uncalibrated(region)
            ]
            options = [
                region
                for region in question["answer_regions"]
                if region.get("option_id")
            ]
            self.assertEqual(len(physical), 1, question_id)
            self.assertEqual(physical[0]["region_id"], f"{question_id}-INPUT")
            self.assertEqual(len(options), 3, question_id)
            self.assertEqual(
                [region["choice_letter"] for region in options],
                ["A", "B", "C"],
            )

    def test_golden_dataset_expected_answers_unchanged(self) -> None:
        self.assertEqual(set(self.by_id), set(GOLDEN_EXPECTED_ANSWERS))
        self.assertEqual(
            {qid: self.by_id[qid]["expected_answer"] for qid in GOLDEN_EXPECTED_ANSWERS},
            GOLDEN_EXPECTED_ANSWERS,
        )
        selected = {
            region["region_id"]: region["expected_selected"]
            for question in self.questions
            if question["response_mode"] != "handwriting"
            for region in question["answer_regions"]
            if "expected_selected" in region
        }
        self.assertEqual(selected, GOLDEN_EXPECTED_SELECTED)

    def test_assignment_pages_structure(self) -> None:
        pages = self.data["assignment_pages"]
        self.assertEqual(expected_pages_per_student(self.data), len(pages))
        self.assertEqual(len(pages), 3)
        self.assertNotIn("pages_per_student", self.data)
        self.assertNotIn("assignment_page_count", self.data)
        self.assertEqual(
            [
                (
                    page["assignment_page_id"],
                    page["sequence"],
                    page["workbook_page"],
                    page["sections"],
                    page["template_image"],
                )
                for page in pages
            ],
            [
                ("MJ5-U1-P1", 1, 4, ["A", "B"], "templates/MJ5-U1-P1.png"),
                ("MJ5-U1-P2", 2, 5, ["C", "D"], "templates/MJ5-U1-P2.png"),
                ("MJ5-U1-P3", 3, 6, ["E", "F"], "templates/MJ5-U1-P3.png"),
            ],
        )

    def test_questions_map_to_assignment_pages_by_workbook_page(self) -> None:
        by_workbook = {
            page["workbook_page"]: page for page in self.data["assignment_pages"]
        }
        expected_workbook = {
            "A": 4,
            "B": 4,
            "C": 5,
            "D": 5,
            "E": 6,
            "F": 6,
        }
        for question in self.questions:
            section = question["section"]
            self.assertEqual(question["page_number"], expected_workbook[section])
            page = by_workbook[question["page_number"]]
            self.assertIn(section, page["sections"])


class HypotheticalFourPageAssignmentTests(unittest.TestCase):
    """Fixture only. Not a real textbook or answer key."""

    def test_four_page_unit_count_is_derived_from_assignment_pages(self) -> None:
        sample = {
            "assignment_id": "FIXTURE-ONLY-four-page-unit",
            "textbook_id": "fixture-only-textbook",
            "unit_id": "fixture-unit",
            "sections": [
                {"section_id": "A", "title": "A"},
                {"section_id": "B", "title": "B"},
                {"section_id": "C", "title": "C"},
                {"section_id": "D", "title": "D"},
                {"section_id": "E", "title": "E"},
                {"section_id": "F", "title": "F"},
                {"section_id": "G", "title": "G"},
                {"section_id": "H", "title": "H"},
            ],
            "assignment_pages": [
                {
                    "assignment_page_id": "FIX-P1",
                    "sequence": 1,
                    "workbook_page": 10,
                    "sections": ["A", "B"],
                },
                {
                    "assignment_page_id": "FIX-P2",
                    "sequence": 2,
                    "workbook_page": 11,
                    "sections": ["C", "D"],
                },
                {
                    "assignment_page_id": "FIX-P3",
                    "sequence": 3,
                    "workbook_page": 12,
                    "sections": ["E", "F"],
                },
                {
                    "assignment_page_id": "FIX-P4",
                    "sequence": 4,
                    "workbook_page": 13,
                    "sections": ["G", "H"],
                },
            ],
            "questions": [],
        }
        validate_assignment_structure(sample)
        self.assertEqual(expected_pages_per_student(sample), 4)
        self.assertEqual(expected_pages_per_student(sample), len(sample["assignment_pages"]))
        self.assertNotEqual(expected_pages_per_student(sample), 3)

    def test_question_on_fourth_page_maps_without_hard_coded_count(self) -> None:
        sample = {
            "assignment_id": "FIXTURE-ONLY-four-page-unit",
            "textbook_id": "fixture-only-textbook",
            "unit_id": "fixture-unit",
            "sections": [
                {"section_id": "A", "title": "A"},
                {"section_id": "H", "title": "H"},
            ],
            "assignment_pages": [
                {
                    "assignment_page_id": "FIX-P1",
                    "sequence": 1,
                    "workbook_page": 10,
                    "sections": ["A"],
                },
                {
                    "assignment_page_id": "FIX-P2",
                    "sequence": 2,
                    "workbook_page": 11,
                    "sections": ["A"],
                },
                {
                    "assignment_page_id": "FIX-P3",
                    "sequence": 3,
                    "workbook_page": 12,
                    "sections": ["A"],
                },
                {
                    "assignment_page_id": "FIX-P4",
                    "sequence": 4,
                    "workbook_page": 13,
                    "sections": ["H"],
                },
            ],
            "questions": [
                {
                    "question_id": "FIX-H1",
                    "section": "H",
                    "question_number": 1,
                    "question_type": "fill_in",
                    "response_mode": "handwriting",
                    "grading_strategy": "multi_blank",
                    "expected_answer": ["placeholder"],
                    "page_number": 13,
                    "answer_regions": [{"region_id": "FIX-H1-B1"}],
                    "notes": "PLACEHOLDER — not textbook content",
                }
            ],
        }
        validate_assignment_structure(sample)
        self.assertEqual(expected_pages_per_student(sample), 4)


if __name__ == "__main__":
    unittest.main()
