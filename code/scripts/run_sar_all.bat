@echo off
rem Run from the code folder:  scripts\run_sar_all.bat
rem Four dates, same parameters (slope 35 deg). Results: data\derived\final_*.json
set S=..\data\raw\sentinel1
set COMMON=--pre %S%\S1_VV_pre_matai_an.tif --dem %S%\NASADEM_matai_an.tif --orbit DESCENDING --lon 121.29752 --lat 23.70061 --lake-id bl071 --pre-label "pre 2025-06-04~07-16 median" --max-water-slope-deg 35 --debug-components

echo [1/4] 2025-07-22 (36 h) + 07-28 recheck
python scripts\analyze_sar_change.py %COMMON% --post %S%\S1_VV_post_matai_an.tif --post-later %S%\S1_VV_post2_matai_an.tif --post-label "post 2025-07-22 21:52 UTC" --out ..\data\derived\final_0722.json > ..\data\derived\final_0722.log 2>&1
echo [2/4] 2025-07-28 (7 days) + 08-03 recheck
python scripts\analyze_sar_change.py %COMMON% --post %S%\S1_VV_post0728_matai_an.tif --post-later %S%\S1_VV_post0803_matai_an.tif --post-label "post 2025-07-28 21:51 UTC" --out ..\data\derived\final_0728.json > ..\data\derived\final_0728.log 2>&1
echo [3/4] 2025-08-21 + 08-27 recheck
python scripts\analyze_sar_change.py %COMMON% --post %S%\S1_VV_post0821_matai_an.tif --post-later %S%\S1_VV_post0827_matai_an.tif --post-label "post 2025-08-21 21:51 UTC" --out ..\data\derived\final_0821.json > ..\data\derived\final_0821.log 2>&1
echo [4/4] 2025-08-27 single scene
python scripts\analyze_sar_change.py %COMMON% --post %S%\S1_VV_post0827_matai_an.tif --post-label "post 2025-08-27 21:52 UTC" --out ..\data\derived\final_0827.json > ..\data\derived\final_0827.log 2>&1

echo.
echo Done. Check data\derived\final_*.json (errors, if any, are in final_*.log)
