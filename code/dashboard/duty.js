/* ════════════════════════════════════════
   值班佇列 · 事件研判
   資料由 data/events.js 提供（window.EVENT_SCENARIOS），
   由 pipeline/events/build.py 產生：逐期回放 SAR 偵測結果，
   每個時點只用當時已取得的影像。
   人工查證紀錄存在這台電腦的瀏覽器（localStorage），可匯出 JSON。
   ════════════════════════════════════════ */

'use strict';

const Duty = (() => {
  const SCENARIOS = window.EVENT_SCENARIOS || [];
  const STORE_KEY = 'ossint.verify.v1';

  const PRIORITY_GROUPS = [
    { key: 'high', title: '建議立即查證' },
    { key: 'medium', title: '建議人工確認' },
    { key: 'low', title: '暫時觀察' },
  ];
  const VERDICTS = {
    confirm: { text: '確認為堰塞湖', tag: '人工確認' },
    watch: { text: '持續觀察', tag: '人工：持續觀察' },
    exclude: { text: '排除（非堰塞湖）', tag: '人工排除' },
  };
  const EVIDENCE_MARK = { support: '✓', against: '✗', context: '·' };

  const st = { scenario: 0, snap: 0, eventId: null };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* ── 人工查證紀錄 ── */

  function loadStore() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch (e) { return {}; }
  }
  function saveStore(store) {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(store)); return true; } catch (e) { return false; }
  }
  let STORE = loadStore();

  const scen = () => SCENARIOS[st.scenario];
  const snap = () => scen().snapshots[st.snap];
  const storeKey = id => `${scen().id}:${id}`;

  /* 查證紀錄只在記錄當下及之後的時點生效，往前回放時看不到 */
  function verification(id) {
    const rec = STORE[storeKey(id)];
    return rec && st.snap >= rec.snapIndex ? rec : null;
  }

  /* 把人工查證疊到系統研判上：系統原本的判斷保留，只調整顯示 */
  function withHuman(ev) {
    const rec = verification(ev.id);
    if (!rec) return { ...ev, human: null };
    const out = { ...ev, human: rec, gaps: ev.gaps.filter(g => g.kind !== 'field') };
    if (rec.verdict === 'confirm') {
      out.confidence = '高';
      out.confidenceReasons = [`人工查證確認（${rec.who || '未署名'}）`, ...ev.confidenceReasons.slice(0, 1)];
    } else if (rec.verdict === 'exclude') {
      out.confidenceReasons = [`人工查證排除（${rec.who || '未署名'}）`, ...ev.confidenceReasons];
    }
    return out;
  }

  function events() {
    return snap().events.map(withHuman);
  }

  /* ── 回放時點 ── */

  function renderRail() {
    const rail = $('#snapRail');
    rail.innerHTML = scen().snapshots.map((s, i) => `
      <button class="snap ${i === st.snap ? 'is-on' : ''}" type="button" role="tab"
              aria-selected="${i === st.snap}" data-i="${i}">
        <span class="snap-time">${esc(s.label)}</span>
        <span class="snap-what">${esc(s.what)}</span>
        <span class="snap-since">${esc(s.since)}</span>
        <span class="snap-counts" aria-label="高 ${s.counts.high}、中 ${s.counts.medium}、低 ${s.counts.low}">
          <i class="c-high">${s.counts.high}</i><i class="c-medium">${s.counts.medium}</i><i class="c-low">${s.counts.low}</i>
        </span>
      </button>`).join('');
    $$('.snap', rail).forEach(b => b.addEventListener('click', () => setSnap(+b.dataset.i)));
  }

  function setSnap(i) {
    const n = scen().snapshots.length;
    st.snap = Math.max(0, Math.min(n - 1, i));
    const ids = snap().events.map(e => e.id);
    if (!ids.includes(st.eventId)) st.eventId = sortedEvents()[0] ? sortedEvents()[0].id : null;
    render();
  }

  /* ── 佇列 ── */

  function sortedEvents() {
    const order = { high: 0, medium: 1, low: 2 };
    return events().sort((a, b) => {
      const ax = a.human && a.human.verdict === 'exclude' ? 1 : 0;
      const bx = b.human && b.human.verdict === 'exclude' ? 1 : 0;
      return ax - bx || order[a.priority] - order[b.priority] || b.areaHectare - a.areaHectare;
    });
  }

  function queueItem(ev) {
    const tags = [];
    if (ev.isNew) tags.push('<span class="q-tag is-new">本期新增</span>');
    if (ev.human) tags.push(`<span class="q-tag is-human">${VERDICTS[ev.human.verdict].tag}</span>`);
    const dist = ev.distanceFromReferenceM != null ? ` · 距清冊壩址 ${ev.distanceFromReferenceM.toLocaleString()} m` : '';
    return `
      <button class="q-item p-${ev.priority} ${ev.id === st.eventId ? 'is-active' : ''}" type="button" data-id="${ev.id}">
        <span class="q-id">${ev.id}</span>
        <span class="q-main">
          <span class="q-action">${ev.action}<span class="q-pers">${ev.persistenceText}</span></span>
          <span class="q-meta">規模 ${ev.scale} · ${ev.areaHectare} 公頃${dist}</span>
        </span>
        <span class="q-tags">${tags.join('')}</span>
      </button>`;
  }

  function renderQueue() {
    const s = snap();
    const evs = sortedEvents();
    $('#queueTitle').textContent = `${s.label} 的事件佇列`;
    $('#queueNote').textContent = `${evs.length} 件 · 下一期 ${s.nextPass}`;

    const excluded = evs.filter(e => e.human && e.human.verdict === 'exclude');
    const active = evs.filter(e => !excluded.includes(e));
    let html = PRIORITY_GROUPS.map(g => {
      const list = active.filter(e => e.priority === g.key);
      if (!list.length) return '';
      return `
        <div class="q-group g-${g.key}">
          <div class="q-group-head"><span>${g.title}</span><b>${list.length}</b></div>
          ${list.map(queueItem).join('')}
        </div>`;
    }).join('');
    if (excluded.length) {
      html += `
        <div class="q-group g-excluded">
          <div class="q-group-head"><span>已人工排除</span><b>${excluded.length}</b></div>
          ${excluded.map(queueItem).join('')}
        </div>`;
    }
    $('#queue').innerHTML = html || '<p class="narr-empty q-empty">這個時點沒有偵測到疑似事件。</p>';
    $$('#queue .q-item').forEach(b => b.addEventListener('click', () => selectEvent(b.dataset.id)));
  }

  /* ── 窗格小地圖 ── */

  function renderMinimap() {
    const svg = $('#minimap');
    const sc = scen();
    const W = 400, half = sc.windowKm / 2;
    const pxPerKm = W / sc.windowKm;
    const [lon0, lat0] = sc.center;
    const kx = 111.32 * Math.cos(lat0 * Math.PI / 180), ky = 110.54;
    const xy = ([lon, lat]) => [W / 2 + (lon - lon0) * kx * pxPerKm, W / 2 - (lat - lat0) * ky * pxPerKm];
    const pts = poly => poly.map(p => xy(p).map(v => v.toFixed(1)).join(',')).join(' ');

    let g = '';
    for (let k = 1; k < sc.windowKm; k++) {
      const v = k * pxPerKm;
      g += `<line class="mm-grid" x1="${v}" y1="0" x2="${v}" y2="${W}"/><line class="mm-grid" x1="0" y1="${v}" x2="${W}" y2="${v}"/>`;
    }
    if (sc.reference) {
      const [rx, ry] = xy(sc.reference.lonLat);
      g += `<g class="mm-ref"><path d="M${rx - 6},${ry - 6}L${rx + 6},${ry + 6}M${rx + 6},${ry - 6}L${rx - 6},${ry + 6}"/>
            <text x="${rx + 12}" y="${ry - 2}">清冊壩址</text><text x="${rx + 12}" y="${ry + 11}">（事後登載）</text></g>`;
    }
    const evs = events();
    // 選取中的畫在最上層
    evs.sort((a, b) => (a.id === st.eventId) - (b.id === st.eventId));
    evs.forEach(ev => {
      const sel = ev.id === st.eventId ? ' is-sel' : '';
      const [cx, cy] = xy(ev.lonLat);
      const shape = ev.polygonLonLat.length >= 3
        ? `<polygon points="${pts(ev.polygonLonLat)}"/>` : '';
      g += `<g class="mm-ev p-${ev.priority}${sel}" data-id="${ev.id}" tabindex="0" role="button" aria-label="${ev.id} ${ev.action}">
              ${shape}<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="4"/>
              <text x="${(cx + 8).toFixed(1)}" y="${(cy + 4).toFixed(1)}">${ev.id}</text></g>`;
    });
    g += `<g class="mm-scale"><line x1="14" y1="${W - 16}" x2="${14 + pxPerKm}" y2="${W - 16}"/>
          <text x="14" y="${W - 22}">1 km</text></g>
          <text class="mm-north" x="${W - 16}" y="20" text-anchor="middle">N↑</text>`;
    svg.setAttribute('viewBox', `0 0 ${W} ${W}`);
    svg.innerHTML = g;
    $$('.mm-ev', svg).forEach(el => {
      el.addEventListener('click', () => selectEvent(el.dataset.id));
      el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectEvent(el.dataset.id); } });
    });
    $('#minimapNote').textContent =
      `${sc.windowKm} km 分析窗格 · 色塊為 SAR 新增水體（陡坡遮罩會擋掉部分湖面）· ±${half} km`;
  }

  /* ── 事件卡 ── */

  function readCell(label, value, sub, cls) {
    return `<div class="cell"><span class="label">${label}</span><div class="num ${cls || ''}">${value}</div>${sub ? `<div class="sub">${sub}</div>` : ''}</div>`;
  }

  function verifyForm(ev) {
    const rec = STORE[storeKey(ev.id)];
    const live = verification(ev.id);
    const hiddenNote = rec && !live
      ? `<p class="vf-note">此事件在 ${esc(scen().snapshots[rec.snapIndex].label)} 有查證紀錄，這個時點還看不到。</p>` : '';
    const saved = live ? `
      <div class="vf-saved">
        <b>${VERDICTS[live.verdict].text}</b>｜${esc(live.who || '未署名')}｜${esc(new Date(live.at).toLocaleString('zh-TW', { hour12: false }))}
        ${live.note ? `<p>${esc(live.note)}</p>` : ''}
        <span class="vf-at">記錄於回放時點 ${esc(scen().snapshots[live.snapIndex].label)}</span>
      </div>` : '';
    return `
      <div class="verify">
        <span class="at">人工查證</span>
        ${saved}${hiddenNote}
        <form class="vf" id="verifyForm">
          <div class="vf-verdicts" role="radiogroup" aria-label="查證結果">
            ${Object.entries(VERDICTS).map(([k, v]) => `
              <label><input type="radio" name="verdict" value="${k}" ${live && live.verdict === k ? 'checked' : ''}>${v.text}</label>`).join('')}
          </div>
          <div class="vf-row">
            <input class="vf-input" name="who" placeholder="查證人員" value="${esc(live ? live.who : '')}" autocomplete="off">
            <input class="vf-input vf-wide" name="note" placeholder="補充說明（例如：UAV 已確認壩體、光學影像可見湖面）" value="${esc(live ? live.note : '')}" autocomplete="off">
          </div>
          <div class="vf-actions">
            <button class="btn" type="submit">儲存查證紀錄</button>
            ${live ? '<button class="btn ghost" type="button" id="verifyClear">清除</button>' : ''}
            <button class="btn ghost" type="button" id="verifyExport">匯出全部查證紀錄</button>
          </div>
          <p class="vf-note">紀錄只存在這台電腦的瀏覽器。系統的研判不會被覆寫，只在旁邊註記人工結果。</p>
        </form>
      </div>`;
  }

  function taskSheet(ev) {
    const s = snap();
    return [
      `【${scen().name}】${ev.id}｜${ev.action}｜${ev.priorityText}`,
      `研判時點：${s.label}（${s.what}）`,
      `位置：${ev.lonLat[1].toFixed(5)}°N ${ev.lonLat[0].toFixed(5)}°E`,
      `摘要：${ev.summary}`,
      '建議任務：',
      ...ev.tasks.map((t, i) => `  ${i + 1}. ${t.label}——${t.reason}`),
      '證據缺口：',
      ...ev.gaps.map(g => `  - ${g.text}`),
    ].join('\n');
  }

  function renderCard() {
    const box = $('#evCard');
    const ev = events().find(e => e.id === st.eventId);
    if (!ev) { box.innerHTML = '<p class="narr-empty ev-empty">選一個事件查看證據與建議任務。</p>'; return; }

    const sc = scen();
    const where = [
      `${ev.lonLat[1].toFixed(5)}°N ${ev.lonLat[0].toFixed(5)}°E`,
      ev.lakeFloorM != null ? `湖底高程 ${ev.lakeFloorM} m` : null,
      ev.distanceFromReferenceM != null ? `距清冊壩址 ${ev.distanceFromReferenceM.toLocaleString()} m` : null,
    ].filter(Boolean).join(' · ');

    const badges = [
      `<span class="badge ev-pri p-${ev.priority}">${ev.priorityText}</span>`,
      `<span class="badge badge-status">${ev.persistenceText}</span>`,
      `<span class="badge badge-status">SAR 證據強度 ${ev.grade}</span>`,
      ev.isNew ? '<span class="badge badge-status">本期新增</span>' : '',
      ev.human ? `<span class="badge ev-human">${VERDICTS[ev.human.verdict].tag}</span>` : '',
    ].join('');

    const evidence = ev.evidence.map(e => `
      <li class="ev-${e.status}"><span class="mk" aria-hidden="true">${EVIDENCE_MARK[e.status]}</span>${esc(e.text)}</li>`).join('');
    const gaps = ev.gaps.map(g => `<li><span class="mk" aria-hidden="true">?</span>${esc(g.text)}</li>`).join('');

    const dets = ev.detections.map(d => {
      const re = d.recheck === 'pending'
        ? (d.recheckTime ? `待複核（${d.recheckTime}）` : '無複核期')
        : `${d.recheck === 'persistent' ? '持續' : '未持續'}（IoU ${d.iou != null ? d.iou.toFixed(2) : '—'}）`;
      const img = d.evidenceImage ? `<a href="../../${d.evidenceImage}" target="_blank" rel="noopener">證據圖</a>` : '—';
      return `<tr><td>${d.passTime}</td><td>${d.areaHectare}</td><td class="re-${d.recheck}">${re}</td><td>${img}</td></tr>`;
    }).join('');

    box.innerHTML = `
      <div class="detail-head">
        <div class="badges">${badges}</div>
        <h1>${ev.id} · 疑似堰塞湖事件</h1>
        <span class="where">${where}</span>
      </div>

      <div class="ev-summary p-${ev.priority}">${esc(ev.summary)}</div>

      <div class="decision-summary ev-readout">
        ${readCell('建議行動', ev.action, ev.priorityText, `t-${ev.priority}`)}
        ${readCell('規模（相對）', ev.scale, `SAR ${ev.areaHectare} 公頃，偏低，視為下限`)}
        ${readCell('研判信心', ev.confidence, ev.confidenceReasons[0])}
        ${readCell('首次出現', ev.firstSeen, `最近一次 ${ev.lastSeen}`)}
      </div>

      ${ev.conflicts.length ? `<div class="ev-conflict"><span class="at">證據衝突</span>${ev.conflicts.map(c => `<p>${esc(c)}</p>`).join('')}</div>` : ''}

      <div class="ev-cols">
        <div><span class="at">目前證據</span><ul class="ev-list">${evidence}</ul></div>
        <div><span class="at">證據缺口</span><ul class="ev-list ev-gaps">${gaps}</ul></div>
      </div>

      <div class="action-card">
        <span class="at">建議任務</span>
        <ol class="ev-tasks">${ev.tasks.map(t => `<li><b>${esc(t.label)}</b><span>${esc(t.reason)}</span></li>`).join('')}</ol>
        <button class="btn ghost ev-copy" type="button" id="taskCopy">複製任務單</button>
      </div>

      ${verifyForm(ev)}

      <div class="evidence-card">
        <div class="et">偵測紀錄（SAR 逐期）</div>
        <table class="ev-dets">
          <thead><tr><th>影像時間</th><th>面積（公頃）</th><th>複核</th><th></th></tr></thead>
          <tbody>${dets}</tbody>
        </table>
        <div class="limitation-note">研判信心：${ev.confidenceReasons.map(esc).join('；')}</div>
        <details class="narr-rules">
          <summary>命中規則（${ev.rulesFired.length} 條）</summary>
          <ul>${ev.rulesFired.map(r => `<li>${r}</li>`).join('')}</ul>
        </details>
        ${sc.reference ? `<button class="btn ghost ev-inv" type="button" id="toInventory">對照清冊：${esc(sc.reference.name)}（事後登載）</button>` : ''}
      </div>`;

    bindCard(ev);
  }

  function bindCard(ev) {
    const form = $('#verifyForm');
    form.addEventListener('submit', e => {
      e.preventDefault();
      const fd = new FormData(form);
      const verdict = fd.get('verdict');
      if (!verdict) { toast('請先選擇查證結果'); return; }
      STORE[storeKey(ev.id)] = {
        verdict, who: (fd.get('who') || '').trim(), note: (fd.get('note') || '').trim(),
        at: new Date().toISOString(), snapIndex: st.snap, snapshot: snap().label,
        systemPriority: ev.priority, systemAction: ev.action,
      };
      toast(saveStore(STORE) ? `已儲存 ${ev.id} 的查證紀錄` : '瀏覽器不允許儲存，紀錄只保留到關閉頁面');
      render();
    });
    const clear = $('#verifyClear');
    if (clear) clear.addEventListener('click', () => {
      delete STORE[storeKey(ev.id)];
      saveStore(STORE);
      render();
    });
    $('#verifyExport').addEventListener('click', exportRecords);
    $('#taskCopy').addEventListener('click', () => {
      const text = taskSheet(ev);
      const done = () => toast(`已複製 ${ev.id} 任務單`);
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, () => fallbackCopy(text, done));
      else fallbackCopy(text, done);
    });
    const inv = $('#toInventory');
    if (inv) inv.addEventListener('click', () => {
      // select() 在 app.js，會把頁面捲回頂端，所以捲動放在它之後
      if (typeof select === 'function') select(scen().reference.lakeId);
      setTimeout(() => $('.board').scrollIntoView({ behavior: 'smooth', block: 'start' }), 0);
    });
  }

  function fallbackCopy(text, done) {
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); done(); } catch (e) { toast('無法複製，請手動選取'); }
    ta.remove();
  }

  function exportRecords() {
    const blob = new Blob([JSON.stringify(STORE, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'verification-records.json';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    toast(`已匯出 ${Object.keys(STORE).length} 筆查證紀錄`);
  }

  function toast(msg) {
    if (typeof showToast === 'function') showToast(msg);
  }

  /* ── 組合 ── */

  function selectEvent(id) {
    st.eventId = id;
    renderQueue();
    renderMinimap();
    renderCard();
  }

  function renderScenarioTabs() {
    const box = $('#scenTabs');
    const kindText = { positive: '正案例', negative: '負案例' };
    const tabs = SCENARIOS.map((s, i) => `
      <button class="filter ${i === st.scenario ? 'is-on' : ''}" type="button" data-i="${i}">
        ${kindText[s.kind] || ''}｜${esc(s.name)}</button>`).join('');
    const pending = SCENARIOS.some(s => s.kind === 'negative') ? ''
      : '<span class="scen-pending">負案例（2026 汛期，同窗格同參數）尚未產生：見 scripts/gee_export_series_s1.js、run_sar_series.py</span>';
    box.innerHTML = `<div class="filters">${tabs}</div>${pending}`;
    $$('button', box).forEach(b => b.addEventListener('click', () => {
      st.scenario = +b.dataset.i;
      st.snap = defaultSnap(scen());
      st.eventId = sortedEvents()[0] ? sortedEvents()[0].id : null;
      render();
    }));
  }

  function render() {
    const sc = scen();
    $('#dutyTitle').textContent = sc.name;
    $('#dutyDesc').textContent = sc.description;
    renderScenarioTabs();
    renderRail();
    renderQueue();
    renderMinimap();
    renderCard();
  }

  /* 預設停在三種優先等級都有的第一個時點（最能看出排序），沒有就停在最後 */
  function defaultSnap(sc) {
    const i = sc.snapshots.findIndex(s => s.counts.high && s.counts.medium && s.counts.low);
    return i >= 0 ? i : sc.snapshots.length - 1;
  }

  function init() {
    const section = $('#duty');
    if (!section) return;
    if (!SCENARIOS.length) {
      section.querySelector('.duty-board').innerHTML =
        '<div class="empty"><b>沒有事件資料</b>請在 code/ 底下執行 python -m pipeline.events.build 產生 data/events.js。</div>';
      return;
    }
    st.snap = defaultSnap(scen());
    st.eventId = sortedEvents()[0] ? sortedEvents()[0].id : null;
    render();

    document.addEventListener('keydown', e => {
      if (!e.target.closest || !e.target.closest('#snapRail')) return;
      if (e.key === 'ArrowRight') { setSnap(st.snap + 1); $('#snapRail .snap.is-on').focus(); }
      if (e.key === 'ArrowLeft') { setSnap(st.snap - 1); $('#snapRail .snap.is-on').focus(); }
    });
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', Duty.init);
