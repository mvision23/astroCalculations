# Bitcoin Universal Clock — native Pine v6

Use the complete [indicator](../pine/bitcoin_universal_clock_native.pine) in TradingView's Pine Editor. It calculates astronomy directly and consumes the chart's prices. No generated ephemeris, Python process, CSV or web app is required at runtime.

**History now spans all bars loaded by TradingView**, subject only to the chosen Display start/end and the model's 2009–2050 validity. The rolling historical-day control and the previous 3,000-bar calculation cap are removed. Historical trajectories use plots; drawing-object limits apply only to future projections.

**Pine compilation/runtime remain unverified:** this environment has no authorized TradingView compiler. The [corrective report](../reports/bitcoin-native/correction-report.md) includes source-derived tests, numeric evidence, figures and remaining platform checks.

## Per-planet counts and price brackets

Each body has a visibility checkbox, color, **0–12 main trajectories**, and either the shared price bracket or a custom minimum/maximum. Defaults are one main per core body, optional Moon off, shared bounds **70,000–125,000**, and opposites on. In **All** mode the nine core bodies are enabled regardless of checkboxes; **Custom** honors checkboxes; **Hide all** hides every body. Count zero suppresses a body's trajectories in any mode.

In **Price-band coverage** mode, selection now behaves as follows:

1. At the first valid loaded sample, choose a contiguous family near the bracket midpoint.
2. Keep every existing branch in the same slot while its price stays inside the bracket.
3. When a branch exits, replace it with an eligible adjacent branch. Keep the requested count whenever that many branches fit.
4. Never change the formula or spacing to squeeze more branches into a narrow bracket. If only six branches fit and the requested count is eight, display six.

The selected family stays contiguous in integer k, so main prices remain separated by **8,856 at unit 369**. Direct and retrograde motion use the same survival/replenishment rules. Existing branches are not removed merely because their price rank changes. A replacement is a new `(body,k,opposite)` identity: its incoming plot connector is hidden and its contact state starts fresh.

The count excludes opposites. Each side is allocated independently within the bracket, with up to N mains and N opposites. Opposites add 4,428 at unit 369; the eligible k sets at the band edges can differ. Body-specific brackets control historical selection, future selection, clipping and contact eligibility. Bitcoin's close is never an input to branch selection.

Loading additional earlier history can change which family was initially seeded, because surviving branches are retained. It never changes the calculated price of a specified `(time,body,k,side)`. The requested count and bounds are still enforced at every sampled bar.

**Fixed reference** and **Manual k** remain optional alternatives without replenishment. Their fixed set begins at `center-floor((N-1)/2)`. Fixed-reference centers use September 1, 2026 and 100,000 initially; Manual k uses the supplied integer. These fixed modes can display fewer lines as their identities leave the bracket.

## Simultaneous curve budget

There are **32 historical curve slots per indicator**, costing **64 plot counts** with dynamic body colors and identity-break coloring. Hidden compiled plots still count; the script declares exactly 32. The allocation check uses the requested counts of enabled bodies:

```text
sum(enabled per-body main counts) * (opposites enabled ? 2 : 1) <= 32
```

Examples that fit: all ten bodies with one main each plus opposites (20 curves); Mars and Neptune with eight mains each plus opposites (32); one body with twelve mains plus opposites (24). Twelve mains need a sufficiently wide price bracket to be simultaneously visible.

If the requested combination exceeds capacity, the script raises an explicit error before plotting. Reduce counts, disable opposites, or add another instance with a separate body selection. No bodies are silently dropped. This is a limit on simultaneous curves, **not historical days**. [TradingView plot limits and dynamic color costs](https://www.tradingview.com/pine-script-docs/visuals/plots/#plot-count-limit).

For a dense family resembling `webapp.png`, use Custom, select Mars and Neptune, set each main count to 8, and leave opposites enabled. Edit the price bracket to the region you want. History extends over the loaded chart, rather than a fixed 120/360/365-day window.

## Historical placement and future paths

Historical calculations run at actual chart timestamps, with no fixed angular increment per candle. **Bar open** plots longitude/price at each bar's open timestamp. **Confirmed close** calculates at `time_close` and shifts the historical plot one chart bar right. On contiguous time-based Bitcoin bars, the next open equals that close. On charts with missing/session bars, Pine's bar-offset placement is not an arbitrary-time renderer: a close value appears at the next chart bar, which may be later. Use Bar open for exact historical timestamp alignment on those charts. Future drawings always use explicit timestamps.

Book mode uses step plots; continuous/monthly modes use broken line plots. Replacements suppress the incoming connector using a `na` plot color, following TradingView's documented discontinuous-level pattern. The replacement's line becomes visible with its next sample; it is never connected to the old branch. There can therefore be a one-bar visual break at replacement, while the allocated count and numerical levels remain valid. [Conditional plot colors and offsets](https://www.tradingview.com/pine-script-docs/visuals/plots/#color-control).

Historical resolution follows chart bars, as with the original plot-based indicator. A daily or weekly Moon curve has coarse step timing; use a shorter chart timeframe for finer historical rendering. Full history does not mean a hidden high-resolution ephemeris has been interpolated between every candle.

Future paths start from a **copy of the confirmed historical allocation**, share its endpoint and continue the same replenish rules. Forecast planning never mutates history/contact state. Defaults are 7 future days, dashed, with 40% transparency. Future days are limited to 0–700 and the display/model end. The maximum future sample-hours input defaults to 6, additionally capped by body speed: Sun ≤5.45h, Mercury ≤2.4h, Venus ≤4h, other planets ≤6h, Moon ≤21.18 minutes. Samples are shared across that body's branches.

Future budgets are 96 segments, 6,000 body samples, 40,000 vertices total and 9,500 vertices per path. A replacement or clipped re-entry starts a new segment. Exceeding these bounds raises an error; shorten the future horizon or reduce enabled counts/bodies. These budgets never truncate historical plots. The maximum setting is 700 days, but the resource budgets still apply. At the default 6-hour maximum sampling setting, 700 days fits Sun alone or Mars and Neptune with one main each plus opposites. Select Custom and enable only those bodies for these configurations. All nine bodies together, or Moon, exceed the existing sample budget at 700 days and require a shorter horizon. The tested 120-day default nine-body and dense Mars/Neptune configurations still fit. Book future transitions are sampled, not exact half-degree root times; continuous paths use `curved=false` linear interpolation. Optional labels/grids are separately bounded. Object-count checks do not establish TradingView execution-time performance.

## Price formula, astronomy and scale

Book mode uses `Q=floor(L+0.5)` for canonical unwrapped longitude L; continuous mode uses `Q=L`:

```text
P(k) = (anchored ? anchorPrice : 0)
       + unit * (Q - (anchored ? anchorLongitude : 0) + 24*k)
O(k) = P(k) + 12*unit
```

At unit 369, main spacing is 8,856 and the opposite offset is 4,428. Manual units/anchors remain available. No normalization, exponential compensation, percent spacing or Bitcoin fitting is applied. Quotes follow the chart; USD and USDT are not converted.

The unchanged native model is geometric geocentric mean ecliptic/equinox of date, valid from **2009-01-01 inclusive to 2051-01-01 exclusive**. It uses native orbital elements, bounded Kepler iterations, planetary perturbations, separate Pluto/Moon models and a secular winding guide. Invalid dates return `na`. The local app uses apparent-of-date by default, so numerical parity is limited by both model error and coordinate convention. Align locally initialized app winding using `L_native ≈ L_app+360*m` and `k_app=k_native+15*m`.

Monthly reproduction rounds/interpolates first-of-month endpoints without re-rounding the interpolated coordinate. It remains a separately labeled mode and is rejected when Moon trajectories are enabled with nonzero count. Events always use instantaneous positions.

The declaration uses `overlay=true, scale=scale.none`. A fresh instance shares the existing chart price scale; remove/re-add an older instance after declaration changes. For comparison with the linear app, select TradingView's Regular price scale and ensure Pin to scale selects Bitcoin's scale. Pine cannot force/read log mode. Additive prices naturally look different on a logarithmic axis; the script does not pre-distort them. [Overlay scale behavior](https://www.tradingview.com/pine-script-docs/visuals/overview/#scale), [indicator attachment](https://www.tradingview.com/support/solutions/43000775579-indicator-moves-separately-or-is-not-attached-to-the-price/).

## Retained research features

Contacts use confirmed standard chart OHLC and the same active identities, counts and brackets as historical plots. A surviving branch retains test/break state; a replacement or clipped re-entry starts fresh. Hidden, zero-count and out-of-band branches cannot alert. Tests/retests, touches, crossings, congestion, gaps, confirmations, reversals and confirming-high/low behavior remain. Alerts are once per bar close, with up to eight messages plus an overflow count. A numerical contact can occur on the first replacement sample before its next visible line segment.

The event-analysis window remains separate from trajectory history. Aspect families, station/ingress/occupancy events, Mars/Saturn clock modes and optional future previews remain. Event labels use an eligible active main price; the first slot may be unavailable at a label time. Root tolerance does not improve orbital accuracy or chart sampling. Manual annotations remain.

Static bands/halfway/adjoining levels and causal research sessions/comparisons remain. Session OHLC must be complete and available by the target instant; weekly bars do not supply daily session comparisons. Outcome ledgers remain internal, with optional source-range boxes. The dashboard and inspection-only controls remain deliberately removed. The [parameter audit](bitcoin-native-pine-parameters.md) records app/schema mappings and local-only controls.
