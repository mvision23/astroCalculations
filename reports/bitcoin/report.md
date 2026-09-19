# Bitcoin Universal Clock research — $369 per step

**The study does not establish any planet as a reliable driver or predictor of Bitcoin cycles.**
All ten bodies fail the predeclared support criterion. Saturn is the most interesting
**exploratory long-horizon candidate** in this particular model comparison, but it
does not beat the simple zero-return forecast and has only three non-overlapping
yearly test cases. This is an observational study of the supplied history, not a
claim that the bodies cause market cycles or a buy/sell strategy.

## What to inspect by horizon

| Horizon | Validation leader | Validation MSE skill | Test MSE skill | Non-overlapping test cases | Supported |
|---|---|---|---|---|---|
| short (7 days) | Moon (extension) | 0.62% | -0.97% | 183 | False |
| intermediate (90 days) | Moon (extension) | -0.41% | -0.39% | 14 | False |
| long (365 days) | Saturn | 86.76% | 65.81% | 3 | False |

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
  0.7471,
  versus 0.6646 for predicting
  no change. The apparent improvement over a weak fitted baseline is insufficient.

These lists identify useful **comparison overlays**, not established important
planets. The Moon is included in the statistical screen as a labeled extension
and is omitted from the default Book I app views. A negative result for this
specified linear model does not prove that every conceivable relationship is absent.

## Data conversion and quality

- Original input: `data/bitcoin_2010-07-02_2025-07-05.csv` (unaltered).
- Prepared input: `data/bitcoin_universal.csv`: 5,467 ascending bars,
  starting **2010-07-17**, last candle starting **2025-07-04**,
  available at **2025-07-05T00:00:00+00:00**. The filename's July 2 start is
  inconsistent with the actual July 17 first row.
- No missing calendar dates, duplicate dates, nonfinite prices, nonpositive prices
  or invalid OHLC. No rows dropped, forward-filled or reconstructed.
- 1,018 flat OHLC rows, mostly 2010–early 2013, and
  1,259 zero-volume rows are retained and flagged. Such
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
- Source SHA256: `2421b4b720866c363bbd07cc7ca14289e5dd560804d036347397d03ef5bb57d5`. Full provenance and validation are in
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

| term | body | validation_rank | validation_skill | test_skill | test_RMSE | zero_change_RMSE | adjusted_p |
|---|---|---|---|---|---|---|---|
| short | Moon | 1 | 0.62% | -0.97% | 0.0777 | 0.0745 | 1.000 |
| short | Mercury | 2 | -1.04% | -5.90% | 0.0796 | 0.0745 | 1.000 |
| short | Sun | 3 | -1.48% | 1.25% | 0.0769 | 0.0745 | 1.000 |
| short | Venus | 4 | -3.94% | -1.75% | 0.0780 | 0.0745 | 1.000 |
| short | Uranus | 5 | -27.07% | -7.75% | 0.0803 | 0.0745 | 1.000 |
| short | Mars | 6 | -32.73% | -11.61% | 0.0817 | 0.0745 | 1.000 |
| short | Neptune | 7 | -95.10% | -1.30% | 0.0779 | 0.0745 | 1.000 |
| short | Jupiter | 8 | -199.54% | -53.02% | 0.0957 | 0.0745 | 1.000 |
| short | Saturn | 9 | -271.21% | 6.72% | 0.0747 | 0.0745 | 1.000 |
| short | Pluto | 10 | -313.31% | -0.34% | 0.0775 | 0.0745 | 1.000 |
| intermediate | Moon | 1 | -0.41% | -0.39% | 0.4412 | 0.2973 | 1.000 |
| intermediate | Sun | 2 | -0.46% | 0.22% | 0.4398 | 0.2973 | 1.000 |
| intermediate | Mercury | 3 | -2.71% | 0.05% | 0.4402 | 0.2973 | 1.000 |
| intermediate | Venus | 4 | -29.03% | -0.77% | 0.4420 | 0.2973 | 1.000 |
| intermediate | Mars | 5 | -231.49% | -37.36% | 0.5161 | 0.2973 | 1.000 |
| intermediate | Pluto | 6 | -242.64% | -20.56% | 0.4835 | 0.2973 | 1.000 |
| intermediate | Neptune | 7 | -503.83% | -31.01% | 0.5040 | 0.2973 | 1.000 |
| intermediate | Uranus | 8 | -977.46% | -81.56% | 0.5933 | 0.2973 | 1.000 |
| intermediate | Jupiter | 9 | -1151.49% | -856.64% | 1.3619 | 0.2973 | 1.000 |
| intermediate | Saturn | 10 | -2018.84% | 60.54% | 0.2766 | 0.2973 | 1.000 |
| long | Saturn | 1 | 86.76% | 65.81% | 0.7471 | 0.6646 | 1.000 |
| long | Neptune | 2 | 70.85% | -708.05% | 3.6319 | 0.6646 | 1.000 |
| long | Pluto | 3 | 56.69% | -2651.99% | 6.7026 | 0.6646 | 1.000 |
| long | Uranus | 4 | 47.90% | -63.17% | 1.6321 | 0.6646 | 1.000 |
| long | Jupiter | 5 | 31.91% | -1701.88% | 5.4235 | 0.6646 | 1.000 |
| long | Venus | 6 | 6.36% | 15.13% | 1.1771 | 0.6646 | 1.000 |
| long | Moon | 7 | 0.32% | -0.21% | 1.2790 | 0.6646 | 1.000 |
| long | Mercury | 8 | -0.62% | -1.64% | 1.2881 | 0.6646 | 1.000 |
| long | Sun | 9 | -1.29% | 0.25% | 1.2760 | 0.6646 | 1.000 |
| long | Mars | 10 | -30.06% | 25.89% | 1.0999 | 0.6646 | 1.000 |

## Trajectory contact controls

Every day is checked against all branches intersecting its observed high/low,
using the longitude at the candle's **open**. Direct and opposite ladders are
reported separately and together, with zero price tolerance. For each planet,
239 fixed random phase rotations preserve its motion but shift its absolute ladder.
These controls make the density of parallel price levels visible. They are
descriptive controls, not proof of independence or forecasting significance.

| body | bars | either_hit_rate | shifted_control_mean | excess_percentage_points |
|---|---|---|---|---|
| Pluto | 1282 | 41.11% | 38.06% | +3.04 |
| Neptune | 1282 | 40.41% | 38.06% | +2.34 |
| Sun | 1282 | 39.16% | 37.98% | +1.18 |
| Mars | 1282 | 38.92% | 37.94% | +0.98 |
| Mercury | 1282 | 38.61% | 38.04% | +0.57 |
| Saturn | 1282 | 37.21% | 38.09% | -0.88 |
| Jupiter | 1282 | 36.35% | 37.94% | -1.59 |
| Venus | 1282 | 35.96% | 37.85% | -1.89 |
| Uranus | 1282 | 35.88% | 37.88% | -1.99 |
| Moon | 1282 | 34.17% | 37.96% | -3.80 |

The holdout has 88 candles wider than the $4,428 combined-ladder spacing; they
necessarily contact some direct/opposite level for **every** planetary phase.
Raw touches alone are therefore not evidence of planetary importance. Pluto and
Neptune have higher observed contact rates here, but that is not a successful
out-of-sample prediction test. See [channel-controls.csv](channel-controls.csv).

## Exact events, ranges and turning points

The shared event engine calculated **26,265 event/interval records**
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

| term | kind | bodies | family | events | match_rate | calendar_baseline | lift |
|---|---|---|---|---|---|---|---|
| intermediate | clock_alignment | Mars/Saturn | clock coincidence | 27 | 0.407 | 0.303 | 1.346 |
| intermediate | aspect | Uranus/Moon | conjunction | 46 | 0.370 | 0.303 | 1.221 |
| intermediate | aspect | Venus/Moon | opposition | 42 | 0.357 | 0.303 | 1.180 |
| intermediate | aspect | Neptune/Moon | sextile | 92 | 0.348 | 0.303 | 1.149 |
| intermediate | aspect | Pluto/Moon | opposition | 46 | 0.348 | 0.303 | 1.149 |
| long | simultaneous_24 | Jupiter/Moon |  | 25 | 0.280 | 0.166 | 1.686 |
| long | 24_band | Mercury |  | 91 | 0.264 | 0.166 | 1.588 |
| long | simultaneous_24 | Mars/Moon |  | 21 | 0.238 | 0.166 | 1.434 |
| long | ingress | Venus |  | 38 | 0.211 | 0.166 | 1.268 |
| long | aspect | Neptune/Moon | opposition | 40 | 0.200 | 0.166 | 1.204 |
| short | simultaneous_24 | Moon/Uranus |  | 55 | 0.600 | 0.459 | 1.308 |
| short | simultaneous_24 | Moon/Saturn |  | 36 | 0.556 | 0.459 | 1.211 |
| short | station | Mercury |  | 22 | 0.545 | 0.459 | 1.189 |
| short | aspect | Saturn/Moon | opposition | 46 | 0.543 | 0.459 | 1.185 |
| short | 24_band | Venus |  | 105 | 0.543 | 0.459 | 1.183 |

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

| body | net_zodiac_turns | net_clock_turns | clock_drift_days | retrograde_fraction |
|---|---|---|---|---|
| Sun | 11.51 | 172.62 | 24.35 | 0.00 |
| Mercury | 11.58 | 173.63 | 24.21 | 0.19 |
| Venus | 11.34 | 170.15 | 24.70 | 0.08 |
| Mars | 5.91 | 88.69 | 47.39 | 0.10 |
| Jupiter | 0.97 | 14.57 | 288.53 | 0.30 |
| Saturn | 0.37 | 5.48 | 766.97 | 0.37 |
| Uranus | 0.14 | 2.13 | 1969.47 | 0.40 |
| Neptune | 0.08 | 1.21 | 3484.47 | 0.42 |
| Pluto | 0.06 | 0.91 | 4627.60 | 0.44 |
| Moon | 153.84 | 2307.64 | 1.82 | 0.00 |

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
Python 3.13.7, PyEphem 4.2.
The report and examples can be regenerated; existing generated outputs are replaced.
Local integration checks and platform-verification limits are recorded in
[validation.md](validation.md).
