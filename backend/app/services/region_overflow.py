"""Runtime crop geometry for handwriting that overflows a printed blank.

Canonical coordinates in assignment.json stay unchanged. Padded, ink-expanded,
and max regions are derived at crop time. No OCR or recognition.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Mapping

from PIL import Image

from app.services.regions import (
    PixelRegion,
    RegionError,
    normalized_region_to_pixels,
    validate_normalized_region,
)

CROP_OK = "ok"
CROP_NEEDS_MANUAL_REVIEW = "needs_manual_review"

REVIEW_EXCEEDS_MAX = (
    "expanded region reaches max_region but handwriting still continues"
)
REVIEW_NEIGHBOR_AMBIGUITY = (
    "ink crosses two neighboring answer regions ambiguously"
)
REVIEW_CONNECTED_BLANKS = "two blanks appear connected"

# Page-normalized insets. Not written into assignment.json.
DEFAULT_PADDING: dict[str, dict[str, float]] = {
    "handwriting": {"left": 0.012, "right": 0.012, "top": 0.018, "bottom": 0.012},
    "circle_selection": {"left": 0.010, "right": 0.010, "top": 0.010, "bottom": 0.010},
    "check_selection": {"left": 0.006, "right": 0.006, "top": 0.006, "bottom": 0.006},
}

DEFAULT_MAX_PADDING: dict[str, dict[str, float]] = {
    "handwriting": {"left": 0.04, "right": 0.04, "top": 0.045, "bottom": 0.03},
    "circle_selection": {"left": 0.02, "right": 0.02, "top": 0.02, "bottom": 0.02},
    "check_selection": {"left": 0.012, "right": 0.012, "top": 0.012, "bottom": 0.012},
}

PAGE_BOUNDS = {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}


def _as_region(x: float, y: float, width: float, height: float) -> dict[str, float]:
    return {"x": x, "y": y, "width": width, "height": height}


def _right(region: Mapping[str, float]) -> float:
    return float(region["x"]) + float(region["width"])


def _bottom(region: Mapping[str, float]) -> float:
    return float(region["y"]) + float(region["height"])


def normalize_padding(padding: float | Mapping[str, float]) -> dict[str, float]:
    if isinstance(padding, (int, float)) and not isinstance(padding, bool):
        value = float(padding)
        if value < 0:
            raise RegionError("padding must be >= 0")
        return {"left": value, "right": value, "top": value, "bottom": value}
    if not isinstance(padding, Mapping):
        raise RegionError("padding must be a number or {left,right,top,bottom}")
    values = {}
    for key in ("left", "right", "top", "bottom"):
        raw = padding.get(key, 0.0)
        if not isinstance(raw, (int, float)) or isinstance(raw, bool) or float(raw) < 0:
            raise RegionError(f"padding.{key} must be a number >= 0")
        values[key] = float(raw)
    return values


def padding_for_response_mode(response_mode: str) -> dict[str, float]:
    try:
        return dict(DEFAULT_PADDING[response_mode])
    except KeyError as exc:
        raise RegionError(f"unknown response_mode for padding: {response_mode}") from exc


def max_padding_for_response_mode(response_mode: str) -> dict[str, float]:
    try:
        return dict(DEFAULT_MAX_PADDING[response_mode])
    except KeyError as exc:
        raise RegionError(f"unknown response_mode for max padding: {response_mode}") from exc


def expand_region_with_padding(
    canonical_region: Mapping[str, Any],
    padding: float | Mapping[str, float],
    bounds: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    """Grow a canonical region by page-normalized padding, clipped to bounds."""
    canonical = validate_normalized_region(canonical_region)
    pad = normalize_padding(padding)
    limit = validate_normalized_region(bounds or PAGE_BOUNDS)
    x = canonical["x"] - pad["left"]
    y = canonical["y"] - pad["top"]
    right = _right(canonical) + pad["right"]
    bottom = _bottom(canonical) + pad["bottom"]
    return constrain_region(_as_region(x, y, right - x, bottom - y), limit)


def constrain_region(
    region: Mapping[str, Any],
    max_region: Mapping[str, Any],
) -> dict[str, float]:
    """Intersect region with max_region. Empty intersection is an error."""
    source = {
        "x": float(region["x"]),
        "y": float(region["y"]),
        "width": float(region["width"]),
        "height": float(region["height"]),
    }
    limit = validate_normalized_region(max_region)
    x = max(source["x"], limit["x"])
    y = max(source["y"], limit["y"])
    right = min(_right(source), _right(limit))
    bottom = min(_bottom(source), _bottom(limit))
    if right <= x + 1e-12 or bottom <= y + 1e-12:
        raise RegionError("constrained region is empty")
    clipped = _as_region(x, y, right - x, bottom - y)
    return validate_normalized_region(clipped)


def union_regions(regions: list[Mapping[str, Any]]) -> dict[str, float]:
    if not regions:
        raise RegionError("union requires at least one region")
    validated = [validate_normalized_region(region) for region in regions]
    x = min(item["x"] for item in validated)
    y = min(item["y"] for item in validated)
    right = max(_right(item) for item in validated)
    bottom = max(_bottom(item) for item in validated)
    return validate_normalized_region(_as_region(x, y, right - x, bottom - y))


def regions_overlap(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    a = validate_normalized_region(left)
    b = validate_normalized_region(right)
    return not (
        _right(a) <= b["x"] + 1e-12
        or _right(b) <= a["x"] + 1e-12
        or _bottom(a) <= b["y"] + 1e-12
        or _bottom(b) <= a["y"] + 1e-12
    )


def region_contains(outer: Mapping[str, Any], inner: Mapping[str, Any]) -> bool:
    a = validate_normalized_region(outer)
    b = validate_normalized_region(inner)
    return (
        b["x"] >= a["x"] - 1e-9
        and b["y"] >= a["y"] - 1e-9
        and _right(b) <= _right(a) + 1e-9
        and _bottom(b) <= _bottom(a) + 1e-9
    )


def pixel_region_to_normalized(
    pixels: PixelRegion,
    image_width: int,
    image_height: int,
) -> dict[str, float]:
    if image_width <= 0 or image_height <= 0:
        raise RegionError("image dimensions must be positive")
    return validate_normalized_region(
        _as_region(
            pixels.left / image_width,
            pixels.top / image_height,
            pixels.width / image_width,
            pixels.height / image_height,
        )
    )


def max_region_for_canonical(
    canonical_region: Mapping[str, Any],
    neighbors: list[Mapping[str, Any]] | None = None,
    bounds: Mapping[str, Any] | None = None,
    max_padding: float | Mapping[str, float] | None = None,
    response_mode: str = "handwriting",
) -> dict[str, float]:
    """Safety box: generous pad, then stop before neighboring canonical regions."""
    canonical = validate_normalized_region(canonical_region)
    limit = validate_normalized_region(bounds or PAGE_BOUNDS)
    pad = (
        normalize_padding(max_padding)
        if max_padding is not None
        else max_padding_for_response_mode(response_mode)
    )
    generous = expand_region_with_padding(canonical, pad, limit)
    x, y, right, bottom = (
        generous["x"],
        generous["y"],
        _right(generous),
        _bottom(generous),
    )
    cx_mid = canonical["x"] + canonical["width"] / 2.0
    cy_mid = canonical["y"] + canonical["height"] / 2.0
    for neighbor in neighbors or []:
        other = validate_normalized_region(neighbor)
        ox_mid = other["x"] + other["width"] / 2.0
        oy_mid = other["y"] + other["height"] / 2.0
        if abs(ox_mid - cx_mid) >= abs(oy_mid - cy_mid):
            if other["x"] >= _right(canonical):
                midpoint = (_right(canonical) + other["x"]) / 2.0
                right = min(right, midpoint)
            elif _right(other) <= canonical["x"]:
                midpoint = (_right(other) + canonical["x"]) / 2.0
                x = max(x, midpoint)
        else:
            if other["y"] >= _bottom(canonical):
                midpoint = (_bottom(canonical) + other["y"]) / 2.0
                bottom = min(bottom, midpoint)
            elif _bottom(other) <= canonical["y"]:
                midpoint = (_bottom(other) + canonical["y"]) / 2.0
                y = max(y, midpoint)
    return constrain_region(_as_region(x, y, right - x, bottom - y), limit)


def question_fallback_region(
    blank_regions: list[Mapping[str, Any]],
    padding: float | Mapping[str, float] | None = None,
    bounds: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    """Union of per-blank canonical regions, then padded. Does not replace blanks."""
    combined = union_regions(list(blank_regions))
    pad = (
        normalize_padding(padding)
        if padding is not None
        else padding_for_response_mode("handwriting")
    )
    return expand_region_with_padding(combined, pad, bounds or PAGE_BOUNDS)


def expand_region_toward_ink(
    padded_region: Mapping[str, Any],
    max_region: Mapping[str, Any],
    ink_mask: Image.Image,
    *,
    proximity_px: int = 2,
    ink_threshold: int = 128,
) -> tuple[dict[str, float], bool]:
    """Grow padded_region toward nearby/connected ink, never past max_region.

    ``ink_mask`` is a page-sized image: dark pixels are ink. Returns
    (expanded_region, ink_continues_past_max).
    """
    padded = validate_normalized_region(padded_region)
    limited = validate_normalized_region(max_region)
    constrained_padded = constrain_region(padded, limited)
    gray = ink_mask.convert("L")
    width, height = gray.size
    padded_px = normalized_region_to_pixels(constrained_padded, width, height)
    max_px = normalized_region_to_pixels(limited, width, height)

    pixels = gray.load()
    visited = set()
    queue: deque[tuple[int, int]] = deque()

    def is_ink(x: int, y: int) -> bool:
        return int(pixels[x, y]) < ink_threshold

    def in_max(x: int, y: int) -> bool:
        return max_px.left <= x < max_px.right and max_px.top <= y < max_px.bottom

    def near_or_in_padded(x: int, y: int) -> bool:
        if padded_px.left <= x < padded_px.right and padded_px.top <= y < padded_px.bottom:
            return True
        dx = 0
        if x < padded_px.left:
            dx = padded_px.left - x
        elif x >= padded_px.right:
            dx = x - (padded_px.right - 1)
        dy = 0
        if y < padded_px.top:
            dy = padded_px.top - y
        elif y >= padded_px.bottom:
            dy = y - (padded_px.bottom - 1)
        return dx * dx + dy * dy <= proximity_px * proximity_px

    for y in range(max_px.top, max_px.bottom):
        for x in range(max_px.left, max_px.right):
            if is_ink(x, y) and near_or_in_padded(x, y):
                queue.append((x, y))
                visited.add((x, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if (nx, ny) in visited or not in_max(nx, ny):
                continue
            if is_ink(nx, ny):
                visited.add((nx, ny))
                queue.append((nx, ny))

    ink_past_max = False
    for y in range(max(0, max_px.top - 1), min(height, max_px.bottom + 1)):
        for x in range(max(0, max_px.left - 1), min(width, max_px.right + 1)):
            if in_max(x, y) or not is_ink(x, y):
                continue
            if near_or_in_padded(x, y) or any(
                (ax, ay) in visited
                for ax, ay in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            ):
                ink_past_max = True
                break
        if ink_past_max:
            break

    if not visited:
        return constrained_padded, ink_past_max

    xs = [x for x, _y in visited]
    ys = [y for _x, y in visited]
    ink_box = PixelRegion(
        left=min(min(xs), padded_px.left),
        top=min(min(ys), padded_px.top),
        width=max(max(xs) + 1, padded_px.right) - min(min(xs), padded_px.left),
        height=max(max(ys) + 1, padded_px.bottom) - min(min(ys), padded_px.top),
    )
    expanded = pixel_region_to_normalized(ink_box, width, height)
    return constrain_region(expanded, limited), ink_past_max


@dataclass(frozen=True)
class RuntimeCropPlan:
    canonical_region: dict[str, float]
    padded_region: dict[str, float]
    ink_expanded_region: dict[str, float] | None
    max_region: dict[str, float]
    crop_region: dict[str, float]
    status: str
    review_reasons: tuple[str, ...]


def plan_runtime_crop(
    canonical_region: Mapping[str, Any],
    *,
    response_mode: str = "handwriting",
    neighbors: list[Mapping[str, Any]] | None = None,
    bounds: Mapping[str, Any] | None = None,
    ink_mask: Image.Image | None = None,
    padding: float | Mapping[str, float] | None = None,
    max_padding: float | Mapping[str, float] | None = None,
) -> RuntimeCropPlan:
    """Derive runtime crops from a stored canonical region.

    Does not mutate ``canonical_region``.
    """
    canonical = validate_normalized_region(canonical_region)
    page = bounds or PAGE_BOUNDS
    pad = padding_for_response_mode(response_mode) if padding is None else padding
    padded = expand_region_with_padding(canonical, pad, page)
    max_box = max_region_for_canonical(
        canonical,
        neighbors=neighbors,
        bounds=page,
        max_padding=max_padding,
        response_mode=response_mode,
    )
    padded = constrain_region(padded, max_box)
    reasons: list[str] = []
    ink_expanded: dict[str, float] | None = None
    crop = padded
    if ink_mask is not None:
        expanded, past_max = expand_region_toward_ink(padded, max_box, ink_mask)
        ink_expanded = expanded
        crop = expanded
        if past_max:
            reasons.append(REVIEW_EXCEEDS_MAX)
        for neighbor in neighbors or []:
            if regions_overlap(expanded, neighbor):
                reasons.append(REVIEW_NEIGHBOR_AMBIGUITY)
                reasons.append(REVIEW_CONNECTED_BLANKS)
                break
    status = CROP_NEEDS_MANUAL_REVIEW if reasons else CROP_OK
    unique_reasons = tuple(dict.fromkeys(reasons))
    return RuntimeCropPlan(
        canonical_region=dict(canonical),
        padded_region=padded,
        ink_expanded_region=ink_expanded,
        max_region=max_box,
        crop_region=crop,
        status=status,
        review_reasons=unique_reasons,
    )


def crop_from_plan(aligned_page: Image.Image, plan: RuntimeCropPlan) -> Image.Image:
    pixels = normalized_region_to_pixels(
        plan.crop_region,
        aligned_page.width,
        aligned_page.height,
    )
    return aligned_page.crop(pixels.as_box())
