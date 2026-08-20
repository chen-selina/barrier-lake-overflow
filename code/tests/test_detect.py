#!/usr/bin/env python3
"""
test_detect.py — pipeline.detect 單元測試（water.py，B1 NDWI 光學半）

只測不需要真實 Sentinel-2 GeoTIFF 的部分：NDWI 公式、Otsu 門檻、
二值化、變化偵測，全部用合成資料驗證。真實影像讀取
（load_sentinel2_bands）不在本檔測試範圍內——那需要真的影像檔案，
等資料到位後另外用整合測試涵蓋。

執行（於 code/ 目錄下）：
    pytest tests/test_detect.py -v
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import numpy as np

from pipeline.detect import water as W


class TestNdwi(unittest.TestCase):
    def test_water_pixel_gives_positive_value(self):
        # 水體：綠光高、近紅外低
        vals = W.ndwi(np.array([0.30]), np.array([0.05]))
        self.assertGreater(vals[0], 0.0)

    def test_land_pixel_gives_negative_value(self):
        # 陸地／植生：近紅外高於綠光
        vals = W.ndwi(np.array([0.10]), np.array([0.35]))
        self.assertLess(vals[0], 0.0)

    def test_zero_denominator_gives_nan(self):
        vals = W.ndwi(np.array([0.0]), np.array([0.0]))
        self.assertTrue(np.isnan(vals[0]))

    def test_matches_hand_computed_formula(self):
        vals = W.ndwi(np.array([0.4]), np.array([0.2]))
        self.assertAlmostEqual(vals[0], (0.4 - 0.2) / (0.4 + 0.2), places=10)


class TestOtsuThreshold(unittest.TestCase):
    def test_separates_two_well_separated_clusters(self):
        rng = np.random.default_rng(1)
        land = rng.normal(-0.5, 0.05, 500)
        water = rng.normal(0.6, 0.05, 500)
        t = W.otsu_threshold(np.concatenate([land, water]))
        self.assertGreater(t, -0.5)
        self.assertLess(t, 0.6)

    def test_constant_array_returns_that_value(self):
        t = W.otsu_threshold(np.full(10, 0.25))
        self.assertEqual(t, 0.25)

    def test_ignores_nan(self):
        rng = np.random.default_rng(2)
        land = rng.normal(-0.5, 0.05, 200)
        water = rng.normal(0.6, 0.05, 200)
        values = np.concatenate([land, water, np.full(50, np.nan)])
        t = W.otsu_threshold(values)
        self.assertGreater(t, -0.5)
        self.assertLess(t, 0.6)

    def test_all_nan_raises(self):
        with self.assertRaises(ValueError):
            W.otsu_threshold(np.full(5, np.nan))


class TestWaterMask(unittest.TestCase):
    def test_fixed_threshold(self):
        arr = np.array([0.7, 0.6, -0.4, -0.5])
        mask, t = W.water_mask(arr, threshold=0.0)
        self.assertEqual(t, 0.0)
        self.assertEqual(mask.tolist(), [True, True, False, False])

    def test_nan_pixels_never_marked_as_water(self):
        arr = np.array([np.nan, 0.5])
        mask, _ = W.water_mask(arr, threshold=0.0)
        self.assertFalse(mask[0])
        self.assertTrue(mask[1])

    def test_auto_otsu_separates_clear_clusters(self):
        rng = np.random.default_rng(3)
        land = rng.normal(-0.5, 0.05, 200)
        water = rng.normal(0.6, 0.05, 200)
        arr = np.concatenate([land, water])
        mask, t = W.water_mask(arr, threshold=None)
        self.assertTrue(mask[200:].all())
        self.assertFalse(mask[:200].any())


class TestExtractWater(unittest.TestCase):
    def test_area_matches_pixel_count_times_cell_area(self):
        green = np.full((4, 4), 0.10)
        nir = np.full((4, 4), 0.35)
        green[1:3, 1:3] = 0.30
        nir[1:3, 1:3] = 0.05
        ext = W.extract_water(green, nir, cell_size_m=10.0, threshold=0.0)
        self.assertEqual(int(ext.mask.sum()), 4)
        self.assertEqual(ext.area_m2, 4 * 100.0)
        self.assertEqual(ext.method, "fixed")

    def test_default_threshold_uses_otsu(self):
        green = np.full((10, 10), 0.10)
        nir = np.full((10, 10), 0.35)
        green[3:7, 3:7] = 0.30
        nir[3:7, 3:7] = 0.05
        ext = W.extract_water(green, nir, cell_size_m=10.0)
        self.assertEqual(ext.method, "otsu")
        self.assertEqual(int(ext.mask.sum()), 16)


class TestChangeDetection(unittest.TestCase):
    def _extent(self, mask):
        return W.WaterExtent(mask=mask, threshold=0.0, method="fixed", cell_size_m=10.0)

    def test_new_water_is_post_minus_pre(self):
        pre = self._extent(np.array([[True, False], [False, False]]))
        post = self._extent(np.array([[True, True], [False, True]]))
        new_water = W.change_detection(pre, post)
        self.assertEqual(new_water.tolist(), [[False, True], [False, True]])

    def test_no_change_gives_all_false(self):
        mask = np.array([[True, False], [False, True]])
        pre = self._extent(mask.copy())
        post = self._extent(mask.copy())
        new_water = W.change_detection(pre, post)
        self.assertFalse(new_water.any())

    def test_shape_mismatch_raises(self):
        pre = self._extent(np.zeros((2, 2), dtype=bool))
        post = self._extent(np.zeros((3, 3), dtype=bool))
        with self.assertRaises(ValueError):
            W.change_detection(pre, post)


class TestSaveExtentSummary(unittest.TestCase):
    def test_round_trip_json(self):
        ext = W.WaterExtent(
            mask=np.array([[True, True], [False, False]]),
            threshold=0.123456, method="otsu", cell_size_m=10.0, date="2025-09-23",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "extent.json")
            W.save_extent_summary(ext, path)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        self.assertEqual(data["date"], "2025-09-23")
        self.assertEqual(data["method"], "otsu")
        self.assertEqual(data["pixel_count"], 2)
        self.assertEqual(data["area_m2"], 200.0)


if __name__ == "__main__":
    unittest.main()
