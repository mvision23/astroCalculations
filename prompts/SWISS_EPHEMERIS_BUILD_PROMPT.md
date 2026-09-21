# Build prompt: optional Swiss Ephemeris provider for Universal Clock

Extend the existing AstroCalc repository with a Swiss Ephemeris provider for the
Universal Clock engine. Keep the original 12-workflow terminal calculations as a
PyEphem compatibility mode. Implement, test, and document the extension.

The objective is reproducible astronomical calculations with explicit coordinate
conventions, time scales, and ephemeris provenance. Results intended for comparison
with Astro.com must state precisely what was compared and which settings were used.
A library change alone must not be presented as proof that results match Astro.com.

## Inspect the current checkout first

Read repository instructions, `CLI_BUILD_PROMPT.md`,
`UNIVERSAL_CLOCK_BUILD_PROMPT.md`, and the current implementation before editing.
Preserve existing user changes, including untracked Universal Clock code and tests.
Do not reset the repository or replace working features with a new application.
This is an additive task; where this prompt conflicts with an earlier requirement
to use only PyEphem, the optional Swiss provider described here is the extension.

Current integration points include:

- `src/astrocalc/calculations.py`: original sampled CLI workflows.
- `src/astrocalc/universal/astronomy.py`: `Provider`, `Position`, `EphemProvider`,
  coordinate modes, and position-series construction.
- `src/astrocalc/universal/events.py`: provider-based event refinement.
- `src/astrocalc/universal/workspace.py`: persisted settings and provider selection.
- Universal Clock UI, CLI, export, plotting, and Pine-generation modules.
- `pyproject.toml` and the existing regression tests.

Verify the current files and interfaces rather than assuming they still match
these descriptions. Establish baseline tests before making changes.

## Scope and compatibility

1. Preserve all 12 CLI workflows, their PyEphem numerical conventions, sampling,
   orbs, approximations, exports, and regression expectations. Keep `astrocalc`
   and the compatibility script entry point working without Swiss Ephemeris.
2. Keep PyEphem as the default for existing Universal Clock workspaces and for
   new workspaces unless the user explicitly chooses Swiss Ephemeris.
3. Add Swiss Ephemeris through the provider interface. Keep astronomy-library
   calls out of event algorithms, UI rendering, market-data logic, and exporters.
4. Support Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune,
   and Pluto, with the application's existing 1900–2100 support limits.
5. Preserve existing price mapping, special-longitude targets, modulo-24 rules,
   rounding/occupancy modes, event definitions, and market-session behavior.
6. Do not add houses, sidereal zodiacs, topocentric charts, asteroids, or a wider
   historical date range in this task. They require separate settings and tests.

Keep the distinction between the two existing calculation paths visible:

- The CLI reports sampled matches and preserves original J2000 calculations.
- Universal Clock refines events using its selected provider. Numerical solver
  tolerance does not establish the physical accuracy of the ephemeris.

## Provider implementation and installation

Implement a `SwissEphemerisProvider` (or comparably clear name) that supplies the
existing `longitude`, `speed`, `position`, and `metadata` capabilities. Reuse the
shared structured result types. Use a maintained Python binding to the Swiss
Ephemeris C library, such as `pyswisseph`, after verifying its installed APIs,
return shapes, flag constants, version information, and licensing.

Add an optional installation extra, for example `.[swiss]`. Keep the base CLI and
PyEphem Universal Clock usable when the binding is absent. Import the optional
binding only where required; choosing an unavailable provider must show an
installation instruction, not crash application startup. Declare and test a
supported version range rather than relying on an unspecified global install.

Use a single provider factory/configuration path for UI, CLI, workspace loading,
comparison tooling, and Pine generation. Provider configuration must be immutable
for a calculation. Do not let injected providers disagree silently with persisted
settings or reported provenance.

Use library-supplied longitude speed for Swiss positions. Preserve units: degrees,
degrees per day, and Earth distance in AU. Validate returned values as finite,
normalize longitude consistently, and retain the existing direct/retrograde/
stationary interpretation with a documented threshold. Do not alter the PyEphem
speed calculation as an incidental part of this work.

## Explicit coordinate profiles

Separate the provider choice from the coordinate profile. Maintain the existing
PyEphem profile behavior and saved identifiers. Provide a documented profile
matrix with effective Swiss flags, not just friendly names.

At minimum support these Swiss profiles:

| Profile | Intended convention |
| --- | --- |
| `apparent_of_date` | Geocentric, tropical, apparent ecliptic longitude and latitude, true equinox/ecliptic of date |
| `astrometric_of_date` | Geocentric astrometric coordinates, mean equinox/ecliptic of date |
| `astrometric_j2000` | Geocentric astrometric coordinates, mean equinox/ecliptic J2000 |

Verify the exact flag combinations against the installed library and official
manual. In particular, verify the roles of `SPEED`, `NONUT`, `NOABERR`, `NOGDEFL`,
and `J2000`; retain light-time in astrometric profiles. Do not confuse geometric
true position with the true equinox of date. Do not request equatorial coordinates
and interpret them as ecliptic longitude.

Reserve the existing `legacy_j2000` compatibility identifier for the original
PyEphem behavior. The Swiss J2000 profile is a comparison convention, not a promise
of identical legacy numbers. Handle provider/profile incompatibilities explicitly
instead of silently renaming or reinterpreting saved choices.

Do not assume the existing PyEphem `apparent_of_date` transformation is numerically
identical to Swiss's apparent profile. Check mean versus true obliquity, nutation,
light-time, aberration, and gravitational-deflection conventions when investigating
differences. Document existing differences without silently changing PyEphem results.

Reference: [Swiss coordinate and speed flags, programming manual sections 3.3–3.4](https://www.astro.com/swisseph/swephprg.htm).

## Time scales and calendar boundaries

Keep timezone-aware UTC datetimes at application boundaries and existing IANA-zone
and fixed-offset display handling. Display timezone changes must not change the
calculated instant, search interval, or cache identity for an equivalent instant.

Use the binding's documented UTC conversion to obtain Julian dates in TT and UT1.
Choose and document a consistent calculation route: TT to the TT calculation API,
or UT1 to the UT API. Never pass a TT Julian date to the UT API, add delta-T twice,
or describe plain UTC calendar conversion as an exact UT1 conversion.

Record the effective conversion route, delta-T model/version information available
from the library, and any external leap-second or delta-T data. Do not hard-code a
present-day UTC/TT offset for every date. Document library behavior for pre-1972
UTC inputs and future leap-second uncertainty within the supported interval.
Python datetime cannot encode a leap second; reject unsupported explicit leap-
second input clearly rather than silently shifting it.

Preserve UTC interval boundaries and existing solver boundary behavior. Validate
selected instants, interpolation look-ahead, derivative look-behind, and future
horizons against the supported range. Keep numerical tolerance separate from time-
scale uncertainty and underlying positional accuracy.

Reference: [Swiss UTC, TT, UT1, and delta-T APIs, sections 9–10](https://www.astro.com/swisseph/swephprg.htm).

## Ephemeris files and backend verification

The initial Swiss integration must support these explicit data-source choices:

- **Swiss data files**: the normal Swiss-provider choice; requires a configured
  local directory and appropriate files covering the requested bodies and dates.
- **Moshier**: an explicitly selected alternative, clearly labelled in every
  result. It must not be described as a Swiss-data/JPL-data calculation.

Direct JPL-file support is optional for this iteration. If exposed, it must have
its own file configuration, validation, provenance, and backend tests. Do not show
a selectable configuration that is only partially implemented.

Use a documented path precedence, such as workspace/CLI configuration before an
application environment variable. Validate directories and required coverage.
Calculations must work offline once data are installed. Provide verified official
download/setup instructions and a small verification command. Do not bundle large
or unreviewed data files or download them silently during a calculation.

Swiss Ephemeris can return a fallback engine when requested files are unavailable.
Inspect the returned backend bits on **every calculation call**, including internal
solver calls. A directory-exists check or a single startup probe is insufficient.
Also verify required coordinate/speed flags and handle binding exceptions, library
errors, and warnings through a clear provider error model.

For this iteration, use a strict policy: if the effective engine differs from the
requested engine, fail the calculation with the requested engine, actual engine,
affected body/date, and actionable data-setup guidance. Let the user explicitly
select Moshier and rerun. Never substitute PyEphem or accept an unlabelled mixture
of engines within one result.

A failed, cancelled, or fallback-rejected run must preserve the previous completed
result and must not produce an apparently successful partial export.

Reference: [Swiss ephemeris selection and returned flags, sections 3.3.2 and 3.5](https://www.astro.com/swisseph/swephprg.htm).

## Reproducibility, state, and caches

Record requested and effective configuration with each completed research result:

- Provider, binding version, C-library version, and application version.
- Coordinate profile, effective correction choices, origin, reference epoch,
  zodiac convention, and angular/speed units.
- Requested engine, effective engine, requested flags, and observed returned flags.
- Identity of the ephemeris files actually used, their coverage and content hashes;
  record additional time-correction files when used. Do not claim unrelated files
  in a configured directory were used by the calculation.
- UTC query interval, time-scale conversion route, solver tolerance, and relevant
  warnings or documented accuracy limitations.

Use a stable configuration/data fingerprint for caches. Different providers,
profiles, file contents, data sources, and library versions must not share cached
positions, events, or generated Pine tables. Avoid rehashing large files inside
every solver evaluation; establish a manifest once per configuration/run and
handle detected changes explicitly.

Investigate the binding's global or thread-local mutable state. Protect the full
configuration-and-calculation sequence with a suitable shared lock or process
isolation if necessary. Setting a global path once per provider instance is not
sufficient when sessions can use different configurations. Include a test that
alternates two configurations without state leakage.

## UI, CLI, saved workspaces, and exports

Add provider, coordinate-profile, ephemeris-path, and explicit data-source controls
to Universal Clock. Keep ordinary controls understandable; place diagnostic flags
and file manifests in an expandable details view or diagnostic command.

The UI must distinguish these outcomes in plain text:

- PyEphem compatibility/current mode.
- Swiss provider with verified Swiss files.
- Swiss provider using explicitly selected Moshier.
- Provider unavailable, data missing, or backend mismatch: calculation not completed.

Show settings validation before long calculations and retain responsive background
execution and cancellation. Changing controls must not relabel an old result with
new settings; calculate a new result before replacing its metadata.

Expose equivalent CLI options and a validation/comparison command. Update help and
provide runnable examples. Persist provider configuration in workspaces, with a
versioned migration from existing settings: workspaces without provider fields
must retain their old PyEphem behavior. Reject unknown profiles/providers clearly.

Carry the result's effective astronomy metadata through existing CSV/JSON/text
exports and relevant plot/Pine outputs. Where a flat format cannot naturally hold
a manifest, use documented metadata columns or a linked sidecar with a matching
result identifier. Empty exports must remain meaningful. Preserve existing
filename/overwrite/error handling.

Pine generation must use the selected provider, identify the generated table's
provider/profile/data fingerprint, and distinguish interpolation error from backend
accuracy. Do not make Pine calculate with Swiss Ephemeris or access the network.

## Comparison harness and reference evidence

Build a reproducible comparison command and checked-in compact reference fixtures.
It must support:

1. **Matched conventions**: compare PyEphem and Swiss at the same instants and
   compatible coordinate settings to investigate model differences.
2. **User-visible defaults**: separately demonstrate CLI J2000 versus Universal
   Clock/Swiss apparent-of-date behavior, labelled as a convention comparison.

Report wrapped signed longitude differences in degrees and arcseconds, latitude
and distance differences where available, speed differences, and event-time
residuals. Include complete configuration and reference provenance. An angle
crossing 0/360 must not appear as an approximately 360-degree error.

Cover all ten bodies and representative dates across 1900–2100. Include a lunar
crossing, an ingress, an aspect, a retrograde station, leap day, and year-end.
For event comparisons, require matching definitions and branches before comparing
timestamps. Refine with the same search settings when comparing providers; do not
compare a daily sampled match with a refined event and call the difference an
engine error.

For Astro.com-facing validation, obtain reference values from a documented Swiss
`swetest` execution or a suitable official Astro.com test output. Record the exact
command/URL, access date, library version if known, data files/engine, coordinate
flags, input calendar/time scale, output precision, and expected values. Distinguish
local C-tool validation from a comparison with the hosted Astro.com service. A
binding calling the same library twice is not an independent reference fixture.
Do not claim all Astro.com chart products share one configuration.

Define justified acceptance tolerances before judging residuals. Separate agreement
with an identically configured Swiss reference from agreement between different
astronomical models. Respect reference rounding; do not infer sub-arcsecond agreement
from a whole-arcminute display. Investigate unexplained discrepancies instead of
loosening tolerances until tests pass. Report unavailable reference evidence
honestly; fabricated or self-labelled reference data are unacceptable.

## Required tests

Run existing tests and add focused coverage for:

- Unchanged CLI and PyEphem regression results and old-workspace migration.
- Base installation/import without the optional Swiss binding or data files.
- Swiss position, speed, distance, zodiac, and direction fields for every body.
- Each coordinate profile's effective flags, with no accidental sidereal,
  topocentric, heliocentric, or geometric-position setting.
- UTC/TT/UT1 conversion route, equivalent instants in different display zones,
  fixed offsets versus DST, leap day, December/January, and date-range limits.
- Missing/corrupt/out-of-coverage files, negative/error returns, and returned
  Moshier fallback when Swiss was requested; include fallback occurring after
  an initially successful sample and during a solver evaluation.
- Explicit Moshier selection with truthful metadata; mixed-engine rejection.
- Wrapped longitude residuals, stationary/retrograde transitions, ingress and
  aspect refinement, and cancellation/failure preserving a completed result.
- Provider/profile/file/version cache separation and mutable-state isolation.
- UI/CLI selection, saved configuration, result provenance, and export/Pine metadata.
- Real Swiss-file integration against recorded reference fixtures.

Use controlled stubs for error/flag edge cases and real-library integration tests
for numerical claims. Ordinary unit tests must not download data. Keep data-required
tests separately identifiable; report skipped integration tests explicitly. A
mock-only suite does not establish Swiss-data accuracy or Astro.com agreement.

## Documentation, licensing, and delivery

Add installation and data-file setup instructions, provider/profile examples,
workspace migration notes, the comparison report, and an explanation of known
residuals and numerical limitations. Document actual behavior and tested versions.

Review the library, Python binding, and data-distribution license terms from their
authoritative sources. Swiss Ephemeris offers AGPL and professional licensing;
document the applicable choices without silently relicensing the existing project
or representing optional installation as a licensing exemption. Commercial license
purchase and public deployment are outside this implementation task. Continue local
implementation and testing while recording any distribution decision still needed.

Deliver the implemented provider and integrations, tests, reference fixtures and
provenance, setup/verification tooling, and documentation. Run the relevant checks.
Report exactly which tests and real-data comparisons passed, any skipped checks,
and any remaining differences. Do not claim Astro.com parity merely because the
same library name appears in metadata.

Official references:

- [Swiss Ephemeris programming manual](https://www.astro.com/swisseph/swephprg.htm)
- [Swiss Ephemeris technical documentation and licensing](https://www.astro.com/swisseph/swisseph.htm)
- [Swiss Ephemeris distribution](https://www.astro.com/swisseph/)

Verify the binding's own documentation and the installed APIs during implementation.
