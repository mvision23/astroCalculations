"""Headless native-Pine checks. These do NOT claim TradingView compilation."""
import ast
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/native_pine'))
import model
from source_harness import compile_functions, CORE, PINE
from astrocalc.universal.geometry import Scale, static_bands
from astrocalc.universal.methods import contacts, ContactSettings
from astrocalc.universal.market import MarketSpec, load_prices

@pytest.fixture(scope='module')
def native():return compile_functions(CORE)

def stamp(text):return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp()*1000)

def test_source_coefficients_and_reference_fixtures(native):
    document=json.loads((ROOT/'tests/fixtures/bitcoin_native_reference.json').read_text())
    assert document['metadata']['samples_per_body'] >= 15340
    for fixture in document['fixtures']:
        t=fixture['timestamp'];mirror=model.sky(t)
        for body,name in enumerate(model.BODIES):
            lon,distance=native['f_position'](body,t)
            assert lon == pytest.approx(mirror[body][1],abs=1e-9)
            assert distance == pytest.approx(mirror[body][2],abs=1e-10)
            assert abs(model.delta(lon,fixture['reference'][body])) <= document['metadata']['bodies'][name]['max_deg']+1e-9

def test_boundaries_and_quadrants(native):
    for t in (model.MIN_TIME-1,model.MAX_TIME):
        assert all(math.isnan(x) for x in native['f_position'](8,t))
    for t in (model.MIN_TIME,model.MAX_TIME-1):
        for body in range(10):assert all(math.isfinite(x) for x in native['f_position'](body,t))
    for x,y in ((1,1),(-1,1),(-1,-1),(1,-1),(0,1),(0,-1)):
        assert native['f_atan'](y,x)==pytest.approx(math.degrees(math.atan2(y,x)))

def test_fixed_winding_across_timeframes_and_future(native):
    start=stamp('2024-03-01');end=stamp('2024-05-01')
    report=json.loads((ROOT/'reports/bitcoin-native/accuracy.json').read_text())
    assert max(x['max_guide_residual'] for x in report['bodies'].values()) < 60 # 120° margin to ambiguous branch
    for body in range(10):
        points={t:native['f_longitude'](body,t) for t in range(start,end,6*3600000)}
        for step in (model.DAY,7*model.DAY):
            for t in range(start,end,step):assert native['f_longitude'](body,t)==points[t]
        deltas=[b-a for a,b in zip(points.values(),list(points.values())[1:])]
        assert max(abs(d) for d in deltas)<5
    assert native['f_speed'](1,stamp('2024-04-10'))<0
    assert native['f_speed'](1,stamp('2024-05-10'))>0
    lon=native['f_longitude'](0,stamp('2024-03-20'))
    later=native['f_longitude'](0,stamp('2024-03-22'))
    assert 0 < later-lon < 3
    assert lon%360>359 and later%360<3

@pytest.mark.parametrize('rounding',['Book','Continuous'])
@pytest.mark.parametrize('anchored',[False,True])
def test_actual_price_expressions_match_scale(rounding,anchored):
    env=compile_functions(('f_q','f_price'),dict(rounding=rounding,anchored=anchored,anchorPrice=91321.25,anchorLongitude=-3.25,unit=369.0))
    scale=Scale(unit=369,rounding=rounding.lower(),anchored=anchored,anchor_price=91321.25,anchor_longitude=-3.25)
    for lon in (-720.5,-360.51,-0.5,0.5,23.5,359.5,10423.456):
        for k in (-450,0,3):
            base=env['f_price'](env['f_q'](lon),k,False)
            assert base==pytest.approx(scale.price(lon,k))
            assert env['f_price'](env['f_q'](lon),k+1,False)-base==pytest.approx(8856)
            assert env['f_price'](env['f_q'](lon),k,True)-base==pytest.approx(4428)

def test_native_event_roots_and_sparse_recrossings(native):
    env=compile_functions(CORE+('f_value','f_velocity','f_root','f_turn'),dict(solverSeconds=1))
    # Independently bracketed native Mercury station and both direct/retro roots.
    a=stamp('2024-04-01');b=stamp('2024-04-03')
    station=env['f_root'](1,-1,a,b,0,True)
    assert abs(env['f_velocity'](1,-1,station))<1e-5
    # Three passes through 20° around the Mercury loop, not one shortest jump.
    crossings=[]
    a=stamp('2024-03-01');b=stamp('2024-05-20')
    target=360*math.floor(env['f_longitude'](1,a)/360)+380
    for lo in range(a,b,6*3600000):
        hi=lo+6*3600000
        if (env['f_longitude'](1,lo)-target)*(env['f_longitude'](1,hi)-target)<0:
            t=env['f_root'](1,-1,lo,hi,target,False)
            assert abs(env['f_longitude'](1,t)-target)<0.00005
            crossings.append(t)
    assert len(crossings)==3
    # Exact phase and modulo-24 clock are separate periods in the delivered source.
    source=PINE.read_text()
    assert 'turnValue,turn,30,0,"aspect"' in source
    assert 'turnValue,turn,24,0,"clock alignment"' in source
    assert 'kind+" tangent"' in source

def test_contact_source_matches_local_causal_machine():
    env=compile_functions(('f_contact',),dict(contactField='range',tolerance=0.01,separation=2,congestion=2,confirmation=2))
    state=SimpleNamespace(lastTest=-10**9,tests=0,congestionCount=0,side=0,sideRun=0,lastBreak=0,inTouch=False,previousHigh=math.nan,previousLow=math.nan,previousBandLow=math.nan,previousBandHigh=math.nan,pendingSide=0,pendingHigh=math.nan,pendingLow=math.nan)
    # Includes separated tests, congestion, gap, close confirmations, taking the
    # confirming high/low and reversal. Changing moving bands is accounted for.
    candles=[(99,101,100),(99,101,100),(96,98,97),(95,98,97),(99,101,100),(102,104,103),(103,105,104),(105,107,106),(97,99,98),(96,98,97),(94,96,95)]
    rows=['timestamp,open,high,low,close'];levels=[];actual=[]
    for i,(lo,hi,close) in enumerate(candles):
        date=f'2024-01-{i+1:02d}'
        rows.append(f'{date},{close},{hi},{lo},{close}')
        env.update(bar_index=i,low=lo,high=hi,close=close)
        tags=env['f_contact'](state,100.,100.).split()
        if tags:actual.append((i,tags))
        levels.append(dict(timestamp=datetime(2024,1,i+1,tzinfo=timezone.utc),id='fixed',low=100.,high=100.,method='test'))
    data=load_prices('\n'.join(rows),MarketSpec(timezone='UTC',session_open='00:00',session_close='00:00',calendar='24/7',bar_convention='close'))
    expected=contacts(data,levels,Scale(),datetime(2024,2,1,tzinfo=timezone.utc),ContactSettings(separation_bars=2,congestion_bars=2,confirmation_bars=2))
    assert actual==[(r['timestamp'].day-1,r['tags']) for r in expected]
    assert {'gap','reversal','first_close_high_taken','first_close_low_taken','second_test','congestion'} <= {tag for _,tags in actual for tag in tags}

def test_static_divisions_and_source_guards():
    scale=Scale(unit=369,anchored=True,anchor_price=123,anchor_longitude=27)
    bands=static_bands(scale,0,24*369,True,True)
    assert {x['low']/369 for x in bands if x['kind']=='halfway'}=={3.5,9.5,15.5,21.5}
    src=PINE.read_text()
    for formula in ('unit*(d+3.5)','unit*(d-2.5),unit*d','unit*(d+1),unit*(d+3.5)'):
        assert formula in src
    assert 'sourceRange = f_range(sourceDate,target.time)' in src
    assert 'complete := complete and time == cursor and time >= op and time_close <= cl' in src
    assert 'time_close == cl and complete' in src
    assert 'timeframe.in_seconds() <= 86400' in src
    assert 'candidate.expandedComplete := known == expected and expected > 0' in src
    assert 'barstate.isconfirmed and priceSupported' in src
    assert 'alert.freq_once_per_bar_close' in src

def test_artifact_resources_and_visibility():
    src=PINE.read_text()
    assert src.startswith('//@version=6\n') and 'overlay=true' in src
    # RE10140: 32 value + series-color calls use exactly 64 plot counts.
    assert len(re.findall(r'^plot\(',src,re.M)) == 32
    assert 'calc_bars_count' not in src and 'renderDays' not in src
    assert 'key != key[1]' in src
    assert 'scale=scale.none' in src
    assert not re.search(r'\b(?:f_cell|inspectionOn|inspectionFixed|inspectionTime|measuredError|f_result_text)\b|\btable\.',src)
    assert not re.search(r'\b(?:plotshape|plotchar|plotarrow|plotcandle|plotbar|bgcolor|barcolor|fill)\(',src)
    assert not re.search(r'\b(request\.|import |strategy\(|alertcondition\()',src)
    assert not re.search(r'\b(TODO|FIXME|placeholder)\b',src,re.I)
    for body,name in enumerate(model.BODIES):
        assert f'"{name}", inline="b{body}"' in src
        assert f'int count{body} = input.int(1,' in src
        assert f'bool custom{body} = input.bool' in src
    assert 'f_visible(body)' in src and 'master != "Hide all"' in src
    assert 'paths.size() >= PATH_BUDGET' in src and 'points.copy()' in src
    assert 'contactKeys.get(index) != key' in src
    assert 'max_labels_count=400' in src
    assert len(src.encode())<150000
    # Every input variable must be consumed outside its own declaration.
    code='\n'.join(line.split('//')[0] for line in src.splitlines())
    for name in re.findall(r'^\w+ (\w+) = input\.',code,re.M):
        assert len(re.findall(r'\b'+name+r'\b',code))>=2,name

def test_parameter_schema_and_app_controls_complete():
    mapping=json.loads((ROOT/'docs/bitcoin-native-pine-parameters.json').read_text())
    expected={}
    for filename,cls in [('workspace','Settings'),('geometry','Scale'),('market','MarketSpec'),('methods','ContactSettings')]:
        module=ast.parse((ROOT/f'src/astrocalc/universal/{filename}.py').read_text())
        node=next(n for n in module.body if isinstance(n,ast.ClassDef) and n.name==cls)
        expected[cls]={n.target.id for n in node.body if isinstance(n,ast.AnnAssign)}
        assert set(mapping['schemas'][cls])==expected[cls]
    module=ast.parse((ROOT/'src/astrocalc/universal/app.py').read_text())
    widgets={'checkbox','number_input','selectbox','multiselect','slider','text_input','text_area','date_input','time_input','radio','button','file_uploader','download_button','form_submit_button'}
    controls={ast.unparse(n.args[0]) for n in ast.walk(module) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in widgets and n.args}
    assert set(mapping['app_controls'])==controls
    markdown=(ROOT/'docs/bitcoin-native-pine-parameters.md').read_text()
    for group in [*mapping['schemas'].values(),mapping['app_controls']]:
        for record in group.values():
            assert record['classification'] in {'editable in Pine','chart-derived','fixed model property','local-only with a concrete reason'}
            assert len(record['mapping'])>15
            assert record['mapping'].replace('|','\\|') in markdown

def test_actual_search_code_tangent_recrossing_multiple_boundaries():
    from types import SimpleNamespace
    math_api=SimpleNamespace(**{name:getattr(math,name) for name in dir(math) if not name.startswith('_')},round=lambda x:math.floor(x+0.5))
    records=[]
    env=compile_functions(('f_root','f_cross_segment','f_cross'),dict(math=math_api,solverSeconds=1))
    env['f_emit']=lambda *event:records.append(event)
    # Two roots hidden by equal sparse endpoints: split at the refined extremum.
    env['f_value']=lambda a,b,t:((t-100000)/100000)**2-0.25
    env['f_cross'](1,-1,0,200000,0.75,0.75,-0.25,100000,30,0,'aspect')
    assert len(records)==2
    assert sorted(x[0] for x in records)==pytest.approx([50000,150000],abs=1000)
    records.clear()
    env['f_value']=lambda a,b,t:((t-100000)/100000)**2
    env['f_cross'](1,-1,0,200000,1,1,0,100000,30,0,'aspect')
    assert records==[(100000,'aspect tangent',1,-1,0)]
    records.clear()
    # Sparse bars spanning several phase branches emit ALL boundaries.
    env['f_value']=lambda a,b,t:t/1000
    env['f_cross'](1,-1,1000,100000,1,100,math.nan,math.nan,30,0,'aspect')
    assert [x[4] for x in records]==[30,60,90]


def test_actual_session_date_bounds_and_policies_match_local():
    from zoneinfo import ZoneInfo
    from datetime import timedelta
    def local(t,zone):return datetime.fromtimestamp(t/1000,ZoneInfo(zone))
    def timestamp(zone,y,m,d,h,minute):
        y+=(m-1)//12;m=(m-1)%12+1
        date=datetime(y,m,1,h,minute,tzinfo=ZoneInfo(zone))+timedelta(days=d-1)
        return int(date.timestamp()*1000)
    class Holidays(list):
        def includes(self,item):return item in self
    class PineString:
        @staticmethod
        def format_time(t,fmt,zone):return local(t,zone).strftime('%Y-%m-%d')
    class Weekday:
        saturday=7;sunday=1
        def __call__(self,t,zone):return (local(t,zone).weekday()+1)%7+1
    context=dict(DAY=model.DAY,timestamp=timestamp,year=lambda t,z:local(t,z).year,month=lambda t,z:local(t,z).month,dayofmonth=lambda t,z:local(t,z).day,str=PineString,dayofweek=Weekday())
    for zone,opening,closing in [('UTC','00:00','00:00'),('UTC','09:30','16:00'),('America/New_York','18:00','05:00')]:
        oh,om=map(int,opening.split(':'));ch,cm=map(int,closing.split(':'))
        env=compile_functions(('f_civil','f_session_date','f_session_day','f_bounds','f_assigned'),dict(context,researchZone=zone,openHour=oh,openMinute=om,closeHour=ch,closeMinute=cm,openMinutes=oh*60+om,closeMinutes=ch*60+cm,calendar='weekdays',holidays=Holidays(['2024-03-11']),sessionPolicy='next'))
        spec=MarketSpec(timezone=zone,session_open=opening,session_close=closing,calendar='weekdays',holidays=('2024-03-11',))
        for t in range(stamp('2024-03-08'),stamp('2024-03-13'),3600000):
            dt=datetime.fromtimestamp(t/1000,timezone.utc)
            civil=env['f_session_date'](t)
            expected=spec.session_date(dt)
            assert datetime.fromtimestamp(civil/1000,timezone.utc).date()==expected
            op,cl=env['f_bounds'](civil)
            assert [op,cl]==[int(x.timestamp()*1000) for x in spec.bounds(expected)]
            result=env['f_assigned'](civil)
            assert datetime.fromtimestamp(result/1000,timezone.utc).date()==spec.assign(dt,'next')


def test_source_ranges_never_available_before_session_close():
    class Dates(list):
        def binary_search(self,x):return self.index(x) if x in self else -1
    class Ranges(list):
        def size(self):return len(self)
        def get(self,i):return self[i]
    range_record=SimpleNamespace(date=1704153600000,available=1704153600000,lo=99.,hi=101.)
    env=compile_functions(('f_range','f_result'),dict(sessions=Ranges([range_record]),sessionDates=Dates([range_record.date])))
    env['f_session_day']=lambda date:True
    env['f_bounds']=lambda date:(date-model.DAY,date)
    assert math.isnan(env['f_range'](range_record.date,range_record.available-1))
    assert env['f_range'](range_record.date,range_record.available) is range_record
    candidate=SimpleNamespace(eligible=True,lo=100.,hi=102.)
    assert env['f_result'](candidate,range_record.date,range_record.available-1)==2
    assert env['f_result'](candidate,range_record.date,range_record.available)==1
    candidate.lo=110.;candidate.hi=120.
    assert env['f_result'](candidate,range_record.date,range_record.available)==0
    candidate.eligible=False
    assert env['f_result'](candidate,range_record.date,range_record.available)==-1
    assert env['f_result'](candidate,range_record.date+model.DAY,range_record.available+model.DAY)==-1

@pytest.mark.parametrize('rounding',['Book','Continuous'])
def test_monthly_endpoint_rounding_and_interpolation(rounding):
    env=compile_functions(('f_mod','f_delta','f_q','f_monthly_coordinate'),dict(rounding=rounding))
    for current,first,nxt in [(359.8,359.5,365.1),(-360.2,-365.5,-359.5),(130125.0,129940.0,130350.0)]:
        x=current+model.delta(first,current);y=x+model.delta(nxt,x)
        q=lambda v:math.floor(v+0.5) if rounding=='Book' else v
        for fraction in (0,.125,.5,1):
            actual=env['f_monthly_coordinate'](current,first,nxt,int(100000*fraction),0,100000)
            assert actual==pytest.approx(q(x)+(q(y)-q(x))*fraction)


def test_actual_session_accumulator_requires_full_contiguous_bars():
    class PineArray(list):
        def size(self):return len(self)
        def push(self,x):self.append(x)
        def shift(self):return self.pop(0)
    src=PINE.read_text();a=src.index('    if time_close > op and time < cl and f_session_day(civil)');b=src.index('f_range(int civil',a)
    args='activeDate,cursor,complete,sessionLow,sessionHigh,civil,op,cl,time,time_close,low,high'
    # Extract and run the actual aggregation block, carrying its persistent state.
    snippet='f_accumulate('+args+') =>\n'+src[a:b]+'    [activeDate,cursor,complete,sessionLow,sessionHigh]\n'
    for omission,start_hour in [(None,0),(10,0),(None,12)]:
        ranges=PineArray();dates=PineArray()
        env=compile_functions(('f_accumulate',),dict(sessions=ranges,sessionDates=dates,f_session_day=lambda _:True,SessionRange=SimpleNamespace(new=lambda civil,cl,lo,hi:SimpleNamespace(date=civil,available=cl,lo=lo,hi=hi))),source=snippet)
        state=[math.nan,math.nan,False,math.nan,math.nan]
        start=stamp('2024-01-01');end=start+model.DAY
        for h in range(start_hour,24):
            if h==omission:continue
            state=env['f_accumulate'](*state,end,start,end,start+h*3600000,start+(h+1)*3600000,90+h,110+h)
            if h<23:assert not ranges
        assert len(ranges)==(1 if omission is None and start_hour==0 else 0)
        if ranges:assert (ranges[0].lo,ranges[0].hi,ranges[0].available)==(90,133,end)
    # Off-session candles do not poison a daytime session's initial state.
    state=[math.nan,math.nan,False,math.nan,math.nan];ranges.clear();dates.clear()
    for h in range(24):
        state=env['f_accumulate'](*state,start,start+9*3600000,start+16*3600000,start+h*3600000,start+(h+1)*3600000,90+h,110+h)
    assert len(ranges)==1 and ranges[0].lo==99 and ranges[0].hi==125

def test_every_body_toggle_and_master_combination():
    class Choices(list):
        def get(self,index):return self[index]
    env=compile_functions(('f_visible',))
    for bits in range(1024):
        chosen=Choices(bool(bits & (1<<i)) for i in range(10))
        for master in ('All','Custom','Hide all'):
            env.update(master=master,chosen=chosen,visible9=chosen[9])
            for body in range(10):
                expected=master!='Hide all' and (chosen[9] if body==9 else master=='All' or chosen[body])
                assert env['f_visible'](body)==expected


def test_closed_occupancy_interpretations():
    env=compile_functions(('f_mod','f_occupied'))
    for mode,inside,outside in [('continuous',[0,1,24,25],[1.01,23.99]),('rounded_labels',[-0.5,0,1.5,23.5],[1.51,23.49]),('degree_buckets',[0,1,2,24],[2.01,23.99])]:
        env['occupancyMode']=mode
        for value in inside:assert env['f_occupied'](value)
        for value in outside:assert not env['f_occupied'](value)
