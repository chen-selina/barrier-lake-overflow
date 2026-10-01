#!/usr/bin/env python3
"""
run_hypsometry_real.py — B2：真實 DEM × 真實 NDWI 偵測面積，反推真實蓄水量

資料來源：
    data/raw/dem/DEM_matai_an.tif —— NASADEM（基於 SRTM，2025 事件前地形），
        Google Earth Engine 匯出，30m 解析度，EPSG:4326（見
        pipeline/assess/dashboard_export.py 的合成版對照，這裡換成真的檔案）

    GEE 匯出腳本（貼到 code.earthengine.google.com 執行，Tasks 分頁按
    Run，跑完到 Google Drive 下載）：

        var aoi = ee.Geometry.Rectangle([121.268, 23.673, 121.327, 23.728]);
        var dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation').clip(aoi);
        Export.image.toDrive({
          image: dem, description: 'DEM_matai_an',
          region: aoi, scale: 30, crs: 'EPSG:4326', maxPixels: 1e9
        });

跟原本規劃的差異——用真實偵測面積反推水位，不用新聞報導的壩高數字：
    新聞對馬太鞍溪壩高的估計從 120m 到 200m 都有，來源不一致，直接採信
    任一個數字都不夠站得住腳。這裡改用 `HypsometricCurve.elevation_at_area()`
    （B2 新增的反查方法）：拿 B1 對真實 Sentinel-2 NDWI 影像偵測到的湖面
    面積（data/derived/real_water_bl071.json 的
    newWaterLargestComponentAreaHectare），反推對應水位，再讀出該水位
    的容積——整條推論鏈只用了兩份真實遙測資料（DEM + NDWI），沒有引用
    任何無法驗證的新聞數字。

**關鍵限制，第一版直接對真實 DEM 跑就踩到了**：這份 DEM 是事件前
（~2000年 SRTM）地形，崩塌堆積體本身（真正擋住河道的東西）完全不在
這份 DEM 裡。從壩址往上游填洼沒問題，但**演算法沒有理由知道不該往
下游繼續填**——事件前的河道在壩址往下游本來就是持續往下流的通路，
一旦水位漲到某個馬鞍部（saddle）高程，連通填洼會直接「溢出」壩址、
灌進下游河道，範圍瞬間暴增到跟真正的堰塞湖完全無關的量級（實測：
867m 時連通面積僅 0.8 公頃，868m 一口氣跳到 137 公頃——這個斷崖式跳躍
本身就是「溢出下游」的訊號，不是真的水位–面積關係）。

處理方式：既然已知崩塌源頭座標在壩址正上游（北方，見
`崩塌X_TW/Y_TW`），下游方向就是壩址以南——把 DEM 裡壩址以南（南緯／
row 較大，只留一點緩衝避免誤傷壩址本身周邊）的像元全部設成 NaN 再跑，
連通填洼就沒有下游可以溢出，只會老實地往上游山谷擴張。這不是「調參數
調到我要的答案」，是把演算法沒有能力知道的物理限制（有一座壩擋著）用
已知的地理資訊（崩塌源頭方向）補回去。

座標系統注意：這份 DEM 是 EPSG:4326（經緯度），不是投影座標，1 度不等於
1 公尺，所以**不能**直接把 pixel size（度）當 cell_size_m 用——這裡用
緯度換算（跟 dashboard_export.py 的 KM_PER_DEGREE_LAT 是同一套換算），
分別算出經度、緯度方向的公尺級距，兩者相乘得到每個像元的真實面積。

用法（於 code/ 目錄下）：python scripts/run_hypsometry_real.py
"""

from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import rasterio
from scipy import ndimage

from pipeline.assess.hypsometry import build_hypsometric_curve, volume_error_rate
from pipeline.assess.backtest import backtest_report
from pipeline.assess.scale import classify_volume

DEM_PATH = "../data/raw/dem/DEM_matai_an.tif"
REAL_WATER_JSON = "../data/derived/real_water_bl071.json"
DAM_LON, DAM_LAT = 121.29752, 23.70061
# 崩塌源頭座標（taiwan-barrier-lakes.csv 第 71 列「崩塌X_TW/Y_TW」轉
# WGS84），確認在壩址正北方（上游）——反過來說，壩址以南就是下游，
# 不該算進水庫範圍。見下方 mask_downstream()。
SLIDE_LON, SLIDE_LAT = 121.29425305920354, 23.721241776670947
OFFICIAL_VOLUME_WAN_M3 = 9100.0
KM_PER_DEGREE_LAT = 111.32
DOWNSTREAM_BUFFER_PX = 2  # pour point 正下方留一點緩衝，避免誤傷壩址本身

# 掃描範圍：從壩址局部最低點往上掃多高，見下方「掃描上限」說明
CREST_SCAN_ABOVE_FLOOR_M = 300.0
ELEVATION_STEP_M = 1.0

# 找壩址真正河道最低點時，在目標像元四周找多大的視窗（像元數，非公尺）
POUR_POINT_SEARCH_RADIUS_PX = 3


def load_dem(path: str):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float64")
        if src.nodata is not None:
            arr = np.where(arr == src.nodata, np.nan, arr)
        return arr, src.transform


def find_pour_point(dem: np.ndarray, transform, lon: float, lat: float, radius_px: int):
    """
    30m 解析度下，壩址座標換算出的像元不一定精準落在河道最低點，
    在目標像元 ±radius_px 視窗內找真正的局部最低點當 pour point，
    比直接用座標換算出的像元更符合「連通填洼從河道出發」的物理意義。
    """
    col_f, row_f = ~transform * (lon, lat)
    r0, c0 = int(round(row_f)), int(round(col_f))
    r_lo, r_hi = max(0, r0 - radius_px), min(dem.shape[0], r0 + radius_px + 1)
    c_lo, c_hi = max(0, c0 - radius_px), min(dem.shape[1], c0 + radius_px + 1)
    window = dem[r_lo:r_hi, c_lo:c_hi]
    local_r, local_c = np.unravel_index(np.nanargmin(window), window.shape)
    return int(r_lo + local_r), int(c_lo + local_c)


def mask_downstream(dem: np.ndarray, transform, pour_point: tuple,
                     slide_lon: float, slide_lat: float, buffer_px: int) -> np.ndarray:
    """
    把壩址以南（下游方向）的像元設成 NaN，避免連通填洼溢出下游河道
    （見檔案開頭「關鍵限制」說明）。方向由崩塌源頭座標（已知在壩址
    正上游）決定：崩塌源頭 row 比壩址小，代表 row 變小＝往上游／北，
    所以 row 比 pour_point 大（且超過緩衝）的像元一律視為下游。
    """
    _, slide_row = ~transform * (slide_lon, slide_lat)
    if slide_row >= pour_point[0]:
        raise ValueError(
            "崩塌源頭座標的 row 不小於壩址 row，跟預期的「崩塌在上游」矛盾，"
            "這份 DEM 的方向假設可能不成立，需要人工確認再繼續。"
        )
    masked = dem.copy()
    masked[pour_point[0] + buffer_px + 1:, :] = np.nan
    return masked


def main() -> None:
    dem, transform = load_dem(DEM_PATH)

    # 每個像元真實面積（公尺²）：經度、緯度方向分別換算再相乘，
    # 不能直接假設「度」是正方形像元
    deg_lon = abs(transform.a)
    deg_lat = abs(transform.e)
    m_per_deg_lon = KM_PER_DEGREE_LAT * 1000.0 * math.cos(math.radians(DAM_LAT))
    m_per_deg_lat = KM_PER_DEGREE_LAT * 1000.0
    cell_w_m = deg_lon * m_per_deg_lon
    cell_h_m = deg_lat * m_per_deg_lat
    cell_area_m2 = cell_w_m * cell_h_m

    pour_point = find_pour_point(dem, transform, DAM_LON, DAM_LAT, POUR_POINT_SEARCH_RADIUS_PX)
    floor_elevation = float(dem[pour_point])
    crest_elevation = floor_elevation + CREST_SCAN_ABOVE_FLOOR_M

    dem_upstream_only = mask_downstream(dem, transform, pour_point, SLIDE_LON, SLIDE_LAT,
                                         DOWNSTREAM_BUFFER_PX)

    curve = build_hypsometric_curve(
        dem_upstream_only, pour_point=pour_point, cell_area_m2=cell_area_m2,
        floor_elevation=floor_elevation, crest_elevation=crest_elevation,
        elevation_step=ELEVATION_STEP_M,
    )

    with open(REAL_WATER_JSON, encoding="utf-8") as f:
        real_water = json.load(f)
    target_area_m2 = real_water["newWaterLargestComponentAreaHectare"] * 1e4

    max_area_on_curve = curve.points[-1][1]
    saturated = target_area_m2 >= max_area_on_curve

    # 斷崖檢查：找出「目標面積落在哪兩個取樣點之間」，如果那個區間本身
    # 面積暴增（例如溢出下游造成的斷崖，見檔案開頭「關鍵限制」），
    # elevation_at_area() 的線性內插結果就不是真的水位–面積關係，
    # 不該被當成可信數字——即使加了下游遮罩，這裡還是留著這道檢查，
    # 因為地形本來就可能還有其他方向的溢出路徑沒被遮罩排除。
    areas_only = [p[1] for p in curve.points]
    bracket_jump_ratio = None
    for i in range(len(areas_only) - 1):
        if areas_only[i] <= target_area_m2 <= areas_only[i + 1]:
            a0, a1 = areas_only[i], areas_only[i + 1]
            bracket_jump_ratio = (a1 / a0) if a0 > 0 else float("inf")
            break
    cliff_detected = bracket_jump_ratio is not None and bracket_jump_ratio > 5.0

    est_elevation = curve.elevation_at_area(target_area_m2)
    est_volume_wan_m3 = curve.volume_at(est_elevation)
    est_dam_height_m = est_elevation - floor_elevation
    err = volume_error_rate(est_volume_wan_m3, OFFICIAL_VOLUME_WAN_M3)

    result = {
        "lakeId": "bl071",
        "source": "NASADEM（GEE匯出，30m）+ B1 真實 NDWI 偵測面積反推水位，"
                   "非採信新聞報導壩高數字；已將壩址以南（下游）像元遮罩，"
                   "避免連通填洼溢出下游河道",
        "pourPointRowCol": list(pour_point),
        "floorElevationM": round(floor_elevation, 1),
        "crestScanUpToM": round(crest_elevation, 1),
        "cellAreaM2": round(cell_area_m2, 2),
        "targetAreaHectare": round(target_area_m2 / 1e4, 2),
        "curveSaturatedBeforeReachingTargetArea": saturated,
        "cliffDetectedAtTargetArea": cliff_detected,
        "bracketAreaJumpRatio": round(bracket_jump_ratio, 1) if bracket_jump_ratio else None,
        "estimatedWaterElevationM": round(est_elevation, 1),
        "estimatedDamHeightM": round(est_dam_height_m, 1),
        "estimatedVolumeWanM3": round(est_volume_wan_m3, 1),
        "officialVolumeWanM3": OFFICIAL_VOLUME_WAN_M3,
        "volumeErrorRate": round(err, 4),
        # 對外用這個，不報單一數字
        "volumeClass": classify_volume(
            est_volume_wan_m3, curve_ok=not (saturated or cliff_detected)).to_dict(),
        "officialVolumeClass": classify_volume(OFFICIAL_VOLUME_WAN_M3, rel_error=0.0).scale,
    }

    with open("../data/derived/real_hypsometry_bl071.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if saturated:
        print(f"\n⚠️ 警告：真實偵測面積 {target_area_m2/1e4:.2f} 公頃已經達到或超過"
              f"掃描範圍內曲線的最大面積 {max_area_on_curve/1e4:.2f} 公頃，"
              f"estimatedWaterElevationM 被夾在掃描上限，數字不可信，"
              f"需要加大 CREST_SCAN_ABOVE_FLOOR_M 重跑。")
    elif cliff_detected:
        print(f"\n⚠️ 警告：目標面積落在一個面積暴增 {bracket_jump_ratio:.1f} 倍的區間內"
              f"（疑似還有溢出路徑沒被遮罩排除，或地形本身有陡峭馬鞍部），"
              f"estimatedWaterElevationM/estimatedVolumeWanM3 不可信，需要人工檢查"
              f"（例如加大 DOWNSTREAM_BUFFER_PX、縮小 CREST_SCAN_ABOVE_FLOOR_M，"
              f"或人工畫出正確的水庫範圍遮罩）。")
    else:
        report = backtest_report(
            lake_name="花蓮馬太鞍溪（真實 DEM + 真實 NDWI 面積反推，C1 因無單一確切偵測日期暫略）",
            estimated_volume_wan_m3=est_volume_wan_m3,
            official_volume_wan_m3=OFFICIAL_VOLUME_WAN_M3,
        )
        with open("../data/derived/real_backtest_bl071.md", "w", encoding="utf-8") as f:
            f.write(report.to_markdown())
        print("\n已寫入 ../data/derived/real_backtest_bl071.md")


if __name__ == "__main__":
    main()
