<p align="center">
  <a href="./README.md">简体中文</a> |
  <a href="./README.en.md">English</a> |
  <a href="./README.zh-TW.md">繁體中文</a> |
  <a href="./README.ja.md">日本語</a> |
  <a href="./README.ko.md">한국어</a>
</p>

# TokenMeter

<p align="center">
  <strong>Windows AI Token 用量、费用与余额监控工具</strong><br>
  <sub>AI Token Usage, Cost & Balance Monitor for DeepSeek and Xiaomi MiMo.</sub>
</p>

TokenMeter 是一款轻量级 Windows 桌面 AI Token 用量监控工具，用于查看 DeepSeek、小米 MiMo 等平台的 Token 消耗、调用费用、账户余额和历史趋势。程序常驻系统托盘，通过悬浮球和展开面板提供 token usage tracker、AI cost monitor、balance monitor 与 Windows desktop widget 体验。

## 功能

- 支持 DeepSeek 与 Xiaomi MiMo，平台缓存互不混用。
- 悬浮球和系统托盘常驻，支持拖动、边缘吸附、位置记忆与失焦收起。
- 提供浅色、深色及跟随 Windows 的主题。
- 展示余额、Token 用量、费用趋势、模型统计、分时图和年度活跃热力图。
- DeepSeek 支持峰谷计价提示；MiMo Cookie 可通过专用 Chrome 会话获取和续期。
- 网络异常时保留最近成功数据；历史数据缓存在本地 SQLite。
- API Key、Bearer Token 和 Cookie 保存到 Windows 凭据管理器。
- 支持迁移应用数据目录、自动更新及单实例运行。

## 界面截图

| 浅色主题 | 深色主题 |
| --- | --- |
| ![TokenMeter 浅色主题](docs/images/token-spider-ui-v3-light.png) | ![TokenMeter 深色主题](docs/images/token-spider-ui-v3-dark.png) |

## 系统要求

- Windows 10 或 Windows 11；源码运行需要 Python 3.11+。
- DeepSeek 账户或 Xiaomi MiMo Token Plan 账户及对应 Cookie / Token。
- DeepSeek API Key 可选，用于官方余额接口。

> [!IMPORTANT]
> 用量数据依赖平台网页控制台接口；MiMo Cookie 需包含 `api-platform_ph`。平台接口或风控变化可能暂时影响数据。请仅使用自己的账户凭据并妥善保管。

## 下载

从 [GitHub Releases](https://github.com/zensoku142/TokenMeter/releases/latest) 下载 `TokenMeter-v{version}-windows-x64.exe`。便携版无需预装 Python；遇到 SmartScreen 提示时请先核对 `SHA256SUMS.txt`。

## 快速开始

```powershell
git clone https://github.com/zensoku142/TokenMeter.git
cd TokenMeter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## 首次配置

1. 启动程序并点击悬浮球展开面板。
2. 打开“设置”，选择 DeepSeek 或 Xiaomi MiMo。
3. 填写 Bearer Token、Cookie 或可选的 DeepSeek API Key。MiMo 可点击“一键获取 MiMo Cookie”，程序会自动提取 `api-platform_ph`。
4. 保存设置并刷新。默认刷新间隔为 60 秒。

`config.example.py` 仅展示配置项；无需复制为 `config.py`。旧版 `config.py` 会在首次启动时尝试迁移。

## 本地数据与隐私

为了兼容 TokenSpider 旧版本，TokenMeter 当前仍沿用 `%APPDATA%\TokenSpider` 作为默认数据目录。Windows 凭据管理器中的目标名仍以 `TokenSpider/` 开头，单实例锁仍为 `Local\TokenSpider.SingleInstance`；改名后无需重新登录。请勿手动删除或重命名该目录。将来若迁移到 `%APPDATA%\TokenMeter`，应由程序自动、事务式完成。

主要文件包括 `config.json`、`usage.db`、`widget-state.json` 和 `TokenSpider.log`。可在“设置 → 运行行为 → 应用数据目录”选择新的本地空目录，重启后完成事务式复制；不支持网络共享路径。敏感凭据不会写入 `config.json`。

## 自动更新

更新检查访问 `zensoku142/TokenMeter` 的 GitHub Releases。新版附件名为 `TokenMeter-*`，同时继续识别 `TokenSpider-*` 与 `TokenScope-*` 旧附件。若当前程序是 `TokenSpider.exe` 或 `TokenScope.exe`，更新会保留原稳定路径，避免旧快捷方式失效；版本化下载文件则迁移到 `TokenMeter.exe`。

## 测试

```powershell
python -m pytest -q
```

Qt 测试建议在可用的 Windows 桌面会话中运行。

## 构建

```powershell
python -m pip install pyinstaller
.\.venv\Scripts\pyinstaller.exe --clean --noconfirm TokenMeter.spec
python scripts/build_release.py
```

发布脚本生成 `dist\TokenMeter.exe`、`dist\TokenMeterUpdater.exe`、两个版本化附件及 `dist\SHA256SUMS.txt`。已验证发布环境为 Python 3.12、PyInstaller 6.21、PySide6 6.11；UPX 可选。

## 项目结构

```text
TokenMeter/
├── api/providers/       # DeepSeek 与 Xiaomi MiMo 适配器
├── data/                # 聚合与 SQLite 历史缓存
├── tests/               # 单元与 Qt 测试
├── ui/                  # PySide6 界面
├── app_identity.py      # 展示品牌与兼容身份
├── config_manager.py    # 配置、凭据与日志
├── main.py              # 应用入口
└── TokenMeter.spec      # PyInstaller 配置
```

## 故障排查

- 未配置：在设置中选择平台并填写凭据。
- 凭据失效：重新获取 Cookie；MiMo 会先尝试复用专用浏览器会话。
- 请求频繁或风控：等待后再刷新，不要持续缩短间隔。
- 数据未更新：查看 `%APPDATA%\TokenSpider\TokenSpider.log`。
- 未出现窗口：检查系统托盘；程序只允许一个实例。

## 版本与 Release

当前版本：`1.9.1`。更新记录及校验文件见 [GitHub Releases](https://github.com/zensoku142/TokenMeter/releases)。

## License

仓库当前未提供独立许可证文件；使用或分发前请联系项目维护者确认授权。
