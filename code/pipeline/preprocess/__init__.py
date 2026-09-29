"""
影像前處理。

- sar.py — Sentinel-1 σ⁰（dB）GeoTIFF 讀取、Lee speckle 濾波、網格對齊
  檢查。輻射／地形校正交給 Google Earth Engine 的 S1_GRD（不需 SNAP）。
- mask.py — 雷達陰影／疊置／陡坡遮罩（DEM 坡度坡向 + 入射角 + 視向）。
"""
