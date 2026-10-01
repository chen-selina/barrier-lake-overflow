#!/usr/bin/env python3
"""
跑全清冊的成因敘述，寫回 dashboard/data/lakes.js（narrative、rulesFired）。

觀測資料來自 data/raw/observations.csv，沒填的湖只輸出不需要觀測的句子。

    python -m pipeline.attribution.annotate
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .compose import Composer
from .rules import LakeRecord, Observations, attribute
from ..ingest.observations import load_observations_table

# code/pipeline/attribution/annotate.py → code/
CODE_ROOT = Path(__file__).resolve().parents[2]
DATA = CODE_ROOT / "dashboard" / "data" / "lakes.js"


def read_lakes(path) -> list:
    """從 lakes.js 取出 JSON 陣列。"""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    start, end = src.index("["), src.rindex("]") + 1
    return json.loads(src[start:end])


def write_lakes(path, rows: list) -> None:
    header = (
        "/* 由 pipeline/ingest/inventory.py 產生，並由 pipeline/attribution/annotate.py 加註敘述。\n"
        "   請勿手動編輯。\n"
        "   資料來源：農業部農村發展及水土保持署 堰塞湖清冊\n"
        "   https://tech.ardswc.gov.tw/Results/BarrierLakeInfo\n"
        "   座標已由 TWD97 TM2 轉為 WGS84。 */\n\n"
    )
    body = json.dumps(rows, ensure_ascii=False, indent=1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + f"window.BARRIER_LAKES = {body};\n")


def to_record(row: dict) -> LakeRecord:
    return LakeRecord(
        seq=row.get("seq", 0),
        name=row.get("name", ""),
        year=row.get("year"),
        county=row.get("county", ""),
        town=row.get("town", ""),
        village=row.get("village", ""),
        landmark=row.get("landmark", ""),
        cause=row.get("cause", ""),
        event=row.get("event", ""),
        formed=row.get("formed", ""),
        duration=row.get("duration", ""),
        volume=row.get("volume"),
        breach_date=row.get("breachDate", ""),
        breach_cause=row.get("breachCause", ""),
        status=row.get("status", ""),
        setting=row.get("setting", ""),
        lon=row.get("lon"),
        lat=row.get("lat"),
    )


_OBS_TABLE: Optional[dict] = None


def load_observations(row: dict) -> Optional[Observations]:
    """
    取得該筆紀錄形成期間的氣象／地震觀測。

    改用人工彙整（見 `pipeline.ingest.observations` 模組開頭說明，為什麼
    不直接呼叫 CWA 即時 API）：從 `data/raw/observations.csv` 依湖 id
    查表，查不到就回傳 None（目前該表大多是空的，行為等同以前的
    「尚未介接」狀態）。有人補進真實觀測值後，敘述會自動變詳細，
    不需要動 rules.py 或 templates.yaml。
    """
    global _OBS_TABLE
    if _OBS_TABLE is None:
        _OBS_TABLE = load_observations_table()
    return _OBS_TABLE.get(row.get("id"))


def main() -> None:
    if not DATA.exists():
        raise SystemExit(
            f"找不到 {DATA}\n"
            "請先執行：python -m pipeline.ingest.inventory "
            "../data/raw/taiwan-barrier-lakes.csv dashboard/data/lakes.js")

    rows = read_lakes(DATA)
    composer = Composer()

    annotated = 0
    unresolved_total = []

    for row in rows:
        rec = to_record(row)
        obs = load_observations(row)
        result = composer.render(attribute(rec, obs))

        row["narrative"] = result.text
        row["rulesFired"] = result.rules_fired
        if result.text:
            annotated += 1
        if result.unresolved:
            unresolved_total.append((rec.seq, rec.name, result.unresolved))

    write_lakes(DATA, rows)

    print(f"已加註 {annotated}/{len(rows)} 筆敘述 → {DATA}")
    if unresolved_total:
        print(f"\n有 {len(unresolved_total)} 筆出現略過的句子：")
        for seq, name, items in unresolved_total[:10]:
            print(f"  #{seq} {name}: {', '.join(items)}")
        if len(unresolved_total) > 10:
            print(f"  ...另有 {len(unresolved_total) - 10} 筆")
    else:
        print("所有句子皆完整填槽，無略過。")

    # 抽樣顯示，方便肉眼檢查
    print("\n抽樣（2025 年）：")
    for row in rows:
        if row.get("year") == 2025 and row.get("narrative"):
            print(f"\n  #{row['seq']} {row['name']}")
            print(f"  {row['narrative']}")


if __name__ == "__main__":
    main()
