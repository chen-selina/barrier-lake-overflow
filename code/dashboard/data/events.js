/* 由 pipeline/events/build.py 產生，請勿手動編輯。
   每個情境逐期回放：某時點只用當時已取得的影像，不含未來的複核結果。 */
window.EVENT_SCENARIOS = [
 {
  "id": "matai_an_2025",
  "name": "馬太鞍溪 · 2025 薇帕颱風",
  "kind": "positive",
  "description": "壩址周圍 4 km 窗格，Sentinel-1 降軌 105 逐期回放。湖於 2025-07-21 17:54 形成，2025-09-23 溢流潰決。",
  "center": [
   121.29752,
   23.70061
  ],
  "windowKm": 4.0,
  "reference": {
   "lakeId": "bl071",
   "name": "花蓮馬太鞍溪",
   "lonLat": [
    121.29752,
    23.70061
   ],
   "label": "清冊壩址（事後登載，僅供對照）"
  },
  "trigger": {
   "label": "薇帕颱風外圍環流",
   "time": "2025-07-21T17:54:00+08:00",
   "source": "observations.csv（bl071）"
  },
  "snapshots": [
   {
    "asOf": "2025-07-22T21:52:00+00:00",
    "label": "7/23 05:52",
    "what": "新一期 SAR 全幅偵測",
    "since": "距觸發約 36 小時",
    "nextPass": "7/29",
    "counts": {
     "high": 0,
     "medium": 2,
     "low": 0
    },
    "newCount": 2,
    "events": [
     {
      "id": "E1",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": true,
      "lonLat": [
       121.302402,
       23.709417
      ],
      "distanceFromReferenceM": 1093,
      "areaHectare": 2.76,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1113.0,
      "polygonLonLat": [
       [
        121.30211792898294,
        23.709414956823352
       ],
       [
        121.30238742356818,
        23.70986411446541
       ],
       [
        121.30301624426707,
        23.709684451408588
       ],
       [
        121.30274674968183,
        23.709145462238116
       ],
       [
        121.30166877134089,
        23.709504788351765
       ],
       [
        121.30157893981247,
        23.708516641539234
       ],
       [
        121.30068062452835,
        23.708696304596057
       ],
       [
        121.30139927675565,
        23.709145462238116
       ],
       [
        121.30121961369882,
        23.70986411446541
       ],
       [
        121.30220776051135,
        23.710133609050647
       ],
       [
        121.30211792898294,
        23.709414956823352
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 2.76,
        "recheck": "pending",
        "recheckTime": "7/29 05:51",
        "iou": null,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 2.76 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 130.07 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1113 m）附近或以下，研判土石堵塞下游河道"
        ]
       }
      ],
      "priority": "medium",
      "priorityText": "中優先",
      "action": "建議人工確認",
      "confidence": "低",
      "confidenceReasons": [
       "只有單期 SAR，尚未複核"
      ],
      "persistence": "pending",
      "persistenceText": "待複核",
      "grade": "B",
      "scale": "中",
      "summary": "E1 需要人工確認：單期 SAR 出現約 2.8 公頃的疑似新增水體，空間條件符合，但尚未複核；建議 7/29 下一期過境複核，暫不派遣 UAV。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 2.76 公頃（證據強度 B 級）"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 130.1 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1113 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.9 km）、2024 花蓮萬里溪（7.7 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "persistence",
        "text": "尚未複核：單期影像無法排除陰影或濕土誤判（下一期 7/29）"
       },
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [],
      "tasks": [
       {
        "label": "值班人員判讀 SAR 證據圖",
        "reason": "確認暗區是否在河谷底、是否為崩塌坡面陰影"
       },
       {
        "label": "排下一期 SAR 複核（7/29）",
        "reason": "A 級需要兩期一致；單期出現的暗區多數會在複核時消失"
       },
       {
        "label": "調閱光學影像（雲況許可時）",
        "reason": "SAR 以外的獨立證據"
       },
       {
        "label": "暫不派遣 UAV",
        "reason": "目前只有單期 SAR，先以複核過濾誤報，避免浪費現地人力"
       },
       {
        "label": "補查形成期間雨量",
        "reason": "確認觸發條件；目前觀測表此欄空白"
       }
      ],
      "rulesFired": [
       "persistence.pending",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "priority.medium.pending"
      ]
     },
     {
      "id": "E2",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": true,
      "lonLat": [
       121.307454,
       23.709175
      ],
      "distanceFromReferenceM": 1386,
      "areaHectare": 1.43,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1212.0,
      "polygonLonLat": [
       [
        121.30750782068766,
        23.708516641539234
       ],
       [
        121.30732815763083,
        23.707887820840348
       ],
       [
        121.30651967387513,
        23.708247146953997
       ],
       [
        121.3070586630456,
        23.708336978482407
       ],
       [
        121.3070586630456,
        23.70878613612447
       ],
       [
        121.30750782068766,
        23.708516641539234
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 1.43,
        "recheck": "pending",
        "recheckTime": "7/29 05:51",
        "iou": null,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 1.43 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 117.66 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1212 m）附近或以下，研判土石堵塞下游河道"
        ]
       }
      ],
      "priority": "medium",
      "priorityText": "中優先",
      "action": "建議人工確認",
      "confidence": "低",
      "confidenceReasons": [
       "只有單期 SAR，尚未複核"
      ],
      "persistence": "pending",
      "persistenceText": "待複核",
      "grade": "B",
      "scale": "中",
      "summary": "E2 需要人工確認：單期 SAR 出現約 1.4 公頃的疑似新增水體，空間條件符合，但尚未複核；建議 7/29 下一期過境複核，暫不派遣 UAV。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 1.43 公頃（證據強度 B 級）"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 117.7 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1212 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.5 km）、2024 花蓮萬里溪（7.8 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "persistence",
        "text": "尚未複核：單期影像無法排除陰影或濕土誤判（下一期 7/29）"
       },
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [],
      "tasks": [
       {
        "label": "值班人員判讀 SAR 證據圖",
        "reason": "確認暗區是否在河谷底、是否為崩塌坡面陰影"
       },
       {
        "label": "排下一期 SAR 複核（7/29）",
        "reason": "A 級需要兩期一致；單期出現的暗區多數會在複核時消失"
       },
       {
        "label": "調閱光學影像（雲況許可時）",
        "reason": "SAR 以外的獨立證據"
       },
       {
        "label": "暫不派遣 UAV",
        "reason": "目前只有單期 SAR，先以複核過濾誤報，避免浪費現地人力"
       },
       {
        "label": "補查形成期間雨量",
        "reason": "確認觸發條件；目前觀測表此欄空白"
       }
      ],
      "rulesFired": [
       "persistence.pending",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "priority.medium.pending"
      ]
     }
    ]
   },
   {
    "asOf": "2025-07-28T21:51:00+00:00",
    "label": "7/29 05:51",
    "what": "新一期 SAR 全幅偵測＋複核 7/23 的候選",
    "since": "距觸發約 7 天",
    "nextPass": "8/4",
    "counts": {
     "high": 1,
     "medium": 0,
     "low": 2
    },
    "newCount": 1,
    "events": [
     {
      "id": "E3",
      "firstSeen": "7/29 05:51",
      "lastSeen": "7/29 05:51",
      "isNew": true,
      "lonLat": [
       121.293466,
       23.698155
      ],
      "distanceFromReferenceM": 494,
      "areaHectare": 5.78,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 882.0,
      "polygonLonLat": [
       [
        121.29187713474398,
        23.697108037430915
       ],
       [
        121.29304494461334,
        23.69782668965821
       ],
       [
        121.29286528155652,
        23.69827584730027
       ],
       [
        121.29538056435204,
        23.6992639941128
       ],
       [
        121.29645854269299,
        23.70115045620945
       ],
       [
        121.29717719492028,
        23.70070129856739
       ],
       [
        121.29681786880664,
        23.700252140925333
       ],
       [
        121.29636871116458,
        23.70052163551057
       ],
       [
        121.2965483742214,
        23.699443657169624
       ],
       [
        121.29600938505094,
        23.699443657169624
       ],
       [
        121.29591955352252,
        23.698994499527565
       ],
       [
        121.29322460767015,
        23.69827584730027
       ],
       [
        121.29313477614176,
        23.697736858129797
       ],
       [
        121.29250595544286,
        23.696569048260443
       ],
       [
        121.29106865098828,
        23.69638938520362
       ],
       [
        121.29097881945987,
        23.695850396033148
       ],
       [
        121.29026016723256,
        23.69558090144791
       ],
       [
        121.28909235736322,
        23.695850396033148
       ],
       [
        121.29079915640304,
        23.696299553675207
       ],
       [
        121.29160764015874,
        23.69737753201615
       ],
       [
        121.29187713474398,
        23.697108037430915
       ]
      ],
      "detections": [
       {
        "passTime": "7/29 05:51",
        "areaHectare": 5.78,
        "recheck": "pending",
        "recheckTime": "8/4 05:52",
        "iou": null,
        "evidenceImage": "docs/evidence/bl071_sar_0728.png",
        "reasons": [
         "新增水體 5.78 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 111.48 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（882 m）附近或以下，研判土石堵塞下游河道"
        ]
       }
      ],
      "priority": "high",
      "priorityText": "高優先",
      "action": "建議立即查證",
      "confidence": "高",
      "confidenceReasons": [
       "SAR 與他單位光學或航拍成果一致（獨立來源）",
       "外部來源：維基百科「花蓮馬太鞍溪堰塞湖災害」"
      ],
      "persistence": "pending",
      "persistenceText": "待複核",
      "grade": "B",
      "scale": "中",
      "summary": "E3 值得優先查證：6 項證據一致（SAR 新增水體、貼河道、附近崩塌、堵塞型態、他單位光學影像、他單位航拍），其中光學或航拍來自其他單位、與 SAR 互相獨立；目前缺少現地證據，建議下一步 UAV 現地查證並取得他單位既有判釋成果。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/29 05:51 SAR 新增水體 5.78 公頃（證據強度 B 級）"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 111.5 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（882 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（9.3 km）、2024 花蓮萬里溪（8.8 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "optical",
        "status": "support",
        "text": "7/24 農村水保署以 Planet 光學衛星影像發現堰塞湖，當日成立應變小組",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」（引農村水保署發布）",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "aerial",
        "status": "support",
        "text": "7/27 航遙分署航拍取得清晰堰塞湖畫面，推估崩塌量約 2 億 m³、壩高約 200 m",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [],
      "tasks": [
       {
        "label": "UAV／現地查證壩體與湖面",
        "reason": "SAR 只能看到水面，壩體高度、材料與溢流風險要現地確認"
       },
       {
        "label": "取得他單位既有光學判釋與航拍成果",
        "reason": "已有其他單位發布的成果，直接串接，不重做"
       },
       {
        "label": "通報主管機關（農村水保署）並評估下游保全對象",
        "reason": "下游已有聚落與橋梁"
       },
       {
        "label": "持續 SAR 監測（下一期 8/4）",
        "reason": "同時完成 SAR 持續性複核"
       },
       {
        "label": "補查形成期間雨量",
        "reason": "確認觸發條件；目前觀測表此欄空白"
       }
      ],
      "rulesFired": [
       "persistence.pending",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "external.optical",
       "external.aerial",
       "exposure.known",
       "gap.rain",
       "priority.high.corroborated"
      ]
     },
     {
      "id": "E1",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": false,
      "lonLat": [
       121.302402,
       23.709417
      ],
      "distanceFromReferenceM": 1093,
      "areaHectare": 2.76,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1113.0,
      "polygonLonLat": [
       [
        121.30211792898294,
        23.709414956823352
       ],
       [
        121.30238742356818,
        23.70986411446541
       ],
       [
        121.30301624426707,
        23.709684451408588
       ],
       [
        121.30274674968183,
        23.709145462238116
       ],
       [
        121.30166877134089,
        23.709504788351765
       ],
       [
        121.30157893981247,
        23.708516641539234
       ],
       [
        121.30068062452835,
        23.708696304596057
       ],
       [
        121.30139927675565,
        23.709145462238116
       ],
       [
        121.30121961369882,
        23.70986411446541
       ],
       [
        121.30220776051135,
        23.710133609050647
       ],
       [
        121.30211792898294,
        23.709414956823352
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 2.76,
        "recheck": "not_persistent",
        "recheckTime": "7/29 05:51",
        "iou": 0.01,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 2.76 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 130.07 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1113 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.01，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.01）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "中",
      "summary": "E1 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.01），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 2.76 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "7/29 複核同位置水體 IoU 0.01，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 130.1 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1113 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.9 km）、2024 花蓮萬里溪（7.7 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.01，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     },
     {
      "id": "E2",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": false,
      "lonLat": [
       121.307454,
       23.709175
      ],
      "distanceFromReferenceM": 1386,
      "areaHectare": 1.43,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1212.0,
      "polygonLonLat": [
       [
        121.30750782068766,
        23.708516641539234
       ],
       [
        121.30732815763083,
        23.707887820840348
       ],
       [
        121.30651967387513,
        23.708247146953997
       ],
       [
        121.3070586630456,
        23.708336978482407
       ],
       [
        121.3070586630456,
        23.70878613612447
       ],
       [
        121.30750782068766,
        23.708516641539234
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 1.43,
        "recheck": "not_persistent",
        "recheckTime": "7/29 05:51",
        "iou": 0.14,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 1.43 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 117.66 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1212 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.14，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.14）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "中",
      "summary": "E2 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.14），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 1.43 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "7/29 複核同位置水體 IoU 0.14，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 117.7 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1212 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.5 km）、2024 花蓮萬里溪（7.8 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.14，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     }
    ]
   },
   {
    "asOf": "2025-08-03T21:52:00+00:00",
    "label": "8/4 05:52",
    "what": "複核 7/29 的候選",
    "since": "距觸發約 13 天",
    "nextPass": "8/10",
    "counts": {
     "high": 1,
     "medium": 0,
     "low": 2
    },
    "newCount": 0,
    "events": [
     {
      "id": "E3",
      "firstSeen": "7/29 05:51",
      "lastSeen": "7/29 05:51",
      "isNew": false,
      "lonLat": [
       121.293466,
       23.698155
      ],
      "distanceFromReferenceM": 494,
      "areaHectare": 5.78,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 882.0,
      "polygonLonLat": [
       [
        121.29187713474398,
        23.697108037430915
       ],
       [
        121.29304494461334,
        23.69782668965821
       ],
       [
        121.29286528155652,
        23.69827584730027
       ],
       [
        121.29538056435204,
        23.6992639941128
       ],
       [
        121.29645854269299,
        23.70115045620945
       ],
       [
        121.29717719492028,
        23.70070129856739
       ],
       [
        121.29681786880664,
        23.700252140925333
       ],
       [
        121.29636871116458,
        23.70052163551057
       ],
       [
        121.2965483742214,
        23.699443657169624
       ],
       [
        121.29600938505094,
        23.699443657169624
       ],
       [
        121.29591955352252,
        23.698994499527565
       ],
       [
        121.29322460767015,
        23.69827584730027
       ],
       [
        121.29313477614176,
        23.697736858129797
       ],
       [
        121.29250595544286,
        23.696569048260443
       ],
       [
        121.29106865098828,
        23.69638938520362
       ],
       [
        121.29097881945987,
        23.695850396033148
       ],
       [
        121.29026016723256,
        23.69558090144791
       ],
       [
        121.28909235736322,
        23.695850396033148
       ],
       [
        121.29079915640304,
        23.696299553675207
       ],
       [
        121.29160764015874,
        23.69737753201615
       ],
       [
        121.29187713474398,
        23.697108037430915
       ]
      ],
      "detections": [
       {
        "passTime": "7/29 05:51",
        "areaHectare": 5.78,
        "recheck": "persistent",
        "recheckTime": "8/4 05:52",
        "iou": 0.52,
        "evidenceImage": "docs/evidence/bl071_sar_0728.png",
        "reasons": [
         "新增水體 5.78 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 111.48 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（882 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.52，持續蓄水"
        ]
       }
      ],
      "priority": "high",
      "priorityText": "高優先",
      "action": "建議立即查證",
      "confidence": "高",
      "confidenceReasons": [
       "SAR 與他單位光學或航拍成果一致（獨立來源）",
       "外部來源：維基百科「花蓮馬太鞍溪堰塞湖災害」"
      ],
      "persistence": "confirmed",
      "persistenceText": "已確認持續",
      "grade": "A",
      "scale": "中",
      "summary": "E3 值得優先查證：7 項證據一致（SAR 新增水體、跨期持續、貼河道、附近崩塌、堵塞型態、他單位光學影像、他單位航拍），其中光學或航拍來自其他單位、與 SAR 互相獨立；目前缺少現地證據，建議下一步 UAV 現地查證並取得他單位既有判釋成果。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/29 05:51 SAR 新增水體 5.78 公頃（證據強度 A 級）"
       },
       {
        "kind": "persistence",
        "status": "support",
        "text": "8/4 複核同位置仍有水體（IoU 0.52），共 1 期偵測到"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 111.5 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（882 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（9.3 km）、2024 花蓮萬里溪（8.8 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "optical",
        "status": "support",
        "text": "7/24 農村水保署以 Planet 光學衛星影像發現堰塞湖，當日成立應變小組",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」（引農村水保署發布）",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "aerial",
        "status": "support",
        "text": "7/27 航遙分署航拍取得清晰堰塞湖畫面，推估崩塌量約 2 億 m³、壩高約 200 m",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [],
      "tasks": [
       {
        "label": "UAV／現地查證壩體與湖面",
        "reason": "SAR 只能看到水面，壩體高度、材料與溢流風險要現地確認"
       },
       {
        "label": "取得他單位既有光學判釋與航拍成果",
        "reason": "已有其他單位發布的成果，直接串接，不重做"
       },
       {
        "label": "通報主管機關（農村水保署）並評估下游保全對象",
        "reason": "下游已有聚落與橋梁"
       },
       {
        "label": "持續 SAR 監測（下一期 8/10）",
        "reason": "追蹤湖面變化"
       },
       {
        "label": "補查形成期間雨量",
        "reason": "確認觸發條件；目前觀測表此欄空白"
       }
      ],
      "rulesFired": [
       "persistence.confirmed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "external.optical",
       "external.aerial",
       "exposure.known",
       "gap.rain",
       "priority.high.confirmed"
      ]
     },
     {
      "id": "E1",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": false,
      "lonLat": [
       121.302402,
       23.709417
      ],
      "distanceFromReferenceM": 1093,
      "areaHectare": 2.76,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1113.0,
      "polygonLonLat": [
       [
        121.30211792898294,
        23.709414956823352
       ],
       [
        121.30238742356818,
        23.70986411446541
       ],
       [
        121.30301624426707,
        23.709684451408588
       ],
       [
        121.30274674968183,
        23.709145462238116
       ],
       [
        121.30166877134089,
        23.709504788351765
       ],
       [
        121.30157893981247,
        23.708516641539234
       ],
       [
        121.30068062452835,
        23.708696304596057
       ],
       [
        121.30139927675565,
        23.709145462238116
       ],
       [
        121.30121961369882,
        23.70986411446541
       ],
       [
        121.30220776051135,
        23.710133609050647
       ],
       [
        121.30211792898294,
        23.709414956823352
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 2.76,
        "recheck": "not_persistent",
        "recheckTime": "7/29 05:51",
        "iou": 0.01,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 2.76 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 130.07 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1113 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.01，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.01）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "中",
      "summary": "E1 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.01），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 2.76 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "7/29 複核同位置水體 IoU 0.01，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 130.1 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1113 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.9 km）、2024 花蓮萬里溪（7.7 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.01，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     },
     {
      "id": "E2",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": false,
      "lonLat": [
       121.307454,
       23.709175
      ],
      "distanceFromReferenceM": 1386,
      "areaHectare": 1.43,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1212.0,
      "polygonLonLat": [
       [
        121.30750782068766,
        23.708516641539234
       ],
       [
        121.30732815763083,
        23.707887820840348
       ],
       [
        121.30651967387513,
        23.708247146953997
       ],
       [
        121.3070586630456,
        23.708336978482407
       ],
       [
        121.3070586630456,
        23.70878613612447
       ],
       [
        121.30750782068766,
        23.708516641539234
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 1.43,
        "recheck": "not_persistent",
        "recheckTime": "7/29 05:51",
        "iou": 0.14,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 1.43 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 117.66 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1212 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.14，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.14）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "中",
      "summary": "E2 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.14），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 1.43 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "7/29 複核同位置水體 IoU 0.14，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 117.7 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1212 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.5 km）、2024 花蓮萬里溪（7.8 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.14，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     }
    ]
   },
   {
    "asOf": "2025-08-21T21:51:00+00:00",
    "label": "8/22 05:51",
    "what": "新一期 SAR 全幅偵測",
    "since": "距觸發約 31 天",
    "nextPass": "8/28",
    "counts": {
     "high": 1,
     "medium": 2,
     "low": 2
    },
    "newCount": 2,
    "events": [
     {
      "id": "E3",
      "firstSeen": "7/29 05:51",
      "lastSeen": "8/22 05:51",
      "isNew": false,
      "lonLat": [
       121.294742,
       23.698303
      ],
      "distanceFromReferenceM": 381,
      "areaHectare": 26.32,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 849.0,
      "polygonLonLat": [
       [
        121.2919669662724,
        23.69728770048774
       ],
       [
        121.29385342836905,
        23.698904667999155
       ],
       [
        121.29511106976682,
        23.699174162584388
       ],
       [
        121.29690770033505,
        23.70186910843675
       ],
       [
        121.29780601561917,
        23.702138603021982
       ],
       [
        121.29699753186347,
        23.700341972453746
       ],
       [
        121.29636871116458,
        23.70052163551057
       ],
       [
        121.2965483742214,
        23.699443657169624
       ],
       [
        121.29717719492028,
        23.699443657169624
       ],
       [
        121.29825517326123,
        23.700611467038982
       ],
       [
        121.29816534173281,
        23.70115045620945
       ],
       [
        121.29933315160217,
        23.701779276908336
       ],
       [
        121.29996197230106,
        23.70285725524928
       ],
       [
        121.30005180382948,
        23.701779276908336
       ],
       [
        121.299512814659,
        23.701240287737864
       ],
       [
        121.29978230924424,
        23.700431803982156
       ],
       [
        121.30005180382948,
        23.70106062468104
       ],
       [
        121.30005180382948,
        23.70052163551057
       ],
       [
        121.30059079299994,
        23.70052163551057
       ],
       [
        121.30023146688629,
        23.700252140925333
       ],
       [
        121.30041112994311,
        23.699174162584388
       ],
       [
        121.299512814659,
        23.699174162584388
       ],
       [
        121.29996197230106,
        23.699533488698037
       ],
       [
        121.29996197230106,
        23.700252140925333
       ],
       [
        121.299512814659,
        23.69971315175486
       ],
       [
        121.299512814659,
        23.700431803982156
       ],
       [
        121.29897382548853,
        23.699174162584388
       ],
       [
        121.29942298313058,
        23.69863517341392
       ],
       [
        121.30023146688629,
        23.69863517341392
       ],
       [
        121.30005180382948,
        23.698365678828683
       ],
       [
        121.29690770033505,
        23.69827584730027
       ],
       [
        121.29672803727823,
        23.69872500494233
       ],
       [
        121.29645854269299,
        23.698365678828683
       ],
       [
        121.29466191212475,
        23.69863517341392
       ],
       [
        121.29322460767015,
        23.69827584730027
       ],
       [
        121.29331443919857,
        23.697557195072974
       ],
       [
        121.29475174365317,
        23.698006352715034
       ],
       [
        121.29466191212475,
        23.697108037430915
       ],
       [
        121.29403309142587,
        23.69683854284568
       ],
       [
        121.2943025860111,
        23.69647921673203
       ],
       [
        121.28909235736322,
        23.694053765464908
       ],
       [
        121.28945168347686,
        23.69540123839109
       ],
       [
        121.28891269430639,
        23.696119890618384
       ],
       [
        121.29034999876097,
        23.69603005908997
       ],
       [
        121.29097881945987,
        23.697108037430915
       ],
       [
        121.2919669662724,
        23.69728770048774
       ]
      ],
      "detections": [
       {
        "passTime": "7/29 05:51",
        "areaHectare": 5.78,
        "recheck": "persistent",
        "recheckTime": "8/4 05:52",
        "iou": 0.52,
        "evidenceImage": "docs/evidence/bl071_sar_0728.png",
        "reasons": [
         "新增水體 5.78 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 111.48 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（882 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.52，持續蓄水"
        ]
       },
       {
        "passTime": "8/22 05:51",
        "areaHectare": 26.32,
        "recheck": "pending",
        "recheckTime": "8/28 05:52",
        "iou": null,
        "evidenceImage": "docs/evidence/bl071_sar_0821.png",
        "reasons": [
         "新增水體 26.33 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 112.83 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（849 m）附近或以下，研判土石堵塞下游河道"
        ]
       }
      ],
      "priority": "high",
      "priorityText": "高優先",
      "action": "建議立即查證",
      "confidence": "高",
      "confidenceReasons": [
       "SAR 與他單位光學或航拍成果一致（獨立來源）",
       "外部來源：維基百科「花蓮馬太鞍溪堰塞湖災害」"
      ],
      "persistence": "confirmed",
      "persistenceText": "已確認持續",
      "grade": "A",
      "scale": "大",
      "summary": "E3 值得優先查證：8 項證據一致（SAR 新增水體、跨期持續、貼河道、附近崩塌、堵塞型態、面積擴大、他單位光學影像、他單位航拍），其中光學或航拍來自其他單位、與 SAR 互相獨立；目前缺少現地證據，建議下一步 UAV 現地查證並取得他單位既有判釋成果。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "8/22 05:51 SAR 新增水體 26.32 公頃（證據強度 A 級）"
       },
       {
        "kind": "persistence",
        "status": "support",
        "text": "8/4 複核同位置仍有水體（IoU 0.52），共 2 期偵測到"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 112.8 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（849 m）以下，符合堵塞型態"
       },
       {
        "kind": "trend",
        "status": "support",
        "text": "面積 5.8 → 26.3 公頃，擴大中"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（9.1 km）、2024 花蓮萬里溪（8.8 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "optical",
        "status": "support",
        "text": "7/24 農村水保署以 Planet 光學衛星影像發現堰塞湖，當日成立應變小組",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」（引農村水保署發布）",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "aerial",
        "status": "support",
        "text": "7/27 航遙分署航拍取得清晰堰塞湖畫面，推估崩塌量約 2 億 m³、壩高約 200 m",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "official",
        "status": "context",
        "text": "8/20 官方估蓄水量 4,800 萬 m³，滿水位 9,100 萬 m³",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [],
      "tasks": [
       {
        "label": "UAV／現地查證壩體與湖面",
        "reason": "SAR 只能看到水面，壩體高度、材料與溢流風險要現地確認"
       },
       {
        "label": "取得他單位既有光學判釋與航拍成果",
        "reason": "已有其他單位發布的成果，直接串接，不重做"
       },
       {
        "label": "通報主管機關（農村水保署）並評估下游保全對象",
        "reason": "下游已有聚落與橋梁"
       },
       {
        "label": "持續 SAR 監測（下一期 8/28）",
        "reason": "追蹤湖面變化；目前面積擴大中"
       },
       {
        "label": "補查形成期間雨量",
        "reason": "確認觸發條件；目前觀測表此欄空白"
       }
      ],
      "rulesFired": [
       "persistence.confirmed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "trend.growing",
       "history.nearby",
       "external.optical",
       "external.aerial",
       "external.official",
       "exposure.known",
       "gap.rain",
       "priority.high.confirmed"
      ]
     },
     {
      "id": "E4",
      "firstSeen": "8/22 05:51",
      "lastSeen": "8/22 05:51",
      "isNew": true,
      "lonLat": [
       121.30725,
       23.695248
      ],
      "distanceFromReferenceM": 1155,
      "areaHectare": 0.75,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 935.0,
      "polygonLonLat": [
       [
        121.30732815763083,
        23.69459275463538
       ],
       [
        121.30678916846037,
        23.69495208074903
       ],
       [
        121.30741798915925,
        23.695131743805852
       ],
       [
        121.30687899998878,
        23.695221575334262
       ],
       [
        121.30714849457401,
        23.695850396033148
       ],
       [
        121.3077773152729,
        23.6954910699195
       ],
       [
        121.30732815763083,
        23.69459275463538
       ]
      ],
      "detections": [
       {
        "passTime": "8/22 05:51",
        "areaHectare": 0.75,
        "recheck": "pending",
        "recheckTime": "8/28 05:52",
        "iou": null,
        "evidenceImage": "docs/evidence/bl071_sar_0821.png",
        "reasons": [
         "新增水體 0.75 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 97.90 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（935 m）附近或以下，研判土石堵塞下游河道"
        ]
       }
      ],
      "priority": "medium",
      "priorityText": "中優先",
      "action": "建議人工確認",
      "confidence": "低",
      "confidenceReasons": [
       "只有單期 SAR，尚未複核"
      ],
      "persistence": "pending",
      "persistenceText": "待複核",
      "grade": "B",
      "scale": "小",
      "summary": "E4 需要人工確認：單期 SAR 出現約 0.8 公頃的疑似新增水體，空間條件符合，但尚未複核；建議 8/28 下一期過境複核，暫不派遣 UAV。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "8/22 05:51 SAR 新增水體 0.75 公頃（證據強度 B 級）"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 97.9 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（935 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（8.2 km）、2024 花蓮萬里溪（9.3 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "persistence",
        "text": "尚未複核：單期影像無法排除陰影或濕土誤判（下一期 8/28）"
       },
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [],
      "tasks": [
       {
        "label": "值班人員判讀 SAR 證據圖",
        "reason": "確認暗區是否在河谷底、是否為崩塌坡面陰影"
       },
       {
        "label": "排下一期 SAR 複核（8/28）",
        "reason": "A 級需要兩期一致；單期出現的暗區多數會在複核時消失"
       },
       {
        "label": "調閱光學影像（雲況許可時）",
        "reason": "SAR 以外的獨立證據"
       },
       {
        "label": "暫不派遣 UAV",
        "reason": "目前只有單期 SAR，先以複核過濾誤報，避免浪費現地人力"
       },
       {
        "label": "補查形成期間雨量",
        "reason": "確認觸發條件；目前觀測表此欄空白"
       }
      ],
      "rulesFired": [
       "persistence.pending",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "priority.medium.pending"
      ]
     },
     {
      "id": "E5",
      "firstSeen": "8/22 05:51",
      "lastSeen": "8/22 05:51",
      "isNew": true,
      "lonLat": [
       121.310437,
       23.70793
      ],
      "distanceFromReferenceM": 1545,
      "areaHectare": 0.51,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1416.0,
      "polygonLonLat": [
       [
        121.31020276654002,
        23.70878613612447
       ],
       [
        121.31020276654002,
        23.70842681001082
       ],
       [
        121.30993327195479,
        23.708696304596057
       ],
       [
        121.31020276654002,
        23.70878613612447
       ]
      ],
      "detections": [
       {
        "passTime": "8/22 05:51",
        "areaHectare": 0.51,
        "recheck": "pending",
        "recheckTime": "8/28 05:52",
        "iou": null,
        "evidenceImage": "docs/evidence/bl071_sar_0821.png",
        "reasons": [
         "新增水體 0.51 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 92.19 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1416 m）附近或以下，研判土石堵塞下游河道"
        ]
       }
      ],
      "priority": "medium",
      "priorityText": "中優先",
      "action": "建議人工確認",
      "confidence": "低",
      "confidenceReasons": [
       "只有單期 SAR，尚未複核"
      ],
      "persistence": "pending",
      "persistenceText": "待複核",
      "grade": "B",
      "scale": "小",
      "summary": "E5 需要人工確認：單期 SAR 出現約 0.5 公頃的疑似新增水體，空間條件符合，但尚未複核；建議 8/28 下一期過境複核，暫不派遣 UAV。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "8/22 05:51 SAR 新增水體 0.51 公頃（證據強度 B 級）"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 92.2 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1416 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.2 km）、2024 花蓮萬里溪（8.0 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "persistence",
        "text": "尚未複核：單期影像無法排除陰影或濕土誤判（下一期 8/28）"
       },
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [],
      "tasks": [
       {
        "label": "值班人員判讀 SAR 證據圖",
        "reason": "確認暗區是否在河谷底、是否為崩塌坡面陰影"
       },
       {
        "label": "排下一期 SAR 複核（8/28）",
        "reason": "A 級需要兩期一致；單期出現的暗區多數會在複核時消失"
       },
       {
        "label": "調閱光學影像（雲況許可時）",
        "reason": "SAR 以外的獨立證據"
       },
       {
        "label": "暫不派遣 UAV",
        "reason": "目前只有單期 SAR，先以複核過濾誤報，避免浪費現地人力"
       },
       {
        "label": "補查形成期間雨量",
        "reason": "確認觸發條件；目前觀測表此欄空白"
       }
      ],
      "rulesFired": [
       "persistence.pending",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "priority.medium.pending"
      ]
     },
     {
      "id": "E1",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": false,
      "lonLat": [
       121.302402,
       23.709417
      ],
      "distanceFromReferenceM": 1093,
      "areaHectare": 2.76,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1113.0,
      "polygonLonLat": [
       [
        121.30211792898294,
        23.709414956823352
       ],
       [
        121.30238742356818,
        23.70986411446541
       ],
       [
        121.30301624426707,
        23.709684451408588
       ],
       [
        121.30274674968183,
        23.709145462238116
       ],
       [
        121.30166877134089,
        23.709504788351765
       ],
       [
        121.30157893981247,
        23.708516641539234
       ],
       [
        121.30068062452835,
        23.708696304596057
       ],
       [
        121.30139927675565,
        23.709145462238116
       ],
       [
        121.30121961369882,
        23.70986411446541
       ],
       [
        121.30220776051135,
        23.710133609050647
       ],
       [
        121.30211792898294,
        23.709414956823352
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 2.76,
        "recheck": "not_persistent",
        "recheckTime": "7/29 05:51",
        "iou": 0.01,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 2.76 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 130.07 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1113 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.01，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.01）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "中",
      "summary": "E1 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.01），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 2.76 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "7/29 複核同位置水體 IoU 0.01，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 130.1 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1113 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.9 km）、2024 花蓮萬里溪（7.7 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.01，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     },
     {
      "id": "E2",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": false,
      "lonLat": [
       121.307454,
       23.709175
      ],
      "distanceFromReferenceM": 1386,
      "areaHectare": 1.43,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1212.0,
      "polygonLonLat": [
       [
        121.30750782068766,
        23.708516641539234
       ],
       [
        121.30732815763083,
        23.707887820840348
       ],
       [
        121.30651967387513,
        23.708247146953997
       ],
       [
        121.3070586630456,
        23.708336978482407
       ],
       [
        121.3070586630456,
        23.70878613612447
       ],
       [
        121.30750782068766,
        23.708516641539234
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 1.43,
        "recheck": "not_persistent",
        "recheckTime": "7/29 05:51",
        "iou": 0.14,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 1.43 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 117.66 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1212 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.14，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.14）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "中",
      "summary": "E2 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.14），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 1.43 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "7/29 複核同位置水體 IoU 0.14，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 117.7 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1212 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.5 km）、2024 花蓮萬里溪（7.8 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.14，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     }
    ]
   },
   {
    "asOf": "2025-08-27T21:52:00+00:00",
    "label": "8/28 05:52",
    "what": "新一期 SAR 全幅偵測＋複核 8/22 的候選",
    "since": "距觸發約 37 天",
    "nextPass": "9/3",
    "counts": {
     "high": 1,
     "medium": 0,
     "low": 4
    },
    "newCount": 0,
    "events": [
     {
      "id": "E3",
      "firstSeen": "7/29 05:51",
      "lastSeen": "8/28 05:52",
      "isNew": false,
      "lonLat": [
       121.294219,
       23.697966
      ],
      "distanceFromReferenceM": 446,
      "areaHectare": 23.57,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 848.0,
      "polygonLonLat": [
       [
        121.29124831404509,
        23.697197868959325
       ],
       [
        121.29304494461334,
        23.69782668965821
       ],
       [
        121.29295511308493,
        23.698365678828683
       ],
       [
        121.29385342836905,
        23.698455510357093
       ],
       [
        121.29322460767015,
        23.69827584730027
       ],
       [
        121.29331443919857,
        23.697557195072974
       ],
       [
        121.29475174365317,
        23.698006352715034
       ],
       [
        121.29466191212475,
        23.697108037430915
       ],
       [
        121.29403309142587,
        23.69683854284568
       ],
       [
        121.29421275448269,
        23.69638938520362
       ],
       [
        121.29026016723256,
        23.69423342852173
       ],
       [
        121.28918218889163,
        23.693963933936494
       ],
       [
        121.28918218889163,
        23.694682586163793
       ],
       [
        121.28873303124956,
        23.694862249220616
       ],
       [
        121.28792454749386,
        23.69423342852173
       ],
       [
        121.28720589526657,
        23.694502923106967
       ],
       [
        121.2882838736075,
        23.695760564504734
       ],
       [
        121.28918218889163,
        23.694862249220616
       ],
       [
        121.28945168347686,
        23.69540123839109
       ],
       [
        121.28891269430639,
        23.69603005908997
       ],
       [
        121.29034999876097,
        23.69603005908997
       ],
       [
        121.29124831404509,
        23.697197868959325
       ]
      ],
      "detections": [
       {
        "passTime": "7/29 05:51",
        "areaHectare": 5.78,
        "recheck": "persistent",
        "recheckTime": "8/4 05:52",
        "iou": 0.52,
        "evidenceImage": "docs/evidence/bl071_sar_0728.png",
        "reasons": [
         "新增水體 5.78 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 111.48 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（882 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.52，持續蓄水"
        ]
       },
       {
        "passTime": "8/22 05:51",
        "areaHectare": 26.32,
        "recheck": "persistent",
        "recheckTime": "8/28 05:52",
        "iou": 0.76,
        "evidenceImage": "docs/evidence/bl071_sar_0821.png",
        "reasons": [
         "新增水體 26.33 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 112.83 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（849 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.76，持續蓄水"
        ]
       },
       {
        "passTime": "8/28 05:52",
        "areaHectare": 23.57,
        "recheck": "pending",
        "recheckTime": null,
        "iou": null,
        "evidenceImage": "docs/evidence/bl071_sar_0827.png",
        "reasons": [
         "新增水體 23.57 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 136.86 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（848 m）附近或以下，研判土石堵塞下游河道",
         "僅單期影像，尚未確認多時相持續性"
        ]
       }
      ],
      "priority": "high",
      "priorityText": "高優先",
      "action": "建議立即查證",
      "confidence": "高",
      "confidenceReasons": [
       "SAR 與他單位光學或航拍成果一致（獨立來源）",
       "外部來源：維基百科「花蓮馬太鞍溪堰塞湖災害」"
      ],
      "persistence": "confirmed",
      "persistenceText": "已確認持續",
      "grade": "A",
      "scale": "大",
      "summary": "E3 值得優先查證：8 項證據一致（SAR 新增水體、跨期持續、貼河道、附近崩塌、堵塞型態、面積擴大、他單位光學影像、他單位航拍），其中光學或航拍來自其他單位、與 SAR 互相獨立；目前缺少現地證據，建議下一步 UAV 現地查證並取得他單位既有判釋成果。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "8/28 05:52 SAR 新增水體 23.57 公頃（證據強度 A 級）"
       },
       {
        "kind": "persistence",
        "status": "support",
        "text": "8/28 複核同位置仍有水體（IoU 0.76），共 3 期偵測到"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 136.9 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（848 m）以下，符合堵塞型態"
       },
       {
        "kind": "trend",
        "status": "support",
        "text": "面積 5.8 → 23.6 公頃，擴大中"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（9.2 km）、2024 花蓮萬里溪（8.9 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "optical",
        "status": "support",
        "text": "7/24 農村水保署以 Planet 光學衛星影像發現堰塞湖，當日成立應變小組",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」（引農村水保署發布）",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "aerial",
        "status": "support",
        "text": "7/27 航遙分署航拍取得清晰堰塞湖畫面，推估崩塌量約 2 億 m³、壩高約 200 m",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "official",
        "status": "context",
        "text": "8/20 官方估蓄水量 4,800 萬 m³，滿水位 9,100 萬 m³",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」",
        "url": "https://zh.wikipedia.org/zh-tw/花蓮馬太鞍溪堰塞湖災害"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [],
      "tasks": [
       {
        "label": "UAV／現地查證壩體與湖面",
        "reason": "SAR 只能看到水面，壩體高度、材料與溢流風險要現地確認"
       },
       {
        "label": "取得他單位既有光學判釋與航拍成果",
        "reason": "已有其他單位發布的成果，直接串接，不重做"
       },
       {
        "label": "通報主管機關（農村水保署）並評估下游保全對象",
        "reason": "下游已有聚落與橋梁"
       },
       {
        "label": "持續 SAR 監測（下一期 9/3）",
        "reason": "追蹤湖面變化；目前面積擴大中"
       },
       {
        "label": "補查形成期間雨量",
        "reason": "確認觸發條件；目前觀測表此欄空白"
       }
      ],
      "rulesFired": [
       "persistence.confirmed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "trend.growing",
       "history.nearby",
       "external.optical",
       "external.aerial",
       "external.official",
       "exposure.known",
       "gap.rain",
       "priority.high.confirmed"
      ]
     },
     {
      "id": "E1",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": false,
      "lonLat": [
       121.302402,
       23.709417
      ],
      "distanceFromReferenceM": 1093,
      "areaHectare": 2.76,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1113.0,
      "polygonLonLat": [
       [
        121.30211792898294,
        23.709414956823352
       ],
       [
        121.30238742356818,
        23.70986411446541
       ],
       [
        121.30301624426707,
        23.709684451408588
       ],
       [
        121.30274674968183,
        23.709145462238116
       ],
       [
        121.30166877134089,
        23.709504788351765
       ],
       [
        121.30157893981247,
        23.708516641539234
       ],
       [
        121.30068062452835,
        23.708696304596057
       ],
       [
        121.30139927675565,
        23.709145462238116
       ],
       [
        121.30121961369882,
        23.70986411446541
       ],
       [
        121.30220776051135,
        23.710133609050647
       ],
       [
        121.30211792898294,
        23.709414956823352
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 2.76,
        "recheck": "not_persistent",
        "recheckTime": "7/29 05:51",
        "iou": 0.01,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 2.76 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 130.07 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1113 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.01，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.01）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "中",
      "summary": "E1 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.01），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 2.76 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "7/29 複核同位置水體 IoU 0.01，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 130.1 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1113 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.9 km）、2024 花蓮萬里溪（7.7 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.01，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     },
     {
      "id": "E2",
      "firstSeen": "7/23 05:52",
      "lastSeen": "7/23 05:52",
      "isNew": false,
      "lonLat": [
       121.307454,
       23.709175
      ],
      "distanceFromReferenceM": 1386,
      "areaHectare": 1.43,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1212.0,
      "polygonLonLat": [
       [
        121.30750782068766,
        23.708516641539234
       ],
       [
        121.30732815763083,
        23.707887820840348
       ],
       [
        121.30651967387513,
        23.708247146953997
       ],
       [
        121.3070586630456,
        23.708336978482407
       ],
       [
        121.3070586630456,
        23.70878613612447
       ],
       [
        121.30750782068766,
        23.708516641539234
       ]
      ],
      "detections": [
       {
        "passTime": "7/23 05:52",
        "areaHectare": 1.43,
        "recheck": "not_persistent",
        "recheckTime": "7/29 05:51",
        "iou": 0.14,
        "evidenceImage": "docs/evidence/bl071_sar_0722.png",
        "reasons": [
         "新增水體 1.43 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 117.66 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1212 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.14，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.14）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "中",
      "summary": "E2 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.14），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "7/23 05:52 SAR 新增水體 1.43 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "7/29 複核同位置水體 IoU 0.14，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 117.7 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1212 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.5 km）、2024 花蓮萬里溪（7.8 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.14，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     },
     {
      "id": "E4",
      "firstSeen": "8/22 05:51",
      "lastSeen": "8/22 05:51",
      "isNew": false,
      "lonLat": [
       121.30725,
       23.695248
      ],
      "distanceFromReferenceM": 1155,
      "areaHectare": 0.75,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 935.0,
      "polygonLonLat": [
       [
        121.30732815763083,
        23.69459275463538
       ],
       [
        121.30678916846037,
        23.69495208074903
       ],
       [
        121.30741798915925,
        23.695131743805852
       ],
       [
        121.30687899998878,
        23.695221575334262
       ],
       [
        121.30714849457401,
        23.695850396033148
       ],
       [
        121.3077773152729,
        23.6954910699195
       ],
       [
        121.30732815763083,
        23.69459275463538
       ]
      ],
      "detections": [
       {
        "passTime": "8/22 05:51",
        "areaHectare": 0.75,
        "recheck": "not_persistent",
        "recheckTime": "8/28 05:52",
        "iou": 0.2,
        "evidenceImage": "docs/evidence/bl071_sar_0821.png",
        "reasons": [
         "新增水體 0.75 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 97.90 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（935 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.20，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.20）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "小",
      "summary": "E4 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.20），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "8/22 05:51 SAR 新增水體 0.75 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "8/28 複核同位置水體 IoU 0.20，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 97.9 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（935 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（8.2 km）、2024 花蓮萬里溪（9.3 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.20，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     },
     {
      "id": "E5",
      "firstSeen": "8/22 05:51",
      "lastSeen": "8/22 05:51",
      "isNew": false,
      "lonLat": [
       121.310437,
       23.70793
      ],
      "distanceFromReferenceM": 1545,
      "areaHectare": 0.51,
      "areaNote": "SAR 陡坡與陰影遮罩會擋掉部分湖面，面積偏低，視為下限",
      "lakeFloorM": 1416.0,
      "polygonLonLat": [
       [
        121.31020276654002,
        23.70878613612447
       ],
       [
        121.31020276654002,
        23.70842681001082
       ],
       [
        121.30993327195479,
        23.708696304596057
       ],
       [
        121.31020276654002,
        23.70878613612447
       ]
      ],
      "detections": [
       {
        "passTime": "8/22 05:51",
        "areaHectare": 0.51,
        "recheck": "not_persistent",
        "recheckTime": "8/28 05:52",
        "iou": 0.21,
        "evidenceImage": "docs/evidence/bl071_sar_0821.png",
        "reasons": [
         "新增水體 0.51 公頃，緊貼事件前河道",
         "500 m 內偵測到崩塌 92.19 公頃（SAR 回波變化 ≥ 門檻）",
         "崩塌延伸至湖底高程（1416 m）附近或以下，研判土石堵塞下游河道",
         "後續 1 期影像同位置水體 IoU 最高 0.21，未確認持續"
        ]
       }
      ],
      "priority": "low",
      "priorityText": "低優先",
      "action": "暫時觀察",
      "confidence": "中",
      "confidenceReasons": [
       "複核結果明確（IoU 0.21）",
       "證據只有 SAR 一種來源，最高到「中」"
      ],
      "persistence": "failed",
      "persistenceText": "複核未持續",
      "grade": "B",
      "scale": "小",
      "summary": "E5 暫時觀察：空間條件符合，但下一期複核未持續（IoU 0.21），不建議派遣任務。",
      "evidence": [
       {
        "kind": "sar",
        "status": "support",
        "text": "8/22 05:51 SAR 新增水體 0.51 公頃（證據強度 B 級）"
       },
       {
        "kind": "persistence",
        "status": "against",
        "text": "8/28 複核同位置水體 IoU 0.21，未持續"
       },
       {
        "kind": "river",
        "status": "support",
        "text": "緊貼事件前河道（DEM 填窪後 D8 河網）"
       },
       {
        "kind": "landslide",
        "status": "support",
        "text": "500 m 內有 SAR 崩塌訊號 92.2 公頃"
       },
       {
        "kind": "terrain",
        "status": "support",
        "text": "崩塌延伸到水體下游、湖底高程（1416 m）以下，符合堵塞型態"
       },
       {
        "kind": "history",
        "status": "context",
        "text": "10 km 內清冊另有 2 筆堰塞湖：2016 萬里溪（7.2 km）、2024 花蓮萬里溪（8.0 km）"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "薇帕颱風外圍環流，2025-07-21 起連日豪雨"
       },
       {
        "kind": "context",
        "status": "context",
        "text": "區域曾受 2024-04-03 花蓮地震（規模 7.2）影響"
       },
       {
        "kind": "exposure",
        "status": "context",
        "text": "下游為光復鄉市區與台 9 線馬太鞍溪橋；9/21 撤離範圍為光復鄉、鳳林鎮、萬榮鄉共 1,800 戶、8,000 多人（事後資料，僅供規模參考）",
        "source": "維基百科「花蓮馬太鞍溪堰塞湖災害」；NCDR 馬太鞍溪堰塞湖災害全紀錄",
        "url": "https://den.ncdr.nat.gov.tw/special/%E9%A6%AC%E5%A4%AA%E9%9E%8D/index.html"
       }
      ],
      "gaps": [
       {
        "kind": "rain",
        "text": "形成期間雨量：尚未取得測站資料（CWA 歷史雨量待補）"
       },
       {
        "kind": "optical",
        "text": "光學影像：尚未調閱（颱風期間多雲，雲散後可調 Sentinel-2）"
       },
       {
        "kind": "field",
        "text": "人工查證：尚未進行"
       }
      ],
      "conflicts": [
       "空間條件（河道、崩塌、堵塞型態）都符合，但下一期複核未持續。以持續性為準：單期暗區常見成因是崩塌後新陡崖的雷達陰影或濕土暫時變暗。"
      ],
      "tasks": [
       {
        "label": "暫時觀察，不派遣任務",
        "reason": "下一期複核同位置水體 IoU 0.21，未持續"
       },
       {
        "label": "若同位置再次出現，重新列入待複核",
        "reason": "跨期追蹤以 250 m 內為同一事件"
       }
      ],
      "rulesFired": [
       "persistence.failed",
       "spatial.on_river",
       "spatial.landslide",
       "spatial.blockage",
       "history.nearby",
       "exposure.known",
       "gap.rain",
       "gap.optical",
       "conflict.spatial_vs_persistence",
       "priority.low.failed"
      ]
     }
    ]
   }
  ]
 }
];
