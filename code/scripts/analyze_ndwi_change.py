#!/usr/bin/env python3
"""
analyze_ndwi_change.py — 拿真實的事件前後 NDWI GeoTIFF 跑一次 B1 水體變化偵測

跟 `pipeline.detect.water` 的關係：這裡只是把該模組已經測過的純函式
（`water_mask`、`change_detection`）接上真實資料的一次性分析腳本，不是
pipeline 套件的一部分——真實影像檔案在使用者本機（例如從 Google Earth
Engine 匯出），路徑因人而異，不適合寫死進可攜的 pipeline 模組裡。

用法（於 code/ 目錄下）：
    python scripts/analyze_ndwi_change.py \
        --before ../data/raw/sentinel2/NDWI_before_matai_an.tif \
        --after  ../data/raw/sentinel2/NDWI_after_matai_an.tif \
        --lon 121.29752 --lat 23.70061 --lake-id bl071 \
        --out ../data/derived/real_water_bl071.json

流程：
1. 讀兩張已經算好 NDWI 的 GeoTIFF（`load_ndwi_geotiff`），確認網格對齊
   （同尺寸、同 transform、同 CRS）——對不齊就直接停，不做任何隱性 resample。
2. 裁出壩址附近的分析視窗（預設 4km 見方），避免整張大圖裡跟事件無關的
   其他變化（例如遠處農地/雲影殘留）混進「新增水體」的統計。
3. 各自跑 Otsu 自動門檻二值化，算 change_detection() = 事件後 水體
   且非事件前水體。
4. 用 scipy.ndimage.label 抓最大連通塊（= 候選堰塞湖本體），跟壩址座標
   算質心距離，當作「這塊新增水體是不是真的在壩址附近」的粗略檢核——
   這是 detect/barrier_lake.py（未實作）「新增水體 × 上游崩塌 × 河道
   相交」判定的簡化版，只做了其中「位置合理性」這一項。
5. 結果存成 JSON，附上分析視窗大小、門檻方法、真實面積等，供 C1/C2 之後
   串接使用，也可以直接引用到提案書當作「真實資料跑過 B1」的證據。
"""

from __future__ import annotations

import argparse
import json
import math

import numpy as np
from scipy import ndimage

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.detect.water import load_ndwi_geotiff, water_mask, change_detection, WaterExtent


def crop_window(data: dict, center_lon: float, center_lat: float, half_width_km: float) -> tuple:
    """
    以 (center_lon, center_lat) 為中心，裁出 half_width_km 公里半寬的方形視窗。
    回傳 (裁切後 ndwi array, row0, col0)——row0/col0 供後續換算裁切區域內
    像元座標回原圖用。
    """
    t = data["transform"]
    a, b, c, d, e, f = t  # affine: x = a*col + c, y = e*row + f
    deg_per_km_lat = 1.0 / 111.32
    deg_per_km_lon = 1.0 / (111.32 * math.cos(math.radians(center_lat)))
    half_lat = half_width_km * deg_per_km_lat
    half_lon = half_width_km * deg_per_km_lon

    def lonlat_to_rowcol(lon, lat):
        col = (lon - c) / a
        row = (lat - f) / e
        return row, col

    r0, c0 = lonlat_to_rowcol(center_lon - half_lon, center_lat + half_lat)
    r1, c1 = lonlat_to_rowcol(center_lon + half_lon, center_lat - half_lat)
    rows, cols = data["ndwi"].shape
    row0, row1 = sorted([int(round(r0)), int(round(r1))])
    col0, col1 = sorted([int(round(c0)), int(round(c1))])
    row0, row1 = max(0, row0), min(rows, row1)
    col0, col1 = max(0, col0), min(cols, col1)
    return data["ndwi"][row0:row1, col0:col1], row0, col0


def largest_component(mask: np.ndarray) -> tuple:
    """回傳 (最大連通塊遮罩, 像元數)；沒有任何 True 就回傳 (全 False, 0)。"""
    if not mask.any():
        return np.zeros_like(mask), 0
    labeled, n = ndimage.label(mask)
    if n == 0:
        return np.zeros_like(mask), 0
    sizes = ndimage.sum(mask, labeled, range(1, n + 1))
    biggest_label = int(np.argmax(sizes)) + 1
    biggest = labeled == biggest_label
    return biggest, int(sizes[int(np.argmax(sizes))])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lake-id", required=True)
    ap.add_argument("--half-width-km", type=float, default=2.0)
    ap.add_argument("--threshold", type=float, default=None,
                     help="固定 NDWI 門檻（McFeeters 慣例 0.0）。不給則用 Otsu 自動門檻——"
                          "但真實山區複雜地形常會被 Otsu 抓到「陰影 vs 非陰影」而不是"
                          "「水 vs 非水」這個分界，建議真實資料明確指定固定門檻。")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    before = load_ndwi_geotiff(args.before)
    after = load_ndwi_geotiff(args.after)

    if before["ndwi"].shape != after["ndwi"].shape or before["transform"] != after["transform"]:
        raise SystemExit(
            "before/after 網格不對齊（尺寸或 transform 不同），"
            "需要重新匯出成同一個 region/scale/crs，不做隱性 resample。"
        )

    before_win, row0, col0 = crop_window(before, args.lon, args.lat, args.half_width_km)
    after_win, _, _ = crop_window(after, args.lon, args.lat, args.half_width_km)
    cell_size_m = before["cell_size_m"] * 111320.0  # 度轉公尺（緯度方向近似）

    before_mask, before_t = water_mask(before_win, threshold=args.threshold)
    after_mask, after_t = water_mask(after_win, threshold=args.threshold)
    method = "fixed" if args.threshold is not None else "otsu"

    before_extent = WaterExtent(mask=before_mask, threshold=before_t, method=method,
                                 cell_size_m=cell_size_m, date="事件前合成影像")
    after_extent = WaterExtent(mask=after_mask, threshold=after_t, method=method,
                                cell_size_m=cell_size_m, date="事件後合成影像")

    new_water = change_detection(before_extent, after_extent)
    biggest, biggest_px = largest_component(new_water)

    rows, cols = new_water.shape
    ys, xs = np.where(biggest)
    centroid_note = None
    if biggest_px > 0:
        centroid_row = row0 + ys.mean()
        centroid_col = col0 + xs.mean()
        t = before["transform"]
        a, b, c, d, e, f = t
        centroid_lon = a * centroid_col + c
        centroid_lat = e * centroid_row + f
        dlat_m = (centroid_lat - args.lat) * 111320.0
        dlon_m = (centroid_lon - args.lon) * 111320.0 * math.cos(math.radians(args.lat))
        dist_m = math.hypot(dlat_m, dlon_m)
        centroid_note = {"lon": centroid_lon, "lat": centroid_lat, "distance_from_dam_m": round(dist_m, 1)}

    result = {
        "lakeId": args.lake_id,
        "synthetic": False,
        "source": "Sentinel-2 NDWI（Google Earth Engine 匯出），非合成資料",
        "analysisWindowKm": args.half_width_km * 2,
        "before": {"threshold": round(before_t, 4), "method": method,
                    "areaHectare": round(before_extent.area_hectare, 3)},
        "after": {"threshold": round(after_t, 4), "method": method,
                   "areaHectare": round(after_extent.area_hectare, 3)},
        "newWaterTotalAreaHectare": round(float(new_water.sum()) * (cell_size_m ** 2) / 1e4, 3),
        "newWaterLargestComponentAreaHectare": round(biggest_px * (cell_size_m ** 2) / 1e4, 3),
        "largestComponentCentroid": centroid_note,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n寫入 {args.out}")


if __name__ == "__main__":
    main()
