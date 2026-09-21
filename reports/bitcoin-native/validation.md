# Full-history replenishment validation

This report supersedes the finite-history polyline validation. See [correction-report.md](correction-report.md) for the implementation, figures, numerical comparisons and platform limitations.

Executed:

```text
.venv/bin/python -m pytest tests/test_bitcoin_native_pine.py tests/test_bitcoin_native_correction.py tests/test_universal_geometry.py tests/test_universal_events.py tests/test_universal_market.py tests/test_universal_book.py -q
75 passed in 11.28s
```

The source-derived tests exercise the actual replenish allocator, contact-state reset block, historical color-break predicate and future path-builder bodies. A separate planner checks exact path/identity parity. Behavioral checks require surviving branches to retain their slots, active counts to match requested/available counts, selected k values to remain contiguous, and all prices to stay in the effective bracket. Both direct and retrograde changes, large timestamp/longitude jumps, zero counts, twelve mains, custom ranges, narrow bands, opposite semantics and future seed immutability are covered.

The 2009–2026 history fixture exceeds 6,000 bars and thousands of lunar branch identities. It is not subject to a historical-day window or drawing-object budget. Static checks require no `calc_bars_count`/render-day cap and exactly 32 plot calls with the 64-count value/color budget. Existing native astronomy, price arithmetic, event-root, model-boundary, contact and causal-session tests pass. The app/schema parameter audit remains complete.

`correction_report.py` ran successfully with the updated source, regenerating numeric/app comparisons, resource examples and PNG figures. The new full-history and Sun/Moon figures were inspected. The original independent full-interval angular sweep remains applicable because the orbital functions are unchanged; current source-derived fixtures still pass. No claim is made that the entire 153,450-comparison sweep was repeated merely for the rendering change.

Recorded full-history configurations use 6,453 daily samples from January 1, 2009 to September 1, 2026, with seven future days. All ten bodies fit 20 requested curves and 24 future segments; dense Mars/Neptune fits 32 requested curves and 25 future segments. Historical segment counts do not allocate polylines.

Development dependencies for figures/reference checks are under `/tmp/bitcoin-native-reference`. The helper was run with `MPLCONFIGDIR=/tmp/native-pine-mpl PYTHONPATH=/tmp/bitcoin-native-reference .venv/bin/python`. These packages are not dependencies of the installed indicator. No local web application or TradingView browser workflow was used.

**Not verified:** Pine compilation/type qualifiers, execution-time limits, actual chart styling/scale attachment, rollback or live alerts. No authorized Pine compiler/runtime is available in this environment. Confirmed-close historical plots use the next chart bar; exact close/open timestamp equivalence requires contiguous time-based bars, as documented in usage.

## 120-day horizon follow-up

The maximum Future days input was raised from 90 to 120; its default remains 7. Added two parameterized source-builder cases for the default nine bodies and dense Mars/Neptune. Both assert full 120-day endpoints for every selected body and fit the existing budgets. Orbital coefficients and historical rendering are unchanged.

```text
.venv/bin/python -m pytest tests/test_bitcoin_native_pine.py tests/test_bitcoin_native_correction.py -q
53 passed in 14.84s
```

The resource fixtures/source hashes were refreshed without rerunning unchanged ephemeris sweeps or regenerating unchanged figures. The report generator includes both new scenarios for future reproduction. TradingView compilation/runtime remain unverified.

## 700-day horizon follow-up

Raised the Future days maximum from 120 to 700, keeping the default at 7. Added source-builder scenarios for Sun alone and Mars/Neptune with one main each plus opposites. Every selected body reaches the full 700-day endpoint within the existing budgets. The default nine-body selection exceeds the sample budget at 700 days; the explicit error is retained and documented.

```text
.venv/bin/python -m pytest tests/test_bitcoin_native_pine.py tests/test_bitcoin_native_correction.py -q
55 passed in 14.35s
```

The numeric resource fixtures, report generator, parameter audit and source hashes were updated. Unchanged astronomy sweeps and figures were not regenerated. TradingView compilation/runtime remain unverified.
