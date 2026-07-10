import threading
import os
from pathlib import Path
from unittest.mock import patch

os.environ["APPDATA"] = str(Path.cwd() / ".test-appdata")

from api import browser_cookie
from api.providers.deepseek import DeepSeekProvider


def test_deepseek_cookie_filter_keeps_only_first_party_domains():
    cookies = [
        {"name": "session", "value": "active", "domain": ".deepseek.com"},
        {"name": "platform", "value": "yes", "domain": "platform.deepseek.com"},
        {"name": "other", "value": "skip", "domain": "example.com"},
    ]

    value = browser_cookie.format_cookie_string(
        cookies,
        allowed_domains=("platform.deepseek.com", "deepseek.com"),
    )

    assert value == "session=active; platform=yes"


def test_deepseek_cookie_acquisition_keeps_bearer_token_separate():
    with patch("api.providers.deepseek.browser_cookie.acquire_cookie_via_chrome") as acquire:
        acquire.return_value = "session=active"
        result = DeepSeekProvider.acquire_cookie_via_chrome(threading.Event())

    assert result == "session=active"
    assert DeepSeekProvider.acquired_cookie_values(result) == {"COOKIE": "session=active"}
    assert acquire.call_args.kwargs["profile_name"] == "deepseek-chrome"
    assert acquire.call_args.kwargs["allowed_domains"] == ("platform.deepseek.com", "deepseek.com")
