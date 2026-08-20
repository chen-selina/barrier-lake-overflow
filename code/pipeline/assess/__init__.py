"""
量化評估。

- hypsometry.py — 已實作。DEM 填洼法建立水位–面積–容積曲線、壩高反演、
  對官方蓄水量數字算誤差率。
- inundation.py — 已實作。bathtub 淹沒模擬（與 hypsometry 共用同一套
  「連通填洼」核心演算法），一維水動力升級版留待輔導期。
- exposure.py — 已實作（僅人口疊加部分）。淹沒範圍 × 村里界線疊合、
  依覆蓋比例估算暴露人口；道路中斷／孤島化聚落判定依可行性評估
  結果不做。

三支都只依賴 numpy / scipy 做核心運算，geopandas / shapely 只在讀真實
向量資料、做疊合時才用得到（見 requirements.txt）。真實 DEM／村里界線圖
尚未接上，目前用合成資料驗證邏輯正確性（見 code/tests/test_assess.py）。
"""
