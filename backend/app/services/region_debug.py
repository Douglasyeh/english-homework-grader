"""Human-verification overlays and crops. No recognition or grading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.services.assignment_data import load_assignment
from app.services.page_alignment import canonical_template_path
from app.services.regions import (
    RegionError,
    crop_answer_region,
    iter_answer_regions,
    normalized_region_to_pixels,
    region_is_uncalibrated,
)


def region_label(question_id: str, region: dict[str, Any]) -> str:
    option_id = region.get("option_id")
    if option_id:
        return f"{question_id}/{option_id}"
    blank = region.get("blank_number")
    if blank is not None:
        return f"{question_id}/B{blank}"
    return str(region.get("region_id") or question_id)


def _overlay_font(size: int = 14):
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_region_overlay(
    aligned_page: Image.Image,
    labeled_regions: list[tuple[str, dict[str, Any]]],
) -> Image.Image:
    overlay = aligned_page.convert("RGB").copy()
    draw = ImageDraw.Draw(overlay)
    font = _overlay_font()
    for label, region in labeled_regions:
        pixels = normalized_region_to_pixels(region, overlay.width, overlay.height)
        draw.rectangle(pixels.as_box(), outline=(220, 0, 0), width=3)
        text_y = max(0, pixels.top - 14)
        draw.text((pixels.left + 2, text_y), label, fill=(220, 0, 0), font=font)
    return overlay


def save_region_overlay(
    aligned_page: Image.Image,
    labeled_regions: list[tuple[str, dict[str, Any]]],
    dest: Path,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    image = draw_region_overlay(aligned_page, labeled_regions)
    image.save(dest, format="PNG")
    return dest


def save_region_crop(
    aligned_page: Image.Image,
    region: dict[str, Any],
    dest: Path,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    crop = crop_answer_region(aligned_page, region)
    if crop.width <= 0 or crop.height <= 0:
        raise RegionError("crop produced an empty image")
    crop.save(dest, format="PNG")
    return dest


def labeled_regions_for_assignment_page(
    assignment: dict[str, Any],
    assignment_page_id: str,
) -> list[tuple[str, dict[str, Any]]]:
    labeled: list[tuple[str, dict[str, Any]]] = []
    for _question, region, page_id in iter_answer_regions(assignment):
        if page_id != assignment_page_id:
            continue
        if region_is_uncalibrated(region):
            continue
        region_id = region.get("region_id")
        if not isinstance(region_id, str) or not region_id:
            raise RegionError("answer region is missing region_id")
        labeled.append((region_id, region))
    return labeled


def template_overlay_dest(template_path: Path) -> Path:
    return template_path.parent / "debug" / f"{template_path.stem}-overlay.png"


def generate_unit_template_overlays(
    textbook_id: str,
    unit_id: str,
    dest_dir: Path | None = None,
) -> list[Path]:
    """Draw every configured region_id on each canonical template page."""
    assignment = load_assignment(textbook_id, unit_id)
    written: list[Path] = []
    for page in assignment.get("assignment_pages") or []:
        page_id = page.get("assignment_page_id")
        template_rel = page.get("template_image")
        template_path = canonical_template_path(textbook_id, unit_id, template_rel)
        if template_path is None or not template_path.is_file():
            raise RegionError(f"missing canonical template for {page_id}")
        labeled = labeled_regions_for_assignment_page(assignment, page_id)
        dest = (
            Path(dest_dir) / f"{template_path.stem}-overlay.png"
            if dest_dir is not None
            else template_overlay_dest(template_path)
        )
        with Image.open(template_path) as template:
            save_region_overlay(template, labeled, dest)
        written.append(dest)
    return written
