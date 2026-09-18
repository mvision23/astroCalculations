from dataclasses import asdict
from datetime import timedelta
import math
import pytest
from astrocalc.universal.astronomy import EphemProvider,instant,delta
from astrocalc.universal.geometry import Scale
from astrocalc.universal.pine import build_table,build_tables,generate_pine
from astrocalc.universal.workspace import Settings,calculate


def test_adaptive_ephemeris_wrap_station_independent_parity():
    p=EphemProvider();a=instant('1993-02-20T00:00:00Z');b=instant('1993-04-20T00:00:00Z')
    table=build_table(p,'Mercury',a,b,.001)
    assert table.station_count==2 and table.max_error_degrees<.001
    assert table.lookup(a-timedelta(seconds=1)) is None and table.lookup(b+timedelta(seconds=1)) is None
    for j in range(351):
        t=a+(b-a)*(j+.371)/352
        assert abs(delta(table.lookup(t)%360,p.longitude('Mercury',t)))<.0012
    for timestamp,lon in zip(table.timestamps,table.longitudes):
        from datetime import datetime,timezone
        assert table.lookup(datetime.fromtimestamp(timestamp,timezone.utc))==pytest.approx(lon,abs=1e-9)
    assert min(table.longitudes)<max(table.longitudes)
    # Check the actual millisecond/nine-decimal precision emitted to Pine as well
    # as translating independent interpolation error into quoted price units.
    from astrocalc.universal.pine import EphemerisTable
    serialized=EphemerisTable(table.body,[round(t,3) for t in table.timestamps],
                              [round(l,9) for l in table.longitudes],table.max_error_degrees,
                              table.rms_error_degrees,table.max_step_hours,table.station_count)
    scale=Scale(.1,rounding='continuous')
    for j in range(67):
        t=a+(b-a)*(j+.731)/68
        longitude=serialized.lookup(t)
        raw=p.longitude('Mercury',t)
        actual=longitude+delta(raw,longitude%360)
        for opposite in (False,True):
            assert abs(scale.price(longitude,-10,opposite)-scale.price(actual,-10,opposite))<.01*.25

def test_generated_scripts_static_semantics_and_budgets():
    s=Settings(bodies=['Jupiter']);s.future_days=3;s.end='1993-03-15T00:00:00Z';s.selected=s.end
    p=EphemProvider();r=calculate(s);tables=build_tables(p,s.bodies,instant(s.start),instant(s.end)+timedelta(days=3),Scale(**s.scale))
    for pane in (False,True):
        source,meta=generate_pine(tables,r.events,s,r.metadata,pane)
        assert source.startswith('//@version=6') and 'request.security' not in source
        assert 'float value = na' in source and 'stamp - epoch' in source
        assert all(not line.startswith(' ') for line in source.splitlines() if line.lstrip().startswith('plot('))
        assert meta['plot_budget']<64 and meta['knots']<100000
        if not pane:assert 'polyline.new' in source and 'barstate.isconfirmed and anyContact' in source
    s.high=10000
    with pytest.raises(ValueError,match='budget|branches'):generate_pine(tables,r.events,s,r.metadata)
