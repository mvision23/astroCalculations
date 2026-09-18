import csv
from dataclasses import replace
from datetime import date
import io

import pytest

from astrocalc.calculations import calculate
from astrocalc.exporters import render_export, save_export, select_records
from astrocalc.models import Query


def test_csv_types_quotes_and_settings():
    result = calculate(Query('positions', date=date(2024,2,29), timezone='America/Chicago'))
    row = dict(result.rows[0], body='quoted, "body"\nline')
    result = replace(result, rows=(row,))
    parsed = list(csv.DictReader(io.StringIO(render_export(result, 'csv'))))[0]
    assert parsed['body'] == row['body']
    assert float(parsed['longitude']) == row['longitude']
    assert parsed['timestamp_utc'].endswith('+00:00')
    assert parsed['timestamp_local'].endswith('-06:00')
    assert parsed['query_date'] == '2024-02-29'
    assert parsed['display_timezone'] == 'America/Chicago'
    assert 'coordinates' in parsed and 'sampling' in parsed


def test_empty_exports_and_sort():
    result = calculate(Query('positions'))
    rows = select_records(result, sort_key='longitude', reverse=True)
    assert rows[0]['longitude'] >= rows[-1]['longitude']
    assert len(select_records(result, search='Pluto')) == 1
    assert len(render_export(result, 'csv', []).splitlines()) == 1
    assert 'No matching results.' in render_export(result, 'txt', [])
    assert '\x1b' not in render_export(result, 'txt')


def test_overwrite_and_invalid_paths(tmp_path):
    result = calculate(Query('positions'))
    path = save_export(result, tmp_path, 'test.csv', 'csv')
    path.write_text('preserve me')
    with pytest.raises(FileExistsError):
        save_export(result, tmp_path, 'test.csv', 'csv')
    assert path.read_text() == 'preserve me'
    save_export(result, tmp_path, 'test.csv', 'csv', overwrite=True)
    assert path.read_text().startswith('workflow,')
    with pytest.raises(ValueError):
        save_export(result, tmp_path, '../bad.txt', 'txt')
    with pytest.raises(ValueError):
        save_export(result, tmp_path / 'absent', 'bad.txt', 'txt')


def test_write_failure_preserves_existing(tmp_path, monkeypatch):
    import astrocalc.exporters as exporters
    result = calculate(Query('positions'))
    path = tmp_path / 'existing.txt'
    path.write_text('original')
    def fail(*args):
        raise OSError('disk full')
    monkeypatch.setattr(exporters.os, 'fsync', fail)
    with pytest.raises(OSError):
        save_export(result, tmp_path, path.name, 'txt', overwrite=True)
    assert path.read_text() == 'original'
    assert list(tmp_path.iterdir()) == [path]
