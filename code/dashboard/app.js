/* ════════════════════════════════════════
   全台堰塞湖清冊 · 邏輯
   資料由 data/lakes.js 提供（window.BARRIER_LAKES）
   來源：農村水保署堰塞湖清冊，座標已轉為 WGS84
   ════════════════════════════════════════ */

'use strict';

const LAKES = (window.BARRIER_LAKES || []).slice();

/* risk.js 以湖名對應，71/75 筆有評估。沒有的顯示「尚無評估」，不要當成低風險。 */
const RISK = window.LAKE_RISK || {};
const RISK_META = window.RISK_MODEL_META || null;

// 真實 SAR 偵測範圍（目前只有 bl071），在 3D 地圖上畫出
const INUNDATION_DEMO = window.INUNDATION_DEMO || {};

LAKES.forEach(lake => {
  lake.risk = RISK[(lake.name || '').trim()] || null;
});

const STATUS_TEXT = { watch: '監測中', stable: '存在已穩定', gone: '已消失' };
const CAUSE_TEXT = { quake: '地震', typhoon: '颱風', rain: '降雨', slide: '崩塌', other: '未記載' };

const fmtProb = p => (p == null ? '—' : `${(p * 100).toFixed(0)}%`);

/* 風險模型不知道湖還在不在，用清冊現況修正：
     gone   → 不適用
     stable → 模型判高時下修一級（已形成穩定溢流道，模型未納入）
     watch  → 直接用模型結果 */
function riskView(lake) {
  const risk = lake.risk;
  if (lake.statusKey === 'gone') {
    return {
      level: 'na', text: '不適用',
      basis: '清冊登載為「已消失」，壩體已不存在；風險模型未區分現況存續，對已消失個案不具意義',
      instruction: '壩體已消失，無需採取行動。如發現清冊現況與實際不符，請通報更新清冊資料。',
    };
  }
  if (!risk) {
    return {
      level: 'none', text: '尚無評估', basis: '無風險模型評估資料',
      instruction: '目前無風險模型評估資料，請以清冊現況與官方公告為準，持續留意當地雨量與河川水位。',
    };
  }
  const stableInstruction = '已有穩定溢流道（風險模型未納入此資訊）。維持例行監測，暴雨期間留意上游雨量。';
  if (risk.risk_level === '高') {
    if (lake.statusKey === 'stable') {
      return {
        level: 'moderate', text: '中（下修）',
        basis: `risk_prob=${fmtProb(risk.risk_prob)}，模型判定為高風險，但清冊登載為「存在(已穩定)」` +
          '（已形成穩定溢流道），模型未納入此事實，下修一級',
        instruction: stableInstruction,
      };
    }
    return {
      level: 'high', text: '高', basis: `risk_prob=${fmtProb(risk.risk_prob)}，模型判定為高風險`,
      instruction: '留意最新降雨與官方公告，避免進入下游河道與低窪地區；現地如有異常湧水、水色混濁、水位快速上升，' +
        '立即遠離並通報；本結果來自統計模型批次推論，須配合現地觀察研判。',
    };
  }
  return {
    level: 'low', text: '低', basis: `risk_prob=${fmtProb(risk.risk_prob)}，模型判定為低風險`,
    instruction: lake.statusKey === 'stable' ? stableInstruction
      : '目前風險判定為低，維持例行監測即可，暴雨期間仍建議留意當地雨量與官方公告。',
  };
}

// 監測中且模型判高：KPI「高風險」與地圖上的高風險環
function isHighRiskWatch(lake) {
  return !!(lake && lake.statusKey === 'watch' && lake.risk && lake.risk.risk_level === '高');
}

function modelLimitation() {
  const n = RISK_META ? RISK_META.nPositives : null;
  const heldOut = RISK_META ? RISK_META.rocAuc : null;
  if (n != null && n < 30 && heldOut == null) {
    return `正樣本數僅 ${n} 筆，且無留出驗證（roc_auc 未提供），模型可信度尚待確認`;
  }
  return '模型樣本數與驗證方式見 RISK_MODEL_META';
}

function topDrivers(risk, n = 2) {
  if (!risk || !RISK_META || !RISK_META.featureImportance) return [];
  const FEATURE_TEXT = {
    volume: '既有蓄水量', rain_7d: '近 7 日累積雨量', rain_3d: '近 3 日累積雨量',
    rain_30d: '近 30 日累積雨量', rain_1d: '近 1 日雨量',
    shaking_30d: '近 30 日地動', quake_max_mag_30d: '近 30 日最大地震規模',
    quake_count_30d: '近 30 日地震次數',
    formed_by_quake: '地震誘發', formed_by_rain: '降雨誘發',
  };
  return Object.entries(RISK_META.featureImportance)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([k]) => FEATURE_TEXT[k] || k);
}

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const state = {
  selected: null,
  status: 'all',
  cause: 'all',
  year: null,
  risk: 'all',       // all / high / low / none
  county: 'all',
  keyword: ''
};

/* 供搜尋/篩選使用的風險分類，跟 riskBadgeInfo() 用同一套邏輯，
   避免兩處各自判斷造成不一致。 */
function riskCategory(lake) {
  if (!lake.risk) return 'none';
  return lake.risk.risk_level === '高' ? 'high' : 'low';
}


/* ── 1. 篩選 ───────────────────────────── */

function matches(lake) {
  if (state.status !== 'all' && lake.statusKey !== state.status) return false;
  if (state.cause !== 'all' && lake.causeKey !== state.cause) return false;
  if (state.year !== null && lake.year !== state.year) return false;
  if (state.risk !== 'all' && riskCategory(lake) !== state.risk) return false;
  if (state.county !== 'all' && lake.county !== state.county) return false;
  if (state.keyword) {
    const kw = state.keyword.trim().toLowerCase();
    if (kw) {
      const hay = `${lake.name} ${lake.county} ${lake.town} ${lake.village} ${lake.landmark || ''}`.toLowerCase();
      if (!hay.includes(kw)) return false;
    }
  }
  return true;
}

function visibleLakes() {
  return LAKES.filter(matches);
}


/* ── 2. 地圖（3D 立體地形，見 map3d.js）──── */


function initMap3D() {
  const wrap = $('#map3dWrap');
  const canvas = $('#map3dCanvas');
  const labels = $('#map3dLabels');
  const resetBtn = $('#map3dReset');

  if (typeof THREE === 'undefined' || typeof Map3D === 'undefined' || !window.TAIWAN_TERRAIN) {
    if (wrap) {
      wrap.innerHTML = '<p class="map3d-fallback">立體地形載入失敗，請確認 vendor/three.min.js 和 data/terrain.js 都在。</p>';
    }
    return;
  }

  Map3D.init(canvas, labels, resetBtn, {
    onSelect: id => select(id),
    onHoverStart: (id, coords) => { setPreview(id); showHoverCard(id, coords); },
    onHoverMove: (id, coords) => positionHoverCard(coords),
    onHoverEnd: id => { clearPreview(id); hideHoverCard(); },
  });
  Map3D.setLakes(LAKES);
  bindFullscreenToggle(wrap);
}

// Map3D 有 ResizeObserver，切換全螢幕不用手動 resize
function bindFullscreenToggle(wrap) {
  const btn = $('#map3dFullscreen');
  if (!btn || !wrap) return;

  btn.addEventListener('click', () => {
    if (document.fullscreenElement === wrap) {
      document.exitFullscreen();
    } else if (wrap.requestFullscreen) {
      wrap.requestFullscreen().catch(() => { });
    }
  });

  document.addEventListener('fullscreenchange', () => {
    const isFs = document.fullscreenElement === wrap;
    wrap.classList.toggle('is-fullscreen', isFs);
    btn.textContent = isFs ? '離開全螢幕' : '全螢幕';
    btn.setAttribute('aria-label', isFs ? '離開全螢幕' : '全螢幕檢視地圖');
  });
}

function hoverCardRiskText(lake) {
  if (lake.statusKey === 'gone') return '不適用';
  if (!lake.risk) return '尚無評估';
  return `${lake.risk.risk_level}風險 ${(lake.risk.risk_prob * 100).toFixed(0)}%`;
}

function showHoverCard(id, coords) {
  const card = $('#mapHoverCard');
  const lake = LAKES.find(l => l.id === id);
  if (!card || !lake) return;
  card.innerHTML = `
    <div class="hc-name">${lake.name}</div>
    <div class="hc-meta">${lake.county}${lake.town}</div>
    <div class="hc-meta">${STATUS_TEXT[lake.statusKey]}｜${hoverCardRiskText(lake)}</div>
    <div class="hc-meta">蓄水量（清冊）${lake.volume ? `${volumeScaleText(lake.volume)} · ${lake.volume.toLocaleString()} 萬 m³` : '—'}</div>`;
  positionHoverCard(coords);
  card.hidden = false;
}

function positionHoverCard(coords) {
  const card = $('#mapHoverCard');
  if (!card || !coords) return;
  card.style.left = `${coords.x + 16}px`;
  card.style.top = `${coords.y + 16}px`;
}

function hideHoverCard() {
  const card = $('#mapHoverCard');
  if (card) card.hidden = true;
}

function syncMarkers() {
  const visible = visibleLakes();
  const visibleIds = new Set(visible.map(l => l.id));
  const highRiskIds = new Set(LAKES.filter(isHighRiskWatch).map(l => l.id));

  // 只有真實 SAR 偵測多邊形（目前只有 bl071）才畫範圍；合成示範資料不畫
  const layer = INUNDATION_DEMO[state.selected];
  const area = (layer && layer.synthetic === false && (layer.polygonLonLat || []).length >= 3)
    ? { lakeId: state.selected, polygonLonLat: layer.polygonLonLat }
    : null;

  if (typeof Map3D !== 'undefined') {
    Map3D.sync({ selectedId: state.selected, visibleIds, highRiskIds, area });
  }

  $('[data-bind="mapCount"]').textContent = `顯示 ${visibleIds.size} / ${LAKES.length} 處`;
}


/* ── 4. 年度分布 ───────────────────────── */

const TL = { w: 1200, h: 260, padL: 40, padR: 20, padT: 30, padB: 46 };

function buildTimeline() {
  const years = LAKES.map(l => l.year).filter(Boolean);
  const y0 = Math.min(...years), y1 = Math.max(...years);
  const span = y1 - y0 + 1;

  const buckets = {};
  for (let y = y0; y <= y1; y++) buckets[y] = { watch: 0, stable: 0, gone: 0, events: {} };
  LAKES.forEach(l => {
    if (!l.year) return;
    buckets[l.year][l.statusKey]++;
    if (l.event) buckets[l.year].events[l.event] = (buckets[l.year].events[l.event] || 0) + 1;
  });

  const counts = Object.values(buckets).map(b => b.watch + b.stable + b.gone);
  const maxCount = Math.max(...counts);

  const plotW = TL.w - TL.padL - TL.padR;
  const plotH = TL.h - TL.padT - TL.padB;
  const slot = plotW / span;
  const barW = Math.max(6, slot * 0.62);
  const baseY = TL.padT + plotH;

  const xOf = y => TL.padL + (y - y0) * slot + (slot - barW) / 2;
  const hOf = n => (n / maxCount) * plotH;

  /* 標註最高的兩年 */
  const peaks = Object.entries(buckets)
    .map(([y, b]) => ({ year: +y, n: b.watch + b.stable + b.gone, b }))
    .sort((a, b) => b.n - a.n)
    .slice(0, 2)
    .filter(p => p.n >= 4);

  let svg = `<line class="tl-axis" x1="${TL.padL - 6}" y1="${baseY}" x2="${TL.w - TL.padR}" y2="${baseY}"/>`;

  for (let y = y0; y <= y1; y++) {
    const b = buckets[y];
    const n = b.watch + b.stable + b.gone;
    const x = xOf(y);
    let cursor = baseY;
    let segs = '';

    [['gone', b.gone], ['stable', b.stable], ['watch', b.watch]].forEach(([key, cnt]) => {
      if (!cnt) return;
      const h = hOf(cnt);
      cursor -= h;
      segs += `<rect class="seg-${key}" x="${x.toFixed(1)}" y="${cursor.toFixed(1)}" width="${barW.toFixed(1)}" height="${h.toFixed(1)}"/>`;
    });

    const dim = state.year !== null && state.year !== y;
    const on = state.year === y;

    svg += `
      <g class="tl-bar${dim ? ' is-dim' : ''}${on ? ' is-on' : ''}" data-year="${y}"
         tabindex="${n ? 0 : -1}" role="button" aria-label="${y} 年，${n} 處">
        <rect class="hit" x="${xOf(y).toFixed(1)}" y="${TL.padT}" width="${barW.toFixed(1)}" height="${plotH}"/>
        ${segs}
        ${n >= 4 ? `<text class="tl-count" x="${(x + barW / 2).toFixed(1)}" y="${(cursor - 6).toFixed(1)}" text-anchor="middle">${n}</text>` : ''}
      </g>`;

    if (y % 5 === 0 || y === y0 || y === y1) {
      svg += `<text class="tl-tick" x="${(x + barW / 2).toFixed(1)}" y="${baseY + 20}" text-anchor="middle">${y}</text>`;
    }
  }

  peaks.forEach((p, i) => {
    const topEvent = Object.entries(p.b.events).sort((a, b) => b[1] - a[1])[0];
    if (!topEvent) return;
    const x = xOf(p.year) + barW / 2;
    const labelY = TL.padT - 8 + i * 0;
    svg += `
      <line class="tl-anno-line" x1="${x.toFixed(1)}" y1="${baseY - hOf(p.n) - 22}" x2="${x.toFixed(1)}" y2="${labelY + 4}"/>
      <text class="tl-anno" x="${x.toFixed(1)}" y="${labelY}" text-anchor="${i === 0 ? 'start' : 'end'}">${topEvent[0]}</text>`;
  });

  $('#timeline').innerHTML = svg;

  $$('#timeline .tl-bar').forEach(el => {
    const y = +el.dataset.year;
    const toggle = () => { state.year = state.year === y ? null : y; refresh(); };
    el.addEventListener('click', toggle);
    el.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });
  });

  $('[data-bind="timelineNote"]').textContent = state.year
    ? `已選取 ${state.year} 年 · 再次點選取消`
    : `色塊由下而上為已消失、已穩定、監測中 · 高峰年多對應單一重大事件`;
}


/* ── 5. 清單 ───────────────────────────── */

function renderList() {
  const visible = visibleLakes();

  $('#lakeList').innerHTML = visible.map(lake => {
    const risk = riskBadgeInfo(lake);
    return `
    <button class="lake ${lake.id === state.selected ? 'is-active' : ''}" data-id="${lake.id}">
      <span class="yr">${lake.year || '—'}</span>
      <span>
        <span class="name">${lake.name}</span>
        <span class="meta">${lake.county}${lake.town} · ${CAUSE_TEXT[lake.causeKey]}${lake.event ? ' · ' + lake.event : ''}</span>
      </span>
      <span class="vol">
        <span class="num">${lake.volume ? lake.volume.toLocaleString() : '—'}</span><span class="u">萬 m³ 清冊</span>
      </span>
      <span class="pills">
        <span class="pill s-${lake.statusKey}">${STATUS_TEXT[lake.statusKey]}</span>
        <span class="pill risk-pill ${risk.cls}">${risk.text}</span>
      </span>
    </button>`;
  }).join('');

  $('#listEmpty').hidden = visible.length > 0;
  if (!visible.length) {
    $('#listEmpty').innerHTML = `
      <b>沒有符合條件的紀錄</b>
      目前套用了 ${activeFilterChips().length} 項篩選條件，放寬篩選條件或按「清除全部」再試一次。`;
  }

  renderActiveFilterChips();

  $('[data-bind="listCount"]').textContent = `${visible.length} 筆`;
}

function activeFilterChips() {
  const chips = [];
  if (state.status !== 'all') chips.push({ key: 'status', label: `存續：${STATUS_TEXT[state.status]}`, clear: () => { state.status = 'all'; } });
  if (state.cause !== 'all') chips.push({ key: 'cause', label: `誘因：${CAUSE_TEXT[state.cause]}`, clear: () => { state.cause = 'all'; } });
  if (state.year !== null) chips.push({ key: 'year', label: `${state.year} 年`, clear: () => { state.year = null; } });
  if (state.risk !== 'all') chips.push({ key: 'risk', label: `風險：${{ high: '高風險', low: '低風險', none: '尚無評估' }[state.risk]}`, clear: () => { state.risk = 'all'; } });
  if (state.county !== 'all') chips.push({ key: 'county', label: state.county, clear: () => { state.county = 'all'; } });
  if (state.keyword.trim()) chips.push({ key: 'keyword', label: `搜尋：${state.keyword.trim()}`, clear: () => { state.keyword = ''; const input = $('#searchInput'); if (input) input.value = ''; } });
  return chips;
}

function renderActiveFilterChips() {
  const box = $('#activeChips');
  if (!box) return;
  const chips = activeFilterChips();

  box.innerHTML = chips.map(c =>
    `<button class="chip" type="button" data-clear="${c.key}" aria-label="清除篩選：${c.label}">${c.label} ×</button>`
  ).join('');

  $$('#activeChips .chip').forEach((el, i) => {
    el.addEventListener('click', () => { chips[i].clear(); syncFilterControls(); refresh(); });
  });

  $('#resetBtn').hidden = chips.length === 0;
}

function syncFilterControls() {
  $$('.filter').forEach(b => {
    const kind = b.dataset.kind;
    if (kind && state[kind] !== undefined) b.classList.toggle('is-on', b.dataset.val === state[kind]);
  });
  const countySelect = $('#countySelect');
  if (countySelect) countySelect.value = state.county;
  const input = $('#searchInput');
  if (input) input.value = state.keyword;
}


/* ── 6. 詳情 ───────────────────────────── */

function renderDetail() {
  const lake = LAKES.find(l => l.id === state.selected);
  if (!lake) return;

  renderEventHeader(lake);
  renderReplayNote(lake);
  renderDecisionSummary(lake);
  renderConclusion(lake);
  renderActionCard(lake);
  renderEvidenceCard(lake);
  renderBasicFacts(lake);
}

/* 有事件回放的湖：提醒下方風險快照跟回放的事件期間不同時，避免兩邊結果被直接比較 */
function renderReplayNote(lake) {
  const box = $('#replayNote');
  if (!box) return;
  const scen = (window.EVENT_SCENARIOS || []).find(s => s.reference && s.reference.lakeId === lake.id);
  if (!scen) { box.hidden = true; return; }
  const snaps = scen.snapshots;
  const period = snaps.length ? `${snaps[0].label.split(' ')[0]}～${snaps[snaps.length - 1].label.split(' ')[0]}` : '';
  const riskDate = lake.risk ? fmtDateOnly(lake.risk.date) : null;
  box.hidden = false;
  box.innerHTML = `
    <b>此湖有事件回放：${scen.name}（${period}）</b>
    <span>${riskDate
      ? `下方風險為 ${riskDate} 的批次模型快照，跟事件回放的時間不同，兩者不能直接比較；事件期間的研判以值班佇列為準。`
      : '事件期間的研判以值班佇列為準。'}</span>
    <a href="#duty">回到值班佇列</a>`;
}

// 存續狀態和風險等級分開顯示
/* 跟 pipeline/attribution/verbalize.py 的 VOLUME_SCALES 一致（專案自訂，非官方分級） */
function volumeScaleText(wanM3) {
  if (wanM3 >= 5000) return '極大型';
  if (wanM3 >= 1000) return '大型';
  if (wanM3 >= 100) return '中型';
  return '小型';
}

function riskBadgeInfo(lake) {
  if (lake.statusKey === 'gone') return { text: '不適用', cls: 'is-na' };
  if (!lake.risk) return { text: '尚無評估', cls: 'is-none' };
  return lake.risk.risk_level === '高'
    ? { text: '高風險', cls: 'is-high' }
    : { text: '低風險', cls: 'is-low' };
}

function renderEventHeader(lake) {
  const set = (key, val) => {
    const el = $(`[data-bind="${key}"]`);
    if (el) el.textContent = val;
  };

  const statusBadge = $('[data-bind="statusBadge"]');
  statusBadge.className = `badge badge-status s-${lake.statusKey}`;
  statusBadge.textContent = lake.status || STATUS_TEXT[lake.statusKey];

  const risk = riskBadgeInfo(lake);
  const riskBadge = $('[data-bind="riskBadge"]');
  riskBadge.hidden = false;
  riskBadge.className = `badge badge-risk ${risk.cls}`;
  riskBadge.textContent = risk.text;

  set('name', lake.name);
  set('where', `${lake.county}${lake.town}${lake.village} · ${lake.lat.toFixed(4)}°N ${lake.lon.toFixed(4)}°E`);
}

function renderDecisionSummary(lake) {
  const box = $('#decisionSummary');
  if (!box) return;

  const rv = riskView(lake);
  const cell = (label, value, sub, danger) => `
    <div class="cell">
      <span class="label">${label}</span>
      <div class="num${danger ? ' risk-high' : ''}">${value}</div>
      ${sub ? `<div class="sub">${sub}</div>` : ''}
    </div>`;

  box.innerHTML = [
    cell('風險機率', lake.risk ? fmtProb(lake.risk.risk_prob) : '尚無評估', null, rv.level === 'high'),
    cell('現況修正後', rv.text, lake.risk ? `模型原判 ${lake.risk.risk_level}` : null, rv.level === 'high'),
    cell('存續狀態', STATUS_TEXT[lake.statusKey], '清冊登載'),
    cell('風險快照', lake.risk ? fmtDateOnly(lake.risk.date) : '—', '批次推論，非即時'),
  ].join('');
}

function conclusionHeadline(lake) {
  const rv = riskView(lake);
  if (rv.level === 'na') return '壩體已消失，無需處理。';
  if (rv.level === 'none') return '尚無風險模型評估，請以清冊現況與官方公告為準。';
  if (rv.level === 'high') return '高風險，建議短期內密切注意。';
  if (rv.level === 'moderate') return '風險經現況修正下修一級，維持例行觀察。';
  return '低風險，維持例行監控。';
}

function renderConclusion(lake) {
  const box = $('#conclusion');
  if (!box) return;

  const drivers = topDrivers(lake.risk);

  box.innerHTML = `
    <div class="line1">風險模型：${conclusionHeadline(lake)}</div>
    <div class="line2">主要依據：${drivers.length ? drivers.join('、') : '清冊登載之存續狀態'}</div>
    ${lake.risk ? `<div class="line3">限制：本結果為 ${fmtDateOnly(lake.risk.date)} 的批次模型推論，仍須配合現地觀測。</div>` : ''}`;
}

function splitInstruction(text) {
  return text.split(/[；。]/).map(s => s.trim()).filter(Boolean);
}

function renderActionCard(lake) {
  const box = $('#actionCard');
  if (!box) return;

  const steps = splitInstruction(riskView(lake).instruction);
  box.innerHTML = `
    <span class="at">建議行動</span>
    <ol>${steps.map(s => `<li>${s}</li>`).join('')}</ol>`;
}

function renderEvidenceCard(lake) {
  const box = $('#evidenceCard');
  if (!box) return;

  if (!lake.risk) {
    box.innerHTML = `
      <div class="et">風險模型依據</div>
      <p class="narr-empty">此筆紀錄尚無風險模型評估。</p>`;
    return;
  }

  const drivers = topDrivers(lake.risk);
  const rules = lake.rulesFired || [];

  box.innerHTML = `
    <div class="et">風險模型依據</div>
    <dl class="evidence-row">
      <dt>風險機率</dt><dd>${fmtProb(lake.risk.risk_prob)}</dd>
      <dt>原始模型分級</dt><dd>${lake.risk.risk_level}風險</dd>
      <dt>現況修正</dt><dd>${riskView(lake).basis}</dd>
      ${RISK_META && RISK_META.mode ? `
      <dt>資料來源</dt><dd>${RISK_META.mode}${lake.risk.nearest_station_km != null ? `｜距最近雨量站 ${lake.risk.nearest_station_km} km` : ''}</dd>` : ''}
    </dl>
    ${drivers.length ? `
      <span class="label" style="display:block;margin-bottom:6px">主要驅動因子</span>
      <ul class="evidence-list">${drivers.map(d => `<li>${d}</li>`).join('')}</ul>` : ''}
    <div class="limitation-note">模型限制：${modelLimitation()}</div>
    ${lake.narrative ? `
      <details class="narr-rules" style="margin-top:12px">
        <summary>成因敘述與命中規則${rules.length ? `（${rules.length} 條）` : ''}</summary>
        <p class="narr-text" style="margin:8px 0 0">${lake.narrative}</p>
        ${rules.length ? `<ul>${rules.map(r => `<li>${r}</li>`).join('')}</ul>` : ''}
      </details>` : ''}`;
}

function renderBasicFacts(lake) {
  const set = (key, val) => {
    const el = $(`[data-bind="${key}"]`);
    if (el) el.textContent = val;
  };

  set('volume', lake.volume ? lake.volume.toLocaleString() : '—');
  set('volumeNote', lake.volume
    ? `${volumeScaleText(lake.volume)}（專案自訂級距）· 清冊登載值，非本系統估算`
    : '清冊未登載或規模極小');

  set('year', lake.year || '—');
  set('formed', lake.formed ? `形成於 ${lake.formed}` : '形成日期未記載');

  /* 持續時間欄位混用日數與「持續至今」「<24HR」等文字 */
  const dur = (lake.duration || '').trim();
  const durNum = Number(dur);
  if (dur === '') {
    set('duration', '—'); set('durationUnit', ''); set('durationNote', '未記載');
  } else if (!Number.isNaN(durNum)) {
    set('duration', durNum.toLocaleString()); set('durationUnit', '日');
    set('durationNote', durNum >= 365 ? `約 ${(durNum / 365).toFixed(1)} 年` : '自形成至潰決或穩定');
  } else {
    set('duration', dur); set('durationUnit', ''); set('durationNote', '清冊原始登載');
  }

  const rows = [
    ['誘因', lake.cause || '未記載', !lake.cause],
    ['觸發事件', lake.event || '未記載', !lake.event],
    ['地標', lake.landmark || '未記載', !lake.landmark],
    ['坐落區位', lake.setting || '未記載', !lake.setting],
    ['潰決時間', lake.breachDate
      ? `${lake.breachDate}${lake.statusKey === 'watch' ? '（清冊存續狀態仍登載「監測中」，依清冊原文）' : ''}`
      : '無紀錄', !lake.breachDate],
    ['潰決原因', lake.breachCause || '無紀錄', !lake.breachCause],
    ['清冊項次', `#${lake.seq}`, false, true]
  ];

  $('#facts').innerHTML = rows.map(([k, v, muted, mono]) =>
    `<dt>${k}</dt><dd class="${muted ? 'muted' : ''}${mono ? ' mono' : ''}">${v}</dd>`
  ).join('');
}


function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  toast.setAttribute('role', 'status');
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('is-visible'));
  setTimeout(() => {
    toast.classList.remove('is-visible');
    setTimeout(() => toast.remove(), 220);
  }, 2500);
}


/* ── 7. 統計 ───────────────────────────── */

function renderStats() {
  const by = key => LAKES.filter(l => l.statusKey === key).length;

  const countHighRisk = LAKES.filter(isHighRiskWatch).length;
  const countUnassessed = LAKES.filter(l => l.risk === null).length;

  // 取最新一筆快照日期
  const snapshotDates = LAKES.map(l => l.risk && l.risk.date).filter(Boolean).sort();
  const riskSnapshotDate = snapshotDates.length
    ? fmtDateOnly(snapshotDates[snapshotDates.length - 1])
    : '—';

  $('[data-bind="countAll"]').textContent = `${LAKES.length}`;
  $('[data-bind="countWatch"]').textContent = `${by('watch')} 處`;
  $('[data-bind="countHighRisk"]').textContent = `${countHighRisk} 處`;
  $('[data-bind="countUnassessed"]').textContent = `${countUnassessed} 處`;
  $('[data-bind="countStableOrGone"]').textContent = `${by('stable') + by('gone')} 處`;
  $('[data-bind="riskSnapshotDate"]').textContent = riskSnapshotDate;

  const riskSourceEl = $('[data-bind="riskSource"]');
  if (riskSourceEl) {
    riskSourceEl.textContent = (RISK_META && RISK_META.mode) || '農村水保署／ERA5-Land';
  }
}

function fmtDateOnly(dateStr) {
  if (!dateStr) return '—';
  const [y, m, d] = dateStr.split('-');
  return `${y}/${m}/${d}`;
}


/* ── 8. 互動 ───────────────────────────── */

function select(id) {
  state.selected = id;
  syncMarkers();
  $$('#lakeList .lake').forEach(b => b.classList.toggle('is-active', b.dataset.id === id));
  renderDetail();
  const panel = $('.detail-panel');
  if (panel) panel.scrollTop = 0;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function setPreview(id) {
  if (!id || id === state.selected) return;
  $$(`.lake[data-id="${id}"]`).forEach(l => l.classList.add('is-preview'));
  if (typeof Map3D !== 'undefined') Map3D.hoverMarker(id);
}
function clearPreview(id) {
  if (!id) return;
  $$(`.lake[data-id="${id}"]`).forEach(l => l.classList.remove('is-preview'));
  if (typeof Map3D !== 'undefined') Map3D.unhoverMarker(id);
}

function bindListInteractions() {
  const list = $('#lakeList');
  if (!list) return;
  list.addEventListener('click', e => {
    const btn = e.target.closest('.lake');
    if (btn) select(btn.dataset.id);
  });
  list.addEventListener('mouseover', e => {
    const btn = e.target.closest('.lake');
    if (btn) setPreview(btn.dataset.id);
  });
  list.addEventListener('mouseout', e => {
    const btn = e.target.closest('.lake');
    if (btn) clearPreview(btn.dataset.id);
  });
}

function refresh() {
  syncMarkers();
  buildTimeline();
  renderList();

  /* 若目前選取的紀錄被篩掉，改選第一筆可見紀錄 */
  const visible = visibleLakes();
  if (visible.length && !visible.some(l => l.id === state.selected)) {
    select(visible[0].id);
  }
}

function bindLayerControls() {
  const map = {
    layerPoints: 'points',
    layerHighRisk: 'highRisk',
    layerArea: 'area',
    layerLabels: 'labels',
  };
  Object.entries(map).forEach(([elId, layerKey]) => {
    const el = $(`#${elId}`);
    if (!el) return;
    el.addEventListener('change', () => {
      if (typeof Map3D !== 'undefined') Map3D.setLayers({ [layerKey]: el.checked });
    });
  });
}

function populateCountyOptions() {
  const select = $('#countySelect');
  if (!select) return;
  const counties = [...new Set(LAKES.map(l => l.county))].sort((a, b) => a.localeCompare(b, 'zh-Hant'));
  select.innerHTML = '<option value="all">全部縣市</option>' +
    counties.map(c => `<option value="${c}">${c}</option>`).join('');
}

function bindFilters() {
  $$('.filter').forEach(btn => {
    btn.addEventListener('click', () => {
      const { kind, val } = btn.dataset;
      state[kind] = val;
      $$(`.filter[data-kind="${kind}"]`).forEach(b =>
        b.classList.toggle('is-on', b.dataset.val === val));
      refresh();
    });
  });

  const countySelect = $('#countySelect');
  if (countySelect) {
    countySelect.addEventListener('change', () => {
      state.county = countySelect.value;
      refresh();
    });
  }

  const searchInput = $('#searchInput');
  if (searchInput) {
    let debounceTimer = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        state.keyword = searchInput.value;
        refresh();
      }, 250);
    });
  }

  $('#resetBtn').addEventListener('click', () => {
    state.status = 'all'; state.cause = 'all'; state.year = null;
    state.risk = 'all'; state.county = 'all'; state.keyword = '';
    $$('.filter').forEach(b => b.classList.toggle('is-on', b.dataset.val === 'all'));
    syncFilterControls();
    refresh();
  });
}


/* ── 9. 啟動 ───────────────────────────── */

function init() {
  if (!LAKES.length) {
    $('#lakeList').innerHTML =
      '<div class="empty"><b>找不到清冊資料</b>請確認 data/lakes.js 已產生，' +
      '或在 code/ 底下執行 python -m pipeline.build_all。</div>';
    return;
  }

  initMap3D();
  renderStats();
  bindFilters();
  bindLayerControls();
  populateCountyOptions();
  bindListInteractions();

  /* 預設選最近一筆監測中的紀錄，沒有就選第一筆 */
  const first = LAKES.find(l => l.statusKey === 'watch') || LAKES[0];
  state.selected = first.id;

  refresh();
  renderDetail();
}

document.addEventListener('DOMContentLoaded', init);