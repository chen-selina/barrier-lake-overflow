#!/usr/bin/env python3
"""
真實事件前後 Sentinel-1 → 新增水體／崩塌 → 疑似堰塞湖 A/B/C

    python scripts/analyze_sar_change.py         --pre  ../data/raw/sentinel1/S1_VV_pre_matai_an.tif         --post ../data/raw/sentinel1/S1_VV_post_matai_an.tif         --post-later ../data/raw/sentinel1/S1_VV_post2_matai_an.tif         --dem  ../data/raw/sentinel1/NASADEM_matai_an.tif         --orbit ASCENDING         --lon 121.29752 --lat 23.70061 --lake-id bl071         --pre-label "2025-06-01~07-18 中位數" --post-label "2025-07-25~08-10 中位數"         --ndwi-json ../data/derived/real_water_bl071.json         --out ../data/derived/real_sar_bl071.json

GEE 匯出（Code Editor 執行）。四張圖要同 region / scale / crs，否則過不了 check_aligned：

    var aoi = ee.Geometry.Point([121.29752, 23.70061]).buffer(5000).bounds();
    var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
      .filterBounds(aoi)
      .filter(ee.Filter.eq('instrumentMode', 'IW'))
      .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
      .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'));
    // 前後要同一條相對軌道，不然回波差異大多來自觀測幾何。先看有哪些軌道：
    print(s1.aggregate_histogram('relativeOrbitNumber_start'));
    var orbit = 69;   // 佔位值，換成上面印出、前後期都有影像的軌道號
    s1 = s1.filter(ee.Filter.eq('relativeOrbitNumber_start', orbit));
    // dB 取中位數等同線性取中位數，也順便壓 speckle
    var pre   = s1.filterDate('2025-06-01', '2025-07-18').select('VV').median();
    var post  = s1.filterDate('2025-07-25', '2025-08-10').select('VV').median();
    var post2 = s1.filterDate('2025-08-10', '2025-08-31').select('VV').median();
    var dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation').resample('bilinear');
    var opt = {crs: 'EPSG:4326', scale: 10, region: aoi, maxPixels: 1e9};
    Export.image.toDrive(Object.assign({image: pre.toFloat(),   description: 'S1_VV_pre_matai_an'}, opt));
    Export.image.toDrive(Object.assign({image: post.toFloat(),  description: 'S1_VV_post_matai_an'}, opt));
    Export.image.toDrive(Object.assign({image: post2.toFloat(), description: 'S1_VV_post2_matai_an'}, opt));
    Export.image.toDrive(Object.assign({image: dem.toFloat(),   description: 'NASADEM_matai_an'}, opt));

--orbit 要和 orbitProperties_pass 一致，它決定視向，會影響陰影／疊置遮罩。

流程：裁 4 km 視窗 → run_sar_chain → 每個候選輸出經緯度、和壩址距離、
湖面多邊形；有 --ndwi-json 時和光學結果比對面積。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from analyze_ndwi_change import crop_window, mask_to_lonlat_polygon, merge_into_dashboard_layer  # noqa: E402
from pipeline.detect.barrier_lake import EIGHT, run_sar_chain  # noqa: E402
from scipy import ndimage  # noqa: E402
from pipeline.preprocess.mask import S1_IW_MID_INCIDENCE_DEG, S1_LOOK_AZIMUTH_DEG  # noqa: E402
from pipeline.preprocess.sar import cell_size_xy_m, check_aligned, lee_filter, load_s1_geotiff  # noqa: E402


def distance_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    dlat = (lat2 - lat1) * 111320.0
    dlon = (lon2 - lon1) * 111320.0 * math.cos(math.radians(lat1))
    return math.hypot(dlat, dlon)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pre", required=True, help="事件前 σ⁰ VV（dB）GeoTIFF")
    ap.add_argument("--post", required=True, help="事件後 σ⁰ VV（dB）GeoTIFF")
    ap.add_argument("--post-later", nargs="*", default=[],
                    help="之後各期 σ⁰（多時相持續性判據用；不給則最高只到 B 級）")
    ap.add_argument("--dem", default=None,
                    help="事件前 DEM，同網格。不給就跳過陰影／疊置遮罩、DEM 河網與壩體位置檢核")
    ap.add_argument("--orbit", choices=sorted(S1_LOOK_AZIMUTH_DEG), default="ASCENDING")
    ap.add_argument("--incidence-deg", type=float, default=S1_IW_MID_INCIDENCE_DEG)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lake-id", required=True)
    ap.add_argument("--half-width-km", type=float, default=2.0)
    ap.add_argument("--water-threshold-db", type=float, default=None,
                    help="固定水體門檻（dB）。不給則 Otsu，Otsu 不合理時退回 −18 dB")
    ap.add_argument("--landslide-threshold-db", type=float, default=3.0)
    ap.add_argument("--min-lake-area-m2", type=float, default=5000.0)
    ap.add_argument("--min-catchment-km2", type=float, default=1.0)
    ap.add_argument("--search-radius-m", type=float, default=500.0)
    ap.add_argument("--dashboard-out", default=None,
                    help="給的話把等級最高、面積最大的候選多邊形寫進 dashboard/data/inundation.js"
                         "（只覆蓋這個 lake-id）。沒有候選就不寫")
    ap.add_argument("--debug-components", action="store_true",
                    help="列出所有新增水體連通塊（含被淘汰的）與淘汰原因，除錯用")
    ap.add_argument("--max-water-slope-deg", type=float, default=20.0,
                    help="坡度超過此值不判水（預設 20）。陡峭窄谷配 30 m DEM 時湖面可能被整片遮掉")
    ap.add_argument("--pre-label", default="事件前")
    ap.add_argument("--post-label", default="事件後")
    ap.add_argument("--ndwi-json", default=None, help="analyze_ndwi_change.py 的輸出，交叉驗證用")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    scenes = [load_s1_geotiff(args.pre), load_s1_geotiff(args.post)]
    scenes += [load_s1_geotiff(p) for p in args.post_later]
    names = ["pre", "post"] + [f"post-later[{i}]" for i in range(len(args.post_later))]
    dem = load_s1_geotiff(args.dem) if args.dem else None   # 單波段通用讀檔，值是高程（m）
    rasters = scenes + ([dem] if dem else [])
    try:
        check_aligned(*rasters, names=tuple(names + (["dem"] if dem else [])))
    except ValueError as e:
        raise SystemExit(str(e))
    if not scenes[0]["geographic"]:
        raise SystemExit("目前只支援 EPSG:4326 匯出（裁切視窗以經緯度計算），請依檔頭 GEE 腳本重新匯出。")

    wins = []
    for sc in scenes:
        win, row0, col0 = crop_window(sc, args.lon, args.lat, args.half_width_km, key="db")
        wins.append(win)
    dem_win = crop_window(dem, args.lon, args.lat, args.half_width_km, key="db")[0] if dem else None

    a, b, c, d, e, f = scenes[0]["transform"]
    win_transform = (a, b, c + col0 * a + row0 * b, d, e, f + col0 * d + row0 * e)
    dx, dy = cell_size_xy_m(scenes[0]["transform"], True, center_lat=args.lat)

    out = run_sar_chain(
        wins[0], wins[1], (dx, dy), dem=dem_win, later_post_dbs=wins[2:],
        transform=win_transform,
        incidence_deg=args.incidence_deg, look_azimuth_deg=S1_LOOK_AZIMUTH_DEG[args.orbit],
        water_threshold_db=args.water_threshold_db,
        landslide_threshold_db=args.landslide_threshold_db,
        min_catchment_km2=args.min_catchment_km2,
        dates=[args.pre_label, args.post_label] + [f"後續第{i + 1}期" for i in range(len(wins) - 2)],
        min_area_m2=args.min_lake_area_m2, search_radius_m=args.search_radius_m,
        max_water_slope_deg=args.max_water_slope_deg,
    )

    candidates = []
    for cand in out["candidates"]:
        entry = cand.to_dict()
        if cand.centroid_xy:
            lon, lat = cand.centroid_xy
            entry["centroidLonLat"] = [round(lon, 6), round(lat, 6)]
            entry["distanceFromDamM"] = round(distance_m(args.lon, args.lat, lon, lat), 1)
        entry["polygonLonLat"] = mask_to_lonlat_polygon(cand.mask, scenes[0]["transform"], row0, col0)
        candidates.append(entry)

    invalid = out["invalid"]
    area_px = dx * dy / 1e4

    # 診斷：事件後影像裡「夠暗、像水」的像元，有多少被遮罩擋掉。
    # 比例很高代表湖面落在遮罩裡，候選為空不一定是影像上沒有湖。
    thr = out["post_water"].threshold
    post_w = lee_filter(wins[1], size=3)
    pre_w = lee_filter(wins[0], size=3)
    with np.errstate(invalid="ignore"):
        dark_new = (post_w < thr) & ~(pre_w < thr)
    dark_new_ha = float(dark_new.sum()) * area_px
    masked_ha = float((dark_new & invalid["water"]).sum()) * area_px if invalid is not None else 0.0
    slope_only = None
    if invalid is not None:
        geom = invalid["layover"] | invalid["shadow"]
        slope_only = invalid["water"] & ~geom
    result = {
        "lakeId": args.lake_id,
        "synthetic": False,
        "source": "Sentinel-1 GRD σ⁰ VV（Google Earth Engine 匯出），非合成資料",
        "orbit": args.orbit,
        "analysisWindowKm": args.half_width_km * 2,
        "cellSizeM": [round(dx, 2), round(dy, 2)],
        "pre": out["pre_water"].summary(),
        "post": out["post_water"].summary(),
        "newWaterTotalAreaHectare": round(float(out["new_water"].sum()) * area_px, 3),
        "landslide": out["landslides"].summary(),
        "geometryMask": None if invalid is None else {
            "layoverHectare": round(float(invalid["layover"].sum()) * area_px, 2),
            "shadowHectare": round(float(invalid["shadow"].sum()) * area_px, 2),
            "excludedForWaterPct": round(100.0 * float(invalid["water"].mean()), 1),
            "slopeOnlyExcludedHectare": round(float(slope_only.sum()) * area_px, 2),
            "maxWaterSlopeDeg": args.max_water_slope_deg,
        },
        "darkNewPixelsDiagnostic": {
            "note": "事件後比門檻暗、事件前不暗的像元（遮罩前）；maskedPct 高代表湖面被遮罩擋掉",
            "thresholdDb": thr,
            "darkNewHectareBeforeMask": round(dark_new_ha, 2),
            "maskedHectare": round(masked_ha, 2),
            "maskedPct": round(100.0 * masked_ha / dark_new_ha, 1) if dark_new_ha else None,
        },
        "laterScenes": len(wins) - 2,
        "candidates": candidates,
    }

    if args.ndwi_json and os.path.exists(args.ndwi_json):
        with open(args.ndwi_json, encoding="utf-8") as fh:
            ndwi = json.load(fh)
        optical = ndwi.get("newWaterLargestComponentAreaHectare")
        top = candidates[0]["areaHectare"] if candidates else None
        result["crossCheckNdwi"] = {
            "opticalLargestNewWaterHectare": optical,
            "sarTopCandidateHectare": top,
            "ratioSarToOptical": round(top / optical, 3) if optical and top else None,
        }

    if args.debug_components:
        # 跟 classify() 同樣的分塊方式（外擴 3 像元合併、河道外擴 2 像元），
        # 列出每一塊為什麼被保留或淘汰。
        nw = out["new_water"]
        groups, n = ndimage.label(ndimage.binary_dilation(nw, EIGHT, iterations=3), structure=EIGHT)
        labeled = np.where(nw, groups, 0)
        river = out["river"]
        river_zone = ndimage.binary_dilation(river, EIGHT, iterations=2)
        min_px = int(math.ceil(args.min_lake_area_m2 / (dx * dy)))
        a0, b0, c0, d0, e0, f0 = win_transform
        comps = []
        for lab in range(1, n + 1):
            comp = labeled == lab
            n_px = int(comp.sum())
            if n_px < 5:
                continue
            ys, xs = np.nonzero(comp)
            lon = a0 * (xs.mean() + 0.5) + c0
            lat = e0 * (ys.mean() + 0.5) + f0
            on_river = bool((comp & river_zone).any()
                            or (ndimage.binary_dilation(comp, EIGHT) & river).any())
            elev = None
            if dem_win is not None:
                v = dem_win[comp]
                if np.isfinite(v).any():
                    elev = [round(float(np.nanmin(v))), round(float(np.nanmax(v)))]
            status = ("面積不足" if n_px < min_px else
                      "未貼河道" if not on_river else "保留（見 candidates）")
            comps.append({
                "areaHectare": round(n_px * area_px, 3),
                "centroidLonLat": [round(float(lon), 6), round(float(lat), 6)],
                "distanceFromDamM": round(distance_m(args.lon, args.lat, lon, lat), 1),
                "demMinMaxM": elev,
                "onRiver": on_river,
                "status": status,
            })
        comps.sort(key=lambda c: -c["areaHectare"])
        result["debugComponents"] = {
            "note": "所有 ≥5 像元的新增水體塊，依面積排序；min_lake_area 換算為 %d 像元" % min_px,
            "riverHectare": round(float(river.sum()) * area_px, 2),
            "components": comps[:15],
        }

    if args.dashboard_out:
        if candidates and len(candidates[0]["polygonLonLat"]) >= 3:
            top = candidates[0]
            date_txt = args.post_label.removeprefix("post ").strip()
            entry = {
                "lakeId": args.lake_id,
                "synthetic": False,
                "source": "sentinel1_sar",
                "grade": top["grade"],
                "detectedOn": date_txt,
                "sourceLabel": f"Sentinel-1 SAR 偵測到的新增水體範圍（證據強度 {top['grade']} 級，{date_txt}）",
                "note": (f"Sentinel-1 SAR 事件前後變化偵測（{args.pre_label} → {date_txt}，"
                         f"{args.orbit}），{top['grade']} 級候選，新增水體 {top['areaHectare']} 公頃，"
                         f"距壩址座標 {top.get('distanceFromDamM')} 公尺。"
                         "雷達陰影／陡坡遮罩會擋掉部分湖面，面積偏低，不可直接用於蓄水量。"),
                "areaHectare": top["areaHectare"],
                "waterElevationM": None,
                "volumeWanM3": None,
                "reasons": top.get("reasons", []),
                "polygonLonLat": top["polygonLonLat"],
            }
            merge_into_dashboard_layer(args.dashboard_out, args.lake_id, entry)
            print(f"\n已更新 {args.dashboard_out}（{args.lake_id}：{top['grade']} 級，{top['areaHectare']} 公頃）")
        else:
            print(f"\n（沒有候選，不寫入 {args.dashboard_out}）")

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    printable = dict(result, candidates=[{k: v for k, v in cd.items() if k != "polygonLonLat"}
                                         for cd in candidates])
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    print(f"\n寫入 {args.out}")


if __name__ == "__main__":
    main()