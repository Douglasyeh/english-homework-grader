"""Positional student-group mapping. No OCR, names, or image inspection."""

from __future__ import annotations

from typing import Any

GROUPING_GROUPED = "grouped"
GROUPING_NEEDS_REVIEW = "needs_manual_review"


def expected_pages_per_student(assignment_pages: list[dict[str, Any]]) -> int:
    return len(assignment_pages)


def _ordered_assignment_pages(
    assignment_pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(assignment_pages, key=lambda page: int(page["sequence"]))


def _student_group_id(group_number: int) -> str:
    return f"group-{group_number:03d}"


def _map_group_pages(
    uploaded_chunk: list[dict[str, Any]],
    ordered_assignment_pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mapped: list[dict[str, Any]] = []
    for offset, uploaded in enumerate(uploaded_chunk):
        assignment_page = ordered_assignment_pages[offset]
        mapped.append(
            {
                "page_index": uploaded["page_index"],
                "page_number": uploaded["page_number"],
                "image_url": uploaded.get("image_url"),
                "assignment_page_id": assignment_page["assignment_page_id"],
                "assignment_page_sequence": assignment_page["sequence"],
                "workbook_page": assignment_page["workbook_page"],
            }
        )
    return mapped


def _make_group(
    group_number: int,
    uploaded_chunk: list[dict[str, Any]],
    ordered_assignment_pages: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "student_group_id": _student_group_id(group_number),
        "group_number": group_number,
        "pages": _map_group_pages(uploaded_chunk, ordered_assignment_pages),
    }


def group_uploaded_pages(
    uploaded_pages: list[dict[str, Any]],
    assignment_pages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Map ordered PDF pages onto assignment_pages in repeating sequence.

    Positional MVP only. Does not inspect images or identify students.
    Incomplete page counts are never silently repaired.
    """
    ordered = _ordered_assignment_pages(assignment_pages)
    expected = expected_pages_per_student(ordered)
    page_count = len(uploaded_pages)

    if expected == 0:
        return {
            "grouping_status": GROUPING_NEEDS_REVIEW,
            "expected_pages_per_student": 0,
            "group_count": 0,
            "complete_group_count": 0,
            "remaining_page_count": page_count,
            "student_groups": [],
            "provisional_groups": [],
            "remaining_pages": list(uploaded_pages),
        }

    remainder = page_count % expected
    complete_group_count = page_count // expected

    complete_chunks: list[dict[str, Any]] = []
    for group_number in range(1, complete_group_count + 1):
        start = (group_number - 1) * expected
        chunk = uploaded_pages[start : start + expected]
        complete_chunks.append(_make_group(group_number, chunk, ordered))

    if remainder == 0:
        return {
            "grouping_status": GROUPING_GROUPED,
            "expected_pages_per_student": expected,
            "group_count": complete_group_count,
            "complete_group_count": complete_group_count,
            "remaining_page_count": 0,
            "student_groups": complete_chunks,
            "provisional_groups": [],
            "remaining_pages": [],
        }

    leftover = uploaded_pages[complete_group_count * expected :]
    return {
        "grouping_status": GROUPING_NEEDS_REVIEW,
        "expected_pages_per_student": expected,
        "group_count": 0,
        "complete_group_count": complete_group_count,
        "remaining_page_count": remainder,
        "student_groups": [],
        "provisional_groups": complete_chunks,
        "remaining_pages": list(leftover),
    }
