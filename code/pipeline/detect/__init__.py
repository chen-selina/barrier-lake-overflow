"""
偵測。

- water.py — 水體萃取。光學 NDWI 半（Otsu／固定門檻）＋ SAR 低回波半
  （σ⁰ dB，Otsu 不合理時退回 −18 dB，吃陰影／疊置／陡坡遮罩），兩者都
  輸出 WaterExtent，共用 change_detection（新增水體）。
- landslide.py — 崩塌變化偵測：SAR 振幅比值法（GRD log-ratio）。
  相干性變化法（SLC）列為升級項目。
- barrier_lake.py — 疑似堰塞湖判定：新增水體 × 河道相交 × 鄰近崩塌
  （有 DEM 時要求崩塌到達湖底高程＝壩體在下游端）× 多時相持續，輸出
  A/B/C 信心分級；run_sar_chain() 一站式串起事件前後 SAR → 候選。

核心演算法只吃 numpy 陣列，不綁死 rasterio；合成資料測試見
code/tests/test_detect.py（NDWI）與 code/tests/test_sar.py（SAR 鏈）。
真實影像分析：scripts/analyze_ndwi_change.py（Sentinel-2）、
scripts/analyze_sar_change.py（Sentinel-1）。
"""
