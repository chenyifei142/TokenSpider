# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TokenSpider is a desktop floating-widget app for real-time monitoring of LLM API usage. It displays a draggable circle on the desktop — click to expand into a detail panel, right-click for menu. Auto-refreshes every 60s.

Currently integrates DeepSeek's platform API (3 endpoints: user summary, usage/amount, usage/cost).

## Environment

- Python virtual environment: `.venv/` — always activate before running: `source .venv/Scripts/activate`
- Install deps: `pip install -r requirements.txt`
- Run: `python main.py`

## Architecture

```
main.py                  # Entry point — creates FloatingWidget + SystemTray
config.py                # API credentials, refresh interval, UI colors/sizes
api/deepseek.py          # DeepSeek platform API client (3 endpoints)
data/store.py            # TokenData — fetches + aggregates all 3 API responses
ui/widget.py             # FloatingWidget (tkinter) — compact circle + expanded panel
ui/tray.py               # SystemTray (pystray) — tray icon with show/hide/refresh/quit
```

**Data flow:** `TokenData.fetch()` calls `api/deepseek` for the 3 DeepSeek endpoints, then aggregates today/week/month token counts and CNY costs from the daily breakdowns. The widget calls `refresh()` on a background thread every 60s and redraws.

**Widget:** Two modes — compact circle (~100px, shows today's cost) and expanded panel (~280x380, shows 8 stat rows). Drag to move, click to toggle modes, right-click for menu. Always-on-top via `wm_attributes("-topmost")`.

**API credentials** are in `config.py`. Rotation requires updating `DEEPSEEK_AUTH` and `DEEPSEEK_COOKIE`.

## Key Dependencies

- `tkinter` — built-in, for the floating widget UI
- `pystray` + `Pillow` — system tray icon
- `requests` — HTTP client for DeepSeek APIs
