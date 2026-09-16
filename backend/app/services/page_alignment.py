"""Align a student page image to a canonical assignment-page template.

Does not run OCR or recognition. Does not treat an unaligned page as aligned.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.assignment_data import TEXTBOOKS_DIR
from app.services.storage import page_image_path

STATUS_ALIGNED = "aligned"
STATUS_TEMPLATE_MISSING = "template_missing"
STATUS_NOT_ALIGNED = "not_aligned"
STATUS_ALIGNMENT_FAILED = "alignment_failed"


def unit_dir(textbook_id: str, unit_id: str) -> Path:
    return TEXTBOOKS_DIR / textbook_id / "units" / unit_id


def canonical_template_path(
    textbook_id: str,
    unit_id: str,
    template_image: str | None,
) -> Path | None:
    if not template_image or not str(template_image).strip():
        return None
    relative = Path(str(template_image).replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        return None
    return unit_dir(textbook_id, unit_id) / relative


def align_page(
    student_page_image: str | Path | None,
    template_page_image: str | Path | None,
) -> dict[str, Any]:
    template_path = Path(template_page_image) if template_page_image else None
    student_path = Path(student_page_image) if student_page_image else None

    if template_path is None or not template_path.is_file():
        return {
            "status": STATUS_TEMPLATE_MISSING,
            "confidence": None,
            "transform": None,
            "aligned_image_path": None,
            "diagnostic": {
                "reason": "Canonical template image is missing",
                "template_page_image": str(template_path) if template_path else None,
            },
        }

    if student_path is None or not student_path.is_file():
        return {
            "status": STATUS_ALIGNMENT_FAILED,
            "confidence": None,
            "transform": None,
            "aligned_image_path": None,
            "diagnostic": {
                "reason": "Student page image is missing",
                "student_page_image": str(student_path) if student_path else None,
            },
        }

    return {
        "status": STATUS_NOT_ALIGNED,
        "confidence": None,
        "transform": None,
        "aligned_image_path": None,
        "diagnostic": {
            "reason": (
                "Template exists, but a geometric alignment transform is not "
                "implemented yet. Template coordinates must not be applied to "
                "the raw student PNG."
            ),
            "student_page_image": str(student_path),
            "template_page_image": str(template_path),
        },
    }


def attach_alignment_to_groups(
    grouping: dict[str, Any],
    *,
    textbook_id: str,
    unit_id: str,
    submission_id: str,
    assignment_pages: list[dict[str, Any]],
) -> dict[str, Any]:
    by_id = {
        page["assignment_page_id"]: page
        for page in assignment_pages
        if page.get("assignment_page_id")
    }
    for key in ("student_groups", "provisional_groups"):
        for group in grouping.get(key) or []:
            for page in group.get("pages") or []:
                assignment_page = by_id.get(page.get("assignment_page_id") or "")
                template_rel = (assignment_page or {}).get("template_image")
                template_path = canonical_template_path(
                    textbook_id,
                    unit_id,
                    template_rel,
                )
                student_path = page_image_path(submission_id, int(page["page_index"]))
                alignment = align_page(student_path, template_path)
                page["alignment_status"] = alignment["status"]
                page["template_image"] = template_rel
                page["aligned_image_url"] = None
                page["debug_overlay_url"] = None
    return grouping
