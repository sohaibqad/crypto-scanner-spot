from backend.golden_pocket import strength_rating,tap_interacts_zone
from backend.models import Zone
def test_strength(): assert strength_rating(160,100)==10 and strength_rating(60,100)==5
def test_bear_breathing():
 z=Zone("1d",101,100,10,1,0,0)
 assert tap_interacts_zone(101.404,z,"BEARISH",.4)
 assert not tap_interacts_zone(101.41,z,"BEARISH",.4)
def test_bull_breathing():
 z=Zone("1d",101,100,10,1,0,0)
 assert tap_interacts_zone(99.6,z,"BULLISH",.4)
 assert not tap_interacts_zone(99.59,z,"BULLISH",.4)


def test_execution_timeframes_include_3h():
    from backend.config import EXECUTION_TIMEFRAMES
    assert EXECUTION_TIMEFRAMES == ("3m","5m","15m","30m","1h","2h","3h","4h")
