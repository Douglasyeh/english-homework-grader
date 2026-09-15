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


def load_assignment(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError("assignment.json must contain a JSON object")
    return data


def require_nonempty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{field} must be a non-empty string")


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
            "questions": [
                {
                    "question_id": "PLACEHOLDER_NOT_REAL_E4",
                    "section": "E",
                    "question_number": "4",
                    "question_type": "look_and_write",
                    "response_mode": "handwriting",
                    "grading_strategy": "multi_blank",
                    "expected_answer": ["Do", "don't"],
                    "page_number": None,
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
            "questions": [
                {
                    "question_id": "PLACEHOLDER_NOT_REAL_CIRCLE",
                    "section": "A",
                    "question_number": "1",
                    "question_type": "listen_and_circle",
                    "response_mode": "circle_selection",
                    "grading_strategy": "exact_answer",
                    "expected_answer": {"selected": ["option_2"]},
                    "page_number": None,
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
            regions = question["answer_regions"]
            self.assertGreaterEqual(len(regions), 2, question["question_id"])
            for region in regions:
                self.assertIn("option_id", region, question["question_id"])
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

    def test_all_coordinates_are_null(self) -> None:
        for question in self.questions:
            for region in question["answer_regions"]:
                for field in ("x", "y", "width", "height"):
                    self.assertIsNone(
                        region[field],
                        f"{region.get('region_id')} {field}",
                    )


if __name__ == "__main__":
    unittest.main()
