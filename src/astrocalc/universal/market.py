"""Validated price inputs and explicit session assignment; no inferred exchange calendar."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from hashlib import sha256
import io
import math
import pandas as pd
from pytz.exceptions import AmbiguousTimeError, NonExistentTimeError
from .astronomy import UTC, instant

@dataclass(frozen=True)
class MarketSpec:
    timezone: str = 'America/New_York'
    timestamp_kind: str = 'daily_label'
    bar_convention: str = 'close'
    session_open: str = '09:30'
    session_close: str = '16:00'
    calendar: str = 'weekdays'
    holidays: tuple = ()
    tick_size: float = .01
    quote_units: str = 'quoted units'
    adjustments: str = 'unspecified'
    contract_roll: str = 'unspecified'
    symbol: str = 'user data'
    synthetic: bool = False
    bar_minutes: int = 1440

    def __post_init__(self):
        object.__setattr__(self,'holidays',tuple(self.holidays))
        try:ZoneInfo(self.timezone)
        except KeyError as exc:raise ValueError(f'Unknown IANA timezone: {self.timezone}') from exc
        time.fromisoformat(self.session_open);time.fromisoformat(self.session_close)
        if self.timestamp_kind not in ('daily_label','instant'):raise ValueError('timestamp_kind: daily_label or instant')
        if self.bar_convention not in ('open','close'):raise ValueError('bar convention must be open or close')
        if self.calendar not in ('weekdays','24/7'):raise ValueError('calendar must be weekdays or 24/7')
        if not math.isfinite(self.tick_size) or self.tick_size<=0:raise ValueError('Tick size must be positive')
        if self.bar_minutes<=0:raise ValueError('Bar duration must be positive')
        for d in self.holidays:date.fromisoformat(d)

    def is_session(self,d):
        return (self.calendar=='24/7' or d.weekday()<5) and d.isoformat() not in self.holidays

    def bounds(self,d):
        zone=ZoneInfo(self.timezone)
        op=datetime.combine(d,time.fromisoformat(self.session_open),zone)
        cl=datetime.combine(d,time.fromisoformat(self.session_close),zone)
        if cl<=op:op-=timedelta(days=1) # date label is closing date for overnight sessions
        return op.astimezone(UTC),cl.astimezone(UTC)

    def session_date(self,t):
        """Nominal closing-date label, before applying holidays/weekends."""
        local=instant(t).astimezone(ZoneInfo(self.timezone));d=local.date()
        # Overnight sessions are labeled by their closing date, including the
        # 00:00–00:00 calendar-day bars used by continuously traded markets.
        opens=time.fromisoformat(self.session_open);closes=time.fromisoformat(self.session_close)
        if (closes<opens and local.time()>closes) or (closes==opens and local.time()>=closes):d+=timedelta(days=1)
        return d

    def assign(self,t,policy='next'):
        if policy not in ('strict','previous','next'):raise ValueError('Invalid session policy')
        d=self.session_date(t)
        if self.is_session(d):return d
        if policy=='strict':return None
        for _ in range(370):
            d+=timedelta(days=1 if policy=='next' else -1)
            if self.is_session(d):return d
        raise ValueError('No session in a year')

@dataclass
class MarketData:
    frame: pd.DataFrame
    spec: MarketSpec
    checksum: str
    report: dict
    ohlc: bool

    @property
    def has_ranges(self):
        return {'low','high'}<=set(self.frame.columns)

    def completed(self,asof):
        return self.frame[self.frame.available_at<=pd.Timestamp(instant(asof))]


def load_prices(content, spec=None, mapping=None, reject_invalid=True, parquet=False):
    spec=spec or MarketSpec();mapping=mapping or {}
    if isinstance(content,str):content=content.encode()
    raw=pd.read_parquet(io.BytesIO(content)) if parquet else pd.read_csv(io.BytesIO(content))
    mapped=[v for v in mapping.values() if v]
    if len(mapped)!=len(set(mapped)):raise ValueError('Map each source column to only one field')
    if not set(mapped)<=set(raw.columns):raise ValueError('Column mapping references a missing source column')
    # mapping is canonical name -> source column.
    raw=raw.rename(columns={v:k for k,v in mapping.items() if v})
    if 'timestamp' not in raw and 'date' in raw:raw=raw.rename(columns={'date':'timestamp'})
    if not {'timestamp','close'}<=set(raw):raise ValueError('Map timestamp/date and close columns')
    ohlc=all(c in raw for c in ('open','high','low'))
    if any(c in raw for c in ('open','high','low')) and not ohlc:raise ValueError('Supply all open/high/low columns or close only')
    fields=['close']+(['open','high','low'] if ohlc else [])+(['volume'] if 'volume' in raw else [])
    valid=[];rejected=[]
    for i,row in raw.iterrows():
        try:
            r=row.to_dict()
            for c in fields:
                r[c]=float(r[c])
                if not math.isfinite(r[c]):raise ValueError(f'Non-finite {c}')
            if ohlc and not r['low']<=min(r['open'],r['close'])<=max(r['open'],r['close'])<=r['high']:raise ValueError('Inconsistent OHLC range')
            if spec.timestamp_kind=='daily_label':
                value=str(r['timestamp'])
                if len(value)!=10:raise ValueError('Daily labels must be YYYY-MM-DD; use instant mode for timestamps')
                d=date.fromisoformat(value)
                if not spec.is_session(d):raise ValueError('Date is not in configured session calendar')
                op,cl=spec.bounds(d)
                t=op if spec.bar_convention=='open' else cl
            else:
                t=pd.Timestamp(r['timestamp'])
                if t.tzinfo is None:t=t.tz_localize(spec.timezone,ambiguous='raise',nonexistent='raise')
                t=t.tz_convert('UTC').to_pydatetime()
                cl=t if spec.bar_convention=='close' else t+timedelta(minutes=spec.bar_minutes)
                local=cl.astimezone(ZoneInfo(spec.timezone));d=local.date()
                if time.fromisoformat(spec.session_close)<=time.fromisoformat(spec.session_open) and local.time()>time.fromisoformat(spec.session_close):d+=timedelta(days=1)
                op,session_close=spec.bounds(d)
                if not spec.is_session(d) or not op<cl<=session_close:raise ValueError('Bar closes outside configured session')
            r.update(timestamp=t,session=d.isoformat(),available_at=cl)
            valid.append(r)
        except (ValueError,TypeError,OverflowError,AmbiguousTimeError,NonExistentTimeError) as exc:rejected.append({'row':i+2,'reason':str(exc)})
    if rejected and reject_invalid:raise ValueError(f'{len(rejected)} rejected rows of {len(raw)}. First: {rejected[:3]}. Choose explicit invalid-row removal to import the rest.')
    frame=pd.DataFrame(valid)
    if frame.empty:raise ValueError('No valid price rows')
    duplicates=int(frame.timestamp.duplicated(keep=False).sum())
    if duplicates:raise ValueError(f'{duplicates} rows have duplicate timestamps; resolve them in the source file')
    sorted_changed=not frame.timestamp.is_monotonic_increasing
    frame=frame.sort_values('timestamp').reset_index(drop=True)
    expected=set()
    if spec.timestamp_kind=='daily_label':
        d=date.fromisoformat(frame.session.min());end=date.fromisoformat(frame.session.max())
        while d<=end:
            if spec.is_session(d):expected.add(d.isoformat())
            d+=timedelta(days=1)
    report=dict(input_rows=len(raw),accepted_rows=len(frame),rejected_rows=len(rejected),rejections=rejected,
                sorted_rows=len(frame) if sorted_changed else 0,missing_sessions=sorted(expected-set(frame.session)),filled_rows=0,column_mapping=mapping)
    if spec.timestamp_kind=='instant':
        report['incomplete_sessions']=[d for d,rows in frame.groupby('session') if not _covers_session(rows,spec,date.fromisoformat(d))]
        report['intraday_completeness']='Continuous coverage from configured open through close, using bar duration; incomplete ranges are unavailable.'
    return MarketData(frame,spec,sha256(content).hexdigest(),report,ohlc)


def _covers_session(rows,spec,d):
    cursor,close=spec.bounds(d)
    for end in sorted(rows.available_at):
        start=end-timedelta(minutes=spec.bar_minutes)
        if start>cursor:return False
        cursor=max(cursor,end)
    return cursor>=close


def session_range(data,d,asof):
    if d is None:return None
    close=data.spec.bounds(d)[1]
    if instant(asof)<close:return None
    rows=data.completed(asof)
    rows=rows[rows.session==d.isoformat()]
    if rows.empty:return None
    if data.spec.timestamp_kind=='instant' and not _covers_session(rows,data.spec,d):return None
    # Close-only files cannot supply a source OHLC trading range.
    if not data.has_ranges:return None
    return dict(low=float(rows.low.min()),high=float(rows.high.max()),available_at=rows.available_at.max().to_pydatetime())


def event_ranges(data,event_time,asof,policy='next',window_days=1):
    strict=data.spec.assign(event_time,'strict');assigned=data.spec.assign(event_time,policy)
    local=data.spec.session_date(event_time)
    expanded=[]
    for offset in range(-window_days,window_days+1):
        d=local+timedelta(days=offset)
        r=session_range(data,d,asof)
        expanded.append(dict(session=d.isoformat(),range=r))
    return dict(astronomical_timestamp=event_time,strict_session=strict,assigned_session=assigned,
                strict=session_range(data,strict,asof),assigned=session_range(data,assigned,asof),expanded=expanded)


def book_ranges(name='sugar_daily',spec=None):
    """Sparse source transcriptions; deliberately no invented open/close values."""
    from importlib.resources import files
    import json
    catalogue=json.loads(files('astrocalc.universal').joinpath('book-fixtures.json').read_text())
    item=catalogue[name]
    spec=spec or MarketSpec(symbol=f'Book: {name}; sparse low/high only')
    records=[]
    for label,low,high in item['ranges']:
        d=date.fromisoformat(label);_,close=spec.bounds(d)
        records.append(dict(timestamp=close,available_at=close,session=label,low=low,high=high))
    content=json.dumps(item,sort_keys=True).encode()
    return MarketData(pd.DataFrame(records),spec,sha256(content).hexdigest(),
                      dict(source_fixture=name,printed_pages=item['printed'],pdf_pages=item['pdf'],sparse=True,
                           rows=len(records),ohlc=False,missing_prices='Not reconstructed; only selected printed ranges'),False)
