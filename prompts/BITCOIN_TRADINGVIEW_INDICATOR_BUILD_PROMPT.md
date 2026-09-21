# Build prompt: Bitcoin Universal Clock indicator for TradingView

Build a complete Pine Script v6 indicator named **Bitcoin Universal Clock**, installed through TradingView's Pine Editor and added directly to the Bitcoin price chart with `overlay=true`. It must show all supported planetary price trajectories, with independent on/off controls, and expose the applicable parameters and methods in the existing local Universal Clock application.

Implement the indicator, its Python ephemeris generator, tests, and documentation. Deliver actual ready-to-paste `.pine` files containing real generated data. Do not stop at a plan, a template, or a single-planet demonstration.

## 1. Required architecture and existing code

Use **locally generated ephemeris data**, as already selected for this project. Python calculates planetary positions and refined astronomical events using the application's astronomy provider. Pine reads embedded tables, interpolates positions by UTC timestamp, applies the price transformations, and draws the indicator. Do not implement a native Pine orbital model or use constant-speed approximations as a fallback.

The repository is `astroCalculations/`. Inspect its current instructions and changes before editing. Reuse and improve these existing modules:

- `src/astrocalc/universal/app.py`: actual UI controls and defaults.
- `workspace.py`: `Settings` and shared result schemas.
- `astronomy.py`, `events.py`: providers, coordinates, event detection.
- `geometry.py`: `Scale`, book rounding, branches, static divisions.
- `methods.py`, `market.py`: presets, contacts, comparisons and session semantics.
- `pine.py`, `cli.py`: existing generation and export commands.
- `docs/universal-clock.md`, `docs/tradingview.md`, `docs/book-methods.md`.
- `data/bitcoin-workspaces/*.json`, `reports/bitcoin/pine/workspace.json`, and existing Pine tests.

Resolve these paths relative to the actual checkout. Preserve the working local application and unrelated changes.

At the time this brief was written, the local Bitcoin preset uses **369 quoted price units per wheel step**, but its research views select subsets of planets and the saved Bitcoin Pine workspace contains only Mercury. Existing Pine export offers fewer controls than the application. These are starting points, not the finished requirements. Generate new coverage and all required bodies rather than reusing the old Mercury-only artifact as the deliverable.

## 2. One primary indicator with every body available

Embed all nine bodies used in Book I in the primary indicator:

**Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, and Pluto.**

Include the Moon as an additional selectable extension, disabled by default. Earth is the geocentric observer and must not be given an invented geocentric trajectory.

Provide an independent visibility checkbox and color for each body. All nine book bodies must be available and able to appear simultaneously in the same indicator. Toggling a body must not require regeneration. Add grouped visibility modes such as All, Custom, and Hide all, without pretending Pine can programmatically change the values of other input widgets. Define how the master mode and individual toggles combine.

A disabled body's price curves, future curves, labels and body-specific alerts disappear. Define a separate policy for pair-event markers so hiding one trajectory does not ambiguously change aspect selection. Preserve user color and visibility choices through ordinary chart recalculation.

Provide a usable default number of channel branches for all nine bodies within the resource budget. Allow additional branches within explicit limits. Splitting essential planets into separate scripts is not an acceptable replacement for the primary all-planets indicator. An optional degrees pane or detailed analysis companion is acceptable.

## 3. Bitcoin chart behavior

Use the active TradingView chart's candles, symbol, quote currency, timeframe and tick size. Work with Bitcoin spot and perpetual charts from different exchanges; do not hardcode a particular provider. Show the actual `syminfo.tickerid` in an optional status table. Bitcoin defaults to a 24/7 calendar and UTC research sessions.

Keep the chart's candles visible. Do not overlay another set of Bitcoin candles or embed the local historical price CSV as a substitute for TradingView data. USD and USDT are distinct quote labels; show the chart's actual quote and interpret the scale in that quote. A historical `369 USD/BTC` preset must not imply an exchange-rate conversion on another quote currency.

Support normal time-based charts, including intraday, daily and weekly views. Compute astronomy using timestamps, not accumulated bar counts. Document behavior on synthetic/non-time-based charts; avoid claiming price-contact equivalence to real OHLC there. Logarithmic chart display must not change the numerical price transformation.

Keep chronological astronomy separate from market sampling. Default to evaluating a bar's trajectory at its opening timestamp, matching current Pine export. Offer a documented close-time mode where valid; use only confirmed bars for price-based alerts. Define handling of unavailable `time_close` values. On higher timeframes, the indicator samples positions at the selected bar instant rather than averaging planetary degrees.

## 4. Match the app's price transformation exactly

Use the existing `Scale` implementation as the numerical reference:

```text
u = positive quoted price units per wheel step; Bitcoin preset u = 369
L(t) = continuous unwrapped ecliptic longitude
Q(L) = floor(L + 0.5) in book mode, or L in continuous mode

Unanchored channel:  P_k(t) = u * (Q(L(t)) + 24*k)
Opposite channel:   O_k(t) = u * (Q(L(t)) + 24*k + 12)

Anchored extension:
P_k(t) = P0 + u * (Q(L(t)) - L0 + 24*k)
O_k(t) = P0 + u * (Q(L(t)) - L0 + 24*k + 12)
```

Expose unit, book/continuous mode, anchor enabled, anchor price `P0`, anchor longitude `L0`, and branch selection. Do not round `L0` unless the local implementation does. At `u=369`, adjacent main channels differ by **8,856** and the opposite offset is **4,428** quoted units. This scale is an existing research preset, not a proven optimal Bitcoin setting.

Keep each branch's identity fixed through time, including retrograde motion and longitude wrap. Do not choose the nearest line to each bar's close and connect the results into an artificial trajectory. Allow manual branch indices. A convenience branch selection may use a fixed user-selected reference timestamp/price; resolve it once per configuration and identify any resulting retrospective view. Do not silently re-anchor on the latest price during replay.

Distinguish selecting branches within `low`/`high` from clipping rendered curves: hiding a value outside the requested range must not stitch different branch identities together. Price-range inputs filter the indicator's output; they do not claim to set TradingView's price-axis bounds.

Draw rounded book trajectories as steps and continuous trajectories as smooth sampled lines. Opposite points are halfway around the 24-step clock, distinct from labeling an astronomical 180° aspect.

## 5. Account for every app parameter

Create `docs/bitcoin-pine-parameters.md` with one row per field in `Settings`, nested `Scale`, `MarketSpec`, `ContactSettings`, and every relevant additional UI control in `app.py`. Record the app name, Pine name, default, units, scope, implementation, and test. Add a schema-completeness check so new or forgotten fields cannot be silently omitted.

Classify each control as **editable in Pine**, **export-time setting requiring regeneration**, **chart-derived**, or **local-only with a specific reason**. Do not add a Pine input that changes a label without changing its calculation. Do not advertise full parity if a setting is unsupported. This is the required starting mapping:

| App settings / control group | Required treatment |
| --- | --- |
| `bodies` | Embed every supported body; expose individual runtime toggles. |
| `scale.unit`, `rounding`, `anchored`, `anchor_price`, `anchor_longitude` | Editable Pine controls with Python parity. Show `quote_units` consistently with the chart. |
| `scale_locked`, `preset` | Preset/manual scale mode with explicit effective scale; document how it reproduces the local scale lock. Retain the Bitcoin 369 preset. |
| `low`, `high` | Editable branch/display price bounds and bounded channel selection. |
| `start`, `end`, `future_days` | Generated coverage plus runtime display start/end and future horizon constrained to that coverage. |
| `selected` / replay | TradingView Bar Replay for price history and optional inspection timestamp for the values table. Pine inputs must not pretend to control TradingView replay. |
| `coordinate_mode` | Generation-time choice: currently `apparent_of_date`, `astrometric_of_date`, or `legacy_j2000`; show the effective mode. Runtime switching only if all selected modes are truly embedded and validated. |
| `step_hours`, `tolerance_seconds` | Generation-time position/event settings; distinguish local plot sampling, adaptive Pine knot spacing and event solver tolerance. |
| Export interpolation error, tick fraction, maximum knot spacing | Generation-time controls with measured metadata. Runtime changes to unit/tick assumptions must update reported price-error estimates. |
| `pair`, `orb` | Runtime pair/orb only for a genuinely supported embedded event configuration; otherwise regenerate explicitly. Support all seven aspect families and both phase branches. |
| `occupancy_mode`, `clock_alignment_mode` | Support generated event variants for `continuous`, `rounded_labels`, `degree_buckets`, and `exact_phase` / `rounded_sector`; identify when regeneration is required. |
| `opposite` | Runtime toggle for opposite/midpoint trajectories. |
| `halfway`, `adjoining`, static-division visibility | Runtime toggles for halfway lines and source-derived adjoining areas, independently of A–D bands. |
| `monthly_sample` | Implement matching monthly reproduction data if feasible; otherwise document the existing explicit export rejection. Never ignore the setting or claim adaptive knots reproduce monthly sampling. |
| `contacts.tolerance_ticks`, `field`, `separation_bars`, `congestion_bars`, `confirmation_bars` | Runtime controls for a causal contact state machine using chart prices and `syminfo.mintick`, with optional explicit tick override. |
| `session_policy`, `window_days`, `last_family_dates`, `comparison_mode`, `conjunction_pairs`, `shifts` | Range-comparison controls using chart-derived completed research sessions and supported embedded events; follow section 7. Clearly delimit any remaining unsupported comparison mode. |
| `sequences`, `annotations` | Bounded manual time/text inputs or generated annotations where practical; identify local editing/persistence functions separately. No hidden local-price dependency. |
| Market `symbol`, `tick_size`, `bar_minutes`, `bar_convention`, `timestamp_kind` | Chart-derived defaults; expose meaningful overrides and document their effects. Distinguish local date-label parsing from actual TradingView bar timestamps. |
| Market `timezone`, `session_open`, `session_close`, `calendar`, `holidays` | UTC/24/7 Bitcoin defaults; explicit research-session controls for comparisons. Preserve the application's closing-date convention or document a deliberate mapped convention. |
| Market `adjustments`, `contract_roll`, `synthetic`, workspace `schema_version` | Provenance/metadata, not fake controls that alter TradingView's feed. |
| `price_file`, `column_mapping`, uploaded CSV/Parquet, invalid-row handling | Local importer only. Pine consumes TradingView chart OHLC. |
| Ring labels, ordinary zodiac/Universal Clock view, radial zoom, wheel price-range shifts/labels | Keep the circular research UI local; preserve underlying numeric values in the optional inspection table and document this UI boundary. |
| Astronomy unwrapped/wrapped/phase/speed controls | Optional companion pane with the same data and body toggles; do not put degree series on Bitcoin's price scale. |
| Event type filters, calendar month and display timezone | Runtime filters and bounded event/status table where possible; time formatting must not change event instants. |
| Workspace reopening, image/HTML/CSV exports, scale comparison reports | Local generator/research workflow; document equivalent configuration and generation steps. |

Use grouped Pine inputs, concise tooltips and sensible defaults. Distinguish generation requirements in documentation and status metadata without cluttering every chart label with implementation details.

## 6. Static levels, trajectories and astronomical events

Reuse `static_bands()` rather than approximating its geometry. Draw multiple bounded cycles as needed, with separate controls for:

- A/24-line bands at `u*[24*k,24*k+1]`.
- B/C/D bands at offsets 6, 12 and 18.
- Halfway lines at offsets **3.5, 9.5, 15.5 and 21.5**, matching the app's gap midpoints.
- Adjoining areas: for each A–D offset `d`, support spans `[d-2.5,d]` and resistance spans `[d+1,d+3.5]`, translated by `24*k` and scaled by `u`.

Match the local distinction between anchored planetary curves and its unanchored static grid. If a grid anchoring extension is added, expose and label it separately.

Support toggles for refined conjunction/aspect markers, stations, sign ingresses, 24-line entry/exit and occupancy, multi-body occupancy, and Mars/Saturn clock alignment. Store event IDs, bodies, type, target, exact time and interval boundaries so filters work correctly. Avoid duplicating a multi-day event on every bar.

Exact event timestamps come from Python's event engine. Runtime filtering of embedded events is permitted; changing an orb or pair must not relabel event records calculated with different parameters. If selectable event variants are impractical, keep those arguments in the generator and make the selected configuration clear. Avoid embedding every possible pair merely to simulate a dropdown.

Future trajectories use the embedded astronomical data, bounded by coverage. Use time-based drawing coordinates, including `chart.point.from_time` and `xloc.bar_time` where appropriate. Expose future days, visibility, style and transparency. Draw future astronomy only; future Bitcoin candles and future price-contact outcomes are unknown.

## 7. Chart-price methods and alerts

Extend the current basic contact alert to match the app's applicable causal methods: touches, crossing/close-through, separated second tests, congestion and confirmation. Provide per-feature visibility and alert selection. Each record should identify the body, branch, event type, timestamp and effective price level. A hidden trajectory must not unexpectedly produce price-contact alerts.

For source-range boxes and target windows, use **TradingView's completed Bitcoin OHLC sessions**, not source highs/lows embedded from the local CSV. Support family/consecutive comparisons, configured previous-event counts and cycle shifts, and superior-to-following-inferior Mercury/Sun pairing. Expose bounded manual sequences or document their local-only editor. Retain misses and unavailable data rather than selecting only successful shifts.

Do not equate one intraday candle with a completed daily source range. Define UTC/session aggregation explicitly. For weekly charts either retrieve the required lower-timeframe session data correctly within Pine limits or visibly disable daily comparisons with a reason. Insufficient loaded history is unavailable data, not a zero range. Comparison bands become available only after the source session closes, and expanded-window outcomes only after the necessary observations exist.

All price-based alerts use confirmed data and must behave consistently in Bar Replay. Future precomputed astronomical events may be displayed; future market data may not influence historical signals. Prefer bounded selectable dynamic alerts if individual `alertcondition()` calls would exhaust plot counts. Do not convert this research indicator into an automatic buy/sell strategy or claim predictive accuracy.

## 8. Ephemeris coverage and resource management

Extend the existing generator to emit one usable all-body artifact plus a manifest. Select a contemporary finite interval at generation time, record exact dates, and include future coverage. Start with a practical target such as 90 historical days plus 30 future days, then measure feasibility. If tighter coverage or different precision is needed, state the tradeoff explicitly; preserve all nine required bodies. Supply a separate small historical fixture for wrap/station validation.

Adaptive tables must preserve retrograde loops and longitude continuity. Use efficient timestamp lookup and independent interpolation probes, including between exported knots after numeric serialization. Record angular maximum/RMS error, sample count, largest spacing, coordinate convention and price-error conversion.

Separate an angular-error visualization target from an optional strict fraction-of-a-tick target. At a Bitcoin scale of 369 and tick size 0.01, even a tiny angular tolerance can imply many samples. Never silently relax precision, drop planets or call sub-dollar interpolation sub-tick accurate. In book rounding mode, a small error near a half-degree boundary can change a plotted level by a whole wheel unit; report and test that discontinuity separately.

Outside coverage return `na`, suppress dependent alerts, and show the coverage interval and regeneration instruction. Do not extrapolate, freeze endpoints or add an analytical fallback. Increasing a runtime future-horizon input cannot extend the embedded data.

Pine cannot directly execute the local Python project or read arbitrary local ephemeris files. Embed the data in the emitted source. Verify current platform behavior using official documentation before implementation:

- [Pine limits](https://www.tradingview.com/pine-script-docs/writing/limitations/): currently 64 plot counts and 100,000 elements per collection, plus compilation and runtime limits. Input toggles do not remove compiled plot counts.
- [Lines, boxes and polylines](https://www.tradingview.com/pine-script-docs/visuals/lines-and-boxes/): use bounded drawings and time coordinates for future trajectories.
- [Other timeframes and data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/): use chart/session data honestly; do not invent a planetary ticker or depend on a new external feed.

Calculate budgets for all enabled bodies, channel branches, optional Moon, events, fills, alerts and drawings. Keep headroom. Static bands can use bounded drawings to preserve plot capacity. Reuse/delete owned drawing objects without deleting unrelated indicator features. Window event drawings instead of allocating every historical event forever. Decimate only visual curves within measured error; retain the calculation data required for lookup and alerts.

Every allowed input combination must either run within the documented budget or be rejected clearly. Provide a default with all nine book bodies visible. Do not solve resource pressure by quietly delivering one planet or requiring nine indicators.

## 9. Deliverables and acceptance criteria

Deliver:

1. `pine/bitcoin_universal_clock.pine`: complete overlay with embedded ephemeris and all required planet controls.
2. Optional `pine/bitcoin_universal_clock_degrees.pine`: longitude/phase/speed companion.
3. Improved shared Python exporter and a reproducible all-body Bitcoin workspace/configuration. Preserve existing CLI functionality and document the exact generation command.
4. A manifest identifying bodies, UTC coverage, coordinates, interpolation measurements, generation settings and estimated resource use.
5. The exhaustive parameter mapping, installation guide, coverage-extension instructions and local/Pine limitations.
6. Tests for astronomy/price parity, parameter behavior, event filtering, contact/range semantics, and existing application regressions.

Acceptance checks:

- The primary script starts with `//@version=6`, uses `indicator(..., overlay=true)`, and contains data for all nine book bodies plus the optional Moon extension.
- Each planet can be toggled independently without regeneration; all nine work together. Colors, branches, opposite lines, future curves, labels and relevant alerts follow their controls.
- Unit 369 produces 8,856 spacing and 4,428 opposite offsets. Book rounding, continuous mode, anchors, static midpoints and adjoining areas match Python fixtures.
- Interpolation preserves Mercury retrograde and zodiac wrap. Branch identity and out-of-range behavior remain correct on different timeframes.
- Changes to every exposed control alter the advertised calculation or display. Generation-only choices cannot appear to update embedded data at runtime.
- Price contacts and source-range availability match causal local fixtures when given equivalent prices, timestamps, sessions and parameters.
- Runtime and drawing budgets are checked with all planets and allowed feature combinations, not only a one-planet example.
- Compile and run the actual generated script in TradingView if access is available, testing a Bitcoin chart, toggles, input changes, Bar Replay and future drawings. If unavailable, distinguish local static/semantic checks from TradingView compilation and provide precise remaining manual steps. Never claim Pine compilation based solely on Python tests.

Finish with links to the generated files, exact regeneration steps, tested coverage/settings, and a concise account of supported and restricted app parameters. The intended result is a practical Bitcoin chart indicator with all planetary trajectories available and settings that faithfully reflect the local Universal Clock app.
