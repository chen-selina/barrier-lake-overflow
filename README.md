# OSSInt 2026 · 堰塞湖快速評估系統

地震或豪雨達門檻時，圈出高風險集水區、調度衛星影像，找出新生崩塌與河道上新增的水體，
用 DEM 估蓄水量與壩體規模，最後輸出可追溯依據的成因敘述與溢流預報。

開源空間資訊於國家韌性應用黑客松競賽（OSSInt 2026）· 災害防救賽道

## 目前進度

| 模組 | 狀態 |
|---|---|
| 清冊轉換（TWD97 → WGS84） | 完成，75 筆 |
| 全台分布儀表板 | 完成 |
| 成因歸因與敘述 | 完成，39 項測試 |
| 溢流預報（水量平衡） | 核心完成，還沒接 QPF |
| 風險模型（ERA5-Land 邏輯迴歸） | 71/75 筆有評估；雨量可抓 CWA 即時，或用訓練平均值佔位 |
| 歷史觀測（成因敘述用） | 人工彙整在 `data/raw/observations.csv`，目前只有馬太鞍溪填了查證過的數字 |
| 水體萃取：光學 NDWI | 完成，已對馬太鞍溪真實 Sentinel-2 影像跑過 |
| 水體萃取：SAR ＋崩塌偵測＋疑似堰塞湖分級 | 演算法完成（31 項測試，合成場景），**還沒跑過真實 Sentinel-1** |
| DEM 蓄水量估算 | 已對馬太鞍溪真實 NASADEM 跑過，對外報規模級距＋信心等級 |
| 淹沒範圍＋人口暴露 | 已接真實村里界線與 SEGIS 人口，但只算湖體本身（見「已知限制」） |
| CAP 示警 | demo，`status=Test` |

### 馬太鞍溪（bl071）真實資料結果

- **水體**：Sentinel-2 NDWI 事件前後比對，偵測到的新增水體多邊形已用在儀表板示警範圍與 CAP `<area>`。
- **蓄水量**：用偵測面積在 DEM 曲線上反推水位，估 12,716 萬 m³，官方 9,100 萬 m³，誤差 39.7%。
  換成級距（`assess/scale.py`）：估計區間 7,630～17,802 萬 m³，和官方值同屬「極大型」；
  信心「中」，因為面積只來自單期 NDWI。
  
  跑的時候遇到一個問題：事件前 DEM 上沒有崩塌堆積體，填洼會一路淹到下游河道。
  後來把壩址下游的像元遮掉，細節在 `scripts/run_hypsometry_real.py` 開頭。
- **暴露人口**：湖體範圍內約 9.5 人。這個數字不代表風險低，見下方限制。

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

### 真實影像分析

影像要自己從 Google Earth Engine 匯出。SAR 和 DEM 的 GEE 匯出腳本寫在對應程式的開頭。

```bash
# 光學：事件前後 NDWI
python scripts/analyze_ndwi_change.py \
    --before ../data/raw/sentinel2/NDWI_before_matai_an.tif \
    --after  ../data/raw/sentinel2/NDWI_after_matai_an.tif \
    --lon 121.29752 --lat 23.70061 --lake-id bl071 --threshold 0.0 \
    --out ../data/derived/real_water_bl071.json \
    --dashboard-out dashboard/data/inundation.js

# SAR：事件前、後、後續一期 σ⁰ VV，加同網格 DEM
python scripts/analyze_sar_change.py \
    --pre  ../data/raw/sentinel1/S1_VV_pre_matai_an.tif \
    --post ../data/raw/sentinel1/S1_VV_post_matai_an.tif \
    --post-later ../data/raw/sentinel1/S1_VV_post2_matai_an.tif \
    --dem  ../data/raw/sentinel1/NASADEM_matai_an.tif --orbit ASCENDING \
    --lon 121.29752 --lat 23.70061 --lake-id bl071 \
    --ndwi-json ../data/derived/real_water_bl071.json \
    --out ../data/derived/real_sar_bl071.json

python scripts/run_hypsometry_real.py   # 蓄水量
python scripts/run_exposure_real.py     # 暴露人口
```

跑完後 `code/dashboard/data/*.js` 就是最新資料，重新整理儀表板即可。

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

- **暴露人口只涵蓋湖體本身，不是下游潰壩淹沒範圍。** 真正的傷亡發生在下游：
  2025 年 9 月馬太鞍溪堰塞湖溢流，下游光復鄉 19 死 5 失蹤。要算下游需要一維河道洪水演算，
  目前沒有做。對外引用暴露人數時一定要附上這點。
- **風險模型**正樣本只有 12 筆，沒有留出驗證，所以 CAP 的 `certainty` 最高只給 `Possible`。
  模型本身不知道湖還在不在，`cap.js` 用清冊現況把關：已消失的不示警，已穩定的下修一級。
  拿掉這層的話，模型判高風險的 24 筆裡有 23 筆是已消失或已穩定的湖。
- **CAP** 是 demo，`status` 固定 `Test`。除了馬太鞍溪，`area` 都是壩址 3 km 圓。
- **SAR 鏈**還沒用真實影像驗證過；相干性法（SLC）沒有做。
- **Sentinel-1 約 6 天重訪**，兩次觀測之間的水位全靠雨量推估。
- **DEM 是事件前地形**，壩體形成後河床改變、湖區淤積，蓄水量估算會漂移，有新影像就要重新校正。
