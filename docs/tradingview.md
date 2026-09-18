# TradingView generated ephemeris

The actual sample indicators are
[`universal_clock_overlay.pine`](../samples/pine/universal_clock_overlay.pine) and
[`universal_clock_degrees.pine`](../samples/pine/universal_clock_degrees.pine).
They contain a finite local ephemeris for Jupiter and Mercury, including the
1993 Mercury retrograde loop. They require no Python connection or external feed.

No TradingView compiler/account is accessible in this build environment. The
generated text has local semantic/static tests and independent interpolation
validation; compilation and chart runtime have **not** been executed in TradingView.
Use the steps below to finish platform verification on your account.

## Generate, install and extend coverage

```sh
universal-clock pine --config samples/pine-workspace.json \
  --error-degrees .001 --tick-fraction .25 --max-step-hours 24 \
  --output /tmp/clock-pine
```

1. Open a TradingView chart with bars inside **1993-02-20 through 1993-04-30 UTC**
   for the supplied samples. Load enough historical bars; availability depends
   on your symbol/account. Alternatively regenerate for an accessible period.
2. Open Pine Editor, create an indicator, paste the complete overlay file, save,
   and Add to chart. Repeat with the degrees indicator in a separate pane.
3. Inspect the coverage table. The sample price unit is **0.1 quoted units per
   wheel step**, with a generated price range 11–13.5. Set the scale and branch
   indices appropriately for the actual chart; the samples do not choose a market.
4. Use Settings to change planet colors/visibility, branch indices, opposite lines,
   rounding, static-cycle index, future style and event visibility. The degrees pane
   offers unwrapped degrees, wrapped degrees and clock phase. Its plots are historical;
   future time-positioned curves are supplied by the price overlay.
5. Extend dates/bodies/future days in a saved workspace and regenerate. Replace the
   **entire** script in the Editor and add/update it. Outside coverage, lookup returns
   `na`; no extrapolation or frozen endpoint is substituted.

The app's Export & Pine tab provides the same exporter. Monthly reproduction mode
is rejected explicitly because the Pine deliverable uses adaptive ephemeris knots.
The generated headers and accompanying `ephemeris.json` record coordinate convention,
coverage, sample count/spacing, station count, angular errors and smooth price errors.

## What is embedded and how it is bounded

Python generates unwrapped longitudes and exact event timestamps using the shared
astronomy/event engine. Pine uses binary search by elapsed UTC milliseconds and
linear interpolation, then the shared scale/anchor/rounding formula. No native
Pine orbital approximation, invented ticker or analytical fallback exists.
Historical positions are sampled at each chart bar's **opening timestamp**. The
contact alert compares that channel with the completed bar's OHLC and requires
`barstate.isconfirmed`; it is not an intrabar moving-line contact solver.

Adaptive knots include refined stations and curvature subdivision. Validation
uses probes different from subdivision probes. Smooth price error is `u*error`;
the target is the smaller of angular tolerance and `tick_size*tick_fraction/u`.
Book rounding is discontinuous: within a tiny neighborhood of a half-degree
threshold, a small longitude error can move a rounded price by one whole `u`.
The reported smooth error is not a guarantee of rounded sub-tick parity. Editing
the price unit in TradingView changes the price-error conversion; regenerate to
validate a stricter tick budget.

Conservative generation limits are 5,000 knots/body, 12,000 total knots, 350 KB of
source, 56 estimated plot counts, 40 channel curves and 400 exact/boundary event
markers. Encoded arrays are chunked into 500 values. Future curves are bounded to
9,000 estimated points and at most 50 polylines. They use `chart.point.from_time`
and `xloc.bar_time`; old drawings are deleted before last-bar redraw. Rounded
curves include step vertices. Requests above budgets fail with instructions to
reduce bodies, coverage, future horizon or price range, disable opposite lines,
increase scale, or split settings into separately named indicators. These are
conservative local budgets, not proof that every accepted script meets every
TradingView account/runtime constraint.

Pine's documented limits include 64 plot counts and 100,000 collection elements.
See the official [limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/)
and [time-positioned drawings](https://www.tradingview.com/pine-script-docs/visuals/lines-and-boxes/).
Pine cannot load arbitrary local CSV/Python/localhost data. New Pine Seeds
repositories are unavailable according to the verified
[data documentation](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/).
These indicators do not depend on Seeds, `request.security()` ephemeris proxies,
or HTTP. Chart candles come from TradingView; CSV research stays local.

## Manual compile/runtime checklist

1. Compile both entire files in Pine Editor v6. Record any error and line number;
   local Python tests cannot establish Pine compilation.
2. On historical bars inside coverage, compare Data Window longitude/price values
   with `ephemeris.json` using the bar's UTC opening time. At knots, longitude
   matches the embedded values; between knots use the reported interpolation
   tolerance and rounding caveat. Test both full precision and book rounding.
3. Check Mercury's February 27 and March 22, 1993 stations and subsequent Aries
   wrap. Unwrapped longitude must preserve the retrograde loop; wrapped/phase
   plots must break at wrap instead of bridging across the pane.
4. Move/replay before coverage and after its end. Historical position plots must
   be `na` and the table say OUTSIDE COVERAGE. An independently embedded event
   drawing inside coverage may remain visible; this is not extrapolated astronomy.
5. Replay a bar within coverage with later embedded dates available. Toggle Future
   astronomical trajectories and inspect the overlay to the right of the last bar.
   Advance replay and verify old curves are deleted and the object count stays bounded.
6. Toggle planets, opposite lines, static bands, events and rounding; edit a branch
   index by one and verify its price shifts by exactly `24*u`. The opposite offset
   is `12*u`. Static divisions show one selected 24-step cycle; change its index
   or use the local chart for all visible cycles and adjoining shaded areas.
7. Create a Confirmed price contact alert. Verify no completed-bar signal is moved
   to an earlier bar. Future event markers are precomputed astronomical facts,
   not future price-contact signals. There are no future OHLC candles.
8. Regenerate a short contemporary interval on your accessible symbol and repeat
   these checks under its timezone/timeframe, especially intraday/DST transitions.

Per-method capabilities and restrictions are listed in
[book-methods.md](book-methods.md). Circular wheels, source-range selection,
manual sequences, the session comparison matrix, advanced contact state and
empirical evaluation belong to the local application. Pine supplies embedded
positions, price/opposite trajectories, divisions, precomputed events and a
basic confirmed contact alert.
