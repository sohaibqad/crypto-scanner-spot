import os
EXECUTION_TIMEFRAMES=("3m","5m","15m","30m","1h","2h","3h","4h")
GP_SOURCES=("12m","6m","3m","1m","1w","1d")
class Settings:
    binance_base="https://data-api.binance.vision"
    rsi_length=int(os.getenv("RSI_LENGTH","14"))
    pivot_left=int(os.getenv("PIVOT_LEFT_BARS","2"))
    pivot_right=int(os.getenv("PIVOT_RIGHT_BARS","2"))
    zone_height_pct=float(os.getenv("ZONE_HEIGHT_PCT","3.0"))
    min_candle_size_pct=float(os.getenv("MIN_CANDLE_SIZE_PCT","60.0"))
    gp_lookback=int(os.getenv("GP_LOOKBACK","20"))
    breathing_pct=float(os.getenv("GP_BREATHING_PCT","0.4"))
    symbols_limit=int(os.getenv("SYMBOLS_LIMIT","30"))
    poll_seconds=60
    alert_from=os.getenv("ALERT_FROM","")
    alert_to=os.getenv("ALERT_TO","spectrifier@gmail.com")
settings=Settings()
