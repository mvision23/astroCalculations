"""Bounded refinement of angular events and contiguous occupancy intervals."""
from dataclasses import dataclass, field, asdict
from datetime import timedelta
import math
from .astronomy import instant, delta

ASPECTS = {0:'conjunction',30:'semisextile',60:'sextile',90:'square',120:'trine',150:'quincunx',180:'opposition'}

@dataclass
class Event:
    kind: str
    bodies: tuple
    start: object
    exact: object | None
    end: object
    target: float | None = None
    direction: str = ''
    method: str = 'UC02-ASP'
    details: dict = field(default_factory=dict)

    def record(self):
        return asdict(self)


def bisect(f,a,b,tolerance=1.):
    fa=f(a);fb=f(b)
    if abs(fa)<1e-10:return a
    if abs(fb)<1e-10:return b
    if fa*fb>0:raise ValueError('Root not bracketed')
    for _ in range(80):
        if (b-a).total_seconds()<=tolerance:break
        m=a+(b-a)/2;fm=f(m)
        if fa*fm<=0:b=m;fb=fm
        else:a=m;fa=fm
    return a+(b-a)/2


def samples(f,start,end,max_hours=6,curvature=.02):
    """6-hour physical-motion ceiling plus curvature-based recursive subdivision."""
    start=instant(start);end=instant(end)
    if end<=start or not 0<max_hours<=24:raise ValueError('Invalid event interval or sampling ceiling')
    output=[(start,f(start))]
    def split(a,fa,b,fb):
        m=a+(b-a)/2;fm=f(m)
        if (abs(fm-(fa+fb)/2)>curvature or abs(fb-fa)>12) and (b-a).total_seconds()>300:
            split(a,fa,m,fm);split(m,fm,b,fb)
        else:
            output.append((m,fm));output.append((b,fb))
    a=start;fa=output[0][1]
    while a<end:
        b=min(a+timedelta(hours=max_hours),end);fb=f(b)
        split(a,fa,b,fb);a=b;fa=fb
    return output


def scalar_roots(f,start,end,tolerance=1.,max_hours=6,tangent_epsilon=1e-7):
    points=samples(f,start,end,max_hours)
    found=[]
    for (a,fa),(b,fb) in zip(points,points[1:]):
        if abs(fa)<tangent_epsilon:found.append(a)
        if fa*fb<0:found.append(bisect(f,a,b,tolerance))
    if abs(points[-1][1])<tangent_epsilon:found.append(end)
    # A local extremum can touch zero without crossing it. Minimize |f| boundedly.
    for (a,fa),(m,fm),(b,fb) in zip(points,points[1:],points[2:]):
        if abs(fm)<abs(fa) and abs(fm)<abs(fb) and fa*fb>0:
            lo,hi=a,b
            for _ in range(60):
                if (hi-lo).total_seconds()<=tolerance:break
                x=lo+(hi-lo)/3;y=hi-(hi-lo)/3
                if abs(f(x))<abs(f(y)):hi=y
                else:lo=x
            t=lo+(hi-lo)/2
            if abs(f(t))<=tangent_epsilon:found.append(t)
    result=[]
    for t in sorted(found):
        if not result or (t-result[-1]).total_seconds()>tolerance*2:result.append(t)
    return result


def angular_roots(angle,start,end,target=0,period=360,tolerance=1.):
    """Use sine only for bracketing; reject the antipodal false branch."""
    f=lambda t:math.sin((angle(t)-target)*2*math.pi/period)
    roots=scalar_roots(f,start,end,tolerance,max_hours=min(3,period/4),tangent_epsilon=1e-9)
    return [t for t in roots if math.cos((angle(t)-target)*2*math.pi/period)>0]


def occupancy(angle,start,end,low,high,period=360,tolerance=1.):
    if not 0<=high-low<period:raise ValueError('Band width must be in [0, period)')
    roots=angular_roots(angle,start,end,low,period,tolerance)+angular_roots(angle,start,end,high,period,tolerance)
    boundaries=sorted(set([start,end]+roots))
    inside=lambda t:(angle(t)-low)%period<=high-low+1e-9
    intervals=[]
    for a,b in zip(boundaries,boundaries[1:]):
        if inside(a+(b-a)/2):
            if intervals and abs((a-intervals[-1][1]).total_seconds())<=2*tolerance: intervals[-1]=(intervals[-1][0],b)
            else:intervals.append((a,b))
    for t in roots:
        if inside(t) and not any(a-timedelta(seconds=2*tolerance)<=t<=b+timedelta(seconds=2*tolerance) for a,b in intervals):intervals.append((t,t))
    return sorted(intervals)


def aspects(provider,body,other,start,end,orb=.3,angles=tuple(ASPECTS),tolerance=1.,clock=False):
    if body==other:raise ValueError('Choose distinct bodies')
    period=24 if clock else 360
    if not 0<=orb<period/4:raise ValueError('Orb is out of range')
    start,end=instant(start),instant(end)
    phase=lambda t:provider.longitude(body,t)-provider.longitude(other,t)
    targets=[0] if clock else sorted({b for a in angles for b in (a,(-a)%360)})
    result=[]
    for target in targets:
        roots=angular_roots(phase,start,end,target,period,tolerance)
        intervals=occupancy(phase,start,end,target-orb,target+orb,period,tolerance) if orb else [(r,r) for r in roots]
        for a,b in intervals:
            exact=[r for r in roots if a-timedelta(seconds=2*tolerance)<=r<=b+timedelta(seconds=2*tolerance)]
            for r in exact or [None]:
                t=r or a;speed=provider.speed(body,t)-provider.speed(other,t)
                family=min(target,360-target)
                details=dict(signed_phase=delta(phase(t),0),branch=target,orb=orb,numerical_tolerance_seconds=tolerance,
                             interval_clipped_start=a==start,interval_clipped_end=b==end,
                             family='clock coincidence' if clock else ASPECTS[family])
                if not clock and family==0 and {body,other}=={'Mercury','Sun'} and r:
                    mercury=provider.position('Mercury',r);sun=provider.position('Sun',r)
                    kind='inferior' if mercury.earth_distance_au<sun.earth_distance_au else 'superior'
                    details.update(conjunction_type=kind,distance_au=mercury.earth_distance_au,
                                   motion_consistent=(mercury.speed<0)==(kind=='inferior'))
                result.append(Event('clock_alignment' if clock else 'aspect',(body,other),a,r,b,target,
                                    'increasing' if speed>0 else 'decreasing','UC07-MATCH' if clock else 'UC02-ASP',details))
    return sorted(result,key=lambda e:e.exact or e.start)


def body_events(provider,body,start,end,tolerance=1.,targets=(),occupancy_mode='continuous'):
    start,end=instant(start),instant(end)
    angle=lambda t:provider.longitude(body,t)
    events=[]
    for t in scalar_roots(lambda t:provider.speed(body,t),start,end,tolerance,tangent_epsilon=1e-8):
        after=provider.speed(body,min(t+timedelta(hours=1),end))
        events.append(Event('station',(body,),t,t,t,direction='direct' if after>0 else 'retrograde',method='UC08-REPLAY',details={'numerical_tolerance_seconds':tolerance}))
    for target in sorted(set(range(0,360,30))|set(targets)):
        for t in angular_roots(angle,start,end,target,tolerance=tolerance):
            events.append(Event('ingress' if target in range(0,360,30) else 'longitude_crossing',(body,),t,t,t,target,
                                'direct' if provider.speed(body,t)>0 else 'retrograde','UC08-REPLAY'))
    band={'continuous':(0,1),'rounded_labels':(-.5,1.5),'degree_buckets':(0,2)}
    if occupancy_mode not in band:raise ValueError('Invalid occupancy interpretation')
    for a,b in occupancy(angle,start,end,*band[occupancy_mode],period=24,tolerance=tolerance):
        speed=provider.speed(body,a+(b-a)/2)
        events.append(Event('24_band',(body,),a,None,b,0,'direct' if speed>0 else 'retrograde','UC07-BAND',
                            dict(duration_hours=(b-a).total_seconds()/3600,clipped_start=a==start,clipped_end=b==end,numerical_tolerance_seconds=tolerance,
                                 occupancy_mode=occupancy_mode,classification='explicit band formalization' if occupancy_mode=='continuous' else 'discretionary interpretation')))
    return sorted(events,key=lambda e:e.exact or e.start)

def clock_sectors(provider,body,other,start,end,tolerance=1.):
    """Optional nearest-degree sector interpretation, distinct from an exact phase match."""
    from .geometry import rounded
    edges={start,end}
    for b in (body,other):
        edges.update(angular_roots(lambda t:provider.longitude(b,t),start,end,.5,1,tolerance))
    edges=sorted(edges);out=[]
    for a,b in zip(edges,edges[1:]):
        t=a+(b-a)/2
        if rounded(provider.longitude(body,t))%24==rounded(provider.longitude(other,t))%24:
            if out and out[-1].end==a:out[-1].end=b
            else:out.append(Event('clock_sector',(body,other),a,None,b,method='UC07-MATCH',details={'classification':'nearest-degree sector interpretation'}))
    return out


def combinations(events,min_bodies=2):
    bands=[e for e in events if e.kind=='24_band']
    edges=sorted({t for e in bands for t in (e.start,e.end)})
    output=[]
    for a,b in zip(edges,edges[1:]):
        mid=a+(b-a)/2
        bodies=tuple(sorted({e.bodies[0] for e in bands if e.start<=mid<=e.end}))
        if len(bodies)>=min_bodies:
            if output and output[-1].bodies==bodies and output[-1].end==a:output[-1].end=b
            else:output.append(Event('simultaneous_24',bodies,a,None,b,method='UC07-COMB',details={'rules':['closed 24-line bands','simultaneous occupancy'],'probability':None}))
    return output


def superior_inferior_pairs(events):
    pending=None;result=[]
    for e in sorted(events,key=lambda e:e.exact or e.start):
        kind=e.details.get('conjunction_type')
        if kind=='superior':pending=e
        elif kind=='inferior' and pending:
            result.append((pending,e));pending=None
    return result
