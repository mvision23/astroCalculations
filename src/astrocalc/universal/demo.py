"""Deterministic synthetic prices: no historical quotes or empirical evidence."""
from datetime import date,timedelta
import csv,io,math,random

def synthetic_csv():
    rng=random.Random(1993);out=io.StringIO();writer=csv.writer(out)
    writer.writerow(['date','open','high','low','close','volume','symbol'])
    d=date(1993,1,1);i=0;previous=11.4
    while d<=date(1993,5,1):
        if d.weekday()<5:
            close=11.4+.7*math.sin(i/9)+.012*i+rng.uniform(-.12,.12)
            op=previous+rng.uniform(-.08,.08);high=max(close,op)+rng.uniform(.04,.2);low=min(close,op)-rng.uniform(.04,.2)
            writer.writerow([d.isoformat(),round(op,2),round(high,2),round(low,2),round(close,2),rng.randrange(1000,5000),'SYNTHETIC'])
            previous=close;i+=1
        d+=timedelta(days=1)
    return out.getvalue()
