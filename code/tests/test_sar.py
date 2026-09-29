#!/usr/bin/env python3
"""
test_sar.py — SAR 鏈單元測試：preprocess.sar / preprocess.mask /
detect.water（SAR 半）/ detect.landslide / detect.barrier_lake

全部用合成資料（`barrier_lake.synthetic_scene`：南北向山谷、河道、
崩塌堵塞、上游回淹、一塊雷達陰影陡坡、一塊跟河道不相連的平台積水），
不需要真實 Sentinel-1 影像。真實資料分析見 scripts/analyze_sar_change.py。

執行（於 code/ 目錄下）：
    pytest tests/test_sar.py -v
"""

from __future__ import annotations

import unittest

import numpy as np

from pipeline.detect import barrier_lake as B
from pipeline.detect import landslide as L
from pipeline.detect import water as W
from pipeline.preprocess import mask as M
from pipeline.preprocess import sar as S


def _chain(**scene_kw):
    s = B.synthetic_scene(**scene_kw)
    out = B.run_sar_chain(s["pre_db"], s["post_db"], s["cell_size_m"], dem=s["dem"],
                          later_post_dbs=s["later_dbs"], min_catchment_km2=0.05)
    return s, out


class TestLeeFilter(unittest.TestCase):
    def test_reduces_speckle_in_homogeneous_area(self):
        rng = np.random.default_rng(0)
        flat = S.linear_to_db(rng.gamma(4.4, 0.1 / 4.4, (80, 80)))
        self.assertLess(np.std(S.lee_filter(flat)), np.std(flat) / 2)

    def test_preserves_mean_level(self):
        rng = np.random.default_rng(1)
        flat = S.linear_to_db(rng.gamma(4.4, 0.1 / 4.4, (80, 80)))
        filtered_lin = S.db_to_linear(S.lee_filter(flat))
        self.assertAlmostEqual(filtered_lin.mean(), 0.1, delta=0.01)

    def test_preserves_water_land_edge(self):
        img = np.full((20, 20), -8.0)
        img[:, :10] = -22.0
        out = S.lee_filter(img)
        self.assertLess(out[10, 5], -20.0)
        self.assertGreater(out[10, 15], -9.0)

    def test_nan_stays_nan(self):
        img = np.full((10, 10), -8.0)
        img[3, 3] = np.nan
        out = S.lee_filter(img)
        self.assertTrue(np.isnan(out[3, 3]))
        self.assertFalse(np.isnan(out[3, 4]))


class TestCheckAligned(unittest.TestCase):
    def test_shape_mismatch_raises(self):
        a = {"db": np.zeros((3, 3)), "transform": (10, 0, 0, 0, -10, 0), "crs": "EPSG:4326"}
        b = dict(a, db=np.zeros((3, 4)))
        with self.assertRaises(ValueError):
            S.check_aligned(a, b)

    def test_crs_mismatch_raises(self):
        a = {"db": np.zeros((3, 3)), "transform": (10, 0, 0, 0, -10, 0), "crs": "EPSG:4326"}
        with self.assertRaises(ValueError):
            S.check_aligned(a, dict(a, crs="EPSG:3826"))

    def test_dem_key_supported(self):
        a = {"db": np.zeros((3, 3)), "transform": (10, 0, 0, 0, -10, 0), "crs": None}
        d = {"dem": np.zeros((3, 3)), "transform": (10, 0, 0, 0, -10, 0), "crs": None}
        S.check_aligned(a, d)


class TestGeometryMask(unittest.TestCase):
    def setUp(self):
        _, self.cols = np.mgrid[0:7, 0:7]

    def test_flat_has_no_distortion(self):
        lay, sh = M.layover_shadow_mask(np.full((7, 7), 100.0), 10.0)
        self.assertFalse(lay.any() or sh.any())

    def test_steep_slope_facing_away_is_shadow(self):
        # 升軌視向朝東；朝東下降 60° 坡 → 背對衛星
        dem = 500.0 - self.cols * 10.0 * np.tan(np.radians(60))
        lay, sh = M.layover_shadow_mask(dem, 10.0, 39.0, M.S1_LOOK_AZIMUTH_DEG["ASCENDING"])
        self.assertTrue(sh[3, 3])
        self.assertFalse(lay[3, 3])

    def test_same_slope_is_not_shadow_on_descending(self):
        # 降軌視向朝西，同一面朝東坡反而面向衛星 → 疊置
        dem = 500.0 - self.cols * 10.0 * np.tan(np.radians(60))
        lay, sh = M.layover_shadow_mask(dem, 10.0, 39.0, M.S1_LOOK_AZIMUTH_DEG["DESCENDING"])
        self.assertFalse(sh[3, 3])
        self.assertTrue(lay[3, 3])

    def test_moderate_slope_has_no_distortion(self):
        dem = 500.0 - self.cols * 10.0 * np.tan(np.radians(25))
        lay, sh = M.layover_shadow_mask(dem, 10.0, 39.0, 77.0)
        self.assertFalse(lay[3, 3] or sh[3, 3])

    def test_landslide_mask_keeps_steep_slopes(self):
        dem = 500.0 - self.cols * 10.0 * np.tan(np.radians(30))
        masks = M.sar_invalid_masks(dem, 10.0)
        self.assertTrue(masks["water"][3, 3])        # 30° > 20° 不可能是水
        self.assertFalse(masks["landslide"][3, 3])   # 但可以是崩塌

    def test_anisotropic_cell_size(self):
        dem = 100.0 - self.cols * 10.0
        s_iso, _ = M.slope_aspect(dem, 10.0)
        s_aniso, _ = M.slope_aspect(dem, (5.0, 10.0))   # 東西向像元只有 5 m → 更陡
        self.assertGreater(s_aniso[3, 3], s_iso[3, 3])


class TestSarWater(unittest.TestCase):
    def test_otsu_on_bimodal_scene(self):
        rng = np.random.default_rng(0)
        vv = np.concatenate([rng.normal(-8, 1, 500), rng.normal(-22, 1, 500)])
        mask, t, method = W.sar_water_mask(vv)
        self.assertEqual(method, "sar_otsu")
        self.assertTrue(-20 < t < -10)
        self.assertEqual(int(mask.sum()), 500)

    def test_fallback_when_otsu_splits_land(self):
        # 全陸地（草地 −12、森林 −6）：Otsu 切在 −9，不合理 → 退回固定門檻
        vv = np.concatenate([np.full(500, -12.0), np.full(500, -6.0)])
        mask, t, method = W.sar_water_mask(vv)
        self.assertEqual(method, "sar_otsu_fallback")
        self.assertEqual(t, W.SAR_WATER_DB_DEFAULT)
        self.assertFalse(mask.any())

    def test_shadow_excluded_by_geometry_mask(self):
        s = B.synthetic_scene(speckle=False)
        masks = M.sar_invalid_masks(s["dem"], s["cell_size_m"])
        without = W.extract_water_sar(s["pre_db"], 10.0, threshold=-18.0)
        with_mask = W.extract_water_sar(s["pre_db"], 10.0, threshold=-18.0,
                                        invalid_mask=masks["water"])
        shadow = s["truth"]["shadow_zone"]
        self.assertTrue(without.mask[shadow].mean() > 0.9)     # 沒遮罩：陰影被當水
        self.assertLess(with_mask.mask[shadow].mean(), 0.2)    # 有遮罩：大部分排除
        self.assertTrue(with_mask.mask[s["truth"]["river"]].all())  # 河道仍在

    def test_change_detection_reused_for_sar(self):
        s = B.synthetic_scene(speckle=False, with_puddle=False)
        pre = W.extract_water_sar(s["pre_db"], 10.0, threshold=-18.0)
        post = W.extract_water_sar(s["post_db"], 10.0, threshold=-18.0)
        new = W.change_detection(pre, post)
        lake = s["truth"]["lake"] & ~s["truth"]["river"]
        np.testing.assert_array_equal(new, lake)


class TestLandslide(unittest.TestCase):
    def test_detects_increase_and_ignores_speckle(self):
        pre = np.full((20, 20), -10.0)
        post = pre.copy()
        post[5:10, 5:10] = -4.0
        post[15, 15] = 0.0
        res = L.detect_landslides(pre, post, 10.0, min_pixels=5)
        self.assertEqual(int(res.mask.sum()), 25)
        self.assertEqual(res.summary()["components"], 1)

    def test_exclude_mask_removes_water(self):
        pre = np.full((10, 10), -8.0)
        post = pre.copy()
        post[:, :5] = -22.0                     # 變成水，回波掉 14 dB
        water = post < -18
        res = L.detect_landslides(pre, post, 10.0, min_pixels=1, exclude_mask=water)
        self.assertFalse(res.mask.any())

    def test_decrease_optional(self):
        pre = np.full((10, 10), -6.0)
        post = pre.copy()
        post[2:6, 2:6] = -11.0
        self.assertEqual(int(L.detect_landslides(pre, post, 10.0, min_pixels=1).mask.sum()), 16)
        self.assertFalse(L.detect_landslides(pre, post, 10.0, min_pixels=1,
                                             include_decrease=False).mask.any())

    def test_chain_finds_scar_not_lake_edge(self):
        s, out = _chain()
        ls = out["landslides"].mask
        self.assertGreater((ls & s["truth"]["landslide"]).sum(), 0.5 * s["truth"]["landslide"].sum())
        self.assertFalse((ls & s["truth"]["lake"]).any())


class TestFlowAccumulation(unittest.TestCase):
    def test_valley_center_collects_flow(self):
        rr, cc = np.mgrid[0:30, 0:21]
        dem = 300.0 - rr + np.abs(cc - 10) * 2.0
        acc = B.flow_accumulation_d8(dem)
        self.assertEqual(int(np.argmax(acc[-1])), 10)
        self.assertGreater(acc[-1, 10], 0.8 * dem.size)


class TestBarrierLake(unittest.TestCase):
    def test_full_scenario_is_grade_a(self):
        s, out = _chain()
        cands = out["candidates"]
        self.assertEqual(len(cands), 1)
        c = cands[0]
        self.assertEqual(c.grade, "A")
        self.assertTrue(c.on_river and c.landslide_nearby and c.dam_downstream and c.persistent)
        self.assertTrue(25 <= c.centroid_row < 50)

    def test_lake_split_by_river_is_one_candidate(self):
        _, out = _chain(speckle=False)
        self.assertEqual(len(out["candidates"]), 1)
        self.assertAlmostEqual(out["candidates"][0].area_hectare, 2.0, delta=0.2)

    def test_single_scene_caps_at_b(self):
        _, out = _chain(n_later=0)
        self.assertEqual([c.grade for c in out["candidates"]], ["B"])

    def test_no_landslide_is_grade_c(self):
        _, out = _chain(with_landslide=False)
        self.assertEqual([c.grade for c in out["candidates"]], ["C"])
        self.assertFalse(out["candidates"][0].landslide_nearby)

    def test_upslope_landslide_is_not_a_dam(self):
        _, out = _chain(landslide_upslope_only=True)
        c = out["candidates"][0]
        self.assertTrue(c.landslide_nearby)
        self.assertFalse(c.dam_downstream)
        self.assertEqual(c.grade, "C")

    def test_off_river_puddle_excluded(self):
        s, out = _chain()
        puddle = s["truth"]["puddle"]
        self.assertTrue((out["new_water"] & puddle).any())      # 有偵測到積水
        for c in out["candidates"]:
            self.assertFalse((c.mask & puddle).any())            # 但不列入候選

    def test_without_dem_downstream_unknown(self):
        s = B.synthetic_scene()
        out = B.run_sar_chain(s["pre_db"], s["post_db"], 10.0, dem=None,
                              later_post_dbs=s["later_dbs"])
        grades = {c.grade for c in out["candidates"]}
        self.assertIn("A", grades)
        top = out["candidates"][0]
        self.assertIsNone(top.dam_downstream)

    def test_to_dict_is_json_serialisable(self):
        import json
        _, out = _chain()
        json.dumps([c.to_dict() for c in out["candidates"]], ensure_ascii=False)

    def test_transform_gives_map_centroid(self):
        nw = np.zeros((10, 10), dtype=bool)
        nw[2:4, 2:4] = True
        river = np.zeros_like(nw)
        river[:, 4] = True
        cands = B.classify(nw, np.zeros_like(nw), river, 10.0, min_area_m2=100,
                           transform=(10.0, 0, 1000.0, 0, -10.0, 2000.0))
        x, y = cands[0].centroid_xy
        self.assertAlmostEqual(x, 1000.0 + 3.0 * 10.0)
        self.assertAlmostEqual(y, 2000.0 - 3.0 * 10.0)


if __name__ == "__main__":
    unittest.main()
