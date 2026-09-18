"""Validated queries and structured results shared by UI and exporters."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc
MIN_YEAR, MAX_YEAR = 1900, 2100
BODIES = ('Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto')
SIGNS = ('Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces')
WORKFLOWS = {
    'new_moons': 'New moons and degree offsets',
    'moon_degree': 'Moon at a zodiac degree',
    'annual_aspects': 'Aspects between two bodies',
    'special': 'Special longitudes',
    'monthly_body': 'Monthly aspects for one body',
    'repeating': 'Repeating aspects (matching sample dates)',
    'repeating_dates': 'Repeating aspects grouped by date',
    'multiple_dates': 'Dates with two or more aspects',
    'positions': 'Planetary positions',
    'zero': 'Bodies near 0 degrees of a sign',
    'alignments': 'Planetary alignments (degree modulo 24)',
    'monthly_all': 'All monthly aspects',
}
MONTHLY = {'moon_degree', 'monthly_body', 'monthly_all'}
BODY_WORKFLOWS = {'annual_aspects', 'monthly_body', 'repeating', 'repeating_dates', 'multiple_dates'}
COORDINATES = 'PyEphem Ecliptic(body), default epoch J2000; original compute(date) convention'


def display_zone(name):
    if name == 'UTC-06:00':
        return timezone(timedelta(hours=-6), name)
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError('Use UTC, UTC-06:00 (fixed), or an IANA zone such as America/Chicago') from exc


class ValidationError(ValueError):
    def __init__(self, field, message):
        self.field = field
        super().__init__(message)


@dataclass(frozen=True)
class Query:
    workflow: str
    year: int = 2026
    month: int = 1
    date: date = date(2026, 1, 1)
    body: str = 'Sun'
    other: str = 'Moon'
    sign: str = 'Aries'
    degree: float = 0
    timezone: str = 'UTC'

    def validate(self):
        def require(ok, field, message):
            if not ok:
                raise ValidationError(field, message)
        require(self.workflow in WORKFLOWS, 'workflow', 'Unknown workflow')
        require(type(self.year) is int and MIN_YEAR <= self.year <= MAX_YEAR, 'year', 'Year must be 1900–2100')
        require(type(self.month) is int and 1 <= self.month <= 12, 'month', 'Month must be 1–12')
        require(type(self.date) is date and MIN_YEAR <= self.date.year <= MAX_YEAR, 'date', 'Date must be in 1900–2100')
        require(self.body in BODIES, 'body', 'Select a supported body')
        require(self.other in BODIES, 'other', 'Select a supported body')
        require(self.workflow != 'annual_aspects' or self.body != self.other, 'other', 'Choose two distinct bodies')
        require(self.sign in SIGNS, 'sign', 'Select a zodiac sign')
        require(isinstance(self.degree, (int, float)) and math.isfinite(self.degree), 'degree', 'Degree must be finite')
        if self.workflow == 'moon_degree':
            require(0 <= self.degree < 30 and self.degree == int(self.degree), 'degree', 'Choose an integer degree bucket, 0–29')
        elif self.workflow == 'new_moons':
            require(-360 <= self.degree <= 360, 'degree', 'Offset must be between -360 and 360 degrees')
        try:
            display_zone(self.timezone)
        except ValueError as exc:
            raise ValidationError('timezone', str(exc)) from exc
        return self

    @property
    def period(self):
        if self.workflow == 'positions':
            return self.date.isoformat()
        return f'{self.year}-{self.month:02}' if self.workflow in MONTHLY else str(self.year)


@dataclass(frozen=True)
class Result:
    query: Query
    columns: tuple[str, ...]
    rows: tuple[dict, ...]
    start: datetime
    end: datetime
    sampling: str
    notes: str

    @property
    def title(self):
        return WORKFLOWS[self.query.workflow]

    def metadata(self):
        q = self.query
        return dict(workflow=q.workflow, period=q.period, query_year=q.date.year if q.workflow == 'positions' else q.year,
                    query_month=q.month if q.workflow in MONTHLY else '',
                    query_date=q.date.isoformat() if q.workflow == 'positions' else '',
                    query_body=q.body if q.workflow in BODY_WORKFLOWS else '',
                    query_other=q.other if q.workflow == 'annual_aspects' else '',
                    query_sign=q.sign if q.workflow == 'moon_degree' else '',
                    query_degree=q.degree if q.workflow in {'moon_degree', 'new_moons'} else '',
                    range_start_utc=self.start.isoformat(), range_end_exclusive_utc=self.end.isoformat(),
                    display_timezone=q.timezone, sampling=self.sampling, notes=self.notes, coordinates=COORDINATES)

    def records(self):
        zone = display_zone(self.query.timezone)
        records = []
        for row in self.rows:
            record = {}
            for key in self.columns:
                value = row.get(key, '')
                if isinstance(value, datetime):
                    record[key + '_utc'] = value.astimezone(UTC).isoformat()
                    record[key + '_local'] = value.astimezone(zone).isoformat()
                elif key in TIME_COLUMNS:
                    record[key + '_utc'] = record[key + '_local'] = ''
                else:
                    record[key] = value
            records.append(record)
        return records

    @property
    def headers(self):
        return tuple(part for key in self.columns for part in
                     ((key + '_utc', key + '_local') if key in TIME_COLUMNS else (key,)))


TIME_COLUMNS = {'timestamp', 'derived_timestamp'}
