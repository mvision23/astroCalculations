# Validation record

## Year-2100 boundary update

The complete Universal Clock suite passes: **32 tests in 29.21 seconds**.

Four additional tests cover the final UTC instant in all three coordinate modes
for every supported body, default future-horizon clipping, December monthly
reproduction, event/chart endpoints, actual CLI-generated Pine coverage, and
single-day replay/Calculate controls on 31 December 2100. Ready-generated
year-2100 Pine artifacts are under `samples/pine-2100`; their tables and metadata
end at 2100-12-31 23:59:59.999 UTC in Pine's millisecond timestamp representation.
The local engine retains microsecond timestamps. TradingView compilation remains
unverified; the existing manual verification procedure still applies.

Verified locally on 2026-09-19 with Python 3.13 and the versions in
`requirements-clock.lock`.

| Check | Result |
|---|---|
| Existing AstroCalc regressions | All 48 passed; original calculation/UI/export code unchanged |
| Universal Clock tests | All 28 passed |
| Streamlit application | Seven tabs render; synchronized Next-day replay tested through AppTest |
| Local launcher | `127.0.0.1:8517/_stcore/health` returned HTTP 200 `ok`; test server stopped |
| Headless CLI | Calculation ZIP, book-fixture wheel HTML and both Pine indicators generated successfully |
| Static image export | Price and clock PNGs generated with Kaleido/local Chrome and visually inspected |
| Serialization | Saved settings roundtrip; bundled CSV/JSON contains input checksum/configuration; HTML embeds Plotly |
| Dependency/import checks | `pip check`, `compileall`, `git diff --check` passed |
| Registry references | 28 method records; all named test functions resolve; 28 source fixtures |
| TradingView compilation/runtime | Not run: no connected TradingView compiler/account; manual procedure in tradingview.md |

The initial combined suite reported 75 passes and one UI failure caused by a
calendar function already imported before its signature was edited during the
run. Rerunning all 28 new tests against the completed files passed. The combined
run also emitted two Python 3.13 executor-shutdown warnings in the existing Textual
tests; their assertions passed, but shutdown extended the run to about eleven
minutes. This record does not conceal that warning or claim a warning-free run.

The 28 new tests cover book arithmetic/rounding, quote units, origin wrap and
interval overlap; both 30°/150° aspect branches; recrossings, tangencies and grouped
occupancy; Mercury conjunction geometry/stations; source-date discrepancies;
supported-body/date boundaries and unchanged legacy coordinates; DST, holidays,
daily/overnight sessions, incomplete intraday coverage and causal availability;
gap-versus-crossing, separated tests and later-bar break confirmation; manual
sequences/anchors; independent and serialized ephemeris/price parity; source
budgets, no out-of-range extrapolation, chart/wheel/export/configuration and UI.

## Sample interpolation measurements

Samples cover 1993-02-20 through 1993-04-30 UTC, use `u=0.1`, tick size `0.01`,
and an angular target of `0.001°`. The embedded tables contain 435 knots total.

| Body | Maximum independent error (degrees) | RMS error (degrees) | Maximum smooth price error | Stations retained |
|---|---:|---:|---:|---:|
| Jupiter | 0.0003297451 | 0.0001475009 | 0.0000329745 | 0 |
| Mercury | 0.0006499539 | 0.0002353397 | 0.0000649954 | 2 |

These are measured errors at independent validation probes against PyEphem, not
analytic all-time error bounds or independent ephemeris truth. Smooth price error
is below a quarter tick (`0.0025`) in these samples. Nearest-degree rounding may
differ by one whole wheel unit near half-degree thresholds; see assumptions.md.
Book-position comparisons use 0.04° tolerance appropriate to the faint printed
minute tables. The backend was not changed to force printed dates or typos.

## Reproduce

```sh
python -m pip install -e '.[clock,images,test]'
python -m pytest -q
python -m pip check
python -m compileall -q src/astrocalc
python tools/reproduce_clock_examples.py --images
```

Image reproduction requires a local Chrome/Chromium; use `BROWSER_PATH` if it is
not automatically found. In the restricted build sandbox, socket binding and
Chrome rendering required permission to run locally outside the sandbox. AppTest,
astronomy, CSV/JSON/HTML export and Pine generation ran without network access.
Source OCR was a setup/audit operation, not an application dependency.

## Remaining boundaries

- No TradingView compiler or runtime was exercised. Generated v6 scripts are
  complete source artifacts with local tests; platform verification is outstanding.
- No complete authentic historical OHLC dataset was supplied. Book fixtures are
  sparse low/high transcriptions; synthetic OHLC is demonstration data only.
- Historical exchange holidays, session hours, contract rolls and adjustments
  require user metadata. No exchange calendar is silently inferred.
- Printed calendar/band interpretations, faint numerals and contradictory dates
  remain explicit in [assumptions.md](assumptions.md). Discretionary sequences and
  planet-to-planet handoffs have manual workflows and no uniquely asserted model.
- No predictive accuracy, calibrated probability, baseline-adjusted edge or trading
  strategy has been established. The application reports descriptive comparisons.
