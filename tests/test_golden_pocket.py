from backend.golden_pocket import aggregate_monthly, construct_zones
from backend.models import Candle
import datetime as dt


def month_ts(year, month):
    return int(dt.datetime(year, month, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)


def m(year, month, open_, high, low, close):
    return Candle(month_ts(year, month), open_, high, low, close, 1.0)


def test_12m_keeps_current_incomplete_group():
    # One complete calendar year + eight months in the current year.
    candles = []
    for month in range(1, 13):
        candles.append(m(2025, month, 100, 110 + month, 90, 105))
    for month in range(1, 9):
        candles.append(m(2026, month, 100, 130 + month, 88, 105))

    out = aggregate_monthly(candles, 12)
    assert len(out) == 2
    assert out[-1].high == max(c.high for c in candles[-8:])


def test_strength_10_is_available_from_construct_zones():
    candles = []
    for month in range(1, 12):
        if month < 11:
            candles.append(m(2025, month, 100, 110, 100, 105))
        else:
            candles.append(m(2025, month, 100, 140, 100, 130))

    zones = construct_zones(candles, "1d", lookback=20, height_pct=3, min_size_pct=60)
    assert any(z.strength == 10 for z in zones)
