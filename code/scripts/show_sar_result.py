#!/usr/bin/env python3
"""
把 analyze_sar_change.py 的結果 JSON 印成給人看的摘要（Demo 用）。

    cd code
    python scripts/show_sar_result.py                       # 預設讀 ../data/derived/final_*.json
    python scripts/show_sar_result.py ../data/derived/final_0728.json
"""

from __future__ import annotations

import glob
import json
import os
import sys

GRADE_TEXT = {"A": "A 級｜立即通報", "B": "B 級｜排下一期影像複核", "C": "C 級｜列入觀察"}


def show(path: str) -> None:
    with open(path, encoding="utf-8") as fh:
        r = json.load(fh)
    print("=" * 64)
    print(f"{r.get('lakeId', '?')}　事件後影像：{r['post']['date']}")
    print(f"事件前基準：{r['pre']['date']}　軌道：{r.get('orbit')}　分析範圍：{r.get('analysisWindowKm')} km 見方")
    print(f"新增水體合計 {r.get('newWaterTotalAreaHectare')} 公頃　複核影像 {r.get('laterScenes', 0)} 期")
    cands = r.get("candidates", [])
    if not cands:
        print("\n→ 無疑似堰塞湖候選")
        return
    print(f"\n→ 疑似堰塞湖候選 {len(cands)} 個：")
    for c in cands:
        lon, lat = c["centroidLonLat"]
        label = GRADE_TEXT.get(c["grade"], c["grade"])
        if c.get("laterScenesChecked", 0) > 0 and not c.get("persistent"):
            label = f"{c['grade']} 級｜已複核、未持續（研判為誤報）"
        print(f"\n  [{c['id']}] {label}")
        print(f"      位置：{lat:.5f}°N {lon:.5f}°E（距壩址座標 {c.get('distanceFromDamM')} m）")
        print(f"      湖面面積：{c['areaHectare']} 公頃（受遮罩影響，為下限）")
        for reason in c.get("reasons", []):
            print(f"      ・{reason}")


def main() -> None:
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join("..", "data", "derived", "final_*.json")))
    if not paths:
        print("找不到結果檔：請先執行 scripts\\run_sar_all.bat")
        sys.exit(1)
    for p in paths:
        show(p)
    print("=" * 64)


if __name__ == "__main__":
    main()
