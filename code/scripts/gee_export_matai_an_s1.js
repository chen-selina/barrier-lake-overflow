// 馬太鞍溪（bl071）Sentinel-1 真實案例驗證：GEE 匯出腳本
// 在 code.earthengine.google.com 執行，Tasks 分頁逐一按 Run，匯出到 Google Drive，
// 下載後放到 data/raw/sentinel1/，再跑 code/scripts/run_sar_all.bat。
//
// 軌道選擇：升軌只有軌道 69（12 天重訪，形成後第一張 8/1，距形成 11 天）；
// 降軌軌道 105（6 天重訪，形成後第一張 7/22 21:52 UTC，距形成約 36 小時），故用降軌。
// 堰塞湖形成時間：2025-07-21 17:54（台灣）= 09:54 UTC。

var aoi = ee.Geometry.Point([121.29752, 23.70061]).buffer(5000).bounds();
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(aoi)
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
  .filterDate('2025-06-01', '2025-09-01');

// 列出每張影像的軌道號與時間（UTC），確認可用日期
print(s1.sort('system:time_start').toList(100).map(function (img) {
  img = ee.Image(img);
  return ee.Number(img.get('relativeOrbitNumber_start')).format('%d')
    .cat('   ').cat(img.date().format('YYYY-MM-dd HH:mm'));
}));

var orbit = 105;
var s = s1.filter(ee.Filter.eq('relativeOrbitNumber_start', orbit)).select('VV');

// 事件前：6/4～7/16 共 8 張取中位數（dB 中位數等同線性中位數，並壓低斑點雜訊）
var pre = s.filterDate('2025-06-01', '2025-07-18').median();

// 事件後：各期單張影像
function scene(day, nextDay) {
  return ee.Image(s.filterDate(day, nextDay).first());
}
var post0722 = scene('2025-07-22', '2025-07-23');   // 距形成約 36 小時
var post0728 = scene('2025-07-28', '2025-07-29');   // 約 7 天
var post0803 = scene('2025-08-03', '2025-08-04');   // 7/28 的複核期
var post0821 = scene('2025-08-21', '2025-08-22');
var post0827 = scene('2025-08-27', '2025-08-28');   // 8/21 的複核期

var dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation').resample('bilinear');

// 四張以上的圖必須同 region / scale / crs，analyze_sar_change.py 會檢查對齊
var opt = {crs: 'EPSG:4326', scale: 10, region: aoi, maxPixels: 1e9};
function exp(img, name) {
  Export.image.toDrive(Object.assign({image: img.toFloat(), description: name}, opt));
}
exp(pre,      'S1_VV_pre_matai_an');
exp(post0722, 'S1_VV_post_matai_an');      // 檔名沿用最初版本
exp(post0728, 'S1_VV_post2_matai_an');     // 7/22 的複核期；與下一行內容相同
exp(post0728, 'S1_VV_post0728_matai_an');
exp(post0803, 'S1_VV_post0803_matai_an');
exp(post0821, 'S1_VV_post0821_matai_an');
exp(post0827, 'S1_VV_post0827_matai_an');
exp(dem,      'NASADEM_matai_an');

// 目視檢查用圖層（水體為暗區）
var vis = {min: -25, max: 0};
Map.centerObject(aoi, 14);
Map.addLayer(pre, vis, 'pre 中位數');
Map.addLayer(post0722, vis, 'post 7/22');
Map.addLayer(post0728, vis, 'post 7/28');
Map.addLayer(post0821, vis, 'post 8/21');
Map.addLayer(post0827, vis, 'post 8/27');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoi).filterDate('2025-08-15', '2025-09-15')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)).median();
Map.addLayer(s2, {bands: ['B4', 'B3', 'B2'], min: 0, max: 3000}, 'S2 光學 8/15-9/15');
Map.addLayer(ee.Geometry.Point([121.29752, 23.70061]).buffer(60), {color: 'red'}, '壩址');
