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
        from types import SimpleNamespace
        im={"1m":"1","3m":"3","5m":"5","15m":"15","30m":"30","1h":"60","2h":"120","4h":"240","6h":"360","12h":"720","1d":"D","1w":"W","1M":"M"}
        r=requests.get("https://api.bybit.com/v5/market/kline",params={"category":"spot","symbol":symbol,"interval":im.get(str(interval),"60"),"limit":min(int(limit),1000)},timeout=15).json()
        raw=r.get("result",{}).get("list",[])
        return [SimpleNamespace(open_time=int(x[0]),timestamp=int(x[0]),open=float(x[1]),high=float(x[2]),low=float(x[3]),close=float(x[4]),volume=float(x[5]),close_time=int(x[0])+60000) for x in reversed(raw)]


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
