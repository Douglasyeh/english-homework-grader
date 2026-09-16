"""Normalized answer-region coordinates on the canonical template page.

Coordinates answer WHERE to inspect. They do not encode the student's answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PIL import Image


class RegionError(ValueError):
    """Invalid normalized region or crop request."""


@dataclass(frozen=True)
class PixelRegion:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def as_box(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)


def region_is_uncalibrated(region: dict[str, Any]) -> bool:
    return all(region.get(key) is None for key in ("x", "y", "width", "height"))


def validate_normalized_region(region: dict[str, Any]) -> dict[str, float]:
    required = ("x", "y", "width", "height")
    values: dict[str, float] = {}
    for key in required:
        raw = region.get(key)
        if not isinstance(raw, (int, float)) or isinstance(raw, bool):
            raise RegionError(f"{key} must be a number between 0.0 and 1.0")
        value = float(raw)
        if value < 0.0 or value > 1.0:
            raise RegionError(f"{key} must be between 0.0 and 1.0")
        values[key] = value
    if values["width"] <= 0.0:
        raise RegionError("width must be greater than 0")
    if values["height"] <= 0.0:
        raise RegionError("height must be greater than 0")
    if values["x"] + values["width"] > 1.0 + 1e-9:
        raise RegionError("x + width must be <= 1.0")
    if values["y"] + values["height"] > 1.0 + 1e-9:
        raise RegionError("y + height must be <= 1.0")
    return values


def normalized_region_to_pixels(
    region: dict[str, Any],
    image_width: int,
    image_height: int,
) -> PixelRegion:
    if image_width <= 0 or image_height <= 0:
        raise RegionError("image dimensions must be positive")
    values = validate_normalized_region(region)
    left = int(round(values["x"] * image_width))
    top = int(round(values["y"] * image_height))
    right = int(round((values["x"] + values["width"]) * image_width))
    bottom = int(round((values["y"] + values["height"]) * image_height))
    left = max(0, min(left, image_width - 1))
    top = max(0, min(top, image_height - 1))
    right = max(left + 1, min(right, image_width))
    bottom = max(top + 1, min(bottom, image_height))
    return PixelRegion(
        left=left,
        top=top,
        width=right - left,
        height=bottom - top,
    )


def template_region_to_aligned_pixels(
    region: dict[str, Any],
    aligned_width: int,
    aligned_height: int,
    transform: dict[str, Any] | None = None,
) -> PixelRegion:
    """Map template-normalized coords onto an aligned page.

    Coordinates are canonical on the template. A student PNG may be used
    only after a geometric transform has placed it in that frame.
    ``transform is None`` means identity on an already-aligned (or template)
    image. Non-identity transforms are not implemented yet.
    """
    if transform is not None:
        raise RegionError(
            "non-identity alignment transforms are not implemented; "
            "do not apply template coordinates to an unaligned student page"
        )
    return normalized_region_to_pixels(region, aligned_width, aligned_height)


def assignment_page_id_for_question(
    assignment: dict[str, Any],
    question: dict[str, Any],
) -> str:
    workbook_page = question.get("page_number")
    for page in assignment.get("assignment_pages") or []:
        if page.get("workbook_page") == workbook_page:
            page_id = page.get("assignment_page_id")
            if isinstance(page_id, str) and page_id:
                return page_id
    raise RegionError(
        f"no assignment page for workbook page {workbook_page!r} "
        f"({question.get('question_id')})"
    )


def iter_answer_regions(
    assignment: dict[str, Any],
) -> list[tuple[dict[str, Any], dict[str, Any], str]]:
    rows: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    for question in assignment.get("questions") or []:
        if not isinstance(question, dict):
            continue
        page_id = assignment_page_id_for_question(assignment, question)
        for region in question.get("answer_regions") or []:
            if isinstance(region, dict):
                rows.append((question, region, page_id))
    return rows


def crop_answer_region(aligned_page: Image.Image, region: dict[str, Any]) -> Image.Image:
    pixels = normalized_region_to_pixels(
        region,
        aligned_page.width,
        aligned_page.height,
    )
    return aligned_page.crop(pixels.as_box())
