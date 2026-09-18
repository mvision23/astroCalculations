"""Original sampled workflows. No input, rendering, or file writes."""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import combinations
import math

import ephem

from .models import BODIES, SIGNS, MONTHLY, Query, Result, UTC

SPECIAL_LONGITUDES = (0, 1, 24, 25, 48, 49, 72, 73, 96, 97, 120, 121, 145, 146, 169, 170, 193, 194, 217, 218, 241, 242, 265, 266, 289, 290, 313, 314, 337, 338)
ASPECTS = ((0, 'Conjunction'), (60, 'Sextile'), (90, 'Square'), (120, 'Trine'), (180, 'Opposition'))
POSITION = ('body', 'longitude', 'sign', 'degree')
ASPECT_COLUMNS = ('timestamp', 'body', 'other', 'aspect', 'aspect_angle', 'separation', 'orb', 'deviation', 'longitude', 'sign', 'degree', 'other_longitude', 'other_sign', 'other_degree')


class Cancelled(Exception):
    """No partial Result is returned."""


class CalculationError(RuntimeError):
    """The search failed and must not be presented as an empty success."""


def ephem_date(instant):
    if instant.tzinfo is None:
        raise ValueError('A timezone-aware datetime is required')
    return ephem.Date(instant.astimezone(UTC).replace(tzinfo=None))


def longitude(body, instant):
    obj = getattr(ephem, body)()
    obj.compute(ephem_date(instant))
    return math.degrees(ephem.Ecliptic(obj).lon) % 360


def zodiac(lon):
    if not math.isfinite(lon):
        raise ValueError('Longitude must be finite')
    lon %= 360
    return SIGNS[int(lon // 30)], lon % 30


def circular_distance(a, b):
    return abs((a - b + 180) % 360 - 180)


def alignment_group(lon):
    return int((lon % 360 or 360) % 24) or 24


def position(body, instant, retro_hours=None):
    lon = longitude(body, instant)
    sign, degree = zodiac(lon)
    row = dict(body=body, longitude=lon, sign=sign, degree=degree)
    if retro_hours is not None:
        row['retrograde'] = body not in ('Sun', 'Moon') and (lon - longitude(body, instant - timedelta(hours=retro_hours))) % 360 > 180
    return row


def bounds(q):
    if q.workflow == 'positions':
        start = datetime(q.date.year, q.date.month, q.date.day, tzinfo=UTC)
        return start, start + timedelta(days=1)
    start = datetime(q.year, q.month if q.workflow in MONTHLY else 1, 1, tzinfo=UTC)
    end = (datetime(q.year, q.month + 1, 1, tzinfo=UTC) if q.workflow in MONTHLY and q.month < 12
           else datetime(q.year + 1, 1, 1, tzinfo=UTC))
    return start, end


def calculate(query: Query, *, cancel=lambda: False, progress=lambda fraction: None) -> Result:
    q = query.validate()
    start, end = bounds(q)
    rows = []
    current = start

    def check(instant):
        if cancel():
            raise Cancelled('Calculation cancelled; no partial result saved')
        progress(min(1.0, max(0.0, (instant - start) / (end - start))))

    try:
        if q.workflow == 'new_moons':
            columns = ('timestamp', 'longitude', 'sign', 'degree', 'offset_degrees', 'derived_timestamp', 'derived_longitude', 'derived_sign', 'derived_degree')
            sampling = 'PyEphem next_new_moon; offset / 13.1764 days'
            notes = 'Derived dates are estimates using constant average lunar motion, not exact angular crossings.'
            while current < end:
                check(current)
                instant = ephem.next_new_moon(ephem_date(current)).datetime().replace(tzinfo=UTC)
                if instant >= end:
                    break
                p = position('Moon', instant)
                derived = instant + timedelta(days=q.degree / 13.1764)
                d = position('Moon', derived)
                rows.append(dict(timestamp=instant, longitude=p['longitude'], sign=p['sign'], degree=p['degree'], offset_degrees=q.degree,
                                 derived_timestamp=derived, derived_longitude=d['longitude'], derived_sign=d['sign'], derived_degree=d['degree']))
                current = (instant + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif q.workflow == 'moon_degree':
            columns = ('timestamp',) + POSITION
            sampling = 'Hourly UTC samples from month start'
            notes = 'First hourly sample in the selected sign with int(degree) equal to the integer bucket; resolution 1 hour, not an exact crossing.'
            for hour in range(int((end - start).total_seconds() // 3600)):
                current = start + timedelta(hours=hour)
                check(current)
                p = position('Moon', current)
                if p['sign'] == q.sign and int(p['degree']) == q.degree:
                    rows.append(dict(timestamp=current, **p))
                    break
        elif q.workflow in {'positions', 'special', 'zero', 'alignments'}:
            columns = ('timestamp',) + POSITION
            step = 6 if q.workflow == 'zero' else 24
            sampling = f'Every {step} hours from 00:00 UTC'
            notes = ''
            if q.workflow == 'positions':
                columns += ('retrograde',)
                sampling = 'Selected date at 00:00 UTC; retrograde compared with 24 hours earlier'
            elif q.workflow == 'special':
                columns += ('target_longitude', 'distance')
                notes = 'Strict circular distance < 0.5 degrees. Corrects original linear comparison at 0/360. Targets: ' + ', '.join(map(str, SPECIAL_LONGITUDES))
            elif q.workflow == 'zero':
                columns = ('month',) + columns + ('retrograde',)
                notes = 'Sampled degree 0–0.5 inclusive; first match per body per UTC date, not guaranteed exact ingress. Retrograde compared with 6 hours earlier.'
            else:
                columns = ('group', 'member_count') + columns + ('retrograde',)
                notes = 'Daily groups with >=2 members: int(longitude % 24) or 24 after normalization (0 becomes 360). Remainders [0,1) map to 24; not contiguous sectors. Retrograde compared with 6 hours earlier.'
            seen = set()
            for hour in range(0, int((end-start).total_seconds() // 3600), step):
                current = start + timedelta(hours=hour)
                check(current)
                groups = defaultdict(list)
                for body in BODIES:
                    check(current)
                    retro = 24 if q.workflow == 'positions' else 6 if q.workflow in {'zero', 'alignments'} else None
                    p = position(body, current, retro)
                    row = dict(timestamp=current, **p)
                    if q.workflow == 'positions':
                        rows.append(row)
                    elif q.workflow == 'special':
                        for target in SPECIAL_LONGITUDES:
                            distance = circular_distance(p['longitude'], target)
                            if distance < 0.5:
                                rows.append(dict(**row, target_longitude=target, distance=distance))
                    elif q.workflow == 'zero':
                        key = (current.date(), body)
                        if p['degree'] <= 0.5 and key not in seen:
                            seen.add(key)
                            rows.append(dict(month=current.month, **row))
                    else:
                        row['longitude'] = row['longitude'] or 360
                        groups[alignment_group(p['longitude'])].append(row)
                for group, members in sorted(groups.items()):
                    if len(members) >= 2:
                        rows.extend(dict(group=group, member_count=len(members), **member) for member in members)
        else:
            columns = ASPECT_COLUMNS
            hour = 12 if q.workflow in {'annual_aspects', 'monthly_all'} else 0
            sampling = f'Daily samples at {hour:02}:00 UTC'
            orb = 0.3 if q.workflow == 'annual_aspects' else 1.0
            notes = f'Orb <= {orb} degrees. Counts are matching sample dates, not distinct astronomical events.'
            if q.workflow == 'monthly_all':
                notes = 'Pair orb = max(per-body values): Mercury/Mars 3.5, Sun 1, others 2.5 degrees. Counts are matching sample dates, not distinct events.'
            pairs = (list(combinations(BODIES, 2)) if q.workflow == 'monthly_all' else
                     [(q.body, q.other)] if q.workflow == 'annual_aspects' else
                     [(q.body, other) for other in BODIES if other != q.body])
            for day in range((end - start).days):
                current = start + timedelta(days=day, hours=hour)
                check(current)
                positions = {b: position(b, current) for b in dict.fromkeys(b for pair in pairs for b in pair)}
                for body, other in pairs:
                    p, o = positions[body], positions[other]
                    separation = circular_distance(p['longitude'], o['longitude'])
                    if q.workflow == 'monthly_all':
                        orb = max({'Mercury': 3.5, 'Mars': 3.5, 'Sun': 1}.get(b, 2.5) for b in (body, other))
                    for angle, name in ASPECTS:
                        if abs(separation - angle) <= orb:
                            rows.append(dict(timestamp=current, **p, other=other, aspect=name, aspect_angle=angle,
                                             separation=separation, orb=orb, deviation=abs(separation-angle),
                                             other_longitude=o['longitude'], other_sign=o['sign'], other_degree=o['degree']))
            if q.workflow == 'repeating':
                counts = Counter((r['other'], r['aspect']) for r in rows)
                rows = [dict(group_sample_count=counts[r['other'], r['aspect']], **r) for r in rows if counts[r['other'], r['aspect']] > 1]
                rows.sort(key=lambda r: (r['other'], r['aspect'], r['timestamp']))
                columns = ('group_sample_count',) + columns
            elif q.workflow in {'repeating_dates', 'multiple_dates'}:
                counts = Counter(r['timestamp'].date() for r in rows)
                rows = [dict(date_match_count=counts[r['timestamp'].date()], **r) for r in rows if counts[r['timestamp'].date()] >= 2]
                columns = ('date_match_count',) + columns
                notes += ' Choices 7 and 8 select identical dates; both measured separation and nominal aspect angle are retained.'
        check(end)
        return Result(q, columns, tuple(rows), start, end, sampling, notes)
    except Cancelled:
        raise
    except Exception as exc:
        raise CalculationError(f'Incomplete calculation at {current.isoformat()}: {exc}') from exc
