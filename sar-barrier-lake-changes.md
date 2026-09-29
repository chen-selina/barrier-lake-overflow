# SAR 變化偵測 → 新增水體／崩塌 → 疑似堰塞湖判定：修改紀錄

日期：2026-09-30

## 為什麼改

檢查時發現系統**做不到**「事件前後 SAR 變化偵測 → 新增水體／崩塌 → 疑似堰塞湖判定」：

- `detect/water.py` 只有光學 NDWI 半，SAR 半沒有實作。
- `detect/landslide.py`、`detect/barrier_lake.py` 只寫在 README 規劃裡，檔案不存在。
- `preprocess/` 是空的。
- `scripts/analyze_ndwi_change.py` 只做了簡化版判定：看最大連通塊離壩址多遠。它沒有看崩塌，沒有檢查是否跟河道相交，也不用 SAR。

## 改完後的流程

```
事件前／後 σ⁰（dB）─ Lee 濾波 ─┬─ 低回波判水（扣雷達陰影／疊置／陡坡）→ 新增水體
                               └─ 振幅比值 |Δσ⁰| ≥ 3 dB（扣水體、疊置、陰影）→ 崩塌
→ 每塊新增水體逐一評分：
    1. 河道相交（事件前水體 ∪ DEM D8 河網）
    2. 鄰近崩塌（有 DEM 時要求崩塌到達湖底高程＝壩體在下游端）
    3. 多時相持續（後續影像同位置 IoU ≥ 0.3）
→ A / B / C 信心分級
```

| 等級 | 條件 | 建議動作 |
|---|---|---|
| A | 河道相交 + 鄰近崩塌 + 多時相持續 | 立即通報 |
| B | 河道相交 + 鄰近崩塌（單期或未確認持續） | 排下一期影像複核 |
| C | 河道相交，附近沒有崩塌，或崩塌沒到河床 | 列觀察 |
| — | 不貼河道的新增水體 | 不列入 |

## 前處理策略

不用 SNAP，改在 Google Earth Engine 取 `COPERNICUS/S1_GRD` 匯出 GeoTIFF。GEE 已經做完軌道修正、熱雜訊去除、輻射校正與地形校正，並轉成 dB。Python 端只補做 Lee 濾波、幾何遮罩和網格對齊檢查，全部用 numpy/scipy 實作，不需要 SNAP 或 scikit-image。

## 新增檔案

| 檔案 | 內容 |
|---|---|
| `code/pipeline/preprocess/sar.py` | `load_s1_geotiff`（地理座標會依緯度把經向像元換成公尺）、`db_to_linear`／`linear_to_db`、`lee_filter`（乘性雜訊 Lee 濾波，ENL 4.4，在線性功率域計算，nan 不參與鄰域統計）、`check_aligned`（尺寸／transform／CRS 不一致就丟錯，不做隱性 resample） |
| `code/pipeline/preprocess/mask.py` | `slope_aspect`、`range_slope_deg`、`layover_shadow_mask`（距離向坡度 > 入射角判為疊置，< 入射角 − 90° 判為陰影）、`steep_slope_mask`、`sar_invalid_masks`（水體遮罩＝疊置、陰影、陡坡 > 20°、nodata；崩塌遮罩不排除陡坡）。升軌視向約 77°，降軌約 283°，入射角取 39° |
| `code/pipeline/detect/landslide.py` | `log_ratio`、`remove_small_components`、`detect_landslides`（\|Δσ⁰\| ≥ 3 dB，增強與減弱兩側都算並記錄正負號）、`LandslideResult` |
| `code/pipeline/detect/barrier_lake.py` | `flow_accumulation_d8`、`river_mask`、`classify`（逐塊評分，輸出 `Candidate` 並附中文判定理由）、`run_sar_chain`（一站式串起整條流程）、`synthetic_scene`（示範與測試共用的合成山谷） |
| `code/scripts/analyze_sar_change.py` | 真實影像一次性分析腳本：檔頭附 GEE 匯出腳本，流程為裁視窗 → `run_sar_chain`。輸出每個候選的經緯度、與壩址距離、湖面多邊形；給 `--ndwi-json` 時跟光學結果比對面積 |
| `code/tests/test_sar.py` | 31 項測試，涵蓋 Lee 濾波、對齊檢查、幾何遮罩、SAR 判水、崩塌偵測、D8、A/B/C 判定 |

## 修改檔案

| 檔案 | 改了什麼 |
|---|---|
| `code/pipeline/detect/water.py` | 新增 `sar_water_mask`、`extract_water_sar`。預設用 Otsu 門檻；Otsu 高於 −14 dB 時，代表切到的是陸地內部兩群，退回固定 −18 dB。兩半都輸出 `WaterExtent`，共用 `change_detection`。另外更新了檔頭說明 |
| `code/pipeline/detect/__init__.py`、`detect/README.md` | 更新模組狀態、分級表、已知限制 |
| `code/pipeline/preprocess/__init__.py` | 由「尚未實作」改成模組說明 |
| `code/scripts/analyze_ndwi_change.py` | `crop_window` 加上 `key` 參數（預設 `"ndwi"`，行為不變），讓 SAR 腳本可以共用 |
| `requirements.txt` | 註明 SAR 鏈不需要 SNAP 或 scikit-image，沒有新增依賴 |
| `README.md` | 更新狀態表、測試數（改為 143 項）、執行指令與目錄結構 |

## 開發過程中修掉的問題

1. **湖被原河道切成兩半。** 原河道是事件前水體，`change_detection` 會把它扣掉，同一座湖因此變成兩個候選。現在 `classify` 會先把新增水體外擴 3 像元再做連通分析。面積仍只算新增水體。
2. **湖岸冒出假崩塌。** 濾波後水陸交界像元的回波掉了好幾 dB，但沒被判成水，於是沿湖岸出現一圈假崩塌。這圈假崩塌又讓「崩塌只在山坡上」的情境被誤判成壩體。現在把水體外擴 2 像元後從崩塌中排除。
3. **窄河道被濾波抹細。** 用 5×5 Lee 濾波時，3 像元寬的河道邊緣會升到門檻以上，湖裡的原河道就被當成新增水體。現在水體改用 3×3 視窗，崩塌維持 5×5：崩塌的 3 dB 門檻需要較強的雜訊抑制。

## 驗證

- `pytest`：143 項全部通過，原本 112 項，新增 31 項。
- 合成場景四種情境的判定都正確：
  - 崩塌堵河、兩期持續：A
  - 只有單期：B
  - 沒有崩塌：C
  - 崩塌只在湖面以上：C
- 跟河道不相連的積水不會列入候選。
- 20 組隨機 speckle 種子 × 5 種情境，每次都只產生 1 個候選，分級正確。
- 把合成場景寫成 EPSG:4326 GeoTIFF 跑 `analyze_sar_change.py`，有 DEM 時得到 A，沒有 DEM 時得到 B（壩體位置無法判斷）；NDWI 交叉比對也有輸出。

## 還沒做／已知限制

- **尚未用真實 Sentinel-1 影像跑過。** 下一步是照 `analyze_sar_change.py` 檔頭的 GEE 腳本匯出馬太鞍溪（bl071）的資料，再執行一次。
  - GEE 腳本裡的 `orbit = 69` 是佔位值，要換成實際印出來、事件前後都有影像的軌道號。
  - `data/derived/real_water_bl071.json` 目前不在本機，光學與 SAR 的交叉比對要等它回來才能做。
- 陰影與疊置只做局部坡面判定，沒有沿距離向射線追蹤，被遠處山脊擋住的陰影抓不到。
- 坡度超過 20° 一律不當水，所以貼著陡峭山壁的湖緣面積會低估。
- D8 河網沒有先填窪，窪地會截斷流量累積。
- 崩塌落在疊置或陰影區時偵測不到，湖會降為 C 級。這種情況要靠升降軌互補或光學影像補足。
- 相干性變化法（SLC／InSAR）列為升級項目。

## 執行方式

```bash
cd code
pytest                                   # 143 項
python -m pipeline.detect.landslide      # 崩塌偵測示範
python -m pipeline.detect.barrier_lake   # 四種合成情境的 A/B/C 判定

python scripts/analyze_sar_change.py \
    --pre  ../data/raw/sentinel1/S1_VV_pre_matai_an.tif \
    --post ../data/raw/sentinel1/S1_VV_post_matai_an.tif \
    --post-later ../data/raw/sentinel1/S1_VV_post2_matai_an.tif \
    --dem  ../data/raw/sentinel1/NASADEM_matai_an.tif --orbit ASCENDING \
    --lon 121.29752 --lat 23.70061 --lake-id bl071 \
    --ndwi-json ../data/derived/real_water_bl071.json \
    --out ../data/derived/real_sar_bl071.json
```
