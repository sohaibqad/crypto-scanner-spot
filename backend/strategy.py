from .indicators import rsi_wilder,divergence_taps,build_sequence
from .golden_pocket import tap_interacts_zone
from .models import Signal
def scan(symbol,tf,candles,zones,settings):
    rsi=rsi_wilder([c.close for c in candles],settings.rsi_length)
    bear,bull=divergence_taps(candles,rsi,settings.pivot_left,settings.pivot_right)
    out=[]
    for direction,taps in (("BEARISH",bear),("BULLISH",bull)):
        for seq in build_sequence(taps,direction):
            for n,t in enumerate(seq,1):
                if n<3:continue
                for src,zs in zones.items():
                    for z in zs:
                        if tap_interacts_zone(t.price,z,direction,settings.breathing_pct):
                            out.append(Signal(symbol,tf,direction,z,n,t))
    return out
