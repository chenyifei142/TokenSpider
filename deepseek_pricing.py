"""DeepSeek peak-pricing schedule calculations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Mapping


BEIJING_TIMEZONE = timezone(timedelta(hours=8), "Asia/Shanghai")
TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")
PERIOD_KEYS = (
    ("DEEPSEEK_PEAK_PERIOD_1_START", "DEEPSEEK_PEAK_PERIOD_1_END"),
    ("DEEPSEEK_PEAK_PERIOD_2_START", "DEEPSEEK_PEAK_PERIOD_2_END"),
)


@dataclass(frozen=True, slots=True)
class PricingState:
    is_peak: bool
    label: str
    tooltip: str
    next_boundary: datetime


def parse_time_text(value: object) -> time:
    """Parse the persisted minute-precision format without accepting loose variants."""
    text = str(value).strip()
    if not TIME_PATTERN.fullmatch(text):
        raise ValueError("时间必须使用 HH:mm 格式")
    hour, minute = (int(part) for part in text.split(":"))
    return time(hour, minute)


def configured_periods(values: Mapping[str, object]) -> tuple[tuple[time, time], ...]:
    periods = tuple(
        (parse_time_text(values[start_key]), parse_time_text(values[end_key]))
        for start_key, end_key in PERIOD_KEYS
    )
    first, second = periods
    # The UI presents numbered daytime periods, so keep their order explicit instead
    # of silently sorting invalid input and showing a schedule the user did not enter.
    if first[0] >= first[1] or second[0] >= second[1]:
        raise ValueError("DeepSeek 高峰时段的开始时间必须早于结束时间")
    if first[1] > second[0]:
        raise ValueError("DeepSeek 高峰时段必须按时间顺序排列且不能重叠")
    return periods


def pricing_state(
    values: Mapping[str, object], now: datetime | None = None
) -> PricingState:
    periods = configured_periods(values)
    if now is None:
        current = datetime.now(BEIJING_TIMEZONE)
    elif now.tzinfo is None:
        current = now.replace(tzinfo=BEIJING_TIMEZONE)
    else:
        current = now.astimezone(BEIJING_TIMEZONE)

    today = current.date()
    boundaries = [
        (
            datetime.combine(today, start, BEIJING_TIMEZONE),
            datetime.combine(today, end, BEIJING_TIMEZONE),
        )
        for start, end in periods
    ]
    is_peak = False
    next_boundary: datetime | None = None
    for start, end in boundaries:
        if current < start:
            next_boundary = start
            break
        if start <= current < end:
            is_peak = True
            next_boundary = end
            break
    if next_boundary is None:
        tomorrow = today + timedelta(days=1)
        next_boundary = datetime.combine(tomorrow, periods[0][0], BEIJING_TIMEZONE)

    boundary_text = next_boundary.strftime("%H:%M")
    if is_peak:
        label = f"峰时 2× · {boundary_text} 结束"
    else:
        day_prefix = "明日 " if next_boundary.date() > today else ""
        label = f"平时 1× · {day_prefix}{boundary_text} 进入峰时"
    schedule = "、".join(
        f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}" for start, end in periods
    )
    tooltip = (
        f"{label}\n北京时间高峰时段：{schedule}\n"
        "高峰价适用所有计费项；本提示不参与账单计算。"
    )
    return PricingState(is_peak, label, tooltip, next_boundary)


__all__ = [
    "BEIJING_TIMEZONE",
    "PricingState",
    "configured_periods",
    "parse_time_text",
    "pricing_state",
]
