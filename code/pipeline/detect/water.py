#!/usr/bin/env python3
"""
water.py — 水體萃取（B1：光學 NDWI 半）

依施工地圖對照表的可行性建議，`detect/water.py` 原規劃是「SAR 低回波
（Otsu 自動門檻）+ 光學 NDWI」雙軌判定，這裡先只做**光學 NDWI 半**。
SAR 半需要先有 preprocess/sar.py（前處理鏈）、preprocess/mask.py
（雷達陰影遮罩，山區水體萃取最大的坑）才能餵資料進來，風險最高，
列入輔導期目標，暫不實作。

方法
----
NDWI（Normalized Difference Water Index，McFeeters 1996）：

    NDWI = (Green − NIR) / (Green + NIR)

水體近紅外反射率低、綠光反射率相對高，NDWI 偏正；植生／裸露地相反，
NDWI 偏負。門檻二值化取水體遮罩，門檻可用固定值（McFeeters 慣例 0.0）
或自動找。

Otsu 門檻演算法這裡用 numpy 自己實作、不引入 scikit-image：跟
assess/hypsometry.py 用 scipy 取代 richdem 是同一個理由——現在只需要
「在雙峰直方圖上找一個門檻」這一個功能，不需要整包 scikit-image，
等真的要做 SAR 那半（形態學運算）才需要解開 requirements.txt 裡的
scikit-image。

變化偵測（「新增水體」）
----------------------
堰塞湖判定要的是「事件後新增的水體」，不是水體本身（河道平常就有水）。
做法：事件前後各算一次水體遮罩，new_water = post_mask & ~pre_mask，
這是 detect/barrier_lake.py（未來要做）「新增水體 × 河道相交 × 上游
崩塌」判定的其中一項輸入。

單位與座標慣例跟 assess/hypsometry.py 一致：像元面積用 m²，輸出面積
另外換算公頃方便閱讀；真實 GeoTIFF 讀取一樣用延遲 import（沒裝
rasterio 不影響核心演算法可測試性）。

執行方式：python -m pipeline.detect.water
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

import numpy as np


# ══════════════════════════════════════════
# Sentinel-2 影像讀取（真實 GeoTIFF；rasterio 延遲 import，
# 跟 assess/hypsometry.py 的 load_dem_geotiff 同款）
# ══════════════════════════════════════════

def load_sentinel2_bands(green_path: str, nir_path: str) -> tuple:
    """
    讀取 Sentinel-2 Green（B03）與 NIR（B08）波段（各自一個 GeoTIFF）。
    需要 rasterio（requirements.txt 目前註解掉，開工時解開該行 +
    `pip install -r requirements.txt`）。

    回傳 (green, nir, cell_size_m)。Sentinel-2 官方分發的 B03/B08 本來
    就是同解析度 10m、同網格，理論上不需要另外 resample；若尺寸不一致
    會直接丟錯，提醒先做好對齊。
    """
    try:
        import rasterio
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "讀取真實 Sentinel-2 影像需要 rasterio："
            "把 requirements.txt 裡 `# rasterio>=1.3` 這行解開後重新安裝。"
        ) from e

    with rasterio.open(green_path) as src_g, rasterio.open(nir_path) as src_n:
        green = src_g.read(1).astype("float64")
        nir = src_n.read(1).astype("float64")
        if green.shape != nir.shape:
            raise ValueError(
                f"Green/NIR 尺寸不一致：{green.shape} vs {nir.shape}，"
                "需先做好共同網格對齊（resample）。"
            )
        if src_g.nodata is not None:
            green[green == src_g.nodata] = np.nan
        if src_n.nodata is not None:
            nir[nir == src_n.nodata] = np.nan
        cell_size = abs(src_g.transform.a)
        return green, nir, cell_size


# ══════════════════════════════════════════
# NDWI 計算
# ══════════════════════════════════════════

def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    NDWI = (Green − NIR) / (Green + NIR)。分母為 0（含兩者皆 nodata）的
    像元回傳 nan，不當成水體也不當成陸地。

    >>> green = np.array([0.30, 0.10])
    >>> nir = np.array([0.05, 0.35])
    >>> vals = ndwi(green, nir)
    >>> round(float(vals[0]), 4), round(float(vals[1]), 4)
    (0.7143, -0.5556)
    """
    green = np.asarray(green, dtype="float64")
    nir = np.asarray(nir, dtype="float64")
    denom = green + nir
    with np.errstate(invalid="ignore", divide="ignore"):
        result = np.where(denom == 0, np.nan, (green - nir) / denom)
    return result


# ══════════════════════════════════════════
# 門檻二值化（Otsu 自動門檻，numpy 自實作）
# ══════════════════════════════════════════

def otsu_threshold(values: np.ndarray, bins: int = 256) -> float:
    """
    Otsu 演算法：在直方圖上找一個門檻，使門檻兩側（前景／背景）的
    類間變異數（between-class variance）最大。忽略 nan。

    >>> rng = np.random.default_rng(0)
    >>> land = rng.normal(-0.5, 0.05, 500)   # 陸地群聚
    >>> water = rng.normal(0.6, 0.05, 500)   # 水體群聚
    >>> t = otsu_threshold(np.concatenate([land, water]))
    >>> -0.5 < t < 0.6
    True
    """
    v = np.asarray(values, dtype="float64")
    v = v[~np.isnan(v)]
    if v.size == 0:
        raise ValueError("values 全是 nan，無法計算門檻")
    if v.min() == v.max():
        return float(v.min())

    hist, edges = np.histogram(v, bins=bins)
    hist = hist.astype("float64")
    centers = (edges[:-1] + edges[1:]) / 2.0

    total = hist.sum()
    sum_all = (hist * centers).sum()

    weight_bg = np.cumsum(hist)
    sum_bg = np.cumsum(hist * centers)
    weight_fg = total - weight_bg

    with np.errstate(invalid="ignore", divide="ignore"):
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_all - sum_bg) / weight_fg
        between_var = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2

    between_var = np.nan_to_num(between_var, nan=-1.0)
    # 直方圖中間若有一段完全沒有資料的空隙（例如兩群樣本分得很開），
    # 該區間內每個門檻的類間變異數都會打平、同為最大值；此時取這段
    # 平段的中點，而不是 argmax 預設回傳的第一個 bin——後者會讓門檻
    # 卡在低群組的邊緣，容易把低群組裡最極端的離群值誤判過線。
    max_var = between_var.max()
    tied = np.flatnonzero(np.isclose(between_var, max_var))
    best_idx = int(round(tied.mean()))
    return float(centers[best_idx])


def water_mask(ndwi_arr: np.ndarray, threshold: Optional[float] = None) -> tuple:
    """
    回傳 (布林遮罩, 實際使用的門檻)。threshold=None 時用 otsu_threshold
    自動找；也可以傳固定值（McFeeters 慣例門檻是 0.0）。

    >>> arr = np.array([0.7, 0.6, -0.4, -0.5])
    >>> mask, t = water_mask(arr, threshold=0.0)
    >>> mask.tolist()
    [True, True, False, False]
    """
    ndwi_arr = np.asarray(ndwi_arr, dtype="float64")
    if threshold is None:
        threshold = otsu_threshold(ndwi_arr)
    mask = np.where(np.isnan(ndwi_arr), False, ndwi_arr > threshold)
    return mask, threshold


# ══════════════════════════════════════════
# 單期水體萃取結果（面積等），單位慣例跟 hypsometry 一致
# ══════════════════════════════════════════

@dataclass
class WaterExtent:
    """單一時期（一景影像）的水體萃取結果。"""
    mask: np.ndarray
    threshold: float
    method: str                    # "otsu" 或 "fixed"
    cell_size_m: float
    date: Optional[str] = None     # ISO 日期字串，供 C1 回測時間點比對用

    @property
    def area_m2(self) -> float:
        return float(self.mask.sum()) * (self.cell_size_m ** 2)

    @property
    def area_hectare(self) -> float:
        return self.area_m2 / 1e4

    def summary(self) -> dict:
        return {
            "date": self.date,
            "method": self.method,
            "threshold": round(float(self.threshold), 4),
            "pixel_count": int(self.mask.sum()),
            "area_m2": round(self.area_m2, 1),
            "area_hectare": round(self.area_hectare, 3),
        }


def extract_water(green: np.ndarray, nir: np.ndarray, cell_size_m: float,
                   threshold: Optional[float] = None,
                   date: Optional[str] = None) -> WaterExtent:
    """
    一站式：算 NDWI → 二值化 → 包成 WaterExtent。

    >>> green = np.full((4, 4), 0.10)
    >>> nir = np.full((4, 4), 0.35)
    >>> green[1:3, 1:3] = 0.30   # 中間 2x2 是水體
    >>> nir[1:3, 1:3] = 0.05
    >>> ext = extract_water(green, nir, cell_size_m=10.0, threshold=0.0)
    >>> int(ext.mask.sum())
    4
    >>> ext.area_hectare
    0.04
    """
    ndwi_arr = ndwi(green, nir)
    mask, used_threshold = water_mask(ndwi_arr, threshold=threshold)
    method = "fixed" if threshold is not None else "otsu"
    return WaterExtent(mask=mask, threshold=used_threshold, method=method,
                        cell_size_m=cell_size_m, date=date)


# ══════════════════════════════════════════
# 變化偵測：事件後新增的水體（barrier_lake.py 未來的輸入之一）
# ══════════════════════════════════════════

def change_detection(pre: WaterExtent, post: WaterExtent) -> np.ndarray:
    """
    新增水體 = 事件後水體 且 非事件前水體（排除河道等常態水體）。
    要求 pre/post 的網格尺寸一致（同一塊區域、同解析度、對齊好的影像）。

    >>> pre_mask = np.array([[True, False], [False, False]])
    >>> post_mask = np.array([[True, True], [False, True]])
    >>> pre = WaterExtent(mask=pre_mask, threshold=0.0, method="fixed", cell_size_m=10.0)
    >>> post = WaterExtent(mask=post_mask, threshold=0.0, method="fixed", cell_size_m=10.0)
    >>> change_detection(pre, post).tolist()
    [[False, True], [False, True]]
    """
    if pre.mask.shape != post.mask.shape:
        raise ValueError(
            f"pre/post 網格尺寸不一致：{pre.mask.shape} vs {post.mask.shape}，"
            "需先做好共同網格對齊。"
        )
    return post.mask & ~pre.mask


# ══════════════════════════════════════════
# 存到 data/derived/，供 B2 定位水體邊界、C1 回測時間點比對使用
# ══════════════════════════════════════════

def save_extent_summary(extent: WaterExtent, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(extent.summary(), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"water: {total - fails}/{total} 通過")

    # 示範：合成一塊背景陸地、中央圓形水體的影像，模擬事件前後對比
    # （事件後水體範圍擴大，模擬堰塞湖形成）
    size = 41
    yy, xx = np.mgrid[0:size, 0:size]
    center = size // 2
    dist = np.sqrt((yy - center) ** 2 + (xx - center) ** 2)

    def make_scene(water_radius: float):
        is_water = dist <= water_radius
        green = np.where(is_water, 0.30, 0.10)
        nir = np.where(is_water, 0.05, 0.35)
        return green, nir

    pre_green, pre_nir = make_scene(water_radius=5.0)     # 事件前：既有河道
    post_green, post_nir = make_scene(water_radius=15.0)  # 事件後：堰塞湖擴大水體範圍

    pre_extent = extract_water(pre_green, pre_nir, cell_size_m=10.0, date="2025-09-20")
    post_extent = extract_water(post_green, post_nir, cell_size_m=10.0, date="2025-09-23")
    new_water = change_detection(pre_extent, post_extent)

    print(f"\n事件前水體面積：{pre_extent.area_hectare:.2f} 公頃"
          f"（{pre_extent.method} 門檻 {pre_extent.threshold:.3f}）")
    print(f"事件後水體面積：{post_extent.area_hectare:.2f} 公頃"
          f"（{post_extent.method} 門檻 {post_extent.threshold:.3f}）")
    area_new_ha = float(new_water.sum()) * 100.0 / 1e4
    print(f"新增水體：{int(new_water.sum())} 像元，約 {area_new_ha:.2f} 公頃")
