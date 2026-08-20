"""
偵測。

- water.py — 已實作（僅光學 NDWI 半）。NDWI 二值化（Otsu 自動門檻或
  固定門檻）、事件前後變化偵測（新增水體）。SAR 低回波半（振幅比值 +
  雷達陰影遮罩）依可行性評估列入輔導期，暫不實作。
- landslide.py — 尚未實作（輔導期目標）。
- barrier_lake.py — 尚未實作（輔導期目標）。

water.py 只吃 numpy 陣列，不綁死 rasterio；真實 Sentinel-2 影像尚未
接上，目前用合成資料驗證邏輯正確性（見 code/tests/test_detect.py）。
"""
