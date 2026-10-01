#!/usr/bin/env python3
"""
抓 CWA 自動雨量站即時觀測（O-A0002-001），配對每座湖最近的測站。
只負責抓資料，風險判斷在 pipeline.ingest.risk。

    python -m pipeline.ingest.cwa   # 除錯用，印出抓到幾個測站
"""

from __future__ import annotations

import math
import os
import ssl

CWA_STATION_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001"


def _as_list(x):
    return [] if x is None else (x if isinstance(x, list) else [x])


def fetch_rainfall_stations(api_key: str, timeout: int = 30) -> list[dict]:
    """抓 CWA O-A0002-001 全部自動雨量站的最新觀測。

    回傳 [{"lat":..,"lon":..,"r24h":..}, ...]；r24h 為過去 24 小時累積雨量
    （毫米），缺測或負值（CWA 用負數標示缺測/微量）一律視為 None。

    需要 `requests`（見 requirements.txt，CWA 介接階段已解開）。
    """
    import requests
    from requests.adapters import HTTPAdapter

    class _TLS(HTTPAdapter):
        """CWA 開放資料平台的憑證鏈在部分環境下會被 OpenSSL 3 的
        嚴格 X509 檢查擋下，放寬到與瀏覽器一致的驗證等級即可，
        仍然驗證憑證，只是不強制最嚴格的鏈完整性規則。"""

        def init_poolmanager(self, *a, **k):
            ctx = ssl.create_default_context()
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
            k["ssl_context"] = ctx
            return super().init_poolmanager(*a, **k)

    session = requests.Session()
    session.mount("https://", _TLS())
    resp = session.get(
        CWA_STATION_URL,
        params={"Authorization": api_key, "format": "JSON"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    stations = []
    for st in _as_list((data.get("records") or {}).get("Station")):
        try:
            geo = st.get("GeoInfo", {})
            coords = _as_list(geo.get("Coordinates") or geo.get("Coordinate"))
            wgs = next(
                (c for c in coords if "WGS" in str(c.get("CoordinateName"))),
                coords[0] if coords else {},
            )
            rain_el = st.get("RainfallElement", {})

            def rain_value(*keys):
                for k in keys:
                    node = next(
                        (rain_el[kk] for kk in rain_el if kk.lower() == k.lower()),
                        None,
                    )
                    if isinstance(node, dict):
                        try:
                            v = float(node.get("Precipitation"))
                            return None if v < 0 else v
                        except (TypeError, ValueError):
                            return None
                return None

            stations.append({
                "lat": float(wgs.get("StationLatitude")),
                "lon": float(wgs.get("StationLongitude")),
                "r24h": rain_value("Past24hr"),
            })
        except (TypeError, ValueError, AttributeError):
            continue
    return stations


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_station_rain(lat: float, lon: float, stations: list[dict]):
    """回傳 (最近站的過去24小時雨量mm 或 0.0, 距離km)；無測站回傳 (None, None)。"""
    best, best_km = None, float("inf")
    for s in stations:
        d = _haversine_km(lat, lon, s["lat"], s["lon"])
        if d < best_km:
            best_km, best = d, s
    if best is None:
        return None, None
    return (best.get("r24h") or 0.0), round(best_km, 1)


def cli() -> None:
    api_key = os.environ.get("CWA_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("✗ 未設定 CWA_API_KEY，無法測試連線。")
    stations = fetch_rainfall_stations(api_key)
    print(f"✓ 取得 {len(stations)} 個雨量站（O-A0002-001）")


if __name__ == "__main__":
    cli()
