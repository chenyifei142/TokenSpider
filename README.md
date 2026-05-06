# TokenSpider

桌面悬浮窗应用，实时监控 LLM API 使用量和费用。在桌面上显示一个可拖拽的圆形窗口，点击展开详情面板，右键弹出菜单，每 60 秒自动刷新。

当前对接 DeepSeek 开放平台 API。

## 功能

- **紧凑视图** — 显示钱包余额、今日费用、本周费用、预算进度条
- **展开面板** — 完整数据明细：预算仪表盘、各维度用量、模型级费用拆解
- **系统托盘** — 托盘图标，右键菜单支持刷新、展开/收起、退出
- 窗口可拖拽、可缩放、始终置顶

## 快速开始

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows
pip install -r requirements.txt
python main.py
```

## 配置

编辑 `config.py`，填入 DeepSeek 平台的 API 凭证（Bearer Token 和 Cookie），以及刷新间隔等参数。

## 项目结构

```
main.py       入口
config.py     配置（凭证、刷新间隔、颜色尺寸）
api/          DeepSeek 平台 API 客户端（3 个接口）
data/         数据获取与聚合
ui/           tkinter 悬浮窗 + pystray 系统托盘
```
