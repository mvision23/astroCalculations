"""Development only. Run with pyswisseph 2.10.3.2 on PYTHONPATH; no runtime feed."""
import json, math, sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
from model import BODIES, DAY, MIN_TIME, MAX_TIME, day, sky, delta, guide
import swisseph as swe
from source_harness import CORE, compile_functions
source=compile_functions(CORE)
ids=[swe.SUN,swe.MERCURY,swe.VENUS,swe.MARS,swe.JUPITER,swe.SATURN,swe.URANUS,swe.NEPTUNE,swe.PLUTO,swe.MOON]
flags=swe.FLG_MOSEPH|swe.FLG_TRUEPOS|swe.FLG_NONUT
stats=[dict(max_deg=0.,sum_squared=0.,max_guide_residual=0.,max_time=None) for _ in ids]
fixtures=[];count=0
samples=sorted(set(range(MIN_TIME,MAX_TIME,DAY))|{MAX_TIME-1}|{int(datetime.fromisoformat(t).replace(tzinfo=timezone.utc).timestamp()*1000) for t in ['2024-03-20T12:34:56','2024-04-01T22:00:00','2024-04-25T13:00:00','2026-09-20T00:00:00','2050-12-31T23:59:59']})
for t in samples:
 native=sky(t); count+=1;refs=[]
 for body in range(10):
  lon,distance=source["f_position"](body,t)
  if abs(lon-native[body][1])>1e-8 or abs(distance-native[body][2])>1e-8:raise AssertionError((t,body,"source/mirror drift"))
  native[body]=(lon%360,lon,distance)
 for body,sid in enumerate(ids):
  reference,returned=swe.calc(day(t)+2451543.5,sid,flags)
  if not returned&swe.FLG_MOSEPH:raise RuntimeError('Reference changed ephemeris')
  error=abs(delta(native[body][0],reference[0]));st=stats[body]
  st['sum_squared']+=error*error
  if error>st['max_deg']:st.update(max_deg=error,max_time=t)
  st['max_guide_residual']=max(st['max_guide_residual'],abs(native[body][1]-guide(body,day(t))))
  refs.append(reference[0])
 if t in [samples[0],samples[-1]] or t%DAY!=0 or t==1789862400000:
  fixtures.append(dict(timestamp=t,reference=refs,native=[r[0] for r in native],unwrapped=[r[1] for r in native]))
for st in stats:
 st['rms_deg']=math.sqrt(st.pop('sum_squared')/count)
 st['smooth_price_max_369']=369*st['max_deg']
report=dict(reference='Swiss Ephemeris '+swe.version+' Moshier, TRUEPOS | NONUT, identical TT',frame='geometric geocentric mean ecliptic/equinox of date',timescale='UTC approximates UT1 + NASA piecewise delta-T polynomials',samples_per_body=count,interval=['2009-01-01T00:00:00Z','2050-12-31T23:59:59.999Z'],bodies=dict(zip(BODIES,stats)),pine_execution=False, source_expressions="Scalar Pine expressions translated by source_harness.py; not a Pine compiler or runtime", mirror_checked=True)
Path('reports/bitcoin-native/accuracy.json').write_text(json.dumps(report,indent=2)+'\n')
Path('tests/fixtures/bitcoin_native_reference.json').write_text(json.dumps(dict(metadata=report,fixtures=fixtures),indent=2)+'\n')
print(json.dumps(report,indent=2))
