#!/usr/bin/env python3
"""
mask.py — SAR 幾何失真遮罩（雷達陰影／疊置／陡坡）

山區用 SAR 抓水體最大的坑：背向衛星的陡坡收不到回波（雷達陰影），
σ⁰ 低到跟水面一樣，Otsu 會直接把整片陰影坡當成水。面向衛星的陡坡則
發生疊置（layover），回波異常增強，容易被誤判成崩塌。這裡用事件前
DEM 算坡度／坡向，配合衛星入射角與視向方位，標出這些不可信像元：

- `slope_aspect`：坡度（度）、坡向（下坡方向，自北順時針，度）。
- `layover_shadow_mask`：局部幾何判定。把坡度投影到雷達距離向
  （range 方向）得到距離向坡度 s_r（正值 = 面向衛星）：
      s_r >  θ        → 疊置（坡面比入射波束還陡、面向衛星）
      s_r < θ − 90°   → 陰影（背向衛星、坡面比掠射角還陡）
  這是只看「像元本身坡面」的局部判定，沒有沿距離向做山脊遮蔽的
  射線追蹤（被上游山脊擋住的平地陰影抓不到）——台灣山區狹谷用 10m
  DEM 時多數陰影來自坡面本身，局部判定已涵蓋大部分，射線追蹤列為
  後續改進。
- `steep_slope_mask`：水面不可能在陡坡上；坡度 > max_deg 一律不當水。
  崩塌偵測**不能**套這個遮罩（崩塌本來就發生在陡坡）。

Sentinel-1 是右視雷達：視向方位 = 航向 + 90°。台灣上空升軌航向約
347°（視向約 77°，朝東），降軌航向約 193°（視向約 283°，朝西）。
IW 模式入射角約 29°–46°，中段取 39°。

執行方式：python -m pipeline.preprocess.mask
"""

from __future__ import annotations

from typing import Union

import numpy as np


S1_LOOK_AZIMUTH_DEG = {"ASCENDING": 77.0, "DESCENDING": 283.0}
S1_IW_MID_INCIDENCE_DEG = 39.0


def _cell_xy(cell_size_m: Union[float, tuple]) -> tuple:
    if isinstance(cell_size_m, (tuple, list)):
        return float(cell_size_m[0]), float(cell_size_m[1])
    return float(cell_size_m), float(cell_size_m)


def slope_aspect(dem: np.ndarray, cell_size_m: Union[float, tuple]) -> tuple:
    """
    回傳 (slope_deg, aspect_deg)。cell_size_m 可給單一值或 (dx, dy)。
    陣列列號往下＝往南、欄號往右＝往東（北向上 GeoTIFF 慣例）。
    aspect 是坡面「朝向」（下坡方向），0°=北、90°=東。

    >>> rows, cols = np.mgrid[0:5, 0:5]
    >>> dem = 100.0 - cols * 10.0            # 往東下降 10 m / 10 m → 45° 朝東坡
    >>> s, a = slope_aspect(dem, 10.0)
    >>> round(float(s[2, 2]), 1), round(float(a[2, 2]), 1)
    (45.0, 90.0)
    """
    dx, dy = _cell_xy(cell_size_m)
    dem = np.asarray(dem, dtype="float64")
    dz_drow, dz_dcol = np.gradient(dem, dy, dx)
    dz_east = dz_dcol
    dz_north = -dz_drow
    slope = np.degrees(np.arctan(np.hypot(dz_east, dz_north)))
    # 下坡方向 = −梯度
    aspect = np.degrees(np.arctan2(-dz_east, -dz_north)) % 360.0
    return slope, aspect


def range_slope_deg(slope_deg: np.ndarray, aspect_deg: np.ndarray,
                    look_azimuth_deg: float) -> np.ndarray:
    """
    距離向坡度：坡面在「朝向衛星」方向的傾角，正值 = 面向衛星。
    衛星位於視向的反方向（look_azimuth + 180°）。

    >>> round(float(range_slope_deg(np.array(30.0), np.array(257.0), 77.0)), 6)  # 正對衛星
    30.0
    >>> round(float(range_slope_deg(np.array(30.0), np.array(77.0), 77.0)), 6)  # 背對
    -30.0
    """
    toward_sensor = (look_azimuth_deg + 180.0) % 360.0
    rel = np.radians(np.asarray(aspect_deg) - toward_sensor)
    return np.degrees(np.arctan(np.tan(np.radians(slope_deg)) * np.cos(rel)))


def layover_shadow_mask(dem: np.ndarray, cell_size_m: Union[float, tuple],
                        incidence_deg: float = S1_IW_MID_INCIDENCE_DEG,
                        look_azimuth_deg: float = S1_LOOK_AZIMUTH_DEG["ASCENDING"]) -> tuple:
    """
    回傳 (layover, shadow) 兩個布林遮罩（局部坡面判定，見檔頭說明）。
    DEM 為 nan 的像元兩者皆 False（交給呼叫端另外處理 nodata）。

    >>> _, cols = np.mgrid[0:5, 0:5]
    >>> away = 100.0 - cols * 20.0     # 朝東 63° 陡坡，升軌視向朝東 → 背對衛星
    >>> lay, sh = layover_shadow_mask(away, 10.0, 39.0, 77.0)
    >>> bool(sh[2, 2]), bool(lay[2, 2])
    (True, False)
    >>> toward = 100.0 + cols * 20.0   # 朝西 63° 陡坡 → 面向衛星
    >>> lay, sh = layover_shadow_mask(toward, 10.0, 39.0, 77.0)
    >>> bool(sh[2, 2]), bool(lay[2, 2])
    (False, True)
    """
    slope, aspect = slope_aspect(dem, cell_size_m)
    s_r = range_slope_deg(slope, aspect, look_azimuth_deg)
    valid = ~np.isnan(s_r)
    layover = valid & (np.nan_to_num(s_r) > incidence_deg)
    shadow = valid & (np.nan_to_num(s_r) < incidence_deg - 90.0)
    return layover, shadow


def steep_slope_mask(slope_deg: np.ndarray, max_deg: float = 20.0) -> np.ndarray:
    """
    >>> steep_slope_mask(np.array([5.0, 25.0, np.nan])).tolist()
    [False, True, False]
    """
    slope_deg = np.asarray(slope_deg, dtype="float64")
    return np.where(np.isnan(slope_deg), False, slope_deg > max_deg)


def sar_invalid_masks(dem: np.ndarray, cell_size_m: Union[float, tuple],
                      incidence_deg: float = S1_IW_MID_INCIDENCE_DEG,
                      look_azimuth_deg: float = S1_LOOK_AZIMUTH_DEG["ASCENDING"],
                      max_water_slope_deg: float = 20.0) -> dict:
    """
    一次算好兩組遮罩：
    - "water"：水體萃取用 = 疊置 | 陰影 | 陡坡 | DEM nodata
    - "landslide"：崩塌偵測用 = 疊置 | 陰影 | DEM nodata（不排除陡坡）
    另附 "layover"、"shadow"、"slope_deg" 供輸出統計。
    """
    dem = np.asarray(dem, dtype="float64")
    layover, shadow = layover_shadow_mask(dem, cell_size_m, incidence_deg, look_azimuth_deg)
    slope, _ = slope_aspect(dem, cell_size_m)
    nodata = np.isnan(dem)
    geom = layover | shadow | nodata
    return {
        "water": geom | steep_slope_mask(slope, max_water_slope_deg),
        "landslide": geom,
        "layover": layover,
        "shadow": shadow,
        "slope_deg": slope,
    }


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"mask: {total - fails}/{total} 通過")
