#!/usr/bin/env python3
"""
讀 data/raw/observations.csv（人工查證的歷史觀測），轉成 rules.Observations。

CWA 開放資料平台的即時端點查不到歷史區間，地震目錄只有當年度，所以這部分
先用人工整理。之後找到可靠的歷史 API，只要換掉 annotate.load_observations()
的資料來源。

欄位：lake_id, rain_24h_mm, rain_window_hours, rain_max_hourly_mm,
rain_percentile, typhoon_name, typhoon_distance_km, southwest_flow,
quake_name, quake_time, quake_magnitude, pga_gal, formed_time,
frontal_system, source

除 lake_id 外都可以空白。布林填 true/false，時間用 ISO 8601。
有填任何觀測值就要填 source（只供人工核對，程式不讀）。

    python -m pipeline.ingest.observations   # 印出填了幾筆
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..attribution.rules import Observations

# code/pipeline/ingest/observations.py → 專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OBSERVATIONS_CSV = PROJECT_ROOT / "data" / "raw" / "observations.csv"

_CSV_FIELDS = [
    "lake_id", "rain_24h_mm", "rain_window_hours", "rain_max_hourly_mm",
    "rain_percentile", "typhoon_name", "typhoon_distance_km", "southwest_flow",
    "quake_name", "quake_time", "quake_magnitude", "pga_gal", "formed_time",
    "frontal_system", "source",
]


def _opt_float(s: Optional[str]) -> Optional[float]:
    s = (s or "").strip()
    return float(s) if s else None


def _opt_bool(s: Optional[str]) -> Optional[bool]:
    s = (s or "").strip().lower()
    if not s:
        return None
    return s in ("1", "true", "yes", "y")


def _opt_datetime(s: Optional[str]) -> Optional[datetime]:
    s = (s or "").strip()
    return datetime.fromisoformat(s) if s else None


def _row_to_observations(row: dict) -> Observations:
    return Observations(
        rain_24h_mm=_opt_float(row.get("rain_24h_mm")),
        rain_window_hours=int(row["rain_window_hours"]) if (row.get("rain_window_hours") or "").strip() else 24,
        rain_max_hourly_mm=_opt_float(row.get("rain_max_hourly_mm")),
        rain_percentile=_opt_float(row.get("rain_percentile")),
        typhoon_name=(row.get("typhoon_name") or "").strip() or None,
        typhoon_distance_km=_opt_float(row.get("typhoon_distance_km")),
        southwest_flow=_opt_bool(row.get("southwest_flow")),
        quake_name=(row.get("quake_name") or "").strip() or None,
        quake_time=_opt_datetime(row.get("quake_time")),
        quake_magnitude=_opt_float(row.get("quake_magnitude")),
        pga_gal=_opt_float(row.get("pga_gal")),
        formed_time=_opt_datetime(row.get("formed_time")),
        frontal_system=_opt_bool(row.get("frontal_system")),
    )


def load_observations_table(path: Path = DEFAULT_OBSERVATIONS_CSV) -> dict:
    """
    讀 observations.csv，回傳 {lake_id: Observations}。

    找不到檔案、或某一列全部觀測欄位都是空的，該筆就不會出現在回傳的
    字典裡——呼叫端用 `.get(lake_id)` 查詢，查不到自然回傳 None，
    跟「尚未有人填這筆」的語意一致，不需要另外判斷。
    """
    path = Path(path)
    if not path.exists():
        return {}

    table = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            lake_id = (row.get("lake_id") or "").strip()
            if not lake_id:
                continue
            obs = _row_to_observations(row)
            if obs.has_any():
                table[lake_id] = obs
    return table


def cli() -> None:
    table = load_observations_table()
    if not DEFAULT_OBSERVATIONS_CSV.exists():
        print(f"✗ 找不到 {DEFAULT_OBSERVATIONS_CSV}（尚未建立，視同全部沒有觀測資料）")
        return
    print(f"✓ {DEFAULT_OBSERVATIONS_CSV} 目前有 {len(table)} 筆湖已填入至少一項觀測值")
    for lake_id in table:
        print(f"  - {lake_id}")


if __name__ == "__main__":
    cli()
