from datetime import datetime, timezone

import pytest

from deepseek_pricing import BEIJING_TIMEZONE, pricing_state


DEFAULTS = {
    "DEEPSEEK_PEAK_PERIOD_1_START": "09:00",
    "DEEPSEEK_PEAK_PERIOD_1_END": "12:00",
    "DEEPSEEK_PEAK_PERIOD_2_START": "14:00",
    "DEEPSEEK_PEAK_PERIOD_2_END": "18:00",
}


@pytest.mark.parametrize(
    ("clock", "is_peak", "label", "next_boundary"),
    (
        ("08:59", False, "平时 1× · 09:00 进入峰时", "09:00"),
        ("09:00", True, "峰时 2× · 12:00 结束", "12:00"),
        ("11:59", True, "峰时 2× · 12:00 结束", "12:00"),
        ("12:00", False, "平时 1× · 14:00 进入峰时", "14:00"),
        ("13:59", False, "平时 1× · 14:00 进入峰时", "14:00"),
        ("14:00", True, "峰时 2× · 18:00 结束", "18:00"),
        ("17:59", True, "峰时 2× · 18:00 结束", "18:00"),
        ("18:00", False, "平时 1× · 明日 09:00 进入峰时", "09:00"),
    ),
)
def test_default_peak_pricing_boundaries(clock, is_peak, label, next_boundary):
    hour, minute = (int(part) for part in clock.split(":"))
    now = datetime(2026, 7, 15, hour, minute, tzinfo=BEIJING_TIMEZONE)

    state = pricing_state(DEFAULTS, now)

    assert state.is_peak is is_peak
    assert state.label == label
    assert state.next_boundary.strftime("%H:%M") == next_boundary
    assert "北京时间高峰时段：09:00–12:00、14:00–18:00" in state.tooltip
    assert "本提示不参与账单计算" in state.tooltip


def test_peak_pricing_converts_aware_times_to_beijing_and_supports_custom_periods():
    values = {
        "DEEPSEEK_PEAK_PERIOD_1_START": "08:30",
        "DEEPSEEK_PEAK_PERIOD_1_END": "10:00",
        "DEEPSEEK_PEAK_PERIOD_2_START": "16:00",
        "DEEPSEEK_PEAK_PERIOD_2_END": "19:30",
    }

    state = pricing_state(values, datetime(2026, 7, 15, 0, 30, tzinfo=timezone.utc))

    assert state.is_peak
    assert state.label == "峰时 2× · 10:00 结束"
