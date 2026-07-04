# TokenSpider

<p align="center">
  <strong>DeepSeek Token 用量监控桌面悬浮窗</strong><br>
  <sub>在 Windows 桌面实时查看余额、Token 用量、费用趋势与年度活跃记录</sub>
</p>

<p align="center">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&amp;logoColor=white">
  <img alt="Windows 10/11" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4?logo=windows&amp;logoColor=white">
  <img alt="Version 1.0.0" src="https://img.shields.io/badge/version-1.0.0-2f6fe4">
</p>

TokenSpider 是一个面向 Windows 的 DeepSeek 用量监控工具。程序常驻系统托盘，以悬浮球展示核心数据；点击后可展开完整面板，查看余额、今日与本周用量、费用趋势、模型统计和过去一年的活跃热力图。

## 功能

- 悬浮球与系统托盘常驻，支持自由拖动、边缘吸附和位置记忆
- 展示账户余额、余额可用 Token、本月 Token 用量和累计费用
- 统计今日、本周及各模型的 Token 用量与费用
- 绘制每日费用趋势和过去一年的 Token 活跃热力图
- 每 60 秒自动刷新，也可从界面手动刷新
- 网络或接口异常时保留最近一次成功数据，并显示明确的错误状态
- 将历史账单缓存在本地 SQLite 数据库，分批补全过去一年的记录
- 将 API Key、Bearer Token 和 Cookie 保存到 Windows 凭据管理器
- 单实例运行，避免重复启动多个悬浮窗

## 运行要求

- Windows 10 或 Windows 11
- Python 3.11 或更高版本
- DeepSeek 账户
- Bearer Token 或 Cookie，用于读取平台用量数据
- DeepSeek API Key（可选），用于通过官方接口读取账户余额

> [!IMPORTANT]
> 用量明细依赖 DeepSeek 平台的非公开接口。平台接口、鉴权方式或风控策略发生变化时，部分数据可能暂时无法读取。请仅使用自己的账户凭据，并妥善保管相关信息。

## 快速开始

在 PowerShell 中执行：

```powershell
git clone https://github.com/chenyifei142/TokenScope.git
cd TokenScope

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

如果 PowerShell 不允许激活虚拟环境，可以直接使用虚拟环境中的 Python：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## 首次配置

1. 启动程序，点击悬浮球展开面板。
2. 打开“设置”。
3. 填写 Bearer Token 或 Cookie；如有官方 API Key，也可一并填写。
4. 保存设置并执行刷新。

默认 API 地址为 `https://platform.deepseek.com`，默认刷新间隔为 60 秒。设置窗口还可以调整刷新间隔、悬浮球尺寸、面板尺寸和界面颜色。

仓库中的 [`config.example.py`](config.example.py) 仅用于展示可配置项。新版程序会自动生成运行时配置，无需将其复制为 `config.py`。如果程序目录中存在旧版 `config.py`，首次启动时会尝试迁移配置并移除其中的明文凭据。

## 本地数据与安全

程序数据默认保存在 `%APPDATA%\TokenSpider`：

| 文件 | 用途 |
| --- | --- |
| `config.json` | 非敏感设置，不包含 API Key、Token 或 Cookie |
| `usage.db` | 本地用量与费用历史缓存 |
| `widget-state.json` | 悬浮球位置 |
| `TokenSpider.log` | 运行日志，单文件最大 2 MB，最多保留 3 个备份 |

敏感凭据保存在 Windows 凭据管理器中，目标名称以 `TokenSpider/` 开头。保存新设置前，程序会备份普通配置；写入失败时会回滚凭据，避免新旧配置混用。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Qt 测试会创建界面组件，建议在可用的 Windows 桌面会话中运行。

## 构建 Windows 可执行文件

项目提供了 PyInstaller 配置：

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\pyinstaller.exe --clean TokenSpider.spec
```

构建产物位于 `dist\TokenSpider.exe`。`build*` 和 `dist*` 目录已被 Git 忽略。

## 项目结构

```text
TokenSpider/
├── api/                 # DeepSeek 官方与平台接口适配器
├── data/                # 数据聚合、SQLite 历史缓存
├── tests/               # 单元测试与 Qt 界面测试
├── ui/                  # PySide6 悬浮球、面板、设置与托盘界面
├── config_manager.py    # 配置、凭据迁移与日志管理
├── config.example.py    # 配置项示例
├── main.py              # 应用入口与单实例控制
├── TokenSpider.spec     # PyInstaller 构建配置
└── requirements.txt     # Python 依赖
```

## 故障排查

- **提示尚未配置**：在设置中填写 Bearer Token 或 Cookie。
- **提示凭据失效**：重新获取并保存当前账户的 Token 或 Cookie。
- **提示请求过于频繁或平台风控拒绝请求**：等待一段时间后再手动刷新；不要持续缩短刷新间隔。
- **数据暂时没有更新**：程序会继续显示上一次成功获取的缓存，可查看 `%APPDATA%\TokenSpider\TokenSpider.log` 获取详细信息。
- **程序没有出现窗口**：检查系统托盘；TokenSpider 只允许一个实例运行。

## 版本

当前版本：`1.0.0`
