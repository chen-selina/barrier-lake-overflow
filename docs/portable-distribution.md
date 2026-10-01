# 打包給沒裝 Python 的人

把 embeddable Python 放進專案資料夾，對方雙擊 `run_dashboard.bat` 就會重新產生資料並開啟儀表板。
以下設定只有打包的人要做一次，限 Windows。

如果對方只要看結果、不需要重新產生資料，就不用這麼麻煩：
直接把資料夾給他，開 `code/dashboard/index.html` 即可。

## 設定步驟

1. 到 <https://www.python.org/downloads/windows/> 下載 embeddable 版，
   檔名像 `python-3.12.x-embed-amd64.zip`（不是 `.exe` 安裝版）。
2. 解壓縮到專案根目錄，資料夾命名為 `python-embed`：

   ```
   barrier-lake-overflow/
   ├── python-embed/
   │   ├── python.exe
   │   ├── python312._pth
   │   └── ...
   ├── code/
   ├── data/
   └── run_dashboard.bat
   ```

3. 打開 `python-embed\python312._pth`，把 `#import site` 前面的 `#` 刪掉。
4. 下載 <https://bootstrap.pypa.io/get-pip.py> 放進 `python-embed\`，在那個資料夾執行：

   ```
   python.exe get-pip.py
   python.exe -m pip install pyproj PyYAML
   ```

   `pipeline` 本身不用裝，`run_dashboard.bat` 會把 `PYTHONPATH` 指到 `code/`。
5. 雙擊 `run_dashboard.bat`，跑完會自動開瀏覽器。能正常顯示就完成了。

## 給對方

把整個資料夾（含 `python-embed/`）壓縮，約多 30–40 MB。對方解壓縮後雙擊 `run_dashboard.bat`。

## 更新資料

1. 更新 `data/raw/` 底下的檔案
2. 自己跑一次 `run_dashboard.bat` 確認結果
3. 重新壓縮整包給對方
