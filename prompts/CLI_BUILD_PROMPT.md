# Build prompt: AstroCalc terminal application

Build a complete Python terminal application named `astrocalc`, using the calculation workflows in `src/degreeCalc.py` from https://github.com/mvision23/astroCalculations.git as its functional foundation.

The repository is already cloned locally as `astroCalculations`. The version reviewed for this brief is on branch `dev`, commit `8babf9e6f150ad4d90e902ec915f4f5727dc3dd2`. Inspect the current checkout and any repository instructions before editing; preserve existing user changes.

My priorities are keyboard navigation with arrow keys, a convenient calendar for entering dates, and reliable export of every calculation's results to plain text and CSV. Implement, test, and document the finished application.

## Technology and structure

Use Python, PyEphem (`ephem`), and Textual for the interactive terminal UI. Verify APIs against the installed framework version. Package the application with `pyproject.toml` and an `astrocalc` console command that opens the UI. Include `--help` and `--version`.

Separate astronomy calculations, structured result models, terminal screens/widgets, and exporters. Calculation functions must accept explicit arguments and return structured data. Keep interactive input, screen rendering, and file creation in their respective layers. Share result data between the UI and exporters.

Preserve the original script's direct entry point where practical, and guard it with `if __name__ == "__main__":` so importing modules cannot launch its menu. Keep dependencies needed only by `concentric_cycles.py` out of the terminal application's required installation dependencies.

## Required calculation workflows

Retain all 12 calculation choices from the original menu. Related workflows may share screens and services, but each must remain discoverable. Support Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, and Pluto where applicable.

| Workflow | Required behavior |
| --- | --- |
| New moons and degree offsets | List a year's new moons with timestamps, ecliptic longitude, zodiac sign, and degree within the sign. Accept a degree offset and show the derived date and lunar position for each new moon. |
| Moon at a zodiac degree | Select year, month, zodiac sign, and target degree; reproduce the original search behavior and clearly describe its resolution. |
| Aspects between two bodies | Select two distinct bodies and a year; find conjunction, sextile, square, trine, and opposition. |
| Special longitudes | Find bodies near the script's predefined longitudes during a selected year. |
| Monthly aspects for one body | Select a body and month; show its aspects with all other supported bodies. |
| Repeating aspects | Select a body and year; group repeated aspect matches by counterpart body and aspect. |
| Repeating aspects grouped by date | Preserve the original date-grouped view, which actually selects dates with multiple aspect matches. |
| Dates with two or more aspects | Expose the original multiple-aspect-date workflow. It may share an implementation with the preceding view if equivalent behavior is verified and the consolidation is documented. |
| Planetary positions | Select a date; show each body's longitude, sign, degree within the sign, and retrograde indicator. |
| Bodies near 0° of a sign | Search a year and group results by month, retaining the original sampling and retrograde information. |
| Planetary alignments | Preserve the original degree-modulo-24 grouping and show group number, participating bodies, longitudes, and retrograde indicators. |
| All monthly aspects | Show aspects across all unique body pairs for a selected month, including each body's sign and degree. |

Use these special-longitude defaults exactly:

`0, 1, 24, 25, 48, 49, 72, 73, 96, 97, 120, 121, 145, 146, 169, 170, 193, 194, 217, 218, 241, 242, 265, 266, 289, 290, 313, 314, 337, 338`.

## Calculation fidelity and known limitations

Read the executed code carefully; several comments and menu labels do not describe its behavior accurately. Establish regression examples before refactoring, preserving the original coordinate conventions, sampling times, and tolerances by default.

- The new-moon offset uses `input_degree / 13.1764` days. Label it as an estimated date based on constant average motion. Its `new_moon_longitude` argument is currently unused; do not reinterpret the feature as an exact angular-crossing solver.
- The existing “exact time” search samples hourly and matches `int(degree)` against an integer degree bucket. Label the result as the first hourly sample within that bucket. Display the sampled position and resolution. A precise crossing solver would be a separate, explicitly labeled enhancement.
- Two-body annual aspects use a 0.3° orb and daily samples at 12:00 UTC. Single-body monthly and repeating-aspect workflows use 1.0° and daily samples at 00:00 UTC.
- All-pairs monthly aspects sample at 12:00 UTC. Preserve the executed pair-orb rule: take the larger of the per-body values, with Mercury and Mars at 3.5°, Sun at 1°, and other bodies at 2.5°.
- Special-longitude searches sample daily at 00:00 UTC with a strict distance threshold of less than 0.5°. Handle the circular boundary at 0°/360° correctly and document this as a correction to the original linear comparison.
- The zero-degree search samples every six hours, retains positions within 0°–0.5° of a sign, and keeps the first match per body per date. Describe these as sampled near-zero positions; a sampled match is not a guaranteed exact ingress.
- Repeating-aspect counts currently count matching sample dates. Consecutive matching days do not establish separate astronomical events. Make that distinction clear in labels and exports.
- Alignment groups use the executed expression `int(longitude % 24) or 24`, following the script's normalization. This is not grouping by contiguous 24° sectors. Preserve the formula and document its boundary behavior.
- Fix loops where an exception can skip the date increment indefinitely. Report failures clearly and distinguish incomplete calculations from successful searches with no matches.

If exposing orb or sampling settings, keep workflow-specific defaults and include the effective settings with results and exports. Document any intentional numerical change and test it. Keep unrelated astronomy enhancements outside the initial implementation.

## Keyboard interface

Provide a main menu, parameter forms, calendar dialog, results table, export dialog, and help screen. Use clear focus highlighting and a footer showing keys that work on the current screen.

- Up/Down navigate menu choices, dropdown options, and result rows.
- Left/Right work naturally within the focused widget, including calendar navigation and horizontal table movement.
- Tab/Shift+Tab move between fields and controls. Arrow keys in text inputs retain normal editing behavior.
- Enter selects or activates; Escape cancels a dialog or returns to the previous screen without discarding existing inputs.
- Provide discoverable shortcuts for help, export, rerun, and quit. Letter shortcuts must not intercept typing in inputs.
- Every essential action must work without a mouse.

Provide scrollable results, readable column headings, sorting, and simple filtering/search. Keep parameter values when returning from results. Support terminal resizing and a usable 80×24 layout with scrolling or stacked panels where necessary. Use text labels as well as color; provide readable fallbacks for astronomical symbols.

Long calculations must run outside the UI event loop, with visible activity/progress and cooperative cancellation. Cancelled or failed work must not replace a completed result with an apparently complete partial dataset.

## Terminal calendar

Provide a reusable calendar dialog accessible from date inputs. Show a month grid with weekday headings, the focused day, today's date, and the selected date.

- Left/Right move one day; Up/Down move one week, including across month and year boundaries.
- PageUp/PageDown move one month, clamping the day when necessary.
- Provide focusable month/year controls and direct year entry so selecting a distant year is quick.
- Enter confirms; Escape cancels and preserves the previous value.
- Include a Today action and direct `YYYY-MM-DD` entry with inline validation.
- Correctly handle leap years, month lengths, December/January transitions, and supported date limits.

For year-only and month-only workflows, provide appropriate year and month/year selectors instead of requiring an arbitrary day. The planetary-position workflow uses a full date picker and clearly states the effective calculation time, defaulting to 00:00 UTC to match the script.

## Time handling

Use UTC internally and timezone-aware application datetimes, with explicit conversion at the PyEphem boundary. Preserve UTC year/month search boundaries by default and identify those boundaries in the form and result metadata.

Let the user choose a display timezone, defaulting to UTC, with IANA timezone support. Preserve the script's fixed UTC−06:00 option under an unambiguous fixed-offset label. Distinguish it from regions such as `America/Chicago`, which observe daylight-saving changes. Display conversions must not silently alter the instants searched. Document the original coordinate/epoch convention without claiming a different astronomical reference frame.

## Text and CSV exports

Every results screen must offer export to `.txt` and `.csv` through the same dialog. Allow format, destination directory, filename, and either all results or the currently filtered results. Show the selected row count and use the chosen table sort order.

Offer descriptive default filenames containing the workflow and selected period. Confirm before overwriting an existing file. Handle invalid paths and write failures clearly, preserve the results after errors, and show the full saved path on success. Calculation alone must not append to `new_moon_data.csv`.

Text exports must contain a readable title, input parameters, date range, timezone, sampling/approximation notes, result count, and aligned results. Export plain UTF-8 text without terminal color codes or screen borders that impair readability.

CSV exports must use stable documented headers and Python's CSV handling, with correct quoting and newline handling. Preserve numeric values as numeric fields, separate sign from degree, and use ISO 8601 timestamps with offsets. Include UTC timestamps and selected-zone timestamps where timestamps are relevant, along with sufficient query/settings columns to interpret the data. Use workflow-specific schemas instead of packing results into display strings. Grouped reports should export ordinary rows with grouping columns; alignment rows may use a group identifier and one row per member. Define meaningful empty exports, including CSV headers when no matches exist.

## Validation and delivery

Validate dates, supported years, body selections, degree values, timezone names, and optional tolerances before running. Reject non-finite numeric values. Keep errors close to their fields and avoid crashes from ordinary invalid input.

Add focused tests for calculation parity, zodiac and circular boundaries, December/leap-year handling, fixed-offset and DST display conversion, calendar navigation and cancellation, export quoting and schemas, overwrite protection, and the exception-loop correction. Include keyboard interaction tests for a representative path through menu → form → calendar → results → each export format. Smoke-test every calculation workflow and verify that all have both exporters.

Deliver the implemented application, installation and launch instructions, a keybinding guide, calculation limitations, export schema examples, and a brief mapping from the original 12 menu choices to the new interface. Run the relevant checks and report what passed and any actual remaining limitations.

Useful framework references: [Textual documentation](https://textual.textualize.io/) and [background workers](https://textual.textualize.io/guide/workers/).
