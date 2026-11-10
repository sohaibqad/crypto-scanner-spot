import argparse,datetime as dt
from .config import settings,EXECUTION_TIMEFRAMES
from .binance_data import BinanceClient
from .golden_pocket import build_all_zones
from .strategy import scan

def main():
    p=argparse.ArgumentParser(); p.add_argument("--symbol",default="BTCUSDT"); p.add_argument("--limit",type=int,default=1000); p.add_argument("--execution",default="ALL"); a=p.parse_args()
    c=BinanceClient(); sym=a.symbol.upper()
    monthly_limit=min(1500, max(a.limit, settings.gp_lookback * 12 + 12))
    monthly=c.klines(sym,"1M",monthly_limit); daily=c.klines(sym,"1d",min(max(a.limit, settings.gp_lookback + 12),1500)); weekly=c.klines(sym,"1w",min(max(a.limit, settings.gp_lookback + 12),1500))
    zones=build_all_zones(monthly,daily,weekly,settings)
    print(f"\n--- {sym} GP ZONES ---")
    for tf,zs in zones.items():
        print(f"\n[{tf.upper()}]")
        for z in zs: print(f"{z.lower:.8f} - {z.upper:.8f} | Strength {z.strength:.0f}/10 | Age {z.age}")
    tfs=EXECUTION_TIMEFRAMES if a.execution.upper()=="ALL" else (a.execution.lower(),)
    seen=set(); signals=[]
    for tf in tfs:
        candles=c.klines(sym,tf,min(a.limit,1500))
        for s in scan(sym,tf,candles[:-1],zones,settings):
            key=(s.symbol,s.execution_tf,s.direction,s.zone.source_tf,round(s.zone.lower,8),round(s.zone.upper,8),s.tap_number,s.tap.time)
            if key not in seen: seen.add(key); signals.append(s)
    signals.sort(key=lambda x:x.tap.time)
    print(f"\n--- CONFIRMED SIGNALS ({len(signals)}) ---")
    for i,s in enumerate(signals,1):
        print(f"[{i}] {s.direction} | {s.execution_tf.upper()} | GP {s.zone.source_tf.upper()} {s.zone.strength:.0f}/10 | Tap {s.tap_number} | Price {s.tap.price:.8f}")
        print(f"    Zone {s.zone.lower:.8f} - {s.zone.upper:.8f} | {dt.datetime.fromtimestamp(s.tap.time/1000,dt.timezone.utc)}")
if __name__=="__main__":main()
