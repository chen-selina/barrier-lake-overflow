#!/usr/bin/env python3
"""
真實村里界線 × SEGIS 人口 × bl071 偵測水體 → 暴露人口

    data/raw/boundaries/VILLAGE_NLSC_1150817.shp
        村里界圖（data.gov.tw/dataset/7438）
    data/raw/population/TW-04-301000000A-010001/114年12月行政區人口統計_村里_花蓮縣.csv
        SEGIS 114 年 12 月村里人口

疊合的多邊形是 inundation.js 裡 bl071 的 polygonLonLat，也就是 NDWI 偵測到的
湖面，不是潰壩淹沒範圍。有下游淹沒結果後，換掉 inundation_polygon 即可。

    python scripts/run_exposure_real.py
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
    SEGIS CSV 有兩列表頭，第二列（中文說明）要跳過。
    V_ID 是 "10015120-004"，去掉連字號就是村里界圖的 VILLCODE。
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
                  "，疊合對象為 NDWI 偵測到的湖面範圍（非淹沒模擬）",
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
