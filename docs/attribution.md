# attribution — 成因敘述與溢流預報

原始碼：`code/pipeline/attribution/`

用規則判斷加模板填空產生中文敘述，不用 LLM。每句話都要能對回是哪條規則、哪個門檻產生的。

## 結構

```
觀測資料 → rules.py → 命中規則＋槽位值 → compose.py → 中文敘述＋rules_fired
                                            ↑
                                      templates.yaml
```

| 檔案 | 做什麼 |
|---|---|
| `rules.py` | 門檻判斷，決定命中哪些規則 |
| `verbalize.py` | 數字轉中文（時長、雨量級距、規模） |
| `templates.yaml` | 句型。領域專家可以直接改，不用碰程式 |
| `compose.py` | 查句型、填槽、排語序，不含判斷 |
| `forecast.py` | 水量平衡與溢流時間 |
| `annotate.py` | 跑全清冊，把敘述寫回 `dashboard/data/lakes.js` |

測試在 `code/tests/test_attribution.py`（39 項）。

## 三條規則

1. **缺值就整句不出。** 任一槽位是 `None` 就丟掉那句，不會出現「達 None mm」。
2. **「無」和「未記載」分開。** 「無潰決紀錄」和「潰決原因未載」意思不同，見 `verbalize.absence()`。
3. **沒資料不推測。** 沒有雨量就不寫雨量；不知道颱風距離就不寫「外圍環流」。

## 用法

```bash
# 在 code/ 底下
python -m pipeline.attribution.annotate   # 全清冊加註
python -m pipeline.attribution.compose    # 示範
```

```python
from pipeline.attribution import LakeRecord, Observations, attribute, describe

rec = LakeRecord(seq=71, name="花蓮馬太鞍溪", cause="颱風",
                 event="薇帕颱風", duration="64", volume=9100.0,
                 status="監測中", landmark="林田山第118林班")
obs = Observations(typhoon_name="薇帕颱風", typhoon_distance_km=180.4,
                   rain_24h_mm=460.0, rain_percentile=99.4)

result = describe(attribute(rec, obs))
print(result.text)
print(result.rules_fired)
```

輸出：

> 本堰塞湖形成於薇帕颱風外圍環流影響期間，颱風中心最近距離約 180 公里，
> 上游集水區 24 小時累積雨量達 460 mm，達大豪雨標準（為該站有紀錄以來
> 前 1% 之強降雨），觸發林田山第118林班崩塌，堵塞馬太鞍溪，崩塌地與壩體
> 相距約 2,309 公尺，形成蓄水量約 9,100 萬立方公尺之極大型堰塞湖，
> 自形成迄今 64 日（約 2.1 個月），現況列為監測中。

不給 `obs` 的話，只會輸出不需要觀測資料的句子。

## 門檻

| 項目 | 門檻 | 來源 |
|---|---|---|
| 雨量分級 | 大雨 80／豪雨 200／大豪雨 350／超大豪雨 500 mm（24h） | 中央氣象署 |
| 颱風直接侵襲 | 中心距離 < 100 km | 自訂 |
| 颱風外圍環流 | 100–300 km | 自訂 |
| 西南氣流 | > 300 km 且西南風場顯著 | 自訂 |
| 地震關聯 | 形成於地震後 72 小時內、規模 ≥ 5.0 | 自訂 |
| 規模分級 | 小型 <100／中型 <1000／大型 <5000／極大型 ≥5000 萬 m³ | 自訂 |

自訂門檻在簡報中要註明。

## 溢流預報

```
剩餘容量 = V(壩頂高程) − V(目前水位)     V 由 DEM 水位–容積曲線查得
淨入流   = C · i · A − 滲流 − 蒸發       合理化公式
溢流時間 = 剩餘容量 / 淨入流
```

- **只給區間。** 低、中、高三個雨量情境各算一次，回報最早、中位、最晚。
- **逕流係數要列出來。** 震後裸露坡面可能從 0.5 升到 0.8 以上，是最大的不確定來源，
  每次輸出都附在 `Forecast.assumptions`。
- **不超出預報時距。** 超過就回報「時距內不致溢流」。

情境雨量應該用 CWA 的 QPF（預報），不是 QPE（觀測估計）。目前還沒接。

限制：Sentinel-1 約 6 天重訪，中間的水位全靠雨量推估，每次輸出都會附這句
（`templates.yaml` 的 `forecast.disclaimer`）。DEM 是事件前地形，河床改變與淤積會讓
蓄水量估算漂移，有新影像就要重新校正曲線。

## 觀測資料

`annotate.py` 從 `data/raw/observations.csv` 讀人工查證過的觀測值（見 `pipeline/ingest/observations.py`）。
目前只有馬太鞍溪有資料。之後如果接上可靠的 CWA 歷史資料，只要換掉讀取來源，
`rules.py` 和 `templates.yaml` 不用動。

## 為什麼用這三筆 2025 年紀錄測試

| | 草嶺清水溪 | 馬太鞍溪 | 燕子口 |
|---|---|---|---|
| 蓄水量 | 1,400 萬 m³ | 9,100 萬 m³ | 190 萬 m³ |
| 存續 | 2 日 | 64 日 | 9 日 |
| 潰決原因 | 溢流沖刷 | 溢流沖刷 | 機具開挖 |

前兩筆都是颱風型、溢流潰決，存續卻差三十倍，敘述要分得出來。
第三筆是人為開挖，不能寫成自然溢流。三點都有測試。
