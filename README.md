# OSSInt 2026 · 堰塞湖快速評估系統

豪雨與颱風期間光學衛星常被雲遮住，本系統以 Sentinel-1 SAR 事件前後變化偵測，
回答災後第一時間的三個問題：**有沒有形成堰塞湖、在哪裡、規模與風險大約多大**。
偵測結果分 A/B/C 三級，附影像證據，交由值班人員確認是否啟動進一步查證。

開源空間資訊於國家韌性應用黑客松競賽（OSSInt 2026）· 災害防救賽道

## 目前進度

決賽聚焦「第一時間偵測與風險快篩」。下表上半部是決賽主線，下半部列為後續擴充、決賽不展示。

| 模組 | 狀態 |
|---|---|
| **SAR 變化偵測 → 新增水體／崩塌 → 疑似堰塞湖 A/B/C 判定** | **完成真實案例驗證**（馬太鞍溪，Sentinel-1 降軌 105，見下節） |
| 清冊轉換（TWD97 → WGS84） | 完成，75 筆 |
| 全台分布儀表板 | 完成；馬太鞍溪湖面範圍已改用 SAR 判定結果 |
| 成因歸因與敘述 | 完成，39 項測試 |
| 蓄水量規模級距＋信心等級 | **需重做**：原本的面積依據有誤（見「已知限制」） |
| 負案例驗證（大崩塌未成湖、豪雨無事件） | 尚未進行 |
| 水體萃取：光學 NDWI | 程式完成；馬太鞍溪的結果已撤下（偵測到的是壩址下游的水體，不是湖） |
| *後續擴充：* 溢流預報、雨量風險模型、淹沒範圍＋人口暴露、CAP 示警 | 程式保留，決賽不展示 |

### 馬太鞍溪（bl071）SAR 真實案例

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
| 只想看結果 | 直接開 `code/dashboard/index.html`，不用裝任何東西 |
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
pytest                                  # 151 項

python -m pipeline.build_all            # 清冊 → lakes.js、風險 → risk.js、加上成因敘述
python -m pipeline.build_all --live     # 風險改抓 CWA 即時雨量
```

`--live` 需要先設 `CWA_API_KEY`（opendata.cwa.gov.tw 免費申請）；沒設的話會退回佔位值，不會失敗。

各步驟也可以單獨跑：

```bash
python -m pipeline.ingest.inventory ../data/raw/taiwan-barrier-lakes.csv dashboard/data/lakes.js
python -m pipeline.attribution.annotate
python -m pipeline.ingest.risk            # 加 --offline 不連網
python -m pipeline.ingest.observations    # 看 observations.csv 填了幾筆
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

光學 NDWI（`scripts/analyze_ndwi_change.py`）與 DEM 蓄水量（`scripts/run_hypsometry_real.py`）的腳本保留，
但馬太鞍溪的結果因面積依據有誤已撤下。

## 目錄

```
code/
  pipeline/
    ingest/        清冊、CWA、風險模型、人工觀測
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

- **參數只用一個案例校準。** 坡度門檻 35° 由馬太鞍溪 8/27 選定；還沒有負案例驗證誤報率。
- **誤報複核後仍標 B 級。** 已複核但未持續的候選目前不會自動降級，值班時需看判定理由中的複核結果。
- **SAR 面積偏低，不能直接算蓄水量。** 陡坡與雷達陰影遮罩仍擋掉約四成的湖面，候選範圍也混入部分山坡像元。
- **原蓄水量估計已撤下。** 先前「12,716 萬 m³、與官方誤差 39.7%」用的是 NDWI 最大連通塊 128 公頃，
  但該水體位於壩址下游，不是堰塞湖；與官方值接近屬巧合。`assess/scale.py` 的 ±40% 區間同樣以此為依據，需重新校正。
- **偵測時效受衛星重訪限制。** Sentinel-1 降軌約 6 天重訪；本案第一次過境時（36 小時）湖尚未成形，
  第 7 天可判 B 級、第 13 天複核後判 A 級。兩次觀測之間的狀況無法從 SAR 得知。
- **DEM 是事件前地形。** 崩塌改變地形後，新陡崖與陰影不在遮罩內，是本案誤報的主因。
- **後續擴充模組的限制**（決賽不展示）：暴露人口只涵蓋湖體本身、不是下游潰壩淹沒範圍；
  風險模型正樣本只有 12 筆、未留出驗證，且與 SAR 結果可能矛盾（儀表板上馬太鞍溪顯示「低風險」）；
  CAP 為 demo，`status` 固定 `Test`；溢流預報只考慮溢頂，未涵蓋滑動與管湧等瞬間破壞。