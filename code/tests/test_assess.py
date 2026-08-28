#!/usr/bin/env python3
"""
test_assess.py — pipeline.assess 單元測試（hypsometry / inundation / exposure）

只測不需要真實 DEM／shapefile 檔案的部分：核心的連通填洼演算法、
水位–容積曲線的內插、bathtub 遮罩、以及用合成資料驗證的人口疊合邏輯。
真實 GeoTIFF／shapefile 讀取（load_dem_geotiff、
population_exposure_from_villages 接真實 SEGIS 資料）不在本檔測試範圍內
——那需要真的資料檔案，等資料到位後另外用整合測試涵蓋。

執行（於 code/ 目錄下）：
    pytest tests/test_assess.py -v
"""

from __future__ import annotations

import unittest

import numpy as np

from pipeline.assess import hypsometry as H
from pipeline.assess import inundation as I
from pipeline.assess import exposure as E
from pipeline.assess import dashboard_export as DX


def _bowl_dem(size: int = 21, floor: float = 640.0, slope: float = 2.0):
    """合成一個碗形山谷 DEM，中心最低，向外均勻升高，方便手算驗證。"""
    yy, xx = np.mgrid[0:size, 0:size]
    center = size // 2
    dist = np.sqrt((yy - center) ** 2 + (xx - center) ** 2)
    dem = floor + dist * slope
    return dem, (center, center)


class TestConnectedFloodFill(unittest.TestCase):
    """連通填洼是 hypsometry 跟 inundation 共用的核心，必須先確保它對。"""

    def test_isolated_low_area_not_counted(self):
        # 右下角是一塊隔開的獨立窪地，不該被算進跟 pour_point 連通的範圍
        dem = np.array([[9., 9., 9., 9.],
                         [9., 1., 9., 1.],
                         [9., 9., 9., 9.],
                         [1., 9., 9., 9.]])
        mask = H._connected_mask_at_level(dem, pour_point=(1, 1), level=5.0)
        self.assertTrue(mask[1, 1])
        self.assertFalse(mask[1, 3])   # 隔著高地，不連通
        self.assertFalse(mask[3, 0])   # 同樣不連通

    def test_pour_point_above_level_gives_empty_mask(self):
        dem = np.full((3, 3), 100.0)
        mask = H._connected_mask_at_level(dem, pour_point=(1, 1), level=5.0)
        self.assertFalse(mask.any())

    def test_nan_cells_never_included(self):
        dem = np.array([[np.nan, 1.0], [1.0, 1.0]])
        mask = H._connected_mask_at_level(dem, pour_point=(1, 0), level=10.0)
        self.assertFalse(mask[0, 0])
        self.assertTrue(mask[1, 0])
        self.assertTrue(mask[1, 1])


class TestHypsometricCurve(unittest.TestCase):
    def test_volume_increases_monotonically_with_elevation(self):
        dem, pour = _bowl_dem()
        curve = H.build_hypsometric_curve(
            dem, pour_point=pour, cell_area_m2=900.0,
            floor_elevation=640.0, crest_elevation=660.0, elevation_step=2.0,
        )
        vols = [v for _, _, v in curve.points]
        self.assertEqual(vols, sorted(vols))
        self.assertEqual(vols[0], 0.0)
        self.assertGreater(vols[-1], 0.0)

    def test_curve_endpoints_match_requested_range(self):
        dem, pour = _bowl_dem()
        curve = H.build_hypsometric_curve(
            dem, pour_point=pour, cell_area_m2=900.0,
            floor_elevation=640.0, crest_elevation=655.0, elevation_step=3.0,
        )
        self.assertEqual(curve.points[0][0], 640.0)
        self.assertEqual(curve.points[-1][0], 655.0)  # 尾端強制補到 crest

    def test_as_forecast_curve_format_matches_LakeState_expectation(self):
        # attribution.forecast.LakeState.hypsometric 要吃 [(高程, 容積), ...]
        dem, pour = _bowl_dem()
        curve = H.build_hypsometric_curve(
            dem, pour_point=pour, cell_area_m2=900.0,
            floor_elevation=640.0, crest_elevation=650.0, elevation_step=5.0,
        )
        fc = curve.as_forecast_curve()
        self.assertTrue(all(isinstance(p, tuple) and len(p) == 2 for p in fc))

    def test_volume_at_interpolates_between_levels(self):
        curve = H.HypsometricCurve(points=[(640.0, 0.0, 0.0), (660.0, 900.0, 100.0)])
        self.assertAlmostEqual(curve.volume_at(650.0), 50.0)
        self.assertAlmostEqual(curve.volume_at(630.0), 0.0)    # 邊界外夾住
        self.assertAlmostEqual(curve.volume_at(700.0), 100.0)  # 邊界外夾住

    def test_crest_must_exceed_floor(self):
        dem, pour = _bowl_dem()
        with self.assertRaises(ValueError):
            H.build_hypsometric_curve(dem, pour, cell_area_m2=900.0,
                                       floor_elevation=650.0, crest_elevation=640.0)


class TestElevationAtArea(unittest.TestCase):
    """反查：拿真實遙測偵測到的湖面面積回推水位（B2 用真實 NDWI 面積校準）。"""

    def test_interpolates_between_levels(self):
        curve = H.HypsometricCurve(points=[(640.0, 0.0, 0.0), (660.0, 900.0, 100.0)])
        self.assertAlmostEqual(curve.elevation_at_area(450.0), 650.0)

    def test_below_range_clamps_to_floor(self):
        curve = H.HypsometricCurve(points=[(640.0, 0.0, 0.0), (660.0, 900.0, 100.0)])
        self.assertAlmostEqual(curve.elevation_at_area(-10.0), 640.0)

    def test_above_range_clamps_to_crest(self):
        curve = H.HypsometricCurve(points=[(640.0, 0.0, 0.0), (660.0, 900.0, 100.0)])
        self.assertAlmostEqual(curve.elevation_at_area(5000.0), 660.0)

    def test_round_trip_with_area_at(self):
        dem, pour = _bowl_dem()
        curve = H.build_hypsometric_curve(
            dem, pour_point=pour, cell_area_m2=900.0,
            floor_elevation=640.0, crest_elevation=660.0, elevation_step=1.0,
        )
        for el in (644.0, 650.0, 655.0):
            area = curve.area_at(el)
            self.assertAlmostEqual(curve.elevation_at_area(area), el, delta=1.0)

    def test_flat_plateau_does_not_divide_by_zero(self):
        # 同一水位區間面積沒有變化（例如垂直峭壁），不該噴 ZeroDivisionError
        curve = H.HypsometricCurve(points=[(640.0, 100.0, 0.0), (641.0, 100.0, 10.0), (660.0, 900.0, 100.0)])
        el = curve.elevation_at_area(100.0)
        self.assertIn(el, (640.0, 641.0))


class TestVolumeErrorRate(unittest.TestCase):
    def test_matches_matai_an_official_figure(self):
        # 官方數字見 data/raw/taiwan-barrier-lakes.csv 第 71 列（花蓮馬太鞍溪，9100.00）
        err = H.volume_error_rate(9100.0, 9100.0)
        self.assertEqual(err, 0.0)

    def test_error_rate_is_relative_not_absolute(self):
        err_small_official = H.volume_error_rate(110.0, 100.0)
        err_large_official = H.volume_error_rate(11000.0, 10000.0)
        self.assertAlmostEqual(err_small_official, err_large_official)

    def test_rejects_zero_official_value(self):
        with self.assertRaises(ValueError):
            H.volume_error_rate(10.0, 0.0)


class TestDamHeight(unittest.TestCase):
    def test_dam_height_from_pre_post_dems(self):
        pre = np.array([[10., 10.], [10., 5.]])
        post = np.array([[10., 10.], [10., 45.]])
        self.assertEqual(H.dam_height_from_dems(pre, post, dam_point=(1, 1)), 40.0)

    def test_dam_height_from_curve_fallback(self):
        curve = H.HypsometricCurve(points=[(640.0, 0.0, 0.0), (682.0, 900.0, 9100.0)])
        self.assertEqual(H.dam_height_from_curve(curve), 42.0)


class TestBathtubInundation(unittest.TestCase):
    def test_higher_water_gives_larger_or_equal_area(self):
        dem, pour = _bowl_dem()
        low = I.bathtub_mask(dem, pour, water_elevation=644.0, cell_area_m2=900.0)
        high = I.bathtub_mask(dem, pour, water_elevation=656.0, cell_area_m2=900.0)
        self.assertGreaterEqual(high.area_m2, low.area_m2)

    def test_result_matches_hypsometry_area_volume_at_same_level(self):
        # inundation 跟 hypsometry 共用同一套核心演算法，同一水位下
        # 兩邊算出的面積/容積必須完全一致，這是本次改動故意的設計
        # （單一事實來源），這條測試就是在保證這件事沒有被破壞。
        dem, pour = _bowl_dem()
        result = I.bathtub_mask(dem, pour, water_elevation=650.0, cell_area_m2=900.0)
        area2, vol2 = H.area_volume_at_level(dem, pour, 650.0, 900.0)
        self.assertEqual(result.area_m2, area2)
        self.assertEqual(result.volume_wan_m3, vol2)

    def test_scenario_wrapper_delegates_to_bathtub_mask(self):
        dem, pour = _bowl_dem()
        r1 = I.inundation_extent_for_scenario(dem, pour, 900.0, water_elevation=648.0)
        r2 = I.bathtub_mask(dem, pour, water_elevation=648.0, cell_area_m2=900.0)
        self.assertEqual(r1.area_m2, r2.area_m2)


class TestPopulationExposureFromGrid(unittest.TestCase):
    def test_sums_only_masked_cells(self):
        mask = np.array([[True, False], [False, True]])
        pop = np.array([[7.0, 999.0], [999.0, 3.0]])
        self.assertEqual(E.population_exposure_from_grid(mask, pop), 10.0)

    def test_shape_mismatch_raises(self):
        mask = np.zeros((2, 2), dtype=bool)
        pop = np.zeros((3, 3))
        with self.assertRaises(ValueError):
            E.population_exposure_from_grid(mask, pop)


class TestPopulationExposureFromVillages(unittest.TestCase):
    """用合成的兩個相鄰村里多邊形驗證疊合邏輯（不需要真實 shapefile）。"""

    def setUp(self):
        try:
            import geopandas  # noqa: F401
            import pandas  # noqa: F401
        except ImportError:
            self.skipTest("geopandas/pandas 未安裝")

    def test_overlap_weighted_population_split(self):
        import geopandas as gpd
        import pandas as pd
        from shapely.geometry import box

        villages_gdf = gpd.GeoDataFrame({
            "VILLCODE": ["A001", "A002"],
            "geometry": [box(0, 0, 10, 10), box(10, 0, 20, 10)],
        }, crs="EPSG:3826").to_crs("EPSG:4326")

        population_df = pd.DataFrame({
            "VILLCODE": ["A001", "A002"],
            "population": [1000, 1000],
        })

        # 淹沒範圍剛好對半切過兩個村里的交界
        inundation_polygon = gpd.GeoSeries(
            [box(5, 0, 15, 10)], crs="EPSG:3826"
        ).to_crs("EPSG:4326").iloc[0]

        summary = E.population_exposure_from_villages(
            inundation_polygon, villages_gdf, population_df,
        )
        self.assertAlmostEqual(summary.total_exposed_population, 1000.0, delta=1.0)
        fractions = {v.village_code: v.overlap_fraction for v in summary.villages}
        self.assertAlmostEqual(fractions["A001"], 0.5, delta=0.01)
        self.assertAlmostEqual(fractions["A002"], 0.5, delta=0.01)

    def test_missing_code_column_raises_with_helpful_message(self):
        import geopandas as gpd
        import pandas as pd
        from shapely.geometry import box

        villages_gdf = gpd.GeoDataFrame({
            "some_other_col": ["x"],
            "geometry": [box(0, 0, 1, 1)],
        }, crs="EPSG:4326")
        population_df = pd.DataFrame({"VILLCODE": ["A001"], "population": [100]})

        with self.assertRaises(ValueError):
            E.population_exposure_from_villages(
                box(0, 0, 1, 1), villages_gdf, population_df,
            )


class TestDashboardExportCoordinateConversion(unittest.TestCase):
    """dashboard_export 只測座標轉換／多邊形整理這些純邏輯；
    真的產生 dashboard/data/inundation.js 屬於 I/O，不在這裡測。"""

    def test_zero_offset_returns_center(self):
        lon, lat = DX.local_meters_to_lonlat(0.0, 0.0, 121.29752, 23.70061)
        self.assertAlmostEqual(lon, 121.29752)
        self.assertAlmostEqual(lat, 23.70061)

    def test_north_offset_increases_latitude_only(self):
        lon, lat = DX.local_meters_to_lonlat(0.0, 1000.0, 121.0, 23.0)
        self.assertAlmostEqual(lon, 121.0)
        self.assertGreater(lat, 23.0)

    def test_east_offset_increases_longitude_only(self):
        lon, lat = DX.local_meters_to_lonlat(1000.0, 0.0, 121.0, 23.0)
        self.assertGreater(lon, 121.0)
        self.assertAlmostEqual(lat, 23.0)

    def test_polygon_to_lonlat_preserves_vertex_count_and_centers_on_lake(self):
        from shapely.geometry import Polygon
        square = Polygon([(-100, -100), (100, -100), (100, 100), (-100, 100)])
        ring = DX.polygon_to_lonlat(square, center_lon=121.0, center_lat=23.0)
        self.assertEqual(len(ring), len(list(square.exterior.coords)))
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        self.assertAlmostEqual(sum(lons) / len(lons), 121.0, places=3)
        self.assertAlmostEqual(sum(lats) / len(lats), 23.0, places=3)

    def test_multipolygon_picks_largest_piece(self):
        from shapely.geometry import MultiPolygon, Polygon
        small = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        big = Polygon([(10, 10), (10, 210), (210, 210), (210, 10)])
        multi = MultiPolygon([small, big])
        ring = DX.polygon_to_lonlat(multi, center_lon=121.0, center_lat=23.0)
        self.assertEqual(len(ring), len(list(big.exterior.coords)))

    def test_build_inundation_demo_layer_shape(self):
        layer = DX.build_inundation_demo_layer("bl071", center_lon=121.29752, center_lat=23.70061)
        self.assertTrue(layer["synthetic"])
        self.assertGreater(layer["areaHectare"], 0)
        self.assertGreaterEqual(len(layer["polygonLonLat"]), 4)
        first, last = layer["polygonLonLat"][0], layer["polygonLonLat"][-1]
        self.assertAlmostEqual(first[0], last[0])
        self.assertAlmostEqual(first[1], last[1])


if __name__ == "__main__":
    unittest.main()
