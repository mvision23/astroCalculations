"""Book comparisons and explicitly parameterized, causal research interpretations."""
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import combinations
import math
from .geometry import intersects, overlap, wheel_overlap
from .market import event_ranges
from .events import superior_inferior_pairs

PRESETS = {
    'Sugar':dict(pair=['Mercury','Sun'],bodies=['Jupiter','Uranus','Neptune','Mercury','Venus','Sun','Mars','Saturn','Pluto'],unit=.1,quote_units='cents/lb',low=9.,high=15.),
    'Dow':dict(pair=['Sun','Jupiter'],bodies=['Saturn'],unit=10.,quote_units='index points',low=2400.,high=3600.),
    'S&P':dict(pair=['Sun','Jupiter'],bodies=['Sun','Jupiter'],unit=1.,quote_units='index points',low=300.,high=480.),
    'British pound':dict(pair=['Mercury','Saturn'],bodies=['Saturn'],unit=.01,quote_units='USD/GBP',low=1.4,high=2.),
    'Deutsche Mark':dict(pair=['Mercury','Saturn'],bodies=['Neptune'],unit=.001,quote_units='USD/DEM',low=.5,high=.8),
    'Swiss franc':dict(pair=['Mercury','Saturn'],bodies=['Saturn'],unit=.001,quote_units='USD/CHF',low=.5,high=.8),
    'Japanese yen':dict(pair=['Mercury','Pluto'],bodies=['Pluto'],unit=.00001,quote_units='USD/JPY',low=.006,high=.01),
    'Crude oil':dict(pair=['Sun','Pluto'],bodies=['Saturn','Jupiter'],unit=.1,quote_units='USD/barrel',low=15.,high=25.),
    'Silver':dict(pair=['Venus','Jupiter'],bodies=['Saturn','Uranus','Neptune'],unit=.01,quote_units='USD/oz',low=3.,high=6.),
    'Soybeans':dict(pair=['Mercury','Sun'],bodies=['Mercury','Sun'],unit=1.,quote_units='cents/bushel',low=450.,high=650.),
}


def compare_events(data,events,scale,asof,policy='next',window_days=1,shifts=(0,),last_n=3,conjunction_pairs=False,comparison_mode='family',sequences=()):
    """All configured candidates, including misses/unavailable. No best-shift selection."""
    if window_days<0 or last_n<1:raise ValueError('Invalid comparison parameters')
    events=[e for e in events if e.kind=='aspect' and e.exact]
    if conjunction_pairs:pairs=superior_inferior_pairs(events)
    elif comparison_mode=='manual':
        by_time={e.exact.isoformat():e for e in events};pairs=[]
        for sequence in sequences:
            selected=[by_time[t] for t in sequence['events'] if t in by_time]
            pairs.extend(zip(selected,selected[1:]))
    else:
        pairs=[];families={}
        for event in sorted(events,key=lambda e:e.exact):
            key=(event.bodies,event.details['family'] if comparison_mode=='family' else 'all families')
            pairs.extend((old,event) for old in families.get(key,[])[-last_n:])
            families.setdefault(key,[]).append(event)
    rows=[]
    for source,target in pairs:
        src=event_ranges(data,source.exact,asof,policy,window_days)
        dst=event_ranges(data,target.exact,asof,policy,window_days)
        for shift in shifts:
            s=src['assigned'];d=dst['assigned'];strict=dst['strict']
            price_range=(s['low']+24*scale.unit*shift,s['high']+24*scale.unit*shift) if s else None
            eligible=s is not None and s['available_at']<=target.exact
            test=lambda r:intersects(price_range,(r['low'],r['high'])) if r and eligible else None
            hit=test(d);strict_hit=test(strict)
            expanded=[test(x['range']) for x in dst['expanded']]
            known=[v for v in expanded if v is not None]
            expected=sum(data.spec.is_session(date.fromisoformat(x['session'])) for x in dst['expanded'])
            complete=len(known)==expected and expected>0
            rows.append(dict(method='UC01-PAIR' if conjunction_pairs else 'UC03-REPEAT',source_time=source.exact,target_time=target.exact,
                family=target.details['family'],source_session=src['assigned_session'],target_session=dst['assigned_session'],
                available_at=s['available_at'] if s else None,eligible=eligible,shift=shift,cycle=24*scale.unit,
                source_low=price_range[0] if s else None,source_high=price_range[1] if s else None,
                target_low=d['low'] if d else None,target_high=d['high'] if d else None,
                strict_hit=strict_hit,assigned_hit=hit,expanded_hit=True if any(known) else False if complete else None,
                expanded_complete=complete,
                distance=max(price_range[0]-d['high'],d['low']-price_range[1],0) if eligible and d else None,
                ordinary_overlap=overlap(price_range,(d['low'],d['high'])) if eligible and d else None,
                wheel_overlap=wheel_overlap((s['low'],s['high']),(d['low'],d['high']),24*scale.unit) if eligible and d else None,
                status='unavailable' if not eligible or d is None else 'hit' if hit else 'miss'))
    return rows


def evaluation(rows,synthetic=False):
    result=dict(total_candidates=len(rows),eligible=sum(r['eligible'] for r in rows),synthetic=synthetic,
                interpretation='Descriptive range overlap; no entry/exit strategy or accuracy claim')
    for field in ('strict_hit','assigned_hit','expanded_hit'):
        values=[r[field] for r in rows if r[field] is not None]
        result[field]=dict(denominator=len(values),hits=sum(values),misses=len(values)-sum(values),unavailable=len(rows)-len(values))
    return result

@dataclass(frozen=True)
class ContactSettings:
    tolerance_ticks: float = 1
    separation_bars: int = 3
    congestion_bars: int = 3
    confirmation_bars: int = 1
    field: str = 'range'

    def __post_init__(self):
        if not math.isfinite(self.tolerance_ticks) or self.tolerance_ticks<0 or min(self.separation_bars,self.congestion_bars,self.confirmation_bars)<1:raise ValueError('Invalid contact settings')
        if self.field not in ('range','close'):raise ValueError('Contact field must be range or close')


def contacts(data,levels,scale,asof,settings=ContactSettings()):
    """Each branch carries its own state. Signals become available only at bar completion."""
    bars=data.completed(asof)
    if 'close' not in bars:return []
    if settings.field=='range' and not data.ohlc:return []
    tolerance=settings.tolerance_ticks*data.spec.tick_size
    by_time={}
    for level in levels:by_time.setdefault(level['timestamp'],[]).append(level)
    states={};result=[]
    for i,bar in enumerate(bars.to_dict('records')):
        for level in by_time.get(bar['timestamp'],[]):
            key=level['id'];a=level['low'];b=level['high']
            lo=bar['low'] if settings.field=='range' else bar['close'];hi=bar['high'] if settings.field=='range' else bar['close']
            touch=lo<=b+tolerance and hi>=a-tolerance
            side=1 if bar['close']>b+tolerance else -1 if bar['close']<a-tolerance else 0
            state=states.setdefault(key,dict(last_test=-10**9,tests=0,congestion=0,side=0,side_run=0,previous=None,previous_band=None,last_break=0,in_touch=False,pending_break=None))
            tags=[]
            pending=state['pending_break']
            if pending and data.ohlc:
                if pending['side']>0 and bar['high']>pending['high']+tolerance:
                    tags.append('first_close_high_taken');state['pending_break']=None
                elif pending['side']<0 and bar['low']<pending['low']-tolerance:
                    tags.append('first_close_low_taken');state['pending_break']=None
            if touch:
                state['congestion']+=1
                if not state['in_touch'] and i-state['last_test']>=settings.separation_bars:
                    state['tests']+=1;state['last_test']=i
                    tags.append('first_test' if state['tests']==1 else 'second_test' if state['tests']==2 else 'retest')
                tags.append('touch')
                if lo<a and hi>b:tags.append('intrabar_crossing')
                if state['congestion']==settings.congestion_bars:tags.append('congestion')
            else:state['congestion']=0
            previous=state['previous'];previous_band=state['previous_band']
            if previous and data.ohlc:
                # Require complete candle ranges on opposite sides, accounting for moving bands.
                if (previous['high']<previous_band[0]-tolerance and bar['low']>b+tolerance) or (previous['low']>previous_band[1]+tolerance and bar['high']<a-tolerance):tags.append('gap')
            if side and side!=state['side']:
                state['side_run']=1
            elif side:state['side_run']+=1
            else:state['side_run']=0
            if side and state['side_run']==settings.confirmation_bars:
                tags.append('close_above' if side>0 else 'close_below')
                if state['last_break'] and side!=state['last_break']:tags.append('reversal')
                state['last_break']=side
                if data.ohlc:state['pending_break']=dict(side=side,high=bar['high'],low=bar['low'])
            if tags:
                distance=0 if a<=bar['close']<=b else min(abs(bar['close']-a),abs(bar['close']-b))
                result.append(dict(method=level['method'],timestamp=bar['timestamp'],available_at=bar['available_at'],level_id=key,
                                   low=a,high=b,tags=tags,distance_ticks=distance/data.spec.tick_size,distance_wheel_units=distance/scale.unit,
                                   classification='parameterized interpretation',contact_field=settings.field))
            state.update(side=side,previous=bar,previous_band=(a,b),in_touch=touch)
    return result


def level_confluences(levels,tolerance):
    by_time={}
    for l in levels:
        if l.get('body'):by_time.setdefault(l['timestamp'],[]).append(l)
    result=[]
    for t,group in by_time.items():
        for a,b in combinations(group,2):
            if a['body']!=b['body'] and abs(a['low']-b['low'])<=tolerance:
                result.append(dict(timestamp=t,method='UC05-MULTI',first=a['id'],second=b['id'],distance=abs(a['low']-b['low'])))
    return result


def validate_sequence(event_ids,label):
    if not 2<=len(event_ids)<=4 or len(set(event_ids))!=len(event_ids):raise ValueError('Choose 2–4 distinct ordered events')
    if list(event_ids)!=sorted(event_ids):raise ValueError('Sequence events must be chronological')
    return dict(method='UC03-SEQUENCE',events=list(event_ids),label=label,classification='manual interpretation')
