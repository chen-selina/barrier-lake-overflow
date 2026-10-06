# OSSInt 2026 · 堰塞湖事件研判平台

豪雨與颱風期間，值班人員要從大量資料裡找出「哪一件最該先查」。本系統把衛星偵測結果整理成
**事件佇列**：每個疑似事件附上證據、證據缺口、優先等級和建議任務，由值班人員做最後判斷。

- **SAR 提供證據，不下結論。** Sentinel-1 能穿雲，但單期暗區可能是陰影或濕土。偵測端的 A/B/C
  只當「SAR 證據強度」，要經過複核、空間條件和人工查證才會排進高優先。
- **系統整理與排序，人員判斷。** 只有 SAR 證據時，研判信心最高到「中」；要有他單位光學／航拍成果或人工查證才會到「高」。
- **串接既有能力，不重做。** 其他單位已發布的光學判釋、航拍成果，依時間與位置自動對到事件，當作獨立證據。
- **不只說哪裡有異常，還說下一步做什麼。** 例如：「E3 值得優先查證：6 項證據一致；
  目前缺少光學影像與現地證據，建議下一步 UAV 現地查證並調閱光學影像。」

規則見 [`docs/events.md`](docs/events.md)。

開源空間資訊於國家韌性應用黑客松競賽（OSSInt 2026）· 災害防救賽道

## 目前進度

決賽聚焦「事件研判與任務編排」。下表上半部是決賽主線，下半部列為後續擴充、決賽不展示。

| 模組 | 狀態 |
|---|---|
| **事件佇列：跨期追蹤 → 優先排序 → 證據缺口 → 建議任務 → 人工查證** | **完成**，馬太鞍溪 5 個時點逐期回放（見下節），28 項測試 |
| 串接他單位既有成果（光學、航拍、下游保全對象） | 完成，馬太鞍溪 4 筆，皆附出處；雨量仍查不到測站數字 |
| SAR 變化偵測 → 新增水體／崩塌 → SAR 證據強度 A/B/C | 完成真實案例驗證（馬太鞍溪，Sentinel-1 降軌 105） |
| 清冊轉換（TWD97 → WGS84） | 完成，75 筆 |
| 全台分布儀表板 | 完成；馬太鞍溪湖面範圍已改用 SAR 判定結果 |
| 成因歸因與敘述 | 完成，39 項測試 |
| 規模 | SAR 事件只給相對級距（大／中／小），不換算蓄水量；清冊數字標明「清冊登載」 |
| 負案例驗證（2026 汛期，同窗格同參數） | 匯出與執行腳本完成，**影像尚未下載、尚未執行** |
| 水體萃取：光學 NDWI | 程式完成；馬太鞍溪的結果已撤下（偵測到的是壩址下游的水體，不是湖） |
| *後續擴充：* 溢流預報、雨量風險模型、淹沒範圍＋人口暴露 | 程式保留，決賽不展示（CAP 示警已移除） |

### 馬太鞍溪事件佇列回放

儀表板最上方的「值班佇列」。每一期衛星過境是一個時點，只用當時已取得的影像：

| 時點（台灣） | 高 | 中 | 低 | 值班人員看到的 |
|---|---|---|---|---|
| 7/23 05:52 | 0 | 2 | 0 | 兩個暗區待複核，建議暫不派 UAV（事後證實是誤報） |
| 7/29 05:51 | 1 | 0 | 2 | 湖（E3）首次被 SAR 偵測到，對上 7/24 農村水保署光學影像、7/27 航遙分署航拍，多源一致直接列高優先：建議 UAV 現地查證、取得既有判釋成果、通報主管機關；前兩個暗區複核未持續，降為觀察 |
| 8/4 05:52 | 1 | 0 | 2 | E3 SAR 複核也持續（IoU 0.52） |
| 8/22 05:51 | 1 | 2 | 2 | E3 擴大到 26 公頃；新增兩個小暗區待複核 |
| 8/28 05:52 | 1 | 0 | 4 | 新暗區複核未持續；佇列只剩 E3 需要處理 |

成功案例和困難案例在同一段回放裡：四個誤報從頭到尾都沒進到高優先。

### 馬太鞍溪（bl071）SAR 偵測結果

同一組參數（坡度門檻 35°、D8 河網先填窪）跑四個日期，結果檔在 `data/derived/final_*.json`，
影像證據圖在 `docs/evidence/`。

| 影像日期 | 距形成 | 湖（壩址西南方 380～500 m） | 其他候選 |
|---|---|---|---|
| 7/22 ＋ 7/28 複核 | 約 36 小時 | 未偵測（影像上湖尚未成形，但崩塌堆積已可見） | 2 個 B 級，複核未持續 |
| 7/28 ＋ 8/3 複核 | 約 7 天 | **A 級**，5.8 公頃，複核重疊度 0.52 | 無 |
| 8/21 ＋ 8/27 複核 | 約 31 天 | **A 級**，26.3 公頃，複核重疊度 0.76 | 2 個 B 級，複核未持續 |
| 8/27 單期 | 約 37 天 | B 級（單期最高為 B） | 無 |

**時間軸**（台灣時間）：7/21 17:54 形成 → 7/23 05:52 第一次過境，湖尚未成形 →
7/29 05:51 第二次過境，判 B 級（排下一期複核）→ 8/4 05:52 第三次過境，複核持續，升 A 級。
瓶頸是衛星重訪（降軌每 6 天），不是運算；影像下載後的分析在筆電上即可完成，耗時遠小於重訪間隔。

**誤報**：4 個，全部位於壩址東側與東北側的崩塌地上（高程 935～1,587 m，遠高於湖底約 850 m），
推測是崩塌改變地形後產生的新陰影。全部在下一期複核時判為未持續（重疊度 ≤ 0.21）。

**參數怎麼來的**：預設坡度門檻 20° 在這個窄谷會遮掉約九成的湖面；改為 35° 是用 8/27
對照組選出後固定，其他日期不再調整。D8 填窪是修正已知問題（未填窪時河網幾乎消失，
湖被誤判為「未貼河道」）。兩者都只用這一個案例校準，負案例需用同一組參數驗證。

## 執行方式

| 情境 | 做法 |
|---|---|
| 只想看結果 | 直接開 `code/dashboard/index.html`，不用裝任何東西，離線也可以（字型在 `dashboard/vendor/fonts/`；資料出現新字時在 `code/` 底下跑 `python scripts/vendor_fonts.py`） |
| 要改程式 | 見下方「開發環境」，需要 Python 3.11+ |
| 要給沒裝 Python 的人用，而且資料會更新 | 見 [`docs/portable-distribution.md`](docs/portable-distribution.md) |

### 開發環境

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd code && pip install -e .
```

以下指令都在 `code/` 底下執行：

```bash
pytest                                  # 179 項

python -m pipeline.build_all            # 清冊 → lakes.js、風險 → risk.js、成因敘述、事件佇列 events.js
python -m pipeline.build_all --live     # 風險改抓 CWA 即時雨量
```

`--live` 需要先設 `CWA_API_KEY`（opendata.cwa.gov.tw 免費申請）；沒設的話會退回佔位值，不會失敗。

各步驟也可以單獨跑：

```bash
python -m pipeline.ingest.inventory ../data/raw/taiwan-barrier-lakes.csv dashboard/data/lakes.js
python -m pipeline.attribution.annotate
python -m pipeline.ingest.risk            # 加 --offline 不連網
python -m pipeline.ingest.observations    # 看 observations.csv 填了幾筆
python -m pipeline.events.build           # SAR 結果 → 事件佇列 events.js（情境設定在 data/raw/scenarios/）
```

每個模組直接執行會跑自己的 doctest 和合成資料示範，例如：

```bash
python -m pipeline.detect.barrier_lake   # 四種合成情境的 A/B/C 分級
python -m pipeline.assess.hypsometry
python -m pipeline.attribution.forecast
```

### SAR 真實案例重現

1. 在 Google Earth Engine 執行 `code/scripts/gee_export_matai_an_s1.js`，匯出 7 張 Sentinel-1 與 1 張 DEM，
   放到 `data/raw/sentinel1/`（這批影像已進版控，可略過此步）。
2. 在 `code/` 底下：

```bash
scripts\run_sar_all.bat                 # Windows：四個日期、同一組參數 → data/derived/final_*.json
python scripts/make_sar_evidence.py     # 影像證據圖 → docs/evidence/*.png（需 matplotlib）
```

單一日期可直接呼叫 `scripts/analyze_sar_change.py`，常用選項：
`--max-water-slope-deg`（坡度門檻）、`--debug-components`（列出被淘汰的水體塊與原因）、
`--dashboard-out dashboard/data/inundation.js`（把最高等級候選寫進儀表板）。

### 負案例（2026 汛期）

1. 在 GEE 執行 `code/scripts/gee_export_series_s1.js`（預設同一個馬太鞍溪窗格、2026-06～09），
   匯出的檔案放到 `data/raw/sentinel1/`，Console 會印出過境時間。
2. 在 `code/` 底下：

```bash
python scripts/run_sar_series.py --name neg2026_matai_an --lon 121.29752 --lat 23.70061 --scenario-name "馬太鞍溪 · 2026 汛期（負案例）" --kind negative
python -m pipeline.events.build
```

參數與正案例相同，不另外調。結果若出現高優先事件，要當成需要查證的發現，不要回頭調參數。

光學 NDWI（`scripts/analyze_ndwi_change.py`）與 DEM 蓄水量（`scripts/run_hypsometry_real.py`）的腳本保留，
但馬太鞍溪的結果因面積依據有誤已撤下。

## 目錄

```
code/
  pipeline/
    ingest/        清冊、CWA、風險模型、人工觀測
    events/        事件追蹤、優先排序、證據缺口、建議任務
    preprocess/    SAR 濾波與幾何遮罩
    detect/        水體、崩塌、疑似堰塞湖分級
    assess/        蓄水量、級距、淹沒、暴露
    attribution/   成因敘述與溢流預報
    build_all.py
  scripts/         真實資料的一次性分析
  tests/
  dashboard/       純靜態前端
data/
  raw/             原始資料（小檔進版控）
  derived/         中間產物（不進版控）
docs/
run_dashboard.bat
```

## 資料來源

堰塞湖清冊來自農業部農村發展及水土保持署
（<https://tech.ardswc.gov.tw/Results/BarrierLakeInfo>），75 筆，1979–2026 年。
其他資料來源與授權見 `docs/ossint-open-data-atlas.html`。

## 設計上的兩個選擇

**敘述不用 LLM。** 每句話都要能對回是哪條規則、哪個門檻產生的，所以用規則判斷加模板填空，
輸出附 `rules_fired`。見 `docs/attribution.md`。

**預報只給區間。** 用高、中、低三個雨量情境各算一次，回報最早、中位、最晚，並列出逕流係數等假設。

## 已知限制

- **參數只用一個案例校準。** 坡度門檻 35° 由馬太鞍溪 8/27 選定；負案例還沒跑，誤報率未知。
- **事件規則的門檻是自訂的。** 追蹤半徑 250 m、規模級距 1／10 公頃都只用這一個案例檢查過，見 `docs/events.md`。
- **外部成果是人工整理進情境檔的。** 他單位的光學、航拍成果目前由人整理成 `externalEvidence`，還沒有自動介接；發布時間只知道日期，一律視為當天 23:59 取得。雨量仍是缺口。
- **回放的分析窗格是事後選的。** 4 km 窗格以清冊壩址為中心；實際值班時窗格要由崩塌熱區或雨量警戒區決定。
- **SAR 面積偏低，不能直接算蓄水量。** 陡坡與雷達陰影遮罩仍擋掉約四成的湖面，候選範圍也混入部分山坡像元。
- **原蓄水量估計已撤下。** 先前「12,716 萬 m³、與官方誤差 39.7%」用的是 NDWI 最大連通塊 128 公頃，
  但該水體位於壩址下游，不是堰塞湖；與官方值接近屬巧合。`assess/scale.py` 的 ±40% 區間同樣以此為依據，需重新校正。
- **偵測時效受衛星重訪限制。** Sentinel-1 降軌約 6 天重訪；本案第一次過境時（36 小時）湖尚未成形，
  第 7 天可判 B 級、第 13 天複核後判 A 級。兩次觀測之間的狀況無法從 SAR 得知。
- **DEM 是事件前地形。** 崩塌改變地形後，新陡崖與陰影不在遮罩內，是本案誤報的主因。
- **後續擴充模組的限制**（決賽不展示）：暴露人口只涵蓋湖體本身、不是下游潰壩淹沒範圍；
  風險模型正樣本只有 12 筆、未留出驗證，且與 SAR 結果可能矛盾（儀表板上馬太鞍溪顯示「低風險」）；
  溢流預報只考慮溢頂，未涵蓋滑動與管湧等瞬間破壞。