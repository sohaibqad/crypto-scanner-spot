import requests
from .models import Candle
from .config import settings


BINANCE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


class BinanceClient:
    def __init__(self):
        self.s = requests.Session()
        # Apply headers to every request made through this Binance session.
        self.s.headers.update(BINANCE_HEADERS)
        self.base = settings.binance_base.rstrip("/")
        self._symbol_cache = []
        self._symbol_cache_at = 0.0

    def get(self, path, params=None):
        r = self.s.get(self.base + path, params=params, timeout=20, headers=BINANCE_HEADERS)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _candle_from_spot_kline(row):
        # Binance Spot /api/v3/klines uses the same positional kline schema:
        # [open time, open, high, low, close, base volume, ...]
        return Candle(
            int(row[0]), float(row[1]), float(row[2]),
            float(row[3]), float(row[4]), float(row[5])
        )

    def klines(self, symbol, interval, limit=1000):
        # Binance Spot does not provide a native 3h interval; aggregate complete
        # 1h candles into UTC-aligned 3h candles, as in the previous scanner.
        if interval == "3h":
            need = min(limit, 1000)
            raw_limit = min(1000, need * 3 + 3)
            data = self.get("/api/v3/klines", {
                "symbol": symbol.upper(), "interval": "1h", "limit": raw_limit
            })
            candles = [self._candle_from_spot_kline(x) for x in data]
            bucket_ms = 3 * 60 * 60 * 1000
            groups = {}
            for c in candles:
                bucket = (c.open_time // bucket_ms) * bucket_ms
                groups.setdefault(bucket, []).append(c)
            out = []
            for bucket, g in sorted(groups.items()):
                if len(g) < 3:
                    continue
                out.append(Candle(
                    g[0].open_time, g[0].open,
                    max(x.high for x in g), min(x.low for x in g),
                    g[-1].close, sum(x.volume for x in g)
                ))
            return out[-need:]

        data = self.get("/api/v3/klines", {
            "symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)
        })
        return [self._candle_from_spot_kline(x) for x in data]

    def _tradable_usdt_spot_pairs(self):
        info = self.get("/api/v3/exchangeInfo")
        return {
            s["symbol"]: s.get("baseAsset", "")
            for s in info["symbols"]
            if s.get("status") == "TRADING"
            and s.get("quoteAsset") == "USDT"
            and s.get("isSpotTradingAllowed", True)
        }

    def top_symbols(self, limit=30):
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT", "DOTUSDT", "NEARUSDT", "APTUSDT", "LTCUSDT", "FETUSDT", "RENDERUSDT", "TAOUSDT", "PEPEUSDT", "SHIBUSDT", "UNIUSDT", "ARBUSDT", "OPUSDT", "INJUSDT", "STXUSDT", "TIAUSDT", "AAVEUSDT", "FILUSDT", "RUNEUSDT", "SEIUSDT", "KASUSDT"][:limit]
