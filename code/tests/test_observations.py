#!/usr/bin/env python3
"""
test_observations.py — pipeline.ingest.observations 單元測試（B6）

全部用臨時合成的 CSV 測，數值皆為測試用假資料，不是真的馬太鞍溪
觀測值——真實觀測資料要由團隊查證後填進 data/raw/observations.csv，
不在本檔測試範圍內。

執行（於 code/ 目錄下）：
    pytest tests/test_observations.py -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime

from pipeline.ingest import observations as O


def _write_csv(path, rows):
    header = ",".join(O._CSV_FIELDS)
    lines = [header]
    for row in rows:
        lines.append(",".join(row.get(f, "") for f in O._CSV_FIELDS))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


class TestLoadObservationsTable(unittest.TestCase):
    def test_missing_file_returns_empty_dict(self):
        table = O.load_observations_table(path="/no/such/file/observations.csv")
        self.assertEqual(table, {})

    def test_row_with_only_lake_id_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "observations.csv")
            _write_csv(path, [{"lake_id": "bl001"}])
            table = O.load_observations_table(path=path)
        self.assertEqual(table, {})

    def test_full_row_parses_all_field_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "observations.csv")
            _write_csv(path, [{
                "lake_id": "bl071",
                "rain_24h_mm": "180.5",
                "rain_window_hours": "24",
                "rain_max_hourly_mm": "45.2",
                "rain_percentile": "97.3",
                "typhoon_name": "測試颱風",
                "typhoon_distance_km": "120.0",
                "southwest_flow": "true",
                "quake_name": "測試地震",
                "quake_time": "2025-07-20T10:00:00+08:00",
                "quake_magnitude": "6.1",
                "pga_gal": "85.0",
                "formed_time": "2025-07-21T08:00:00+08:00",
                "frontal_system": "false",
            }])
            table = O.load_observations_table(path=path)

        self.assertIn("bl071", table)
        obs = table["bl071"]
        self.assertEqual(obs.rain_24h_mm, 180.5)
        self.assertEqual(obs.rain_window_hours, 24)
        self.assertEqual(obs.typhoon_name, "測試颱風")
        self.assertEqual(obs.typhoon_distance_km, 120.0)
        self.assertTrue(obs.southwest_flow)
        self.assertFalse(obs.frontal_system)
        self.assertEqual(obs.quake_magnitude, 6.1)
        self.assertEqual(obs.pga_gal, 85.0)
        self.assertEqual(obs.quake_time, datetime.fromisoformat("2025-07-20T10:00:00+08:00"))
        self.assertEqual(obs.formed_time, datetime.fromisoformat("2025-07-21T08:00:00+08:00"))

    def test_partial_row_leaves_unfilled_fields_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "observations.csv")
            _write_csv(path, [{"lake_id": "bl002", "rain_24h_mm": "50.0"}])
            table = O.load_observations_table(path=path)

        obs = table["bl002"]
        self.assertEqual(obs.rain_24h_mm, 50.0)
        self.assertIsNone(obs.typhoon_name)
        self.assertIsNone(obs.quake_magnitude)
        self.assertEqual(obs.rain_window_hours, 24)  # 預設值

    def test_multiple_rows_keyed_by_lake_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "observations.csv")
            _write_csv(path, [
                {"lake_id": "bl001", "rain_24h_mm": "10.0"},
                {"lake_id": "bl002", "rain_24h_mm": "20.0"},
            ])
            table = O.load_observations_table(path=path)

        self.assertEqual(set(table.keys()), {"bl001", "bl002"})
        self.assertEqual(table["bl001"].rain_24h_mm, 10.0)
        self.assertEqual(table["bl002"].rain_24h_mm, 20.0)


if __name__ == "__main__":
    unittest.main()
