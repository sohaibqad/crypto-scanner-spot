def sma(values,n):
    out=[None]*len(values)
    for i in range(n-1,len(values)):
        window=values[i-n+1:i+1]
        if all(x is not None for x in window): out[i]=sum(window)/n
    return out

def rsi_wilder(closes,n=14):
    out=[None]*len(closes)
    if len(closes)<=n:return out
    gains=[0.0]*len(closes); losses=[0.0]*len(closes)
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]; gains[i]=max(d,0); losses[i]=max(-d,0)
    ag=sum(gains[1:n+1])/n; al=sum(losses[1:n+1])/n
    out[n]=100 if al==0 else 100-100/(1+ag/al)
    for i in range(n+1,len(closes)):
        ag=((n-1)*ag+gains[i])/n; al=((n-1)*al+losses[i])/n
        out[i]=100 if al==0 else 100-100/(1+ag/al)
    return out

def pivot_high(v,left,right):
    out=[False]*len(v)
    for i in range(left,len(v)-right):
        if v[i] is None: continue
        a=v[i-left:i]; b=v[i+1:i+right+1]
        if all(x is not None for x in a+b) and all(v[i]>x for x in a) and all(v[i]>=x for x in b): out[i]=True
    return out

def pivot_low(v,left,right):
    out=[False]*len(v)
    for i in range(left,len(v)-right):
        if v[i] is None: continue
        a=v[i-left:i]; b=v[i+1:i+right+1]
        if all(x is not None for x in a+b) and all(v[i]<x for x in a) and all(v[i]<=x for x in b): out[i]=True
    return out

def divergence_taps(candles,rsi,left,right):
    ph=pivot_high([c.high for c in candles],left,right)
    pl=pivot_low([c.low for c in candles],left,right)
    rh=pivot_high(rsi,left,right)
    rl=pivot_low(rsi,left,right)
    bear=[]; bull=[]
    from .models import Tap
    for i,c in enumerate(candles):
        if ph[i] and rh[i] and rsi[i] is not None: bear.append(Tap(i,c.open_time,c.high,rsi[i]))
        if pl[i] and rl[i] and rsi[i] is not None: bull.append(Tap(i,c.open_time,c.low,rsi[i]))
    return bear,bull

def build_sequence(taps,direction):
    sequences=[]; cur=[]
    for t in taps:
        if not cur: cur=[t]; continue
        p=cur[-1]
        ok=(t.price>=p.price and t.rsi<p.rsi) if direction=="BEARISH" else (t.price<=p.price and t.rsi>p.rsi)
        if ok: cur.append(t)
        else:
            if len(cur)>=3: sequences.append(cur)
            cur=[t]
    if len(cur)>=3: sequences.append(cur)
    return sequences
