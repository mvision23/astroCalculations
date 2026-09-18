import json
from importlib.resources import files
from datetime import timedelta
import pytest
from astrocalc.universal.astronomy import EphemProvider,instant,BODIES
from astrocalc.universal.events import body_events,aspects
from astrocalc.universal.geometry import price_label,Scale,intersects
from astrocalc.universal.methods import validate_sequence

FIXTURES=json.loads(files('astrocalc.universal').joinpath('book-fixtures.json').read_text())

def test_book_ephemeris_fixtures():
    p=EphemProvider();fixture=FIXTURES['saturn_1992']
    for d,longitude,rounded in fixture['values']:
        assert p.longitude('Saturn',instant(d+'T00:00:00Z'))==pytest.approx(longitude,abs=fixture['tolerance_degrees'])
    fixture=FIXTURES['march_1993_positions']
    for body,lon in fixture['values'].items():
        assert p.longitude(body,instant(fixture['date']+'T00:00:00Z'))==pytest.approx(lon,abs=fixture['tolerance_degrees'])

def test_book_family_ranges():
    assert price_label(2678,10)==2680 and price_label(2215,10)==2210
    assert intersects((332.5+36,338+36),(370,374.5))
    assert intersects((379+36,382.5+36),(418,422))
    assert len(FIXTURES['dow_trines']['ranges'])==11

def test_book_timing_fixtures():
    p=EphemProvider();a=instant('1987-10-01T00:00:00Z');b=instant('1987-11-01T00:00:00Z')
    es=aspects(p,'Mars','Saturn',a,b,clock=True)
    assert [e.exact.date().isoformat() for e in es if e.exact]==['1987-10-16']
    visits=[e for e in body_events(p,'Jupiter',a,b) if e.kind=='24_band']
    # Book says Oct 9–23; continuous [24,25] actually starts Oct 16.
    # Do not force agreement. The inclusive degree-bucket interpretation begins Oct 9.
    assert visits[0].start.day==16 and visits[0].end.day==23
    buckets=[e for e in body_events(p,'Jupiter',a,b,occupancy_mode='degree_buckets') if e.kind=='24_band']
    assert buckets[0].start.day in (8,9) and buckets[0].end.day==23
    a=instant('1993-12-01T00:00:00Z');b=instant('1994-01-01T00:00:00Z')
    continuous=[e for e in body_events(p,'Neptune',a,b) if e.kind=='24_band']
    buckets=[e for e in body_events(p,'Neptune',a,b,occupancy_mode='degree_buckets') if e.kind=='24_band']
    assert continuous==[] and len(buckets)==1 and buckets[0].end.day in (19,20)

def test_supported_bodies_dates():
    p=EphemProvider()
    for body in BODIES+('Moon',):
        for stamp in ('1900-01-01T00:00:00Z','2100-12-31T00:00:00Z'):
            pos=p.position(body,instant(stamp));assert 0<=pos.longitude<360
    with pytest.raises(ValueError):p.longitude('Earth',instant('2000-01-01T00:00:00Z'))
    with pytest.raises(ValueError):p.longitude('Sun',instant('1800-01-01T00:00:00Z'))

def test_manual_sequences():
    assert validate_sequence(['1993-01-01','1993-02-01'],'1–2')['classification']=='manual interpretation'
    with pytest.raises(ValueError):validate_sequence(['same','same'],'1–2')

def test_anchor_transform():
    assert Scale(10,anchored=True,anchor_price=100,anchor_longitude=300).price(305,1)==390
