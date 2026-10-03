@echo off
rem Live demo for judges. Run from the code folder:  scripts\demo_sar.bat
rem 1) re-run SAR analysis for 4 dates  2) print summary  3) make evidence images  4) open them
echo [1/3] Running SAR analysis (4 dates, same parameters)...
call scripts\run_sar_all.bat
echo.
echo [2/3] Summary
python scripts\show_sar_result.py
echo.
echo [3/3] Evidence images
python scripts\make_sar_evidence.py
start "" "..\docs\evidence\bl071_sar_0728.png"
start "" "..\docs\evidence\bl071_sar_0821.png"
