"""Normalized region math and crops. Synthetic coordinates only."""

from __future__ import annotations

import unittest
from PIL import Image

from app.services.region_debug import draw_region_overlay, region_label, save_region_crop
from app.services.regions import (
    RegionError,
    crop_answer_region,
    normalized_region_to_pixels,
    template_region_to_aligned_pixels,
    validate_normalized_region,
)

VALID = {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.2}


class NormalizedRegionTests(unittest.TestCase):
    def test_valid_region(self) -> None:
        self.assertEqual(
            validate_normalized_region(VALID),
            {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.2},
        )

    def test_invalid_negative_x(self) -> None:
        with self.assertRaises(RegionError):
            validate_normalized_region({**VALID, "x": -0.1})

    def test_invalid_negative_y(self) -> None:
        with self.assertRaises(RegionError):
            validate_normalized_region({**VALID, "y": -0.01})

    def test_invalid_zero_width(self) -> None:
        with self.assertRaises(RegionError):
            validate_normalized_region({**VALID, "width": 0})

    def test_invalid_zero_height(self) -> None:
        with self.assertRaises(RegionError):
            validate_normalized_region({**VALID, "height": 0})

    def test_invalid_x_plus_width(self) -> None:
        with self.assertRaises(RegionError):
            validate_normalized_region(
                {"x": 0.8, "y": 0.1, "width": 0.3, "height": 0.1}
            )

    def test_invalid_y_plus_height(self) -> None:
        with self.assertRaises(RegionError):
            validate_normalized_region(
                {"x": 0.1, "y": 0.8, "width": 0.1, "height": 0.3}
            )

    def test_normalized_to_pixels_example(self) -> None:
        region = {"x": 0.10, "y": 0.20, "width": 0.30, "height": 0.25}
        pixels = normalized_region_to_pixels(region, 1000, 2000)
        self.assertEqual(pixels.left, 100)
        self.assertEqual(pixels.top, 400)
        self.assertEqual(pixels.width, 300)
        self.assertEqual(pixels.height, 500)

    def test_crop_dimensions(self) -> None:
        image = Image.new("RGB", (1000, 2000), color=(12, 34, 56))
        crop = crop_answer_region(
            image,
            {"x": 0.10, "y": 0.20, "width": 0.30, "height": 0.25},
        )
        self.assertEqual(crop.size, (300, 500))

    def test_debug_overlay_and_labeled_crop(self) -> None:
        import tempfile
        from pathlib import Path

        image = Image.new("RGB", (200, 200), color=(255, 255, 255))
        region = {
            "x": 0.1,
            "y": 0.1,
            "width": 0.2,
            "height": 0.2,
            "option_id": "MJ5-U1-A1-O2",
        }
        overlay = draw_region_overlay(
            image,
            [("MJ5-U1-A1/MJ5-U1-A1-O2", region)],
        )
        self.assertEqual(overlay.size, (200, 200))
        self.assertEqual(
            region_label("MJ5-U1-E4", {"blank_number": 2, "region_id": "x"}),
            "MJ5-U1-E4/B2",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            crop_path = Path(temp_dir) / "crop.png"
            save_region_crop(image, region, crop_path)
            self.assertTrue(crop_path.is_file())
            with Image.open(crop_path) as saved:
                self.assertEqual(saved.size, (40, 40))

    def test_identity_transform_matches_normalized_pixels(self) -> None:
        pixels = template_region_to_aligned_pixels(VALID, 1000, 2000, transform=None)
        self.assertEqual(pixels, normalized_region_to_pixels(VALID, 1000, 2000))

    def test_non_identity_transform_is_refused(self) -> None:
        with self.assertRaises(RegionError):
            template_region_to_aligned_pixels(
                VALID,
                1000,
                2000,
                transform={"type": "affine"},
            )

    def test_mj5_template_overlays_label_region_ids(self) -> None:
        import tempfile
        from pathlib import Path

        from app.services.region_debug import generate_unit_template_overlays

        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            written = generate_unit_template_overlays(
                "magic-joy-5",
                "unit-1",
                dest_dir=dest,
            )
            names = sorted(path.name for path in written)
            self.assertEqual(
                names,
                [
                    "MJ5-U1-P1-overlay.png",
                    "MJ5-U1-P2-overlay.png",
                    "MJ5-U1-P3-overlay.png",
                ],
            )
            for path in written:
                self.assertTrue(path.is_file())
                with Image.open(path) as overlay:
                    self.assertGreater(overlay.width, 100)
                    self.assertGreater(overlay.height, 100)


if __name__ == "__main__":
    unittest.main()
