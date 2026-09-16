"""Synthetic overflow-crop tests. No real student pages or OCR."""

from __future__ import annotations

import copy
import unittest

from PIL import Image, ImageDraw

from app.services.assignment_data import load_assignment
from app.services.region_overflow import (
    CROP_NEEDS_MANUAL_REVIEW,
    CROP_OK,
    REVIEW_EXCEEDS_MAX,
    constrain_region,
    crop_from_plan,
    expand_region_toward_ink,
    expand_region_with_padding,
    max_region_for_canonical,
    padding_for_response_mode,
    plan_runtime_crop,
    question_fallback_region,
    region_contains,
    regions_overlap,
)
from app.services.regions import validate_normalized_region

# Approved MJ5 Unit 1 Section F canonical boxes. Overflow tests must not rewrite them.
FROZEN_MJ5_F_COORDS = {
    "MJ5-U1-F1-B1": (0.228, 0.722, 0.142, 0.032),
    "MJ5-U1-F1-B2": (0.382, 0.722, 0.168, 0.032),
    "MJ5-U1-F2-B1": (0.115, 0.812, 0.152, 0.034),
    "MJ5-U1-F2-B2": (0.308, 0.812, 0.128, 0.034),
    "MJ5-U1-F2-B3": (0.448, 0.812, 0.128, 0.034),
    "MJ5-U1-F2-B4": (0.588, 0.812, 0.185, 0.034),
    "MJ5-U1-F3-B1": (0.185, 0.886, 0.14, 0.028),
    "MJ5-U1-F3-B2": (0.338, 0.886, 0.142, 0.028),
    "MJ5-U1-F3-B3": (0.492, 0.886, 0.158, 0.028),
    "MJ5-U1-F3-B4": (0.118, 0.928, 0.152, 0.028),
    "MJ5-U1-F3-B5": (0.405, 0.928, 0.145, 0.028),
    "MJ5-U1-F3-B6": (0.562, 0.928, 0.175, 0.028),
}

BLANK = {"x": 0.30, "y": 0.35, "width": 0.20, "height": 0.15}
PAGE = 200


def _white() -> Image.Image:
    return Image.new("L", (PAGE, PAGE), color=255)


def _paint_ink(image: Image.Image, region: dict, color: int = 0) -> None:
    draw = ImageDraw.Draw(image)
    left = int(round(region["x"] * PAGE))
    top = int(round(region["y"] * PAGE))
    right = int(round((region["x"] + region["width"]) * PAGE))
    bottom = int(round((region["y"] + region["height"]) * PAGE))
    draw.rectangle((left, top, right - 1, bottom - 1), fill=color)


def _ink_pixels(image: Image.Image) -> int:
    data = getattr(image, "get_flattened_data", None)
    values = data() if callable(data) else image.getdata()
    return sum(1 for value in values if int(value) < 128)


class OverflowGeometryTests(unittest.TestCase):
    def test_a_handwriting_inside_canonical_uses_padded_crop(self) -> None:
        ink = {"x": 0.32, "y": 0.37, "width": 0.14, "height": 0.10}
        mask = _white()
        _paint_ink(mask, ink)
        plan = plan_runtime_crop(BLANK, ink_mask=mask, padding=0.04, max_padding=0.10)
        self.assertEqual(plan.status, CROP_OK)
        self.assertTrue(region_contains(plan.padded_region, BLANK))
        crop = crop_from_plan(mask.convert("RGB"), plan)
        self.assertGreater(_ink_pixels(crop.convert("L")), 0)
        self.assertEqual(_ink_pixels(crop.convert("L")), _ink_pixels(mask))

    def test_b_slight_overflow_fits_in_padded_crop(self) -> None:
        ink = {"x": 0.27, "y": 0.32, "width": 0.26, "height": 0.21}
        mask = _white()
        _paint_ink(mask, ink)
        plan = plan_runtime_crop(BLANK, ink_mask=mask, padding=0.05, max_padding=0.12)
        self.assertTrue(region_contains(plan.padded_region, ink))
        crop = crop_from_plan(mask.convert("RGB"), plan)
        self.assertEqual(_ink_pixels(crop.convert("L")), _ink_pixels(mask))

    def test_c_overflow_past_padding_can_ink_expand(self) -> None:
        ink = {"x": 0.30, "y": 0.35, "width": 0.34, "height": 0.15}
        mask = _white()
        _paint_ink(mask, ink)
        plan = plan_runtime_crop(BLANK, ink_mask=mask, padding=0.02, max_padding=0.18)
        self.assertIsNotNone(plan.ink_expanded_region)
        self.assertGreater(
            plan.ink_expanded_region["width"],
            plan.padded_region["width"] + 1e-9,
        )
        self.assertTrue(region_contains(plan.max_region, plan.ink_expanded_region))

    def test_d_max_region_stops_before_neighboring_blank(self) -> None:
        left = {"x": 0.10, "y": 0.40, "width": 0.20, "height": 0.12}
        right = {"x": 0.42, "y": 0.40, "width": 0.20, "height": 0.12}
        max_box = max_region_for_canonical(left, neighbors=[right], max_padding=0.20)
        self.assertLessEqual(max_box["x"] + max_box["width"], right["x"] + 1e-9)
        self.assertFalse(region_contains(max_box, right))
        self.assertFalse(regions_overlap(max_box, right))
        ink = {"x": 0.10, "y": 0.40, "width": 0.40, "height": 0.12}
        mask = _white()
        _paint_ink(mask, ink)
        plan = plan_runtime_crop(
            left,
            neighbors=[right],
            ink_mask=mask,
            padding=0.02,
            max_padding=0.20,
        )
        self.assertFalse(region_contains(plan.crop_region, right))
        self.assertLessEqual(
            plan.crop_region["x"] + plan.crop_region["width"],
            right["x"] + 1e-9,
        )

    def test_e_padding_clips_to_page_edge(self) -> None:
        edge = {"x": 0.93, "y": 0.92, "width": 0.06, "height": 0.07}
        padded = expand_region_with_padding(edge, 0.05)
        validate_normalized_region(padded)
        self.assertGreaterEqual(padded["x"], 0.0)
        self.assertGreaterEqual(padded["y"], 0.0)
        self.assertLessEqual(padded["x"] + padded["width"], 1.0 + 1e-9)
        self.assertLessEqual(padded["y"] + padded["height"], 1.0 + 1e-9)

    def test_f_adjacent_canonical_coords_stay_unchanged(self) -> None:
        a = {"x": 0.20, "y": 0.50, "width": 0.12, "height": 0.08}
        b = {"x": 0.36, "y": 0.50, "width": 0.12, "height": 0.08}
        snapshot_a = copy.deepcopy(a)
        snapshot_b = copy.deepcopy(b)
        mask = _white()
        _paint_ink(mask, {"x": 0.18, "y": 0.48, "width": 0.20, "height": 0.12})
        plan_runtime_crop(a, neighbors=[b], ink_mask=mask, padding=0.03, max_padding=0.08)
        plan_runtime_crop(b, neighbors=[a], ink_mask=mask, padding=0.03, max_padding=0.08)
        self.assertEqual(a, snapshot_a)
        self.assertEqual(b, snapshot_b)

    def test_g_oversized_ink_stays_inside_max_and_flags_review(self) -> None:
        canonical = dict(BLANK)
        snapshot = copy.deepcopy(canonical)
        huge = {"x": 0.05, "y": 0.05, "width": 0.80, "height": 0.80}
        mask = _white()
        _paint_ink(mask, huge)
        plan = plan_runtime_crop(
            canonical,
            padding=0.02,
            max_padding=0.08,
            ink_mask=mask,
        )
        self.assertEqual(canonical, snapshot)
        self.assertTrue(region_contains(plan.max_region, plan.crop_region))
        self.assertEqual(plan.status, CROP_NEEDS_MANUAL_REVIEW)
        self.assertIn(REVIEW_EXCEEDS_MAX, plan.review_reasons)

    def test_h_fallback_region_does_not_replace_blanks(self) -> None:
        blanks = [
            {"x": 0.10, "y": 0.70, "width": 0.12, "height": 0.05, "region_id": "B1"},
            {"x": 0.26, "y": 0.70, "width": 0.12, "height": 0.05, "region_id": "B2"},
            {"x": 0.42, "y": 0.70, "width": 0.12, "height": 0.05, "region_id": "B3"},
            {"x": 0.58, "y": 0.70, "width": 0.14, "height": 0.05, "region_id": "B4"},
        ]
        originals = copy.deepcopy(blanks)
        fallback = question_fallback_region(blanks, padding=0.01)
        self.assertEqual(len(blanks), 4)
        self.assertEqual(blanks, originals)
        for blank in blanks:
            self.assertTrue(region_contains(fallback, blank))
        self.assertGreater(fallback["width"], blanks[-1]["x"] + blanks[-1]["width"] - blanks[0]["x"])

    def test_constrain_never_exceeds_max(self) -> None:
        big = {"x": 0.0, "y": 0.0, "width": 0.9, "height": 0.9}
        max_box = {"x": 0.2, "y": 0.2, "width": 0.2, "height": 0.2}
        clipped = constrain_region(big, max_box)
        self.assertEqual(clipped, max_box)

    def test_response_mode_padding_is_not_uniform(self) -> None:
        hand = padding_for_response_mode("handwriting")
        circle = padding_for_response_mode("circle_selection")
        check = padding_for_response_mode("check_selection")
        self.assertGreater(hand["top"], check["top"])
        self.assertGreater(circle["top"], check["top"])
        self.assertNotEqual(hand, circle)
        self.assertNotEqual(circle, check)

    def test_ink_expand_without_mask_keeps_padded(self) -> None:
        plan = plan_runtime_crop(BLANK, padding=0.03, max_padding=0.08)
        self.assertIsNone(plan.ink_expanded_region)
        self.assertEqual(plan.crop_region, plan.padded_region)
        self.assertEqual(plan.status, CROP_OK)

    def test_expand_toward_ink_on_empty_mask(self) -> None:
        padded = expand_region_with_padding(BLANK, 0.02)
        max_box = expand_region_with_padding(BLANK, 0.08)
        expanded, past = expand_region_toward_ink(padded, max_box, _white())
        self.assertEqual(expanded, padded)
        self.assertFalse(past)


class CanonicalDatasetIsolationTests(unittest.TestCase):
    def test_mj5_f_canonical_coordinates_unchanged(self) -> None:
        data = load_assignment("magic-joy-5", "unit-1")
        found: dict[str, tuple[float, float, float, float]] = {}
        for question in data["questions"]:
            for region in question["answer_regions"]:
                region_id = region["region_id"]
                if region_id in FROZEN_MJ5_F_COORDS:
                    found[region_id] = (
                        region["x"],
                        region["y"],
                        region["width"],
                        region["height"],
                    )
                    plan_runtime_crop(region, padding=0.02, max_padding=0.05)
                    self.assertEqual(
                        (region["x"], region["y"], region["width"], region["height"]),
                        FROZEN_MJ5_F_COORDS[region_id],
                    )
        self.assertEqual(set(found), set(FROZEN_MJ5_F_COORDS))
        self.assertEqual(found, FROZEN_MJ5_F_COORDS)

    def test_overflow_helpers_do_not_write_dataset_coords(self) -> None:
        data = load_assignment("magic-joy-5", "unit-1")
        before = copy.deepcopy(
            [
                (region["region_id"], region.get("x"), region.get("y"), region.get("width"), region.get("height"))
                for question in data["questions"]
                for region in question["answer_regions"]
            ]
        )
        blanks = [
            region
            for question in data["questions"]
            if question["question_id"] == "MJ5-U1-F2"
            for region in question["answer_regions"]
        ]
        question_fallback_region(blanks)
        for region in blanks:
            plan_runtime_crop(region, neighbors=[item for item in blanks if item is not region])
        after = [
            (region["region_id"], region.get("x"), region.get("y"), region.get("width"), region.get("height"))
            for question in data["questions"]
            for region in question["answer_regions"]
        ]
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
