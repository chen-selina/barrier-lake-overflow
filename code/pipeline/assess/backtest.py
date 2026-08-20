#!/usr/bin/env python3
"""
backtest.py — C1 時點回測 + C2 蓄水量誤差率

依施工地圖對照表：
- C1：拿 B1（detect/water.py）偵測到「新增水體」的時間，跟官方紀錄的
  「實際形成時間」「實際溢流時間」比對，算出提前量／延遲量。
- C2：拿 B2（assess/hypsometry.py）反演出的蓄水量，跟官方蓄水量數字
  算誤差率——這條公式已經在 `hypsometry.volume_error_rate()` 做好，
  這裡只是把它跟時點回測包成同一份報告，不重寫一次。

官方 ground truth 來源：`data/raw/taiwan-barrier-lakes.csv`（或轉換後的
`dashboard/data/lakes.js`），例如馬太鞍溪的 `formed="2025/7/21"`、
`breachDate="2025/09/23"`、蓄水量 9,100.00 萬立方公尺。

目前限制：B1 還沒接真實 Sentinel-2 影像，所以還沒有真的偵測時間點可以
拿來跑這支——本檔案先把邏輯做好、用合成日期測過，真實資料（B1 偵測
輸出的 `WaterExtent.date`、B2 真實反演出的蓄水量）到位後，直接餵進
`backtest_report()` 就能出報告，不需要再改這支程式。

執行方式：python -m pipeline.assess.backtest
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from .hypsometry import volume_error_rate


def parse_lake_date(text: str) -> date:
    """
    解析 `dashboard/data/lakes.js`／清冊 CSV 慣用的日期格式，例如
    "2025/7/21"、"2025/09/23"（月、日有無前導零都要吃）。

    >>> parse_lake_date("2025/7/21")
    datetime.date(2025, 7, 21)
    >>> parse_lake_date("2025/09/23")
    datetime.date(2025, 9, 23)
    """
    return datetime.strptime(text.strip(), "%Y/%m/%d").date()


@dataclass
class TimingBacktest:
    """單一時間點的回測結果（形成或溢流，用同一個結構）。"""
    label: str                 # "形成" 或 "溢流"，供報告顯示用
    detected_date: date
    official_date: date

    @property
    def lead_days(self) -> int:
        """正值＝系統偵測早於官方紀錄日（提前量）；負值＝晚於（延遲量）。

        >>> TimingBacktest("形成", date(2025, 7, 19), date(2025, 7, 21)).lead_days
        2
        >>> TimingBacktest("形成", date(2025, 7, 23), date(2025, 7, 21)).lead_days
        -2
        """
        return (self.official_date - self.detected_date).days

    def summary(self) -> str:
        d = self.lead_days
        if d > 0:
            return f"{self.label}偵測提前官方紀錄 {d} 天"
        if d < 0:
            return f"{self.label}偵測延遲官方紀錄 {-d} 天"
        return f"{self.label}偵測與官方紀錄同一天"


@dataclass
class VolumeBacktest:
    """C2：蓄水量誤差率。"""
    estimated_wan_m3: float
    official_wan_m3: float

    @property
    def error_rate(self) -> float:
        return volume_error_rate(self.estimated_wan_m3, self.official_wan_m3)

    def summary(self) -> str:
        return (f"模型估算蓄水量 {self.estimated_wan_m3:,.0f} 萬m³，"
                f"官方紀錄 {self.official_wan_m3:,.0f} 萬m³，"
                f"誤差率 {self.error_rate:.1%}")


@dataclass
class BacktestReport:
    """C1+C2 合併報告。"""
    lake_name: str
    timings: list
    volume: Optional[VolumeBacktest] = None

    def summary_lines(self) -> list:
        lines = [f"{self.lake_name} 回測結果："]
        lines += [f"  - {t.summary()}" for t in self.timings]
        if self.volume:
            lines.append(f"  - {self.volume.summary()}")
        return lines

    def to_markdown(self) -> str:
        return "\n".join(self.summary_lines())


def backtest_report(lake_name: str,
                     formed_detected: Optional[date] = None,
                     formed_official: Optional[date] = None,
                     breach_detected: Optional[date] = None,
                     breach_official: Optional[date] = None,
                     estimated_volume_wan_m3: Optional[float] = None,
                     official_volume_wan_m3: Optional[float] = None) -> BacktestReport:
    """
    一站式組報告；每組日期／蓄水量都可選填——資料還沒到位的部分留 None，
    不會硬湊出一個假結果。至少要有一組日期或一組蓄水量，否則報告是空的
    沒有意義，直接丟錯提醒呼叫端。
    """
    timings = []
    if formed_detected and formed_official:
        timings.append(TimingBacktest("形成", formed_detected, formed_official))
    if breach_detected and breach_official:
        timings.append(TimingBacktest("溢流", breach_detected, breach_official))

    volume = None
    if estimated_volume_wan_m3 is not None and official_volume_wan_m3 is not None:
        volume = VolumeBacktest(estimated_volume_wan_m3, official_volume_wan_m3)

    if not timings and not volume:
        raise ValueError("至少需要一組日期或一組蓄水量才能產生回測報告")

    return BacktestReport(lake_name=lake_name, timings=timings, volume=volume)


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"backtest: {total - fails}/{total} 通過")

    # 示範：合成一組日期／蓄水量（不是真的偵測結果！等 B1 真的接上
    # Sentinel-2、B2 真的反演出蓄水量之後，這裡要換成真實數字）
    report = backtest_report(
        lake_name="花蓮馬太鞍溪（示範資料，非真實偵測結果）",
        formed_detected=date(2025, 7, 19),
        formed_official=parse_lake_date("2025/7/21"),
        breach_detected=date(2025, 9, 24),
        breach_official=parse_lake_date("2025/09/23"),
        estimated_volume_wan_m3=8700.0,
        official_volume_wan_m3=9100.0,
    )
    print()
    print(report.to_markdown())
