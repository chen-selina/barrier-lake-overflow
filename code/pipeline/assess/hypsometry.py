#!/usr/bin/env python3
"""
水位–面積–容積曲線

從壩址往上游填洼：每個水位只算「高程 ≤ 水位且和壩址 4-連通」的像元，
不相干的低窪地不算進去。

    面積(h) = 連通像元數 × 像元面積
    容積(h) = Σ (h − 像元高程) × 像元面積

容積單位是萬 m³，和清冊、forecast.LakeState.hypsometric 一致。
核心只吃 numpy 陣列，讀 GeoTIFF 才需要 rasterio。

    python -m pipeline.assess.hypsometry
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import ndimage


# DEM 讀取（真實 GeoTIFF；rasterio 為延遲 import，
# 沒裝也不影響下面的核心演算法可測試性）

@dataclass
class DemGrid:
    """DEM 網格資料。elevation 內 nodata 一律以 np.nan 表示。"""
    elevation: np.ndarray          # 2D array，[row, col]，公尺
    cell_size_m: float             # 像元邊長（假設正方形像元、投影座標系）
    crs: str = "EPSG:3826"         # 預設 TWD97 TM2，跟專案其餘座標轉換一致
    transform: Optional[tuple] = None  # rasterio affine（a, b, c, d, e, f），若有

    @property
    def cell_area_m2(self) -> float:
        return self.cell_size_m ** 2

    def rowcol_of_xy(self, x: float, y: float) -> tuple:
        """把投影座標 (x, y) 換算成陣列的 (row, col)。需要 transform。"""
        if self.transform is None:
            raise ValueError("DemGrid 缺少 transform，無法由座標反查 row/col")
        a, b, c, d, e, f = self.transform
        col = int((x - c) / a)
        row = int((y - f) / e)
        return row, col


def load_dem_geotiff(path: str) -> DemGrid:
    """
    讀取事件前 DEM（GeoTIFF）。需要 rasterio（requirements.txt 裡目前
    註解掉，開工時解開該行 + `pip install -r requirements.txt`）。

    政府開放 DEM 來源見 docs/ossint-open-data-atlas.html。
    """
    try:
        import rasterio
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "讀取真實 DEM 需要 rasterio："
            "把 requirements.txt 裡 `# rasterio>=1.3` 這行解開後重新安裝。"
        ) from e

    with rasterio.open(path) as src:
        arr = src.read(1).astype("float64")
        if src.nodata is not None:
            arr = np.where(arr == src.nodata, np.nan, arr)
        transform = src.transform
        cell_size = abs(transform.a)
        return DemGrid(
            elevation=arr,
            cell_size_m=cell_size,
            crs=str(src.crs) if src.crs else "EPSG:3826",
            transform=(transform.a, transform.b, transform.c,
                       transform.d, transform.e, transform.f),
        )


# 核心：連通填洼

# 4-連通結構元素（上下左右），跟「水面連續」的物理意義一致；
# 8-連通會讓對角相鄰的獨立窪地誤判成連通，故不用。
_STRUCT_4CONN = np.array([[0, 1, 0],
                           [1, 1, 1],
                           [0, 1, 0]])


def _connected_mask_at_level(dem: np.ndarray, pour_point: tuple,
                              level: float) -> np.ndarray:
    """
    給定水位 level，回傳「高程 ≤ level 且跟 pour_point 水力連通」的布林遮罩。

    >>> dem = np.array([[5., 5., 5., 5.],
    ...                 [5., 1., 2., 5.],
    ...                 [5., 3., 9., 5.],   # 右下 9 是獨立高地，隔開了
    ...                 [5., 5., 5., 5.]])
    >>> m = _connected_mask_at_level(dem, (1, 1), level=4.0)
    >>> m[1,1], m[1,2], m[2,1]   # 三個連通的窪地像元都應為 True
    (np.True_, np.True_, np.True_)
    >>> m[2,2]                    # 高程 9 的像元不該被淹沒
    np.False_
    """
    r0, c0 = pour_point
    below = np.where(np.isnan(dem), False, dem <= level)
    if not below[r0, c0]:
        return np.zeros_like(below)
    labeled, _ = ndimage.label(below, structure=_STRUCT_4CONN)
    target_label = labeled[r0, c0]
    if target_label == 0:
        return np.zeros_like(below)
    return labeled == target_label


def area_volume_at_level(dem: np.ndarray, pour_point: tuple, level: float,
                          cell_area_m2: float) -> tuple:
    """
    回傳 (面積 m², 容積 萬m³) at 指定水位。

    >>> dem = np.array([[5., 5., 5.],
    ...                 [5., 0., 5.],
    ...                 [5., 5., 5.]])
    >>> area, vol_wan = area_volume_at_level(dem, (1, 1), level=2.0, cell_area_m2=100.0)
    >>> area
    100.0
    >>> vol_wan   # (2-0) * 100 m2 = 200 m3 = 0.02 萬m3
    0.02
    """
    mask = _connected_mask_at_level(dem, pour_point, level)
    if not mask.any():
        return 0.0, 0.0
    depth = np.clip(level - dem[mask], a_min=0.0, a_max=None)
    area_m2 = float(mask.sum()) * cell_area_m2
    volume_m3 = float(depth.sum()) * cell_area_m2
    return area_m2, volume_m3 / 1e4  # 換算萬立方公尺


# 建立整條曲線

@dataclass
class HypsometricCurve:
    """水位–面積–容積曲線。points 由低至高排列。"""
    points: list = field(default_factory=list)   # [(elevation, area_m2, volume_wan_m3), ...]
    pour_point: Optional[tuple] = None
    cell_size_m: Optional[float] = None

    def as_forecast_curve(self) -> list:
        """轉成 attribution.forecast.LakeState.hypsometric 直接吃的格式：
        [(高程, 累積容積萬m3), ...]。"""
        return [(el, vol) for el, _area, vol in self.points]

    def volume_at(self, elevation: float) -> float:
        """線性內插查容積（萬m³）；邊界外夾住（clamp）到端點值。"""
        els = [p[0] for p in self.points]
        vols = [p[2] for p in self.points]
        if elevation <= els[0]:
            return vols[0]
        if elevation >= els[-1]:
            return vols[-1]
        import bisect
        i = bisect.bisect_right(els, elevation) - 1
        e0, e1, v0, v1 = els[i], els[i + 1], vols[i], vols[i + 1]
        t = (elevation - e0) / (e1 - e0)
        return v0 + t * (v1 - v0)

    def area_at(self, elevation: float) -> float:
        """線性內插查水面面積（m²）。"""
        els = [p[0] for p in self.points]
        areas = [p[1] for p in self.points]
        if elevation <= els[0]:
            return areas[0]
        if elevation >= els[-1]:
            return areas[-1]
        import bisect
        i = bisect.bisect_right(els, elevation) - 1
        e0, e1, a0, a1 = els[i], els[i + 1], areas[i], areas[i + 1]
        t = (elevation - e0) / (e1 - e0)
        return a0 + t * (a1 - a0)

    def elevation_at_area(self, target_area_m2: float) -> float:
        """
        給定水面面積，內插反查水位（公尺），超出範圍夾到端點。
        填洼的面積隨水位單調不減，所以可以反查。

        用途：沒有事件後 DEM 時，用遙測偵測到的湖面面積推水位，再讀容積。

        >>> dem = np.array([[10., 10., 10., 10., 10.],
        ...                 [10.,  2.,  1.,  2., 10.],
        ...                 [10.,  3.,  0.,  3., 10.],
        ...                 [10.,  2.,  1.,  2., 10.],
        ...                 [10., 10., 10., 10., 10.]])
        >>> curve = build_hypsometric_curve(dem, pour_point=(2, 2), cell_area_m2=100.0,
        ...                                  floor_elevation=0.0, crest_elevation=4.0, elevation_step=1.0)
        >>> round(curve.elevation_at_area(curve.area_at(2.0)), 6)
        2.0
        """
        els = [p[0] for p in self.points]
        areas = [p[1] for p in self.points]
        if target_area_m2 <= areas[0]:
            return els[0]
        if target_area_m2 >= areas[-1]:
            return els[-1]
        import bisect
        i = bisect.bisect_right(areas, target_area_m2) - 1
        e0, e1, a0, a1 = els[i], els[i + 1], areas[i], areas[i + 1]
        if a1 == a0:
            return e0
        t = (target_area_m2 - a0) / (a1 - a0)
        return e0 + t * (e1 - e0)

    def to_json(self) -> str:
        return json.dumps({
            "pour_point": self.pour_point,
            "cell_size_m": self.cell_size_m,
            "points": self.points,
        }, ensure_ascii=False, indent=2)


def build_hypsometric_curve(dem: np.ndarray, pour_point: tuple,
                             cell_area_m2: float,
                             floor_elevation: float,
                             crest_elevation: float,
                             elevation_step: float = 1.0) -> HypsometricCurve:
    """
    掃描 floor_elevation ~ crest_elevation，逐級算連通面積／容積，組成曲線。

    - floor_elevation：淤積前河床高程（＝壩體形成前該位置的原始高程）
    - crest_elevation：壩頂高程（崩塌堆積體最高點，蓄水超過此高即溢流）
    - elevation_step：掃描間距，預設 1 公尺；DEM 解析度較粗時可以加大，
      換取執行速度

    >>> dem = np.array([[10., 10., 10., 10., 10.],
    ...                 [10.,  2.,  1.,  2., 10.],
    ...                 [10.,  3.,  0.,  3., 10.],
    ...                 [10.,  2.,  1.,  2., 10.],
    ...                 [10., 10., 10., 10., 10.]])
    >>> curve = build_hypsometric_curve(dem, pour_point=(2, 2), cell_area_m2=100.0,
    ...                                  floor_elevation=0.0, crest_elevation=4.0,
    ...                                  elevation_step=1.0)
    >>> curve.points[0]   # 水位=floor時，容積應為 0
    (0.0, 100.0, 0.0)
    >>> curve.points[-1][0]
    4.0
    """
    if crest_elevation <= floor_elevation:
        raise ValueError("crest_elevation 必須大於 floor_elevation")

    levels = list(np.arange(floor_elevation, crest_elevation + elevation_step / 2,
                             elevation_step))
    if levels[-1] < crest_elevation:
        levels.append(crest_elevation)

    points = []
    for level in levels:
        area_m2, vol_wan = area_volume_at_level(dem, pour_point, level, cell_area_m2)
        points.append((round(float(level), 3), area_m2, vol_wan))

    return HypsometricCurve(points=points, pour_point=pour_point,
                             cell_size_m=cell_area_m2 ** 0.5)


# 壩高反演

def dam_height_from_dems(pre_event_dem: np.ndarray, post_event_dem: np.ndarray,
                          dam_point: tuple) -> float:
    """
    壩高 = 事件後壩址高程 − 事件前河床原高程，用事件前後兩期 DEM 相減。
    需要事件前後各一期涵蓋壩址的 DEM（同解析度、同網格對齊）。

    >>> pre = np.array([[10., 10.], [10., 5.]])
    >>> post = np.array([[10., 10.], [10., 45.]])
    >>> dam_height_from_dems(pre, post, dam_point=(1, 1))
    40.0
    """
    return float(post_event_dem[dam_point] - pre_event_dem[dam_point])


def dam_height_from_curve(curve: HypsometricCurve) -> float:
    """
    沒有事件前後兩期 DEM 時，用曲線端點差（crest − floor）粗估壩高。
    準確度低，輸出時要註明是估計值。
    """
    if not curve.points:
        raise ValueError("曲線是空的")
    return curve.points[-1][0] - curve.points[0][0]


# 和清冊官方蓄水量比較

def volume_error_rate(estimated_wan_m3: float, official_wan_m3: float) -> float:
    """
    |模型估算值 − 官方值| / 官方值。

    馬太鞍溪官方蓄水量見 data/raw/taiwan-barrier-lakes.csv 第 71 列
    （「花蓮馬太鞍溪」，9,100.00 萬立方公尺）。

    >>> round(volume_error_rate(8700.0, 9100.0), 4)
    0.044
    """
    if official_wan_m3 == 0:
        raise ValueError("official_wan_m3 不可為 0")
    return abs(estimated_wan_m3 - official_wan_m3) / official_wan_m3


# 存檔／讀檔

def save_curve(curve: HypsometricCurve, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(curve.to_json())


def load_curve(path: str) -> HypsometricCurve:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return HypsometricCurve(
        points=[tuple(p) for p in data["points"]],
        pour_point=tuple(data["pour_point"]) if data.get("pour_point") else None,
        cell_size_m=data.get("cell_size_m"),
    )


if __name__ == "__main__":
    # 執行方式：python -m pipeline.assess.hypsometry
    import doctest
    fails, total = doctest.testmod()
    print(f"hypsometry: {total - fails}/{total} 通過")

    # 示範：合成一個馬太鞍溪型量級的山谷地形（實際使用時用
    # load_dem_geotiff() 讀真正的 DEM，並用真正的壩址座標定位 pour_point）
    size = 61
    yy, xx = np.mgrid[0:size, 0:size]
    center = size // 2
    dist = np.sqrt((yy - center) ** 2 + (xx - center) ** 2)
    dem = 640.0 + dist * 1.4  # 谷底 640m，向外每格升高，模擬一個碗形山谷
    pour_point = (center, center)

    curve = build_hypsometric_curve(
        dem, pour_point=pour_point, cell_area_m2=30.0 * 30.0,  # 30m 解析度
        floor_elevation=640.0, crest_elevation=682.0, elevation_step=2.0,
    )
    print("\n水位–容積曲線（節錄）：")
    for el, area, vol in curve.points[::5]:
        print(f"  高程 {el:6.1f} m  面積 {area/1e4:7.2f} 公頃  容積 {vol:9.1f} 萬m³")

    est = curve.volume_at(682.0)
    err = volume_error_rate(est, 9100.0)
    print(f"\n壩頂容積估計 {est:,.0f} 萬m³，與官方 9,100 萬m³ 誤差率 {err:.1%}")
