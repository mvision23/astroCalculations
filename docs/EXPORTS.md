# Export schemas (version 1)

CSV is UTF-8, comma-delimited, with a header row and standard Python CSV quoting.
Numbers are numeric fields, booleans are `True`/`False`, and timestamps use ISO 8601
with an offset. The UI/text uses Yes/No for booleans. No display strings combine
sign and degree. Grouped reports use ordinary rows with grouping columns.

Every CSV starts with these query/settings columns, in this order:

```text
workflow,period,query_year,query_month,query_date,query_body,query_other,query_sign,query_degree,range_start_utc,range_end_exclusive_utc,display_timezone,sampling,notes,coordinates,result_count
```

`query_*` fields irrelevant to a workflow are empty. `query_year` is the supplied
year (for positions, always the selected date's year). The range end is exclusive. `result_count` is the number
of exported rows. Metadata repeats on each row; empty CSV exports consist solely
of the schema header. Use text if metadata is needed for an empty result.

Text exports include title, inputs, UTC range, timezone, sampling, approximation
notes, coordinate convention, row count, and aligned plain-text columns.

## Workflow data columns

Each list below follows the common metadata columns. The schemas are also
available as `Result.headers`. `timestamp` is the sample/new-moon instant;
`derived_timestamp` is the estimated lunar-offset instant. Each expands to
separate `_utc` and `_local` columns. All angular values are degrees.

### new_moons — New moons and degree offsets

```text
timestamp_utc,timestamp_local,longitude,sign,degree,offset_degrees,derived_timestamp_utc,derived_timestamp_local,derived_longitude,derived_sign,derived_degree
```

### moon_degree — Moon at a zodiac degree

```text
timestamp_utc,timestamp_local,body,longitude,sign,degree
```

### annual_aspects — Aspects between two bodies

```text
timestamp_utc,timestamp_local,body,other,aspect,aspect_angle,separation,orb,deviation,longitude,sign,degree,other_longitude,other_sign,other_degree
```

### special — Special longitudes

```text
timestamp_utc,timestamp_local,body,longitude,sign,degree,target_longitude,distance
```

### monthly_body — Monthly aspects for one body

```text
timestamp_utc,timestamp_local,body,other,aspect,aspect_angle,separation,orb,deviation,longitude,sign,degree,other_longitude,other_sign,other_degree
```

### repeating — Repeating aspects (matching sample dates)

```text
group_sample_count,timestamp_utc,timestamp_local,body,other,aspect,aspect_angle,separation,orb,deviation,longitude,sign,degree,other_longitude,other_sign,other_degree
```

### repeating_dates — Repeating aspects grouped by date

```text
date_match_count,timestamp_utc,timestamp_local,body,other,aspect,aspect_angle,separation,orb,deviation,longitude,sign,degree,other_longitude,other_sign,other_degree
```

### multiple_dates — Dates with two or more aspects

```text
date_match_count,timestamp_utc,timestamp_local,body,other,aspect,aspect_angle,separation,orb,deviation,longitude,sign,degree,other_longitude,other_sign,other_degree
```

### positions — Planetary positions

```text
timestamp_utc,timestamp_local,body,longitude,sign,degree,retrograde
```

### zero — Bodies near 0 degrees of a sign

```text
month,timestamp_utc,timestamp_local,body,longitude,sign,degree,retrograde
```

### alignments — Planetary alignments (degree modulo 24)

```text
group,member_count,timestamp_utc,timestamp_local,body,longitude,sign,degree,retrograde
```

### monthly_all — All monthly aspects

```text
timestamp_utc,timestamp_local,body,other,aspect,aspect_angle,separation,orb,deviation,longitude,sign,degree,other_longitude,other_sign,other_degree
```

## Grouping and angle fields

- `group_sample_count`: number of matching daily samples for the counterpart/aspect group.
- `date_match_count`: matches on this UTC sample date.
- `month`: UTC sample month (1–12), for the near-zero report.
- `group`: modulo-24 alignment group; group together with `timestamp_utc`.
- `member_count`: number of bodies in that alignment group, repeated per member.
- `aspect_angle`: nominal aspect angle; `separation`: measured shorter circular separation.
- `deviation`: absolute difference from nominal angle; `orb`: effective allowed difference.
- `target_longitude` / `distance`: matched special target and circular separation.
- `longitude`, `sign`, `degree`: full longitude, zodiac sign, degree within sign.
- `other_*` / `derived_*`: equivalent position fields for the counterpart/estimated date.

## Example (data columns only)

A complete export includes the common settings columns before these fields:

```csv
timestamp_utc,timestamp_local,body,longitude,sign,degree,retrograde
2026-01-01T00:00:00+00:00,2025-12-31T18:00:00-06:00,Sun,280.20970560870967,Capricorn,10.209705608709669,False
```

Exports follow the current table sort even when exporting all rows from a
filtered view. An empty filter match still exports a valid header-only CSV or
a text report stating `No matching results.`.
