# preprocess — SAR 前處理

輻射校正、地形校正交給 Google Earth Engine 的 `COPERNICUS/S1_GRD`，不用 SNAP。
這裡只做後續幾步，全部用 numpy / scipy：

- `sar.py`：讀 GeoTIFF（經緯度網格會換算成公尺）、dB ↔ 線性、Lee 濾波、網格對齊檢查
- `mask.py`：坡度坡向、雷達疊置／陰影、陡坡遮罩

山區最常見的誤判是陰影坡被當成水，所以判水前一定要先套 `mask.py` 的遮罩。
升軌視向約 77°、降軌約 283°，入射角取 39°。
