#!/usr/bin/env python3
"""
inundation.py — bathtub 淹沒模擬

先做 bathtub model 快估（本檔目前的範圍），之後可再升級成簡化一維水動力
（例如沿河道做逐斷面演算），但那是輔導期項目，MVP 階段先求「淹沒範圍
拿得出來、邏輯站得住腳」。

跟 hypsometry.py 共用同一套「連通填洼」核心演算法（`_connected_mask_at_level`
/ `area_volume_at_level`）：蓄水範圍與淹沒範圍本質上是同一個運算在不同
水位下的結果，這裡不重寫一次，直接 import 沿用，維持單一事實來源。

輸出：一個布林遮罩（哪些像元被淹沒）+ 對應的地理多邊形（供 exposure.py
疊合人口資料、以及前端地圖畫圖層用）。

執行方式：python -m pipeline.assess.inundation
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

import numpy as np

from .hypsometry import DemGrid, _connected_mask_at_level, area_volume_at_level


# ══════════════════════════════════════════
# 核心：給定水位，回傳淹沒遮罩
# ══════════════════════════════════════════

@dataclass
class InundationResult:
    mask: np.ndarray            # 布林陣列，True = 淹沒
    water_elevation: float
    area_m2: float
    volume_wan_m3: float
    pour_point: tuple


def bathtub_mask(dem: np.ndarray, pour_point: tuple,
                  water_elevation: float, cell_area_m2: float) -> InundationResult:
    """
    水位以下、且跟 pour_point 水力連通的像元 = 淹沒範圍。

    跟 hypsometry.area_volume_at_level 算的是同一件事，這裡多回傳
    遮罩本身（hypsometry 那邊只回傳面積/容積數字，是刻意簡化，因為
    掃整條曲線時不需要每一級都留著遮罩，只有「最終那一個水位」
    才需要把遮罩留下來用於畫圖跟疊合人口）。

    >>> dem = np.array([[5., 5., 5.],
    ...                 [5., 1., 5.],
    ...                 [5., 5., 5.]])
    >>> r = bathtub_mask(dem, (1, 1), water_elevation=3.0, cell_area_m2=100.0)
    >>> bool(r.mask[1, 1])
    True
    >>> r.area_m2
    100.0
    """
    mask = _connected_mask_at_level(dem, pour_point, water_elevation)
    area_m2, vol_wan = area_volume_at_level(dem, pour_point, water_elevation, cell_area_m2)
    return InundationResult(mask=mask, water_elevation=water_elevation,
                             area_m2=area_m2, volume_wan_m3=vol_wan,
                             pour_point=pour_point)


def mask_to_polygons(mask: np.ndarray, transform: tuple) -> list:
    """
    把淹沒遮罩轉成地理座標多邊形清單（每個連通區塊一個多邊形），
    供 exposure.py 疊合、或前端地圖畫圖層。

    需要 shapely + rasterio（`rasterio.features.shapes` 做柵格轉多邊形）。
    這兩個套件目前在 requirements.txt 裡是註解掉的，開工時解開：
        # rasterio>=1.3
        # shapely>=2.0
    """
    try:
        from rasterio import features
        from rasterio.transform import Affine
        from shapely.geometry import shape
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "mask_to_polygons 需要 rasterio + shapely，"
            "把 requirements.txt 對應行解開後安裝。"
        ) from e

    affine = Affine(*transform)
    polygons = []
    for geom, value in features.shapes(mask.astype("uint8"), mask=mask, transform=affine):
        if value == 1:
            polygons.append(shape(geom))
    return polygons


def mask_to_polygon_shapely_only(mask: np.ndarray, dem_grid: DemGrid):
    """
    不依賴 rasterio 的替代版本：只用 shapely 手動把每個「被淹沒像元」
    組成一個小方塊，再 union 起來，得到單一（可能是 MultiPolygon）淹沒範圍。
    像元數量大時比 rasterio.features.shapes 慢很多，但拿掉了 rasterio
    這個依賴，適合先求有結果、之後再優化。

    >>> mask = np.array([[True, True], [False, True]])
    >>> grid = DemGrid(elevation=np.zeros((2, 2)), cell_size_m=10.0,
    ...                 transform=(10.0, 0.0, 0.0, 0.0, -10.0, 20.0))
    >>> poly = mask_to_polygon_shapely_only(mask, grid)
    >>> round(poly.area, 1)
    300.0
    """
    from shapely.geometry import box
    from shapely.ops import unary_union

    if dem_grid.transform is None:
        raise ValueError("dem_grid 缺少 transform")
    a, b, c, d, e, f = dem_grid.transform
    boxes = []
    rows, cols = np.where(mask)
    for r, col in zip(rows, cols):
        x0 = c + col * a
        y0 = f + r * e
        boxes.append(box(min(x0, x0 + a), min(y0, y0 + e),
                          max(x0, x0 + a), max(y0, y0 + e)))
    return unary_union(boxes)


# ══════════════════════════════════════════
# 由 B2 的水位–容積曲線推算「目前」水位（供還沒溢流前的淹沒範圍展示）
# 或直接指定壩頂水位（供「假設溢流會淹到哪裡」的情境展示）
# ══════════════════════════════════════════

def inundation_extent_for_scenario(dem: np.ndarray, pour_point: tuple,
                                    cell_area_m2: float,
                                    water_elevation: float) -> InundationResult:
    """
    對外的主入口：給定情境水位（可以是 B2 反演出的目前水位、
    也可以是壩頂高程＝「萬一蓄滿溢流」情境），算出淹沒範圍。

    這支刻意跟 bathtub_mask 拆開成獨立函式名稱，是為了讓呼叫端
    語意清楚（「這是在跑一個情境」），未來要接一維水動力模擬時，
    只需要在這一層把 bathtub_mask 換掉即可，上層呼叫介面不必變動。
    """
    return bathtub_mask(dem, pour_point, water_elevation, cell_area_m2)


def save_result(result: InundationResult, path: str) -> None:
    """
    存成 JSON，供 exposure.py（B3 後半）與前端
    `code/dashboard/data/inundation.js`（仿照 lakes.js/risk.js/terrain.js
    的模式）轉譯使用。遮罩本身不存進 JSON（太大），只存範圍摘要；
    真正要畫圖的多邊形另外用 mask_to_polygons() 產生。
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "water_elevation_m": result.water_elevation,
            "area_m2": result.area_m2,
            "area_hectare": result.area_m2 / 1e4,
            "volume_wan_m3": result.volume_wan_m3,
            "pour_point_rowcol": list(result.pour_point),
        }, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 執行方式：python -m pipeline.assess.inundation
    import doctest
    fails, total = doctest.testmod()
    print(f"inundation: {total - fails}/{total} 通過")

    # 示範：沿用 hypsometry.py 示範用的碗形山谷地形
    size = 61
    yy, xx = np.mgrid[0:size, 0:size]
    center = size // 2
    dist = np.sqrt((yy - center) ** 2 + (xx - center) ** 2)
    dem = 640.0 + dist * 1.4
    pour_point = (center, center)

    result = inundation_extent_for_scenario(
        dem, pour_point, cell_area_m2=30.0 * 30.0, water_elevation=670.0,
    )
    print(f"\n水位 670m 情境：淹沒面積 {result.area_m2/1e4:.2f} 公頃，"
          f"對應容積 {result.volume_wan_m3:,.0f} 萬m³")

    grid = DemGrid(elevation=dem, cell_size_m=30.0,
                    transform=(30.0, 0.0, 280000.0, 0.0, -30.0, 2622000.0))
    poly = mask_to_polygon_shapely_only(result.mask, grid)
    print(f"淹沒範圍多邊形面積（shapely 交叉驗證）：{poly.area/1e4:.2f} 公頃")
