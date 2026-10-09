#!/usr/bin/env python3
"""事件研判測試。合成情境測規則本身，馬太鞍溪真實結果測整條回放。"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipeline.events import build as B
from pipeline.events import triage as T

UTC = timezone.utc
T0 = datetime(2025, 7, 22, 21, 52, tzinfo=UTC)
DAY6 = timedelta(days=6)


def cand(lon=121.30, lat=23.70, area=3.0, landslide=True, persistent=False, checked=1, iou=0.1):
    return {
        "id": "cand1", "grade": "B", "areaHectare": area,
        "centroidLonLat": [lon, lat], "onRiver": True, "landslideNearby": landslide,
        "damDownstream": landslide, "persistent": persistent, "laterScenesChecked": checked,
        "landslideAreaHectare": 100.0, "lakeFloorM": 900.0,
        "reasons": [f"後續 1 期影像同位置水體 IoU 最高 {iou:.2f}，"
                    + ("持續蓄水" if persistent else "未確認持續")],
        "polygonLonLat": [],
    }


def det(t, c, recheck=True):
    return T.Detection(pass_time=t, recheck_time=t + DAY6 if recheck else None, cand=c)


def ctx(as_of, latest_pass=None, rain=False):
    return T.Context(as_of=as_of, latest_analyzed_pass=latest_pass or as_of,
                     next_pass=as_of + DAY6, rain_available=rain)


class TestTriageRules(unittest.TestCase):

    def test_single_pass_is_medium_and_does_not_dispatch_uav(self):
        a = T.assess("E1", [det(T0, cand())], ctx(T0))
        self.assertEqual((a.priority, a.persistence, a.grade, a.confidence),
                         ("medium", "pending", "B", "低"))
        labels = [t["label"] for t in a.tasks]
        self.assertIn("暫不派遣 UAV", labels)
        self.assertTrue(any("複核" in l for l in labels))

    def test_future_recheck_is_not_used(self):
        # 複核結果在 json 裡已經有，但時點還沒到複核影像，不能用
        d = det(T0, cand(persistent=True))
        self.assertEqual(d.recheck_state(T0), "pending")
        self.assertEqual(d.recheck_state(T0 + DAY6), "persistent")
        self.assertEqual(T.assess("E1", [d], ctx(T0)).priority, "medium")

    def test_confirmed_with_landslide_is_high(self):
        d = det(T0, cand(persistent=True, iou=0.52))
        a = T.assess("E1", [d], ctx(T0 + DAY6, latest_pass=T0))
        self.assertEqual((a.priority, a.grade, a.action), ("high", "A", "建議立即查證"))
        self.assertIn("priority.high.confirmed", a.rules_fired)
        self.assertTrue(any("UAV" in t["label"] for t in a.tasks))

    def test_sar_only_confidence_caps_at_medium(self):
        d1 = det(T0, cand(persistent=True))
        d2 = det(T0 + DAY6, cand(persistent=True))
        a = T.assess("E1", [d1, d2], ctx(T0 + 2 * DAY6, latest_pass=T0 + DAY6))
        self.assertEqual(a.confidence, "中")

    def test_failed_recheck_is_low_and_flags_conflict(self):
        d = det(T0, cand(persistent=False, iou=0.01))
        a = T.assess("E1", [d], ctx(T0 + DAY6))
        self.assertEqual((a.priority, a.persistence, a.action), ("low", "failed", "暫時觀察"))
        self.assertTrue(a.conflicts)
        self.assertIn("IoU 0.01", a.summary)

    def test_no_landslide_pending_is_low(self):
        a = T.assess("E1", [det(T0, cand(landslide=False))], ctx(T0))
        self.assertEqual((a.priority, a.grade), ("low", "C"))

    def test_confirmed_then_missing_is_high_lost(self):
        d1 = det(T0, cand(persistent=True))
        later_pass = T0 + 2 * DAY6
        a = T.assess("E1", [d1], ctx(later_pass, latest_pass=later_pass))
        self.assertEqual((a.persistence, a.priority), ("lost", "high"))

    def test_failed_then_reappears_goes_back_to_pending(self):
        d1 = det(T0, cand(persistent=False))
        d2 = det(T0 + 2 * DAY6, cand(), recheck=False)
        a = T.assess("E1", [d1, d2], ctx(T0 + 2 * DAY6))
        self.assertEqual((a.persistence, a.priority), ("pending", "medium"))

    def test_growing_area(self):
        d1 = det(T0, cand(area=5.8, persistent=True))
        d2 = det(T0 + DAY6, cand(area=26.3), recheck=False)
        a = T.assess("E1", [d1, d2], ctx(T0 + DAY6))
        self.assertIn("trend.growing", a.rules_fired)
        self.assertEqual(a.scale, "大")

    def test_rain_gap_only_when_missing(self):
        d = det(T0, cand())
        self.assertIn("gap.rain", T.assess("E1", [d], ctx(T0)).rules_fired)
        self.assertNotIn("gap.rain", T.assess("E1", [d], ctx(T0, rain=True)).rules_fired)

    def test_external_optical_corroborates_single_pass(self):
        c = ctx(T0)
        c.external = [{"time": T0, "kind": "optical", "text": "光學影像可見湖面", "source": "某單位"}]
        a = T.assess("E1", [det(T0, cand())], c)
        self.assertEqual((a.priority, a.confidence), ("high", "高"))
        self.assertNotIn("gap.optical", a.rules_fired)
        self.assertNotIn("暫不派遣 UAV", [t["label"] for t in a.tasks])

    def test_official_estimate_alone_is_not_independent(self):
        c = ctx(T0)
        c.external = [{"time": T0, "kind": "official", "text": "官方估蓄水量", "source": "某單位"}]
        a = T.assess("E1", [det(T0, cand())], c)
        self.assertEqual((a.priority, a.confidence), ("medium", "低"))

    def test_external_does_not_rescue_failed_recheck(self):
        c = ctx(T0 + DAY6)
        c.external = [{"time": T0, "kind": "optical", "text": "x", "source": "y"}]
        a = T.assess("E1", [det(T0, cand(persistent=False))], c)
        self.assertEqual(a.priority, "low")

    def test_exposure_replaces_gap(self):
        c = ctx(T0)
        c.exposure = {"text": "下游有聚落", "source": "s"}
        a = T.assess("E1", [det(T0, cand())], c)
        self.assertNotIn("gap.exposure", a.rules_fired)
        self.assertIn("exposure.known", a.rules_fired)

    def test_empty_detections(self):
        with self.assertRaises(ValueError):
            T.assess("E1", [], ctx(T0))


class TestTracking(unittest.TestCase):

    def _pass(self, t, cands, recheck=True):
        p = {"file": "x", "time": t.isoformat(),
             "recheckTime": (t + DAY6).isoformat() if recheck else None}
        return p, {"candidates": cands}

    def test_nearby_candidates_merge(self):
        passes = [self._pass(T0, [cand(121.2935, 23.6982)]),
                  self._pass(T0 + DAY6, [cand(121.2947, 23.6983)])]   # 約 120 m
        events = B.track(passes)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0]["detections"]), 2)

    def test_far_candidates_split(self):
        passes = [self._pass(T0, [cand(121.3075, 23.7092)]),
                  self._pass(T0 + DAY6, [cand(121.3104, 23.7079)])]   # 約 330 m
        self.assertEqual(len(B.track(passes)), 2)


class TestMatchingExternal(unittest.TestCase):

    SCEN = {"externalEvidence": [
        {"time": T0.isoformat(), "kind": "optical", "lonLat": [121.30, 23.70], "radiusM": 600, "text": "a"},
    ]}

    def test_time_and_radius(self):
        self.assertEqual(len(B.matching_external(self.SCEN, (121.30, 23.70), T0)), 1)
        self.assertEqual(B.matching_external(self.SCEN, (121.30, 23.70), T0 - DAY6), [])
        self.assertEqual(B.matching_external(self.SCEN, (121.31, 23.70), T0), [])   # 約 1 km


class TestNegativeScenario(unittest.TestCase):

    def test_no_candidates_builds_empty_snapshots(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "final_a.json").write_text(json.dumps({"candidates": []}), encoding="utf-8")
            scenario = {
                "id": "neg", "name": "負案例", "kind": "negative", "center": [121.3, 23.7],
                "referenceLakeId": None, "observationsLakeId": None,
                "passes": [{"file": "final_a.json", "time": T0.isoformat(),
                            "recheckTime": (T0 + DAY6).isoformat()},
                           {"file": "missing.json", "time": (T0 + DAY6).isoformat()}],
            }
            r = B.build_scenario(scenario, d)
            self.assertIsNone(r["reference"])
            self.assertEqual(len(r["snapshots"]), 2)
            self.assertTrue(all(s["events"] == [] for s in r["snapshots"]))

    def test_all_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            scenario = {"id": "x", "name": "x", "center": [0, 0],
                        "passes": [{"file": "nope.json", "time": T0.isoformat()}]}
            self.assertIsNone(B.build_scenario(scenario, Path(d)))


class TestMataiAnReplay(unittest.TestCase):
    """馬太鞍溪真實結果：湖在 7/29 出現、8/4 複核後升高優先；四個誤報複核後都降為低優先。"""

    @classmethod
    def setUpClass(cls):
        scenario = json.loads((B.SCENARIOS / "matai_an_2025.json").read_text(encoding="utf-8"))
        if not all((B.DERIVED / p["file"]).exists() for p in scenario["passes"]):
            raise unittest.SkipTest("data/derived/final_*.json 不在，先跑 scripts/run_sar_all.bat")
        cls.result = B.build_scenario(scenario, B.DERIVED, B.read_lakes(B.LAKES_JS),
                                      B.load_observations_table())
        cls.snaps = {s["label"]: s for s in cls.result["snapshots"]}

    def _by_priority(self, label):
        s = self.snaps[label]
        return {k: [e["id"] for e in s["events"] if e["priority"] == k] for k in T.PRIORITY_RANK}

    def test_snapshot_timeline(self):
        self.assertEqual(list(self.snaps),
                         ["7/23 05:52", "7/29 05:51", "8/4 05:52", "8/22 05:51", "8/28 05:52"])

    def test_first_pass_has_no_high(self):
        p = self._by_priority("7/23 05:52")
        self.assertEqual(p["high"], [])
        self.assertEqual(len(p["medium"]), 2)

    def test_lake_high_on_first_sar_pass_because_of_external_evidence(self):
        # 7/29 SAR 首次偵測，尚未複核；但 7/24 光學、7/27 航拍已發布，多源一致
        e3 = next(e for e in self.snaps["7/29 05:51"]["events"] if e["id"] == "E3")
        self.assertEqual((e3["priority"], e3["persistence"], e3["confidence"]), ("high", "pending", "高"))
        self.assertIn("priority.high.corroborated", e3["rulesFired"])
        self.assertEqual(self._by_priority("8/4 05:52")["high"], ["E3"])

    def test_external_evidence_not_used_before_published(self):
        # 7/23 時光學（7/24）還沒發布；E1、E2 也離壩址太遠，不會對到
        for e in self.snaps["7/23 05:52"]["events"]:
            self.assertFalse(any(r.startswith("external.") for r in e["rulesFired"]))

    def test_lake_is_near_reference_dam(self):
        e3 = self.snaps["8/22 05:51"]["events"][0]
        self.assertEqual(e3["id"], "E3")
        self.assertLess(e3["distanceFromReferenceM"], 600)
        self.assertIn("trend.growing", e3["rulesFired"])

    def test_false_alarms_end_low(self):
        p = self._by_priority("8/28 05:52")
        self.assertEqual(p["high"], ["E3"])
        self.assertEqual(sorted(p["low"]), ["E1", "E2", "E4", "E5"])

    def test_reference_lake_not_counted_as_history(self):
        e3 = self.snaps["8/4 05:52"]["events"][0]
        hist = [e for e in e3["evidence"] if e["kind"] == "history"]
        self.assertTrue(hist)
        self.assertNotIn("馬太鞍", hist[0]["text"])

    def test_hindsight_is_attached_but_not_used_for_triage(self):
        hs = {"lonLat": [121.30, 23.70], "radiusM": 300, "verdict": "false_positive",
              "title": "事後查證：誤報", "text": "光學查證不是水"}
        near = B.matching_hindsight({"hindsight": [hs]}, (121.301, 23.700))
        far = B.matching_hindsight({"hindsight": [hs]}, (121.31, 23.70))
        self.assertEqual((len(near), len(far)), (1, 0))
        # 研判只看 Detection 與 Context，事後查證不會進來
        a = T.assess("E1", [det(T0, cand(persistent=True, iou=0.52))], ctx(T0 + DAY6, latest_pass=T0))
        self.assertEqual(a.priority, "high")

    def test_write_js_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "events.js"
            B.write_js([self.result], out)
            src = out.read_text(encoding="utf-8")
            data = json.loads(src[src.index("["):src.rindex("]") + 1])
            self.assertEqual(data[0]["id"], "matai_an_2025")


if __name__ == "__main__":
    unittest.main()
