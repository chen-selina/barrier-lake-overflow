#!/usr/bin/env python3
"""
把逐期 SAR 偵測結果（data/derived/final_*.json）整理成事件，再依時間逐期回放研判結果。

    python -m pipeline.events.build        # → dashboard/data/events.js

情境設定在 data/raw/scenarios/*.json，一個檔案一個情境（地點＋影像期別）。
偵測結果檔不存在的期別會略過；整個情境都沒有結果就整個略過，不會失敗。

跨期追蹤：新一期候選的中心點跟既有事件最新位置相距 TRACK_RADIUS_M 以內，
視為同一事件；否則開新事件。事件代號依首次出現順序編 E1、E2…。

回放時點：每一期影像（含只拿來複核的影像）各是一個時點。某時點只用到
當時已經拿到的影像，不會用到未來的複核結果。
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from pipeline.attribution.annotate import read_lakes
from pipeline.ingest.observations import load_observations_table

from . import triage as T

CODE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CODE_ROOT.parent
SCENARIOS = REPO_ROOT / "data" / "raw" / "scenarios"
DERIVED = REPO_ROOT / "data" / "derived"
LAKES_JS = CODE_ROOT / "dashboard" / "data" / "lakes.js"
OUT = CODE_ROOT / "dashboard" / "data" / "events.js"

TRACK_RADIUS_M = 250.0


def distance_m(a: tuple, b: tuple) -> float:
    """經緯度近似距離（等距圓柱投影，幾公里內誤差可忽略）。

    >>> round(distance_m((121.0, 23.7), (121.0, 23.701)))
    111
    """
    lat = math.radians((a[1] + b[1]) / 2)
    dx = (a[0] - b[0]) * 111_320 * math.cos(lat)
    dy = (a[1] - b[1]) * 110_540
    return math.hypot(dx, dy)


def _t(s: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(s) if s else None


def load_passes(scenario: dict, derived: Path) -> list:
    """回傳 [(pass 設定, final json)]，結果檔不存在的期別略過。"""
    out = []
    for p in scenario["passes"]:
        path = derived / p["file"]
        if not path.exists():
            print(f"  略過 {p['file']}：找不到結果檔")
            continue
        out.append((p, json.loads(path.read_text(encoding="utf-8"))))
    return out


def track(passes: list) -> list:
    """把各期候選串成事件。回傳 [{"id": "E1", "detections": [Detection…]}]。"""
    events: list = []
    for p, result in sorted(passes, key=lambda x: _t(x[0]["time"])):
        for cand in result.get("candidates", []):
            det = T.Detection(
                pass_time=_t(p["time"]),
                recheck_time=_t(p.get("recheckTime")),
                cand=cand,
                evidence_image=p.get("evidenceImage"),
            )
            match = None
            for ev in events:
                if distance_m(ev["detections"][-1].lon_lat, det.lon_lat) <= TRACK_RADIUS_M:
                    match = ev
                    break
            if match:
                match["detections"].append(det)
            else:
                events.append({"id": f"E{len(events) + 1}", "detections": [det]})
    return events


def snapshot_times(scenario: dict, passes: list) -> list:
    """每一期影像（偵測期＋複核期）各一個時點，依時間排序。"""
    times = set()
    for p, _ in passes:
        times.add(_t(p["time"]))
        if p.get("recheckTime"):
            times.add(_t(p["recheckTime"]))
    return sorted(times)


def nearby_history(lakes: list, lon_lat: tuple, before: datetime,
                   exclude_id: Optional[str]) -> list:
    """清冊中、在 before 之前形成、距離 HISTORY_RADIUS_KM 內的堰塞湖。"""
    out = []
    for lake in lakes:
        if lake.get("id") == exclude_id or lake.get("lon") is None:
            continue
        year = lake.get("year")
        if not year or year > before.year:
            continue
        d = distance_m(lon_lat, (lake["lon"], lake["lat"])) / 1000
        if d <= T.HISTORY_RADIUS_KM:
            out.append({"name": lake["name"], "year": year, "distanceKm": round(d, 1)})
    return sorted(out, key=lambda h: h["year"])


def matching_external(scenario: dict, lon_lat: tuple, as_of: datetime) -> list:
    """情境檔 externalEvidence 中，as_of 以前已發布、且位置在 radiusM 內的他單位成果。"""
    out = []
    for x in scenario.get("externalEvidence", []):
        t = _t(x["time"])
        if t > as_of or distance_m(lon_lat, tuple(x["lonLat"])) > x.get("radiusM", 600):
            continue
        out.append({**x, "time": t})
    return sorted(out, key=lambda x: x["time"])


def _snapshot_label(t: datetime, analyzed: set, rechecks: dict, trigger: Optional[datetime]) -> dict:
    parts = []
    if t in analyzed:
        parts.append("新一期 SAR 全幅偵測")
    if t in rechecks:
        parts.append(f"複核 {'、'.join(rechecks[t])} 的候選")
    since = ""
    if trigger:
        h = (t - trigger).total_seconds() / 3600
        since = f"距觸發約 {h:.0f} 小時" if h < 72 else f"距觸發約 {h / 24:.0f} 天"
    return {"what": "＋".join(parts), "since": since}


def build_scenario(scenario: dict, derived: Path = DERIVED,
                   lakes: Optional[list] = None, observations: Optional[dict] = None) -> Optional[dict]:
    passes = load_passes(scenario, derived)
    if not passes:
        return None
    lakes = lakes or []
    observations = observations or {}

    events = track(passes)
    analyzed = {_t(p["time"]) for p, _ in passes}
    rechecks: dict = {}
    for p, _ in passes:
        if p.get("recheckTime"):
            rechecks.setdefault(_t(p["recheckTime"]), []).append(T.tw_date(_t(p["time"])))
    trigger = _t(scenario.get("trigger", {}).get("time"))

    obs = observations.get(scenario.get("observationsLakeId"))
    rain_available = bool(obs and obs.rain_24h_mm is not None)

    ref = next((l for l in lakes if l.get("id") == scenario.get("referenceLakeId")), None)
    reference = ({"lakeId": ref["id"], "name": ref["name"], "lonLat": [ref["lon"], ref["lat"]],
                  "label": scenario.get("referenceLabel", "")} if ref else None)

    revisit = timedelta(days=scenario.get("revisitDays", 6))
    snapshots = []
    for t in snapshot_times(scenario, passes):
        latest_analyzed = max((a for a in analyzed if a <= t), default=None)
        ctx_base = dict(
            as_of=t,
            latest_analyzed_pass=latest_analyzed,
            next_pass=t + revisit,
            rain_available=rain_available,
            trigger_label=scenario.get("trigger", {}).get("label", ""),
            context_lines=scenario.get("context", []),
        )
        cards = []
        for ev in events:
            dets = [d for d in ev["detections"] if d.pass_time <= t]
            if not dets:
                continue
            latest = dets[-1]
            ctx = T.Context(
                **ctx_base,
                history=nearby_history(lakes, latest.lon_lat, t, scenario.get("referenceLakeId")),
                external=matching_external(scenario, latest.lon_lat, t),
                exposure=scenario.get("exposure"),
            )
            a = T.assess(ev["id"], dets, ctx)
            card = {
                "id": ev["id"],
                "firstSeen": T.tw_label(dets[0].pass_time),
                "lastSeen": T.tw_label(latest.pass_time),
                "isNew": latest.pass_time == t and len(dets) == 1,
                "lonLat": list(latest.lon_lat),
                "distanceFromReferenceM": (round(distance_m(latest.lon_lat, tuple(reference["lonLat"])))
                                           if reference else None),
                "areaHectare": round(latest.area_ha, 2),
                "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
                "lakeFloorM": latest.cand.get("lakeFloorM"),
                "polygonLonLat": latest.cand.get("polygonLonLat") or [],
                "detections": [{
                    "passTime": T.tw_label(d.pass_time),
                    "areaHectare": round(d.area_ha, 2),
                    "recheck": d.recheck_state(t),
                    "recheckTime": T.tw_label(d.recheck_time) if d.recheck_time else None,
                    "iou": d.iou if d.recheck_state(t) != "pending" else None,
                    "evidenceImage": d.evidence_image,
                    "reasons": [r for r in d.cand.get("reasons", [])
                                if d.recheck_state(t) != "pending" or "IoU" not in r],
                } for d in dets],
                **a.to_dict(),
            }
            cards.append(card)
        cards.sort(key=lambda c: (T.PRIORITY_RANK[c["priority"]], -c["areaHectare"]))

        counts = {k: sum(1 for c in cards if c["priority"] == k) for k in T.PRIORITY_RANK}
        label = _snapshot_label(t, analyzed, rechecks, trigger)
        snapshots.append({
            "asOf": t.isoformat(),
            "label": T.tw_label(t),
            "what": label["what"],
            "since": label["since"],
            "nextPass": T.tw_date(t + revisit),
            "counts": counts,
            "newCount": sum(1 for c in cards if c["isNew"]),
            "events": cards,
        })

    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "kind": scenario.get("kind", "positive"),
        "description": scenario.get("description", ""),
        "center": scenario["center"],
        "windowKm": scenario.get("windowKm", 4.0),
        "reference": reference,
        "trigger": scenario.get("trigger"),
        "snapshots": snapshots,
    }


def write_js(scenarios: list, path: Path = OUT) -> None:
    body = json.dumps(scenarios, ensure_ascii=False, indent=1)
    path.write_text(
        "/* 由 pipeline/events/build.py 產生，請勿手動編輯。\n"
        "   每個情境逐期回放：某時點只用當時已取得的影像，不含未來的複核結果。 */\n"
        f"window.EVENT_SCENARIOS = {body};\n",
        encoding="utf-8",
    )


def main(scenario_dir: Path = SCENARIOS, derived: Path = DERIVED, out: Path = OUT) -> list:
    lakes = read_lakes(LAKES_JS) if LAKES_JS.exists() else []
    observations = load_observations_table()
    built = []
    for path in sorted(scenario_dir.glob("*.json")):
        scenario = json.loads(path.read_text(encoding="utf-8"))
        print(f"情境 {scenario['id']}（{scenario['name']}）")
        result = build_scenario(scenario, derived, lakes, observations)
        if result is None:
            print("  沒有任何偵測結果，略過")
            continue
        for s in result["snapshots"]:
            c = s["counts"]
            print(f"  {s['label']}  高 {c['high']}／中 {c['medium']}／低 {c['low']}  {s['what']}")
        built.append(result)
    write_js(built, out)
    print(f"已寫出 {out}（{len(built)} 個情境）")
    return built


if __name__ == "__main__":
    main()
