# Native Bitcoin Pine parameter audit

Historical plots now cover all loaded bars. Per-body counts are retained/replenished within each price bracket; 32 combined curves fit the 64 plot-count budget. Only future paths have drawing/sample budgets. The dashboard remains deliberately removed. See [usage](bitcoin-native-pine.md).

## Settings

| Field / control | Classification | Implementation or boundary |
| --- | --- | --- |
| `start` | editable in Pine | Display start; model dates begin 2009-01-01 UTC. Earlier dates return na. |
| `end` | editable in Pine | Display end; limits history and future drawings within 2050. |
| `selected` | chart-derived | TradingView Bar Replay supplies the selected chart time. The inspection table and its timestamp controls were deliberately removed. |
| `bodies` | editable in Pine | All / Custom / Hide all, ten independent toggles and colors. All enables nine core bodies; Moon still opt-in. |
| `pair` | editable in Pine | Pair first / second; every supported body. Calculation includes a selected Moon even when hidden. |
| `coordinate_mode` | fixed model property | Geometric geocentric mean ecliptic/equinox of date only. Apparent-of-date, astrometric-of-date and legacy J2000 are NOT implemented or offered. |
| `scale` | editable in Pine | See every Scale field below; exact price arithmetic, different documented astronomical model. |
| `market` | chart-derived | Chart OHLC and metadata plus editable research calendar; see MarketSpec below. |
| `column_mapping` | local-only with a concrete reason | CSV/Parquet column parsing has no meaning for TradingView chart OHLC. |
| `price_file` | local-only with a concrete reason | The installed indicator consumes the active chart; it cannot read a local file. |
| `low` | editable in Pine | Shared minimum price (default 70,000), with a per-body override; used for branch selection, clipping, future paths and contacts. |
| `high` | editable in Pine | Shared maximum price (default 125,000), per-body overrides and independent 0–12 main counts. Keep eligible branches and replenish on exit; counts exclude opposites. Combined active requests must fit 32 curves. |
| `orb` | editable in Pine | Aspect orb degrees, 0–5.9; refined entry/exit around all phase targets and exact modulo-24 clock matches. |
| `occupancy_mode` | editable in Pine | continuous [0,1], rounded_labels [-0.5,1.5], degree_buckets [0,2] repeated modulo 24; boundary events retained. |
| `clock_alignment_mode` | editable in Pine | exact_phase modulo 24, or rounded_sector boundaries searched in each body. Neither is zodiac conjunction. |
| `step_hours` | editable in Pine | Event grid hours (1–6); historical resolution follows chart bars. Maximum future sample hours (1–24), additionally capped by body speed. No historical-day limit. |
| `future_days` | editable in Pine | Future days 0–700 (default 7). Future-only budgets: 96 paths, 6000 body samples and 40000 vertices. Historical plots cover all loaded bars with no rolling day/calc-bar cap. |
| `session_policy` | editable in Pine | strict / previous / next assignment of non-session closing dates; never substitutes partial session ranges. |
| `window_days` | editable in Pine | Expanded window ± calendar days, capped at 3. Strict, assigned and expanded results remain separate. |
| `shifts` | editable in Pine | Cycle shifts CSV, at most five. Every shift creates a retained hit/miss/unavailable/pending candidate; no best-shift selection. |
| `last_family_dates` | editable in Pine | Previous events per target, 1–5; retained event history bounded at 128 and analysis window at 180 days. |
| `comparison_mode` | editable in Pine | family or consecutive; manual sequences remain local-only because Pine has no persistent arbitrary event-selection editor. |
| `conjunction_pairs` | editable in Pine | Comparison mode Mercury superior to inferior; distances identify type. Each superior is consumed by its following inferior. |
| `opposite` | editable in Pine | Opposites add 12 steps. Each side retains its eligible branches and replenishes on exit, up to N each within the bracket. Combined historical capacity is 32 curves including opposites. |
| `halfway` | editable in Pine | Halfway lines: offsets 3.5, 9.5, 15.5, 21.5; independent of A–D bands. |
| `adjoining` | editable in Pine | Adjoining support/resistance [d-2.5,d] / [d+1,d+3.5], independent of bands; unanchored static geometry. |
| `monthly_sample` | editable in Pine | Monthly reproduction: UTC first-of-month endpoint rounding followed by linear interpolation, using local shortest-angle endpoint semantics, including Moon aliasing. |
| `tolerance_seconds` | editable in Pine | Root tolerance seconds, 1–300, numerical bracket width only; model error is separately measured. |
| `contacts` | editable in Pine | Calculate price contacts, labels, alerts and tag filters; see all ContactSettings fields below. |
| `sequences` | local-only with a concrete reason | The local arbitrary 2–4 event sequence editor and persistence are not implemented; use supported family/consecutive or Mercury pairing in Pine. |
| `annotations` | editable in Pine | Three bounded manual timestamp/text annotations, each with an enable toggle. Saved workspace annotation lists remain local. |
| `scale_locked` | editable in Pine | Bitcoin 369 preset fixes effective unit at 369; Manual activates Manual units per step. |
| `preset` | editable in Pine | Bitcoin 369 or Manual; other named historical presets can be reproduced numerically with Manual but are not extra preset menus. |
| `schema_version` | local-only with a concrete reason | Local workspace JSON version; Pine inputs are saved by TradingView and do not deserialize workspace JSON. |

## Scale

| Field / control | Classification | Implementation or boundary |
| --- | --- | --- |
| `unit` | editable in Pine | Bitcoin 369 / Manual units per step; positive values only. |
| `rounding` | editable in Pine | Book = floor(L+0.5), Continuous = L; negative half ties match Python. |
| `quote_units` | chart-derived | syminfo.currency and syminfo.ticker; USD and USDT remain distinct, with no currency conversion. |
| `anchor_price` | editable in Pine | Anchor price P0, applied only when Anchor trajectories is enabled. |
| `anchor_longitude` | editable in Pine | Anchor unwrapped longitude L0 is subtracted without rounding. |
| `anchored` | editable in Pine | Anchor trajectories affects planetary curves only; static grid stays unanchored. |

## MarketSpec

| Field / control | Classification | Implementation or boundary |
| --- | --- | --- |
| `timezone` | editable in Pine | Research timezone (IANA), UTC default; separate event display timezone. |
| `timestamp_kind` | chart-derived | Actual Unix bar timestamps; local daily-label parsing is not a Pine feed operation. |
| `bar_convention` | editable in Pine | Astronomy sample Bar open / Confirmed close; price availability always at confirmed close. |
| `session_open` | editable in Pine | Research session HHMM-HHMM; default 0000-0000, closing-date labels. |
| `session_close` | editable in Pine | Research session close with overnight/equal-open-close convention and timezone-aware DST bounds. |
| `calendar` | editable in Pine | 24/7 or weekdays calendar, keyed by session closing date. |
| `holidays` | editable in Pine | Up to 30 excluded ISO closing dates in Holiday closing dates CSV. |
| `tick_size` | editable in Pine | syminfo.mintick by default; Tick override >0 changes contact tolerance and display, never the chart feed. |
| `quote_units` | chart-derived | syminfo.currency and syminfo.ticker; USD and USDT remain distinct, with no currency conversion. |
| `adjustments` | chart-derived | TradingView feed provenance; Pine cannot change corporate-action adjustments with a text input. |
| `contract_roll` | chart-derived | Selected chart symbol/feed determines futures roll; no fictional roll override. |
| `symbol` | chart-derived | Active TradingView syminfo.ticker; no exchange or CSV symbol hardcoded. |
| `synthetic` | chart-derived | chart.is_standard gates all price methods; synthetic OHLC is not treated as observed standard market data. |
| `bar_minutes` | chart-derived | Actual time/time_close coverage and timeframe.in_seconds(); standard weekly charts explicitly disable daily comparisons. |

## ContactSettings

| Field / control | Classification | Implementation or boundary |
| --- | --- | --- |
| `tolerance_ticks` | editable in Pine | Tolerance ticks times effective tick size; applies to touches, sides, gaps, taking confirming extremes. |
| `separation_bars` | editable in Pine | Test separation bars; separated new touches increment first/second/retest state per branch identity (reset when a plot slot changes k). |
| `congestion_bars` | editable in Pine | Congestion bars; consecutive touches trigger once at the configured count. |
| `confirmation_bars` | editable in Pine | Close confirmation bars; consecutive closes beyond tolerance trigger close-through, reversal and pending extreme tests. |
| `field` | editable in Pine | Contact field range / close; close-only touch tests still use standard OHLC for gap and extreme-taking logic, matching Python. |

## App controls

| Field / control | Classification | Implementation or boundary |
| --- | --- | --- |
| `'24-line occupancy'` | editable in Pine | continuous [0,1], rounded_labels [-0.5,1.5], degree_buckets [0,2] repeated modulo 24; boundary events retained. |
| `'Additional clock alignment interpretation'` | editable in Pine | exact_phase modulo 24, or rounded_sector boundaries searched in each body. Neither is zodiac conjunction. |
| `'Anchor longitude L0'` | editable in Pine | Anchor unwrapped longitude L0 is subtracted without rounding. |
| `'Anchor price P0'` | editable in Pine | Anchor price P0, applied only when Anchor trajectories is enabled. |
| `'Apply example settings'` | editable in Pine | Bitcoin 369 or Manual; other named historical presets can be reproduced numerically with Manual but are not extra preset menus. |
| `'Apply method settings'` | chart-derived | TradingView recalculates automatically when inputs change; no extra Calculate action is needed. |
| `'Aspect body'` | editable in Pine | Pair first / second; every supported body. Calculation includes a selected Moon even when hidden. |
| `'Aspect counterpart'` | editable in Pine | Pair first / second; every supported body. Calculation includes a selected Moon even when hidden. |
| `'Asset / contract'` | chart-derived | Active TradingView syminfo.ticker; no exchange or CSV symbol hardcoded. |
| `'Astronomy scale'` | local-only with a concrete reason | The inspection table and numeric astronomy display were deliberately removed from this price overlay. Headless reports retain longitude and speed comparisons. |
| `'Bar timestamp labels'` | editable in Pine | Astronomy sample Bar open / Confirmed close; price availability always at confirmed close. |
| `'Bitcoin research findings'` | local-only with a concrete reason | Local report and file/image exporters; the native indicator does not invoke the local application. |
| `'Bitcoin research view'` | editable in Pine | Bitcoin 369 or Manual; other named historical presets can be reproduced numerically with Manual but are not extra preset menus. |
| `'Book price labels · nearest step, exact ties down'` | local-only with a concrete reason | Circular wheel layout and printed label centering are local research UI; Pine supplies price trajectories, not a wheel renderer. |
| `'Calculate'` | chart-derived | TradingView recalculates automatically when inputs change; no extra Calculate action is needed. |
| `'Calendar month YYYY-MM'` | editable in Pine | Marker month 0–12 filters display within configured dates; use display start/end to select a year. |
| `'Compare completed price-range dates'` | local-only with a concrete reason | Manual circular-chart overlays stay in the local wheel editor; Pine cycle-shift comparison controls operate on supported event pairs instead. |
| `'Comparison selection'` | editable in Pine | family or consecutive; manual sequences remain local-only because Pine has no persistent arbitrary event-selection editor. |
| `'Consecutive closes for confirmation'` | editable in Pine | Close confirmation bars; consecutive closes beyond tolerance trigger close-through, reversal and pending extreme tests. |
| `'Consecutive contact bars for congestion'` | editable in Pine | Congestion bars; consecutive touches trigger once at the configured count. |
| `'Contact tolerance, ticks'` | editable in Pine | Tolerance ticks times effective tick size; applies to touches, sides, gaps, taking confirming extremes. |
| `'Contract / roll convention'` | chart-derived | Selected chart symbol/feed determines futures roll; no fictional roll override. |
| `'Coordinates'` | fixed model property | Geometric geocentric mean ecliptic/equinox of date only. Apparent-of-date, astrometric-of-date and legacy J2000 are NOT implemented or offered. |
| `'Corporate-action adjustments'` | chart-derived | TradingView feed provenance; Pine cannot change corporate-action adjustments with a text input. |
| `'Daily observation / movement between planets'` | editable in Pine | Three bounded manual timestamp/text annotations, each with an enable toggle. Saved workspace annotation lists remain local. |
| `'Degrees / phase .pine'` | local-only with a concrete reason | Old generated-ephemeris exporter remains local. The new populated native .pine file is already delivered and requires no export/generation step. |
| `'Display IANA timezone'` | editable in Pine | Event timezone changes formatting only; calculation timestamps remain absolute. |
| `'Download image'` | local-only with a concrete reason | Local report and file/image exporters; the native indicator does not invoke the local application. |
| `'End (UTC)'` | editable in Pine | Display end; limits history and future drawings within 2050. |
| `'Event markers'` | editable in Pine | Astronomical events master and type toggles, pair visibility filter; most recent 120 historical labels. |
| `'Event orb (degrees / clock units)'` | editable in Pine | Aspect orb degrees, 0–5.9; refined entry/exit around all phase targets and exact modulo-24 clock matches. |
| `'Event types'` | editable in Pine | Astronomical events master and type toggles, pair visibility filter; most recent 120 historical labels. |
| `'Excluded holiday dates (comma separated)'` | editable in Pine | Up to 30 excluded ISO closing dates in Holiday closing dates CSV. |
| `'Expanded window ± calendar days'` | editable in Pine | Expanded window ± calendar days, capped at 3. Strict, assigned and expanded results remain separate. |
| `'Explicitly remove invalid rows and show rejection report'` | local-only with a concrete reason | Local file/fixture importer and validation; Pine uses active TradingView OHLC, with no CSV dependency. |
| `'Export results · CSV + JSON + metadata'` | local-only with a concrete reason | Local report and file/image exporters; the native indicator does not invoke the local application. |
| `'Extension: anchored price transform'` | editable in Pine | Anchor trajectories affects planetary curves only; static grid stays unanchored. |
| `'Future astronomy (days)'` | editable in Pine | Future days 0–700 (default 7). Future-only budgets: 96 paths, 6000 body samples and 40000 vertices. Historical plots cover all loaded bars with no rolling day/calc-bar cap. |
| `'Generate Pine v6 indicators'` | local-only with a concrete reason | Old generated-ephemeris exporter remains local. The new populated native .pine file is already delivered and requires no export/generation step. |
| `'Halfway divisions'` | editable in Pine | Halfway lines: offsets 3.5, 9.5, 15.5, 21.5; independent of A–D bands. |
| `'Historical price file'` | local-only with a concrete reason | Local file/fixture importer and validation; Pine uses active TradingView OHLC, with no CSV dependency. |
| `'Intraday bar duration, minutes'` | chart-derived | Actual time/time_close coverage and timeframe.in_seconds(); standard weekly charts explicitly disable daily comparisons. |
| `'Load Bitcoin · $369'` | editable in Pine | Bitcoin 369 or Manual; other named historical presets can be reproduced numerically with Manual but are not extra preset menus. |
| `'Load workspace'` | local-only with a concrete reason | Local workspace serialization is not read by Pine; TradingView saves indicator inputs and chart layouts. |
| `'Local price file'` | local-only with a concrete reason | Local file/fixture importer and validation; Pine uses active TradingView OHLC, with no CSV dependency. |
| `'Lock price scale'` | editable in Pine | Bitcoin 369 preset fixes effective unit at 369; Manual activates Manual units per step. |
| `'Longitude plotting'` | editable in Pine | Book = floor(L+0.5), Continuous = L; negative half ties match Python. |
| `'Manual sequence (select 2–4 events in order)'` | local-only with a concrete reason | The local arbitrary 2–4 event sequence editor and persistence are not implemented; use supported family/consecutive or Mercury pairing in Pine. |
| `'Market / historical example'` | editable in Pine | Bitcoin 369 or Manual; other named historical presets can be reproduced numerically with Manual but are not extra preset menus. |
| `'Maximum knot spacing, hours'` | fixed model property | Dated-table export tolerances do not apply. The native model has measured angular errors; rendering spacing and root tolerance are distinct runtime inputs, with no precision guarantee. |
| `'Maximum measured interpolation error, degrees'` | fixed model property | Dated-table export tolerances do not apply. The native model has measured angular errors; rendering spacing and root tolerance are distinct runtime inputs, with no precision guarantee. |
| `'Maximum smooth price error, fraction of a tick'` | fixed model property | Dated-table export tolerances do not apply. The native model has measured angular errors; rendering spacing and root tolerance are distinct runtime inputs, with no precision guarantee. |
| `'Minimum bars between tests'` | editable in Pine | Test separation bars; separated new touches increment first/second/retest state per branch identity (reset when a plot slot changes k). |
| `'Monthly Saturn-style reproduction'` | editable in Pine | Monthly reproduction: UTC first-of-month endpoint rounding followed by linear interpolation, using local shortest-angle endpoint semantics, including Moon aliasing. |
| `'Next →'` | chart-derived | TradingView Bar Replay controls chart history. The optional inspection timestamp and numeric table were deliberately removed. |
| `'Non-session event-date assignment'` | editable in Pine | strict / previous / next assignment of non-session closing dates; never substitutes partial session ranges. |
| `'Opposite / midpoint channels'` | editable in Pine | Opposites add 12 steps. Each side retains its eligible branches and replenishes on exit, up to N each within the bracket. Combined historical capacity is 32 curves including opposites. |
| `'Planets · Moon is an extension'` | editable in Pine | All / Custom / Hide all, ten independent toggles and colors. All enables nine core bodies; Moon still opt-in. |
| `'Position spacing (hours)'` | editable in Pine | Event grid hours (1–6); historical resolution follows chart bars. Maximum future sample hours (1–24), additionally capped by body speed. No historical-day limit. |
| `'Prepare static image'` | local-only with a concrete reason | Local report and file/image exporters; the native indicator does not invoke the local application. |
| `'Preselected cycle shifts (comma separated; 0.5 = opposite)'` | editable in Pine | Cycle shifts CSV, at most five. Every shift creates a retained hit/miss/unavailable/pending candidate; no best-shift selection. |
| `'Previous dates from same aspect family'` | editable in Pine | Previous events per target, 1–5; retained event history bounded at 128 and analysis window at 180 days. |
| `'Price overlay .pine'` | local-only with a concrete reason | Old generated-ephemeris exporter remains local. The new populated native .pine file is already delivered and requires no export/generation step. |
| `'Price panel maximum'` | editable in Pine | Shared maximum price (default 125,000), per-body overrides and independent 0–12 main counts. Keep eligible branches and replenish on exit; counts exclude opposites. Combined active requests must fit 32 curves. |
| `'Price panel minimum'` | editable in Pine | Shared minimum price (default 70,000), with a per-body override; used for branch selection, clipping, future paths and contacts. |
| `'Price source'` | local-only with a concrete reason | Local file/fixture importer and validation; Pine uses active TradingView OHLC, with no CSV dependency. |
| `'Price-range shift in cycles · 0.5 is opposite'` | local-only with a concrete reason | Manual circular-chart overlays stay in the local wheel editor; Pine cycle-shift comparison controls operate on supported event pairs instead. |
| `'Quote units'` | chart-derived | syminfo.currency and syminfo.ticker; USD and USDT remain distinct, with no currency conversion. |
| `'Quoted units per wheel step'` | editable in Pine | Bitcoin 369 / Manual units per step; positive values only. |
| `'Radial zoom · time rings 2–9, price rings above 9'` | local-only with a concrete reason | Circular wheel layout and printed label centering are local research UI; Pine supplies price trajectories, not a wheel renderer. |
| `'Reopen workspace'` | local-only with a concrete reason | Local workspace serialization is not read by Pine; TradingView saves indicator inputs and chart layouts. |
| `'Replay day · focus slider and use arrow keys'` | chart-derived | TradingView Bar Replay controls chart history. The optional inspection timestamp and numeric table were deliberately removed. |
| `'Replay day'` | chart-derived | TradingView Bar Replay controls chart history. The optional inspection timestamp and numeric table were deliberately removed. |
| `'Restore Bitcoin prices'` | local-only with a concrete reason | Local file/fixture importer and validation; Pine uses active TradingView OHLC, with no CSV dependency. |
| `'Save daily annotation'` | editable in Pine | Three bounded manual timestamp/text annotations, each with an enable toggle. Saved workspace annotation lists remain local. |
| `'Save sequence'` | local-only with a concrete reason | The local arbitrary 2–4 event sequence editor and persistence are not implemented; use supported family/consecutive or Mercury pairing in Pine. |
| `'Save workspace'` | local-only with a concrete reason | Local workspace serialization is not read by Pine; TradingView saves indicator inputs and chart layouts. |
| `'Self-contained clock chart'` | local-only with a concrete reason | Local report and file/image exporters; the native indicator does not invoke the local application. |
| `'Self-contained interactive price chart'` | local-only with a concrete reason | Local report and file/image exporters; the native indicator does not invoke the local application. |
| `'Sequence label'` | local-only with a concrete reason | The local arbitrary 2–4 event sequence editor and persistence are not implemented; use supported family/consecutive or Mercury pairing in Pine. |
| `'Session IANA timezone'` | editable in Pine | Research timezone (IANA), UTC default; separate event display timezone. |
| `'Session calendar'` | editable in Pine | 24/7 or weekdays calendar, keyed by session closing date. |
| `'Session closes (local HH:MM)'` | editable in Pine | Research session close with overnight/equal-open-close convention and timezone-aware DST bounds. |
| `'Session opens (local HH:MM)'` | editable in Pine | Research session HHMM-HHMM; default 0000-0000, closing-date labels. |
| `'Show ring labels'` | local-only with a concrete reason | Circular wheel layout and printed label centering are local research UI; Pine supplies price trajectories, not a wheel renderer. |
| `'Source range fixture'` | local-only with a concrete reason | Local file/fixture importer and validation; Pine uses active TradingView OHLC, with no CSV dependency. |
| `'Source ranges / target windows'` | editable in Pine | Completed-session comparisons and optional Source-range boxes remain. Causal strict/assigned/expanded state is retained internally; its dashboard was deliberately removed. |
| `'Source-derived adjoining areas'` | editable in Pine | Adjoining support/resistance [d-2.5,d] / [d+1,d+3.5], independent of bands; unanchored static geometry. |
| `'Start (UTC)'` | editable in Pine | Display start; model dates begin 2009-01-01 UTC. Earlier dates return na. |
| `'Static divisions'` | editable in Pine | A–D bands, Halfway lines and Adjoining areas; bounded cycles around the fixed reference price. |
| `'Static image format'` | local-only with a concrete reason | Local report and file/image exporters; the native indicator does not invoke the local application. |
| `'Superior → following inferior Mercury/Sun pairs'` | editable in Pine | Comparison mode Mercury superior to inferior; distances identify type. Each superior is consumed by its following inferior. |
| `'Tick size'` | editable in Pine | syminfo.mintick by default; Tick override >0 changes contact tolerance and display, never the chart feed. |
| `'Timestamp meaning'` | chart-derived | Actual Unix bar timestamps; local daily-label parsing is not a Pine feed operation. |
| `'Touch field'` | editable in Pine | Contact field range / close; close-only touch tests still use standard OHLC for gap and extreme-taking logic, matching Python. |
| `'UTC time'` | chart-derived | TradingView Bar Replay controls chart history. The optional inspection timestamp and numeric table were deliberately removed. |
| `'Wheel'` | local-only with a concrete reason | Circular wheel layout and printed label centering are local research UI; Pine supplies price trajectories, not a wheel renderer. |
| `'← Previous'` | chart-derived | TradingView Bar Replay controls chart history. The optional inspection timestamp and numeric table were deliberately removed. |
| `f'Map {key}'` | local-only with a concrete reason | Dynamic local CSV column-mapping controls; TradingView supplies named OHLC fields directly. |

