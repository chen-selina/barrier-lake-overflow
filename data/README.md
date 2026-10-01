# data

- `raw/`：原始資料，小檔進版控
- `derived/`：中間產物，不進版控，可重新產生

## raw/

| 檔案 | 來源 | 說明 |
|---|---|---|
| `taiwan-barrier-lakes.csv` | 農業部農村發展及水土保持署 | 堰塞湖清冊，75 筆，1979–2026。座標是 TWD97 TM2（EPSG:3826），由 `pipeline/ingest/inventory.py` 轉成經緯度 |
| `observations.csv` | 團隊人工查證 | 每個湖一列的歷史雨量／颱風／地震觀測，來源寫在 `source` 欄。欄位說明見 `pipeline/ingest/observations.py` |
| `sentinel2/*.tif` | 自行從 GEE 匯出（不進版控） | 事件前後 NDWI，給 `scripts/analyze_ndwi_change.py` |
| `sentinel1/*.tif` | 自行從 GEE 匯出（不進版控） | 事件前後 σ⁰ VV 與 DEM，給 `scripts/analyze_sar_change.py` |
| `dem/DEM_matai_an.tif` | 自行從 GEE 匯出 NASADEM（不進版控） | 事件前地形，給 `scripts/run_hypsometry_real.py` |
| `boundaries/` | 內政部國土測繪中心村里界圖，data.gov.tw/dataset/7438（不進版控） | 全台 7,986 個村里，`VILLCODE` 欄位 |
| `population/` | SEGIS（segis.moi.gov.tw），不用登入（不進版控） | 114 年 12 月花蓮縣村里人口。路徑：資料集查詢下載 → 人口 → 縣市 → 村里別。`V_ID` 格式是 `10015120-004`，去掉連字號才對得上 `VILLCODE`，轉換寫在 `run_exposure_real.py` 的 `load_population()` |
| `risk/` | 舊版外部建模流程的輸出（已停用） | 係數現在寫在 `pipeline/ingest/risk.py`，這些檔案沒有程式讀取，只留著對照 |

GEE 匯出腳本寫在各支 script 的開頭。

## 重新產生

```bash
cd code
python -m pipeline.build_all          # 清冊、風險、成因敘述
python -m pipeline.build_all --live   # 風險改用 CWA 即時雨量（需 CWA_API_KEY）
```

## derived/

衛星影像、DEM 中間結果、風險模型的逐日特徵矩陣（例如 `feature_panel.csv`，26 MB）都放這裡，不進版控。

馬太鞍溪的真實分析結果也在這裡：

| 檔案 | 產生者 |
|---|---|
| `real_water_bl071.json` | `scripts/analyze_ndwi_change.py` |
| `real_hypsometry_bl071.json`、`real_backtest_bl071.md` | `scripts/run_hypsometry_real.py` |
| `real_exposure_bl071.json` | `scripts/run_exposure_real.py` |
| `cap-bl071.xml` | 儀表板手動下載 |
