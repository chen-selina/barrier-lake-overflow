#!/usr/bin/env python3
"""
test_backtest.py — pipeline.assess.backtest 單元測試（C1 時點回測 / C2 誤差率）

全部用合成日期／數字測試——真實的偵測時間點跟反演蓄水量還沒有，
等 B1 接上真實 Sentinel-2 影像、B2 接上真實 DEM 之後，同一套
backtest_report() 直接餵真數字即可，不用再測一次。

執行（於 code/ 目錄下）：
    pytest tests/test_backtest.py -v
"""

from __future__ import annotations

import unittest
from datetime import date

from pipeline.assess import backtest as B


class TestParseLakeDate(unittest.TestCase):
    def test_single_digit_month_and_day(self):
        self.assertEqual(B.parse_lake_date("2025/7/21"), date(2025, 7, 21))

    def test_zero_padded_month_and_day(self):
        self.assertEqual(B.parse_lake_date("2025/09/23"), date(2025, 9, 23))


class TestTimingBacktest(unittest.TestCase):
    def test_early_detection_gives_positive_lead_days(self):
        t = B.TimingBacktest("形成", date(2025, 7, 19), date(2025, 7, 21))
        self.assertEqual(t.lead_days, 2)
        self.assertIn("提前", t.summary())

    def test_late_detection_gives_negative_lead_days(self):
        t = B.TimingBacktest("溢流", date(2025, 9, 26), date(2025, 9, 23))
        self.assertEqual(t.lead_days, -3)
        self.assertIn("延遲", t.summary())

    def test_same_day_is_neither_early_nor_late(self):
        t = B.TimingBacktest("形成", date(2025, 7, 21), date(2025, 7, 21))
        self.assertEqual(t.lead_days, 0)
        self.assertIn("同一天", t.summary())


class TestVolumeBacktest(unittest.TestCase):
    def test_error_rate_matches_hypsometry_formula(self):
        v = B.VolumeBacktest(8700.0, 9100.0)
        self.assertAlmostEqual(v.error_rate, abs(8700.0 - 9100.0) / 9100.0)
        self.assertIn("誤差率", v.summary())


class TestBacktestReport(unittest.TestCase):
    def test_full_report_includes_both_timings_and_volume(self):
        report = B.backtest_report(
            lake_name="測試湖",
            formed_detected=date(2025, 7, 19), formed_official=date(2025, 7, 21),
            breach_detected=date(2025, 9, 24), breach_official=date(2025, 9, 23),
            estimated_volume_wan_m3=8700.0, official_volume_wan_m3=9100.0,
        )
        self.assertEqual(len(report.timings), 2)
        self.assertIsNotNone(report.volume)
        md = report.to_markdown()
        self.assertIn("測試湖", md)
        self.assertIn("提前", md)
        self.assertIn("延遲", md)
        self.assertIn("誤差率", md)

    def test_partial_data_only_includes_whats_available(self):
        # B1/B2 資料還沒到位很常見的情況：只有形成時間，沒有溢流時間跟蓄水量
        report = B.backtest_report(
            lake_name="測試湖",
            formed_detected=date(2025, 7, 19), formed_official=date(2025, 7, 21),
        )
        self.assertEqual(len(report.timings), 1)
        self.assertIsNone(report.volume)

    def test_no_data_at_all_raises(self):
        with self.assertRaises(ValueError):
            B.backtest_report(lake_name="測試湖")

    def test_incomplete_pair_is_silently_skipped_not_guessed(self):
        # 只有偵測日期、沒有官方日期（或反過來）：不該硬湊一個提前量出來
        report = B.backtest_report(
            lake_name="測試湖",
            formed_detected=date(2025, 7, 19),
            estimated_volume_wan_m3=8700.0, official_volume_wan_m3=9100.0,
        )
        self.assertEqual(len(report.timings), 0)
        self.assertIsNotNone(report.volume)


if __name__ == "__main__":
    unittest.main()
