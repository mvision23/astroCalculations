# Development prompt: Universal Clock research and visualization

Build a complete local application implementing the calculable methods in Jeanne Long's *Universal Clock: Forecasting Time and Price in the Footsteps of W. D. Gann*, Book I (1993), together with a working Pine Script alternative for visualizing planetary trajectories and price levels in TradingView. Implement, test, and document the software; do not stop at an architecture proposal or code skeleton.

The primary source is the user-provided file:

`../Universal clock: Forecasting time and price in the footsteps -- Jeanne Long -- 1993 -- P_A_S_ Publications -- 15a5fad06f4d1e32e805e3083c6e7c2e -- Anna’s Archive.pdf`

The existing astronomy project is `astroCalculations/`, referred to by the user as `astroCalc`. Resolve paths from the actual working directory. Reuse its calculation code where appropriate. The requested product is an interactive research tool: I must be able to calculate and plot planetary positions without prices, load an asset's historical prices, and explore the book's time/price relationships on both a chart and its circular clock.

Treat the author's market predictions as hypotheses to examine, not established forecasting accuracy. Faithfully implementing a calculation does not establish that it predicts prices. Keep factual astronomical results, book interpretations, and optional research extensions distinguishable.

## 1. Read the source and establish complete method coverage

Read the whole PDF, including diagrams, captions, tables, and trading examples. It has 142 PDF pages; most pages after PDF page 10 are scans without usable extracted text. Render and inspect them, using local OCR if useful. Do not treat empty text extraction as an empty page. Number source references using both printed and one-based PDF pages; printed page 1 is PDF page 4 in this copy.

Create `docs/book-methods.md` and a machine-readable method registry. For each method record its ID, chapter, printed/PDF pages, source figure, inputs, formula or procedure, outputs, units, rounding, assumptions, example fixture, implementation module, UI location, Pine support, tests, and completion status. Classify each item as an explicit book rule, an implementation formalization of a diagram, a discretionary interpretation, or an extension. Record scan ambiguities and contradictions instead of inventing missing rules.

This is the starting coverage map, to verify and expand during the source audit:

| Source | Required coverage |
| --- | --- |
| Chapter 1, printed 1–9 / PDF 4–12 | Mercury/Sun superior-to-inferior conjunction pairs, first-date price ranges and subsequent overlap, event-date windows, non-trading-day handling. |
| Chapter 2, printed 10–16 / PDF 13–19 | Geocentric positions, ephemeris reading, zodiac conversion, seven aspect families and their progression around the full cycle. Historical background needs documentation, not a fabricated algorithm. |
| Chapter 3, printed 17–38 / PDF 20–41 | Aspect-date price repetition; 1–2, 1–2–3, and 1–2–3–4 patterns; previous price areas; asset-specific planetary pairs. |
| Chapter 4, printed 39–62 / PDF 42–65 | Inner time wheel, outer price wheel, 24-based scales, same-sector and opposite-sector ranges, changing price levels, comparisons within aspect families. |
| Chapter 5, printed 63–86 / PDF 66–89 | Longitude rounding and conversion to price, planetary channels, midchannels, retrograde slopes, multiple planets in one clock sector, line contacts and breaks. |
| Chapter 6, printed 87–107 / PDF 90–110 | Static 24-lines, three intermediate divisions, halfway divisions, support/resistance areas, congestion, second tests, gaps and breaks. |
| Chapter 7, printed 108–125 / PDF 111–128 | Planetary passages through the 24-line, simultaneous occupancy, slow/fast planet combinations, Mars/Saturn clock alignments, monthly event calendar, combining time and price. |
| Chapter 8, printed 126–137 / PDF 129–140 | Daily price movement between planets and their opposite clock points; sugar/Jupiter example; stations, ingresses, fast-planet participation, daily replay and combined analysis. |

Do not import unrelated Gann techniques such as Square of Nine merely because they are associated with Gann. Book II's promised heliocentric, intraday, monthly, and yearly expansions are not fully specified by this Book I; document that boundary. The Moon may be available as an explicitly labeled extension: printed page 79 says lunar techniques are not covered here.

Discretionary passages still need usable visual/manual workflows. An automated interpretation must expose its chosen parameters and be labeled as an interpretation; it must not masquerade as a uniquely specified book algorithm.

## 2. Integrate with the existing project

First inspect repository instructions, working-tree changes, README, package metadata, and tests. Preserve user work and the current Textual application and its 12 workflows.

Read at least:

- `src/astrocalc/calculations.py`, especially `longitude`, `position`, `circular_distance`, `alignment_group`, and `calculate`.
- `src/astrocalc/models.py` and `exporters.py`.
- `src/concentric_cycles.py`, a useful drawing prototype, not the final book implementation.
- `tests/`, `README.md`, and `docs/EXPORTS.md`.

The legacy longitude function executes `body.compute(date); ephem.Ecliptic(body).lon`, preserving an astrometric J2000 convention. Existing searches mostly sample daily or every six hours; they do not solve exact crossings. The legacy aspect set lacks 30° and 150°. The grouping `int(longitude % 24) or 24` is a legacy binning rule, not a general definition of book rounding or clock alignment.

Add a separate, reusable book calculation layer with explicit parameters and structured results. Keep legacy behavior in a named compatibility mode. Use shared adapters rather than duplicating astronomy inside chart callbacks or importing an interactive script.

Important source/code discrepancy: printed page 109 / PDF 112 gives 24-line bands at 0–1°, 24–25°, 48–49°, …, 144–145°, 168–169°, …, 336–337°, with 360° identified with 0°. The current `SPECIAL_LONGITUDES` omits 144° and shifts several later entries. Preserve that list for the existing workflow, but implement and test a separately named book-derived sequence. Do not silently copy the legacy constants into book mode or silently alter the existing application.

## 3. Astronomy, time, and event engine

Support Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, and Pluto; make the Moon optional. Earth is the geocentric observer, not a planet with a meaningful geocentric longitude. Use UTC instants internally and explicit IANA timezones for display and market sessions.

Expose a provider interface returning longitude, coordinate metadata, angular speed, and direct/retrograde/stationary status. Define origin, zodiac, equinox/epoch, astrometric versus apparent convention, time scale, backend version, and supported date range. Reconcile the book's geocentric ephemerides against suitable reference fixtures before selecting book-mode coordinates. Do not claim that changing an epoch alone makes astrometric coordinates apparent. Consult the [PyEphem coordinate documentation](https://rhodesmill.org/pyephem/coordinates.html).

Reuse PyEphem where it meets the requirements. If another local backend is needed, isolate it behind the provider interface and document its dependencies, data files, license, coverage, and measured agreement. Work offline after setup; do not silently download ephemerides during a calculation. The current UI supports 1900–2100, not literally every date; validate any newly supported interval.

Implement:

1. Position series at configurable UTC instants, zodiac conversion, and continuous unwrapped longitude. Preserve full precision separately from book-rounded degrees.
2. Exact aspects at 0°, 30°, 60°, 90°, 120°, 150°, and 180°, with both branches for non-symmetric aspects over the 360° cycle. Retain signed phase and increasing/decreasing phase information so repeated contacts remain distinguishable.
3. Superior/inferior Mercury/Sun conjunction classification. Use validated geometry/distance information where available, with direct/retrograde motion as a consistency check. Greatest elongation and a station are different events; do not encode the introductory drawing as an assertion that they coincide.
4. Stations, zodiac ingresses, specified longitude crossings, entry/exit into 24-line bands, and clock-sector coincidences between planets.
5. Configurable event orbs and entry/exact/exit timestamps, with contiguous occupancy reported as an interval rather than a new event every sample.

Bracket and refine crossings using adaptive sampling and a bounded solver. Correctly handle angular wrap, retrograde recrossings, tangencies, and multiple events between coarse samples. Report numerical time tolerance separately from ephemeris accuracy. Compute stations from a stable derivative of unwrapped longitude; do not reuse the legacy once-per-day retrograde flag as an exact station detector.

Always retain the original astronomical timestamp separately from the trading session assigned to it. Support configurable previous/next session and the book's surrounding-date comparison window. Show strict event-day and expanded-window results separately. Do not silently select whichever session produces the best match.

## 4. Universal Clock geometry and price transformations

Reconstruct the inner 15 rings, each containing 24 consecutive integers, and the outer price rings from the source figures. Numbers increase counterclockwise; the 24-line lies between the last and first positions of a turn. Keep this geometry separate from an ordinary 360° zodiac wheel. Allow zoom and optional labels so the full diagram stays readable.

Use the following mathematical formalization, verified against the book's worked examples. It expresses the wheel's mapping; it is not a quoted formula from the book:

```text
u          = actual quoted price units per one numbered wheel step; u > 0
P          = actual quoted market price
x          = P / u                           # book-aligned price coordinate
phase(x)   = x modulo 24                     # in [0, 24)
lambda(t)  = ecliptic longitude in degrees
L(t)       = book-rounded or continuous longitude, according to selected mode

Planetary price ladder:
P_k(t)     = u * (L(t) + 24*k), k integer
Opposite clock-point ladder:
O_k(t)     = u * (L(t) + 12 + 24*k)
Neighboring planetary channels are 24*u apart.
Their midpoint is 12*u from either channel.
```

Generate only the branches within the configured price range plus a margin. Preserve branch identity through time; do not splice together whichever branch is nearest each bar's closing price. Use continuous unwrapped longitude for continuous trajectories, with explicit branch reindexing at zodiac wrap. Break wrapped degree plots at discontinuities rather than drawing a diagonal across the panel.

An opposite clock point is a half-turn of the 24-step wheel: 12 wheel units. It is conceptually different from a 180° astronomical aspect even where modular arithmetic yields the same clock phase.

Verify and document discrete label placement separately from the continuous phase formula. For integer labels 1–360, ring indexing follows `(n-1)//24`; labels 24 and 1 straddle the 24-line. Do not shift every plotted channel by one unit while trying to center a sector label.

Book mode rounds longitude minutes to the nearest degree, as on printed page 64; choose and document an explicit tie convention at exactly 30 minutes, which that passage leaves unspecified. Avoid accidental Python banker's rounding. Provide a smooth full-precision mode as a labeled extension, and an optional monthly-sampled reproduction mode for the Saturn examples. Do not round intermediate astronomy calculations prematurely.

Required arithmetic fixtures, independent of backend astronomy:

- Saturn at 5°51′ Aquarius converts to 305°51′ and rounds to 306°. With `u=10`, its Dow ladder includes 3060 and 3300, separated by 240 (printed 64–68).
- Longitude 304° with `u=0.01` gives British-pound channel levels 1.60 and 1.84; the midpoint is 1.72 (printed 75–76).
- Jupiter at rounded longitude 191° with `u=0.10` gives the sugar level 11.90; the opposite ladder includes 13.10 (printed 128–133).
- Rounded longitudes 98°, 194°, and 290° share the same clock phase, despite not being ordinary zodiac conjunctions (printed 85).

Keep quoted price units explicit: 500 cents and 5 dollars describe the same value with different numeric scales. Include presets reproducing the book, plus editable scales for other assets. The book's 6-, 12-, 24-, and 240-point examples are historical scale choices, not universal defaults for today's markets. Let the user lock a scale and inspect alternatives; do not optimize it secretly against future prices. An optional anchored transform `P0 + u*(L-L0+24*k)` must be labeled as an extension, not the default book mapping.

Implement interval projection and overlap on the wheel, including wraparound and ranges spanning a complete turn. Keep ordinary price-range overlap separate from overlap after shifts by multiples of the configured price cycle.

For static divisions, formalize and verify bands at:

```text
24-line A:       u * [24*k,      24*k + 1]
Intermediate B:  u * [24*k + 6,  24*k + 7]
Intermediate C:  u * [24*k + 12, 24*k + 13]
Intermediate D:  u * [24*k + 18, 24*k + 19]
```

Derive the halfway divisions and adjoining support/resistance areas from the actual diagrams, not an invented universal orb. For example, British-pound bands include 1.68–1.69 and 1.62–1.63, while the Dow examples include 3360–3370. Make boundary inclusivity explicit. For planetary occupancy, use the book's 24-line longitude bands independently of rounded plotting labels; expose any rounding-based occupancy interpretation separately.

## 5. Implement every method family

### A. Aspect dates and repeating ranges

Pair each superior Mercury/Sun conjunction with the following inferior conjunction for the soybean example. Capture the source session's low/high only when that session is complete. Compare subsequent observed ranges with it; include misses and unavailable sessions.

Provide presets for the book's geocentric aspect-date pairs:

| Asset examples | Pair |
| --- | --- |
| Soybeans; agricultural examples discussed in the text | Mercury/Sun, conjunction pairing |
| British pound, Deutsche Mark, Swiss franc | Mercury/Saturn |
| Japanese yen | Mercury/Pluto |
| Crude oil | Sun/Pluto |
| Silver | Venus/Jupiter |
| Dow and S&P | Sun/Jupiter |

For the non-conjunction-only examples use the seven aspect families. Keep these historical presets editable for arbitrary assets; do not imply their applicability has been validated.

Show aspect markers, source range boxes, projected target windows, overlap results, and manually assignable 1–2 / 1–2–3 / 1–2–3–4 sequences. If the source supplies no deterministic way to choose the first event or distinguish a new sequence, make that choice explicit. Any automated detector needs documented parameters, a causal availability timestamp, and an interpretation label.

Support comparisons with earlier occurrences of the same aspect family and the chapter 4 procedure of reviewing the last three family dates. Show same-range and shifted-range candidates using the market's selected cycle. Do not retrospectively choose a successful shift and present it as a prior forecast.

### B. Price wheel and aspect families

Plot daily low/high ranges on the outer wheel, multiple dates in different colors, and connections between matching phases. Support shifts by the selected price-cycle unit and half-cycle relationships. Reproduce the S&P trine-family comparisons and the Dow family clusters. Allow years of user-supplied history to be compared without reducing the entire history to handpicked successes.

### C. Planetary channels and contacts

Plot each selected planet's price ladder, optional opposite/midpoint lines, future trajectories, and stations. Include Saturn/Dow, Saturn/British-pound, Neptune/Deutsche-Mark, Saturn–Uranus–Neptune/silver, Saturn–Jupiter/oil, and Pluto/sugar examples in the fixture catalogue.

Detect configurable price touches, crossings, closes beyond lines, and overlap between different planets' projected levels. Document whether touch uses the full OHLC range, close, or another field. Expose distance in ticks and wheel units. Congestion, isolated-bar breaks, reversals, and second tests need parameterized definitions or manual annotations where the prose is discretionary. Preserve any book-specific numerical threshold only within its associated market/example preset.

### D. Static clock divisions

Draw 24-line bands, intermediate bands, halfway divisions, and source-derived support/resistance areas over prices. Provide annotations for touches, first/second tests, close-throughs, gaps, and congestion. Implement a transparent state machine for automated interpretations, with tolerances, minimum separation between tests, and causal confirmation rules. A gap between candles on opposite sides of a band is not identical to an intrabar crossing.

### E. Wheels within wheels and timing combinations

Create an event timeline and monthly matrix with one column per planet, showing 24-line entry/exit, occupancy duration, direction, and simultaneous occupancy. Find Mars/Saturn matches anywhere on the clock, not only at its 24-line and not only at zodiac conjunctions. Support slow-planet occupancy combined with fast-planet arrivals, including the October 1987 example and December 1993 table as source fixtures.

The Sun's roughly 24-day passage is an approximation; compute actual positions, not a repeating fixed-day schedule. Group multi-day occupancy and multiple-body combinations without inflating the event count for every date or every pair. If ranking combinations, show the component rules rather than inventing a probability score.

### F. Daily price/planet interaction

Implement a synchronized daily replay of the sugar example, especially March 17–April 19, 1993: price ranges, Jupiter and its opposite point, Uranus/Neptune, Mercury/Venus/Sun/Mars, stations, ingresses, 24-line visits, and Mars/Saturn alignments. Show the candidate planet levels around each day's range and let the user annotate movement between them.

Separate the book's observations from a general automatic model. Display alternate candidate levels if direction is unresolved. Extend the same tools to any supplied asset without asserting that the sugar-specific interpretation transfers automatically. Include a combined view of aspect dates, channels, static divisions, and event combinations.

## 6. Local application and price data

Default implementation: Python 3.11+, the existing astronomy package, pandas/NumPy for tabular data, and a local Streamlit interface with Plotly charts. Keep graphical dependencies optional for existing terminal users. A justified alternative UI is acceptable if it delivers the same functionality. Use the current [Streamlit Plotly integration](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart) and [Plotly candlestick documentation](https://plotly.com/python/candlestick-charts/).

Bind the application to localhost. No account or hosted service should be required. Supply a documented one-command launcher after installation, a reproducible environment, and a headless CLI for calculation, chart export, and Pine generation.

Required views:

- Price chart: OHLC/candles or close line, selectable planet ladders and static divisions, event markers, range boxes, labels, toggles, zoom, and inspectable values.
- Astronomy panel: longitude against time, wrapped or unwrapped, wheel phase, angular speed, aspects, and retrograde/station markers. Degrees belong on a clearly labeled separate scale, not the asset's price axis.
- Universal Clock: time and price rings, multiple bodies at the same location, date/time control, replay, price-range arcs, and source explanations. Also provide an ordinary zodiac view for comparison.
- Event table/calendar, aspect-family analysis, method settings, and export/Pine generator.

Synchronize the selected date across views. Make keyboard date stepping available. Retain parameters across reruns and allow a workspace/configuration to be saved and reopened. Work without a price dataset; disable only features that actually depend on prices.

Import CSV and optionally Parquet. Offer column mapping for timestamp/date, open/high/low/close, optional volume and symbol. Accept a close-only file honestly as a line series, not invented OHLC. Validate sorting, duplicate timestamps, finite prices, `low <= open/close <= high`, timezone interpretation, and missing data. Surface corrections and rejections with row counts. Never silently forward-fill OHLC or invent prices at future dates.

Record exchange/session timezone, date-label meaning, bar-open/bar-close convention, tick size, quote units, corporate-action adjustments, and futures contract/roll convention. Daily dates and UTC midnights are not interchangeable. Keep calendar time distinct from trading bars. Accommodate 24/7 assets and exchange sessions. Unsupported transformations, such as logarithms of nonpositive prices, need clear validation.

Export positions, events, levels, matches, and settings as CSV/JSON; export a self-contained interactive HTML chart and static images. Include source-method IDs, astronomy metadata, input checksum, scale, rounding, session policy, configuration, and software version. Keep calculations independent of rendering and file I/O.

## 7. TradingView alternative: runnable Pine Script v6

Deliver actual `.pine` indicators and a Python exporter that generates them from the same astronomy and transformation engine. Do not deliver placeholders, invented functions, or an instruction to call Python from Pine.

### Required approach: embedded ephemeris generated locally

The local application accepts bodies, start/end, future horizon, coordinate mode, sampling/error target, rounding, and scale, then emits a self-contained script with a finite ephemeris and event dataset embedded in its source. The user pastes it into TradingView's Pine Editor and adds it to the chart. Regenerating the file extends coverage.

Use compact bounded arrays or another tested source representation. Perform lookup using elapsed UTC timestamps, not bar counts. Interpolate continuous unwrapped longitude, then apply the shared transform. Adapt knot spacing to motion and stations, and validate between knots against the local backend. Interpolation must not erase retrograde loops. Exact event markers should come from the local refined event engine, not be inferred from a sparse visual curve.

Outside embedded coverage, return `na` and display the coverage interval. Never continue silently with a frozen endpoint, a guessed orbital speed, or fabricated precision. Include provider, coordinate convention, epoch, time convention, export version, sample spacing, and measured interpolation error in generated metadata.

Deliver an overlay indicator for planetary price trajectories, opposite/midpoint channels, static divisions, and event markers; deliver a separate degree/phase-pane indicator if necessary. Use TradingView's chart price data for candles. Arbitrary user CSV plotting is provided by the local app; the Pine deliverable must not promise native CSV ingestion.

Pine does not provide general local-file, Python, localhost, or arbitrary HTTP access. Do not invent an ephemeris ticker for `request.security()`. Do not make new Pine Seeds availability a dependency: TradingView currently says creation of new repositories is unavailable. Verify these constraints at implementation time against [TradingView data documentation](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/).

Budget source size, compilation complexity, arrays, loop/runtime work, plot counts, and drawing objects before emitting a script; reject oversized requests with actionable options to reduce bodies, interval, horizon, or channels. Current documented limits include 64 plot counts and 100,000 elements per collection; generated output should leave headroom. Check the then-current [Pine limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/). Split output into clearly named indicators when needed.

Use global `plot()` calls for historical series. For future curves use bounded time-positioned drawing objects, such as `chart.point.from_time` with `polyline.new` and `xloc.bar_time`, following [TradingView drawing documentation](https://www.tradingview.com/pine-script-docs/visuals/lines-and-boxes/). Manage object lifetimes and redraw work explicitly. Future astronomy is computable, but future market OHLC is unknown. Do not represent the curve as a future candle forecast.

Preserve curve identity and avoid wrap bridges. Make scale, channel selection, color, line style, supported display modes, and event visibility adjustable. Use confirmed bars for price-contact alerts. Replaying history must not move a price-dependent signal to a time before its inputs were available. An ephemeris table containing future astronomical positions is acceptable; future observed asset prices are not.

### Optional second approach: fully native astronomy

Only if feasible within measured Pine limits, offer a standalone analytical astronomy variant that computes positions from time. Cite the actual algorithms and coefficients, give supported bodies and dates, and measure maximum/RMS angular and price-level errors against the local backend. Do not substitute constant average orbital speeds or a sine wave for geocentric ephemerides. Pluto and the Moon may require separate models. Label any approximation and unsupported bodies; this optional route must not delay the required generated-ephemeris deliverable.

Provide a local/Pine capability table for every book method: implemented calculation, embedded/precomputed display, manual interpretation, or unsupported feature with reason. Local method coverage must remain complete even when a Pine feature is restricted to precomputed events or levels.

## 8. Validation, reproducibility, and completion

Build meaningful tests and a fixture catalogue, including:

1. Existing AstroCalc regressions still pass.
2. Book arithmetic fixtures above, 0/360 wrapping, minute rounding, 24-line boundaries, quote-unit conversions, same/opposite clock phases, and price ranges crossing the wheel origin.
3. New 30°/150° aspects, direct/retrograde recrossings, stations, band entry/exit, distinct-event grouping, and superior/inferior pairing.
4. Selected book dates and positions compared with the chosen coordinate convention, stating scan precision and accepted tolerances. Do not alter the backend to force agreement with a rounded or possibly erroneous table.
5. DST, weekend/holiday mapping, daily-session labels, missing data, and confirmed source-range availability.
6. Local versus exported ephemeris/price-level parity at knots and independent points between knots, including wrap and station cases. Translate angular error into price error using `u` and compare with a configurable fraction of a tick.
7. Representative local workflow: load a fixture, select a method/planet/scale, inspect matching chart and wheel values, save a configuration, export HTML/CSV, and generate Pine.
8. Generated Pine compile and runtime validation in TradingView where access is available, including out-of-range behavior and future drawings. If no TradingView compiler is accessible, explicitly report that limitation, distinguish local semantic/static checks from Pine compilation, and provide exact manual verification steps. Do not claim execution that did not occur.

Use selected transcribed book values and diagrams as fixtures with provenance; do not fabricate complete historical OHLC from scanned charts. Supply clearly labeled synthetic data for application demos and tests where authentic prices are absent. Research statistics computed on synthetic data must never be presented as evidence for the book's claims.

Provide an optional descriptive evaluation report: total eligible events, missing/excluded cases, hits and misses, distance to target, strict versus expanded windows, and comparisons with simple baselines. Expose assumptions and denominator. Freeze scales, anchors, event pairing, thresholds, and planet selection before a holdout period. Do not reproduce the author's quoted accuracy as a measured result or invent a trading strategy when entry/exit rules are unspecified.

Organize the added code into astronomy adapters, event detection, clock geometry, price transforms, book methods, market-data/session handling, plotting/UI, exports, and Pine generation. Follow existing project structure where possible. A method's local view and Pine exporter must consume the same result schema.

Deliver:

- The working local application and CLI, integrated without breaking existing functionality.
- `docs/book-methods.md`, a method registry, assumptions/discrepancy log, and book fixture catalogue.
- Runnable Pine v6 files, the ephemeris exporter, and a TradingView installation/verification guide.
- Sample datasets, saved configurations, and reproducible chart examples.
- Installation/offline setup, calculation conventions, data schema, supported dates, and local/Pine capability documentation.
- Test results and an honest list of remaining source ambiguities or platform limitations.

Work in runnable increments: source audit and registry; astronomy and events; wheel and price transforms; book methods and local charts; Pine export; validation and documentation. Continue through all stages. Ask only when an unresolved source or data question genuinely prevents progress; finish independent work first. Do not silently omit difficult chapters or substitute generic planetary overlays for the book's full method set.
