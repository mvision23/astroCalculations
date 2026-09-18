# Universal Clock research application

This optional addition implements the calculable Book I methods, with explicit
manual workflows for discretionary sequences and price interpretation. It uses
the existing PyEphem dependency and a separate calculation layer. The original
`astrocalc` terminal application and its twelve workflows retain their behavior.

## Install and launch

Python 3.11+ is supported. The tested environment uses Python 3.13; its exact
dependency versions are in `requirements-clock.lock`.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[clock,test]'
universal-clock ui
```

The launcher binds to `127.0.0.1:8501` and disables usage telemetry. Open that
address in a browser. Use `universal-clock ui --port 8502` for another local port.
No account, price feed or hosted service is required. Runtime calculations do not
download ephemerides. The source PDF and OCR software are not runtime dependencies.
For terminal-only installation, continue using `pip install .` and `astrocalc`.

For the pinned environment, install `-r requirements-clock.lock` followed by
`pip install --no-deps -e .`. Pins reflect one tested platform, not all Python/OS
combinations. To prepare an offline machine of the same Python/OS/architecture,
download these wheels in advance with `pip download -r requirements-clock.lock
-d wheelhouse`, include a built project wheel (`pip wheel --no-deps . -w
wheelhouse`), and install with `--no-index --find-links=wheelhouse`. Include
setuptools when installing the checkout offline.

Static PNG/SVG export additionally needs `pip install '.[images]'` and a local
Chrome/Chromium. Install Chrome during setup with `kaleido_get_chrome`, or set
`BROWSER_PATH` to an existing binary. The app reports a missing browser; it does
not fetch one during calculation. HTML export embeds Plotly and needs no network.

## First exploration

1. Start without prices. Select bodies, dates and coordinate mode, then Calculate.
   Position spacing controls rendered samples; exact-event searches use their
   own adaptive refinement. Future days extend astronomy beyond the end date.
2. Use Previous/Next, the keyboard arrows while the day slider has focus, and the
   UTC time field. All views share that instant. Observed prices and contact
   annotations appear only after their availability timestamps.
3. Select a historical example and Apply example settings. Unlock the scale to
   edit it. Presets reproduce historical quote conventions, not current market
   recommendations. Applying a preset is an explicit scale change.
4. Expand Price data & market sessions. Choose a synthetic demonstration, upload
   prices, or use sparse transcribed book ranges. Synthetic data is clearly marked.
   For chapter 8, reopen `samples/sugar-book.json` and select `sugar_daily`.
   Book ranges deliberately lack invented opens/closes and missing dates.
5. Inspect Price & replay, Astronomy, Universal Clock, Events & calendar, and
   Aspect families. The wheel has optional labels, radial zoom, dated range arcs,
   overlap connections, cycle shifts and a separate ordinary zodiac view.
6. In Methods & settings, choose session policy, expanded window, prior-family
   depth, fixed shifts and contact parameters. Select manual event sequences in
   chronological order. Save daily annotations for discretionary planet handoffs.
7. Export a workspace, result bundle, standalone HTML or image. Reopen the workspace
   and select the price source again; file bytes and uploads are not hidden inside
   configuration files. Pine generation is described in [tradingview.md](tradingview.md).

The price chart's legend toggles individual trajectories. Static bands, events
and range boxes have separate controls. Candles use authentic supplied OHLC;
close-only inputs remain a line. Sparse source fixtures use floating low/high bars.
Future astronomy is dotted; future observed candles are never constructed.
The local channel plot connects the configured samples (book mode uses steps).
Use finer spacing to inspect visual rounding changes; refined event times remain
independent of that plotting interval. Monthly reproduction connects rounded
first-of-month values linearly, matching the Saturn construction.

## Price schema and sessions

CSV needs `date` or `timestamp`, plus `close`. Provide all of `open,high,low` to
enable OHLC ranges; partial OHLC is rejected. `volume` and `symbol` are optional.
Use one asset/contract per dataset. Parquet is also supported. UI mapping maps
canonical names to input columns and is saved in the workspace; canonical headers
work directly in the CLI, which also honors a saved `column_mapping`.

```csv
date,open,high,low,close,volume
1993-03-17,11.80,12.05,11.65,11.95,100
1993-03-18,11.95,12.15,11.85,12.05,120
```

These two rows illustrate the schema only; they are not historical observations.
`samples/synthetic.csv` is the reproducible demonstration dataset (seeded generator).

Daily labels must be `YYYY-MM-DD` and name the session's closing date. An overnight
22:00–02:00 session labeled March 9 opens on March 8. In `instant` mode, ISO
timestamps carry offsets or are interpreted in the configured IANA zone; ambiguous
or nonexistent DST wall times are rejected. Open-labeled bars require their duration.
Instant bars are assigned to the session containing their close, including overnight
sessions. Use 00:00–00:00 with the 24/7 calendar for complete calendar-day sessions.

Record tick size, quote units, timezone, session hours, holiday exclusions, bar
convention, corporate adjustments and futures contract/roll policy. Weekdays is a
simple calendar with supplied exclusions; it is not an exchange holiday database.
Event-date assignment follows the configured local calendar date, with strict,
previous or next handling for non-session dates; original UTC events are retained.

Imports reject duplicate timestamps, nonfinite values and inconsistent OHLC.
Sorting corrections, rejected row numbers, missing daily sessions and incomplete
intraday sessions are reported. Invalid-row removal is opt-in. No OHLC is filled.
Intraday source ranges require continuous bar coverage from the configured open
through close. Sparse book fixtures use an explicit end-of-printed-date availability
assumption; genuine historical session-aware data is needed for empirical evaluation.

## Calculations and research interpretation

The provider supports 1900–2100, nine geocentric bodies and optional Moon. It
exposes apparent-of-date, astrometric-of-date and unchanged legacy-J2000 modes.
The default converts apparent geocentric RA/Dec to ecliptic coordinates of date;
this is distinct from merely changing an astrometric epoch. See the
[PyEphem coordinate documentation](https://rhodesmill.org/pyephem/coordinates.html).
Source positions agree within the scan fixture tolerance of 0.04°. This is not
an independent high-precision certification of the backend over its full range.

Events use bounded adaptive brackets and refinement, both branches of all seven
aspect families, wrap-safe unwrapping, stations and contiguous band occupancy.
Default numerical tolerance is one second; backend accuracy is a separate issue.
Full precision survives into exports. Longitude rounds half-up only for book price
transforms; the optional outer price-label rule rounds exact ties downward.

For unit `u`, channels are `u*(L+24*k)` and opposite points are `u*(L+12+24*k)`.
Branch identities remain fixed. Opposite clock points are not 180° zodiac events.
Default occupancy uses the book's separate closed bands `[24*k,24*k+1]`.
Nearest-label and degree-bucket interpretations are exposed separately to investigate
the source's approximate calendar tables. Smooth channels, anchors and Moon are
labeled extensions. Static A–D bands and adjoining regions follow the audited
diagrams; contact/state-machine parameters are explicit research interpretations.

Range comparisons retain every preselected shift, misses and unavailable cases.
Sources become eligible at completed session close and before the target event.
Strict-day, assigned-session and expanded-window outcomes have separate denominators.
Manual sequences and daily notes remain manual. Descriptive counts do not define
a trading strategy or validate forecasting skill. Freeze scale, anchors, bodies,
pairing and contact settings before a holdout interval if conducting research.
No baseline-adjusted or out-of-sample predictive performance is claimed.

## CLI and reproducible examples

```sh
universal-clock demo --output /tmp/clock-demo
universal-clock calculate --config samples/workspace.json \
  --prices samples/synthetic.csv --output /tmp/clock-results.zip
universal-clock chart --config samples/sugar-book.json --book-ranges sugar_daily \
  --output /tmp/sugar.html
universal-clock chart --config samples/sugar-book.json --book-ranges sugar_daily \
  --view clock --image --output /tmp/clock.png
universal-clock pine --config samples/pine-workspace.json --error-degrees .001 \
  --output /tmp/clock-pine
python tools/reproduce_clock_examples.py --images
```

CLI also accepts `--start`, `--end`, `--bodies` and `--unit`. Timestamp overrides
require explicit UTC offsets. Existing files are protected unless `--overwrite`
is given. The reproduction script intentionally replaces its generated examples.
It produces the demo dataset, saved configurations, actual embedded Pine indicators,
self-contained sugar chart, result bundle and optional chart/wheel images.

The bundle includes positions, events, levels, matches, contacts, confluences,
workspace and full JSON results. Metadata accompanies CSV rows and the bundle:
input SHA256, synthetic flag, source method IDs, provider/version, coordinate mode,
solver tolerance, scale, rounding, session rules and software version. Nested CSV
cells use JSON. Standalone HTML includes the same inspectable provenance.

## Code and source coverage

`astronomy.py` adapts PyEphem; `events.py` detects events; `geometry.py` defines the
wheel and scales; `market.py` validates prices and sessions; `methods.py` handles
comparisons and causal contacts; `workspace.py` provides settings/shared results;
`plotting.py`/`app.py` render; `exports.py` serializes; `pine.py` embeds ephemerides.

See [book-methods.md](book-methods.md) for every method's local/Pine capability,
[assumptions.md](assumptions.md) for source contradictions and interpretation choices,
[book-fixtures.json](book-fixtures.json) for selected transcriptions, and
[source-audit.json](source-audit.json) for the complete scan audit record.
The source book/OCR is not redistributed. `tools/build_book_catalogue.py` regenerates
the registry and source catalogue; this does not rerun OCR or assert new source evidence.

Validation commands and measured results are in [validation.md](validation.md).
