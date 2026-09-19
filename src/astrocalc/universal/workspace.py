"""Versioned settings and shared result schema consumed by UI, CLI and Pine."""
from dataclasses import dataclass, field, asdict
import math
from datetime import timedelta
from .astronomy import instant, EphemProvider, series, BODIES, MIN_TIME, MAX_TIME
from .geometry import Scale, static_bands
from .events import aspects, body_events, combinations, clock_sectors
from .methods import compare_events, contacts, level_confluences, ContactSettings
from .market import MarketSpec

@dataclass
class Settings:
    start: str = '1993-03-01T00:00:00+00:00'
    end: str = '1993-05-01T00:00:00+00:00'
    selected: str = '1993-03-17T21:00:00+00:00'
    bodies: list = field(default_factory=lambda:['Jupiter','Saturn','Mercury'])
    pair: list = field(default_factory=lambda:['Mercury','Sun'])
    coordinate_mode: str = 'apparent_of_date'
    scale: dict = field(default_factory=lambda:asdict(Scale()))
    market: dict = field(default_factory=lambda:asdict(MarketSpec()))
    column_mapping: dict = field(default_factory=dict)
    low: float = 9.
    high: float = 15.
    orb: float = .3
    occupancy_mode: str = 'continuous'
    clock_alignment_mode: str = 'exact_phase'
    step_hours: float = 24
    future_days: int = 30
    session_policy: str = 'next'
    window_days: int = 1
    shifts: list = field(default_factory=lambda:[0])
    last_family_dates: int = 3
    comparison_mode: str = 'family'
    conjunction_pairs: bool = False
    opposite: bool = True
    halfway: bool = True
    adjoining: bool = True
    monthly_sample: bool = False
    tolerance_seconds: float = 1.
    contacts: dict = field(default_factory=lambda:asdict(ContactSettings()))
    sequences: list = field(default_factory=list)
    annotations: list = field(default_factory=list)
    scale_locked: bool = True
    preset: str = 'Sugar'
    schema_version: int = 1

    @property
    def horizon(self):
        """Effective inclusive endpoint, shared by local plots and Pine exports."""
        return min(instant(self.end)+timedelta(days=self.future_days),MAX_TIME)

    @property
    def horizon_clipped(self):
        return instant(self.end)+timedelta(days=self.future_days)>MAX_TIME

    def validate(self):
        a,b=instant(self.start),instant(self.end);instant(self.selected)
        if not MIN_TIME<=a<b<=MAX_TIME:raise ValueError('Use increasing dates in 1900–2100')
        if not self.bodies or not set(self.bodies)<=set(BODIES+('Moon',)):raise ValueError('Choose supported bodies')
        if len(self.pair)!=2 or self.pair[0]==self.pair[1] or not set(self.pair)<=set(BODIES+('Moon',)):raise ValueError('Choose two distinct supported bodies')
        if not .25<=self.step_hours<=744 or not 0<=self.future_days<=730:raise ValueError('Invalid sampling/future horizon')
        self.selected=max(a,min(instant(self.selected),self.horizon)).isoformat()
        if not all(math.isfinite(v) for v in [self.low,self.high,self.orb,self.step_hours,self.tolerance_seconds,*self.shifts]):raise ValueError('Settings must be finite')
        if not self.low<self.high or not 0<=self.orb<6:raise ValueError('Invalid range/orb')
        if self.tolerance_seconds<.01 or self.window_days<0:raise ValueError('Invalid tolerance/window')
        if self.session_policy not in ('next','previous','strict'):raise ValueError('Invalid session policy')
        if self.comparison_mode not in ('family','consecutive','manual'):raise ValueError('Invalid comparison mode')
        if self.occupancy_mode not in ('continuous','rounded_labels','degree_buckets'):raise ValueError('Invalid occupancy mode')
        if self.clock_alignment_mode not in ('exact_phase','rounded_sector'):raise ValueError('Invalid clock alignment mode')
        self.scale=asdict(Scale(**self.scale));self.market=asdict(MarketSpec(**self.market))
        ContactSettings(**self.contacts);EphemProvider(self.coordinate_mode)
        return self

    @classmethod
    def from_dict(cls,d):
        if d.get('schema_version',1)!=1:raise ValueError('Unsupported workspace version')
        return cls(**d).validate()

@dataclass
class ResearchResult:
    settings: Settings
    metadata: dict
    positions: list
    events: list
    levels: list
    matches: list
    contacts: list
    confluences: list


def calculate(settings,data=None,provider=None,include_events=True):
    settings.validate();provider=provider or EphemProvider(settings.coordinate_mode)
    a,b=instant(settings.start),instant(settings.end)
    horizon=settings.horizon
    scale=Scale(**settings.scale)
    times=[];t=a
    while t<=horizon:
        times.append(t);t+=timedelta(hours=settings.step_hours)
    times.extend([horizon,instant(settings.selected)])
    if data is not None:times.extend(x.to_pydatetime() for x in data.frame.timestamp if a<=x<=horizon)
    times=sorted(set(t for t in times if a<=t<=horizon))
    if len(times)*len(settings.bodies)>200000:raise ValueError('Too many position rows; increase step or reduce date interval')
    positions=series(provider,settings.bodies,times)
    events=[]
    if include_events:
        events=aspects(provider,*settings.pair,a,horizon,settings.orb,tolerance=settings.tolerance_seconds)
        for body in settings.bodies:events.extend(body_events(provider,body,a,horizon,settings.tolerance_seconds,occupancy_mode=settings.occupancy_mode))
        events.extend(aspects(provider,'Mars','Saturn',a,horizon,settings.orb,tolerance=settings.tolerance_seconds,clock=True))
        if settings.clock_alignment_mode=='rounded_sector':events.extend(clock_sectors(provider,'Mars','Saturn',a,horizon,settings.tolerance_seconds))
        events.extend(combinations(events))
        events.sort(key=lambda e:e.exact or e.start)
    levels=[]
    for body in settings.bodies:
        rows=[r for r in positions if r['body']==body]
        if settings.monthly_sample:
            # Reproduction: interpolate full longitude between first-of-month samples.
            from .astronomy import delta
            for r in rows:
                t=r['timestamp'];first=t.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
                # The final supported month uses its actual final instant as the
                # terminal anchor, rather than requesting an out-of-range date.
                next_month=min((first.replace(day=28)+timedelta(days=4)).replace(day=1),MAX_TIME)
                x=provider.longitude(body,first);y=provider.longitude(body,next_month)
                x=r['unwrapped']+delta(x,r['longitude']);y=x+delta(y,x%360)
                r['plot_longitude']=scale.coordinate(x)+(scale.coordinate(y)-scale.coordinate(x))*(t-first)/(next_month-first)
        plotting_scale=Scale(**dict(settings.scale,rounding='continuous')) if settings.monthly_sample else scale
        for opposite in ([False,True] if settings.opposite else [False]):
            ks=plotting_scale.branches([r.get('plot_longitude',r['unwrapped']) for r in rows],settings.low,settings.high,scale.unit,opposite)
            for k in ks:
                for r in rows:
                    p=plotting_scale.price(r.get('plot_longitude',r['unwrapped']),k,opposite)
                    levels.append(dict(timestamp=r['timestamp'],id=f'{body}:{k}:{int(opposite)}',body=body,k=k,opposite=opposite,
                                       low=p,high=p,method='UC05-CHANNEL',longitude=r['longitude'],unwrapped=r['unwrapped']))
    bands=static_bands(scale,settings.low,settings.high,settings.halfway,settings.adjoining)
    for t in times:
        for band in bands:levels.append(dict(timestamp=t,**band))
    matches=compare_events(data,events,scale,instant(settings.selected),settings.session_policy,settings.window_days,settings.shifts,settings.last_family_dates,settings.conjunction_pairs,settings.comparison_mode,settings.sequences) if data is not None else []
    contact_rows=contacts(data,levels,scale,instant(settings.selected),ContactSettings(**settings.contacts)) if data is not None else []
    from . import __version__
    metadata=dict(software='AstroCalc Universal Clock',version=__version__,astronomy=provider.metadata(),
                  input_checksum=data.checksum if data is not None else None,data_report=data.report if data is not None else None,
                  synthetic=data.spec.synthetic if data is not None else False,source_method_ids=sorted({l['method'] for l in levels}|{e.method for e in events}),
                  numerical_tolerance_seconds=settings.tolerance_seconds,
                  coverage_start=a,coverage_end=horizon,future_horizon_clipped=settings.horizon_clipped,
                  monthly_terminal_anchor=MAX_TIME if settings.monthly_sample and horizon.year==2100 and horizon.month==12 else None)
    confluences=level_confluences([l for l in levels if l['timestamp']==instant(settings.selected)],MarketSpec(**settings.market).tick_size)
    return ResearchResult(settings,metadata,positions,events,levels,matches,contact_rows,confluences)
