"""Source-derived math/path regressions, not TradingView compilation."""
import math
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/native_pine'))
from render_check import DAY,build,source_paths,stamp,environment,longitude,coordinate,PineArray,history,stream
from source_harness import PINE,compile_functions

def test_band_selection_counts_boundaries_and_anchors():
    for anchored in (False,True):
        env=environment(anchored=anchored,anchorPrice=80000,anchorLongitude=-5.5)
        for q in (-700.5,0.,10532.):
            for side in (False,True):
                lo=env['f_price'](q,-2,side);hi=env['f_price'](q,4,side)
                for n in range(13):
                    selected=[env['f_selected_k'](q,lo,hi,n,100,slot,side) for slot in range(12)]
                    assert [k for k in selected if not math.isnan(k)]==list(range(-2,min(5,-2+n)))
                assert math.isnan(env['f_selected_k'](q,lo+1,lo+2,12,0,0,side))
                assert env['f_selected_k'](q,lo,lo+1,1,0,0,side)==-2
    env=environment(branchMode='Manual k')
    assert [env['f_selected_k'](0,-1e6,1e6,4,0,i,False) for i in range(4)]==[-1,0,1,2]

@pytest.mark.parametrize('rounding',['Book','Continuous'])
@pytest.mark.parametrize('monthly',[False,True])
def test_actual_path_source_matches_plan_and_keeps_identity(rounding,monthly):
    start=stamp('2024-03-25T12:34:56');split=stamp('2024-04-02T16:01:03');end=stamp('2024-04-09T16:01:03')
    bounds={1:(80000,110000),3:(71000,124000)};counts={1:5,3:0,7:4}
    paths,stats,samples=build(start,split,end,counts,bounds,rounding=rounding,monthly=monthly)
    actual,vertices=source_paths(start,split,end,counts,bounds,rounding=rounding,monthly=monthly)
    assert actual==paths and vertices==stats['vertices']
    env=environment(rounding=rounding)
    for p in paths:
        assert p.body != 3
        lo,hi=bounds.get(p.body,(70000,125000))
        assert all(lo<=y<=hi for _,y in p.points)
        assert all(t2>=t1 for (t1,_),(t2,_) in zip(p.points,p.points[1:]))
        # Step verticals repeat t; the final point at each t is the actual price.
        for t,y in dict(p.points).items():
            q=coordinate(env,p.body,t,monthly)
            assert y==pytest.approx(env['f_price'](q,p.k,p.side))
        if p.future:assert p.points[0][0]>=split
        else:assert p.points[-1][0]<=split
    histories={(p.body,p.k,p.side):p.points[-1] for p in paths if not p.future and p.points[-1][0]==split}
    futures={(p.body,p.k,p.side):p.points[0] for p in paths if p.future and p.points[0][0]==split}
    assert histories and histories==futures

@pytest.mark.parametrize('offset',[0,3600000,86400000])
def test_open_and_confirmed_close_use_exact_timestamp(offset):
    split=stamp('2026-09-01')+offset
    paths,_,_=build(split-DAY,split,split+DAY,{0:1},rounding='Continuous')
    assert {p.points[0][0] for p in paths if p.future}=={split}
    for p in paths:
        if p.future:
            assert p.points[0][1]==pytest.approx(environment()['f_price'](longitude(0,split),p.k,p.side))

def test_long_lunar_coverage_and_no_slot_connectors():
    t=stamp('2026-09-01');start=t-30*DAY
    paths,stats,samples=build(start,t,t+7*DAY,{0:3,9:3})
    actual,_=source_paths(start,t,t+7*DAY,{0:3,9:3})
    assert actual==paths
    assert longitude(9,t)-longitude(9,start)>360
    moon=[p for p in paths if p.body==9]
    assert len({p.k for p in moon})>15
    # Count is maintained at every historical bar; survivors retain their slots.
    _,_,hist=history(start,t,{9:3},source=True)
    for time,q,rows in hist[9]:
        assert len({k for k,p in rows[0] if not math.isnan(k)})==3
        assert all(70000<=p<=125000 for k,p in rows[0])
    # All alerts are keyed, and absent levels replace state with a fresh Contact.
    source=PINE.read_text()
    assert 'contactKeys.get(index) != key' in source
    assert 'contactStates.set(index,Contact.new())' in source
    assert 'slot < counts.get(body) and (not opp or opposite) and not na(k)' in source
    assert 'calc_bars_count' not in source and 'renderDays' not in source


def test_visibility_ranges_and_zero_count_are_source_derived():
    shared=dict(levelKeys=PineArray([5]*240),priceLow=70000.,priceHigh=125000.,customRanges=PineArray([False,True]),bodyLows=PineArray([0,80000]),bodyHighs=PineArray([1,100000]),counts=PineArray([0,6]),centers=PineArray([0,0]),opposite=True,f_visible=lambda b:True)
    env=compile_functions(('f_low','f_high','f_body_level'),dict(environment(),**shared))
    assert env['f_low'](0)==70000 and env['f_low'](1)==80000
    assert math.isnan(env['f_body_level'](0,100,0,False))
    assert 80000<=env['f_body_level'](1,100,0,False)<=100000
    env['f_visible']=lambda b:False
    assert math.isnan(env['f_body_level'](1,100,0,False))

@pytest.mark.parametrize('counts,history,future',[ (dict.fromkeys(range(9),1),14,7), (dict.fromkeys(range(10),1),14,7), ({3:8,7:8},120,30), (dict.fromkeys(range(9),1),120,120), ({3:8,7:8},120,120), ({0:1},120,700), ({3:1,7:1},120,700)])
def test_resource_examples_execute_actual_builder(counts,history,future):
    t=stamp('2026-09-01');a=t-history*DAY;b=t+future*DAY
    paths,stats,_=build(a,t,b,counts)
    actual,vertices=source_paths(a,t,b,counts)
    assert paths==actual and vertices==stats['vertices']
    for body in counts:
        assert max(p.points[-1][0] for p in actual if p.future and p.body==body)==b
    assert stats['paths']<=96 and stats['samples']<=6000 and stats['vertices']<=40000
    if 8 in counts.values():
        assert len([p for p in paths if p.body==3 and not p.side and p.points[0][0]<=t-60*DAY<=p.points[-1][0]])>3


def test_twelve_mains_and_opposite_semantics():
    t=stamp('2026-09-01')
    for opposite in (False,True):
        paths,_,_=build(t-DAY,t,t,{7:12},{7:(10000,125000)},opposite=opposite)
        assert len(paths)==12*(2 if opposite else 1)
        assert sum(not p.side for p in paths)==12


def test_invalid_inputs_and_actual_path_budget_rejection():
    t=stamp('2026-09-01')
    for kwargs,error in [(dict(bounds={3:(1,1)}),'range'),(dict(monthly=True,counts={9:1}),'Moon monthly'),(dict(counts={3:13}),'counts'),(dict(counts=dict.fromkeys(range(10),12)),'32 historical curves')]:
        args=dict(counts={3:1});args.update(kwargs)
        with pytest.raises(ValueError,match=error):build(t-DAY,t,t+DAY,**args)
    with pytest.raises(ValueError,match='vertex budget'):
        source_paths(t-DAY,t,t+60*DAY,{9:12})
    with pytest.raises(ValueError,match='samples'):
        build(t-365*DAY,t,t+90*DAY,{9:1})
    assert 'if f_low(body) >= f_high(body)' in PINE.read_text()
    assert 'if monthly and f_visible(9) and counts.get(9) > 0' in PINE.read_text()


def test_fast_body_resolution_and_retrograde():
    env=environment(rounding='Continuous')
    for body in range(10):
        step=int(env['f_sample_hours'](body)*3600000)
        for date in ('2024-04-02','2024-12-08','2026-08-12'):
            t=stamp(date);a=longitude(body,t);b=longitude(body,t+step);m=longitude(body,t+step//2)
            assert abs(b-a)<.26
            assert abs(m-(a+b)/2)<.003
    assert env['f_speed'](3,stamp('2025-01-01'))<0
    assert env['f_speed'](3,stamp('2025-04-01'))>0
    assert env['f_sample_hours'](9)<=.353
    for days in (1,7,30):
        # Direct timestamp evaluation; no per-candle angular increment.
        t=stamp('2026-08-01')+days*DAY
        assert coordinate(env,9,t)==longitude(9,t)


def test_same_prices_have_different_log_spacing_and_fixture_provenance():
    import csv,json,hashlib
    env=environment(rounding='Continuous')
    q=longitude(0,stamp('2025-11-24'));k=-415
    prices=[env['f_price'](q,k+i,False) for i in range(3)]
    assert prices[1]-prices[0]==pytest.approx(8856)
    assert prices[2]-prices[1]==pytest.approx(8856)
    assert math.log(prices[1])-math.log(prices[0]) > math.log(prices[2])-math.log(prices[1])
    report=json.loads((ROOT/'reports/bitcoin-native/correction-numerics.json').read_text())
    assert report['source_sha256']==hashlib.sha256(PINE.read_bytes()).hexdigest()
    assert len(report['comparison'])==10
    with (ROOT/'reports/bitcoin-native/correction-comparison.csv').open() as f:
        rows=list(csv.DictReader(f))
    assert {r['body'] for r in rows}==set(report['comparison'])
    for r in rows[::31]:
        assert int(r['app_k'])==int(r['k'])+15*int(r['winding_m'])
        assert float(r['price'])==float(r['q'])*369+8856*int(r['k'])+(4428 if r['opposite']=='True' else 0)
    assert report['pine_compiled'] is False


def test_actual_slot_identity_reset_block():
    from types import SimpleNamespace
    # Execute the delivered reset block, including first entry and unchanged k.
    src=PINE.read_text();a=src.index('                if index < 240\n');b=src.index('                string tags =',a)
    body='\n'.join(line[12:] for line in src[a:b].splitlines())
    env=compile_functions(('f_reset_fixture',),dict(Contact=SimpleNamespace(new=lambda:SimpleNamespace(tests=0))),source='f_reset_fixture() =>\n'+body+'\n')
    original=SimpleNamespace(tests=4);states=PineArray([original]);keys=PineArray([-2]);current=PineArray([-1])
    env.update(index=0,contactKeys=keys,levelKeys=current,contactStates=states)
    env['f_reset_fixture']();assert states[0].tests==0 and keys[0]==-1
    states[0].tests=3;env['f_reset_fixture']();assert states[0].tests==3
    keys[0]=math.nan;env['f_reset_fixture']();assert states[0].tests==0


@pytest.mark.parametrize('n',[0,1,3,8,12])
@pytest.mark.parametrize('side',[False,True])
def test_replenishment_preserves_eligible_branches_and_count(n,side):
    env=environment();keys=PineArray([math.nan]*n)
    # Direct, retrograde, and jumps larger than the band. This is a behavioral
    # oracle (survival, count, contiguity), not a copied allocation formula.
    for q in list(range(-500,500,7))+list(range(500,-500,-7))+[100000.,-100000.]:
        previous=keys.copy()
        env['f_replenish'](keys,q,70000,125000,n,0,side)
        active=[k for k in keys if not math.isnan(k)]
        base=env['f_price'](q,0,side)
        lo=math.ceil((70000-base)/8856);hi=math.floor((125000-base)/8856)
        assert len(active)==min(n,max(0,hi-lo+1))
        assert len(set(active))==len(active)
        assert sorted(active)==list(range(min(active),max(active)+1)) if active else True
        for index,k in enumerate(previous):
            if not math.isnan(k) and lo<=k<=hi:assert keys[index]==k
        assert all(70000<=env['f_price'](q,k,side)<=125000 for k in active)


def test_loaded_history_exceeds_old_day_and_bar_caps():
    start=stamp('2009-01-01');split=stamp('2026-09-01')
    # More than 6,000 daily bars and many thousands of visited lunar identities;
    # historical branches consume a fixed plot pool, never polyline capacity.
    paths,stats,_=build(start,split,split+DAY,{0:2,9:3})
    actual,vertices=source_paths(start,split,split+DAY,{0:2,9:3})
    assert paths==actual and vertices==stats['vertices']
    assert stats['historical_bars']>6000 and stats['historical_segments']>100
    assert min(p.points[0][0] for p in paths)==start
    assert max(p.points[-1][0] for p in paths if not p.future)==split
    assert stats['plots']==32 and stats['plot_counts']==64
    assert stats['paths']<96


def test_future_uses_confirmed_identity_seed_without_mutating_history():
    env=environment();start=stamp('2025-01-01');split=stamp('2026-09-01')
    _,seed,samples=history(start,split,{3:4,9:3},source=True)
    saved=seed.copy()
    for b,n in ((3,4),(9,3)):
        snapshots=stream(env,b,[split,split+DAY],n,(70000,125000),0,True,False,seed,source=True)
        for side in range(2):
            assert snapshots[0][2][side]==samples[b][-1][2][side]
        assert all((math.isnan(x) and math.isnan(y)) or x==y for x,y in zip(seed,saved))
    src=PINE.read_text()
    assert 'confirmedKeys := levelKeys.copy()' in src
    assert 'futureEnd,confirmedKeys)' in src
    assert 'f_build_paths(paths,used,body,renderStart' not in src


def test_historical_plot_color_suppresses_only_identity_connectors():
    # Verify actual predicate used by the series-color helper with scalar history
    # substituted for Pine's [1] operator, rather than emulate a chart renderer.
    src=PINE.read_text();start=src.index('    bool changed =',src.index('f_history_color'))
    expression=src[start:src.index('\n',start)].replace('key[1]','oldKey')
    source='f_changed(int key, int oldKey) =>\n'+expression+'\n    changed\n'
    env=compile_functions(('f_changed',),source=source)
    assert env['f_changed'](3,2)
    assert not env['f_changed'](3,3)
    assert not env['f_changed'](3,math.nan)
    assert not env['f_changed'](math.nan,3)
