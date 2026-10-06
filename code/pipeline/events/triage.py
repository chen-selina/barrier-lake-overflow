#!/usr/bin/env python3
"""
事件研判：輸入一個事件在某時點的狀態，輸出優先等級、研判信心、證據、證據缺口與建議任務。

SAR 只當證據來源之一，不直接下結論。規則全部寫死在這裡，每項判斷都記進
rules_fired，跟 attribution 一樣可以對回是哪條規則產生的。

優先等級（決策表，依序比對）：
    持續性中斷   前期已確認蓄水、最新一期卻未見         → 高　建議立即查證（可能潰決或排空）
    已確認持續   多期 SAR 一致且附近有崩塌（A 級）        → 高　建議立即查證
    待複核       單期 SAR，空間條件符合（B 級）            → 中　建議人工確認
    待複核       單期 SAR，附近無崩塌訊號（C 級）          → 低　暫時觀察
    複核未持續   下一期同位置水體 IoU 未達門檻              → 低　暫時觀察
同一等級內依面積由大到小排。

研判信心（高／中／低）：
    證據只有 SAR 時最高到「中」。要到「高」需要 SAR 以外的獨立證據
    （人工查證、光學影像），這部分由值班人員在儀表板上補。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

TW = timezone(timedelta(hours=8))

# 門檻常數（專案自訂，對外須註明）
SCALE_LARGE_HA = 10.0          # SAR 面積 ≥ 此值視為「大」
SCALE_MEDIUM_HA = 1.0          # 1～10 公頃為「中」，以下為「小」
GROWING_RATIO = 1.5            # 最新面積 ≥ 首次 × 此值視為擴大
SHRINKING_RATIO = 0.67
HISTORY_RADIUS_KM = 10.0       # 歷史災害的搜尋半徑

PRIORITY_TEXT = {"high": "高優先", "medium": "中優先", "low": "低優先"}
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
ACTION_TEXT = {"high": "建議立即查證", "medium": "建議人工確認", "low": "暫時觀察"}
PERSISTENCE_TEXT = {
    "confirmed": "已確認持續",
    "pending": "待複核",
    "failed": "複核未持續",
    "lost": "持續性中斷",
}
SHORT_NAME = {"sar": "SAR 新增水體", "persistence": "跨期持續", "river": "貼河道",
              "landslide": "附近崩塌", "terrain": "堵塞型態", "trend": "面積擴大"}


# 時間

def tw_label(t: datetime) -> str:
    """
    >>> tw_label(datetime(2025, 7, 22, 21, 52, tzinfo=timezone.utc))
    '7/23 05:52'
    """
    t = t.astimezone(TW)
    return f"{t.month}/{t.day} {t:%H:%M}"


def tw_date(t: datetime) -> str:
    t = t.astimezone(TW)
    return f"{t.month}/{t.day}"


# 資料結構

@dataclass
class Detection:
    """某一期 SAR 偵測到的一個候選水體（final_*.json 的 candidates 一筆）。"""
    pass_time: datetime
    recheck_time: Optional[datetime]     # 該期排定的複核影像時間；沒有複核期為 None
    cand: dict
    evidence_image: Optional[str] = None

    @property
    def area_ha(self) -> float:
        return float(self.cand["areaHectare"])

    @property
    def lon_lat(self) -> tuple:
        return tuple(self.cand["centroidLonLat"])

    @property
    def iou(self) -> Optional[float]:
        """複核 IoU。偵測端只寫在 reasons 文字裡，從那裡取。"""
        for r in self.cand.get("reasons", []):
            m = re.search(r"IoU 最高 ([\d.]+)", r)
            if m:
                return float(m.group(1))
        return None

    def recheck_state(self, as_of: datetime) -> str:
        """as_of 當下這筆偵測的複核狀態：persistent / not_persistent / pending。"""
        if (self.recheck_time is None or self.recheck_time > as_of
                or not self.cand.get("laterScenesChecked")):
            return "pending"
        return "persistent" if self.cand.get("persistent") else "not_persistent"


@dataclass
class Context:
    """跟單一事件無關、整個時點共用的背景。"""
    as_of: datetime
    latest_analyzed_pass: Optional[datetime]   # as_of 以前最近一期有跑全幅偵測的影像
    next_pass: Optional[datetime]              # 下一期預計過境
    rain_available: bool = False
    trigger_label: str = ""
    context_lines: list = field(default_factory=list)
    history: list = field(default_factory=list)   # [{"name", "year", "distanceKm"}]
    reference_lon_lat: Optional[tuple] = None


# 判定

def persistence(dets: list, ctx: Context) -> str:
    """
    事件層級的持續性。曾經被複核確認，或在兩期以上都被偵測到，就算確認過。
    確認過之後如果最新一期沒再出現，改判「持續性中斷」。
    """
    states = [d.recheck_state(ctx.as_of) for d in dets]
    # 複核未持續之後又在同位置出現，不直接算確認，回到待複核
    redetected = len({d.pass_time for d in dets}) >= 2 and "not_persistent" not in states
    confirmed_ever = "persistent" in states or redetected
    latest = dets[-1]
    if confirmed_ever:
        missing_since = (ctx.latest_analyzed_pass is not None
                         and ctx.latest_analyzed_pass > latest.pass_time)
        if states[-1] == "not_persistent" or missing_since:
            return "lost"
        return "confirmed"
    return "failed" if states[-1] == "not_persistent" else "pending"


def sar_grade(landslide: bool, pers: str) -> str:
    """跟 detect.barrier_lake._grade 同一套：崩塌＋持續為 A、只有崩塌為 B、其餘為 C。"""
    if landslide and pers in ("confirmed", "lost"):
        return "A"
    return "B" if landslide else "C"


def scale_of(area_ha: float) -> str:
    """
    >>> scale_of(26.3), scale_of(5.8), scale_of(0.5)
    ('大', '中', '小')
    """
    if area_ha >= SCALE_LARGE_HA:
        return "大"
    if area_ha >= SCALE_MEDIUM_HA:
        return "中"
    return "小"


def trend_of(dets: list) -> Optional[str]:
    if len(dets) < 2:
        return None
    first, last = dets[0].area_ha, dets[-1].area_ha
    if last >= first * GROWING_RATIO:
        return "growing"
    if last <= first * SHRINKING_RATIO:
        return "shrinking"
    return "stable"


def _iou_text(d: Detection) -> str:
    return f"IoU {d.iou:.2f}" if d.iou is not None else "IoU 未記錄"


@dataclass
class Assessment:
    priority: str
    action: str
    confidence: str
    confidence_reasons: list
    persistence: str
    grade: str
    scale: str
    summary: str
    evidence: list
    gaps: list
    conflicts: list
    tasks: list
    rules_fired: list

    def to_dict(self) -> dict:
        return {
            "priority": self.priority,
            "priorityText": PRIORITY_TEXT[self.priority],
            "action": self.action,
            "confidence": self.confidence,
            "confidenceReasons": self.confidence_reasons,
            "persistence": self.persistence,
            "persistenceText": PERSISTENCE_TEXT[self.persistence],
            "grade": self.grade,
            "scale": self.scale,
            "summary": self.summary,
            "evidence": self.evidence,
            "gaps": self.gaps,
            "conflicts": self.conflicts,
            "tasks": self.tasks,
            "rulesFired": self.rules_fired,
        }


def assess(label: str, dets: list, ctx: Context) -> Assessment:
    """
    label：事件代號（例如 E2）
    dets：as_of 以前的偵測，依時間排序
    """
    if not dets:
        raise ValueError("事件至少要有一筆偵測")
    rules: list = []
    latest = dets[-1]
    c = latest.cand
    pers = persistence(dets, ctx)
    grade = sar_grade(bool(c.get("landslideNearby")), pers)
    rules.append(f"persistence.{pers}")
    trend = trend_of(dets)
    next_pass = tw_date(ctx.next_pass) if ctx.next_pass else "下一期"

    # ── 證據（status：support 支持／against 不支持／context 背景）
    evidence = [{
        "kind": "sar", "status": "support",
        "text": f"{tw_label(latest.pass_time)} SAR 新增水體 {latest.area_ha:.2f} 公頃（證據強度 {grade} 級）",
    }]

    persistent_dets = [d for d in dets if d.recheck_state(ctx.as_of) == "persistent"]
    if pers == "confirmed":
        if persistent_dets:
            d = persistent_dets[-1]
            text = (f"{tw_date(d.recheck_time)} 複核同位置仍有水體（{_iou_text(d)}），"
                    f"共 {len(dets)} 期偵測到")
        else:
            text = f"連續 {len(dets)} 期在同位置偵測到"
        evidence.append({"kind": "persistence", "status": "support", "text": text})
    elif pers == "failed":
        evidence.append({"kind": "persistence", "status": "against",
                         "text": f"{tw_date(latest.recheck_time)} 複核同位置水體 {_iou_text(latest)}，未持續"})
    elif pers == "lost":
        evidence.append({"kind": "persistence", "status": "against",
                         "text": "前期已確認蓄水，最新一期同位置未再偵測到或複核未持續"})

    if c.get("onRiver"):
        rules.append("spatial.on_river")
        evidence.append({"kind": "river", "status": "support",
                         "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"})
    if c.get("landslideNearby"):
        rules.append("spatial.landslide")
        evidence.append({"kind": "landslide", "status": "support",
                         "text": f"500 m 內有 SAR 崩塌訊號 {float(c.get('landslideAreaHectare') or 0):.1f} 公頃"})
    if c.get("damDownstream"):
        rules.append("spatial.blockage")
        evidence.append({"kind": "terrain", "status": "support",
                         "text": f"崩塌延伸到水體下游、湖底高程（{c.get('lakeFloorM'):.0f} m）以下，符合堵塞型態"})

    if trend == "growing":
        rules.append("trend.growing")
        evidence.append({"kind": "trend", "status": "support",
                         "text": f"面積 {dets[0].area_ha:.1f} → {latest.area_ha:.1f} 公頃，擴大中"})
    elif trend == "shrinking":
        rules.append("trend.shrinking")
        evidence.append({"kind": "trend", "status": "context",
                         "text": f"面積 {dets[0].area_ha:.1f} → {latest.area_ha:.1f} 公頃，縮小中"})

    if ctx.history:
        rules.append("history.nearby")
        items = "、".join(f"{h['year']} {h['name']}（{h['distanceKm']:.1f} km）" for h in ctx.history)
        evidence.append({"kind": "history", "status": "context",
                         "text": f"{HISTORY_RADIUS_KM:.0f} km 內清冊另有 {len(ctx.history)} 筆堰塞湖：{items}"})
    for line in ctx.context_lines:
        evidence.append({"kind": "context", "status": "context", "text": line})

    # ── 證據缺口
    gaps = []
    if pers == "pending":
        gaps.append({"kind": "persistence", "text": f"尚未複核：單期影像無法排除陰影或濕土誤判（下一期 {next_pass}）"})
    if not ctx.rain_available:
        rules.append("gap.rain")
        gaps.append({"kind": "rain", "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"})
    rules.append("gap.optical")
    gaps.append({"kind": "optical", "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"})
    rules.append("gap.exposure")
    gaps.append({"kind": "exposure", "text": "下游保全對象：尚未串接（可接 BigGIS、內政部道路與聚落圖層）"})
    gaps.append({"kind": "field", "text": "人工查證：尚未進行"})

    # ── 證據衝突
    conflicts = []
    spatial_ok = all(c.get(k) for k in ("onRiver", "landslideNearby", "damDownstream"))
    if pers == "failed" and spatial_ok:
        rules.append("conflict.spatial_vs_persistence")
        conflicts.append("空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見"
                         "成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。")
    if pers == "lost":
        conflicts.append("前期多期一致，最新一期卻未見：可能是潰決、排空，也可能是陰影遮罩擋掉湖面，需人工判斷。")

    # ── 優先等級、行動、任務
    tasks = []
    area_note = f"{latest.area_ha:.1f} 公頃"
    if pers == "lost":
        priority = "high"
        rules.append("priority.high.lost")
        tasks += [
            {"label": "立即查證是否潰決或排空", "reason": "前期已確認蓄水，最新一期未見；潰決會直接影響下游"},
            {"label": "調閱最新光學影像", "reason": "確認湖面是否仍在，排除 SAR 遮罩造成的漏偵"},
            {"label": "通報主管機關（農村水保署）", "reason": "下游保全對象尚未串接，需由主管機關評估"},
        ]
    elif pers == "confirmed" and grade == "A":
        priority = "high"
        rules.append("priority.high.confirmed")
        tasks += [
            {"label": "UAV／現地查證壩體與湖面", "reason": "SAR 只能看到水面，壩體高度、材料與溢流風險要現地確認"},
            {"label": "調閱最新光學影像", "reason": "SAR 陡坡遮罩會擋掉約四成湖面，面積偏低，需光學影像確認範圍"},
            {"label": "通報主管機關（農村水保署）並評估下游保全對象", "reason": "下游聚落、道路圖層尚未串接"},
            {"label": f"持續 SAR 監測（下一期 {next_pass}）",
             "reason": "追蹤湖面變化" + ("；目前面積擴大中" if trend == "growing" else "")},
        ]
    elif pers == "pending" and grade == "B":
        priority = "medium"
        rules.append("priority.medium.pending")
        tasks += [
            {"label": "值班人員判讀 SAR 證據圖", "reason": "確認暗區是否在河谷底、是否為崩塌坡面陰影"},
            {"label": f"排下一期 SAR 複核（{next_pass}）", "reason": "A 級需要兩期一致；單期出現的暗區多數會在複核時消失"},
            {"label": "調閱光學影像（雲況許可時）", "reason": "SAR 以外的獨立證據"},
            {"label": "暫不派遣 UAV", "reason": "目前只有單期 SAR，先以複核過濾誤報，避免浪費現地人力"},
        ]
    else:
        priority = "low"
        rules.append("priority.low." + ("failed" if pers == "failed" else "no_landslide"))
        if pers == "failed":
            reason = f"下一期複核同位置水體 {_iou_text(latest)}，未持續"
        else:
            reason = "附近沒有崩塌訊號，不符合堵塞成湖的型態"
        tasks += [
            {"label": "暫時觀察，不派遣任務", "reason": reason},
            {"label": "若同位置再次出現，重新列入待複核", "reason": "跨期追蹤以 250 m 內為同一事件"},
        ]
    if not ctx.rain_available and priority != "low":
        tasks.append({"label": "補查形成期間雨量", "reason": "確認觸發條件；目前觀測表此欄空白"})

    # ── 研判信心
    if pers == "confirmed":
        confidence = "中"
        conf_reasons = [f"SAR {len(dets)} 期一致", "證據只有 SAR 一種來源，最高到「中」；需光學或現地證據才能到「高」"]
    elif pers == "failed":
        confidence = "中"
        conf_reasons = [f"複核結果明確（{_iou_text(latest)}）", "證據只有 SAR 一種來源，最高到「中」"]
    else:
        confidence = "低"
        conf_reasons = (["只有單期 SAR，尚未複核"] if pers == "pending"
                        else ["前後期結果不一致，需人工判斷"])

    # ── 一句話摘要
    support = [SHORT_NAME[e["kind"]] for e in evidence if e["status"] == "support"]
    if priority == "high" and pers == "confirmed":
        summary = (f"{label} 值得優先查證：{len(support)} 項證據一致（{'、'.join(support)}）；"
                   f"目前缺少光學影像與現地證據，建議下一步 UAV 現地查證並調閱光學影像。")
    elif priority == "high":
        summary = f"{label} 需要立即查證：前期已確認蓄水，最新一期未再出現，可能已潰決或排空。"
    elif priority == "medium":
        summary = (f"{label} 需要人工確認：單期 SAR 出現約 {area_note}的疑似新增水體，空間條件符合，但尚未複核；"
                   f"建議 {next_pass} 下一期過境複核，暫不派遣 UAV。")
    elif pers == "failed":
        summary = f"{label} 暫時觀察：空間條件符合，但下一期複核未持續（{_iou_text(latest)}），不建議派遣任務。"
    else:
        summary = f"{label} 暫時觀察：附近沒有崩塌訊號，不符合堵塞成湖的型態。"

    return Assessment(
        priority=priority, action=ACTION_TEXT[priority],
        confidence=confidence, confidence_reasons=conf_reasons,
        persistence=pers, grade=grade, scale=scale_of(latest.area_ha),
        summary=summary, evidence=evidence, gaps=gaps, conflicts=conflicts,
        tasks=tasks, rules_fired=rules,
    )
