from datetime import date,timedelta
import pytest
from astrocalc.universal.astronomy import instant
from astrocalc.universal.market import *
from astrocalc.universal.events import Event
from astrocalc.universal.methods import compare_events,contacts,ContactSettings
from astrocalc.universal.geometry import Scale

CSV=b'date,open,high,low,close\n2024-03-08,10,12,9,11\n2024-03-11,11,13,10,12\n'

def test_dst_session_labels_weekends_and_holidays():
    spec=MarketSpec(holidays=('2024-03-12',))
    data=load_prices(CSV,spec)
    assert data.frame.timestamp[0].hour==21 and data.frame.timestamp[1].hour==20
    saturday=instant('2024-03-09T12:00:00Z')
    assert spec.assign(saturday,'previous')==date(2024,3,8)
    assert spec.assign(saturday,'next')==date(2024,3,11)
    assert spec.assign(saturday,'strict') is None
    assert spec.assign(instant('2024-03-12T12:00:00Z'),'next')==date(2024,3,13)
    assert session_range(data,date(2024,3,11),instant('2024-03-11T19:59:59Z')) is None
    assert session_range(data,date(2024,3,11),instant('2024-03-11T20:00:00Z'))['high']==13

def test_invalid_missing_close_only_and_sorting():
    with pytest.raises(ValueError,match='rejected'):load_prices(b'date,open,high,low,close\n2024-03-08,20,12,9,11\n')
    with pytest.raises(ValueError,match='duplicate'):load_prices(CSV+CSV.splitlines()[1]+b'\n')
    with pytest.raises(ValueError,match='rejected'):load_prices(b'date,close\n2024-03-08,nan\n')
    data=load_prices(b'date,close\n2024-03-12,12\n2024-03-08,10\n')
    assert not data.ohlc and data.report['sorted_rows']==2 and data.report['missing_sessions']==['2024-03-11']
    assert session_range(data,date(2024,3,8),instant('2024-03-13T00:00:00Z')) is None
    mapped=load_prices(b'Day,Last\n2024-03-08,10\n',mapping={'timestamp':'Day','close':'Last'})
    assert mapped.report['column_mapping']=={'timestamp':'Day','close':'Last'}
    with pytest.raises(ValueError,match='only one field'):load_prices(CSV,mapping={'open':'close','close':'close'})
    with pytest.raises(ValueError,match='rejected'):load_prices(b'timestamp,close\n2024-03-10T02:30:00,10\n',MarketSpec(timestamp_kind='instant'))

def test_comparison_causal_availability_and_missing_denominator():
    data=load_prices(CSV)
    times=[instant('2024-03-08T12:00:00Z'),instant('2024-03-11T12:00:00Z'),instant('2024-03-15T12:00:00Z')]
    es=[Event('aspect',('Sun','Jupiter'),t,t,t,120,details={'family':'trine'}) for t in times]
    rows=compare_events(data,es,Scale(1),instant('2024-03-15T22:00:00Z'),shifts=[0,1])
    assert len(rows)==6 and any(r['status']=='unavailable' for r in rows)
    first=rows[0];assert first['available_at']>first['source_time'] and first['available_at']<first['target_time']
    assert first['strict_hit'] is True and rows[1]['strict_hit'] is False
    earlier=compare_events(data,es,Scale(1),instant('2024-03-08T15:00:00Z'))
    assert all(r['status']=='unavailable' for r in earlier)

def test_gap_is_not_intrabar_crossing_and_second_test_separation():
    data=load_prices(b'date,open,high,low,close\n2024-03-04,8,9,7,8\n2024-03-05,12,13,11,12\n2024-03-06,10,12,9,11\n2024-03-07,12,13,11,12\n2024-03-08,10,12,9,11\n')
    levels=[dict(timestamp=t,id='A',low=10,high=10.5,method='UC06-DIV') for t in data.frame.timestamp]
    rows=contacts(data,levels,Scale(1),instant('2024-03-09T00:00:00Z'),ContactSettings(tolerance_ticks=0,separation_bars=2))
    assert 'gap' in rows[1]['tags'] and 'intrabar_crossing' not in rows[1]['tags']
    assert 'first_test' in rows[2]['tags'] and 'second_test' in rows[-1]['tags']
    assert all(r['available_at']<=instant('2024-03-09T00:00:00Z') for r in rows)

def test_intraday_missing_coverage_and_overnight_closing_date():
    spec=MarketSpec(timestamp_kind='instant',session_open='22:00',session_close='02:00',bar_minutes=60,calendar='24/7',timezone='UTC')
    header='timestamp,open,high,low,close\n'
    bars=['2024-03-08T23:00:00Z','2024-03-09T00:00:00Z','2024-03-09T01:00:00Z','2024-03-09T02:00:00Z']
    csv=header+''.join(t+',10,12,9,11\n' for t in bars)
    full=load_prices(csv,spec)
    assert set(full.frame.session)=={'2024-03-09'}
    assert session_range(full,date(2024,3,9),instant(bars[-1]))['high']==12
    missing=load_prices(header+''.join(t+',10,12,9,11\n' for t in bars if 'T00:' not in t),spec)
    assert missing.report['incomplete_sessions']==['2024-03-09']
    assert session_range(missing,date(2024,3,9),instant(bars[-1])) is None

def test_continuous_touch_is_one_test_and_break_followup_is_causal():
    data=load_prices(b'date,open,high,low,close\n2024-03-04,10,11,9,10\n2024-03-05,10,11,9,10\n2024-03-06,10,12,9,11\n2024-03-07,11,13,10,12\n')
    levels=[dict(timestamp=t,id='A',low=10,high=10.5,method='UC06-DIV') for t in data.frame.timestamp]
    rows=contacts(data,levels,Scale(1),instant('2024-03-08T00:00:00Z'),ContactSettings(tolerance_ticks=0,separation_bars=1))
    assert sum('first_test' in r['tags'] for r in rows)==1
    assert not any('second_test' in r['tags'] for r in rows)
    assert 'first_close_high_taken' not in rows[2]['tags']
    assert 'first_close_high_taken' in rows[3]['tags']
