"""TokenMeter 配置字段示例；请通过设置窗口保存，不要复制真实凭据。"""

# DeepSeek API credentials
DEEPSEEK_API_KEY = ""  # 可选：官方 API Key，用于稳定的余额接口
DEEPSEEK_AUTH = ""  # 填入你的 Bearer token
DEEPSEEK_COOKIE = ""  # 填入你的 Cookie 字符串

# API base URL
DEEPSEEK_BASE = "https://platform.deepseek.com"

# 可选：按北京时间显示 DeepSeek 峰谷计价状态，仅提示、不参与账单计算
DEEPSEEK_PEAK_PRICING_ENABLED = False
DEEPSEEK_PEAK_PERIOD_1_START = "09:00"
DEEPSEEK_PEAK_PERIOD_1_END = "12:00"
DEEPSEEK_PEAK_PERIOD_2_START = "14:00"
DEEPSEEK_PEAK_PERIOD_2_END = "18:00"

# 小米 MiMo 控制台凭据
MIMO_COOKIE = ""  # 通常包含 serviceToken、userId、slh、ph
MIMO_API_PLATFORM_PH = ""  # 兼容旧配置；完整 Cookie 已包含时留空
MIMO_API_KEY = ""  # 推理 API Key；控制台用量查询不会使用
MIMO_BASE = "https://platform.xiaomimimo.com"

# Active provider: "deepseek" or "mimo"
ACTIVE_PROVIDER = "deepseek"

# Refresh interval in milliseconds
REFRESH_INTERVAL = 60_000  # 60 seconds
# Today intraday chart display interval in minutes; raw cache remains minute-level
MINUTE_USAGE_INTERVAL_MINUTES = 5
# Today intraday chart type: "bar" or "line"
MINUTE_USAGE_CHART_TYPE = "bar"
EDGE_HIDE_ENABLED = True

# Widget appearance
WIDGET_COMPACT_SIZE = 96
WIDGET_EXPANDED_SIZE = (820, 564)
BG_COLOR = "#071427"
ACCENT_COLOR = "#2f6fe4"
TEXT_COLOR = "#edf4ff"
