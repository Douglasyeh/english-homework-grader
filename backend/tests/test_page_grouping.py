"""Positional page grouping tests. No OCR or student identity."""

from __future__ import annotations

import unittest

from app.services.page_grouping import (
    GROUPING_GROUPED,
    GROUPING_NEEDS_REVIEW,
    expected_pages_per_student,
    group_uploaded_pages,
)

MJ5_U1_PAGES = [
    {
        "assignment_page_id": "MJ5-U1-P1",
        "sequence": 1,
        "workbook_page": 4,
        "sections": ["A", "B"],
    },
    {
        "assignment_page_id": "MJ5-U1-P2",
        "sequence": 2,
        "workbook_page": 5,
        "sections": ["C", "D"],
    },
    {
        "assignment_page_id": "MJ5-U1-P3",
        "sequence": 3,
        "workbook_page": 6,
        "sections": ["E", "F"],
    },
]


def _uploaded(count: int) -> list[dict]:
    return [
        {
            "page_index": index,
            "page_number": index + 1,
            "image_url": f"/pages/{index}.png",
        }
        for index in range(count)
    ]


class PageGroupingTests(unittest.TestCase):
    def test_expected_count_is_len_assignment_pages(self) -> None:
        self.assertEqual(expected_pages_per_student(MJ5_U1_PAGES), 3)
        self.assertEqual(expected_pages_per_student(MJ5_U1_PAGES), len(MJ5_U1_PAGES))

    def test_fifteen_pages_make_five_groups_of_three(self) -> None:
        result = group_uploaded_pages(_uploaded(15), MJ5_U1_PAGES)
        self.assertEqual(result["grouping_status"], GROUPING_GROUPED)
        self.assertEqual(result["expected_pages_per_student"], 3)
        self.assertEqual(result["group_count"], 5)
        self.assertEqual(len(result["student_groups"]), 5)
        for group in result["student_groups"]:
            self.assertEqual(len(group["pages"]), 3)

    def test_mapping_repeats_after_each_packet(self) -> None:
        result = group_uploaded_pages(_uploaded(6), MJ5_U1_PAGES)
        groups = result["student_groups"]
        self.assertEqual(groups[0]["pages"][0]["page_index"], 0)
        self.assertEqual(groups[0]["pages"][0]["assignment_page_sequence"], 1)
        self.assertEqual(groups[0]["pages"][1]["page_index"], 1)
        self.assertEqual(groups[0]["pages"][1]["assignment_page_sequence"], 2)
        self.assertEqual(groups[0]["pages"][2]["page_index"], 2)
        self.assertEqual(groups[0]["pages"][2]["assignment_page_sequence"], 3)
        self.assertEqual(groups[1]["pages"][0]["page_index"], 3)
        self.assertEqual(groups[1]["pages"][0]["assignment_page_sequence"], 1)

    def test_mj5_u1_workbook_pages(self) -> None:
        result = group_uploaded_pages(_uploaded(3), MJ5_U1_PAGES)
        pages = result["student_groups"][0]["pages"]
        self.assertEqual(pages[0]["workbook_page"], 4)
        self.assertEqual(pages[1]["workbook_page"], 5)
        self.assertEqual(pages[2]["workbook_page"], 6)
        self.assertEqual(pages[0]["assignment_page_id"], "MJ5-U1-P1")
        self.assertEqual(pages[1]["assignment_page_id"], "MJ5-U1-P2")
        self.assertEqual(pages[2]["assignment_page_id"], "MJ5-U1-P3")

    def test_four_page_assignment_groups_in_sets_of_four(self) -> None:
        assignment_pages = [
            {
                "assignment_page_id": f"FIX-P{index}",
                "sequence": index,
                "workbook_page": 9 + index,
            }
            for index in range(1, 5)
        ]
        result = group_uploaded_pages(_uploaded(8), assignment_pages)
        self.assertEqual(result["grouping_status"], GROUPING_GROUPED)
        self.assertEqual(result["expected_pages_per_student"], 4)
        self.assertEqual(result["group_count"], 2)
        self.assertEqual(len(result["student_groups"][0]["pages"]), 4)
        self.assertEqual(len(result["student_groups"][1]["pages"]), 4)
        self.assertEqual(
            result["student_groups"][1]["pages"][0]["assignment_page_id"],
            "FIX-P1",
        )
        self.assertEqual(result["student_groups"][1]["pages"][0]["page_index"], 4)

    def test_fourteen_pages_need_review_and_keep_all_pages(self) -> None:
        uploaded = _uploaded(14)
        result = group_uploaded_pages(uploaded, MJ5_U1_PAGES)
        self.assertEqual(result["grouping_status"], GROUPING_NEEDS_REVIEW)
        self.assertEqual(result["complete_group_count"], 4)
        self.assertEqual(result["remaining_page_count"], 2)
        self.assertEqual(result["student_groups"], [])
        self.assertEqual(len(result["provisional_groups"]), 4)
        self.assertEqual(len(result["remaining_pages"]), 2)
        kept = [
            page["page_index"]
            for group in result["provisional_groups"]
            for page in group["pages"]
        ] + [page["page_index"] for page in result["remaining_pages"]]
        self.assertEqual(kept, list(range(14)))

    def test_sixteen_pages_need_review_and_keep_all_pages(self) -> None:
        result = group_uploaded_pages(_uploaded(16), MJ5_U1_PAGES)
        self.assertEqual(result["grouping_status"], GROUPING_NEEDS_REVIEW)
        self.assertEqual(result["complete_group_count"], 5)
        self.assertEqual(result["remaining_page_count"], 1)
        self.assertEqual(result["student_groups"], [])
        kept_count = sum(len(group["pages"]) for group in result["provisional_groups"])
        kept_count += len(result["remaining_pages"])
        self.assertEqual(kept_count, 16)

    def test_zero_assignment_pages_does_not_divide(self) -> None:
        result = group_uploaded_pages(_uploaded(6), [])
        self.assertEqual(result["grouping_status"], GROUPING_NEEDS_REVIEW)
        self.assertEqual(result["expected_pages_per_student"], 0)
        self.assertEqual(result["complete_group_count"], 0)
        self.assertEqual(result["remaining_page_count"], 6)
        self.assertEqual(len(result["remaining_pages"]), 6)
        self.assertEqual(result["student_groups"], [])


if __name__ == "__main__":
    unittest.main()
