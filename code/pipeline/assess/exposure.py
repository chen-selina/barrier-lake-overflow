#!/usr/bin/env python3
"""
暴露人口：淹沒多邊形 × 村里界線 × 人口。

- 人口：SEGIS 村里人口（沒有幾何），用村里代碼 join 村里界圖
  （data.gov.tw/dataset/7438）。用代碼不用中文名，同名村里很多。
- 疊合是多邊形交集，依每個村里被覆蓋的面積比例分配人口。
- 備案：WorldPop 100 m 網格，見 population_exposure_from_grid()。

道路中斷、孤島聚落沒有做。

    python -m pipeline.assess.exposure
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# 資料結構

@dataclass
class VillageExposure:
    """單一村里的暴露結果。"""
    village_code: str
    village_name: str
    county: str
    town: str
    population_total: int
    village_area_m2: float
    overlap_area_m2: float
    exposed_population: float   # 依面積比例加權估算（非整數）

    @property
    def overlap_fraction(self) -> float:
        if self.village_area_m2 <= 0:
            return 0.0
        return self.overlap_area_m2 / self.village_area_m2


@dataclass
class ExposureSummary:
    villages: list
    total_exposed_population: float
    inundation_area_m2: float

    def top_n(self, n: int = 5) -> list:
        return sorted(self.villages, key=lambda v: v.exposed_population,
                      reverse=True)[:n]


# 核心：淹沒範圍 × 村里界線 疊合

# 村里人口表跟界線圖的欄位名稱常不完全一樣，這裡集中列出常見別名，
# 實際 join 前務必自己先 print 兩份資料的欄位名稱核對一次
# （不同年份下載的界線圖欄位命名可能改版）。
_CODE_COLUMN_CANDIDATES = ("VILLCODE", "VILL_ID", "V_CODE", "village_code")
_POP_COLUMN_CANDIDATES = ("population", "人口數", "pop_total", "POP")


def _first_matching_column(columns, candidates) -> Optional[str]:
    for name in candidates:
        if name in columns:
            return name
    return None


def population_exposure_from_villages(inundation_polygon, villages_gdf,
                                       population_df, code_col: Optional[str] = None,
                                       pop_col: Optional[str] = None) -> ExposureSummary:
    """
    主入口：淹沒範圍多邊形 × 村里界線（geopandas GeoDataFrame，需含幾何
    與村里代碼欄位）× 人口數字表（pandas DataFrame，需含村里代碼與人口
    欄位，來源即 SEGIS 人口村里級資料集）。

    - villages_gdf：至少要有幾何欄位 + 村里代碼欄位（例如 `VILLCODE`）
    - population_df：至少要有村里代碼欄位 + 人口欄位（例如 `population`）
    - code_col / pop_col：欄位名稱不確定時可省略，會依常見別名自動找，
      找不到就丟例外要求呼叫端明確指定（寧可報錯，不要用錯欄位悄悄算出
      錯的暴露人數）

    這支函式需要 geopandas + shapely（見 requirements.txt，開工時解開
    `geopandas>=0.14` 那行）。
    """
    try:
        import geopandas as gpd
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "population_exposure_from_villages 需要 geopandas，"
            "把 requirements.txt 裡 `# geopandas>=0.14` 這行解開後安裝。"
        ) from e

    code_col = code_col or _first_matching_column(villages_gdf.columns,
                                                    _CODE_COLUMN_CANDIDATES)
    if code_col is None:
        raise ValueError(
            "villages_gdf 裡找不到村里代碼欄位，請明確傳入 code_col=。"
            f"目前欄位有：{list(villages_gdf.columns)}"
        )
    pop_code_col = _first_matching_column(population_df.columns, _CODE_COLUMN_CANDIDATES)
    if pop_code_col is None:
        raise ValueError(
            "population_df 裡找不到村里代碼欄位，請確認 SEGIS 資料的代碼欄位名稱。"
            f"目前欄位有：{list(population_df.columns)}"
        )
    pop_col = pop_col or _first_matching_column(population_df.columns,
                                                  _POP_COLUMN_CANDIDATES)
    if pop_col is None:
        raise ValueError(
            "population_df 裡找不到人口欄位，請明確傳入 pop_col=。"
            f"目前欄位有：{list(population_df.columns)}"
        )

    # 座標系統對齊：界線圖標示 TWD97 經緯度，若跟系統其他部分慣用的
    # WGS84（EPSG:4326）不同，先轉換再疊合，避免疊合出錯位的結果。
    if villages_gdf.crs is not None and villages_gdf.crs.to_epsg() != 4326:
        villages_gdf = villages_gdf.to_crs("EPSG:4326")

    inundation_gdf = gpd.GeoDataFrame(
        {"geometry": [inundation_polygon]}, crs="EPSG:4326"
    )

    # 用代碼 join 人口數字（不是用中文名稱），避免同名不同地的誤植
    merged = villages_gdf.merge(
        population_df[[pop_code_col, pop_col]],
        left_on=code_col, right_on=pop_code_col, how="left",
    )
    merged[pop_col] = merged[pop_col].fillna(0)

    # 多邊形疊合（不是 .contains(point) 那種單點查詢）：
    # 用投影座標系算面積比較準（度為單位的面積沒有物理意義），
    # 這裡用等積投影 EPSG:3826（TWD97 TM2，跟專案其他座標轉換一致）
    merged_proj = merged.to_crs("EPSG:3826")
    inundation_proj = inundation_gdf.to_crs("EPSG:3826")

    overlay = gpd.overlay(merged_proj, inundation_proj, how="intersection")
    overlay_by_village = overlay.groupby(code_col).geometry.apply(
        lambda geoms: geoms.union_all().area if hasattr(geoms, "union_all")
        else geoms.unary_union.area
    )

    villages = []
    total_exposed = 0.0
    for _, row in merged_proj.iterrows():
        code = row[code_col]
        village_area = row.geometry.area
        overlap_area = float(overlay_by_village.get(code, 0.0))
        pop_total = float(row[pop_col])
        fraction = (overlap_area / village_area) if village_area > 0 else 0.0
        exposed = pop_total * fraction
        total_exposed += exposed
        villages.append(VillageExposure(
            village_code=str(code),
            village_name=str(row.get("VILLNAME", row.get("村里", ""))),
            county=str(row.get("COUNTYNAME", row.get("縣市", ""))),
            town=str(row.get("TOWNNAME", row.get("鄉鎮", ""))),
            population_total=int(pop_total),
            village_area_m2=float(village_area),
            overlap_area_m2=overlap_area,
            exposed_population=exposed,
        ))

    return ExposureSummary(
        villages=villages,
        total_exposed_population=total_exposed,
        inundation_area_m2=float(inundation_proj.geometry.area.sum()),
    )


# 備案：WorldPop 100m 網格（不需要 join，卡關時退回這個）

def population_exposure_from_grid(inundation_mask, population_grid) -> float:
    """
    WorldPop 網格版：inundation_mask 跟 population_grid 是**同解析度、
    同網格對齊**的兩個 numpy 陣列（population_grid 每格是人口估計值），
    直接用遮罩加總。比 population_exposure_from_villages 簡單很多，
    代價是準確度不如官方村里資料（WorldPop 是全球推估模型）。

    >>> import numpy as np
    >>> mask = np.array([[True, False], [True, True]])
    >>> pop = np.array([[10.0, 99.0], [5.0, 2.0]])
    >>> population_exposure_from_grid(mask, pop)
    17.0
    """
    import numpy as np
    if inundation_mask.shape != population_grid.shape:
        raise ValueError("inundation_mask 跟 population_grid 形狀不一致，"
                          "請確認兩者解析度與地理範圍是否對齊")
    return float(np.where(inundation_mask, population_grid, 0.0).sum())


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"exposure: {total - fails}/{total} 通過")

    # 示範 1：WorldPop 網格版（不需要真實 shapefile，隨時可跑）
    import numpy as np
    mask = np.zeros((5, 5), dtype=bool)
    mask[1:4, 1:4] = True
    pop_grid = np.full((5, 5), 40.0)  # 假設每格 40 人
    exposed = population_exposure_from_grid(mask, pop_grid)
    print(f"\nWorldPop 網格版示範：淹沒 {mask.sum()} 格，暴露人口估計 {exposed:.0f} 人")

    # 示範 2：村里疊合版，用合成的兩個村里多邊形展示疊合邏輯
    # （真正使用時 villages_gdf 來自 data.gov.tw/dataset/7438 的 shapefile，
    #  population_df 來自 SEGIS 人口村里級資料集）
    try:
        import geopandas as gpd
        import pandas as pd
        from shapely.geometry import box

        villages_gdf = gpd.GeoDataFrame({
            "VILLCODE": ["A001", "A002"],
            "VILLNAME": ["明利村", "隔壁村"],
            "COUNTYNAME": ["花蓮縣", "花蓮縣"],
            "TOWNNAME": ["萬榮鄉", "萬榮鄉"],
            "geometry": [box(0, 0, 10, 10), box(10, 0, 20, 10)],
        }, crs="EPSG:3826").to_crs("EPSG:4326")

        population_df = pd.DataFrame({
            "VILLCODE": ["A001", "A002"],
            "population": [1200, 800],
        })

        inundation_polygon = gpd.GeoSeries(
            [box(5, 0, 15, 10)], crs="EPSG:3826"
        ).to_crs("EPSG:4326").iloc[0]

        summary = population_exposure_from_villages(
            inundation_polygon, villages_gdf, population_df,
        )
        print(f"\n村里疊合版示範：暴露人口估計 {summary.total_exposed_population:.0f} 人")
        for v in summary.top_n():
            print(f"  {v.county}{v.town}{v.village_name}："
                  f"覆蓋 {v.overlap_fraction:.0%}，暴露約 {v.exposed_population:.0f} 人")
    except ImportError:
        print("\n（geopandas 未安裝，略過村里疊合版示範；"
              "解開 requirements.txt 的 geopandas 行後可跑）")
