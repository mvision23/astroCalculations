# Replacement build prompt: Bitcoin Universal Clock calculated directly in Pine

Implement a complete **Bitcoin Universal Clock** TradingView indicator in Pine Script v6, with all astronomical positions, planetary price trajectories, event calculations and chart-price methods executed directly by the Pine script.

**This prompt replaces the generated-ephemeris architecture in `BITCOIN_TRADINGVIEW_INDICATOR_BUILD_PROMPT.md`.** Retain that prompt's functional requirements for planets, Bitcoin charts, Universal Clock settings and method coverage, subject to the explicit replacements below. If the two prompts conflict, this prompt takes precedence. Do not modify the previous prompt.

The agent must write the finished script directly into the repository at:

`astroCalculations/pine/bitcoin_universal_clock_native.pine`

Resolve this path relative to the workspace: if already inside `astroCalculations`, use `pine/bitcoin_universal_clock_native.pine`. Create the directory if necessary. Deliver an actual populated, ready-to-paste file, not a response containing only instructions, a web-app feature, a code skeleton or a generator that the user must run later.

## 1. Work directly in the repository

Inspect repository instructions and existing changes, then implement using filesystem edits and command-line tools. Preserve unrelated work and the existing local application.

Do not launch, navigate, automate or interact with the Streamlit/Universal Clock web app. Do not ask the user to select planets, configure dates, click Calculate, click Generate Pine, download a file, or provide web-app output. Read the application's Python source and saved settings directly to understand its behavior.

Do not require an interactive browser session, TradingView login, upload or publishing workflow to create the deliverable. Reading official documentation and astronomical algorithm sources is allowed. The user can later paste the completed repository file into TradingView; that installation step is not a prerequisite for finishing the file.

Proceed with sensible documented defaults without routine clarification. Implement, validate and save the result rather than stopping at a plan or offering to continue. If an actual technical limitation remains, complete independent work and describe it accurately; do not silently substitute another architecture.

Read these existing sources as applicable:

- `src/astrocalc/universal/astronomy.py` and `events.py` for coordinate and event semantics.
- `geometry.py` for `Scale`, rounding, channel branches and static divisions.
- `workspace.py`, `app.py`, `methods.py` and `market.py` for every setting and price/session method.
- `docs/book-methods.md`, `docs/universal-clock.md` and the Bitcoin saved workspaces.
- The preceding Bitcoin indicator prompt for its complete feature and parameter checklist.

The existing `pine.py` exports precomputed ephemerides. It is useful as a reference for chart rendering, but its data-table architecture does not satisfy this task.

## 2. Replace precomputed ephemerides with a native astronomy engine

Implement functions in Pine that calculate positions for an explicitly supplied timestamp. The indicator must work without Python, a local server, an external planetary feed, a CSV, a downloaded ephemeris, or a table of dated positions/events at runtime.

Astronomical model constants, orbital elements and published analytical-series coefficients may be embedded in the script. They are algorithm inputs, not a disguised cache of daily positions. Temporary caching of results calculated by Pine during execution is allowed. Do not embed sampled timestamp/longitude tables or precomputed event dates as the computational source.

Select and cite documented astronomical algorithms with an accuracy and computational cost suitable for Pine. Implement their actual terms and transformations. Do not replace geocentric motion with constant angular speeds, independent sine waves, a hardcoded retrograde calendar, or heliocentric longitude presented as geocentric longitude.

The implementation must address:

1. Unix milliseconds to Julian date and the time scales required by the selected model. Identify UTC/UT/TT approximations and their consequences.
2. Earth and planetary orbital positions, including a dedicated supported model for Pluto where required.
3. Transformation to geocentric ecliptic longitude using positions in a consistent reference frame.
4. Epoch/equinox and coordinate convention. Implement the corrections needed for a mode before labeling it apparent-of-date, astrometric-of-date or J2000. Do not claim that these modes are interchangeable.
5. Degree/radian conversion, quadrant-correct angles, circular normalization and numerically bounded iterative calculations.
6. Direct/retrograde motion and stations derived from the computed positions, with appropriate finite-difference or analytical speed calculations.
7. A separate lunar model for the optional Moon extension.

Aim to support at least Bitcoin-era dates from 2009 through 2050, and support a broader interval only where the selected model is valid and tested. Publish the supported interval. Outside it, return `na` and explain the limitation; do not invent accuracy for arbitrary dates. This is a model validity boundary, not a date table that needs periodic regeneration.

Use Python or the local astronomy provider only for development-time validation and reference fixtures. Every calculation needed by the installed indicator must exist in Pine. Any development helper must be run by the agent, and the final `.pine` file must already exist when the task ends.

## 3. All planets in one Bitcoin overlay

Use `//@version=6` and `indicator(..., overlay=true)`.

Calculate **Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune and Pluto** in the primary script. Provide a Moon extension, disabled by default. Earth is the observer and must not be assigned a fictitious geocentric trajectory.

Each body needs independent visibility and color controls. All nine book bodies must work simultaneously in a single indicator. Provide grouped input sections and a usable default branch count. Retain optional master visibility controls, opposite channels, future curves, labels and alert filtering from the preceding prompt.

Use the active TradingView chart's prices, symbol, currency and tick size. Keep its candles visible. Default Bitcoin research sessions to UTC/24/7, and preserve the distinction between USD and USDT. Do not hardcode an exchange or assume the local CSV's prices match the active chart.

Evaluate astronomy at explicit bar timestamps; do not advance planets by one fixed amount per candle. Document open-time versus confirmed-close-time sampling. Support time-based intraday, daily and weekly charts with clear behavior for unavailable or nonstandard OHLC.

Compute future positions by calling the same native astronomy functions at future timestamps. Changing the future horizon within supported bounds must not require regenerating source code. Use bounded time-positioned drawings for future curves, with no fabricated future Bitcoin prices.

## 4. Preserve the Universal Clock mathematics

Use the existing local `Scale` semantics:

```text
u = quoted price units per wheel step; default Bitcoin preset = 369
L(t) = continuous unwrapped geocentric ecliptic longitude
Q(L) = floor(L + 0.5) in book mode, or L in continuous mode

P_k(t) = u * (Q(L(t)) + 24*k)
O_k(t) = u * (Q(L(t)) + 24*k + 12)

Anchored extension:
P_k(t) = P0 + u * (Q(L(t)) - L0 + 24*k)
O_k(t) = P0 + u * (Q(L(t)) - L0 + 24*k + 12)
```

At scale 369, adjacent main channels differ by 8,856 and opposite channels by 4,428. Treat 369 as a configurable research preset, not a demonstrated forecasting optimum.

Expose unit, rounding, anchors, fixed branches, price display bounds and opposite/midpoint controls. Maintain branch identities through retrograde motion and zodiac wrap. Do not repeatedly select whichever branch is nearest the current closing price.

Choose and document a consistent longitude-unwrapping reference so historical and future curves join correctly. The same timestamp and settings must not acquire a different channel solely because a different number of chart bars is loaded. Handle sparse chart bars and multiple revolutions without deriving the winding count from an ambiguous shortest-angle jump. Any runtime numerical unwrapping path must be bounded and validated.

Reuse the app's static grid: A–D bands at offsets 0, 6, 12 and 18 within each 24-step cycle; halfway lines at 3.5, 9.5, 15.5 and 21.5; source-derived adjoining support/resistance areas. Preserve the existing distinction between an anchored planetary curve and the unanchored static grid unless a separately labeled extension is provided.

## 5. Replace export settings with real runtime settings

Audit every field in `Settings`, `Scale`, `MarketSpec`, `ContactSettings`, and relevant additional `app.py` controls. Write the mapping to `docs/bitcoin-native-pine-parameters.md`.

Classify controls as **editable in Pine**, **chart-derived**, **fixed model property**, or **local-only with a concrete reason**. There is no generated-ephemeris or regeneration category in this implementation.

Apply these replacements to the earlier prompt:

- Dates and future days become runtime calculation/display settings within model validity and resource bounds.
- Body selection is a runtime visibility/calculation setting; all required body models are present in the script.
- Aspect pair, seven aspect families, orb, occupancy interpretation and clock-alignment interpretation operate on positions calculated in Pine. No embedded event catalogue needs rebuilding.
- Coordinate modes are runtime choices only if their actual transformations are implemented. Otherwise expose the actual fixed convention and list the unsupported mode explicitly; never show a nonfunctional dropdown.
- Monthly reproduction, when supported, calculates first-of-month positions directly in Pine and follows the local interpolation/rounding semantics.
- Position spacing becomes future-rendering or event-search spacing where appropriate. Event solver tolerance remains distinct from astronomical model accuracy.
- Ephemeris export knot spacing, source generation and table interpolation settings no longer apply. Replace them with documented native-model accuracy and numerical/rendering tolerances; do not pretend they control the underlying model's precision.
- Contacts, static bands, halfway/adjoining areas, anchors, session comparisons, shifts and source-range windows retain their applicable runtime behavior from the preceding prompt.
- CSV import, full circular research UI, workspace-file handling and local image/HTML export remain local-only facilities, not dependencies required to build or run the indicator.

Every visible input must affect its advertised calculation or display. Preserve numeric semantics rather than merely copying input labels.

## 6. Native events, chart-price methods and alerts

Calculate the selected pair's 0°, 30°, 60°, 90°, 120°, 150° and 180° aspects, retaining both phase branches as appropriate. Calculate stations, zodiac ingresses, 24-line occupancy, simultaneous occupancy and Mars/Saturn clock alignment from the same native positions. Distinguish clock alignment modulo 24 from zodiac conjunction.

Use bounded timestamp searches and refinement for requested exact events. Handle wrap, retrograde recrossings, stationary touches, and more than one crossing between sparse chart bars. Do not label the first sampled bar inside an orb as an exact event time. Where only sampled detection fits a chosen mode, label its resolution clearly. Restrict expensive refined-event searches to a documented analysis window instead of rerunning an entire century on every candle.

Implement the applicable price-contact state machine and source-range methods using the chart's confirmed prices and completed research sessions. Preserve tolerance, field, separation, congestion and confirmation controls. Do not use future OHLC, make a daily source range available before its session closes, or treat an intraday candle as a complete day.

Use proper daily/session data for comparison methods on weekly charts, or explicitly disable those methods when the required data cannot be obtained. Retain missing cases and misses. Bound source-range boxes, event labels, annotations and history. Price alerts must respect visibility/selection settings and confirmed-bar rules. Future astronomical events are computable; future price-contact outcomes are not.

## 7. Performance and accuracy are part of the implementation

Check the current official [Pine limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/) and [drawing APIs](https://www.tradingview.com/pine-script-docs/visuals/lines-and-boxes/). Budget compilation size, plot counts, arrays, drawings, per-bar work and total execution time with all nine bodies enabled. Disabled plots still occupy compiled plot capacity.

Share reusable Earth/time/frame calculations across bodies at the same timestamp. Calculate expensive future paths and event windows only when required, cache Pine-computed results where useful, and cap sampling/iteration counts. Reduce optional branch count or drawing density explicitly before sacrificing required planets or silently degrading astronomical accuracy. Keep all nine core bodies in the primary indicator.

Compare the native astronomy against independent reference positions in a matching frame. Report maximum/RMS angular errors per body, supported intervals and test coverage. Convert longitude error into smooth price error with `abs(u)*angular_error`; book rounding additionally has discontinuities near half-degree boundaries. Do not promise sub-tick price accuracy when the model does not support it, or confuse a one-second root-solver tolerance with one-second astronomical accuracy.

If the native model is less accurate than the local application, retain exact price-transform semantics and document the measured astronomical difference. Do not force agreement by fitting offsets to Bitcoin price movements or substitute dated lookup tables to hide model errors.

## 8. Write, verify and deliver the files directly

Required output:

1. `pine/bitcoin_universal_clock_native.pine`: the complete self-contained overlay, containing the astronomical algorithms and all nine book bodies plus the selectable Moon extension.
2. `docs/bitcoin-native-pine.md`: installation steps, algorithm/coefficient references and licenses, model convention, supported dates, defaults, performance limits and measured accuracy.
3. `docs/bitcoin-native-pine-parameters.md`: exhaustive app-to-indicator parameter mapping.
4. Appropriate local validation fixtures/tests and a report stating exactly what was run. An optional native degrees/phase/speed companion may also be provided.

Validate scale/rounding/anchor arithmetic, all planet toggles, static divisions, event semantics, branch continuity, date boundaries, future trajectories and non-repainting price logic. Include independent timestamps around Mercury retrograde, longitude wrap and Pluto positions, and check behavior across chart timeframes. Preserve existing application tests relevant to any shared-code edits.

Distinguish a local mathematical reference test from execution of the actual Pine code. Use a noninteractive Pine compiler/test facility if one is available and authorized. If it is not, save the finished script and report that TradingView compilation/runtime remain unverified, with a short manual checklist. Do not request web-app interaction or a login to finish repository delivery, and do not claim compilation based on a Python reimplementation.

Before finishing, verify that the actual `.pine` file exists at the requested path, contains the native astronomy functions and usable indicator code, and has no TODO-only bodies, fake positions, dated ephemeris/event tables or runtime dependency on the local app. Report any genuine remaining limitation without declaring unimplemented requirements complete.

Finish with links to the repository files, the checks performed and any material limitations. The user should receive a directly usable repository artifact whose calculations run inside Pine, with no Universal Clock web-app generation step.
