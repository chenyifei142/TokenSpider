"""Runtime configuration loading, saving, validation, and rollback."""

from __future__ import annotations

import ast
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "DEEPSEEK_AUTH": "",
    "DEEPSEEK_COOKIE": "",
    "DEEPSEEK_BASE": "https://platform.deepseek.com",
    "REFRESH_INTERVAL": 60_000,
    "WIDGET_COMPACT_SIZE": 72,
    "WIDGET_EXPANDED_SIZE": (390, 710),
    "BG_COLOR": "#1a1a2e",
    "ACCENT_COLOR": "#4d7cff",
    "TEXT_COLOR": "#e0e0e0",
}

FIELD_META: dict[str, dict[str, Any]] = {
    "DEEPSEEK_AUTH": {"label": "Bearer Token", "kind": "text", "secret": True},
    "DEEPSEEK_COOKIE": {"label": "Cookie", "kind": "text", "secret": True, "multiline": True},
    "DEEPSEEK_BASE": {"label": "API 地址", "kind": "text"},
    "REFRESH_INTERVAL": {"label": "刷新间隔(毫秒)", "kind": "int", "min": 5_000},
    "WIDGET_COMPACT_SIZE": {"label": "悬浮球尺寸", "kind": "int", "min": 56, "max": 120},
    "WIDGET_EXPANDED_SIZE": {"label": "展开面板尺寸", "kind": "tuple_int"},
    "BG_COLOR": {"label": "背景色", "kind": "color"},
    "ACCENT_COLOR": {"label": "强调色", "kind": "color"},
    "TEXT_COLOR": {"label": "文本色", "kind": "color"},
}


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".tokenspider-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except Exception:
        return False


def config_dir() -> Path:
    base = app_dir()
    if not getattr(sys, "frozen", False):
        return base
    if (base / "config.py").exists() or _is_writable_dir(base):
        return base
    fallback_root = Path(os.environ.get("APPDATA", Path.home()))
    fallback = fallback_root / "TokenSpider"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


CONFIG_DIR = config_dir()
CONFIG_PATH = CONFIG_DIR / "config.py"
LOG_PATH = CONFIG_DIR / "TokenSpider.log"

_config: dict[str, Any] = DEFAULT_CONFIG.copy()
_logger_ready = False


def _logger() -> logging.Logger:
    global _logger_ready
    logger = logging.getLogger("TokenSpider.config")
    if not _logger_ready:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        _logger_ready = True
    return logger


def _parse_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.isupper():
                values[target.id] = ast.literal_eval(node.value)
    return values


def _validate_value(key: str, value: Any) -> Any:
    meta = FIELD_META.get(key, {"kind": "text"})
    kind = meta["kind"]
    if kind == "int":
        value = int(value)
        if "min" in meta and value < meta["min"]:
            raise ValueError(f"{key} 不能小于 {meta['min']}")
        if "max" in meta and value > meta["max"]:
            raise ValueError(f"{key} 不能大于 {meta['max']}")
        return value
    if kind == "tuple_int":
        if isinstance(value, str):
            parts = [p.strip() for p in value.replace("x", ",").split(",") if p.strip()]
            if len(parts) != 2:
                raise ValueError(f"{key} 必须是宽,高格式")
            value = (int(parts[0]), int(parts[1]))
        if (
            not isinstance(value, tuple)
            or len(value) != 2
            or not all(isinstance(v, int) for v in value)
        ):
            raise ValueError(f"{key} 必须是两个整数")
        if value[0] < 280 or value[1] < 360:
            raise ValueError(f"{key} 尺寸过小")
        return value
    if kind == "color":
        value = str(value).strip()
        if len(value) != 7 or not value.startswith("#"):
            raise ValueError(f"{key} 必须是 #RRGGBB 颜色")
        int(value[1:], 16)
        return value
    return str(value)


def validate_config(values: dict[str, Any]) -> dict[str, Any]:
    merged = DEFAULT_CONFIG.copy()
    merged.update(values)
    for key in list(merged):
        merged[key] = _validate_value(key, merged[key])
    if not str(merged["DEEPSEEK_BASE"]).startswith(("http://", "https://")):
        raise ValueError("DEEPSEEK_BASE 必须以 http:// 或 https:// 开头")
    return merged


def _format_value(value: Any) -> str:
    return repr(value)


def _render_config(values: dict[str, Any]) -> str:
    ordered = list(DEFAULT_CONFIG)
    extras = sorted(k for k in values if k not in DEFAULT_CONFIG)
    lines = [
        '"""TokenSpider runtime configuration.',
        "",
        "This file is safe to edit from the built-in settings panel.",
        '"""',
        "",
    ]
    for key in ordered + extras:
        lines.append(f"{key} = {_format_value(values[key])}")
    lines.append("")
    return "\n".join(lines)


def ensure_config_file() -> None:
    if CONFIG_PATH.exists():
        return
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(_render_config(DEFAULT_CONFIG), encoding="utf-8")
    _logger().info("Created default config at %s", CONFIG_PATH)


def load_config() -> dict[str, Any]:
    global _config
    ensure_config_file()
    try:
        values = _parse_config(CONFIG_PATH)
        _config = validate_config(values)
        return _config.copy()
    except Exception as exc:
        _logger().exception("Config load failed, using previous/default values: %s", exc)
        return _config.copy()


def get(key: str, default: Any = None) -> Any:
    return _config.get(key, default)


def all_config() -> dict[str, Any]:
    return _config.copy()


def save_config(values: dict[str, Any]) -> dict[str, Any]:
    global _config
    ensure_config_file()
    old_values = _parse_config(CONFIG_PATH)
    merged = old_values.copy()
    merged.update(values)
    validated = validate_config(merged)

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = CONFIG_PATH.with_suffix(f".py.bak-{stamp}")
    temp_path = CONFIG_PATH.with_suffix(".py.tmp")
    shutil.copy2(CONFIG_PATH, backup_path)

    try:
        temp_path.write_text(_render_config(validated), encoding="utf-8")
        validate_config(_parse_config(temp_path))
        temp_path.replace(CONFIG_PATH)
        _config = validated.copy()
        _logger().info("Config saved successfully. Backup: %s", backup_path.name)
        return _config.copy()
    except Exception as exc:
        if temp_path.exists():
            temp_path.unlink()
        shutil.copy2(backup_path, CONFIG_PATH)
        _config = validate_config(old_values)
        _logger().exception("Config save failed; rolled back to %s: %s", backup_path.name, exc)
        raise


load_config()
