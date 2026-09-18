from datetime import date, datetime
import importlib.util
import json
from pathlib import Path

import pytest

from astrocalc import calculations as calc
from astrocalc.models import Query, WORKFLOWS, UTC, display_zone, ValidationError

GOLDEN = json.loads(Path(__file__).with_name('legacy_regression.json').read_text())


def test_original_regression():
    moons = calc.calculate(Query('new_moons', year=2024, degree=30))
    assert [r['timestamp'].replace(tzinfo=None).isoformat() for r in moons.rows] == GOLDEN['new_moons_2024']
    for row in moons.rows:
        assert (row['derived_timestamp'] - row['timestamp']).total_seconds() == pytest.approx(30 / 13.1764 * 86400, abs=1e-5)
    aspects = calc.calculate(Query('annual_aspects', year=2024, body='Mars', other='Venus'))
    assert [[r['timestamp'].date().isoformat(), r['aspect'], r['aspect_angle']] for r in aspects.rows] == GOLDEN['mars_venus_2024']
    positions = calc.calculate(Query('positions', date=date(2024,2,29)))
    for row in positions.rows:
        assert row['longitude'] == pytest.approx(GOLDEN['positions_2024_02_29'][row['body']], abs=1e-10)


@pytest.mark.parametrize('workflow', WORKFLOWS)
def test_all_workflows_and_exporters(workflow):
    from astrocalc.exporters import render_export
    result = calc.calculate(Query(workflow, year=2024, month=12, date=date(2024,2,29)))
    assert result.rows
    assert set(result.records()[0]) == set(result.headers)
    assert render_export(result, 'csv').splitlines()[0].endswith(','.join(result.headers))
    assert 'Result count:' in render_export(result, 'txt')
    assert result.start.tzinfo is not None


def test_date_grouped_equivalence():
    a = calc.calculate(Query('repeating_dates', year=2024))
    b = calc.calculate(Query('multiple_dates', year=2024))
    assert a.rows == b.rows
    assert all(r['date_match_count'] >= 2 for r in a.rows)


def test_circular_and_zodiac_boundaries():
    assert calc.zodiac(360) == ('Aries', 0)
    assert calc.zodiac(-1) == ('Pisces', 29)
    assert calc.zodiac(30) == ('Taurus', 0)
    assert calc.circular_distance(359.8, 0) == pytest.approx(.2)
    assert [calc.alignment_group(x) for x in (0, .99, 1, 23.99, 24, 25, 360)] == [24,24,1,23,24,1,24]


def test_special_wrap_and_strict_threshold(monkeypatch):
    monkeypatch.setattr(calc, 'longitude', lambda body, instant: 359.75 if body == 'Sun' else 359.5)
    result = calc.calculate(Query('special', year=2024))
    assert len(result.rows) == 366
    assert all(r['body'] == 'Sun' and r['target_longitude'] == 0 for r in result.rows)


def test_zero_first_sample_and_retrograde(monkeypatch):
    monkeypatch.setattr(calc, 'longitude', lambda body, instant: .25)
    result = calc.calculate(Query('zero', year=2024))
    assert len(result.rows) == 3660
    assert all(r['timestamp'].hour == 0 for r in result.rows)
    assert all(not r['retrograde'] for r in result.rows)


def test_hourly_bucket_resolution(monkeypatch):
    monkeypatch.setattr(calc, 'longitude', lambda body, instant: 2.9 if instant.hour >= 3 else 1.9)
    result = calc.calculate(Query('moon_degree', year=2024, month=12, degree=2))
    assert result.rows[0]['timestamp'] == datetime(2024,12,1,3,tzinfo=UTC)
    assert result.rows[0]['degree'] == 2.9
    assert result.end == datetime(2025,1,1,tzinfo=UTC)


def test_sampling_orbs_and_repeating_counts():
    for wf, orb, hour in [('annual_aspects', .3, 12), ('monthly_body', 1, 0), ('repeating', 1, 0)]:
        result = calc.calculate(Query(wf, year=2024))
        assert all(r['orb'] == orb and r['timestamp'].hour == hour for r in result.rows)
    result = calc.calculate(Query('monthly_all', year=2024))
    for r in result.rows:
        assert r['orb'] == max({'Sun':1, 'Mercury':3.5, 'Mars':3.5}.get(b,2.5) for b in (r['body'], r['other']))
        assert r['timestamp'].hour == 12


def test_failure_does_not_loop_or_return_partial(monkeypatch):
    calls = []
    def broken(*args):
        calls.append(args)
        raise RuntimeError('ephemeris unavailable')
    monkeypatch.setattr(calc, 'longitude', broken)
    for workflow in WORKFLOWS:
        with pytest.raises(calc.CalculationError, match='Incomplete calculation'):
            calc.calculate(Query(workflow))
    assert len(calls) == 12


def test_cancellation():
    with pytest.raises(calc.Cancelled):
        calc.calculate(Query('zero'), cancel=lambda: True)


def test_zones_and_ephem_boundary():
    winter = datetime(2024,1,1,12,tzinfo=UTC)
    summer = datetime(2024,7,1,12,tzinfo=UTC)
    assert winter.astimezone(display_zone('America/Chicago')).hour == 6
    assert summer.astimezone(display_zone('America/Chicago')).hour == 7
    assert summer.astimezone(display_zone('UTC-06:00')).hour == 6
    assert calc.ephem_date(summer) == calc.ephem_date(summer.astimezone(display_zone('America/Chicago')))
    with pytest.raises(ValueError):
        calc.ephem_date(datetime(2024,1,1))


@pytest.mark.parametrize('values', [{'year':1899}, {'year':2101}, {'month':13}, {'degree':float('nan')}, {'degree':float('inf')}, {'timezone':'No/Such_Zone'}, {'body':'Earth'}, {'other':'Sun'}, {'degree':30}])
def test_validation(values):
    wf = 'annual_aspects' if 'other' in values else 'moon_degree'
    with pytest.raises(ValidationError):
        Query(wf, **values).validate()


def test_legacy_import_has_no_menu(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda *args: pytest.fail('Import prompted for input'))
    spec = importlib.util.spec_from_file_location('legacy', Path(__file__).parents[1] / 'src/degreeCalc.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


@pytest.mark.parametrize('workflow', ['monthly_body', 'repeating', 'repeating_dates', 'multiple_dates', 'zero', 'alignments', 'monthly_all'])
def test_original_workflow_digests(workflow):
    """Original function-local results captured at return, before presentation."""
    from collections import defaultdict
    import hashlib
    expected = json.loads(Path(__file__).with_name('legacy_workflow_digests.json').read_text())[workflow]
    result = calc.calculate(Query(workflow, year=2024, month=12))
    rows = []
    for r in result.rows:
        d = r['timestamp'].replace(tzinfo=None)
        if workflow == 'monthly_body':
            rows.append([d.isoformat(), r['body'], r['other'], r['aspect'], r['aspect_angle'], round(r['separation'],2)])
        elif workflow == 'repeating':
            rows.append([d.isoformat(),r['other'],r['aspect'],r['group_sample_count']])
        elif workflow in {'repeating_dates','multiple_dates'}:
            angle = r['separation'] if workflow == 'repeating_dates' else r['aspect_angle']
            rows.append([d.date().isoformat(),r['other'],r['aspect'],round(angle,8)])
        elif workflow == 'zero':
            rows.append([d.date().isoformat(),r['body'],r['sign'],round(r['degree'],2),'Rx' if r['retrograde'] else ''])
        elif workflow == 'monthly_all':
            rows.append([d.date().isoformat(),r['body'],r['other'],r['aspect'],r['aspect_angle'],r['sign'],round(r['degree'],8),r['other_sign'],round(r['other_degree'],8)])
    if workflow == 'alignments':
        groups = defaultdict(list)
        for r in result.rows:
            groups[r['timestamp'].date().isoformat(),r['group']].append(r)
        for (d,g),members in groups.items():
            bodies = ', '.join(r['body'] + ('(Rx)' if r['retrograde'] else '') for r in members)
            degrees = ', '.join(f"{r['longitude']:.1f}°" for r in members)
            rows.append([d,g,bodies,degrees])
    assert len(rows) == expected['count']
    digest = hashlib.sha256(json.dumps(sorted(rows),sort_keys=True).encode()).hexdigest()
    assert digest == expected['sha256']
