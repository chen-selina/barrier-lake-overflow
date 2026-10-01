#!/usr/bin/env python3
"""
Sentinel-1 前處理

GEE 的 COPERNICUS/S1_GRD 已經做完軌道修正、熱雜訊去除、輻射與地形校正，
像元值是 σ⁰（dB）。這裡只補 speckle 濾波和網格檢查，匯出腳本見
scripts/analyze_sar_change.py。

- load_s1_geotiff：讀檔，回傳格式同 detect.water.load_ndwi_geotiff
- lee_filter：Lee 濾波，在線性功率域算，輸入輸出都是 dB
- check_aligned：網格不一致直接丟錯，不偷偷 resample

    python -m pipeline.preprocess.sar
"""

from __future__ import annotations

import math

import numpy as np
from scipy import ndimage


# Sentinel-1 IW GRD 的等效視數（ENL），ESA 產品規格約 4.4；
# Lee 濾波用它估計乘性雜訊的變異係數 Cu = 1/sqrt(ENL)。
S1_IW_GRD_ENL = 4.4

# 一度緯度約 111.32 km；GEE 預設以 EPSG:4326 匯出時像元大小是「度」。
M_PER_DEG_LAT = 111320.0


# GeoTIFF 讀取（rasterio 延遲 import，同 water.load_ndwi_geotiff）

def load_s1_geotiff(path: str, band: int = 1) -> dict:
    """
    讀取 GEE 匯出的 Sentinel-1 σ⁰（dB）GeoTIFF。

    回傳 dict：`{"db": array, "cell_size_m": float, "cell_size_xy_m":
    (dx, dy), "transform": affine 六元組, "crs": str, "bounds": (w, s, e, n),
    "geographic": bool}`。

    地理座標（EPSG:4326）匯出時像元是「度」：`cell_size_xy_m` 會依影像
    中心緯度把經向乘上 cos(lat) 換成公尺，`cell_size_m` 取 sqrt(dx·dy)
    當等效邊長（面積用），不像 NDWI 那支 script 直接拿緯度方向近似。
    """
    try:
        import rasterio
    except ImportError as e:  # pragma: no cover
        raise ImportError("讀取 Sentinel-1 GeoTIFF 需要 rasterio（見 requirements.txt）。") from e

    with rasterio.open(path) as src:
        arr = src.read(band).astype("float64")
        if src.nodata is not None:
            arr = np.where(arr == src.nodata, np.nan, arr)
        t = src.transform
        geographic = bool(src.crs and src.crs.is_geographic)
        b = src.bounds
        info = {
            "db": arr,
            "transform": (t.a, t.b, t.c, t.d, t.e, t.f),
            "crs": str(src.crs) if src.crs else None,
            "bounds": (b.left, b.bottom, b.right, b.top),
            "geographic": geographic,
        }
    info["cell_size_xy_m"] = cell_size_xy_m(info["transform"], geographic,
                                            center_lat=(info["bounds"][1] + info["bounds"][3]) / 2)
    dx, dy = info["cell_size_xy_m"]
    info["cell_size_m"] = math.sqrt(dx * dy)
    return info


def cell_size_xy_m(transform: tuple, geographic: bool, center_lat: float = 0.0) -> tuple:
    """
    由 affine 六元組算 (dx, dy) 公尺。投影座標（例如 EPSG:3826）直接取
    |a|、|e|；地理座標把度換成公尺。

    >>> cell_size_xy_m((10.0, 0, 0, 0, -10.0, 0), geographic=False)
    (10.0, 10.0)
    >>> dx, dy = cell_size_xy_m((1e-4, 0, 0, 0, -1e-4, 0), geographic=True, center_lat=60.0)
    >>> round(dx, 3), round(dy, 3)
    (5.566, 11.132)
    """
    a, _, _, _, e, _ = transform
    if not geographic:
        return abs(a), abs(e)
    return (abs(a) * M_PER_DEG_LAT * math.cos(math.radians(center_lat)),
            abs(e) * M_PER_DEG_LAT)


# dB ↔ 線性功率

def db_to_linear(db: np.ndarray) -> np.ndarray:
    """
    >>> db_to_linear(np.array([0.0, -10.0, 10.0])).tolist()
    [1.0, 0.1, 10.0]
    """
    return np.power(10.0, np.asarray(db, dtype="float64") / 10.0)


def linear_to_db(lin: np.ndarray, floor: float = 1e-10) -> np.ndarray:
    """
    功率轉 dB；≤0 的值先夾到 floor，避免 log10(0)。

    >>> linear_to_db(np.array([1.0, 0.01])).tolist()
    [0.0, -20.0]
    """
    lin = np.asarray(lin, dtype="float64")
    return 10.0 * np.log10(np.maximum(lin, floor))


# Lee speckle 濾波

def lee_filter(img_db: np.ndarray, size: int = 5, enl: float = S1_IW_GRD_ENL) -> np.ndarray:
    """
    Lee（1980）乘性雜訊模型濾波：

        Cu² = 1/ENL                 （雜訊變異係數平方）
        Ci² = Var_local / Mean_local²
        w   = max(0, 1 − Cu²/Ci²)
        out = Mean_local + w · (I − Mean_local)

    均勻區（Ci≈Cu）w→0，輸出≈局部平均（壓掉 speckle）；邊緣／點目標
    （Ci≫Cu）w→1，保留原值（不糊掉水陸邊界）。在線性功率域計算，輸入
    輸出都是 dB。nan 像元不參與鄰域統計，輸出仍為 nan。

    >>> rng = np.random.default_rng(0)
    >>> flat = linear_to_db(rng.gamma(4.4, 0.1 / 4.4, (60, 60)))  # 均勻區 + speckle
    >>> bool(np.std(lee_filter(flat)) < np.std(flat) / 2)
    True
    """
    db = np.asarray(img_db, dtype="float64")
    valid = ~np.isnan(db)
    lin = np.where(valid, db_to_linear(np.where(valid, db, 0.0)), 0.0)
    w_valid = ndimage.uniform_filter(valid.astype("float64"), size=size, mode="nearest")

    with np.errstate(invalid="ignore", divide="ignore"):
        mean = ndimage.uniform_filter(lin, size=size, mode="nearest") / w_valid
        sq_mean = ndimage.uniform_filter(lin ** 2, size=size, mode="nearest") / w_valid
        var = np.maximum(sq_mean - mean ** 2, 0.0)
        ci2 = var / mean ** 2
        cu2 = 1.0 / enl
        weight = np.clip(1.0 - cu2 / ci2, 0.0, 1.0)
    weight = np.nan_to_num(weight, nan=0.0)
    out = mean + weight * (lin - mean)
    return np.where(valid, linear_to_db(out), np.nan)


# 網格對齊檢查

def check_aligned(*rasters: dict, names: tuple = (), array_key: str = "db") -> None:
    """
    確認多張 raster（load_s1_geotiff / load_ndwi_geotiff / DEM 等 dict）
    同尺寸、同 transform、同 CRS；任何一項不同就丟 ValueError。
    dict 裡陣列的 key 依序找 array_key、"ndwi"、"dem"、"elevation"。

    >>> a = {"db": np.zeros((2, 2)), "transform": (10, 0, 0, 0, -10, 0), "crs": "EPSG:3826"}
    >>> check_aligned(a, dict(a))
    >>> b = dict(a, transform=(10, 0, 5, 0, -10, 0))
    >>> check_aligned(a, b, names=("pre", "post"))
    Traceback (most recent call last):
    ...
    ValueError: pre 與 post 的 transform 不一致，需重新匯出成同一 region/scale/crs（不做隱性 resample）
    """
    if len(rasters) < 2:
        return
    names = tuple(names) + tuple(f"#{i}" for i in range(len(names), len(rasters)))

    def arr(r):
        for k in (array_key, "ndwi", "dem", "elevation"):
            if k in r:
                return np.asarray(r[k])
        raise KeyError("raster dict 找不到陣列欄位")

    ref, ref_name = rasters[0], names[0]
    for r, name in zip(rasters[1:], names[1:]):
        problem = None
        if arr(r).shape != arr(ref).shape:
            problem = f"尺寸（{arr(ref).shape} vs {arr(r).shape}）"
        elif not np.allclose(r["transform"], ref["transform"]):
            problem = "transform"
        elif (r.get("crs") or None) != (ref.get("crs") or None):
            problem = "CRS"
        if problem:
            raise ValueError(f"{ref_name} 與 {name} 的 {problem} 不一致，"
                             "需重新匯出成同一 region/scale/crs（不做隱性 resample）")


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"sar: {total - fails}/{total} 通過")
