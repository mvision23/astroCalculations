"""Lossless normalization and explicit conventions for the supplied Bitcoin history."""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import io

import numpy as np
import pandas as pd

from .market import MarketSpec, load_prices

UNIT = 369.0


def bitcoin_market():
    return MarketSpec(timezone='UTC', timestamp_kind='instant', bar_convention='open',
                      session_open='00:00', session_close='00:00', calendar='24/7',
                      bar_minutes=1440, tick_size=.01, quote_units='USD/BTC', symbol='BTC/USD',
                      adjustments='Source values unchanged; source adjustment methodology unspecified',
                      contract_roll='Spot-style supplied series; exchange/provider unspecified; no futures roll')


def normalize_bitcoin(content):
    """Retain every supplied bar; date-only Start/End are explicitly assumed UTC."""
    raw=pd.read_csv(io.BytesIO(content),encoding='utf-8-sig')
    required=['Start','End','Open','High','Low','Close','Volume','Market Cap']
    if not set(required)<=set(raw):raise ValueError(f'Expected source columns: {required}')
    starts=pd.to_datetime(raw.Start,utc=True,errors='raise')
    ends=pd.to_datetime(raw.End,utc=True,errors='raise')
    if not ((ends-starts).dt.total_seconds()==86400).all():raise ValueError('Expected one-day Start/End intervals')
    if starts.duplicated().any():raise ValueError('Duplicate Bitcoin start dates')
    numeric=raw[required[2:]].astype(float)
    if not np.isfinite(numeric.to_numpy()).all():raise ValueError('Nonfinite Bitcoin values')
    if (numeric[['Open','High','Low','Close']]<=0).any().any():raise ValueError('Log-return research requires positive prices')
    if not ((raw.Low<=raw[['Open','Close']].min(axis=1))&(raw.High>=raw[['Open','Close']].max(axis=1))).all():raise ValueError('Invalid Bitcoin OHLC')
    normalized=pd.DataFrame(dict(timestamp=starts.dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                 bar_end=ends.dt.strftime('%Y-%m-%dT%H:%M:%SZ')))
    for name in ('Open','High','Low','Close','Volume'):
        normalized[name.lower()]=raw[name]
    normalized['market_cap']=raw['Market Cap']
    normalized['source_start']=raw.Start
    normalized['source_end']=raw.End
    normalized['flat_ohlc']=raw.High==raw.Low
    normalized['zero_volume']=raw.Volume==0
    normalized=normalized.sort_values('timestamp').reset_index(drop=True)
    output=normalized.to_csv(index=False,float_format='%.17g').encode()
    imported=load_prices(output,bitcoin_market())
    actual=pd.DatetimeIndex(starts.sort_values())
    report=dict(source_sha256=sha256(content).hexdigest(),normalized_sha256=sha256(output).hexdigest(),
                rows=len(raw),first_start=str(actual.min().date()),last_start=str(actual.max().date()),
                last_available_at=ends.max().isoformat(),duplicate_dates=0,invalid_rows=0,
                missing_dates=pd.date_range(actual.min(),actual.max()).difference(actual).strftime('%Y-%m-%d').tolist(),
                flat_ohlc_rows=int(normalized.flat_ohlc.sum()),zero_volume_rows=int(normalized.zero_volume.sum()),
                sorted_ascending=True,filled_rows=0,discarded_rows=0,price_rescaling=False,
                timezone_assumption='Source has dates without timezone. Treat Start as UTC 00:00 inclusive and End as next UTC 00:00 exclusive.',
                source_identity='Provider, venue, volume units and adjustment methodology are not supplied.',
                tick_assumption='0.01 USD is a research/display setting, not a verified historical exchange tick; prices are not rounded to it.',
                market=asdict(bitcoin_market()),import_report=imported.report)
    return output,report


def data_root():
    """Use checkout data when installed editable; otherwise the working directory."""
    checkout=Path(__file__).resolve().parents[3]/'data'
    return checkout if checkout.is_dir() else Path.cwd()/'data'


def local_price_path(relative):
    root=data_root().resolve()
    path=(root/relative).resolve()
    if not path.is_relative_to(root) or path.suffix.lower() not in ('.csv','.parquet'):
        raise ValueError('Saved price files must be CSV/Parquet inside the local data directory')
    return path
