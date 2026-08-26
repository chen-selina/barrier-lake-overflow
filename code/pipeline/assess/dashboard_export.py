#!/usr/bin/env python3
"""
dashboard_export.py — 把 assess 模組的淹沒模擬結果轉成前端圖層資料

B3 施工地圖對照表的「前端顯示」步驟：目前 `dashboard/map3d.js` 的
CAP 示警範圍還是壩址座標＋3km 固定半徑的示意圓（`cap.js` 註解已明講
「等 assess/ 模組做出多邊形」）。`inundation.py` 的演算法已經完成，
這裡把它的輸出接上前端——但**目前還沒有真實 DEM**，所以本檔案產出的
是用合成地形跑出來的「示範多邊形」，不是馬太鞍溪真實的淹沒範圍。
資料裡會誠實標註 `synthetic: true`，前端也要顯示對應提示文字，
不能讓人誤以為這是真實模擬結果。

真實 DEM 到位後，只要把 `_synthetic_dem_around()` 換成
`hypsometry.load_dem_geotiff()` 讀真實資料、`pour_point` 換成真實壩址
座標，下面的轉換與輸出邏輯不需要再改。

座標轉換慣例
------------
`inundation.py` 的核心演算法只吃區域網格座標（公尺），要畫在
`map3d.js`（吃經緯度）上，需要轉成 (lon, lat)。這裡用簡化的等距圓柱
投影近似（1 緯度 ≈ 111.32 公里，1 經度 ≈ 111.32×cos(lat) 公里），
跟 `map3d.js` 的 `kmToWorldUnits()` 用同一個緯度換算常數，
量級上一致；示範用途，不追求測量級精度。

執行方式：python -m pipeline.assess.dashboard_export
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
    合成一個以壩址為中心的**狹長河谷型** DEM，純供示範前端管線用。

    刻意不用對稱碗形：真實堰塞湖是沿河道分布的狹長水體，不是同心圓；
    早期版本用對稱碗形合成地形，跑出來的淹沒多邊形在地圖上看起來就是
    一個圓，跟原本要取代的「3km 固定半徑圓」示意圈幾乎分不出來，
    容易讓人誤以為多邊形圖層沒有真的接上。這裡改用「垂直河道方向陡升
    （狹窄河谷）、沿河道方向緩升（狹長水體）＋緩和彎曲（模擬河道蜿蜒）」
    的地形，讓淹沒範圍明顯是長條彎曲形狀，一眼就能跟圓形示意圈區分開。

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
