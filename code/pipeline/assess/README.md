# assess — 量化評估

| 檔案 | 內容 |
|---|---|
| `hypsometry.py` | 從壩址往上游填洼，建立水位–面積–容積曲線；用偵測面積反推水位；和官方蓄水量算誤差 |
| `scale.py` | 蓄水量 → 規模級距＋信心等級，對外用這個 |
| `inundation.py` | bathtub 淹沒範圍（和 hypsometry 共用填洼），輸出遮罩與多邊形 |
| `exposure.py` | 淹沒多邊形 × 村里界線 × SEGIS 人口，依面積比例算暴露人口；備案用 WorldPop 網格 |
| `backtest.py` | 偵測日期 vs 官方形成／溢流日期、蓄水量誤差率 |
| `dashboard_export.py` | 輸出 `dashboard/data/inundation.js` |

核心只用 numpy / scipy。讀 GeoTIFF 要 rasterio，做向量疊合要 geopandas / shapely。

真實資料的執行腳本在 `code/scripts/`（`run_hypsometry_real.py`、`run_exposure_real.py`）。

限制：淹沒只做 bathtub，不會往下游傳遞，所以暴露人口只涵蓋湖體本身。
