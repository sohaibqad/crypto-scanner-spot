import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import settings, EXECUTION_TIMEFRAMES
from .binance_data import BinanceClient
from .golden_pocket import build_all_zones
from .strategy import scan
from .alerts import send

def _scan_symbol(c, sym):
    monthly_limit = min(1500, settings.gp_lookback * 12 + 12)
    zones = build_all_zones(
        c.klines(sym, "1M", monthly_limit),
        c.klines(sym, "1d", settings.gp_lookback + 12),
        c.klines(sym, "1w", settings.gp_lookback + 12),
        settings,
    )
    signals = []
    for tf in EXECUTION_TIMEFRAMES:
        candles = c.klines(sym, tf, 400)
        # Do not analyze the currently forming execution candle.
        signals.extend(scan(sym, tf, candles[:-1], zones, settings))
    return signals

def main():
    c = BinanceClient()
    seen = set()

    print("V8 LIVE SPOT SCANNER — TOP 30 MARKET-CAP COINS")
    print("Execution:", ", ".join(x.upper() for x in EXECUTION_TIMEFRAMES))
    print("Email recipient:", settings.alert_to)
    print("Polling:", settings.poll_seconds, "seconds")

    while True:
        try:
            # Refresh the market-cap universe every polling cycle so the scanner
            # does not remain stuck on an old top-30 list.
            symbols = c.top_symbols(settings.symbols_limit)
            print("\nMonitoring:", ", ".join(symbols))

            with ThreadPoolExecutor(max_workers=min(10, len(symbols))) as pool:
                futures = {pool.submit(_scan_symbol, c, sym): sym for sym in symbols}
                for fut in as_completed(futures):
                    sym = futures[fut]
                    try:
                        for s in fut.result():
                            key = (
                                s.symbol, s.execution_tf, s.direction,
                                s.zone.source_tf, round(s.zone.lower, 8),
                                round(s.zone.upper, 8), s.tap_number, s.tap.time
                            )
                            if key not in seen:
                                seen.add(key)
                                print(
                                    f"ALERT {s.symbol} {s.direction} "
                                    f"{s.execution_tf.upper()} "
                                    f"GP {s.zone.source_tf.upper()} "
                                    f"TAP {s.tap_number}"
                                )
                                send(s)
                    except Exception as e:
                        print(f"{sym}: scan error:", repr(e))

            time.sleep(settings.poll_seconds)

        except KeyboardInterrupt:
            return
        except Exception as e:
            print("Scanner cycle error:", repr(e))
            time.sleep(settings.poll_seconds)

if __name__ == "__main__":
    main()
