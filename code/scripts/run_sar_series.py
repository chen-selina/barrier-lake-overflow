#!/usr/bin/env python3
"""
一個地點的逐期 SAR 影像 → 每期跑 analyze_sar_change.py（下一期當複核）→ 寫事件研判情境。

配合 scripts/gee_export_series_s1.js 的匯出檔名：
    data/raw/sentinel1/S1_VV_<name>_pre.tif
    data/raw/sentinel1/NASADEM_<name>.tif
    data/raw/sentinel1/S1_VV_<name>_YYYYMMDD.tif   （逐期，UTC 日期）

在 code/ 底下執行（預設是 2026 低災年負案例，參數與馬太鞍溪正案例相同）：

    python scripts/run_sar_series.py --name neg2026_matai_an --lon 121.29752 --lat 23.70061 \\
        --scenario-name "馬太鞍溪 · 2026 汛期（負案例）" --kind negative
    python -m pipeline.events.build

產出：data/derived/final_<name>_<YYYYMMDD>.json、data/raw/scenarios/<name>.json。
參數（坡度門檻 35°、D8 填窪）跟 run_sar_all.bat 一致，負案例不另外調。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
REPO = CODE.parent
RAW = REPO / "data" / "raw" / "sentinel1"
DERIVED = REPO / "data" / "derived"
SCENARIOS = REPO / "data" / "raw" / "scenarios"

MAX_WATER_SLOPE_DEG = "35"   # 與 run_sar_all.bat 相同，不為負案例調整


def scene_files(name: str, raw: Path) -> list:
    """[(YYYYMMDD, path)]，依日期排序。"""
    pat = re.compile(rf"S1_VV_{re.escape(name)}_(\d{{8}})\.tif$")
    out = [(m.group(1), p) for p in raw.glob(f"S1_VV_{name}_*.tif") if (m := pat.search(p.name))]
    return sorted(out)


def pass_time(day: str, hhmm: str) -> datetime:
    return datetime.strptime(f"{day} {hhmm}", "%Y%m%d %H:%M").replace(tzinfo=timezone.utc)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--orbit", default="DESCENDING", choices=["ASCENDING", "DESCENDING"])
    ap.add_argument("--pass-time", default="21:52", help="過境時間 HH:MM（UTC），見 GEE Console")
    ap.add_argument("--pre-label", default="事件前中位數")
    ap.add_argument("--scenario-name", required=True)
    ap.add_argument("--kind", default="negative", choices=["positive", "negative"])
    ap.add_argument("--description", default="")
    ap.add_argument("--raw-dir", type=Path, default=RAW)
    args = ap.parse_args()

    pre = args.raw_dir / f"S1_VV_{args.name}_pre.tif"
    dem = args.raw_dir / f"NASADEM_{args.name}.tif"
    scenes = scene_files(args.name, args.raw_dir)
    missing = [p for p in (pre, dem) if not p.exists()]
    if missing or not scenes:
        sys.exit(f"缺少影像：{', '.join(map(str, missing)) or '沒有任何逐期影像'}（見 gee_export_series_s1.js）")

    DERIVED.mkdir(parents=True, exist_ok=True)
    passes = []
    for i, (day, path) in enumerate(scenes):
        later = scenes[i + 1] if i + 1 < len(scenes) else None
        t = pass_time(day, args.pass_time)
        out = DERIVED / f"final_{args.name}_{day}.json"
        cmd = [sys.executable, str(CODE / "scripts" / "analyze_sar_change.py"),
               "--pre", str(pre), "--post", str(path), "--dem", str(dem),
               "--orbit", args.orbit, "--lon", str(args.lon), "--lat", str(args.lat),
               "--lake-id", args.name, "--pre-label", args.pre_label,
               "--post-label", f"post {t:%Y-%m-%d %H:%M} UTC",
               "--max-water-slope-deg", MAX_WATER_SLOPE_DEG, "--out", str(out)]
        if later:
            cmd += ["--post-later", str(later[1])]
        print(f"[{i + 1}/{len(scenes)}] {day}" + (f" + 複核 {later[0]}" if later else "（無複核期）"))
        log = out.with_suffix(".log")
        with open(log, "w", encoding="utf-8") as f:
            r = subprocess.run(cmd, cwd=CODE, stdout=f, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            print(f"  失敗，見 {log}")
            continue
        passes.append({
            "file": out.name,
            "time": t.isoformat(),
            "recheckTime": pass_time(later[0], args.pass_time).isoformat() if later else None,
            "evidenceImage": None,
        })

    scenario = {
        "id": args.name,
        "name": args.scenario_name,
        "kind": args.kind,
        "description": args.description or f"{len(passes)} 期 Sentinel-1（{args.orbit}），參數與正案例相同。",
        "center": [args.lon, args.lat],
        "windowKm": 4.0,
        "revisitDays": 6 if args.orbit == "DESCENDING" else 12,
        "context": [],
        "observationsLakeId": None,
        "referenceLakeId": None,
        "passes": passes,
    }
    SCENARIOS.mkdir(parents=True, exist_ok=True)
    path = SCENARIOS / f"{args.name}.json"
    path.write_text(json.dumps(scenario, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已寫出 {path}，接著跑 python -m pipeline.events.build")


if __name__ == "__main__":
    main()
