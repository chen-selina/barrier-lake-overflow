#!/usr/bin/env python3
"""
observations.py — 讀取人工彙整的歷史觀測資料（B6）

`attribution.annotate.load_observations()` 原本寫死回傳 None，理由是
「CWA 歷史資料 API 尚未介接」。查證後發現這個「介接」比預期複雜：
CWA 開放資料平台（`opendata.cwa.gov.tw`）目前用到的即時雨量端點
（見 `pipeline.ingest.cwa`）本質上是「最新觀測」feed，不是任意日期
區間查詢；地震目錄（E-A0073-001）文件明講「只記錄當年度」，查不到
去年的事件；雨量/颱風的真正歷史資料要走另一個服務（CODiS 等），
不是這個專案現有在用的 REST API 型態，也還沒有驗證過的查詢方式。

與其硬寫一個「看起來對、但可能接錯 endpoint」的自動化查詢（這正是
架構文件警告 SAR 前處理那段「似是而非的半成品」問題），這裡改用
**人工彙整**：`data/raw/observations.csv` 是一張「每個湖 id 一列」的
表格，欄位對應 `rules.Observations` 的每個欄位，由團隊在
查證過歷史氣象/地震資料後手動填入（來源可以是 CWA 官網的歷史查詢
頁面、颱風資料庫、新聞報導等）。程式只負責讀表、轉型別、餵給
`attribute()`——資料本身尚未有人填寫時，行為跟現在完全一樣（各湖
仍然拿到 None，退回不含觀測值的簡化敘述），不會憑空生出假資料。

之後如果真的驗證出可用的即時查詢 API，可以直接在
`annotate.load_observations()` 換掉這個模組的呼叫，`rules.py` /
`templates.yaml` 完全不用動——這是這個模組原本設計就有的介接優點。

CSV 欄位：
    lake_id, rain_24h_mm, rain_window_hours, rain_max_hourly_mm,
    rain_percentile, typhoon_name, typhoon_distance_km, southwest_flow,
    quake_name, quake_time, quake_magnitude, pga_gal, formed_time,
    frontal_system
（除 lake_id 外全部選填，跟 `Observations` 的「全部選填、沒有就不輸出
對應句子」原則一致；布林欄位填 true/false/1/0，時間欄位用 ISO 8601，
例如 2025-07-21T08:00:00+08:00）

執行方式：python -m pipeline.ingest.observations（僅供除錯，印出目前
表格裡已經有觀測值的湖數量）
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
    "frontal_system",
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
