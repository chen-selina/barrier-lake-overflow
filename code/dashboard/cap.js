/* cap.js — 把 risk.js 的風險結果轉成 CAP 1.2 (CAP-TWP) 欄位與 XML。

   不做新的風險判斷，每個欄位的依據都放進 <parameter>。
   status 固定 Test，正式上線前要人工改。
   certainty 最高 Possible：正樣本 12 筆，沒有留出驗證。
   area：有真實偵測多邊形（inundation.js 中 synthetic:false）才用 <polygon>，
   其餘用壩址圓形。 */

'use strict';

const CAP = (() => {

  const CAP_TWP_CODE = 'CAP-TWP:1.0';
  const DEFAULT_CIRCLE_RADIUS_KM = 3;

  // ── 門檻（唯一該調整風險分級的地方）───────────

  /* 模型不知道湖還在不在，用清冊 statusKey 修正：
       gone   → urgency=Past，severity 不採用模型值
       stable → 模型判高時下修一級（Severe → Moderate）
       watch  → 直接用模型結果 */

  function severityFromRisk(risk, lake) {
    if (lake && lake.statusKey === 'gone') {
      return {
        value: 'Unknown',
        basis: '清冊登載為「已消失」（壩體已不存在），風險模型未區分現況存續，此欄位對已消失個案不具意義',
      };
    }
    if (!risk) return { value: 'Unknown', basis: '無風險模型評估資料' };

    if (risk.risk_level === '高') {
      if (lake && lake.statusKey === 'stable') {
        return {
          value: 'Moderate',
          basis: `risk_prob=${fmtProb(risk.risk_prob)}，模型判定為高風險，` +
                 '但清冊登載為「存在(已穩定)」（已形成穩定溢流道），模型未納入此事實，下修一級',
        };
      }
      return { value: 'Severe', basis: `risk_prob=${fmtProb(risk.risk_prob)}，模型判定為高風險` };
    }
    if (risk.risk_level === '低') {
      return { value: 'Minor', basis: `risk_prob=${fmtProb(risk.risk_prob)}，模型判定為低風險` };
    }
    return { value: 'Unknown', basis: 'risk_level 欄位為空或無法辨識' };
  }

  // 批次快照不是即時觀測，不給 Immediate
  function urgencyFromRisk(risk, lake) {
    if (lake && lake.statusKey === 'gone') {
      return { value: 'Past', basis: '壩體已消失，已無應變必要（CAP「Past」原意即為此）' };
    }
    if (!risk) return { value: 'Unknown', basis: '無風險模型評估資料' };
    if (risk.risk_level === '高') {
      return { value: 'Expected', basis: '批次風險評估判定為高風險，應於短期內密切注意（非即時觀測，不判為 Immediate）' };
    }
    return { value: 'Future', basis: '目前風險判定為低，僅列入例行監控' };
  }

  function certaintyFromModel(meta) {
    const n = meta ? meta.nPositives : null;
    const heldOut = meta ? meta.rocAuc : null;
    if (n != null && n < 30 && heldOut == null) {
      return {
        value: 'Possible',
        basis: `正樣本數僅 ${n} 筆，且無留出驗證（roc_auc 未提供），模型可信度尚待確認`,
      };
    }
    return { value: 'Likely', basis: '模型樣本數與驗證方式已達可接受水準' };
  }

  function fmtProb(p) {
    return (p == null) ? '—' : (p * 100).toFixed(0) + '%';
  }

  // ── 敘述 ──────────────────────────────────

  function topDrivers(risk, meta, n = 2) {
    if (!risk || !meta || !meta.featureImportance) return [];
    const FEATURE_TEXT = {
      volume: '既有蓄水量', rain_7d: '近 7 日累積雨量', rain_3d: '近 3 日累積雨量',
      rain_30d: '近 30 日累積雨量', rain_1d: '近 1 日雨量',
      shaking_30d: '近 30 日地動', quake_max_mag_30d: '近 30 日最大地震規模',
      quake_count_30d: '近 30 日地震次數',
      formed_by_quake: '地震誘發', formed_by_rain: '降雨誘發',
    };
    return Object.entries(meta.featureImportance)
      .filter(([, v]) => v > 0)
      .sort((a, b) => b[1] - a[1])
      .slice(0, n)
      .map(([k]) => FEATURE_TEXT[k] || k);
  }

  function headline(lake, risk) {
    if (lake && lake.statusKey === 'gone') {
      return `${lake.name}：已消失，無需示警（風險模型未納入現況存續）`;
    }
    if (!risk) return `${lake.name}：無風險模型評估`;
    return `${lake.name}堰塞湖風險示警 — ${risk.risk_level}風險（risk_prob ${fmtProb(risk.risk_prob)}）`;
  }

  function description(lake, risk, meta) {
    if (lake && lake.statusKey === 'gone') {
      return `${lake.name}清冊登載為「已消失」，壩體已不存在。風險模型僅依雨量與登載蓄水量特徵計算，` +
        `並未判斷湖體現況是否仍存在，其原始輸出${risk ? `（risk_prob ${fmtProb(risk.risk_prob)}，${risk.risk_level}風險）` : ''}` +
        `對本案不具意義，故不發布示警。`;
    }
    if (!risk) return `${lake.name}目前無風險模型評估資料，無法產生示警內容。`;

    const drivers = topDrivers(risk, meta);
    const driverText = drivers.length ? `，主要驅動特徵為${drivers.join('、')}` : '';
    const stableNote = (lake && lake.statusKey === 'stable')
      ? '清冊登載為「存在(已穩定)」（已形成穩定溢流道），模型未納入此事實，故已將嚴重度下修一級。'
      : '';
    return `依 ERA5-Land 降雨再分析資料與邏輯迴歸風險模型（快照日期 ${risk.date}）評估，` +
      `${lake.name}目前風險機率為 ${fmtProb(risk.risk_prob)}，模型原始判定為「${risk.risk_level}風險」${driverText}。${stableNote}` +
      `本評估屬統計模型推論，非現地實測確認，正樣本數少（${meta ? meta.nPositives : '—'} 筆），` +
      `請配合現地觀測與官方公告研判，不應單獨作為疏散決策依據。`;
  }

  // 只有監測中且模型判高才上示警橫幅
  function shouldAlert(lake) {
    return !!(lake && lake.statusKey === 'watch' && lake.risk && lake.risk.risk_level === '高');
  }

  // effective = 快照日期，expires = +1 天（下次批次會取代）
  function effectiveWindow(risk) {
    const base = (risk && risk.date) ? new Date(`${risk.date}T00:00:00+08:00`) : new Date();
    const effective = base.toISOString();
    const expires = new Date(base.getTime() + 24 * 3600 * 1000).toISOString();
    return { effective, expires };
  }

  function instructionFor(lake, risk, severity, urgency) {
    if (lake && lake.statusKey === 'gone') {
      return '壩體已消失，無需採取行動。如發現清冊現況與實際不符，請通報更新清冊資料。';
    }
    if (!risk) {
      return '目前無風險模型評估資料，請以清冊現況與官方公告為準，持續留意當地雨量與河川水位。';
    }
    if (lake && lake.statusKey === 'stable') {
      return '已有穩定溢流道（風險模型未納入此資訊）。維持例行監測，暴雨期間留意上游雨量。';
    }
    if (severity.value === 'Severe') {
      return '留意最新降雨與官方公告，避免進入下游河道與低窪地區；現地如有異常湧水、水色混濁、水位快速上升，立即遠離並通報；本示警來自統計模型批次結果，須配合現地觀察研判。';
    }
    return '目前風險判定為低，維持例行監測即可，暴雨期間仍建議留意當地雨量與官方公告。';
  }

  // CAP <polygon> 是 "lat,lon lat,lon ..."，內部資料是 [lon, lat]。
  // 合成示範資料不能進 CAP，只接受 synthetic === false。
  function buildArea(lake, inundation) {
    const areaDesc = `${lake.county}${lake.town}${lake.village}`;
    const hasRealPolygon = inundation && inundation.synthetic === false &&
      Array.isArray(inundation.polygonLonLat) && inundation.polygonLonLat.length >= 3;

    if (hasRealPolygon) {
      const polygon = inundation.polygonLonLat
        .map(([lon, lat]) => `${lat},${lon}`)
        .join(' ');
      return { areaDesc, circle: null, polygon };
    }

    return {
      areaDesc,
      circle: (lake.lat != null && lake.lon != null)
        ? `${lake.lat},${lake.lon} ${DEFAULT_CIRCLE_RADIUS_KM}`
        : null,
      polygon: null,
    };
  }

  // ── 組裝 CAP 物件（供 UI 與 XML 共用）──────────

  function build(lake, risk, meta, opts = {}) {
    const severity = severityFromRisk(risk, lake);
    const urgency = urgencyFromRisk(risk, lake);
    const certainty = certaintyFromModel(meta);
    const { effective, expires } = effectiveWindow(risk);

    return {
      identifier: opts.identifier || `ossint-${lake.id}-${risk ? risk.date : 'na'}`,
      sender: opts.sender || 'ossint2026-demo@example.org',
      sent: new Date().toISOString(),
      status: 'Test',       // demo 階段固定值，正式上線前必須人工確認並改掉
      msgType: 'Alert',
      scope: 'Public',
      code: CAP_TWP_CODE,
      info: {
        language: 'zh-TW',
        category: 'Geo',
        event: '堰塞湖溢流風險示警',
        responseType: (lake && lake.statusKey === 'gone')
          ? 'AllClear'
          : (risk && risk.risk_level === '高' ? 'Monitor' : 'None'),
        urgency, severity, certainty,
        senderName: 'OSSInt 2026 堰塞湖快速評估系統（Demo）',
        headline: headline(lake, risk),
        description: description(lake, risk, meta),
        instruction: instructionFor(lake, risk, severity, urgency),
        effective, expires,
        area: buildArea(lake, opts.inundation),
        parameters: buildParameters(lake, risk, meta, severity, urgency, certainty),
      },
    };
  }

  function buildParameters(lake, risk, meta, severity, urgency, certainty) {
    const params = [
      { valueName: 'severity_basis', value: severity.basis },
      { valueName: 'urgency_basis', value: urgency.basis },
      { valueName: 'certainty_basis', value: certainty.basis },
    ];
    if (risk) {
      params.push({ valueName: 'risk_prob', value: String(risk.risk_prob) });
      params.push({ valueName: 'risk_snapshot_date', value: risk.date });
      params.push({ valueName: 'model', value: meta ? meta.model : '' });
    }
    return params;
  }

  // ── XML 輸出 ──────────────────────────────

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function toXML(alert) {
    const info = alert.info;
    const params = info.parameters.map(p =>
      `    <parameter><valueName>${esc(p.valueName)}</valueName><value>${esc(p.value)}</value></parameter>`
    ).join('\n');

    const areaLines = [
      `    <areaDesc>${esc(info.area.areaDesc)}</areaDesc>`,
      info.area.polygon ? `    <polygon>${esc(info.area.polygon)}</polygon>` : '',
      info.area.circle ? `    <circle>${esc(info.area.circle)}</circle>` : '',
    ].filter(Boolean).join('\n');

    return `<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>${esc(alert.identifier)}</identifier>
  <sender>${esc(alert.sender)}</sender>
  <sent>${esc(alert.sent)}</sent>
  <status>${esc(alert.status)}</status>
  <msgType>${esc(alert.msgType)}</msgType>
  <scope>${esc(alert.scope)}</scope>
  <code>${esc(alert.code)}</code>
  <info>
    <language>${esc(info.language)}</language>
    <category>${esc(info.category)}</category>
    <event>${esc(info.event)}</event>
    <responseType>${esc(info.responseType)}</responseType>
    <urgency>${esc(info.urgency.value)}</urgency>
    <severity>${esc(info.severity.value)}</severity>
    <certainty>${esc(info.certainty.value)}</certainty>
    <senderName>${esc(info.senderName)}</senderName>
    <headline>${esc(info.headline)}</headline>
    <description>${esc(info.description)}</description>
    <instruction>${esc(info.instruction)}</instruction>
    <effective>${esc(info.effective)}</effective>
    <expires>${esc(info.expires)}</expires>
${params}
  <area>
${areaLines}
  </area>
  </info>
</alert>
`;
  }

  return { build, toXML, severityFromRisk, urgencyFromRisk, certaintyFromModel, topDrivers, shouldAlert };
})();
