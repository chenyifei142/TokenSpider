<p align="center">
  <a href="./README.md">简体中文</a> |
  <a href="./README.en.md">English</a> |
  <a href="./README.zh-TW.md">繁體中文</a> |
  <a href="./README.ja.md">日本語</a> |
  <a href="./README.ko.md">한국어</a>
</p>

# TokenMeter

<p align="center">
  <strong>Windows AI Token 用量、費用與餘額監控工具</strong><br>
  <sub>適用於 DeepSeek 與 Xiaomi MiMo 的 AI Token Usage, Cost & Balance Monitor。</sub>
</p>

TokenMeter 是輕量級 Windows 桌面 AI Token 用量監控工具，用於查看 DeepSeek、Xiaomi MiMo 的 Token 消耗、呼叫費用、帳戶餘額與歷史趨勢。程式常駐系統匣，提供浮動小工具與可展開的詳細面板。

## 功能

- 支援 DeepSeek 與 Xiaomi MiMo，各平台快取互不混用。
- 浮動小工具與系統匣常駐，支援拖曳、邊緣吸附、位置記憶及失焦收合。
- 提供淺色、深色及跟隨 Windows 的主題。
- 顯示餘額、Token 用量、費用趨勢、模型統計、分時圖與年度活躍熱力圖。
- DeepSeek 峰谷計價提示；MiMo Cookie 可透過專用 Chrome 工作階段取得與續期。
- 網路異常時保留最近成功資料；歷史資料快取於本機 SQLite。
- API Key、Bearer Token 與 Cookie 儲存於 Windows 認證管理員。
- 支援資料目錄遷移、自動更新及單一執行個體。

## 介面截圖

| 淺色主題 | 深色主題 |
| --- | --- |
| ![TokenMeter 淺色主題](docs/images/token-spider-ui-v3-light.png) | ![TokenMeter 深色主題](docs/images/token-spider-ui-v3-dark.png) |

## 系統需求

- Windows 10 或 Windows 11；從原始碼執行需要 Python 3.11+。
- DeepSeek 或 Xiaomi MiMo Token Plan 帳戶及對應 Cookie / Token。
- DeepSeek API Key 為選用，用於官方餘額端點。

> [!IMPORTANT]
> 用量資料依賴平台網頁控制台端點；MiMo Cookie 必須包含 `api-platform_ph`。平台 API 或風控變更可能暫時影響資料。請只使用自己的憑據並妥善保管。

## 下載

從 [GitHub Releases](https://github.com/zensoku142/TokenMeter/releases/latest) 下載 `TokenMeter-v{version}-windows-x64.exe`。可攜版不需預裝 Python；遇到 SmartScreen 提示時請先核對 `SHA256SUMS.txt`。

## 快速開始

```powershell
git clone https://github.com/zensoku142/TokenMeter.git
cd TokenMeter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## 首次設定

1. 啟動程式並點擊浮動小工具展開面板。
2. 開啟「設定」，選擇 DeepSeek 或 Xiaomi MiMo。
3. 填寫 Bearer Token、Cookie 或選用的 DeepSeek API Key。MiMo 的「一鍵取得 MiMo Cookie」會自動擷取 `api-platform_ph`。
4. 儲存並重新整理。預設重新整理間隔為 60 秒。

`config.example.py` 僅展示欄位，不必複製為 `config.py`。舊版 `config.py` 會在首次啟動時嘗試遷移。

## 本機資料與隱私

為相容 TokenSpider 舊版本，TokenMeter 目前仍使用 `%APPDATA%\TokenSpider` 作為預設資料目錄。Windows 認證管理員目標仍以 `TokenSpider/` 開頭，單一執行個體 Mutex 仍為 `Local\TokenSpider.SingleInstance`；改名後無需重新登入。請勿手動刪除或重新命名此目錄。未來若遷移到 `%APPDATA%\TokenMeter`，必須由程式自動且以交易方式完成。

主要檔案包括 `config.json`、`usage.db`、`widget-state.json` 與 `TokenSpider.log`。設定可在重新啟動後把全部資料移至新的本機空目錄；不支援網路共用路徑。敏感憑據不會寫入 `config.json`。

## 自動更新

更新檢查使用 `zensoku142/TokenMeter` 的 GitHub Releases。新附件使用 `TokenMeter-*`，同時仍辨識 `TokenSpider-*` 與 `TokenScope-*`。以 `TokenSpider.exe` 或 `TokenScope.exe` 執行時會保留原穩定路徑，確保舊捷徑有效；版本化下載檔則遷移為 `TokenMeter.exe`。

## 測試

```powershell
python -m pytest -q
```

Qt 測試建議在可用的 Windows 桌面工作階段中執行。

## 建置

```powershell
python -m pip install pyinstaller
.\.venv\Scripts\pyinstaller.exe --clean --noconfirm TokenMeter.spec
python scripts/build_release.py
```

發布腳本會產生 `dist\TokenMeter.exe`、`dist\TokenMeterUpdater.exe`、兩個版本化附件及 `dist\SHA256SUMS.txt`。已驗證環境為 Python 3.12、PyInstaller 6.21、PySide6 6.11；UPX 為選用。

## 專案結構

```text
TokenMeter/
├── api/providers/       # DeepSeek 與 Xiaomi MiMo 介接器
├── data/                # 聚合與 SQLite 歷史
├── tests/               # 單元與 Qt 測試
├── ui/                  # PySide6 介面
├── app_identity.py      # 顯示品牌與相容身分
├── config_manager.py    # 設定、憑據與記錄
├── main.py              # 程式進入點
└── TokenMeter.spec      # PyInstaller 設定
```

## 疑難排解

- 尚未設定：在設定中選擇平台並填入憑據。
- 憑據失效：重新取得 Cookie；MiMo 會先嘗試專用瀏覽器工作階段。
- 請求頻繁或風控：等待後再重新整理，不要持續縮短間隔。
- 資料未更新：檢查 `%APPDATA%\TokenSpider\TokenSpider.log`。
- 未出現視窗：檢查系統匣；程式只允許一個執行個體。

## 版本與 Release

目前版本：`1.9.1`。更新說明與校驗檔請見 [GitHub Releases](https://github.com/zensoku142/TokenMeter/releases)。

## License

儲存庫目前沒有獨立授權檔；使用或散布前請聯絡維護者確認授權。
