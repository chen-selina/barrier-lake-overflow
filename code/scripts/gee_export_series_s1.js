// 負案例／任意地點的 Sentinel-1 逐期匯出（GEE Code Editor 執行）
// 匯出：事件前中位數 1 張、DEM 1 張、事件後期間內同一軌道的每一張影像。
// 下載後放到 data/raw/sentinel1/，再跑：
//     python scripts/run_sar_series.py --name <NAME> --lon <LON> --lat <LAT> ...
//
// 預設是決賽建議的「2026 低災年」負案例：同一個馬太鞍溪窗格、同一組參數，
// 看 2026 年汛期系統會不會亂報。這個窗格崩塌地形仍新、陰影多，算是困難的負案例。
// 換地點只要改下面的參數。執行結果若出現高優先事件，那是需要查證的發現，
// 不要為了讓負案例「過關」回頭調參數。

var NAME        = 'neg2026_matai_an';           // 檔名前綴，也是 run_sar_series.py 的 --name
var CENTER      = [121.29752, 23.70061];        // 窗格中心（經度, 緯度）
var ORBIT_PASS  = 'DESCENDING';
var ORBIT       = 105;                          // 相對軌道號；換地點先看下方 print 的直方圖
var PRE_START   = '2026-03-01', PRE_END  = '2026-05-31';   // 事件前：取中位數
var POST_START  = '2026-06-01', POST_END = '2026-10-01';   // 事件後：逐張匯出

var aoi = ee.Geometry.Point(CENTER).buffer(5000).bounds();
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(aoi)
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.eq('orbitProperties_pass', ORBIT_PASS));
print('各軌道影像數', s1.filterDate(PRE_START, POST_END).aggregate_histogram('relativeOrbitNumber_start'));

var s = s1.filter(ee.Filter.eq('relativeOrbitNumber_start', ORBIT)).select('VV');
var pre = s.filterDate(PRE_START, PRE_END).median();
var posts = s.filterDate(POST_START, POST_END).sort('system:time_start');
var dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation').resample('bilinear');

// 所有圖同 region / scale / crs，analyze_sar_change.py 會檢查對齊
var opt = {crs: 'EPSG:4326', scale: 10, region: aoi, maxPixels: 1e9};
function exp(img, name) {
  Export.image.toDrive(Object.assign({image: img.toFloat(), description: name}, opt));
}
exp(pre, 'S1_VV_' + NAME + '_pre');
exp(dem, 'NASADEM_' + NAME);

// 逐日匯出（同一次過境可能有兩個相鄰 frame 都蓋到窗格，同日先 mosaic），檔名帶 UTC 日期。
// 過境時間（UTC）印在 Console，給 run_sar_series.py --pass-time 用。
posts.aggregate_array('system:time_start').evaluate(function (times) {
  var seen = {};
  times.forEach(function (t) {
    var dt = new Date(t);
    var day = dt.toISOString().slice(0, 10).replace(/-/g, '');
    if (seen[day]) return;
    seen[day] = true;
    print(day, dt.toISOString().slice(11, 16) + ' UTC');
    var start = ee.Date(t).update(null, null, null, 0, 0, 0);
    exp(posts.filterDate(start, start.advance(1, 'day')).mosaic(), 'S1_VV_' + NAME + '_' + day);
  });
});

var vis = {min: -25, max: 0};
Map.centerObject(aoi, 13);
Map.addLayer(pre, vis, '事件前中位數');
Map.addLayer(ee.Geometry.Point(CENTER).buffer(60), {color: 'red'}, '窗格中心');
