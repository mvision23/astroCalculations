from datetime import timedelta
from types import SimpleNamespace
import math
import pytest
from astrocalc.universal.astronomy import EphemProvider,instant,delta,series
from astrocalc.universal.events import *

START=instant('2000-01-01T00:00:00Z')
class Fake:
    def __init__(self,f):self.f=f
    def longitude(self,body,t):return (self.f((t-START).total_seconds()/86400) if body=='Mercury' else 0)%360
    def speed(self,body,t):
        return delta(self.longitude(body,t+timedelta(seconds=10)),self.longitude(body,t-timedelta(seconds=10)))*4320
    def position(self,body,t):return SimpleNamespace(earth_distance_au=.5 if self.speed(body,t)<0 else 1.5,speed=self.speed(body,t))

def test_new_aspects_both_branches():
    p=Fake(lambda d:20+d*40)
    events=aspects(p,'Mercury','Sun',START,START+timedelta(days=9),orb=.3,angles=[30,150])
    assert [e.target for e in events if e.exact]==[30,150,210,330]
    assert all(e.start<e.exact<e.end for e in events)
    assert all(abs(math.sin(math.radians(p.longitude('Mercury',e.exact)-e.target)))<1e-5 for e in events)

def test_multiple_recrossings_tangent_and_band_grouping():
    p=Fake(lambda d:24+2*math.cos(d*math.pi))
    es=aspects(p,'Mercury','Sun',START,START+timedelta(days=4),orb=.05,clock=True)
    assert len([e for e in es if e.exact])==4
    assert {e.direction for e in es}=={'increasing','decreasing'}
    tangent=angular_roots(lambda t:24+((t-START).total_seconds()/86400-.413)**2,START,START+timedelta(days=1),0,24)
    assert len(tangent)==1 and (tangent[0]-START).total_seconds()/86400==pytest.approx(.413,abs=2e-5)
    intervals=occupancy(lambda t:23+(t-START).total_seconds()/86400,START,START+timedelta(days=3),0,1,24)
    assert len(intervals)==1
    assert (intervals[0][0]-START).total_seconds()==pytest.approx(86400,abs=2)
    assert (intervals[0][1]-START).total_seconds()==pytest.approx(172800,abs=2)

def test_real_conjunction_geometry_and_stations():
    p=EphemProvider();a=instant('1993-01-01T00:00:00Z');b=instant('1993-04-01T00:00:00Z')
    events=aspects(p,'Mercury','Sun',a,b,angles=[0])
    exact=[e for e in events if e.exact]
    assert [e.exact.date().isoformat() for e in exact]==['1993-01-23','1993-03-09']
    from zoneinfo import ZoneInfo
    assert exact[1].exact.astimezone(ZoneInfo('America/New_York')).date().isoformat()=='1993-03-08'
    assert [e.details['conjunction_type'] for e in exact]==['superior','inferior']
    assert all(e.details['motion_consistent'] for e in exact)
    assert len(superior_inferior_pairs(events))==1
    stations=[e for e in body_events(p,'Mercury',a,b) if e.kind=='station']
    assert len(stations)==2
    assert all(abs(p.speed('Mercury',e.exact))<2e-6 for e in stations)

def test_simultaneous_intervals_not_pairs_or_days():
    a=START;b=a+timedelta(days=3);c=a+timedelta(days=1)
    es=[Event('24_band',('Jupiter',),a,None,b),Event('24_band',('Uranus',),a,None,b),Event('24_band',('Sun',),c,None,b)]
    grouped=combinations(es)
    assert len(grouped)==2 and len(grouped[-1].bodies)==3

def test_legacy_provider_parity_and_sparse_unwrap():
    from astrocalc.calculations import longitude
    p=EphemProvider('legacy_j2000')
    assert p.longitude('Sun',START)==longitude('Sun',START)
    rows=series(p,['Sun'],[START,START+timedelta(days=730)])
    assert 710<rows[-1]['unwrapped']-rows[0]['unwrapped']<730
