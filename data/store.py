"""Data model and aggregation."""

from datetime import date, timedelta
from typing import Any

import api.deepseek as ds


def _safe_float(v: Any) -> float:
    return float(v) if v else 0.0


def _safe_int(v: Any) -> int:
    return int(v) if v else 0


def _sum_item_usage(item: dict, token_type: str) -> float:
    """Sum a specific usage type from a single item dict."""
    total = 0.0
    for u in item.get("usage", []):
        if u["type"] == token_type:
            total += _safe_float(u["amount"])
    return total


def _sum_all_items(items: list, token_type: str) -> float:
    """Sum a specific usage type across a list of item dicts."""
    return sum(_sum_item_usage(item, token_type) for item in items)


def _total_tokens_in_item(item: dict) -> float:
    return (
        _sum_item_usage(item, "PROMPT_CACHE_HIT_TOKEN")
        + _sum_item_usage(item, "PROMPT_CACHE_MISS_TOKEN")
        + _sum_item_usage(item, "RESPONSE_TOKEN")
    )


class TokenData:
    """Aggregated view of DeepSeek usage data."""

    def __init__(self):
        self.balance_cny: float = 0.0
        self.balance_tokens: int = 0
        self.monthly_usage_tokens: int = 0
        self.monthly_cost_cny: float = 0.0
        self.today_tokens: int = 0
        self.today_cost_cny: float = 0.0
        self.weekly_tokens: int = 0
        self.weekly_cost_cny: float = 0.0
        self.total_cost_cny: float = 0.0
        self.per_model_amount: list = []
        self.per_model_cost: list = []
        self.last_updated: str = ""

    @classmethod
    def fetch(cls) -> "TokenData":
        data = cls()
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        week_start = today - timedelta(days=today.weekday())

        # 1. User summary
        try:
            summary = ds.get_user_summary()
            for w in summary.get("normal_wallets", []):
                if w["currency"] == "CNY":
                    data.balance_cny = _safe_float(w["balance"])
                    data.balance_tokens = _safe_int(w["token_estimation"])
            data.monthly_cost_cny = _safe_float(
                summary.get("monthly_costs", [{}])[0].get("amount", 0)
            )
            data.monthly_usage_tokens = _safe_int(
                summary.get("monthly_token_usage", 0)
            )
        except Exception:
            pass

        # 2. Usage amount (tokens)
        try:
            amount = ds.get_usage_amount(today.month, today.year)
            data.per_model_amount = amount.get("total", [])

            for day_entry in amount.get("days", []):
                try:
                    d = date.fromisoformat(day_entry["date"])
                except (ValueError, KeyError):
                    continue

                for item in day_entry.get("data", []):
                    tokens = _total_tokens_in_item(item)
                    if d == today:
                        data.today_tokens += int(tokens)
                    if week_start <= d <= today:
                        data.weekly_tokens += int(tokens)
        except Exception:
            pass

        # 3. Usage cost (CNY)
        try:
            cost = ds.get_usage_cost(today.month, today.year)
            data.per_model_cost = cost.get("total", [])

            for day_entry in cost.get("days", []):
                try:
                    d = date.fromisoformat(day_entry["date"])
                except (ValueError, KeyError):
                    continue

                for item in day_entry.get("data", []):
                    cost_cny = _total_tokens_in_item(item)
                    if d == today:
                        data.today_cost_cny += cost_cny
                    if week_start <= d <= today:
                        data.weekly_cost_cny += cost_cny
        except Exception:
            pass

        data.total_cost_cny = data.monthly_cost_cny

        from datetime import datetime
        data.last_updated = datetime.now().strftime("%H:%M:%S")
        return data
