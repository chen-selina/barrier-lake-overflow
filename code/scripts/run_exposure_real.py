#!/usr/bin/env python3
"""
run_exposure_real.py — B3：真實村里界線圖 × 真實 SEGIS 人口 × 真實偵測水體範圍

資料來源（皆已下載到 data/raw/，*.shp/*.csv 依 .gitignore 規則不進版控）：
    data/raw/boundaries/VILLAGE_NLSC_1150817.shp
        內政部國土測繪中心「村里界圖(TWD97經緯度)」（data.gov.tw/dataset/7438）
    data/raw/population/TW-04-301000000A-010001/114年12月行政區人口統計_村里_花蓮縣.csv
        SEGIS 社會經濟資料服務平台，114年12月（最新）行政區人口統計，村里級

**注意**：這裡疊合的是 `dashboard/data/inundation.js` 裡 bl071 的
`polygonLonLat`——那是 B1 對真實 Sentinel-2 NDWI 影像跑出來的「目前偵測
到的水體範圍」，不是「假設溢流會淹到哪裡」的淹沒模擬（B3 原始設計裡的
inundation.py bathtub 模擬，需要 B2 真實 DEM 反演出的水位才能跑，DEM
還沒到位）。這裡先用真實觀測到的水體範圍代入疊合邏輯，驗證 join／
overlay 邏輯在真實資料上正確；等 B2 有真實 DEM 反演出的溢流範圍，
直接把 inundation_polygon 換成那個結果即可，population_exposure_from_
villages() 不用改。

用法（於 code/ 目錄下）：python scripts/run_exposure_real.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from pipeline.assess.exposure import population_exposure_from_villages

BOUNDARY_SHP = "../data/raw/boundaries/VILLAGE_NLSC_1150817.shp"
POPULATION_CSV = ("../data/raw/population/TW-04-301000000A-010001/"
                   "114年12月行政區人口統計_村里_花蓮縣.csv")
INUNDATION_JS = "dashboard/data/inundation.js"
LAKE_ID = "bl071"


def load_population(path: str) -> pd.DataFrame:
    """
    SEGIS 匯出的 CSV 有兩列表頭（英文欄位代碼 + 中文說明），第二列
    （中文說明）要當一般資料列略過，不是真的資料。V_ID 格式是
    "10015120-004"（鄉鎮碼-村里序），村里界線圖的 VILLCODE 是無連字號
    的 11 碼（"10015120004"）——這裡統一成 VILLCODE 格式再 join，
    這正是施工地圖對照表提醒的「用代碼不用名稱 join」的實際操作。
    """
    df = pd.read_csv(path, dtype=str, skiprows=[1])
    df["VILLCODE"] = df["V_ID"].str.replace("-", "", regex=False)
    df["population"] = pd.to_numeric(df["P_CNT"], errors="coerce").fillna(0)
    return df


def load_inundation_polygon(js_path: str, lake_id: str) -> Polygon:
    with open(js_path, encoding="utf-8") as f:
        text = f.read()
    start, end = text.index("{"), text.rindex("}") + 1
    data = json.loads(text[start:end])
    entry = data[lake_id]
    if entry.get("synthetic") is not False:
        raise SystemExit(
            f"{lake_id} 的 inundation.js 資料不是標明為真實偵測結果"
            "（synthetic 應為 false），中止，避免拿合成示範資料算暴露人口。"
        )
    return Polygon(entry["polygonLonLat"])


def main() -> None:
    villages = gpd.read_file(BOUNDARY_SHP)
    if villages.crs is None or villages.crs.to_epsg() != 4326:
        villages = villages.set_crs("EPSG:4326", allow_override=True) if villages.crs is None else villages.to_crs("EPSG:4326")

    population = load_population(POPULATION_CSV)
    polygon = load_inundation_polygon(INUNDATION_JS, LAKE_ID)

    result = population_exposure_from_villages(polygon, villages, population)

    affected = [v for v in result.villages if v.overlap_area_m2 > 0]
    affected.sort(key=lambda v: -v.overlap_area_m2)

    summary = {
        "lakeId": LAKE_ID,
        "source": "村里界線圖 data.gov.tw/dataset/7438 + SEGIS 114年12月人口統計_村里_花蓮縣"
                  "，疊合對象為 B1 真實 NDWI 偵測水體範圍（非模擬淹沒範圍）",
        "inundationAreaHectare": round(result.inundation_area_m2 / 1e4, 3),
        "totalExposedPopulation": round(result.total_exposed_population, 1),
        "affectedVillages": [
            {
                "village_code": v.village_code,
                "village_name": v.village_name,
                "town": v.town,
                "population_total": v.population_total,
                "overlap_fraction": round(v.overlap_fraction, 4),
                "exposed_population": round(v.exposed_population, 1),
            }
            for v in affected
        ],
    }

    out_path = "../data/derived/real_exposure_bl071.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n寫入 {out_path}")


if __name__ == "__main__":
    main()
