"""Textual screens. Calculations run in cancellable background threads."""
from datetime import date
from pathlib import Path
from threading import Event
import time

from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.message import Message
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, OptionList, Select, Static

from .calendar import CalendarDialog, parse_date
from .calculations import calculate, Cancelled
from .exporters import default_filename, format_value, save_export, select_records
from .models import BODIES, BODY_WORKFLOWS, MONTHLY, SIGNS, WORKFLOWS, Query, ValidationError


class HelpScreen(ModalScreen):
    BINDINGS = [('escape', 'close', 'Back'), ('f1', 'close', 'Back')]

    def compose(self):
        with VerticalScroll(classes='dialog'):
            yield Label('AstroCalc help', classes='title')
            yield Static('Menu: Up/Down then Enter. Tab/Shift+Tab moves focus.\n'
                         'Inputs: arrows edit text; Enter submits where indicated.\n'
                         'F1 help • F5 calculate/rerun • Ctrl+E export • Ctrl+Q quit\n'
                         'Escape returns, cancels a dialog, or cancels running work.\n\n'
                         'Calendar: arrows move a day/week; PageUp/PageDown move a month.\n'
                         'Tab to month/year controls, enter a year, then Go.\n'
                         'Type YYYY-MM-DD then Enter, or focus grid and Enter.\n\n'
                         'Results: arrows move cells/rows; Tab reaches search and sort.\n'
                         'F6 sorts the focused column; repeat to reverse.\n'
                         'Search matches any column. Exports preserve the sort order.\n\n'
                         'Search boundaries and sampling times are UTC. Display zones only\n'
                         'convert timestamps. UTC-06:00 is fixed, unlike America/Chicago.\n'
                         'Years 1900–2100. Rx/Yes means sampled retrograde motion.\n'
                         'Results are sampled matches, not necessarily distinct events.\n'
                         'See README.md and docs/EXPORTS.md for numerical conventions.', markup=False)
            yield Button('Back', id='help-back')
        yield Footer()

    def action_close(self):
        self.dismiss()

    def on_button_pressed(self):
        self.dismiss()


class MenuScreen(Screen):
    def compose(self):
        yield Header()
        yield Label('AstroCalc • choose a calculation', classes='title')
        yield OptionList(*(f'{i:2}. {title}' for i, title in enumerate(WORKFLOWS.values(), 1)), id='menu')
        yield Footer()

    @on(OptionList.OptionSelected)
    def selected(self, event):
        key = list(WORKFLOWS)[event.option_index]
        if key not in self.app.forms:
            self.app.forms[key] = FormScreen(key)
            self.app.install_screen(self.app.forms[key], key)
        self.app.push_screen(key)


class FormScreen(Screen):
    BINDINGS = [('escape', 'back', 'Back'), ('f5', 'run', 'Calculate')]

    def __init__(self, workflow):
        super().__init__()
        self.workflow = workflow
        self.result = None

    def field(self, name, label, widget):
        yield Label(label)
        yield widget
        yield Static('', id='error-' + name, classes='field-error', markup=False)

    def compose(self):
        yield Header()
        with VerticalScroll(id='form-scroll'):
            yield Label(WORKFLOWS[self.workflow], classes='title')
            yield Static('UTC search boundaries • display timezone does not change the search.\nSupported years: 1900–2100.', markup=False)
            if self.workflow == 'positions':
                yield from self.field('date', 'Date (YYYY-MM-DD), calculated at 00:00 UTC', Input(date.today().isoformat(), id='date'))
                yield Button('Open calendar', id='calendar')
            else:
                yield from self.field('year', 'Year', Input(str(date.today().year), id='year'))
            if self.workflow in MONTHLY:
                yield from self.field('month', 'Month', Select([(f'{m:02}', m) for m in range(1,13)], value=date.today().month, allow_blank=False, id='month'))
            if self.workflow in BODY_WORKFLOWS:
                yield from self.field('body', 'Body', Select([(b,b) for b in BODIES], value='Sun', allow_blank=False, id='body'))
            if self.workflow == 'annual_aspects':
                yield from self.field('other', 'Other body', Select([(b,b) for b in BODIES], value='Moon', allow_blank=False, id='other'))
            if self.workflow == 'moon_degree':
                yield from self.field('sign', 'Zodiac sign', Select([(s,s) for s in SIGNS], value='Aries', allow_blank=False, id='sign'))
            if self.workflow in {'new_moons', 'moon_degree'}:
                label = 'Estimated offset (-360 to 360 degrees; offset / 13.1764 days)' if self.workflow == 'new_moons' else 'Integer degree bucket (0–29); first hourly sample'
                yield from self.field('degree', label, Input('0', id='degree'))
            yield from self.field('timezone', 'Display timezone: UTC, UTC-06:00 (fixed), or IANA name', Input('UTC', id='timezone'))
            with Horizontal(classes='controls'):
                yield Button('Calculate (F5)', id='run', variant='primary')
                yield Button('Last result', id='last', disabled=self.result is None)
                yield Button('Back', id='back')
        yield Footer()

    def action_back(self):
        self.app.pop_screen()

    def open_calendar(self):
        field = self.query_one('#date', Input)
        try:
            selected = parse_date(field.value)
        except ValueError:
            selected = date.today()
        def chosen(value):
            if value is not None:
                field.value = value.isoformat()
            field.focus()
        self.app.push_screen(CalendarDialog(selected), chosen)

    def get_query(self):
        values = {'workflow': self.workflow}
        for field in ('year', 'month', 'date', 'body', 'other', 'sign', 'degree', 'timezone'):
            matches = self.query('#' + field)
            if matches:
                value = matches.first().value
                try:
                    if field in {'year', 'month'}:
                        value = int(value)
                    elif field == 'degree':
                        value = float(value)
                    elif field == 'date':
                        value = parse_date(value)
                    else:
                        value = str(value).strip()
                except ValueError as exc:
                    raise ValidationError(field, str(exc) if field == 'date' else 'Enter a valid number') from exc
                values[field] = value
        if 'date' in values:
            values['year'] = values['date'].year
        return Query(**values).validate()

    def action_run(self):
        for error in self.query('.field-error'):
            error.update('')
        try:
            query = self.get_query()
        except ValidationError as exc:
            self.query_one('#error-' + exc.field, Static).update(str(exc))
            self.query_one('#' + exc.field).focus()
            return
        self.app.push_screen(RunningScreen(query), self.finished)

    def finished(self, outcome):
        if outcome is not None:
            self.result = outcome
            self.query_one('#last', Button).disabled = False
            self.app.push_screen(ResultsScreen(outcome, self))

    def on_button_pressed(self, event):
        if event.button.id == 'calendar':
            self.open_calendar()
        elif event.button.id == 'run':
            self.action_run()
        elif event.button.id == 'last' and self.result is not None:
            self.app.push_screen(ResultsScreen(self.result, self))
        elif event.button.id == 'back':
            self.action_back()


class RunningScreen(ModalScreen):
    BINDINGS = [('escape', 'cancel', 'Cancel')]

    class Progress(Message):
        def __init__(self, text):
            super().__init__()
            self.text = text

    class Finished(Message):
        def __init__(self, result=None, error=None):
            super().__init__()
            self.result = result
            self.error = error

    def __init__(self, query):
        super().__init__()
        self.calculation_query = query
        self.cancel_event = Event()
        self.closed = False

    def compose(self):
        with VerticalScroll(classes='dialog'):
            yield Label('Calculating…', classes='title')
            yield Static('Starting…', id='progress', markup=False)
            yield Button('Cancel', id='cancel')
        yield Footer()

    def on_mount(self):
        self.calculate_work()

    @work(thread=True)
    def calculate_work(self):
        last = 0.0
        def progress(fraction):
            nonlocal last
            now = time.monotonic()
            if now - last > 0.1:
                last = now
                self.post_message(self.Progress(f'{fraction:.0%} • Escape to cancel'))
        try:
            result = calculate(self.calculation_query, cancel=self.cancel_event.is_set, progress=progress)
        except Cancelled:
            self.post_message(self.Finished())
        except Exception as exc:
            self.post_message(self.Finished(error=str(exc)))
        else:
            self.post_message(self.Finished(result))

    @on(Progress)
    def progress_message(self, event):
        self.update_progress(event.text)

    @on(Finished)
    def finished_message(self, event):
        if event.error is not None:
            self.failure(event.error)
        else:
            self.finish(event.result)

    def update_progress(self, text):
        if not self.closed:
            self.query_one('#progress', Static).update(text)

    def finish(self, result):
        if not self.closed:
            self.closed = True
            self.dismiss(None if self.cancel_event.is_set() else result)

    def failure(self, message):
        if not self.closed:
            self.update_progress('Failed: ' + message + '\nNo partial result was saved. Escape to return.')
            self.query_one('#cancel', Button).label = 'Back'

    def action_cancel(self):
        self.cancel_event.set()
        self.finish(None)

    def on_unmount(self):
        self.cancel_event.set()

    def on_button_pressed(self):
        self.action_cancel()


class ResultsScreen(Screen):
    BINDINGS = [('escape', 'back', 'Parameters'), Binding('ctrl+e', 'export', 'Export', priority=True),
                ('f5', 'rerun', 'Rerun'), ('f6', 'sort_column', 'Sort column')]

    def __init__(self, result, form):
        super().__init__()
        self.result = result
        self.form = form
        self.sort_key = result.headers[0]
        self.reverse = False

    def compose(self):
        yield Header()
        yield Label(self.result.title, classes='title')
        yield Static(f'{self.result.query.period} • {self.result.query.timezone}\n{self.result.sampling}', id='result-meta', markup=False)
        yield Input(placeholder='Filter results (any column)', id='search')
        with Horizontal(classes='controls'):
            yield Select([(k.replace('_', ' ').title(), k) for k in self.result.headers], value=self.sort_key, allow_blank=False, id='sort')
            yield Button('Ascending', id='direction')
            yield Button('Export', id='export')
        yield Static('', id='count', markup=False)
        yield DataTable(id='results', zebra_stripes=True, cursor_type='cell')
        yield Footer()

    def on_mount(self):
        table = self.query_one(DataTable)
        for key in self.result.headers:
            table.add_column(key.replace('_', ' ').title(), key=key)
        self.refresh_table()
        table.focus()

    def records(self, filtered=True):
        search = self.query_one('#search', Input).value if filtered else ''
        return select_records(self.result, search, self.sort_key, self.reverse)

    def refresh_table(self):
        table = self.query_one(DataTable)
        table.clear()
        rows = self.records()
        for row in rows:
            table.add_row(*(format_value(row[k]) for k in self.result.headers))
        self.query_one('#count', Static).update(f'{len(rows)} / {len(self.result.rows)} rows • F6 sort selected column • F2 calculation notes')

    @on(Input.Changed, '#search')
    def search_changed(self):
        self.refresh_table()

    @on(Select.Changed, '#sort')
    def sort_changed(self, event):
        if isinstance(event.value, str):
            self.sort_key = event.value
            self.refresh_table()

    def action_sort_column(self):
        key = self.result.headers[self.query_one(DataTable).cursor_column]
        if key == self.sort_key:
            self.reverse = not self.reverse
        self.sort_key = key
        self.query_one('#sort', Select).value = key
        self.query_one('#direction', Button).label = 'Descending' if self.reverse else 'Ascending'
        self.refresh_table()

    def action_back(self):
        self.app.pop_screen()

    def action_export(self):
        self.app.push_screen(ExportDialog(self.result, self.records(False), self.records(True)))

    def action_rerun(self):
        self.app.push_screen(RunningScreen(self.result.query), self.rerun_finished)

    def rerun_finished(self, result):
        if result is not None:
            self.result = self.form.result = result
            self.refresh_table()

    def on_button_pressed(self, event):
        if event.button.id == 'export':
            self.action_export()
        elif event.button.id == 'direction':
            self.reverse = not self.reverse
            event.button.label = 'Descending' if self.reverse else 'Ascending'
            self.refresh_table()

    BINDINGS = BINDINGS + [('f2', 'notes', 'Notes')]

    def action_notes(self):
        self.app.push_screen(NotesDialog(self.result))


class NotesDialog(ModalScreen):
    BINDINGS = [('escape', 'close', 'Back')]

    def __init__(self, result):
        super().__init__()
        self.result = result

    def compose(self):
        with VerticalScroll(classes='dialog'):
            yield Label('Calculation settings', classes='title')
            yield Static('\n\n'.join(f'{k}: {v}' for k,v in self.result.metadata().items()), markup=False)
            yield Button('Back')
        yield Footer()

    def action_close(self):
        self.dismiss()

    def on_button_pressed(self):
        self.dismiss()


class ConfirmOverwrite(ModalScreen[bool]):
    BINDINGS = [('escape', 'cancel', 'Cancel')]

    def __init__(self, path):
        super().__init__()
        self.path = path

    def compose(self):
        with VerticalScroll(classes='dialog'):
            yield Static(f'File exists:\n{self.path}\nReplace this file?', markup=False)
            yield Button('Cancel', id='no')
            yield Button('Replace', id='yes', variant='warning')
        yield Footer()

    def action_cancel(self):
        self.dismiss(False)

    def on_button_pressed(self, event):
        self.dismiss(event.button.id == 'yes')


class ExportDialog(ModalScreen):
    BINDINGS = [('escape', 'cancel', 'Back to results'), Binding('ctrl+s', 'save', 'Save', priority=True)]

    def __init__(self, result, all_rows, filtered_rows):
        super().__init__()
        self.result, self.all_rows, self.filtered_rows = result, all_rows, filtered_rows

    def compose(self):
        with VerticalScroll(classes='dialog'):
            yield Label('Export results', classes='title')
            yield Label('Format')
            yield Select([('Plain text (.txt)', 'txt'), ('CSV (.csv)', 'csv')], value='txt', allow_blank=False, id='format')
            yield Label('Destination directory')
            yield Input(str(Path.cwd()), id='directory')
            yield Label('Filename')
            yield Input(default_filename(self.result, 'txt'), id='filename')
            yield Label('Rows (current table sort order)')
            yield Select([('All results', 'all'), ('Filtered results', 'filtered')], value='all', allow_blank=False, id='scope')
            yield Static(f'{len(self.all_rows)} rows selected', id='export-count', markup=False)
            yield Static('', id='export-status', classes='error', markup=False)
            with Horizontal(classes='controls'):
                yield Button('Save (Ctrl+S)', id='save', variant='primary')
                yield Button('Back', id='export-back')
        yield Footer()

    @on(Select.Changed, '#format')
    def format_changed(self, event):
        if isinstance(event.value, str):
            field = self.query_one('#filename', Input)
            field.value = str(Path(field.value).with_suffix('.' + event.value))

    @on(Select.Changed, '#scope')
    def scope_changed(self, event):
        rows = self.all_rows if event.value == 'all' else self.filtered_rows
        self.query_one('#export-count', Static).update(f'{len(rows)} rows selected')

    def action_save(self):
        directory = self.query_one('#directory', Input).value
        filename = self.query_one('#filename', Input).value
        format = self.query_one('#format', Select).value
        rows = self.all_rows if self.query_one('#scope', Select).value == 'all' else self.filtered_rows
        def write(overwrite=False):
            try:
                path = save_export(self.result, directory, filename, format, rows, overwrite=overwrite)
            except FileExistsError:
                self.app.push_screen(ConfirmOverwrite(Path(directory).expanduser() / filename), lambda yes: write(True) if yes else None)
            except (OSError, ValueError) as exc:
                self.query_one('#export-status', Static).update(f'Export failed: {exc}')
            else:
                self.query_one('#export-status', Static).update(f'Saved {len(rows)} rows to {path}')
                self.app.notify(f'Saved: {path}', timeout=8)
        write()

    def action_cancel(self):
        self.dismiss()

    def on_button_pressed(self, event):
        if event.button.id == 'save':
            self.action_save()
        elif event.button.id == 'export-back':
            self.action_cancel()


class AstroApp(App):
    TITLE = 'AstroCalc'
    BINDINGS = [('f1', 'help', 'Help'), Binding('ctrl+q', 'quit', 'Quit', priority=True)]
    CSS = '''
    Screen { background: $surface; }
    .title { text-style: bold; color: $accent; margin: 1 1; height: auto; }
    #menu { height: 1fr; margin: 0 1; }
    #form-scroll { padding: 0 2; }
    Label { height: auto; }
    Input, Select { margin: 0; }
    .field-error { height: auto; color: $error; }
    .error { height: auto; color: $warning; }
    .controls { height: auto; min-height: 3; }
    .controls Button { min-width: 10; width: auto; }
    .controls Select, .controls Input { width: 1fr; }
    ModalScreen { align: center middle; background: $background 65%; }
    .dialog { width: 72; max-width: 96%; height: auto; max-height: 90%; padding: 1 2; border: thick $accent; background: $surface; }
    .calendar-dialog { width: 64; }
    #month-grid { height: 10; width: 100%; }
    #month-grid:focus { border: heavy $accent; }
    #cal-summary { height: 2; }
    #result-meta { height: auto; max-height: 3; }
    #count { height: 1; }
    #results { height: 1fr; }
    Input:focus, Button:focus, Select:focus { border: heavy $accent; }
    '''

    def __init__(self):
        super().__init__()
        self.forms = {}

    def on_mount(self):
        self.push_screen(MenuScreen())

    def action_help(self):
        if not isinstance(self.screen, HelpScreen):
            self.push_screen(HelpScreen())
