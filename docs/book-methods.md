# Book methods and capability registry

Source: Jeanne Long, *Universal Clock*, Book I (1993), the supplied 142-page PDF.
Printed page 1 is PDF page 4. Page references below are printed / one-based PDF.
All pages were rendered; diagrams, captions and examples were inspected with OCR
as a reading aid. Selected ambiguous numerals are logged in [assumptions.md](assumptions.md).
The source PDF and OCR text are not redistributed.

The complete machine-readable registry is
[`src/astrocalc/universal/method-registry.json`](../src/astrocalc/universal/method-registry.json).
Every entry includes inputs, procedure, outputs, units, rounding, assumptions,
fixture, implementation, UI, Pine capability, tests and status. Numeric source
transcriptions are in [book-fixtures.json](book-fixtures.json).

| ID | Chapter; printed / PDF | Classification | Local procedure / view | Pine capability |
|---|---|---|---|---|
| UC01-PAIR | 1; 3–9 / 6–12 | explicit book rule | Pair superior with following inferior; compare closed source and target ranges — Aspect families | embedded conjunction display; range research local |
| UC01-WINDOW | 1; 9 / 12 | explicit book rule | Retain strict day; independently compare ±1 calendar day and selected session assignment — Aspect families / market sessions | exact UTC events; session comparison local |
| UC02-POS | 2; 11–16 / 14–19 | explicit book rule | Geocentric longitude; sign=floor(longitude/30); within-sign degree=longitude mod 30 — Astronomy / zodiac | embedded positions in degrees pane |
| UC02-ASP | 2; 15–16 / 18–19 | explicit book rule | Search 0, ±30, ±60, ±90, ±120, ±150, 180 with bounded roots — Astronomy / Events | precomputed exact event drawings |
| UC03-REPEAT | 3; 17–37 / 20–40 | explicit book rule | Expose source/target ranges and all preselected shifted candidates, including misses — Aspect families / Price | astronomical dates displayed; range selection local |
| UC03-SEQUENCE | 3; 18–22, 29 / 21–25, 32 | discretionary interpretation | User assigns sequence and its first event; no unique automatic segmentation in prose — Aspect families | manual local annotation; no automated Pine signal |
| UC03-HISTORY | 3; 28, 38 / 31, 41 | discretionary interpretation | Review prior occurrences and dated wheel ranges; user controls history depth — Aspect families / Clock | local historical-range workflow |
| UC04-WHEEL | 4; 41–49 / 44–52 | implementation formalization of a diagram | 15 rings of 24; (n-1)//24; labels centered, continuous phase x mod 24 separate — Universal Clock | wheel local; phase pane embedded |
| UC04-SCALE | 4; 43–50, 57 / 46–53, 60 | implementation formalization of a diagram | x=P/u; price cycle 24u; historical scales explicitly chosen — Sidebar / methods | adjustable price scale; no optimization |
| UC04-SHIFT | 4; 48–56 / 51–59 | implementation formalization of a diagram | Ordinary overlap separately from modulo-24 overlap; half-cycle=12u — Aspect families / Clock | opposite price trajectories; range overlap local |
| UC04-FAMILY | 4; 52–62 / 55–65 | explicit book rule | Review last three family dates, same and half-cycle shifts without best-fit selection — Aspect families | embedded family labels; historical comparison local |
| UC05-ROUND | 5; 64–68 / 67–71 | explicit book rule | Nearest degree; half-up tie is implementation choice; preserve raw astronomy — Sidebar / Astronomy | same half-up transform; monthly mode rejected explicitly |
| UC05-CHANNEL | 5; 66–83 / 69–86 | implementation formalization of a diagram | P=u(L+24k); O=u(L+12+24k); branch identity fixed through time — Price / Clock | embedded ephemeris, global plots, finite future curves |
| UC05-MULTI | 5; 79–86 / 82–89 | discretionary interpretation | List nearby levels; 98,194,290 share phase 2; no probability inferred — Price candidates / Clock | multiple embedded planet trajectories |
| UC05-CONTACT | 5; 71–77, 84 / 74–80, 87 | discretionary interpretation | Full-range or close touch; intrabar crossing; close beyond; reversal; explicit causal state — Price & replay / Methods | confirmed OHLC contact alert; advanced annotations local |
| UC06-DIV | 6; 87–107 / 90–110 | implementation formalization of a diagram | A=u[24k,24k+1]; B/C/D offsets 6/12/18; closed edges — Price / Clock | static A–D bands for selected cycle |
| UC06-HALF | 6; 90–93 / 93–96 | implementation formalization of a diagram | Midpoint of intervening open gap: offsets 3.5,9.5,15.5,21.5 — Price / Methods | static halfway divisions |
| UC06-AREA | 6; 90–107 / 93–110 | implementation formalization of a diagram | Below band to preceding midpoint = support area; above band to next midpoint = resistance area — Price / Methods | local shaded areas; Pine static reference levels |
| UC06-TEST | 6; 92–95 / 95–98 | discretionary interpretation | Per-level causal state: tests, consecutive contacts, confirmed closes, isolated break/reversal, candle-range gap — Price & replay / Methods | basic confirmed contacts; state-machine analysis local |
| UC07-BAND | 7; 108–114 / 111–117 | explicit book rule | Closed [24k,24k+1] longitude occupancy, independent of rounding — Events / calendar | precomputed band boundaries |
| UC07-COMB | 7; 114–121 / 117–124 | discretionary interpretation | Sweep interval endpoints; show full simultaneous body set once per contiguous interval — Events / monthly calendar | precomputed interval boundaries |
| UC07-MATCH | 7; 119–121 / 122–124 | implementation formalization of a diagram | Solve difference = 24k anywhere on wheel; optional sector interpretation distinct from exact phase — Events / Clock | precomputed exact alignment events |
| UC07-CALENDAR | 7; 125 / 128 | explicit book rule | One column per planet; retain interval entries/exits and simultaneous bodies — Events & calendar | precomputed drawings; matrix local |
| UC08-REPLAY | 8; 126–137 / 129–140 | discretionary interpretation | Synchronize chart/wheel/date; list all levels; show stations, ingresses, visits, alignments; annotate handoffs manually — Price & replay / Clock | embedded astronomy and channels; daily interpretation local |
| UC08-OPPOSITE | 8; 129–137 / 132–140 | implementation formalization of a diagram | Opposite clock level = u(L+12+24k), not an astronomical opposition event — Price & replay / Clock | embedded trajectory transform |
| EXT-SMOOTH | extension; not in Book I / not applicable | extension | Continuous channels instead of rounded book degrees — Sidebar | supported |
| EXT-MOON | extension; 79 boundary / 82 | extension | Use provider/interface for Moon; no claim of Book I lunar method — Sidebar | embedded when requested |
| EXT-ANCHOR | extension; not in Book I / not applicable | extension | P0+u(L-L0+24k) — Methods | fixed exported anchors |

## Source audit notes by chapter

1. Superior → inferior pairing is explicit. Shared endpoint contact counts as
   overlap. Printed p9 expands comparison to surrounding dates, and distinguishes
   Saturday/Friday from Sunday/Monday. The opening Mercury drawing conflates
   greatest elongation with a station; the event engine keeps them separate.
2. Historical archaeology and Gann narratives are documented as the author's
   account, not converted into algorithms. All seven aspect families have both
   branches over a complete cycle. Earth is the observer.
3. The first event of a sequence is chosen visually after several dates; there is
   no uniquely specified automatic rule. The UI records a manual first event and
   sequence. The author's percentage claims are not measured application results.
4. Numbers increase counterclockwise from the right-hand 24-line. Fifteen inner
   rings each hold 24 numbers. Outer price labels retain congruence modulo 24.
   Chapter 4's S&P examples use different futures contracts; their ranges cannot
   be silently concatenated into one historical dataset. Family comparison uses
   all eligible occurrences and exposes the last-three-date choice.
5. Half-degree ties are unspecified. The application uses half-up, preserves raw
   longitudes and separates monthly reproduction from continuous astronomy. A
   30-point Dow break threshold is an example, not a default for every market.
6. A–D are one-unit bands, with midpoint dotted divisions between neighboring
   band edges. Adjoining support/resistance areas extend to those midpoints.
   Congestion, second tests and gaps have explicit adjustable interpretation rules.
7. Actual solar crossings replace a fixed 24-day schedule. Events are occupancy
   intervals and grouped combinations. Mars/Saturn can align on any clock segment.
   The October 1987 discussion and December 1993 hand-drawn matrix are date-level
   comparisons, not exact timestamp ephemerides.
8. Daily sugar replay combines the foregoing tools and annotations. Source ranges
   are sparse transcriptions, not a reconstructed OHLC history. Multiple candidate
   levels remain visible when direction is unresolved. Stations and sign ingresses
   are astronomical events; their suggested market effects are interpretations.

Book II's promised heliocentric, intraday, monthly/yearly clock expansions are not
specified sufficiently in Book I and are outside this implementation. Monthly
sampling here reproduces Book I's Saturn chart construction; it is not Book II's
monthly clock. Moon, anchored transforms and smooth channels are labeled extensions.
No Square of Nine or native Pine astronomy engine is included.
