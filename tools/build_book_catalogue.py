"""Maintain the source index and selected numeric transcriptions (not historical OHLC)."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
rows=[
('UC01-PAIR',1,'3–9','6–12','Charts 1A–1D; conjunction diagrams','explicit book rule','Mercury/Sun exact conjunctions; completed session low/high','Pair superior with following inferior; compare closed source and target ranges','pair rows, hits, misses, unavailable','events.py; methods.py','Aspect families','embedded conjunction display; range research local','soybean_pairs','test_real_conjunction_geometry_and_stations; test_comparison_causal_availability_and_missing_denominator'),
('UC01-WINDOW',1,'9','12','Requirements for overlapping price ranges','explicit book rule','UTC event; IANA sessions; window; session policy','Retain strict day; independently compare ±1 calendar day and selected session assignment','strict/assigned/expanded outcomes','market.py; methods.py','Aspect families / market sessions','exact UTC events; session comparison local','weekend_window','test_dst_session_labels_weekends_and_holidays'),
('UC02-POS',2,'11–16','14–19','January 1993 ephemeris; aspect series','explicit book rule','body, UTC time, coordinates','Geocentric longitude; sign=floor(longitude/30); within-sign degree=longitude mod 30','longitude, zodiac, speed, metadata','astronomy.py','Astronomy / zodiac','embedded positions in degrees pane','march_1993_positions','test_book_ephemeris_fixtures'),
('UC02-ASP',2,'15–16','18–19','Aspect series diagrams','explicit book rule','pair, time range, orb','Search 0, ±30, ±60, ±90, ±120, ±150, 180 with bounded roots','entry/exact/exit, signed phase, branch, direction','events.py','Astronomy / Events','precomputed exact event drawings','conjunction_1993','test_new_aspects_both_branches; test_multiple_recrossings_tangent_and_band_grouping'),
('UC03-REPEAT',3,'17–37','20–40','Charts 2A–9B','explicit book rule','all aspect events; asset preset; completed ranges','Expose source/target ranges and all preselected shifted candidates, including misses','range boxes and comparison rows','methods.py','Aspect families / Price','astronomical dates displayed; range selection local','asset_pairs','test_comparison_causal_availability_and_missing_denominator'),
('UC03-SEQUENCE',3,'18–22, 29','21–25, 32','Charts 2B–2F, 3A–3D, 6A','discretionary interpretation','2–4 manually selected dated events','User assigns sequence and its first event; no unique automatic segmentation in prose','saved 1–2 / 1–2–3 / 1–2–3–4 annotation','methods.py; app.py','Aspect families','manual local annotation; no automated Pine signal','sequence_examples','test_manual_sequences'),
('UC03-HISTORY',3,'28, 38','31, 41','Chart 5E; previous-price-area sketch','discretionary interpretation','history; previous family-date count; manual dates','Review prior occurrences and dated wheel ranges; user controls history depth','dated ranges and manual annotations','methods.py; plotting.py','Aspect families / Clock','local historical-range workflow','previous_price_areas','test_local_workflow_chart_wheel_config_export'),
('UC04-WHEEL',4,'41–49','44–52','Figures 1–9','implementation formalization of a diagram','integers 1–360; quoted price ranges; unit u','15 rings of 24; (n-1)//24; labels centered, continuous phase x mod 24 separate','time rings, price rings, wrap-safe arcs','geometry.py; plotting.py','Universal Clock','wheel local; phase pane embedded','wheel_ranges','test_rounding_labels_wrap_and_units; test_intervals_and_static_bands'),
('UC04-SCALE',4,'43–50, 57','46–53, 60','Figures 5–7, 13','implementation formalization of a diagram','quote units, u>0, locked scale','x=P/u; price cycle 24u; historical scales explicitly chosen','scale configuration and alternatives','geometry.py; methods.py','Sidebar / methods','adjustable price scale; no optimization','scale_examples','test_book_arithmetic; test_rounding_labels_wrap_and_units'),
('UC04-SHIFT',4,'48–56','51–59','Figures 9–12','implementation formalization of a diagram','source and target intervals; fixed shifts','Ordinary overlap separately from modulo-24 overlap; half-cycle=12u','shifted ranges, opposite arcs','geometry.py; methods.py','Aspect families / Clock','opposite price trajectories; range overlap local','sp_trines','test_intervals_and_static_bands; test_book_family_ranges'),
('UC04-FAMILY',4,'52–62','55–65','Figures 10–15; Dow trine table','explicit book rule','same aspect family; last three dates; chosen price cycle','Review last three family dates, same and half-cycle shifts without best-fit selection','complete candidate table and wheel comparisons','methods.py','Aspect families','embedded family labels; historical comparison local','dow_trines','test_book_family_ranges'),
('UC05-ROUND',5,'64–68','67–71','Figures 17–19','explicit book rule','full longitude including minutes','Nearest degree; half-up tie is implementation choice; preserve raw astronomy','rounded degrees and monthly reproduction','geometry.py; workspace.py','Sidebar / Astronomy','same half-up transform; monthly mode rejected explicitly','saturn_1992','test_book_arithmetic; test_book_ephemeris_fixtures'),
('UC05-CHANNEL',5,'66–83','69–86','Charts 11A–14C; Figures 18–22','implementation formalization of a diagram','unwrapped longitude; u; fixed integer branch k','P=u(L+24k); O=u(L+12+24k); branch identity fixed through time','planet and midpoint levels, future trajectories','geometry.py; workspace.py','Price / Clock','embedded ephemeris, global plots, finite future curves','channel_examples','test_book_arithmetic; test_adaptive_ephemeris_wrap_station_independent_parity'),
('UC05-MULTI',5,'79–86','82–89','Figures 22–23; Charts 13B–15B','discretionary interpretation','multiple bodies; projected levels; explicit tick tolerance','List nearby levels; 98,194,290 share phase 2; no probability inferred','confluence rows and coincident markers','methods.py; plotting.py','Price candidates / Clock','multiple embedded planet trajectories','clock_phase_cluster','test_book_arithmetic; test_local_workflow_chart_wheel_config_export'),
('UC05-CONTACT',5,'71–77, 84','74–80, 87','Charts 11C–12C, 15A','discretionary interpretation','completed bars; field; tolerance; confirmation','Full-range or close touch; intrabar crossing; close beyond; reversal; explicit causal state','contact table with ticks and wheel-unit distances','methods.py','Price & replay / Methods','confirmed OHLC contact alert; advanced annotations local','dow_30_point_example','test_gap_is_not_intrabar_crossing_and_second_test_separation'),
('UC06-DIV',6,'87–107','90–110','Figures 24–25A; Charts 16A–20D','implementation formalization of a diagram','u, configured price range','A=u[24k,24k+1]; B/C/D offsets 6/12/18; closed edges','static bands','geometry.py','Price / Clock','static A–D bands for selected cycle','static_examples','test_intervals_and_static_bands'),
('UC06-HALF',6,'90–93','93–96','Chart 16D dotted divisions','implementation formalization of a diagram','adjacent one-unit bands','Midpoint of intervening open gap: offsets 3.5,9.5,15.5,21.5','halfway divisions','geometry.py','Price / Methods','static halfway divisions','pound_halfway','test_intervals_and_static_bands'),
('UC06-AREA',6,'90–107','93–110','Charts 16D–20D shaded areas','implementation formalization of a diagram','static bands; gap midpoints','Below band to preceding midpoint = support area; above band to next midpoint = resistance area','source-derived adjoining areas','geometry.py','Price / Methods','local shaded areas; Pine static reference levels','pound_halfway','test_intervals_and_static_bands'),
('UC06-TEST',6,'92–95','95–98','Charts 16E–16H; four sketches p93','discretionary interpretation','tolerance; separation; congestion; confirmation bars','Per-level causal state: tests, consecutive contacts, confirmed closes, isolated break/reversal, candle-range gap','tagged completed-bar observations and manual notes','methods.py','Price & replay / Methods','basic confirmed contacts; state-machine analysis local','second_test_gap','test_gap_is_not_intrabar_crossing_and_second_test_separation'),
('UC07-BAND',7,'108–114','111–117','Figures 26–26A; Charts 21A–22B','explicit book rule','continuous geocentric longitude; UTC interval','Closed [24k,24k+1] longitude occupancy, independent of rounding','entry/exit, duration, direction, clipped intervals','events.py','Events / calendar','precomputed band boundaries','book_band_sequence','test_multiple_recrossings_tangent_and_band_grouping'),
('UC07-COMB',7,'114–121','117–124','Charts 23A–24E; Figure 26B','discretionary interpretation','occupancy intervals for slow and fast bodies','Sweep interval endpoints; show full simultaneous body set once per contiguous interval','grouped combinations; component rules, no score','events.py','Events / monthly calendar','precomputed interval boundaries','october_1987','test_simultaneous_intervals_not_pairs_or_days; test_book_timing_fixtures'),
('UC07-MATCH',7,'119–121','122–124','Figure 27','implementation formalization of a diagram','Mars/Saturn longitude difference; clock orb','Solve difference = 24k anywhere on wheel; optional sector interpretation distinct from exact phase','clock coincidences and windows','events.py','Events / Clock','precomputed exact alignment events','october_1987','test_multiple_recrossings_tangent_and_band_grouping; test_book_timing_fixtures'),
('UC07-CALENDAR',7,'125','128','December 1993 planetary table','explicit book rule','monthly event/occupancy set; display timezone','One column per planet; retain interval entries/exits and simultaneous bodies','monthly matrix and event timeline','plotting.py','Events & calendar','precomputed drawings; matrix local','december_1993','test_book_timing_fixtures; test_local_workflow_chart_wheel_config_export'),
('UC08-REPLAY',8,'126–137','129–140','Charts 25A–25B; Figures 28–34','discretionary interpretation','daily UTC replay; observed ranges; all bodies; notes','Synchronize chart/wheel/date; list all levels; show stations, ingresses, visits, alignments; annotate handoffs manually','daily candidates and saved observations','workspace.py; plotting.py; app.py','Price & replay / Clock','embedded astronomy and channels; daily interpretation local','sugar_daily','test_local_workflow_chart_wheel_config_export; test_streamlit_default_astronomy_only'),
('UC08-OPPOSITE',8,'129–137','132–140','Figures 29–33; Chart 25B','implementation formalization of a diagram','planet longitude; scale; integer branch','Opposite clock level = u(L+12+24k), not an astronomical opposition event','opposite / midpoint ladder','geometry.py','Price & replay / Clock','embedded trajectory transform','sugar_jupiter','test_book_arithmetic'),
('EXT-SMOOTH',None,'not in Book I','not applicable','none','extension','unrounded longitude','Continuous channels instead of rounded book degrees','smooth trajectories','geometry.py','Sidebar','supported','interpolation','test_adaptive_ephemeris_wrap_station_independent_parity'),
('EXT-MOON',None,'79 boundary','82','Book I excludes lunar methods','extension','Moon selection','Use provider/interface for Moon; no claim of Book I lunar method','optional positions/events','astronomy.py','Sidebar','embedded when requested','moon_boundary','test_supported_bodies_dates'),
('EXT-ANCHOR',None,'not in Book I','not applicable','none','extension','P0,L0,u','P0+u(L-L0+24k)','anchored channels','geometry.py','Methods','fixed exported anchors','anchor','test_anchor_transform'),
]
registry=[]
for id,ch,printed,pdf,figure,classification,inputs,procedure,outputs,module,ui,pine,fixture,tests in rows:
 registry.append(dict(id=id,chapter=ch,printed_pages=printed,pdf_pages=pdf,source_figure=figure,classification=classification,inputs=inputs,
                      formula_or_procedure=procedure,outputs=outputs,units='UTC instants; degrees; quoted price units; wheel units',rounding='Full astronomy; optional half-up book rounding only at transform',
                      assumptions='See docs/assumptions.md; scale and session policy explicit; no forecast validation',example_fixture=fixture,
                      implementation_module='astrocalc.universal.'+module,ui_location=ui,pine_support=pine,tests=tests,
                      completion_status='implemented; discretionary selection remains manual' if classification=='discretionary interpretation' else 'implemented'))
(ROOT/'src/astrocalc/universal/method-registry.json').write_text(json.dumps(registry,indent=2)+'\n')
fixtures=dict(
 source=dict(title='Universal Clock, Book I',author='Jeanne Long',year=1993,pdf_pages=142,page_offset=3,provenance='User-provided scans; selected numeric transcription; source charts are not complete OHLC data'),
 saturn_1992=dict(printed=68,pdf=71,figure='Figure 19 / Saturn monthly table',time='00:00 UTC on first day; ephemeris convention',values=[['1992-01-01',305+51/60,306],['1992-02-01',309+29/60,309],['1992-03-01',312+51/60,313],['1992-04-01',315+55/60,316],['1992-05-01',317+52/60,318],['1992-06-01',318+28/60,318],['1992-07-01',317+37/60,318],['1992-08-01',315+36/60,316]],tolerance_degrees=.04),
 march_1993_positions=dict(printed=128,pdf=131,date='1993-03-22',time='00:00 UTC',values={'Sun':1+22/60,'Mercury':340+18/60,'Venus':17+43/60,'Mars':104+53/60,'Jupiter':190+53/60,'Saturn':325+35/60,'Uranus':291+40/60,'Neptune':290+52/60,'Pluto':235+22/60},tolerance_degrees=.04,ambiguity='Neptune sign-degree line is faint: appears 21 in low-resolution scan, while rounded column 291 and ephemeris support 20°52′. Preserve this ambiguity.'),
 conjunction_1993=dict(printed=[4,12],pdf=[7,15],superior_date='1993-01-23',superior_gmt='15:43',inferior_book_date='1993-03-08',note='Inferior event is March 9 UTC and March 8 in New York; do not force UTC date to match book label'),
 book_band_sequence=dict(printed=109,pdf=112,bands=[[x,x+1] for x in range(0,360,24)],legacy_difference='Legacy special list remains unchanged'),
 pound_halfway=dict(printed=[90,91],pdf=[93,94],figure='Chart 16D',bands=[[1.62,1.63],[1.68,1.69]],halfway=1.655,support=[1.655,1.68],resistance=[1.63,1.655],classification='midpoint of gap formalization of diagram; dotted values not numerically printed'),
 static_examples=dict(pound=[[1.44,1.45],[1.68,1.69],[1.92,1.93]],dow=[[3360,3370]],oil=[[19.2,19.3],[21.6,21.7]],printed=[91,100,103],pdf=[94,103,106]),
 sugar_jupiter=dict(printed=[128,131,133],pdf=[131,134,136],longitude=191,unit=.1,level=11.9,opposite=13.1),
 clock_phase_cluster=dict(printed=85,pdf=88,rounded_longitudes=[98,194,290],phase=2),
 wheel_ranges=dict(printed=[47,48],pdf=[50,51],soybean_overlap=[[539,554],[544,549]],soybean_shifted=[[599,609],[557,565]],note='Figure 8 rounded range differs from earlier Chapter 1 prose 540–553'),
 sp_trines=dict(printed=[54,56],pdf=[57,59],ranges=[['1990-12-05',332.5,338],['1991-03-24',370,374.5],['1991-03-24',379,382.5],['1992-01-05',418,422]],shift=36,note='Different futures contracts on consecutive examples: June 1991 vs March 1992; do not merge into continuous prices'),
 dow_trines=dict(printed=61,pdf=64,ranges=[['1987-08-23',2678,2730],['1987-12-12',1838,1889],['1988-09-28',2070,2096],['1989-01-16',2215,2236],['1989-11-03',2612,2650],['1990-02-19',2579,2619],['1990-12-05',2558,2615],['1991-03-24',2837,2897],['1992-01-05',3166,3230],['1992-04-24',3305,3381],['1993-02-03',3325,3400]],note='Book event-date labels, including weekends; nearest actual session is not specified for every row. Price figures printed in units of one, wheel price labels round to nearest 10 with exact 5-point ties downward (2678→2680; 2215→2210).'),
 october_1987=dict(printed=[118,119,120,121],pdf=[121,122,123,124],claims=[dict(body='Uranus',start='1987-01-01',end='1987-12-31',type='near 24-line; qualitative'),dict(body='Jupiter',start='1987-10-09',end='1987-10-23',type='24-line'),dict(body='Venus',date='1987-10-15',type='24-line arrival'),dict(body='Mars/Saturn',date='1987-10-16',type='same wheel segment')],note='Compare calculated continuous bands and rounded clock sectors; source labels are dates and rounded occupancy interpretations, not exact UTC boundaries'),
 december_1993=dict(printed=125,pdf=128,figure='Table for planets on 24-lines',bands=[['Venus',2,4],['Uranus',1,2],['Mercury',7,9],['Mars',11,14],['Jupiter',9,15],['Sun',14,17],['Neptune',1,19],['Mercury',22,24],['Venus',22,24]],note='Hand-drawn arrow endpoints approximate ±1–2 days; circles mark combinations, not extra daily events; asterisks indicate Mars/Saturn matches'),
 sugar_daily=dict(printed=[127,130,131,134],pdf=[130,133,134,137],ranges=[['1993-03-17',11.4,11.75],['1993-03-18',12.,12.7],['1993-03-22',12.3,13.],['1993-03-23',12.15,12.4],['1993-03-24',11.85,12.15],['1993-03-25',11.75,12.25],['1993-04-19',11.2,11.7]],observations=[['1993-03-22','Mercury turns direct; Jupiter opposite and Uranus/Neptune candidate areas'],['1993-03-24','Jupiter contacted; prose says price remains near it through March 26'],['1993-03-29','Uranus/Neptune region mentioned'],['1993-04-05','Mercury near 17° Pisces; Jupiter and its opposite remain candidates'],['1993-04-08','Mars/Saturn clock alignment; Jupiter/opposite candidates'],['1993-04-15','Mercury/Sun near the 24-line'],['1993-04-19','Mars passes the Jupiter clock phase; prose describes the opposite side of its wheel position']],note='Selected LOW/HIGH only. No open, close or volume transcribed; no invented full history.'),
 channel_examples=[dict(asset=a,bodies=b,printed=p,pdf=p+3,figure=f) for a,b,p,f in [('Dow',['Saturn'],68,'Charts 11A–11D'),('British pound',['Saturn'],75,'Charts 12A–12C'),('Deutsche Mark',['Neptune'],79,'Chart 13A'),('Silver',['Saturn','Uranus','Neptune'],79,'Chart 13B'),('Crude oil',['Saturn','Jupiter'],82,'Chart 14A'),('Sugar',['Pluto'],83,'Charts 14B–14C')]],
 dow_30_point_example=dict(printed=71,pdf=74,threshold_points=30,interpretation='Example-specific close beyond Saturn line, not universal contact tolerance'),
 asset_pairs=dict(printed='17–37',pdf='20–40',note='Editable historical pair presets in methods.PRESETS'),
 sequence_examples=dict(printed='18–22,29',pdf='21–25,32',note='Manual choice after viewing 6–7 dates; no causal unique segmentation supplied'),
 previous_price_areas=dict(printed=38,pdf=41,note='Manual historical comparison sketch; no numeric fixture invented'),
 second_test_gap=dict(printed=93,pdf=96,note='Chart 16E: Dec 5 second test, Dec 6 gap; Feb 7 second test, Feb 11 gap. Full OHLC absent; synthetic causal state-machine tests separate.'),
 scale_examples=dict(printed=50,pdf=53,cycles=[6,12,24,240],note='Historical choices depend on market quotes, not modern-market defaults'),
 weekend_window=dict(printed=9,pdf=12,note='Saturday: inspect Friday; Sunday: inspect Monday. Either surrounding session may overlap. Strict and expanded results separate.'),
 interpolation=dict(classification='extension',note='Measured against local provider at independent points, not book validation'),
 moon_boundary=dict(printed=79,pdf=82,note='Lunar techniques excluded from Book I'),anchor=dict(classification='extension',formula='P0+u(L-L0+24k)'))
fixtures['sp_trines_june_1991']=dict(fixtures['sp_trines'],ranges=fixtures['sp_trines']['ranges'][:2])
fixtures['sp_trines_march_1992']=dict(fixtures['sp_trines'],ranges=fixtures['sp_trines']['ranges'][2:])
(ROOT/'src/astrocalc/universal/book-fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n')
(ROOT/'docs/book-fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n')
header='''# Book methods and capability registry

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
'''
lines=[header]
for r in registry:lines.append(f"| {r['id']} | {r['chapter'] or 'extension'}; {r['printed_pages']} / {r['pdf_pages']} | {r['classification']} | {r['formula_or_procedure']} — {r['ui_location']} | {r['pine_support']} |\n")
lines.append('''
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
''')
(ROOT/'docs/book-methods.md').write_text(''.join(lines))
