from dataclasses import asdict
from datetime import date, timedelta
import json
import math
from pathlib import Path

import pytest

from astrocalc.universal.astronomy import BODIES, MODES, MAX_TIME, EphemProvider, instant
from astrocalc.universal.cli import main
from astrocalc.universal.geometry import Scale
from astrocalc.universal.plotting import price_chart
from astrocalc.universal.workspace import Settings, calculate


def year_end(**changes):
    values=dict(start='2100-12-30T00:00:00Z', end=MAX_TIME.isoformat(),
                selected='2100-12-31T21:00:00Z', bodies=['Saturn'])
    values.update(changes)
    return Settings(**values)


def test_final_instant_all_supported_coordinates_and_bodies():
    for mode in MODES:
        provider=EphemProvider(mode)
        for body in BODIES+('Moon',):
            position=provider.position(body,MAX_TIME)
            assert 0<=position.longitude<360 and math.isfinite(position.speed)
        with pytest.raises(ValueError,match='1900–2100'):
            provider.longitude('Sun',MAX_TIME+timedelta(microseconds=1))


def test_year_end_horizon_events_and_monthly_terminal_anchor():
    settings=year_end(monthly_sample=True)
    result=calculate(settings)
    assert settings.horizon==MAX_TIME and settings.horizon_clipped
    assert max(r['timestamp'] for r in result.positions)==MAX_TIME
    assert all(e.end<=MAX_TIME for e in result.events)
    terminal=next(r for r in result.positions if r['timestamp']==MAX_TIME)
    assert terminal['plot_longitude']==Scale(**settings.scale).coordinate(terminal['unwrapped'])
    assert result.metadata['monthly_terminal_anchor']==MAX_TIME
    assert price_chart(result).layout.xaxis.range[-1]==MAX_TIME
    with pytest.raises(ValueError,match='1900–2100'):
        year_end(end='2101-01-01T00:00:00Z').validate()


def test_cli_pine_export_reaches_last_day(tmp_path):
    config=tmp_path/'workspace.json'
    config.write_text(json.dumps(asdict(year_end())))
    output=tmp_path/'pine'
    assert main(['pine','--config',str(config),'--output',str(output)])==0
    embedded=json.loads((output/'ephemeris.json').read_text())
    assert embedded['metadata']['coverage_end']==int(MAX_TIME.timestamp()*1000)
    assert embedded['metadata']['future_horizon_clipped'] is True
    assert embedded['tables'][0]['timestamps'][-1]==MAX_TIME.timestamp()
    for file in output.glob('*.pine'):
        assert f'int coverageEnd = {int(MAX_TIME.timestamp()*1000)}' in file.read_text()


def test_ui_select_last_supported_day_and_replay():
    from streamlit.testing.v1 import AppTest
    app=Path(__file__).parents[1]/'src/astrocalc/universal/app.py'
    at=AppTest.from_file(str(app),default_timeout=60)
    at.session_state['workspace']=asdict(year_end(start='2100-12-31T00:00:00Z'))
    at.run()
    assert not at.exception
    end=next(widget for widget in at.date_input if widget.label=='End (UTC)')
    assert end.value==date(2100,12,31)
    next(button for button in at.button if button.label=='Calculate').click().run()
    assert not at.exception
    assert instant(at.session_state['workspace']['end'])==MAX_TIME
    next(button for button in at.button if button.label=='Next →').click().run()
    assert not at.exception and at.session_state['replay_day']==date(2100,12,31)
