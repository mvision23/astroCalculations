"""Offline geocentric providers. No market data or rendering dependencies."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import math
from typing import Protocol
import ephem
from astrocalc.calculations import ephem_date, longitude as legacy_longitude, zodiac

UTC = timezone.utc
MIN_TIME = datetime(1900, 1, 1, tzinfo=UTC)
MAX_TIME = datetime(2101, 1, 1, tzinfo=UTC)-timedelta(microseconds=1)
BODIES = ('Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto')
MODES = ('apparent_of_date', 'astrometric_of_date', 'legacy_j2000')

def instant(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('An explicit timezone/UTC offset is required')
    return value.astimezone(UTC)

def delta(a, b):
    """Signed shortest difference a-b in degrees."""
    return (a-b+180) % 360-180

@dataclass(frozen=True)
class Position:
    timestamp: datetime
    body: str
    longitude: float
    speed: float
    direction: str
    earth_distance_au: float
    sign: str
    degree: float

class Provider(Protocol):
    def longitude(self, body: str, time: datetime) -> float: ...
    def speed(self, body: str, time: datetime) -> float: ...
    def position(self, body: str, time: datetime) -> Position: ...
    def metadata(self) -> dict: ...

class EphemProvider:
    def __init__(self, mode='apparent_of_date'):
        if mode not in MODES:
            raise ValueError(f'Coordinate mode must be one of {MODES}')
        self.mode = mode

    def metadata(self):
        return dict(provider='PyEphem', backend_version=ephem.__version__, mode=self.mode,
                    origin='geocentric', zodiac='tropical', epoch='J2000' if self.mode=='legacy_j2000' else 'of date',
                    convention='apparent RA/Dec transformed to ecliptic of date' if self.mode=='apparent_of_date' else 'astrometric',
                    time_scale='UTC input; PyEphem internal dynamical time / delta-T',
                    supported_dates='1900-01-01 through 2100-12-31 UTC',
                    accuracy='Backend accuracy is not the event solver time tolerance; see docs/universal-clock.md',
                    downloads=False)

    @lru_cache(maxsize=250000)
    def _raw(self, body, time):
        time = instant(time)
        if body not in BODIES + ('Moon',):
            raise ValueError('Unsupported body (Earth is the observer)')
        if not 1900 <= time.year <= 2100:
            raise ValueError('Supported dates are 1900–2100')
        obj = getattr(ephem, body)()
        date = ephem_date(time)
        obj.compute(date)
        if self.mode == 'legacy_j2000':
            lon = legacy_longitude(body, time)
        elif self.mode == 'astrometric_of_date':
            lon = math.degrees(ephem.Ecliptic(obj, epoch=date).lon) % 360
        else:
            equ = ephem.Equatorial(obj.g_ra, obj.g_dec, epoch=date)
            lon = math.degrees(ephem.Ecliptic(equ, epoch=date).lon) % 360
        return lon, float(obj.earth_distance)

    def longitude(self, body, time):
        return self._raw(body, instant(time))[0]

    def speed(self, body, time):
        time = instant(time)
        h = timedelta(minutes=30)
        # Symmetric derivative; one-sided at supported interval boundaries.
        lo = max(time-h, MIN_TIME)
        hi = min(time+h, MAX_TIME)
        return delta(self.longitude(body, hi), self.longitude(body, lo)) / ((hi-lo).total_seconds()/86400)

    def position(self, body, time):
        time=instant(time)
        lon, distance = self._raw(body,time)
        speed=self.speed(body,time)
        sign,degree=zodiac(lon)
        return Position(time,body,lon,speed,'stationary' if abs(speed)<1e-5 else 'direct' if speed>0 else 'retrograde',distance,sign,degree)


def series(provider, bodies, times):
    rows=[]
    times=sorted(set(map(instant,times)))
    # Intermediate daily steps prevent wrap ambiguity for sparse requested instants.
    for body in bodies:
        previous_time=None; previous_lon=None; unwrapped=0.
        for t in times:
            p=provider.position(body,t)
            if previous_time is None:
                unwrapped=p.longitude
            else:
                cursor=previous_time
                while cursor<t:
                    cursor=min(cursor+timedelta(hours=6),t)
                    lon=provider.longitude(body,cursor)
                    unwrapped += delta(lon,previous_lon)
                    previous_lon=lon
            rows.append(dict(asdict(p),unwrapped=unwrapped,phase=p.longitude%24))
            previous_time=t;previous_lon=p.longitude
    return rows
