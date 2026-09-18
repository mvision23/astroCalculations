"""Reusable keyboard calendar. Cancellation returns None, never a new value."""
import calendar
from datetime import date, timedelta

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, Select, Static

from .models import MIN_YEAR, MAX_YEAR

MIN_DATE, MAX_DATE = date(MIN_YEAR, 1, 1), date(MAX_YEAR, 12, 31)


def move_month(value, delta):
    index = value.year * 12 + value.month - 1 + delta
    index = max(MIN_YEAR * 12, min(MAX_YEAR * 12 + 11, index))
    year, month = divmod(index, 12)
    return date(year, month + 1, min(value.day, calendar.monthrange(year, month + 1)[1]))


def parse_date(value):
    if len(value) != 10 or value[4] != '-' or value[7] != '-':
        raise ValueError('Use YYYY-MM-DD')
    parsed = date.fromisoformat(value)
    if not MIN_DATE <= parsed <= MAX_DATE:
        raise ValueError('Supported dates: 1900-01-01 through 2100-12-31')
    return parsed


class MonthGrid(Static, can_focus=True):
    BINDINGS = [('left', 'move(-1)', 'Day back'), ('right', 'move(1)', 'Day forward'),
                ('up', 'move(-7)', 'Week back'), ('down', 'move(7)', 'Week forward'),
                ('pageup', 'month(-1)', 'Previous month'), ('pagedown', 'month(1)', 'Next month'),
                ('enter', 'confirm', 'Select date')]

    def action_move(self, days):
        value = self.screen.focused_date + timedelta(days=days)
        self.screen.set_date(max(MIN_DATE, min(MAX_DATE, value)))

    def action_month(self, delta):
        value = self.screen.focused_date
        if (value == MIN_DATE and delta < 0) or (value.year == MAX_YEAR and value.month == 12 and delta > 0):
            return
        self.screen.set_date(move_month(value, delta))

    def action_confirm(self):
        self.screen.dismiss(self.screen.focused_date)


class CalendarDialog(ModalScreen[date | None]):
    BINDINGS = [('escape', 'cancel', 'Cancel')]

    def __init__(self, selected):
        super().__init__()
        self.selected_date = selected
        self.focused_date = selected

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes='dialog calendar-dialog'):
            yield Label('Choose date • arrows move days/weeks', classes='title')
            with Horizontal(classes='controls'):
                yield Select([(calendar.month_name[m], m) for m in range(1, 13)], value=self.focused_date.month, allow_blank=False, id='cal-month')
                yield Input(str(self.focused_date.year), id='cal-year', placeholder='Year')
                yield Button('Go', id='cal-go')
            yield MonthGrid(id='month-grid')
            yield Static(id='cal-summary', markup=False)
            yield Input(self.focused_date.isoformat(), id='cal-date', placeholder='YYYY-MM-DD')
            yield Static('', id='cal-error', classes='error', markup=False)
            with Horizontal(classes='controls'):
                yield Button('Today', id='cal-today')
                yield Button('Select', id='cal-select', variant='primary')
                yield Button('Cancel', id='cal-cancel')
        yield Footer()

    def on_mount(self):
        self.set_date(self.focused_date)
        self.query_one(MonthGrid).focus()

    def set_date(self, value):
        self.focused_date = value
        self.query_one('#cal-month', Select).value = value.month
        self.query_one('#cal-year', Input).value = str(value.year)
        self.query_one('#cal-date', Input).value = value.isoformat()
        text = Text(f'{calendar.month_name[value.month]} {value.year}\n Mo   Tu   We   Th   Fr   Sa   Su\n')
        for week in calendar.monthcalendar(value.year, value.month):
            for day in week:
                if day == value.day:
                    text.append(f'[{day:02}] ', style='bold reverse')
                elif day and date(value.year, value.month, day) == date.today():
                    text.append(f'*{day:02}* ', style='bold')
                else:
                    text.append(f' {day:02}  ' if day else '     ')
            text.append('\n')
        self.query_one(MonthGrid).update(text)
        self.query_one('#cal-summary', Static).update(f'Focused: {value} | Selected: {self.selected_date}\nToday: {date.today()} (* marks today)')

    @on(Input.Changed, '#cal-date')
    def validate_direct(self, event):
        try:
            parse_date(event.value)
            error = ''
        except ValueError as exc:
            error = str(exc)
        self.query_one('#cal-error', Static).update(error)

    def choose_direct(self):
        try:
            self.dismiss(parse_date(self.query_one('#cal-date', Input).value))
        except ValueError as exc:
            self.query_one('#cal-error', Static).update(str(exc))

    @on(Input.Submitted, '#cal-date')
    def direct_submit(self):
        self.choose_direct()

    @on(Input.Submitted, '#cal-year')
    def year_submit(self):
        self.go()

    def go(self):
        try:
            year = int(self.query_one('#cal-year', Input).value)
            month = int(self.query_one('#cal-month', Select).value)
            if not MIN_YEAR <= year <= MAX_YEAR:
                raise ValueError('Year must be 1900–2100')
            self.set_date(date(year, month, min(self.focused_date.day, calendar.monthrange(year, month)[1])))
            self.query_one('#cal-error', Static).update('')
            self.query_one(MonthGrid).focus()
        except ValueError as exc:
            self.query_one('#cal-error', Static).update(str(exc))

    def on_button_pressed(self, event):
        actions = {'cal-go': self.go, 'cal-select': self.choose_direct, 'cal-cancel': self.action_cancel,
                   'cal-today': lambda: self.set_date(max(MIN_DATE, min(MAX_DATE, date.today())))}
        actions[event.button.id]()

    def action_cancel(self):
        self.dismiss(None)
