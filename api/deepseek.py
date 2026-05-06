"""DeepSeek platform API client."""

import requests
from config import DEEPSEEK_BASE, DEEPSEEK_AUTH, DEEPSEEK_COOKIE

HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "authorization": DEEPSEEK_AUTH,
    "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "x-app-version": "20240425.0",
    "referer": "https://platform.deepseek.com/usage",
    "cookie": DEEPSEEK_COOKIE,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
}


def _get(path: str) -> dict:
    r = requests.get(f"{DEEPSEEK_BASE}{path}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()["data"]["biz_data"]


def get_user_summary() -> dict:
    """Fetch account overview: wallet balance, monthly tokens/cost."""
    return _get("/api/v0/users/get_user_summary")


def get_usage_amount(month: int, year: int) -> dict:
    """Fetch token usage breakdown (total + daily) for a given month."""
    return _get(f"/api/v0/usage/amount?month={month}&year={year}")


def get_usage_cost(month: int, year: int) -> dict:
    """Fetch cost breakdown in CNY (total + daily) for a given month.

    API returns biz_data as a list; we unwrap the first element.
    """
    result = _get(f"/api/v0/usage/cost?month={month}&year={year}")
    if isinstance(result, list):
        return result[0] if result else {}
    return result
