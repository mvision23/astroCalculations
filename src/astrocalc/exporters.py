"""Plain UTF-8 and stable CSV exports, with atomic publication."""
import csv
import io
import os
from pathlib import Path
import tempfile

from .models import Result


def format_value(value):
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, float):
        return f'{value:.6f}'
    return str(value)


def select_records(result, search='', sort_key=None, reverse=False):
    rows = result.records()
    if search:
        rows = [row for row in rows if search.casefold() in ' '.join(map(str, row.values())).casefold()]
    if sort_key:
        rows.sort(key=lambda row: row[sort_key], reverse=reverse)
    return rows


def render_export(result: Result, format: str, records=None):
    records = result.records() if records is None else list(records)
    metadata = result.metadata()
    if format == 'csv':
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fieldnames=tuple(metadata) + ('result_count',) + result.headers)
        writer.writeheader()
        for row in records:
            writer.writerow(dict(metadata, result_count=len(records), **row))
        return stream.getvalue()
    if format != 'txt':
        raise ValueError('Format must be txt or csv')
    lines = [result.title, *(f'{key}: {value}' for key, value in metadata.items()), f'Result count: {len(records)}', '']
    widths = {key: max(len(key), *(len(format_value(row[key])) for row in records)) for key in result.headers} if records else {key: len(key) for key in result.headers}
    lines.append('  '.join(key.ljust(widths[key]) for key in result.headers))
    lines.extend('  '.join(format_value(row[key]).ljust(widths[key]) for key in result.headers) for row in records)
    if not records:
        lines.append('No matching results.')
    return '\n'.join(lines) + '\n'


def default_filename(result, format):
    return f'astrocalc_{result.query.workflow}_{result.query.period}.{format}'


def save_export(result, directory, filename, format, records=None, *, overwrite=False):
    if not filename or Path(filename).name != filename or filename in {'.', '..'}:
        raise ValueError('Filename must be a name without directory components')
    if not filename.endswith('.' + format):
        raise ValueError(f'Filename must end in .{format}')
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError('Destination directory does not exist')
    path = directory / filename
    content = render_export(result, format, records)
    # Stage before publishing: write failures cannot truncate an existing export.
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=directory, delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temp, path)
        else:
            os.link(temp, path)  # Atomic no-clobber, including a racing creator.
        return path
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
