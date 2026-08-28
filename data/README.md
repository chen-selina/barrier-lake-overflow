# data

```
data/
├── raw/       原始資料，小型 CSV 進版控
└── derived/   中繼產物，不進版控（可重新產生）
```

## raw/

| 檔案 | 來源 | 說明 |
|---|---|---|
| `taiwan-barrier-lakes.csv` | 農業部農村發展及水土保持署 | 堰塞湖清冊，75 筆、1979–2026 |
| `sentinel2/*.tif` | 使用者自行從 Google Earth Engine 匯出，**已 gitignore 不進版控** | 事件前後 NDWI GeoTIFF（`NDWI_before_matai_an.tif` / `NDWI_after_matai_an.tif`），供 `code/scripts/analyze_ndwi_change.py` 做真實水體變化偵測用。匯出腳本見該檔案開頭說明 |
| `dem/DEM_matai_an.tif` | 使用者自行從 Google Earth Engine 匯出 NASADEM，**已 gitignore 不進版控** | 事件前地形（基於 SRTM），供 `code/scripts/run_hypsometry_real.py` 做真實蓄水量反演。匯出腳本見該檔案開頭說明 |
| `boundaries/*.shp` 等 | 內政部國土測繪中心「村里界圖(TWD97經緯度)」（`data.gov.tw/dataset/7438`，免費直接下載，不用註冊），**已 gitignore 不進版控** | 全台 7,986 個村里界線，含 `VILLCODE` 代碼欄位，供 `code/scripts/run_exposure_real.py` 疊合真實水體範圍算暴露人口 |
| `population/` | SEGIS 社會經濟資料服務平台（`segis.moi.gov.tw`，開放資料、免登入即可下載，路徑：資料集查詢下載 → 類別選人口 → 空間範圍選縣市 → 空間統計單元選村里別），**已 gitignore 不進版控** | 114年12月（最新）花蓮縣村里級人口統計，`V_ID` 欄位格式是「鄉鎮碼-村里序」（例如 `10015120-004`），需去掉連字號才能對上村里界線圖的 `VILLCODE`——這個轉換已經寫在 `run_exposure_real.py` 的 `load_population()` 裡 |
| `observations.csv` | 團隊人工彙整（部分欄位已用公開新聞/官方資料查證填入，見檔案 `source` 欄） | 每個湖 id 一列的歷史觀測資料（雨量／颱風／地震），供 `code/pipeline/attribution/annotate.py` 產生更詳細的敘述；欄位說明見 `code/pipeline/ingest/observations.py` 檔頭 |
| `risk/lake_risk_predictions.csv` | 外部建模流程輸出快照（**已停用**） | 舊版 ERA5-Land 批次預測，`pipeline.ingest.risk` 已改用 package 版模型，不再讀取；保留供對照 |
| `risk/risk_formula_coefs.csv` | 同上（**已停用**） | 邏輯迴歸係數；係數本身跟 package 版一致，但已改為寫死在 `pipeline/ingest/risk.py`，不再讀此檔 |
| `risk/feature_importance.csv` | 同上（**已停用**） | 決策樹特徵重要性；package 版模型沒有對應的決策樹，目前無人讀取 |
| `risk/decision_rules.txt` | 同上（**已停用**） | 決策樹規則文字版；同上，目前無人讀取 |
| `risk/metrics.json` | 同上（**已停用**） | 模型後設資料；`nPositives=12` 等數字已內建於 `pipeline/ingest/risk.py` |

清冊原始座標為 **TWD97 TM2（EPSG:3826）**，不是經緯度，直接畫會落到
非洲外海。轉換由 `code/pipeline/ingest/inventory.py` 處理。

清冊更新後重跑：

```bash
cd code
python -m pipeline.ingest.inventory \
    ../data/raw/taiwan-barrier-lakes.csv dashboard/data/lakes.js
python -m pipeline.attribution.annotate
```

風險模型更新後重跑（產生 CAP 示警要用的 `dashboard/data/risk.js`）：

```bash
cd code
export CWA_API_KEY="CWA-你的授權碼"    # opendata.cwa.gov.tw 免費申請
python -m pipeline.ingest.risk         # 沒設金鑰會自動退回 offline 佔位
```

模型公式、係數、平均值都採用 package（`make_risk_snapshot.py`）版本，
直接寫在 `pipeline/ingest/risk.py` 裡；雨量特徵抓 CWA 即時觀測，
不再依賴上面標「已停用」的那幾份外部建模流程輸出。那幾份檔案還留在
`risk/` 底下供對照／歸檔，確定不需要可自行刪除，本專案不會自動清掉。

`risk/` 底下的檔案都很小（快照，非時序），可以進版控。**但風險模型
的逐日特徵矩陣（如 `feature_panel.csv`，215,117 列、26MB）屬於中繼產物，
放在 `derived/` 不進版控**——這是可重跑重新產生的東西，不是快照本身。

## derived/

衛星影像、DEM、中繼運算結果、風險模型的逐日特徵矩陣。**一律不進版控**
——單景 Sentinel-1 動輒數 GB，GitHub 單檔上限 100 MB。

其中 `real_water_bl071.json`（`scripts/analyze_ndwi_change.py` 產生）、
`real_exposure_bl071.json`（`scripts/run_exposure_real.py` 產生）、
`real_hypsometry_bl071.json` / `real_backtest_bl071.md`
（`scripts/run_hypsometry_real.py` 產生，B2/C2 真實蓄水量與誤差率）、
`cap-bl071.xml`（儀表板手動匯出）都是可以重新產生的中繼產物，內容是
馬太鞍溪的真實分析結果（非合成示範），對應的原始輸入檔案在
`data/raw/sentinel2/`、`data/raw/boundaries/`、`data/raw/population/`、
`data/raw/dem/`。
