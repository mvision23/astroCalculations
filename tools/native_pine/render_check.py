"""Headless historical plot streams and future paths; NOT a Pine runtime.

The independent planner is compared with actual extracted f_replenish and
f_build_paths bodies. Chart bar placement, qualifiers and rollback need Pine.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import math,re
from types import SimpleNamespace
from source_harness import CORE,PINE,compile_functions
DAY=86400000

def stamp(text):return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp()*1000)
def environment(**kwargs):
    settings=dict(rounding='Book',anchored=False,anchorPrice=0.,anchorLongitude=0.,unit=369.,branchMode='Price-band coverage',futureHours=6)
    settings.update(kwargs)
    return compile_functions(CORE+('f_q','f_price','f_selected_k','f_replenish','f_sample_hours','f_monthly_coordinate'),settings)

class PineArray(list):
    def get(self,i):return self[i]
    def set(self,i,v):self[i]=v
    def size(self):return len(self)
    def push(self,v):self.append(v)
    def copy(self):return PineArray(self)
    def includes(self,v):return v in self

@dataclass
class Path:
    body:int
    k:int
    side:bool
    future:bool
    points:list

CORE_ENV=compile_functions(CORE)
@lru_cache(maxsize=100000)
def longitude(body,t):return CORE_ENV['f_longitude'](body,t)
def coordinate(env,body,t,monthly=False):
    lon=longitude(body,t)
    if not monthly:return env['f_q'](lon)
    date=datetime.fromtimestamp(t/1000,timezone.utc)
    first=date.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    nxt=first.replace(year=first.year+1,month=1) if first.month==12 else first.replace(month=first.month+1)
    a=int(first.timestamp()*1000);b=min(2556143999999,int(nxt.timestamp()*1000))
    return env['f_monthly_coordinate'](lon,longitude(body,a),longitude(body,b),t,a,b)
def limits():return {k:int(v) for k,v in re.findall(r'^const int (\w+_BUDGET) = (\d+)',PINE.read_text(),re.M)}
def isna(v):return math.isnan(v)

def replenish(env,keys,q,lo,hi,n,center,side):
    """Independent set-allocation implementation, compared against Pine source."""
    if env['branchMode']!='Price-band coverage':
        for i in range(n):keys[i]=env['f_selected_k'](q,lo,hi,n,center,i,side)
        return
    base=env['f_price'](q,0,side);lower=math.ceil((lo-base)/(24*env['unit']));upper=math.floor((hi-base)/(24*env['unit']))
    middle=math.floor(((lo+hi)/2-base)/(24*env['unit'])+.5)
    for i,k in enumerate(keys):
        if not isna(k) and not lower<=k<=upper:keys[i]=math.nan
    for i,k in enumerate(keys):
        if isna(k):
            survivors=sorted(k for k in keys if not isna(k))
            candidates=[survivors[0]-1,survivors[-1]+1] if survivors else [middle]
            choices=[k for k in candidates if lower<=k<=upper]
            keys[i]=min(choices,key=lambda k:(abs(k-middle),k)) if choices else math.nan

def centers_for(env,counts,monthly):return {b:math.floor((100000-env['f_price'](coordinate(env,b,stamp('2026-09-01'),monthly),0,False))/(24*env['unit'])+.5) for b in counts}

def stream(env,body,times,n,bounds,center,opposite,monthly,seed=None,source=False):
    lo,hi=bounds;alloc=[PineArray([math.nan]*n) for _ in range(2 if opposite else 1)]
    if seed is not None:
        for side,keys in enumerate(alloc):
            for slot in range(n):keys[slot]=seed[body*24+slot*2+side]
    snapshots=[]
    for t in times:
        q=coordinate(env,body,t,monthly)
        rows=[]
        for side,keys in enumerate(alloc):
            (env['f_replenish'] if source else lambda k,q,lo,hi,n,c,s:replenish(env,k,q,lo,hi,n,c,s))(keys,q,lo,hi,n,center,bool(side))
            rows.append([(k,env['f_price'](q,k,bool(side)) if not isna(k) else math.nan) for k in keys])
        snapshots.append((t,q,rows))
    return snapshots

def paths_from_stream(body,snapshots,n,opposite,book,future):
    paths=[];vertices=0
    for side in range(2 if opposite else 1):
        for slot in range(n):
            pts=[];previousK=math.nan;previous=math.nan
            def flush():
                if len(pts)>=2:paths.append(Path(body,previousK,bool(side),future,pts.copy()))
                pts.clear()
            for t,q,rows in snapshots:
                k,p=rows[side][slot]
                if isna(k) or (not isna(previousK) and k!=previousK):flush();previous=math.nan
                if not isna(p):
                    if book and not isna(previous):pts.append((t,previous));vertices+=1
                    pts.append((t,p));vertices+=1
                previousK=k;previous=p
            flush()
    return paths,vertices

def history(start,split,counts,bounds=None,opposite=True,monthly=False,bar_hours=24,source=False,**settings):
    env=environment(**settings);bounds=bounds or {};centers=centers_for(env,counts,monthly);seed=PineArray([math.nan]*240);paths=[];samples={}
    step=int(bar_hours*3600000);times=list(range(start,split,step))+[split]
    for b,n in counts.items():
        if not n:continue
        snapshots=stream(env,b,times,n,bounds.get(b,(70000,125000)),centers[b],opposite,monthly,source=source)
        samples[b]=snapshots
        pp,_=paths_from_stream(b,snapshots,n,opposite,env['rounding']=='Book' and not monthly,False);paths.extend(pp)
        for side,rows in enumerate(snapshots[-1][2]):
            for slot,(k,p) in enumerate(rows):seed[b*24+slot*2+side]=k
    return paths,seed,samples

def build(start,split,end,counts,bounds=None,opposite=True,monthly=False,bar_hours=24,**settings):
    env=environment(**settings);budget=limits();bounds=bounds or {}
    if any(not 0<=n<=12 for n in counts.values()):raise ValueError('counts')
    if sum(counts.values())*(2 if opposite else 1)>budget['CURVE_BUDGET']:raise ValueError('32 historical curves')
    if monthly and counts.get(9,0):raise ValueError('Moon monthly')
    if any(lo>=hi for lo,hi in bounds.values()):raise ValueError('range')
    paths,seed,hist=history(start,split,counts,bounds,opposite,monthly,bar_hours,**settings)
    historical_paths=len(paths);samples=vertices=0;coordinates={}
    centers=centers_for(env,counts,monthly)
    for b,n in counts.items():
        if not n:continue
        coordinates[b,False]=[(t,q) for t,q,_ in hist[b]]
        if end<=split:continue
        step=math.floor(env['f_sample_hours'](b)*3600000);steps=math.ceil((end-split)/step)
        samples+=steps+1
        if samples>budget['SAMPLE_BUDGET']:raise ValueError('future samples')
        times=[min(end,split+i*step) for i in range(steps+1)]
        snapshots=stream(env,b,times,n,bounds.get(b,(70000,125000)),centers[b],opposite,monthly,seed)
        coordinates[b,True]=[(t,q) for t,q,_ in snapshots]
        pp,v=paths_from_stream(b,snapshots,n,opposite,env['rounding']=='Book' and not monthly,True)
        if any(len(p.points)>budget['PATH_VERTEX_BUDGET'] for p in pp):raise ValueError('future vertices')
        vertices+=v;paths.extend(pp)
        if vertices>budget['VERTEX_BUDGET']:raise ValueError('future vertices')
        if len(paths)-historical_paths>budget['PATH_BUDGET']:raise ValueError('future paths')
    return paths,dict(paths=len(paths)-historical_paths,historical_segments=historical_paths,historical_bars=len(next(iter(hist.values()))) if hist else 0,samples=samples,vertices=vertices,plots=32,plot_counts=64,allocated_curves=sum(counts.values())*(2 if opposite else 1)),coordinates

def source_paths(start,split,end,counts,bounds=None,opposite=True,monthly=False,bar_hours=24,**settings):
    """Actual allocation and future-builder source with drawing stubs."""
    env=environment(**settings);bounds=bounds or {};budget=limits()
    hist,seed,_=history(start,split,counts,bounds,opposite,monthly,bar_hours,source=True,**settings)
    centers=centers_for(env,range(10),monthly)
    def fail(message):raise ValueError(message)
    extra=dict(env,**budget,counts=PineArray(counts.get(b,0) for b in range(10)),centers=PineArray(centers[b] for b in range(10)),monthly=monthly,opposite=opposite,
        array=SimpleNamespace(new=lambda *args:PineArray([args[1] if len(args)>1 else math.nan]*args[0]) if args else PineArray()),
        chart=SimpleNamespace(point=SimpleNamespace(from_time=lambda t,p:(t,p))),runtime=SimpleNamespace(error=fail),
        RenderPath=SimpleNamespace(new=lambda pts,body,side,k,future:Path(body,k,bool(side),future,list(pts))),
        f_low=lambda b:bounds.get(b,(70000,125000))[0],f_high=lambda b:bounds.get(b,(70000,125000))[1],
        f_body_coordinate=lambda b,t:coordinate(env,b,t,monthly))
    actual=compile_functions(('f_build_paths','f_queue','f_vertex'),extra)
    paths=PineArray();used=PineArray([0])
    for b,n in counts.items():
        if n:actual['f_build_paths'](paths,used,b,split,end,seed)
    return hist+list(paths),used[0]

if __name__=='__main__':
    t=stamp('2026-09-01')
    for name,counts in [('all_ten',dict.fromkeys(range(10),1)),('dense',{3:8,7:8}),('moon',{0:3,9:3})]:
        planned,stats,_=build(stamp('2020-01-01'),t,t+7*DAY,counts)
        actual,v=source_paths(stamp('2020-01-01'),t,t+7*DAY,counts)
        assert planned==actual and v==stats['vertices']
        print(name,stats)
