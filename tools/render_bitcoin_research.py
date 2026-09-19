"""Render the completed Bitcoin study and shared-engine app/Pine examples."""
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path
import argparse
import json
import platform

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from astrocalc.universal.astronomy import EphemProvider,instant
from astrocalc.universal.bitcoin import bitcoin_market,UNIT
from astrocalc.universal.exports import dumps,html_chart,bundle
from astrocalc.universal.geometry import Scale
from astrocalc.universal.market import load_prices
from astrocalc.universal.methods import evaluation
from astrocalc.universal.pine import build_tables,generate_pine
from astrocalc.universal.plotting import price_chart,wheel,theme
from astrocalc.universal.workspace import Settings,calculate


def markdown_table(frame,columns):
    lines=['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']
    for row in frame[columns].to_dict('records'):
        lines.append('| '+' | '.join(str(row[c]) for c in columns)+' |')
    return '\n'.join(lines)


def main(root):
    report=root/'reports/bitcoin';data_dir=root/'data'
    summary=json.loads((report/'summary.json').read_text());audit=summary['audit'];protocol=summary['protocol']
    scores=pd.read_csv(report/'planet-scores.csv')
    channels=pd.read_csv(report/'channel-controls.csv')
    motion=pd.read_csv(report/'motion-summary.csv')
    associations=pd.read_csv(report/'event-associations.csv').fillna({'family':''})
    data=load_prices((data_dir/'bitcoin_universal.csv').read_bytes(),bitcoin_market())
    comparison=json.loads((report/'aspect-range-comparisons.json').read_text())
    leaders=[]
    for term in ['short','intermediate','long']:
        row=scores[scores.term==term].sort_values('validation_rank').iloc[0]
        leaders.append({'Horizon':f'{term} ({row.horizon_days} days)','Validation leader':row.body+(' (extension)' if row.body=='Moon' else ''),
                        'Validation MSE skill':f'{100*row.validation_skill:.2f}%',
                        'Test MSE skill':f'{100*row.test_skill:.2f}%',
                        'Non-overlapping test cases':int(row.nonoverlap_cases),
                        'Supported':str(bool(row.supported))})
    leader_table=markdown_table(pd.DataFrame(leaders),list(leaders[0]))
    channel_view=channels[channels.split=='test'].sort_values('excess_percentage_points',ascending=False).copy()
    for field in ['either_hit_rate','shifted_control_mean']:channel_view[field]=channel_view[field].map(lambda v:f'{100*v:.2f}%')
    channel_view['excess_percentage_points']=channel_view.excess_percentage_points.map(lambda v:f'{v:+.2f}')
    channel_table=markdown_table(channel_view,['body','bars','either_hit_rate','shifted_control_mean','excess_percentage_points'])
    ranked=[]
    for term in ['short','intermediate','long']:
        for _,r in scores[scores.term==term].sort_values('validation_rank').iterrows():
            ranked.append(dict(term=term,body=r.body,validation_rank=int(r.validation_rank),
                               validation_skill=f'{100*r.validation_skill:.2f}%',test_skill=f'{100*r.test_skill:.2f}%',
                               test_RMSE=f'{r.test_rmse_logreturn:.4f}',zero_change_RMSE=f'{r.zero_return_rmse:.4f}',
                               adjusted_p=f'{r.holm_p:.3f}'))
    rank_table=markdown_table(pd.DataFrame(ranked),list(ranked[0]))
    top_events=associations[(associations.split=='test')&(associations.events>=20)].sort_values(['term','lift'],ascending=[True,False]).groupby('term').head(5).copy()
    for field in ['match_rate','calendar_baseline','lift']:top_events[field]=top_events[field].map(lambda x:f'{x:.3f}')
    event_table=markdown_table(top_events,['term','kind','bodies','family','events','match_rate','calendar_baseline','lift'])
    motion_view=motion.copy()
    for c in ['net_clock_turns','net_zodiac_turns','clock_drift_days','retrograde_fraction']:motion_view[c]=motion_view[c].map(lambda x:f'{x:.2f}')
    motion_table=markdown_table(motion_view,['body','net_zodiac_turns','net_clock_turns','clock_drift_days','retrograde_fraction'])
    text=f'''# Bitcoin Universal Clock research — $369 per step

**The study does not establish any planet as a reliable driver or predictor of Bitcoin cycles.**
All ten bodies fail the predeclared support criterion. Saturn is the most interesting
**exploratory long-horizon candidate** in this particular model comparison, but it
does not beat the simple zero-return forecast and has only three non-overlapping
yearly test cases. This is an observational study of the supplied history, not a
claim that the bodies cause market cycles or a buy/sell strategy.

## What to inspect by horizon

{leader_table}

- **Short term, 7-day target:** the Moon extension ranks first in validation but
  loses skill in the held-out period. Among the nine Book I bodies, Mercury, Sun
  and Venus are the least-poor validation candidates and form the app's short view.
  None improves on the price/calendar baseline in validation. The Sun's positive test
  result is post-selection/descriptive and fails the 30-comparison correction.
- **Intermediate term, 90-day target:** every body has negative validation skill.
  There is no supported selection. The app shows Sun, Mercury and Venus for
  comparison. Saturn's strong test-only result was not selected in validation and
  must not be promoted retrospectively to a validated finding.
- **Long term, 365-day target:** Saturn, Neptune and Pluto rank highest in
  validation, so those are the frozen long-view choices. Only Saturn remains
  positive against the fitted price/calendar baseline on test data; Neptune and
  Pluto deteriorate severely. Saturn's test log-return RMSE is
  {scores[(scores.term=='long')&(scores.body=='Saturn')].iloc[0].test_rmse_logreturn:.4f},
  versus {scores[scores.term=='long'].iloc[0].zero_return_rmse:.4f} for predicting
  no change. The apparent improvement over a weak fitted baseline is insufficient.

These lists identify useful **comparison overlays**, not established important
planets. The Moon is included in the statistical screen as a labeled extension
and is omitted from the default Book I app views. A negative result for this
specified linear model does not prove that every conceivable relationship is absent.

## Data conversion and quality

- Original input: `data/bitcoin_2010-07-02_2025-07-05.csv` (unaltered).
- Prepared input: `data/bitcoin_universal.csv`: {audit['rows']:,} ascending bars,
  starting **{audit['first_start']}**, last candle starting **{audit['last_start']}**,
  available at **{audit['last_available_at']}**. The filename's July 2 start is
  inconsistent with the actual July 17 first row.
- No missing calendar dates, duplicate dates, nonfinite prices, nonpositive prices
  or invalid OHLC. No rows dropped, forward-filled or reconstructed.
- {audit['flat_ohlc_rows']:,} flat OHLC rows, mostly 2010–early 2013, and
  {audit['zero_volume_rows']:,} zero-volume rows are retained and flagged. Such
  early OHLC may be close-like observations; it cannot establish intraday ranges.
  Main comparisons start January 2014; one later flat bar is excluded from range
  contact statistics. Volume is not used as a predictor because its units are unknown.
- The source supplies no venue, provider or timezone. **UTC midnight Start inclusive
  to End exclusive is an explicit assumption**, not verified exchange metadata.
  Candles plot at Start and become available only at End. Events inside a UTC day
  are compared with that day's candle, whose session label is the following midnight.
- All prices stay in supplied USD units, including small early decimals. Market cap,
  source Start/End, original volume and quality flags remain in the normalized CSV.
  A $0.01 tick is a display/research setting, not a verified historical venue tick.
- Source SHA256: `{audit['source_sha256']}`. Full provenance and validation are in
  [data-audit.json](data-audit.json). No prices after July 2025 were supplied or fetched.

## Fixed scale and app configuration

`u = $369` per numbered step, ordinary book mapping and no fitted anchor:

```text
planet branch:   P_k = 369 × (round_half_up(longitude) + 24k)
opposite branch: O_k = 369 × (round_half_up(longitude) + 12 + 24k)
full price cycle = $8,856; opposite/midpoint offset = $4,428
```

Static A–D bands remain one step ($369) wide at offsets 0, 6, 12 and 18 steps.
The user's scale was fixed before comparisons; it was not optimized on the test
set. No price-dependent nearest-branch stitching is used for plotted trajectories.
An absolute $369 step has a very different percentage size at early and recent
Bitcoin prices; its apparent contact behavior is therefore sensitive to price and
volatility regimes. The control ladders use the same spacing on the same days.

Launch `.venv/bin/universal-clock ui`, choose **Bitcoin research view** in the
sidebar, then **Load Bitcoin · $369**. The workspace loads the local normalized
file, UTC/24-hour sessions, USD quote units and locked scale automatically.

| Saved view | Display interval | Selected overlays |
|---|---|---|
| `data/bitcoin-workspaces/short.json` | Last 90 supplied days | Mercury, Sun, Venus |
| `data/bitcoin-workspaces/intermediate.json` | Last supplied year | Sun, Mercury, Venus |
| `data/bitcoin-workspaces/long.json` | Last four supplied years | Saturn, Neptune, Pluto |

The forecast target and visible chart span are different parameters. Change dates
to inspect any part of the full imported history. Future astronomy extends 30 days
from the last supplied close; it does not invent future candles. Manual annotations
state that these are exploratory selections.

## Protocol and controls

The protocol was written to [protocol.json](protocol.json) before model scoring.
Prices-only/calendar baseline features are trailing 7/30/90/365-day log returns,
30-day return volatility, a time trend, annual harmonics and weekday harmonics.
Each body adds longitude/clock-phase harmonics, speed, retrograde, 24-band occupancy
and the completed close's phase relative to the direct/opposite ladders. Continuous
astronomy is retained; nearest-degree rounding is applied only to the price mapping.
This feature study is a research extension, not a quoted book algorithm.

One fixed ridge penalty (10), training-only standardization, and clipping to five
training standard deviations are used. No hyperparameter or scale search is made.

1. Fit on 2014–2018; require each forward-return label to finish before 2019.
2. Rank bodies on 2019–2021; require validation labels to finish before 2022.
3. Refit using matured labels before 2022, freeze the model, and report the
   2022–July 2025 holdout. Labels extending beyond the file are unavailable.
4. Daily test predictions overlap. For inference, use every horizon-th case:
   183 short, 14 intermediate and 3 long cases. Adjacent two-case circular bootstrap
   blocks, 1,999 draws and seed 369 preserve some remaining dependence. Fewer than
   20 cases receive no inferential p-value. These blocks are not a guarantee of
   independence in a nonstationary market.
5. One-sided paired-loss tests are Holm-adjusted across all 30 body/horizon
   comparisons. Support requires the validation winner, positive validation and
   test skill, at least 20 cases, and adjusted p below .05. None qualifies.

MSE skill = `1 − planet_model_MSE / baseline_MSE`; positive is better. All RMSEs
below are in **log-return units**, not dollars or trading profits. The zero-return
benchmark exposes cases where beating the fitted baseline is still unhelpful.
The time-ordered evaluation follows the principle of keeping future observations
out of model fitting described in [Forecasting: Principles and Practice](https://otexts.com/fpp3/tscv.html).

{rank_table}

## Trajectory contact controls

Every day is checked against all branches intersecting its observed high/low,
using the longitude at the candle's **open**. Direct and opposite ladders are
reported separately and together, with zero price tolerance. For each planet,
239 fixed random phase rotations preserve its motion but shift its absolute ladder.
These controls make the density of parallel price levels visible. They are
descriptive controls, not proof of independence or forecasting significance.

{channel_table}

The holdout has 88 candles wider than the $4,428 combined-ladder spacing; they
necessarily contact some direct/opposite level for **every** planetary phase.
Raw touches alone are therefore not evidence of planetary importance. Pluto and
Neptune have higher observed contact rates here, but that is not a successful
out-of-sample prediction test. See [channel-controls.csv](channel-controls.csv).

## Exact events, ranges and turning points

The shared event engine calculated **{summary['event_count']:,} event/interval records**
over January 2014–the last supplied close, including all 45 body pairs (Moon
extension included), all seven aspect families and both branches, 0.3° orbs,
Mercury superior/inferior geometry, stations, ingresses, continuous 24-band visits,
simultaneous occupancy and Mars/Saturn matches anywhere on the clock.
Numerical event tolerance is one second; this is not one-second ephemeris accuracy.

The range study compares the last three dates in each aspect family with all
predeclared shifts `0, +0.5, +1, −0.5, −1` cycles. Strict UTC event-day and expanded
±1-calendar-day outcomes retain misses/unavailable cases, and sources must be
complete before the target event. No best shift is selected. Results are in
[aspect-range-comparisons.json](aspect-range-comparisons.json) and
[mercury-conjunction-ranges.json](mercury-conjunction-ranges.json).
These are descriptive matches; proximity in time and broad price ranges create
ordinary overlap without any predictive mechanism.

Turning points are retrospective close extrema with ±7, ±30 or ±180-day windows.
They are only confirmed after that many later bars. Event proximity radii are
±2, ±7 and ±30 days respectively. Incomplete edge windows are excluded. The table
below deliberately shows descriptive extremes among many screened groups, with at
least 20 holdout event dates; it **does not establish significant or tradable signals**.
Calendar baseline means the fraction of eligible calendar days near such a pivot.
Event intervals use boundary dates, with same-group/same-day duplicates collapsed.

{event_table}

All groups, including weak matches, remain in [event-associations.csv](event-associations.csv).
Pivot confirmation timestamps are in [retrospective-pivots.csv](retrospective-pivots.csv).
Examples worth inspecting, strictly as hypotheses from this retrospective screen,
are Mercury stations on the short horizon and Mars/Saturn clock coincidences on
the intermediate horizon. These were found by screening many groups on the test
period itself and require fresh data for validation; they do not replace the
validation-selected overlays or establish important market drivers.
The app's separate causal contact state records touches, tests, congestion, gaps,
confirmed closes and reversals; those annotations are not silently equated with
these retrospective pivots.

## What the history can resolve

{motion_table}

Net clock travel uses a 24° turn; zodiac travel uses 360°. Clock drift days are
the observed span divided by net clock turns, **not an orbital period** or a
stable cycle estimate. Retrograde loops can revisit levels and are retained.
The slow outer planets cover too little zodiac travel for this dataset to validate
their full cycles. A visual match to Bitcoin's few large historical swings is weak
evidence even when the plot looks persuasive.

## Project tool coverage and artifacts

| Tool family | Use in this study |
|---|---|
| Provider, coordinates, unwrapping | All nine Book I bodies plus optional Moon; apparent geocentric of date; daily exports |
| Exact aspects / stations / ingresses / bands | Full event archive and descriptive pivot association |
| Mercury pair / aspect-family ranges | Shared causal session comparison; all configured shifts and unavailable cases |
| Channels / opposite points / static divisions | $369 transforms, shifted controls, app charts, source-derived adjoining areas |
| Tests / gaps / congestion / confirmations | Shared contact state in chart workspaces and result bundle |
| Clock / zodiac / timeline / monthly calendar / replay | Available in loaded Bitcoin workspace; standalone price and clock examples |
| Manual sequences / annotations | Available for inspection; no fabricated automatic book sequence or planet handoff |
| All 12 legacy terminal workflows | Executed on 2024 (December for monthly workflows), exported in `legacy-2024.zip`; original J2000/sampled convention kept separate |
| Original concentric-circle prototype | Its role is covered by the integrated, scalable Universal Clock wheel; not imported as an interactive calculation engine |
| Pine generator | Actual Bitcoin indicator examples and finite ephemeris below; no TradingView compilation claimed |
| Statistical evaluation | Frozen chronological model screen, non-overlap inference and phase-rotation controls; explicit research extension |

The data neither supplies trading costs/venue details nor specifies an executable
entry/exit system. No returns from a trading strategy or causal effect are claimed.
Possible timezone mismatch, source quality, model choice, changing market regimes,
multiple exploration paths and very few long cycles limit interpretation.

The Pine example uses one Mercury overlay over the last 30 supplied days plus
30 further astronomical days, keeping source/drawing budgets small. It is an
exploratory chart example, not the selection of a validated signal. At this $369
scale, its smooth interpolation error is below the configured quarter-cent
target; nearest-degree rounding can still shift a level by a full $369 near a
half-degree threshold. See `pine/ephemeris.json` and the project's
[TradingView verification guide](../../docs/tradingview.md) before platform use.

## Reproduce

```sh
.venv/bin/python tools/analyze_bitcoin.py
.venv/bin/python tools/render_bitcoin_research.py
.venv/bin/universal-clock calculate --config data/bitcoin-workspaces/short.json --output /tmp/btc.zip
.venv/bin/universal-clock ui
```

The original supplied CSV is required to rerun normalization. Exact-event caching
checks interval, bodies, provider and astronomy/event source hashes. Normalized
prices and research artifacts are local; no external price data is downloaded.
Python {platform.python_version()}, PyEphem {summary['astronomy']['backend_version']}.
The report and examples can be regenerated; existing generated outputs are replaced.
Local integration checks and platform-verification limits are recorded in
[validation.md](validation.md).
'''
    (report/'report.md').write_text(text)
    # Compact interactive overview: log-price and all thirty held-out skill values.
    fig=make_subplots(rows=2,cols=1,vertical_spacing=.16,subplot_titles=['Supplied Bitcoin close · logarithmic USD axis','Held-out MSE skill · all screened bodies (positive is better)'])
    fig.add_trace(go.Scatter(x=data.frame.timestamp,y=data.frame.close,mode='lines',name='BTC/USD close',line_color='#e8b65b'),row=1,col=1)
    fig.update_yaxes(type='log',title_text='USD/BTC',row=1,col=1)
    for term in ['short','intermediate','long']:
        values=scores[scores.term==term]
        fig.add_trace(go.Bar(x=values.body,y=100*values.test_skill,name=f'{term}: {int(values.horizon_days.iloc[0])} days',customdata=values.nonoverlap_cases,
                            hovertemplate='%{x}<br>skill %{y:.2f}%<br>nonoverlap cases %{customdata}<extra></extra>'),row=2,col=1)
    fig.add_hline(y=0,line_dash='dash',row=2,col=1)
    fig.update_layout(height=1000,barmode='group')
    theme(fig,'Bitcoin · $369 research · no validated planetary predictor')
    (report/'overview.html').write_text(html_chart(fig,summary))
    render_views(root)


def render_views(root):
    report=root/'reports/bitcoin';data_dir=root/'data'
    data=load_prices((data_dir/'bitcoin_universal.csv').read_bytes(),bitcoin_market())
    config=Settings.from_dict(json.loads((data_dir/'bitcoin-workspaces/short.json').read_text()))
    result=calculate(config,data)
    metadata=dict(result.metadata,settings=asdict(config))
    (report/'bitcoin-price.html').write_text(html_chart(price_chart(result,data),metadata))
    (report/'bitcoin-clock.html').write_text(html_chart(wheel(result,data,dates=data.frame.session.tail(3).tolist()),metadata))
    (report/'bitcoin-short-results.zip').write_bytes(bundle(result))
    # Keep Pine examples comfortably within platform source/plot budgets.
    pine_config=Settings.from_dict(asdict(config));pine_config.bodies=[config.bodies[0]]
    pine_config.start=(instant(config.end)-timedelta(days=30)).isoformat()
    close=float(data.frame.close.iloc[-1]);pine_config.low=np.floor((close-8856)/369)*369;pine_config.high=np.ceil((close+8856)/369)*369
    pine_dir=report/'pine';pine_dir.mkdir(exist_ok=True)
    (pine_dir/'workspace.json').write_text(dumps(pine_config))
    pine_result=calculate(pine_config,data);provider=EphemProvider()
    tables=build_tables(provider,pine_config.bodies,instant(pine_config.start),pine_config.horizon,Scale(**pine_config.scale),.01,.25,.002)
    for pane,name in [(False,'overlay'),(True,'degrees')]:
        source,meta=generate_pine(tables,pine_result.events,pine_config,pine_result.metadata,pane)
        (pine_dir/f'bitcoin_369_{name}.pine').write_text(source)
        if not pane:(pine_dir/'ephemeris.json').write_text(dumps(dict(tables=[asdict(t) for t in tables],metadata=meta)))
    print('Wrote price/clock charts, result bundle and Pine examples.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--views-only',action='store_true',help='Build chart/Pine examples while the exact-event study is running')
    args=parser.parse_args()
    (render_views if args.views_only else main)(args.root)
