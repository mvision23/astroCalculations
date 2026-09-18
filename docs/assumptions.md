# Assumptions, ambiguities and discrepancies

This log separates source transcription, astronomical calculation and research
interpretation. The source is the supplied 142-page scan; printed pages = PDF − 3.
The PDF checksum and rendering/OCR coverage are in [source-audit.json](source-audit.json).

| Topic | Source | Resolution |
|---|---|---|
| Mercury elongation vs station | printed 4 / PDF 7, cycle drawing | They are distinct astronomical events. Stations solve the longitude derivative; no elongation=station rule is encoded. |
| First repetition date | 18 / 21 | The author suggests inspecting 6–7 dates. Manual sequences expose the first date. Consecutive comparisons are a parameterized interpretation; same-family comparison is separate. |
| Percentage claims | 18, 57 / 21, 60 | Not treated as measured accuracy. Synthetic demos never support the author's claims. |
| Weekend policy | 9 / 12 vs 110 / 113 | Chapter 1 suggests Friday for Saturday and Monday for Sunday, while the later two-day August 1991 example uses Monday. Explicit previous/next/strict policies and the expanded window remain separate. |
| Mercury conjunction date | 4 / 7 | The March 8, 1993 label corresponds to March 9 ~04:01 UTC / March 8 ~23:01 New York. The source's January 23 ~15:43 GMT is close to the backend ~15:41:39 UTC. No timestamp is changed to force the book date. |
| Nearest longitude degree | 64 / 67 | Less than / more than 30 minutes specified; exactly 30 unspecified. Implementation uses floor(L+0.5), including unwrapped turns. |
| Dow price-label ties | 61 / 64 | **Separate** nearest-price-label rule: 2678→2680, 2215→2210; half-step ties downward. Does not change planetary channels or longitude rounding. |
| Halfway dotted divisions | 90–93 / 93–96, Chart 16D | Formalize the midpoint between neighboring band edges: 1.655 between 1.63 and 1.68. These values are inferred from the diagram, not printed exact universal orbs. Bands [a,a+u] have adjoining support [a−2.5u,a] and resistance [a+u,a+3.5u]. The prose calls this the 3-cent area approximately. |
| Neptune March 22 numeral | 128 / 131 | The faint list can look like 21°52′ Capricorn, but the printed rounded column is 291 and the ephemeris/backend give ~20°52′. The fixture uses 290°52′ and records the ambiguity. The backend was not modified. |
| Saturn monthly lines | 68 / 71 | Reproduction rounds monthly samples then connects those values with straight lines. Standard book mode rounds the actual timestamp longitude. Smooth mode is an extension. |
| Legacy special longitudes | 109 / 112 vs calculations.py | Book-derived bands include 144–145, 168–169, etc. Existing legacy constants and all terminal workflows remain untouched. |
| Meaning of occupancy | 109, 118–125 / 112, 121–128 | Default uses the stated continuous closed bands [24k,24k+1]. Optional nearest-degree labels and integer-degree buckets are explicitly labeled interpretations. They are not silently substituted to improve agreement. |
| October 1987 | 118–120 / 121–123 | Continuous Jupiter occupancy is Oct 16–23, whereas source says Oct 9–23; integer-degree buckets [24,26) reproduce the wider dates. Uranus was ~263.51° on Oct 15, rounded to 264 but outside continuous [264,265]. Thus the source's simultaneous grouping differs from default strict bands. |
| Uranus zodiac conversion typo | 118 / 121 | 24–25° Sagittarius is 264–265°, not the printed parenthetical 240–241°. Also, Uranus did not continuously occupy that one-degree band all year. Keep the qualitative claim and measured occupancy separate. |
| December 1993 calendar | 125 / 128 | Drawn date-level arrows have approximate endpoints and appear to include whole-degree buckets. Neptune is ~289.39° on Dec 1, outside [288,289], but within [288,290), explaining an interpreted visit through Dec 19. The default continuous result legitimately differs. |
| October wheel price typo | 121 / 124 | The prose lists 2060 then subtracts 240 from 2090. The uniform 240-step ladder implies 2090; the inconsistency is retained here. |
| April dates and Mercury | 132–134 / 135–137 | 'Friday April 3' conflicts with the 1993 calendar (April 3 was Saturday). Mercury is still in Pisces around April 5; Aries ingress occurs mid-April. Exact events and the prose's daily observations are separate. |
| Sugar tolerances | 127, 131 / 130, 134 | Printed prices are rounded to .05; prose allows one sector either side. This is a sugar-example interpretation, not a universal price-touch tolerance. |
| Cash vs futures | 19, 55, 84 / 22, 58, 87 | No roll or adjustment is inferred. The two S&P range examples use different contract months and are separate fixtures. Chart-derived Dow ranges can be one point imprecise and some date labels are weekends. |
| Moon and Book II | 79, 137 / 82, 140 | Moon is an extension; heliocentric and Book II clock expansions are not specified here. |

## Operational conventions

- UTC-aware instants inside calculations; IANA zones only for display/session interpretation.
- Supported interval 1900–2100; this is an application boundary, not uniform accuracy certification.
- PyEphem 4.2 apparent geocentric equatorial coordinates (`g_ra`, `g_dec`) are
  explicitly transformed into ecliptic coordinates of date. Astrometric-of-date
  and unchanged legacy-J2000 modes are available. Changing the epoch alone is
  **not** the apparent-coordinate conversion.
- A symmetric 30-minute finite difference measures angular speed. Numerical
  event tolerance (default one second) is not a statement of one-second
  ephemeris accuracy. Probes/refinement are bounded and designed for the physical
  motion rates of the supported bodies, not arbitrary pathological functions.
- The source's minute-rounded samples are compared at 00:00 UTC with a 0.04°
  acceptance tolerance. This establishes consistency at the scan's practical
  resolution, not an independent high-precision ephemeris validation across 201 years.
- Session calendars are 24/7 or weekdays plus supplied holiday exclusions. No
  exchange calendar is inferred. Daily labels mean the session's closing date;
  overnight opens belong to the previous local day. Intraday open labels require
  an explicit bar duration. Ambiguous/nonexistent DST instants are rejected.
- The first source range becomes usable only at session completion. A missing
  close-only/partial/unavailable source range stays unavailable. Expanded-window
  misses are not counted until all expected sessions in that window are present.
- Contacts use completed bars only. A continuous touch episode is one test;
  leaving and re-entering after minimum separation permits another. Congestion
  requires consecutive touches. Close-through confirmation is consecutive closes
  beyond a boundary. Full-candle gaps require disjoint candle ranges on opposite
  sides, distinct from intrabar crossing. Taking the first confirmed close bar's
  high/low is recorded only on the later completed bar. These are interpretations.
- No OHLC forward filling, price-dependent nearest-branch splicing, future-price
  generation, secret scale fitting, or trading strategy is performed.
- Sparse book range files contain low/high only. Their displayed availability is
  an explicit end-of-printed-date convention, not proof of the actual exchange
  session for every historical chart. Use genuine session-aware OHLC for empirical
  evaluation. A supplied source date is never silently moved to make an example fit.
- Pine error figures measure independent interpolation probes against this local
  provider. Full-precision price error is `u * angular error`; nearest-degree
  rounding can differ by one whole unit near a half-degree threshold. The
  exporter reports this discontinuity rather than promising sub-tick rounded parity.
