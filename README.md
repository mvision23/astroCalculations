# AstroCalc

A keyboard-driven Python terminal application for the 12 astronomy workflows in
`src/degreeCalc.py` at commit `8babf9e6f150ad4d90e902ec915f4f5727dc3dd2`.
Calculations use PyEphem; the interface uses Textual. Results can be searched,
sorted, and exported as plain text or CSV.

An optional **Universal Clock** application adds local Streamlit/Plotly research
views for Jeanne Long's Book I: planetary events, time/price wheels, historical
range comparisons, channels, daily replay and generated Pine v6 indicators.

```sh
python -m pip install -e '.[clock,test]'
universal-clock ui
```

Open `http://127.0.0.1:8501`. See the [application guide](docs/universal-clock.md),
[book-method coverage](docs/book-methods.md), [assumptions](docs/assumptions.md),
and [TradingView guide](docs/tradingview.md). The terminal application below keeps
its original conventions. The new graphical dependencies remain optional.

## Install and launch

Python 3.11 or later is required. From this checkout:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
astrocalc
astrocalc --help
astrocalc --version
```

`python -m astrocalc` and `python src/degreeCalc.py` also open the application.
Importing either module does not start an interactive session. Installation with
`pip install .` works without the development checkout. The UI needs a terminal;
80×24 and larger are supported. Forms and dialogs scroll as focus moves.

`pip install -r requirements.txt` also installs the terminal application.
The separate graphical `src/concentric_cycles.py` script has optional dependencies;
install `.[cycles]` if you want to use it. Those packages are not required by
AstroCalc. No calculation creates or appends to `new_moon_data.csv`.

## Keyboard guide

| Where | Keys |
| --- | --- |
| Everywhere | F1 help, Ctrl+Q quit, Tab / Shift+Tab change focus |
| Main menu | Up / Down, Enter select |
| Forms | F5 calculate; Escape back; Enter activates focused buttons |
| Text inputs | Normal editing arrows; letter keys always type |
| Dropdowns | Enter opens; Up / Down selects; Enter confirms; Escape closes |
| Calendar grid | Left / Right one day; Up / Down one week; PageUp / PageDown one month; Enter confirms |
| Calendar controls | Tab to month and year; type year and activate Go (or Enter in year); Today; direct YYYY-MM-DD + Enter |
| Results | Arrows move cells and rows, F6 sort current column / reverse, F2 settings and notes |
| Results controls | Tab to filter, sort selector, direction button, or Export |
| Results shortcuts | Ctrl+E export, F5 rerun, Escape return to existing parameters |
| Export | Choose format, directory, filename, and all/filtered rows; Ctrl+S save; Escape return |
| Running calculation | Escape or Cancel stops work and preserves the previous completed result |

The calendar distinguishes focused day `[DD]`, today `*DD*`, and the originally
selected date. Escape preserves the original input. Month navigation clamps the
day, so January 31 → February 28/29. Dates are limited to 1900–2100; this is an
application support range, not a claim of uniform ephemeris accuracy.

## Original menu mapping and calculation conventions

All 12 choices retain their original order and remain separately discoverable.
Every workflow has both exporters. All aspect names use readable words, without
requiring astronomical-symbol fonts. Retrograde is shown as Yes/No.

| Original choice | New interface | Sampling and behavior |
| --- | --- | --- |
| 1 | New moons and degree offsets | Year's `next_new_moon` instants; estimated offset date = new moon + degree / 13.1764 days; signed offsets -360 to 360 accepted |
| 2 | Moon at a zodiac degree | First hourly sample from UTC month start whose sign matches and `int(degree)` equals the selected 0–29 bucket |
| 3 | Aspects between two bodies | Daily 12:00 UTC; 0.3° inclusive orb; distinct bodies |
| 4 | Special longitudes | Daily 00:00 UTC; circular distance strictly less than 0.5° |
| 5 | Monthly aspects for one body | Daily 00:00 UTC; 1° inclusive orb; all other supported bodies |
| 6 | Repeating aspects | Annual daily 00:00 UTC; 1° orb; counterpart/aspect groups with more than one matching sample date |
| 7 | Repeating aspects grouped by date | Annual daily 00:00 UTC; 1° orb; dates with at least two matching aspects |
| 8 | Dates with two or more aspects | Same selected dates as choice 7; shared implementation |
| 9 | Planetary positions | Selected date at 00:00 UTC; retrograde motion relative to 24 hours earlier |
| 10 | Bodies near 0 degrees of a sign | Every 6 hours starting at 00:00 UTC; degree within sign in [0, 0.5]; first match per body per UTC date; month grouping column |
| 11 | Planetary alignments | Daily 00:00 UTC; groups with at least two bodies using `int(longitude % 24) or 24`; one row per member |
| 12 | All monthly aspects | All 45 unique pairs daily at 12:00 UTC; pair orb is the larger per-body value: Mercury/Mars 3.5°, Sun 1°, others 2.5° |

Supported bodies: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus,
Neptune, Pluto. Aspects: conjunction 0°, sextile 60°, square 90°, trine 120°,
opposition 180°. Effective settings are available with F2 and in every export.
No custom sampling or orb controls are exposed in this release.

The predefined special longitudes are exactly:

```text
0, 1, 24, 25, 48, 49, 72, 73, 96, 97, 120, 121, 145, 146, 169, 170,
193, 194, 217, 218, 241, 242, 265, 266, 289, 290, 313, 314, 337, 338
```

Choices 7 and 8 originally filter the same dates but print different angles:
choice 7 prints measured separation, choice 8 the nominal aspect angle. The new
shared result includes **both** fields, plus the number of matches on the date.
Choice 6 counts sample dates, including consecutive days, not separate events.
The initial table sort uses its first column; use the sort selector to group or
order by a different field. Filtering is a case-insensitive substring search
across the values in all table columns.

## Numerical fidelity, corrections, and limits

The calculation boundary explicitly converts timezone-aware UTC datetimes to
PyEphem's naive UTC date representation. It preserves the original
`body.compute(date); ephem.Ecliptic(body).lon` convention and PyEphem's default
J2000 epoch. It does not substitute apparent ecliptic longitude of date or claim
a different reference frame. See [PyEphem coordinate transformations](https://rhodesmill.org/pyephem/coordinates.html).

Search intervals are UTC calendar years/months with inclusive starts and
exclusive ends. Position reports cover one selected UTC date at midnight.
Timestamps may display on a different local date without changing the sample
instant or UTC grouping. Use `UTC`, an IANA zone such as `Europe/Athens`, or
`UTC-06:00`. The last is a fixed offset, including in summer;
`America/Chicago` follows historical DST rules. Both UTC and display timestamps
are retained in exports, including derived new-moon dates outside the year.

The lunar offset is an average-motion **estimate**, not an angular crossing
solver. The lunar degree search has **one-hour resolution** and matches a full
integer degree bucket; it is not an exact-time solver. Near-zero matches are
sampled positions, not guaranteed exact ingresses. Retrograde compares wrapped
longitude changes; Sun and Moon are excluded. Choices 10 and 11 compare with six
hours earlier, choice 9 with one day earlier.

Alignment normalization maps longitude 0 to 360; the group formula maps every
remainder in [0,1) to group 24, [1,2) to group 1, and so on through [23,24) to
group 23. It is **not** grouping bodies into contiguous 24° sectors.

Intentional changes from the old script:

- Special-longitude comparison uses circular distance: 359.8° now matches 0°.
- Failures abort with an explicit incomplete-calculation error. No partial
  result can appear as a completed search or overwrite a completed result.
  This also removes exception paths that repeated the same date forever.
- Validation rejects invalid dates, non-finite degrees, unknown timezones,
  unsupported bodies, and identical two-body selections before work starts.
- Results retain full floating-point values; the table/text format shows six
  decimals, and CSV preserves numeric precision rather than old print rounding.
- Export is explicit and protects existing files. Calculations have no file I/O.

Astronomical accuracy remains that of the original PyEphem model and sampling;
there is no precise crossing/event refinement. A successful empty search is a
valid result and can be exported. Failed/cancelled searches cannot be exported.

## Exports

Ctrl+E opens the same export dialog for every result. Choose `.txt` or `.csv`, an
existing destination directory, a basename, and all or filtered rows. The dialog
shows the selected row count. Both choices follow the current table sort. A
second dialog confirms replacement; the default focus is Cancel. Files are
staged in the destination before atomic publication, so write failures do not
truncate an existing file. Errors leave results available; success displays the
full saved path. Exports run locally; no upload or external service is used.

See [export schemas and examples](docs/EXPORTS.md).

## Development and verification

```sh
python -m pytest -q
python -m pip check
python -m compileall -q src/astrocalc
```

The package separates `models.py` (validation/result metadata),
`calculations.py` (explicit pure calculation interface), `calendar.py`
(reusable calendar), `ui.py` (screens/workers), and `exporters.py` (serialization
and protected file writes). For example:

```python
from astrocalc.models import Query
from astrocalc.calculations import calculate
from astrocalc.exporters import save_export

result = calculate(Query("annual_aspects", year=2024, body="Mars", other="Venus"))
save_export(result, ".", "mars_venus_2024.csv", "csv")
```

Calculations run in a Textual thread worker with cooperative cancellation at
sample/body boundaries; widget updates are marshalled to the UI thread. See
[Textual workers](https://textual.textualize.io/guide/workers/). The regression
fixture was captured from the original script before replacing its entry point.
Tests cover all 12 workflows and both exporters, baseline numerical parity,
circular boundaries, calendar transitions, DST/fixed-offset conversion,
exception termination, cancellation, protected writes, and a keyboard-only
menu → form → calendar → results → text/CSV export path at 80×24.
