from __future__ import annotations

import datetime as dt
from typing import Iterable

from .models import Candle, Zone
from .indicators import sma


# ---------------------------------------------------------------------------
# Golden Pocket math
# ---------------------------------------------------------------------------
# This is the math encoded by the supplied Pine source:
#   midpoint = low + range * 0.559
#   fixed half-height = ADR10 * (zone_height_pct / 100) / 2
#   eligibility = candle_range / ADR10 >= min_candle_size_pct
#   strength = 4..10 using the Pine thresholds
#
# The scanner applies that same calculation independently to the manually
# selected source timeframes:
#   12M, 6M, 3M, 1M, 1W, 1D
#
# 12M/6M/3M are constructed from Binance 1M candles because Binance does
# not provide native 3M/6M/12M Spot klines.


def strength_rating(candle_range: float, adr: float) -> int:
    if adr <= 0:
        return 0
    pct = candle_range / adr * 100.0
    if pct >= 160:
        return 10
    if pct >= 140:
        return 9
    if pct >= 120:
        return 8
    if pct >= 100:
        return 7
    if pct >= 80:
        return 6
    if pct >= 60:
        return 5
    return 4


def _month_key(open_time_ms: int) -> tuple[int, int]:
    d = dt.datetime.fromtimestamp(open_time_ms / 1000, dt.timezone.utc)
    return d.year, d.month


def _add_months(year: int, month: int, count: int) -> tuple[int, int]:
    n = year * 12 + (month - 1) + count
    return n // 12, n % 12 + 1


def aggregate_monthly(monthly: list[Candle], months: int) -> list[Candle]:
    """Aggregate 1M candles into N-month candles.

    Important TradingView behavior:
    the *current* higher-timeframe candle is allowed to be incomplete.
    Older groups must be contiguous/full. This matters for the live 6M/12M
    candle: the current 12M candle can be only 8 months old in August and
    still exists on a TradingView 12M chart.

    Groups are anchored to calendar boundaries:
      1M: Jan
      3M: Jan/Apr/Jul/Oct
      6M: Jan/Jul
      12M: Jan
    """
    if months <= 0:
        raise ValueError("months must be > 0")

    if not monthly:
        return []

    ordered = sorted(monthly, key=lambda c: c.open_time)
    groups: dict[tuple[int, int], list[Candle]] = {}

    for c in ordered:
        year, month = _month_key(c.open_time)
        start_month = ((month - 1) // months) * months + 1
        groups.setdefault((year, start_month), []).append(c)

    keys = sorted(groups)
    out: list[Candle] = []

    for pos, key in enumerate(keys):
        group = groups[key]
        year, start_month = key

        # Verify there are no missing months inside this group.
        expected = [_add_months(year, start_month, i) for i in range(len(group))]
        actual = [_month_key(c.open_time) for c in group]
        contiguous = actual == expected

        if not contiguous:
            continue

        is_last = pos == len(keys) - 1
        complete = len(group) == months

        # Historical groups need all N months. The current group may be
        # partial because its TradingView higher-timeframe candle is still open.
        if not complete and not is_last:
            continue

        out.append(
            Candle(
                open_time=group[0].open_time,
                open=group[0].open,
                high=max(c.high for c in group),
                low=min(c.low for c in group),
                close=group[-1].close,
                volume=sum(c.volume for c in group),
            )
        )

    return out


def _merge_overlapping_pine_style(zones: list[Zone]) -> list[Zone]:
    """Merge zones using the supplied Pine script's overlap rules.

    The Pine implementation processes zones in source order and merges a
    later overlapping zone into the current zone, retaining:
      - maximum upper/lower envelope
      - maximum strength
      - maximum age
      - earliest start time
      - earliest source index

    We intentionally do not add extra 'smart' merging rules here.
    """
    if not zones:
        return []

    merged: list[Zone] = []
    consumed = [False] * len(zones)

    for i in range(len(zones)):
        if consumed[i]:
            continue

        z = zones[i]
        upper, lower = z.upper, z.lower
        strength = z.strength
        age = z.age
        start_time = z.start_time
        source_index = z.source_index

        for j in range(i + 1, len(zones)):
            if consumed[j]:
                continue

            q = zones[j]
            overlaps = not (upper < q.lower or q.upper < lower)
            if not overlaps:
                continue

            upper = max(upper, q.upper)
            lower = min(lower, q.lower)
            strength = max(strength, q.strength)
            age = max(age, q.age)
            start_time = min(start_time, q.start_time)
            source_index = min(source_index, q.source_index)
            consumed[j] = True

        merged.append(
            Zone(
                source_tf=z.source_tf,
                upper=upper,
                lower=lower,
                strength=strength,
                age=age,
                start_time=start_time,
                source_index=source_index,
            )
        )

    return merged


def construct_zones(
    candles: list[Candle],
    tf: str,
    lookback: int = 20,
    height_pct: float = 3.0,
    min_size_pct: float = 60.0,
) -> list[Zone]:
    """Construct GP zones for one source timeframe.

    ADR10 is calculated from the source timeframe's candle ranges, and the
    latest valid ADR10 is used as the fixed zone height for every qualifying
    candle in the lookback window, matching the supplied Pine behavior.
    """
    if len(candles) < 11:
        return []

    candles = sorted(candles, key=lambda c: c.open_time)
    candles = candles[-lookback:]

    ranges = [c.high - c.low for c in candles]
    adr_values = sma(ranges, 10)

    current_adr = next(
        (x for x in reversed(adr_values) if x is not None and x > 0),
        None,
    )
    if current_adr is None:
        return []

    fixed_half_height = current_adr * (height_pct / 100.0) / 2.0

    raw: list[Zone] = []

    for i, (c, adr) in enumerate(zip(candles, adr_values)):
        if adr is None or adr <= 0:
            continue

        candle_range = c.high - c.low
        size_pct = candle_range / adr * 100.0

        if size_pct < min_size_pct:
            continue

        gp_mid = c.low + candle_range * 0.559
        upper = gp_mid + fixed_half_height
        lower = gp_mid - fixed_half_height

        # Newest candle has age 0, previous candle age 1, etc.
        age = len(candles) - 1 - i

        raw.append(
            Zone(
                source_tf=tf,
                upper=upper,
                lower=lower,
                strength=float(strength_rating(candle_range, adr)),
                age=age,
                start_time=c.open_time,
                source_index=i,
            )
        )

    return _merge_overlapping_pine_style(raw)


def build_all_zones(
    monthly: list[Candle],
    daily: list[Candle],
    weekly: list[Candle],
    settings,
) -> dict[str, list[Zone]]:
    """Build exactly the six GP source buckets used by the scanner.

    Monthly-family sources:
      12M, 6M, 3M, 1M -> all qualifying strengths.

    Higher-frequency confirmation sources:
      1W, 1D -> 10/10 only.

    The colors used on the user's TradingView charts are presentation-only;
    source_tf is the machine-readable identity used by the scanner.
    """
    data: dict[str, list[Zone]] = {}

    # 1M comes directly from Binance's monthly candles.
    data["1m"] = construct_zones(
        monthly,
        "1m",
        settings.gp_lookback,
        settings.zone_height_pct,
        settings.min_candle_size_pct,
    )

    # These are the manually selected TradingView higher monthly periods.
    for tf, n in (("3m", 3), ("6m", 6), ("12m", 12)):
        aggregated = aggregate_monthly(monthly, n)
        data[tf] = construct_zones(
            aggregated,
            tf,
            settings.gp_lookback,
            settings.zone_height_pct,
            settings.min_candle_size_pct,
        )

    # Weekly and daily are only eligible when the Pine strength is 10/10.
    data["1w"] = [
        z
        for z in construct_zones(
            weekly,
            "1w",
            settings.gp_lookback,
            settings.zone_height_pct,
            settings.min_candle_size_pct,
        )
        if z.strength == 10
    ]

    data["1d"] = [
        z
        for z in construct_zones(
            daily,
            "1d",
            settings.gp_lookback,
            settings.zone_height_pct,
            settings.min_candle_size_pct,
        )
        if z.strength == 10
    ]

    return data


def tap_interacts_zone(
    price: float,
    z: Zone,
    direction: str,
    breathing: float = 0.4,
) -> bool:
    """Apply the existing scanner's directional GP breathing rule."""
    b = breathing / 100.0
    if direction == "BEARISH":
        return z.lower <= price <= z.upper * (1 + b)
    return z.lower * (1 - b) <= price <= z.upper
