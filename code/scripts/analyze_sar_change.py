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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from analyze_ndwi_change import crop_window, mask_to_lonlat_polygon  # noqa: E402
from pipeline.detect.barrier_lake import run_sar_chain  # noqa: E402
from pipeline.preprocess.mask import S1_IW_MID_INCIDENCE_DEG, S1_LOOK_AZIMUTH_DEG  # noqa: E402
from pipeline.preprocess.sar import cell_size_xy_m, check_aligned, load_s1_geotiff  # noqa: E402


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

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    printable = dict(result, candidates=[{k: v for k, v in cd.items() if k != "polygonLonLat"}
                                         for cd in candidates])
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    print(f"\n寫入 {args.out}")


if __name__ == "__main__":
    main()
