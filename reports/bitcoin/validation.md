# Bitcoin integration validation

Executed locally on 20 September 2026:

```sh
.venv/bin/python -m pytest -q tests/test_calculations.py tests/test_exports.py tests/test_universal_*.py tests/test_bitcoin.py
```

**81 passed** in 197.23 seconds. This covers existing calculations/exports,
Universal Clock geometry, events, market sessions, dates through 2100, Pine
generation, and the Bitcoin integration. The legacy Textual UI test module was
not part of this run.

The Bitcoin app test clicks **Load Bitcoin · $369**, verifies the local file,
UTC/24-hour convention and scale, and checks that all 5,467 bars are loaded.
Separate chart-engine checks rendered both remaining saved configurations:

| View | Position rows | Event records | Price traces | Clock traces |
|---|---:|---:|---:|---:|
| Intermediate | 1,131 | 122 | 298 | 83 |
| Long | 4,398 | 77 | 168 | 89 |

The chart-shape batching change was also compared with the original plotting
function on a fixture with multiple range comparisons: the full Plotly JSON
matched exactly. It avoids repeatedly validating an ever-growing shape list.

The session-boundary regression verifies that Bitcoin's event-day range and
expanded window use the same closing-date labels, and that a future candle's
range remains unavailable until its close. Compact static-band contacts match
the former per-timestamp representation.

Pine source generation and local semantic/budget checks succeeded. The Bitcoin
example's measured smooth-price interpolation error is below $0.0025 at the
configured scale; book-rounding threshold jumps have separate behavior. Pine
has not been compiled or executed in TradingView. See `pine/ephemeris.json` and
the [manual platform checks](../../docs/tradingview.md).
