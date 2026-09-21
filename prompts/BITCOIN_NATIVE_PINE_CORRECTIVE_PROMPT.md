# Corrective build: native Bitcoin Universal Clock trajectories and price-band controls

Correct the existing `pine/bitcoin_universal_clock_native.pine` directly. This is a repair of the native Pine v6 indicator, not a new generated-ephemeris architecture. Deliver an updated populated script, regression tests and documentation. Preserve unrelated repository changes and the working local application.

The user requires three changes:

1. Remove **all `f_cell` code and the on-chart table/dashboard**.
2. Investigate, numerically verify and correct the distorted planetary trajectories, especially Sun, Moon, Mercury, Venus and Mars. Use `output.png`, `output2.png` and the expected appearance in `webapp.png` as visual evidence.
3. Let the user choose **how many parallel trajectories each planet displays and the minimum/maximum price levels within which they appear**.

This prompt overrides conflicting display and branch-allocation requirements in `BITCOIN_NATIVE_PINE_BUILD_PROMPT.md`. Retain native astronomy, all nine core planets, optional Moon, exact Universal Clock price arithmetic and causal price methods. Do the implementation and validation, not merely propose a fix.

## Read the implementation and visual evidence

Read the three images before changing code. Inspect:

- `pine/bitcoin_universal_clock_native.pine`, including orbital functions, `f_guide`, `f_geo`, `f_coordinates`, `f_monthly_coordinate`, `f_price`, `centers`, `levels`, the 60 historical plots, future paths, contact identities and the dashboard.
- `src/astrocalc/universal/astronomy.py`, especially `EphemProvider` and `series`.
- `src/astrocalc/universal/geometry.py`, especially `Scale.price` and `Scale.branches`.
- `src/astrocalc/universal/workspace.py` and `plotting.py`, including monthly reproduction, branch enumeration, price-axis bounds and historical/future joining.
- Existing native tests, `tools/native_pine/`, saved Bitcoin workspaces and `reports/bitcoin-native/`.

Do not launch or automate the Streamlit application. Reproduce its calculations and rendering using its source/headless helpers. Do not require a TradingView login, browser session or user configuration to finish the repository files. If no authorized Pine compiler/runtime is available, state that precisely and complete all independent work.

### Findings to start from, not assumptions to hardcode

The current implementation has:

- A single global `branchCount` capped at three main branches, rather than independent per-body counts.
- Three fixed k slots centered once at 2026-09-01 and price 100,000. The app instead enumerates branches intersecting its price interval across its calculation interval.
- A default display interval of 0–200,000 quote units. Fast-body fixed branches can approach zero and then leave that interval. This can greatly affect autoscaling.
- Historical `plot()` values attached to chart bars, while future drawings use explicit timestamps. Check close-time sampling alignment as well as numerical values.
- A large table implemented by `f_cell`, plus inspection-only controls and calculations.

In `output2.png`, the pronounced Sun/Moon bending and compressed candles are **consistent with** logarithmic price scaling and near-zero trajectories. Neither cropped TradingView image exposes enough axis/settings information to establish that conclusively. A linear price trajectory becomes curved in logarithmic screen coordinates. Do not assert from the screenshots alone that the ephemeris is wrong, that the price scale is logarithmic, or that the three images cover identical dates/settings.

A headless spot check of the current source expressions, using its default fixed reference and book unit 369, found these center-branch values during the preceding year:

- Sun: price 102,951 at the reference; a sampled price of 369 on 2025-11-23.
- Moon: price 97,785 at the reference; a sampled price of 3,321 on 2026-08-12.
- Mars: price 99,999 at the reference; a sampled price of 1,845 on 2025-09-02.
- Neptune: price 98,892 at the reference; minimum sampled positive value 97,047 in that interval.

Those are reproducible diagnostic examples, not inferred screenshot settings or constants to put into the indicator. Verify them against the current file. Existing angular-error reports are useful evidence but do not prove that Pine execution, branch allocation, timestamps or chart rendering are correct.

## 1. Remove the table completely

Delete the `f_cell` definition and every invocation. Remove the dashboard's `table.new`/`table.cell` code and all table-only inputs, arrays, formatting helpers and work. In particular audit `inspectionOn`, `inspectionFixed`, `inspectionTime`, `measuredError` and `f_result_text` for removal when they have no remaining use.

Do not just disable the table by default, rename its helper, or replace it with another persistent dashboard or a wall of labels. Preserve actual contact/session/comparison calculations and manual annotations where they serve independent functionality. Rename shared controls such as “Event / table timezone” to describe their remaining purpose. Update the parameter audit to mark the inspection table as deliberately removed.

Keep necessary unsupported-setting/resource errors concise. Put detailed model accuracy and validation output in repository reports. A temporary validation script or optional separate development artifact is acceptable; the delivered primary overlay must have no dashboard.

Acceptance: a search for `f_cell` in the delivered indicator returns no matches, and there are no remaining table declarations/calls or dead inspection inputs.

## 2. Establish why the trajectories differ, then fix the responsible layer

Separate these layers in the diagnostic report:

1. Orbital calculation and geocentric longitude.
2. Longitude winding/reference and direct/retrograde motion.
3. Price transform and branch selection.
4. Timestamp placement, sampling and line segmentation.
5. Linear/logarithmic axis, shared price scale and autoscaling.

### Verify the astronomy and price values

Build a reproducible numerical comparison for **Sun, Moon, Mercury, Venus, Mars and Neptune**, with regression coverage for the other bodies. For explicit UTC timestamps record wrapped longitude, canonical unwrapped longitude, speed, rounded coordinate, body/k/opposite identity and resulting price.

Use an independent ephemeris in a matching coordinate frame to check the astronomy. Separately compare the app's actual output and document its coordinate convention. The current native model is geometric mean ecliptic/equinox of date; the app defaults to apparent-of-date. Do not silently treat these as identical, fit offsets to the screenshots or substitute heliocentric positions. Preserve or improve the measured angular accuracy and report maximum/RMS error per body after any model change.

Align winding references correctly for app comparisons. A constant difference of 360*m degrees between unwrapped series is offset by **15*m branches** because 360/24=15. Show the reference transformation explicitly; raw k labels from differently initialized series need not match. Do not correct a constant branch/reference offset by changing orbital speed.

Preserve exactly:

```text
Q(L) = floor(L + 0.5) in book mode, otherwise L
P_k(t) = (anchored ? P0 : 0) + u * (Q(L(t)) - (anchored ? L0 : 0) + 24*k)
O_k(t) = P_k(t) + 12*u
```

At u=369, adjacent main branches differ by 8,856 and opposites by 4,428. For a given body, all parallel branches have the same shape as functions of time and differ by constant additive prices. Do not replace this with percentages, compounded/exponential prices, independent sine waves, current-close anchoring or a rescaled longitude slope.

Check degrees/radians, atan2 quadrants, Julian-date epochs/time units, Earth-vector sign, model frame, rounding order, integer/float behavior in actual Pine expressions, 0°/360° wrap and lunar multi-revolution intervals. Evaluate actual timestamps rather than advancing a fixed amount per candle. Preserve correct retrograde loops. Monthly reproduction must remain a separately labeled mode: do not use shortest-angle month endpoints as a substitute for the Moon's instantaneous trajectory. Reject or explicitly delimit an unsuitable lunar monthly mode rather than making it the default repair.

### Verify the chart scale rather than distorting the formula

The comparison against the app must use a **regular linear price axis**, matching timestamps, quote units, scale, rounding, anchors, visible price bounds and body selection. Compare the same price coordinates, not just screenshot slopes from different aspect ratios/date spans.

The indicator must share the symbol's price scale, not create an unrelated normalized/percentage/degree scale. Investigate the supported `indicator()` scale behavior and actual chart attachment. Do not invent a Pine API that reads or forces the user's log/linear mode. If the chart setting cannot be controlled programmatically, document the exact supported TradingView scale selection; do not make that user action a prerequisite for implementing the repair.

**Do not exponentiate or otherwise pre-distort prices to make them look straight on a logarithmic axis.** Constant additive channel spacing will not have constant pixel spacing on a logarithmic chart. Correct USD/USDT price values must remain correct in either display mode; visual parity with the linear app is evaluated on a linear axis.

Use positive, useful Bitcoin display bounds by default, such as 70,000–125,000, and let the user edit them. Do not plot zero placeholders or near-zero off-band points that compress the candles. Clip by returning no value/ending a segment, not by clamping all out-of-range values onto the price boundary. Never freeze invalid or expired astronomy at an endpoint.

### Fix sampling and segmentation

Inspect historical plot versus future drawing timestamps, especially confirmed-close mode: a value calculated at `time_close` must not silently masquerade as an open-time sample in a timestamp-parity claim. Resolve any placement mismatch using a supported rendering approach and document bar-associated plot limitations if relevant.

Ensure all historical/future paths use the same model, price formula, branch identity and relevant monthly/rounding mode. Prevent joins between different k values, different bodies, clipped gaps or longitude wraps. A fast-body trajectory must not become a spurious near-vertical connector because a rendering slot was reused.

Use enough temporal resolution for fast bodies and lunar motion, with explicit rendering-error/sample budgets. Default coarse future samples must not be presented as exact half-degree step-transition times. Do not turn `curved=true` into an apparent astronomy fix; any interpolation must preserve the numerical trajectory and avoid overshoot.

## 3. Independent counts and price intervals for each body

Replace the single global three-branch restriction with functional per-body controls for every core planet and Moon:

- Body visibility and existing color behavior.
- **Main parallel trajectory count**, including zero. Support at least 0–12 per body in configurations that fit the declared resource budget, and demonstrate more than three for one body.
- **Use shared price range / use body-specific price range**.
- **Minimum price** and **maximum price** for the effective range.
- Preserve the opposite-channel toggle; explicitly state whether the count excludes opposites. Use “main trajectories” for the count, so N mains with opposites enabled can produce up to 2N visible curves.

Shared bounds should remain a convenient default. Body-specific bounds must genuinely control branch selection/clipping, future paths and price-contact eligibility, not merely relabel the chart. Reject invalid ranges clearly. When fewer branches fit a band, show the eligible branches; never fabricate spacing to achieve the requested number.

Provide a clearly defined **price-band coverage mode** that can reproduce the repeated family of trajectories across the selected interval seen in `webapp.png`. Do not merely add per-body N inputs around the existing fixed September 2026 center and leave most historical fast-body coverage empty.

Define the count in this mode as the maximum number of simultaneously displayed main branches for that body. Select eligible branches deterministically from the configured price interval, with an explicit documented ordering when N is smaller than the eligible set. Selection must not depend on the current Bitcoin close. As branches enter/leave the fixed band, preserve their mathematical identity `(body, k, opposite)`; drawing-slot reuse must start a separate segment and must not inherit another branch's contact state.

A fixed-reference/manual-k mode may remain as an optional alternative. In that mode, N refers to a fixed set of integer branches; do not promise N visible lines at all dates if they leave the range. Explain this difference in the input tooltips/docs.

For instantaneous branch eligibility, use the exact transform as the basis:

```text
base(t, side) = (anchored ? P0 : 0) + u * (Q(L(t)) - (anchored ? L0 : 0) + (side == opposite ? 12 : 0))
k_min(t, side) = ceil((effective_low  - base(t, side)) / (24*u))
k_max(t, side) = floor((effective_high - base(t, side)) / (24*u))
```

Here Q must follow the active rendering mode; monthly coordinates are already interpolated/rounded as specified and must not be rounded again. Retain exact boundary inclusion and opposite semantics. A bounded union of eligible branches over an explicit rendering interval is also useful, but do not confuse total branch identities visited across that interval with the simultaneous count requested by the user.

All actually displayed segments must remain within the effective price bounds. Labels, future curves, contact states and alerts must use those same identities and selection rules. Rendering-window changes must not change the astronomical value or price of a given `(timestamp, body, k, side)`.

## 4. Respect Pine limits while increasing useful coverage

Do not simply expand the current 60 `plot()` calls beyond Pine's 64 plot-count limit. Current source uses constant historical plot colors for a reason: non-constant colors, including input colors, can consume another plot count. Hidden plots still consume compiled capacity.

Choose and implement a viable bounded rendering strategy: time-positioned polylines/line segments, a correctly segmented plot/drawing hybrid, or another supported design. Preserve simultaneous support for all nine core planets plus optional Moon. Price-band coverage cannot be achieved by stitching unrelated branches into one continuous plot.

If drawings require finite history, expose and document the rendering window separately from astronomical model validity and from event analysis. Share native samples across branches rather than recalculating the orbit for each parallel line. Account for clipped/re-entering paths, future styles and all optional feature drawings when budgeting resources. User counts must have predictable effects.

Check current official limits. Reject configurations exceeding the declared budget before silently losing planets, truncating branches, decimating away retrograde loops or invoking garbage collection as the allocation strategy. Demonstrate both the default all-body configuration and a dense Mars/Neptune configuration approximating the requested visual density. Do not claim unlimited counts or full chart history if the implemented renderer cannot provide them.

Preserve existing causal sessions/contacts/events unless a change is necessary for correct branch identities. Do not reintroduce the removed table as a budget/error reporting device.

## 5. Validation and deliverables

Create a corrective report that separates **confirmed defects**, **scale/setting differences**, **hypotheses** and **remaining unverified platform behavior**. It must explain what accounts for the Sun/Moon and Mars/Neptune examples without claiming screenshot metadata that is not visible.

Required regression checks:

1. No `f_cell`, dashboard/table API calls or dead inspection controls in the primary indicator.
2. Independent astronomy checks and app comparisons with explicit frame and winding alignment; Sun, Moon, Mercury, Venus, Mars and Neptune must be included.
3. Constant 8,856 main / 4,428 opposite price offsets at u=369, negative half-degree ties and anchor parity.
4. Solar smooth motion in continuous price coordinates, Mercury/Mars retrograde cases, lunar wrap and multiple revolutions, validity endpoints, and different chart bar spacings.
5. Linear versus logarithmic **presentation** fixtures demonstrating that the same numerical prices can look different; no change to price arithmetic to compensate.
6. Independent body counts, more than three branches, zero count, shared and per-body bounds, opposite counting, narrow bands, exact boundary inclusion, and invalid/over-budget input rejection.
7. Price-band coverage across the rendering window, branch entries/exits, slot reuse and no cross-branch connectors. Use a sufficiently long Moon example that a three-fixed-branch implementation would visibly fail coverage.
8. Historical/future joining for open and confirmed-close samples, clipping, monthly mode and sufficient fast-body rendering resolution.
9. Hidden/out-of-band/reallocated branches cannot generate unintended confirmed-price alerts; source sessions remain causal.
10. Resource checks under all-body and dense selected-body configurations, preserving color/plot limits.

Generate headless comparison figures and numeric fixtures from the implementation for the Mars/Neptune and Sun/Moon cases, using a common explicit date range and positive price bounds. If exact screenshot settings cannot be recovered, label the chosen fixture assumptions rather than pretending it is a pixel-exact reproduction. Use the existing image references as acceptance guidance, not numeric ground truth. The development mirror alone is insufficient: test expressions/data derived from the actual Pine source wherever practical.

Deliver:

- Updated `pine/bitcoin_universal_clock_native.pine`.
- Updated native usage documentation, parameter audit and relevant tests.
- `reports/bitcoin-native/correction-report.md` with numerical comparisons, visual fixtures, resource measurements and the diagnosed causes.

Run the development helpers yourself. The indicator must remain self-contained, with no Python/server/CSV/dated-position-table dependency at runtime. Do not fit trajectories to Bitcoin prices. Keep the existing supported date interval unless a broader interval is independently validated.

Compile/test the actual script with an authorized facility if available. Otherwise clearly distinguish headless mathematical/rendering checks from unverified TradingView compilation, runtime and scale attachment, and provide a short remaining manual checklist. A passing Python mirror is not evidence of Pine compilation.

Finish with links to the updated artifacts and a concise statement of what was fixed, how it was confirmed, per-body count/range behavior and any actual remaining limitation.

## Official references to verify during implementation

- Chart price scales: https://www.tradingview.com/support/solutions/43000748166-how-to-configure-your-supercharts/
- Indicator attachment to the price scale: https://www.tradingview.com/support/solutions/43000775579-indicator-moves-separately-or-is-not-attached-to-the-price/
- Plot counts and color qualifiers: https://www.tradingview.com/pine-script-docs/visuals/plots/#plot-count-limit
- Platform limits: https://www.tradingview.com/pine-script-docs/writing/limitations/
- Time-positioned drawings: https://www.tradingview.com/pine-script-docs/visuals/lines-and-boxes/
