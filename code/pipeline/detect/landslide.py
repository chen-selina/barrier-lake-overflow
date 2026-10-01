#!/usr/bin/env python3
"""
崩塌偵測：SAR 振幅比值法（GRD）

    Δ = σ⁰_post(dB) − σ⁰_pre(dB)，|Δ| ≥ 3 dB 視為變化

植生坡崩塌成裸岩多半回波增強，但平滑泥流或背向衛星的新崩崖會減弱，
所以兩個方向都算，另外記正負號。排除：水體（呼叫端傳 exclude_mask）、
疊置與陰影（不排除陡坡，崩塌本來就在陡坡上）、小於 min_pixels 的碎塊。

相干性法（SLC）沒有做。

    python -m pipeline.detect.landslide
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import ndimage


# 3 dB = 回波倍增／減半，文獻上 GRD 崩塌偵測常見門檻落在 2–3 dB。
LANDSLIDE_THRESHOLD_DB = 3.0


def log_ratio(pre_db: np.ndarray, post_db: np.ndarray) -> np.ndarray:
    """
    >>> log_ratio(np.array([-10.0, -8.0]), np.array([-4.0, -8.0])).tolist()
    [6.0, 0.0]
    """
    pre_db = np.asarray(pre_db, dtype="float64")
    post_db = np.asarray(post_db, dtype="float64")
    if pre_db.shape != post_db.shape:
        raise ValueError(f"pre/post 網格尺寸不一致：{pre_db.shape} vs {post_db.shape}")
    return post_db - pre_db


def remove_small_components(mask: np.ndarray, min_pixels: int) -> np.ndarray:
    """
    去掉像元數 < min_pixels 的連通塊（8 連通）。

    >>> m = np.zeros((5, 5), dtype=bool)
    >>> m[0, 0] = True           # 單像元雜訊
    >>> m[2:5, 2:5] = True       # 9 像元的真實變化
    >>> int(remove_small_components(m, 4).sum())
    9
    """
    mask = np.asarray(mask, dtype=bool)
    if min_pixels <= 1 or not mask.any():
        return mask.copy()
    labeled, n = ndimage.label(mask, structure=np.ones((3, 3)))
    sizes = np.bincount(labeled.ravel())
    keep = sizes >= min_pixels
    keep[0] = False
    return keep[labeled]


@dataclass
class LandslideResult:
    """一組事件前後影像的崩塌偵測結果。"""
    mask: np.ndarray               # 崩塌像元
    sign: np.ndarray               # int8：+1 回波增強、−1 減弱、0 非崩塌
    threshold_db: float
    cell_size_m: float
    date: Optional[str] = None

    @property
    def area_m2(self) -> float:
        return float(self.mask.sum()) * (self.cell_size_m ** 2)

    @property
    def area_hectare(self) -> float:
        return self.area_m2 / 1e4

    def summary(self) -> dict:
        n_comp = int(ndimage.label(self.mask, structure=np.ones((3, 3)))[1]) if self.mask.any() else 0
        return {
            "date": self.date,
            "method": "sar_log_ratio",
            "threshold_db": self.threshold_db,
            "pixel_count": int(self.mask.sum()),
            "increase_pixels": int((self.sign > 0).sum()),
            "decrease_pixels": int((self.sign < 0).sum()),
            "components": n_comp,
            "area_m2": round(self.area_m2, 1),
            "area_hectare": round(self.area_hectare, 3),
        }


def detect_landslides(pre_db: np.ndarray, post_db: np.ndarray, cell_size_m: float,
                      threshold_db: float = LANDSLIDE_THRESHOLD_DB,
                      min_pixels: int = 10,
                      invalid_mask: Optional[np.ndarray] = None,
                      exclude_mask: Optional[np.ndarray] = None,
                      include_decrease: bool = True,
                      date: Optional[str] = None) -> LandslideResult:
    """
    |Δσ⁰| ≥ threshold_db 的像元，扣掉 invalid_mask（疊置／陰影）與
    exclude_mask（水體），再去掉小於 min_pixels 的連通塊。
    pre_db/post_db 建議先過 preprocess.sar.lee_filter。

    >>> pre = np.full((10, 10), -10.0)
    >>> post = pre.copy()
    >>> post[2:6, 2:6] = -4.0          # 16 像元回波增強 6 dB
    >>> post[8, 8] = -2.0              # 單像元 speckle
    >>> res = detect_landslides(pre, post, cell_size_m=10.0, min_pixels=4)
    >>> int(res.mask.sum()), int((res.sign > 0).sum())
    (16, 16)
    """
    delta = log_ratio(pre_db, post_db)
    valid = ~np.isnan(delta)
    d = np.nan_to_num(delta, nan=0.0)

    changed = valid & (d >= threshold_db)
    if include_decrease:
        changed |= valid & (d <= -threshold_db)
    if invalid_mask is not None:
        changed &= ~np.asarray(invalid_mask, dtype=bool)
    if exclude_mask is not None:
        changed &= ~np.asarray(exclude_mask, dtype=bool)

    mask = remove_small_components(changed, min_pixels)
    sign = np.where(mask, np.sign(d), 0).astype("int8")
    return LandslideResult(mask=mask, sign=sign, threshold_db=float(threshold_db),
                           cell_size_m=cell_size_m, date=date)


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"landslide: {total - fails}/{total} 通過")

    # 示範：均勻植生坡 + speckle，中間一塊崩塌（回波 +5 dB）
    from pipeline.preprocess.sar import lee_filter, linear_to_db
    rng = np.random.default_rng(1)
    size = 60
    base_lin = 10 ** (-9.0 / 10)
    pre = linear_to_db(rng.gamma(4.4, base_lin / 4.4, (size, size)))
    post_lin = np.full((size, size), base_lin)
    post_lin[20:35, 25:40] *= 10 ** (5.0 / 10)
    post = linear_to_db(rng.gamma(4.4, post_lin / 4.4))
    res = detect_landslides(lee_filter(pre), lee_filter(post), cell_size_m=10.0)
    print(f"\n真實崩塌 225 像元（2.25 公頃），偵測：{res.summary()}")
