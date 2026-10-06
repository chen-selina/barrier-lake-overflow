#!/usr/bin/env python3
"""
重建儀表板資料：清冊 → lakes.js、風險 → risk.js、成因敘述寫回 lakes.js、SAR 結果 → events.js。

    python -m pipeline.build_all          # 風險用訓練平均值佔位，不連網
    python -m pipeline.build_all --live   # 風險抓 CWA 即時雨量（需 CWA_API_KEY）

各步驟也可以單獨跑，見 README。
"""

from __future__ import annotations

import argparse

from pipeline.ingest import inventory, risk
from pipeline.attribution import annotate
from pipeline.events import build as events

RAW = "../data/raw"
DASHBOARD_DATA = "dashboard/data"


def main(live: bool = False) -> None:
    print("== [1/4] 轉換清冊 CSV → lakes.js ==")
    inventory.main(f"{RAW}/taiwan-barrier-lakes.csv", f"{DASHBOARD_DATA}/lakes.js")

    print("\n== [2/4] 風險模型（package）→ risk.js ==")
    risk.main(
        f"{DASHBOARD_DATA}/lakes.js",
        f"{DASHBOARD_DATA}/risk.js",
        offline=not live,
    )

    print("\n== [3/4] 產生成因敘述，加註回 lakes.js ==")
    annotate.main()

    print("\n== [4/4] SAR 偵測結果 → 事件佇列 events.js ==")
    events.main()

    print("\n完成。dashboard/data/ 已是最新資料。")


def cli() -> None:
    ap = argparse.ArgumentParser(description="一鍵重建前端所需的所有資料")
    ap.add_argument("--live", action="store_true",
                     help="風險模型改抓 CWA 即時雨量（需 CWA_API_KEY，見 pipeline.ingest.risk）")
    args = ap.parse_args()
    main(live=args.live)


if __name__ == "__main__":
    cli()
