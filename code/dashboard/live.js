/* live.js — 在瀏覽器直接抓 CWA 即時雨量（O-A0002-001），重算風險。

   模型係數跟 pipeline/ingest/risk.py 相同。結果只留在這個分頁，
   重新整理就回到 risk.js 的快照。金鑰只存在瀏覽器（勾「記住」才寫 localStorage）。
   CWA 自動站只有 24 小時累積雨量，rain_3d / rain_7d 用 24h 值代替，
   rain_30d 用訓練平均值。如果瀏覽器擋跨網域請求，改跑
   python -m pipeline.build_all --live。 */

'use strict';

(function () {
  const CWA_URL = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001';
  const STORAGE_KEY = 'cwaApiKey';

  // ── 模型（同 pipeline/ingest/risk.py）──
  const LOGIT_INTERCEPT = -3.0259088850754257;
  const LOGIT_COEF_RAW = {
    rain_7d: 0.03584177519291969, rain_30d: -0.004287918499608312,
    formed_by_rain: 0.8962255211119667, rain_3d: -0.009245420542333044,
    formed_by_quake: 0.7759403879983273, volume: -0.327464903294034,
    rain_1d: 0.007929487298660217,
  };
  const FEATURE_MEANS = {
    rain_7d: 51.235, rain_30d: 218.283, formed_by_rain: 0.584,
    rain_3d: 21.968, formed_by_quake: 0.264, volume: 0.288,
    rain_1d: 7.322,
  };

  function logitProb(features) {
    let z = LOGIT_INTERCEPT;
    for (const k of Object.keys(LOGIT_COEF_RAW)) {
      const x = features[k];
      z += LOGIT_COEF_RAW[k] * (x != null ? x : (FEATURE_MEANS[k] || 0));
    }
    return 1 / (1 + Math.exp(-z));
  }
  const zhLevel = p => (p >= 0.5 ? '高' : '低');
  function alertLevel(p) {
    if (p >= 0.80) return 'IMMEDIATE';
    if (p >= 0.50) return 'URGENT';
    if (p >= 0.30) return 'WATCH';
    return 'STABLE';
  }

  function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371, toRad = d => (d * Math.PI) / 180;
    const dphi = toRad(lat2 - lat1), dl = toRad(lon2 - lon1);
    const a = Math.sin(dphi / 2) ** 2 +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dl / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  const asArray = x => (x == null ? [] : (Array.isArray(x) ? x : [x]));

  // ── 抓 CWA 即時雨量站（跟 pipeline/ingest/cwa.py 邏輯相同）──
  async function fetchStations(apiKey) {
    const url = `${CWA_URL}?Authorization=${encodeURIComponent(apiKey)}&format=JSON`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`CWA API 回應 ${res.status}`);
    const data = await res.json();
    const list = asArray(data && data.records && data.records.Station);

    const stations = [];
    for (const st of list) {
      try {
        const geo = st.GeoInfo || {};
        const coords = asArray(geo.Coordinates || geo.Coordinate);
        const wgs = coords.find(c => String(c.CoordinateName || '').includes('WGS')) || coords[0];
        if (!wgs) continue;

        const rainEl = st.RainfallElement || {};
        let r24 = null;
        for (const key of Object.keys(rainEl)) {
          if (key.toLowerCase() === 'past24hr') {
            const v = parseFloat(rainEl[key] && rainEl[key].Precipitation);
            r24 = (!isNaN(v) && v >= 0) ? v : null;
            break;
          }
        }
        const lat = parseFloat(wgs.StationLatitude), lon = parseFloat(wgs.StationLongitude);
        if (isNaN(lat) || isNaN(lon)) continue;
        stations.push({ lat, lon, r24h: r24 });
      } catch (e) { /* 單筆解析失敗跳過，不影響其他測站 */ }
    }
    return stations;
  }

  function nearestStationRain(lat, lon, stations) {
    let best = null, bestKm = Infinity;
    for (const s of stations) {
      const d = haversineKm(lat, lon, s.lat, s.lon);
      if (d < bestKm) { bestKm = d; best = s; }
    }
    if (!best) return [null, null];
    return [best.r24h != null ? best.r24h : 0, Math.round(bestKm * 10) / 10];
  }

  // ── 套公式，更新 LAKES / RISK / RISK_META（來自 app.js 的模組層級變數）──
  function computeAllLakes(stations) {
    const today = new Date().toISOString().slice(0, 10);
    let nHi = 0;

    for (const lake of LAKES) {
      const name = (lake.name || '').trim();
      if (!name || lake.lat == null || lake.lon == null) continue;

      let rain, distKm;
      if (stations && stations.length) {
        const [r24, d] = nearestStationRain(lake.lat, lake.lon, stations);
        rain = { rain_1d: r24, rain_3d: r24, rain_7d: r24, rain_30d: FEATURE_MEANS.rain_30d };
        distKm = d;
      } else {
        rain = { rain_1d: FEATURE_MEANS.rain_1d, rain_3d: FEATURE_MEANS.rain_3d,
                 rain_7d: FEATURE_MEANS.rain_7d, rain_30d: FEATURE_MEANS.rain_30d };
        distKm = null;
      }

      const volWan = lake.volume;
      const volume = (volWan != null && volWan !== '') ? Number(volWan) / 100 : FEATURE_MEANS.volume;
      const formedByRain = lake.causeKey === 'rain' ? 1 : 0;
      const formedByQuake = lake.causeKey === 'quake' ? 1 : 0;

      const features = Object.assign({}, rain,
        { volume, formed_by_rain: formedByRain, formed_by_quake: formedByQuake });
      const p = logitProb(features);
      if (p >= 0.5) nHi += 1;

      const entry = {
        date: today,
        rain_1d: rain.rain_1d, rain_3d: rain.rain_3d, rain_7d: rain.rain_7d, rain_30d: rain.rain_30d,
        volume, formed_by_quake: formedByQuake, formed_by_rain: formedByRain,
        nearest_station_km: distKm,
        risk_prob: Math.round(p * 10000) / 10000,
        risk_level: zhLevel(p),
        alert: alertLevel(p),
      };

      RISK[name] = entry;
      lake.risk = entry;
    }

    if (RISK_META) {
      RISK_META.mode = (stations && stations.length)
        ? 'LIVE(CWA O-A0002-001，瀏覽器端直接抓取)'
        : 'OFFLINE(訓練平均值佔位)';
      RISK_META.updated = new Date().toISOString();
    }
    return nHi;
  }

  function setStatus(msg, kind) {
    const el = document.getElementById('liveStatus');
    if (!el) return;
    el.textContent = msg;
    el.className = 'livebar-status' + (kind ? ` live-${kind}` : '');
  }

  function redrawEverything() {
    // 這幾個都是 app.js 的全域函式
    if (typeof refresh === 'function') refresh();
    if (typeof renderDetail === 'function') renderDetail();
    if (typeof renderStats === 'function') renderStats();
  }

  async function updateLive() {
    const input = document.getElementById('cwaKeyInput');
    const remember = document.getElementById('cwaKeyRemember');
    const key = (input && input.value || '').trim();

    try {
      if (remember && remember.checked && key) {
        localStorage.setItem(STORAGE_KEY, key);
      } else if (remember && !remember.checked) {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (e) { /* localStorage 被封鎖（例如無痕模式）也不影響主流程 */ }

    if (!key) {
      setStatus('沒有輸入金鑰，改用訓練平均值佔位（非真雨量）…', 'warn');
      computeAllLakes(null);
      redrawEverything();
      setStatus('已套用 offline 佔位資料，不是真雨量。', 'warn');
      return;
    }

    setStatus('抓取 CWA 即時雨量中…', 'busy');
    try {
      const stations = await fetchStations(key);
      if (!stations.length) throw new Error('沒有取得任何雨量站資料，請確認金鑰是否正確');
      const nHi = computeAllLakes(stations);
      redrawEverything();
      setStatus(`✓ 已更新即時風險｜${stations.length} 個雨量站｜判高 ${nHi} 座｜${new Date().toLocaleTimeString('zh-TW')}`, 'ok');
    } catch (err) {
      console.error(err);
      setStatus(
        `✗ 抓取失敗：${err.message}。若持續失敗，可能是瀏覽器封鎖跨網域請求，` +
        '改用本機 Python 執行「python -m pipeline.build_all --live」。',
        'error'
      );
    }
  }

  function init() {
    const btn = document.getElementById('cwaFetchBtn');
    const input = document.getElementById('cwaKeyInput');
    if (!btn || !input) return;

    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        input.value = saved;
        const remember = document.getElementById('cwaKeyRemember');
        if (remember) remember.checked = true;
      }
    } catch (e) { /* localStorage 不可用就跳過，不影響手動輸入 */ }

    btn.addEventListener('click', updateLive);
    input.addEventListener('keydown', e => { if (e.key === 'Enter') updateLive(); });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
