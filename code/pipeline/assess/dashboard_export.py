#!/usr/bin/env python3
"""
淹沒結果 → dashboard/data/inundation.js

本檔的示範是用合成地形產生多邊形，輸出會標 synthetic: true，
儀表板地圖只畫 synthetic: false 的範圍。真實偵測結果由 scripts/analyze_ndwi_change.py 寫入
（synthetic: false）。

網格座標轉經緯度用等距圓柱近似（1° 緯度 ≈ 111.32 km），和 map3d.js 相同，
只供顯示，不是測量精度。

    python -m pipeline.assess.dashboard_export
"""

from __future__ import annotations

import json
import math
from typing import Optional

import numpy as np

from .hypsometry import DemGrid, build_hypsometric_curve
from .inundation import inundation_extent_for_scenario, mask_to_polygon_shapely_only

KM_PER_DEGREE_LAT = 111.32


def _synthetic_dem_around(radius_cells: int = 40, cell_size_m: float = 10.0,
                           floor_elevation: float = 600.0,
                           rim_height: float = 45.0) -> tuple:
    """
    合成一段彎曲的狹長河谷 DEM，只給示範用。

    不用碗形是因為碗形淹出來是圓，在地圖上和 3 km 示意圓分不出來。

    回傳 (dem, pour_point, cell_size_m, floor_elevation, crest_elevation)。
    """
    size = radius_cells * 2 + 1
    yy, xx = np.mgrid[0:size, 0:size]
    center = radius_cells
    dx = xx - center
    dy = yy - center

    # 河道中心線隨 dx 做正弦彎曲，模擬河道蜿蜒
    channel_center_y = 0.35 * radius_cells * np.sin(dx / (radius_cells * 0.9))
    dist_from_channel = np.abs(dy - channel_center_y)
    along_channel = np.abs(dx)

    dem = (floor_elevation
           + dist_from_channel * (rim_height / (radius_cells * 0.35))   # 垂直河道：陡升
           + along_channel * (rim_height / (radius_cells * 2.2)))       # 沿河道：緩升
    pour_point = (center, center)
    crest_elevation = floor_elevation + rim_height
    return dem, pour_point, cell_size_m, floor_elevation, crest_elevation


def local_meters_to_lonlat(x_m: float, y_m: float, center_lon: float, center_lat: float) -> tuple:
    """
    區域座標（公尺，原點在壩址）→ (lon, lat)，等距圓柱近似。

    >>> lon, lat = local_meters_to_lonlat(0.0, 0.0, 121.29752, 23.70061)
    >>> round(lon, 5), round(lat, 5)
    (121.29752, 23.70061)
    >>> lon2, _ = local_meters_to_lonlat(11132.0, 0.0, 0.0, 0.0)  # 東移約 1/10 緯度距離換算的經度
    >>> round(lon2, 3)
    0.1
    """
    dlat = y_m / (KM_PER_DEGREE_LAT * 1000.0)
    km_per_degree_lon = KM_PER_DEGREE_LAT * math.cos(math.radians(center_lat))
    dlon = x_m / (km_per_degree_lon * 1000.0) if km_per_degree_lon != 0 else 0.0
    return center_lon + dlon, center_lat + dlat


def polygon_to_lonlat(polygon, center_lon: float, center_lat: float) -> list:
    """
    shapely Polygon（外環，區域公尺座標）→ [[lon, lat], ...] 收尾閉合的清單。
    MultiPolygon 只取面積最大的那一塊（示範用途，避免前端要處理多塊多邊形）。
    """
    geom = polygon
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    coords = list(geom.exterior.coords)
    return [list(local_meters_to_lonlat(x, y, center_lon, center_lat)) for x, y in coords]


def build_inundation_demo_layer(lake_id: str, center_lon: float, center_lat: float,
                                 water_level_fraction: float = 0.7,
                                 simplify_tolerance_m: float = 15.0) -> dict:
    """
    產出單一湖泊的示範淹沒圖層資料（給 `export_layer_js` 寫成 JS）。

    water_level_fraction：0（河床原高程）~1（壩頂／滿蓄），示範情境選
    0.7（接近滿蓄但還沒溢流），比選壩頂水位更有「示警」的展示效果。
    """
    dem, pour_point, cell_size_m, floor_el, crest_el = _synthetic_dem_around()
    curve = build_hypsometric_curve(
        dem, pour_point=pour_point, cell_area_m2=cell_size_m ** 2,
        floor_elevation=floor_el, crest_elevation=crest_el, elevation_step=1.0,
    )
    water_elevation = floor_el + (crest_el - floor_el) * water_level_fraction

    result = inundation_extent_for_scenario(
        dem, pour_point, cell_area_m2=cell_size_m ** 2, water_elevation=water_elevation,
    )

    half_extent = (dem.shape[0] // 2) * cell_size_m
    grid = DemGrid(
        elevation=dem, cell_size_m=cell_size_m,
        transform=(cell_size_m, 0.0, -half_extent, 0.0, -cell_size_m, half_extent),
    )
    poly = mask_to_polygon_shapely_only(result.mask, grid)
    poly = poly.simplify(simplify_tolerance_m, preserve_topology=True)
    ring = polygon_to_lonlat(poly, center_lon, center_lat)

    return {
        "lakeId": lake_id,
        "synthetic": True,
        "note": "示範用合成地形，尚未接真實 DEM；水位為情境假設（壩頂水位的"
                f"{water_level_fraction:.0%}），非現地實測。",
        "waterElevationM": round(water_elevation, 1),
        "areaHectare": round(result.area_m2 / 1e4, 2),
        "volumeWanM3": round(result.volume_wan_m3, 1),
        "polygonLonLat": ring,
        "curvePreview": [(el, round(vol, 1)) for el, _area, vol in curve.points[::5]],
    }


def export_layer_js(layers: dict, path: str) -> None:
    """寫成 `window.INUNDATION_DEMO = {...}`，仿照 lakes.js/risk.js/terrain.js 的模式。"""
    body = json.dumps(layers, ensure_ascii=False, indent=2)
    with open(path, "w", encoding="utf-8") as f:
        f.write("// 由 pipeline.assess.dashboard_export 產生，見該檔案開頭說明\n")
        f.write("// 示範用合成資料——尚未接真實 DEM，不是馬太鞍溪真實的淹沒模擬結果\n")
        f.write(f"window.INUNDATION_DEMO = {body};\n")


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"dashboard_export: {total - fails}/{total} 通過")

    # 馬太鞍溪（bl071，見 dashboard/data/lakes.js）座標
    layer = build_inundation_demo_layer("bl071", center_lon=121.29752, center_lat=23.70061)
    out_path = "dashboard/data/inundation.js"
    export_layer_js({"bl071": layer}, out_path)
    print(f"\n寫入 {out_path}：淹沒面積 {layer['areaHectare']:.2f} 公頃，"
          f"多邊形 {len(layer['polygonLonLat'])} 個頂點（示範資料，非真實模擬）")
