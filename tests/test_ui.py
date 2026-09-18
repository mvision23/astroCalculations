from datetime import date
import time

import pytest
from textual.widgets import Input, Select, Static, DataTable

from astrocalc.calendar import CalendarDialog, MonthGrid, move_month, parse_date
from astrocalc.ui import AstroApp, FormScreen, ResultsScreen, ExportDialog, RunningScreen, ConfirmOverwrite


async def tab_to(pilot, app, widget_id, limit=30):
    for _ in range(limit):
        if app.focused is not None and app.focused.id == widget_id:
            return
        await pilot.press('tab')
    pytest.fail(f'Could not reach {widget_id} with Tab; focus is {app.focused}')


async def replace_text(pilot, value):
    await pilot.press('home', 'shift+end', *list(value))


async def wait_for_screen(pilot, app, cls):
    for _ in range(80):
        if isinstance(app.screen, cls):
            return
        await pilot.pause(.05)
    pytest.fail(f'Expected {cls.__name__}, got {type(app.screen).__name__}')


def test_calendar_math():
    assert move_month(date(2024,1,31),1) == date(2024,2,29)
    assert move_month(date(2023,1,31),1) == date(2023,2,28)
    assert move_month(date(2024,12,31),1) == date(2025,1,31)
    assert move_month(date(2024,1,31),-1) == date(2023,12,31)
    with pytest.raises(ValueError):
        parse_date('2023-02-29')
    with pytest.raises(ValueError):
        parse_date('2101-01-01')


async def test_keyboard_calendar_results_both_exports(tmp_path):
    app = AstroApp()
    async with app.run_test(size=(80,24)) as pilot:
        await pilot.press(*(['down'] * 8), 'enter')
        assert isinstance(app.screen, FormScreen)
        await tab_to(pilot, app, 'date')
        await replace_text(pilot, '2024-02-28')
        await tab_to(pilot, app, 'calendar')
        await pilot.press('enter')
        assert isinstance(app.screen, CalendarDialog)
        await pilot.press('right', 'enter')
        assert app.screen.query_one('#date', Input).value == '2024-02-29'
        await tab_to(pilot, app, 'calendar')
        await pilot.press('enter', 'right', 'escape')
        assert app.screen.query_one('#date', Input).value == '2024-02-29'
        await pilot.press('f5')
        await wait_for_screen(pilot, app, ResultsScreen)
        assert app.screen.query_one(DataTable).row_count == 10
        await pilot.press('right', 'down', 'f6')
        await tab_to(pilot, app, 'search')
        await pilot.press(*list('Pluto'))
        assert app.screen.query_one(DataTable).row_count == 1
        await pilot.press('ctrl+e')
        assert isinstance(app.screen, ExportDialog)
        await tab_to(pilot, app, 'directory')
        await replace_text(pilot, str(tmp_path))
        await tab_to(pilot, app, 'scope')
        await pilot.press('enter', 'down', 'enter')
        assert app.screen.query_one('#scope', Select).value == 'filtered'
        await pilot.press('ctrl+s')
        files = list(tmp_path.glob('*.txt'))
        assert len(files) == 1 and 'Result count: 1' in files[0].read_text()
        await tab_to(pilot, app, 'format')
        await pilot.press('enter', 'down', 'enter', 'ctrl+s')
        files = list(tmp_path.glob('*.csv'))
        assert len(files) == 1 and len(files[0].read_text().splitlines()) == 2
        await pilot.press('ctrl+s')
        assert isinstance(app.screen, ConfirmOverwrite)
        await pilot.press('escape', 'escape', 'escape')
        assert isinstance(app.screen, FormScreen)
        assert app.screen.query_one('#date', Input).value == '2024-02-29'
        await pilot.resize_terminal(100,30)
        await pilot.press('escape', 'enter')
        assert app.screen.query_one('#date', Input).value == '2024-02-29'


async def test_calendar_boundaries_and_direct_year():
    app = AstroApp()
    async with app.run_test(size=(80,24)) as pilot:
        selected = []
        app.push_screen(CalendarDialog(date(2024,12,31)), selected.append)
        await pilot.pause()
        await pilot.press('right')
        assert app.screen.focused_date == date(2025,1,1)
        await pilot.press('left', 'pageup')
        assert app.screen.focused_date == date(2024,11,30)
        await tab_to(pilot, app, 'cal-year')
        await replace_text(pilot, '2000')
        await pilot.press('enter')
        assert app.screen.focused_date == date(2000,11,30)
        await tab_to(pilot, app, 'cal-date')
        await replace_text(pilot, '2000-02-29')
        await pilot.press('enter')
        assert selected == [date(2000,2,29)]
        app.push_screen(CalendarDialog(date(1900,1,1)), selected.append)
        await pilot.pause()
        await pilot.press('left', 'up', 'pageup')
        assert app.screen.focused_date == date(1900,1,1)
        await pilot.press('escape')
        assert selected[-1] is None


async def test_cancel_and_failure_preserve_completed_result(monkeypatch):
    import astrocalc.ui as ui
    from astrocalc.calculations import Cancelled
    app = AstroApp()
    async with app.run_test() as pilot:
        await pilot.press(*(['down']*8), 'enter', 'f5')
        await wait_for_screen(pilot, app, ResultsScreen)
        original = app.screen.result
        def slow(query, *, cancel, progress):
            while not cancel():
                time.sleep(.01)
            raise Cancelled()
        monkeypatch.setattr(ui, 'calculate', slow)
        await pilot.press('f5')
        assert isinstance(app.screen, RunningScreen)
        await pilot.press('escape')
        await pilot.pause(.1)
        assert isinstance(app.screen, ResultsScreen) and app.screen.result is original
        def fail(*args, **kwargs):
            raise RuntimeError('test failure')
        monkeypatch.setattr(ui, 'calculate', fail)
        await pilot.press('f5')
        await pilot.pause(.2)
        assert isinstance(app.screen, RunningScreen)
        assert 'Failed:' in str(app.screen.query_one('#progress', Static).content)
        await pilot.press('escape')
        assert app.screen.result is original


async def test_invalid_input_and_help_do_not_lose_values():
    app = AstroApp()
    async with app.run_test() as pilot:
        await pilot.press('enter')
        await tab_to(pilot, app, 'year')
        await replace_text(pilot, 'oops')
        await pilot.press('f5')
        assert isinstance(app.screen, FormScreen)
        assert 'valid number' in str(app.screen.query_one('#error-year', Static).content)
        await pilot.press('f1', 'escape')
        assert app.screen.query_one('#year', Input).value == 'oops'
