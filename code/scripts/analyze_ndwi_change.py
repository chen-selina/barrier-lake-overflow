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
        --threshold 0.0 \
        --before-label "2025-06-01~07-18 中位數合成" \
        --after-label "2025-07-25~09-15 中位數合成" \
        --out ../data/derived/real_water_bl071.json \
        --dashboard-out dashboard/data/inundation.js

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


def mask_to_lonlat_polygon(mask: np.ndarray, transform: tuple, row0: int, col0: int,
                            simplify_tolerance_deg: float = 0.0003) -> list:
    """
    把裁切視窗內的遮罩轉成原圖座標系下的 (lon, lat) 多邊形外環頂點清單。

    `transform` 是原圖（未裁切）的 affine 六元組；視窗左上角在原圖的
    (row0, col0)，只要把 affine 的平移項 (c, f) 往視窗方向挪過去即可，
    不用另外處理縮放/旋轉——這幾張 GeoTIFF 都是北向上、無旋轉。
    找不到任何多邊形（遮罩全空）回傳 None。
    """
    from rasterio import features
    from rasterio.transform import Affine
    from shapely.geometry import shape
    from shapely.ops import unary_union

    if not mask.any():
        return None

    a, b, c, d, e, f = transform
    window_transform = Affine(a, b, c + col0 * a + row0 * b, d, e, f + col0 * d + row0 * e)

    polys = [shape(geom) for geom, value in
             features.shapes(mask.astype("uint8"), mask=mask, transform=window_transform)
             if value == 1]
    if not polys:
        return None
    merged = unary_union(polys)
    if merged.geom_type == "MultiPolygon":
        merged = max(merged.geoms, key=lambda g: g.area)
    simplified = merged.simplify(simplify_tolerance_deg, preserve_topology=True)
    return [list(pt) for pt in simplified.exterior.coords]


def merge_into_dashboard_layer(path: str, lake_id: str, entry: dict) -> None:
    """
    把 entry 合併進 `dashboard/data/inundation.js` 的 `window.INUNDATION_DEMO`
    物件，只覆蓋 lake_id 這一筆，保留其他湖既有的資料（例如
    `pipeline.assess.dashboard_export` 產生的合成示範資料）。
    """
    import os

    existing = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        start, end = text.index("{"), text.rindex("}") + 1
        existing = json.loads(text[start:end])

    existing[lake_id] = entry
    with open(path, "w", encoding="utf-8") as f:
        f.write("// 由 pipeline.assess.dashboard_export（合成示範）與\n")
        f.write("// scripts/analyze_ndwi_change.py（真實 Sentinel-2 NDWI 資料）共同維護，\n")
        f.write("// 每筆各自的 synthetic 欄位標明資料來源，請勿手動編輯\n")
        f.write(f"window.INUNDATION_DEMO = {json.dumps(existing, ensure_ascii=False, indent=2)};\n")


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
    ap.add_argument("--dashboard-out", default=None,
                     help="有給的話，把偵測到的最大連通塊多邊形合併寫進這份 "
                          "dashboard/data/inundation.js（只覆蓋這個 lake-id，"
                          "不動其他湖既有的資料）。")
    ap.add_argument("--before-label", default="事件前", help="存進結果 JSON 的日期/期間描述文字")
    ap.add_argument("--after-label", default="事件後", help="存進結果 JSON 的日期/期間描述文字")
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
                                 cell_size_m=cell_size_m, date=args.before_label)
    after_extent = WaterExtent(mask=after_mask, threshold=after_t, method=method,
                                cell_size_m=cell_size_m, date=args.after_label)

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

    polygon_lonlat = mask_to_lonlat_polygon(biggest, before["transform"], row0, col0)

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
        "polygonLonLat": polygon_lonlat,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n寫入 {args.out}")

    if args.dashboard_out:
        if not polygon_lonlat or len(polygon_lonlat) < 3:
            print(f"\n（沒有偵測到有效多邊形，不寫入 {args.dashboard_out}）")
        else:
            dashboard_entry = {
                "lakeId": args.lake_id,
                "synthetic": False,
                "note": (f"Sentinel-2 NDWI 真實影像偵測到的新增水體範圍（{args.before_label} → "
                         f"{args.after_label}），非模擬淹沒範圍；門檻={method}"
                         f"({round(before_t, 3) if method == 'fixed' else 'auto'})，"
                         f"最大連通塊 {round(biggest_px * (cell_size_m ** 2) / 1e4, 1)} 公頃，"
                         f"距壩址座標 {centroid_note['distance_from_dam_m'] if centroid_note else '—'} 公尺。"),
                "areaHectare": round(biggest_px * (cell_size_m ** 2) / 1e4, 3),
                "waterElevationM": None,
                "volumeWanM3": None,
                "polygonLonLat": polygon_lonlat,
            }
            merge_into_dashboard_layer(args.dashboard_out, args.lake_id, dashboard_entry)
            print(f"已合併寫入 {args.dashboard_out}（lakeId={args.lake_id}）")


if __name__ == "__main__":
    main()
