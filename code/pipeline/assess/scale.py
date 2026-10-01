"""
蓄水量 → 規模級距 + 信心等級

hypsometry 算出的蓄水量只當作「落在哪個級距」的依據，不對外報單一數字。
級距沿用 attribution.verbalize.VOLUME_SCALES（專案自訂，對外須註明）。

估計區間：估計值 ×(1 ± rel_error)。rel_error 預設 0.4，取自馬太鞍溪
C2 回測（39.7%），目前只有這一個案例。區間跨兩個級距時輸出「大型～極大型」。

信心等級（高／中／低）：
- 依湖面面積的來源決定起點：SAR 判定 A 級為高、B 級為中、C 級為低；
  面積沒經過 A/B/C 判定（例如單期 NDWI）為中
- 估計區間跨級距：降一級
- 曲線有問題（面積超出掃描範圍、落在面積斷崖）：直接為低
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pipeline.attribution.verbalize import volume_scale

# 跟 attribution/templates.yaml 的 formation.scale 一致
SCALE_LABEL = {"tiny": "小型", "small": "小型", "medium": "中型",
               "large": "大型", "huge": "極大型"}
CONFIDENCE = ["高", "中", "低"]
GRADE_TO_LEVEL = {"A": 0, "B": 1, "C": 2}

DEFAULT_REL_ERROR = 0.4


@dataclass
class VolumeClass:
    estimate_wan_m3: float
    low_wan_m3: float
    high_wan_m3: float
    scale_low: str
    scale_high: str
    confidence: str
    reasons: list = field(default_factory=list)

    @property
    def scale(self) -> str:
        if self.scale_low == self.scale_high:
            return self.scale_low
        return f"{self.scale_low}～{self.scale_high}"

    def to_dict(self) -> dict:
        return {
            "scale": self.scale,
            "confidence": self.confidence,
            "rangeWanM3": [round(self.low_wan_m3), round(self.high_wan_m3)],
            "estimateWanM3": round(self.estimate_wan_m3, 1),
            "reasons": self.reasons,
        }


def _label(wan_m3: float) -> str:
    return SCALE_LABEL[volume_scale(wan_m3) or "tiny"]


def classify_volume(estimate_wan_m3: float,
                    rel_error: float = DEFAULT_REL_ERROR,
                    detection_grade: Optional[str] = None,
                    curve_ok: bool = True) -> VolumeClass:
    """
    estimate_wan_m3：hypsometry 估的蓄水量（萬 m³）
    detection_grade：湖面面積來自 SAR 判定時給 "A"/"B"/"C"，否則 None
    curve_ok：run_hypsometry_real 的飽和／斷崖檢查都沒觸發時為 True

    >>> c = classify_volume(12716)
    >>> c.scale, c.confidence
    ('極大型', '中')
    >>> classify_volume(4000, detection_grade="A").scale
    '大型～極大型'
    """
    if estimate_wan_m3 <= 0:
        raise ValueError("蓄水量估計值必須大於 0")
    if not 0 <= rel_error < 1:
        raise ValueError("rel_error 須介於 0 與 1 之間")

    low = estimate_wan_m3 * (1 - rel_error)
    high = estimate_wan_m3 * (1 + rel_error)
    scale_low, scale_high = _label(low), _label(high)
    reasons = [f"估計 {estimate_wan_m3:,.0f} 萬 m³，誤差 ±{rel_error:.0%} → "
               f"{low:,.0f}～{high:,.0f} 萬 m³"]

    if not curve_ok:
        reasons.append("水位–容積曲線未通過檢查（面積飽和或斷崖），數值不可信")
        level = 2
    else:
        if detection_grade is None:
            level = 1
            reasons.append("湖面面積未經 SAR 多時相判定")
        else:
            level = GRADE_TO_LEVEL[detection_grade]
            reasons.append(f"湖面面積來自 SAR 判定 {detection_grade} 級")
        if scale_low != scale_high:
            level = min(level + 1, 2)
            reasons.append("估計區間跨兩個級距，降一級")

    return VolumeClass(estimate_wan_m3, low, high, scale_low, scale_high,
                       CONFIDENCE[level], reasons)
