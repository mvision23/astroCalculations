from dataclasses import asdict
import json,io,zipfile
from astrocalc.universal.workspace import Settings,calculate
from astrocalc.universal.market import MarketSpec,load_prices
from astrocalc.universal.demo import synthetic_csv
from astrocalc.universal.plotting import price_chart,astronomy_chart,wheel,calendar_rows
from astrocalc.universal.exports import dumps,bundle,html_chart
from astrocalc.universal.geometry import Scale
from astrocalc.universal.astronomy import instant


def test_local_workflow_chart_wheel_config_export(tmp_path):
    s=Settings(bodies=['Jupiter'],start='1993-03-15T00:00:00Z',end='1993-03-26T00:00:00Z',selected='1993-03-22T21:00:00Z',future_days=3)
    s.market['synthetic']=True
    s.column_mapping={'timestamp':'date','close':'close'}
    data=load_prices(synthetic_csv(),MarketSpec(**s.market))
    result=calculate(s,data)
    saved=tmp_path/'workspace.json';saved.write_text(dumps(s))
    assert asdict(Settings.from_dict(json.loads(saved.read_text())))==asdict(s)
    row=next(r for r in result.positions if r['timestamp']==instant(s.selected))
    candidates=[l for l in result.levels if l['timestamp']==instant(s.selected) and l.get('body')]
    assert all(l['low']==Scale(**s.scale).price(row['unwrapped'],l['k'],l['opposite']) for l in candidates)
    figures=[price_chart(result,data),astronomy_chart(result),wheel(result,data),wheel(result,data,zodiac=True)]
    for fig in figures:
        text=html_chart(fig,result.metadata)
        assert 'plotly.js' in text and 'Research provenance' in text
        assert len(fig.data)>0
    with zipfile.ZipFile(io.BytesIO(bundle(result))) as archive:
        assert {'positions.csv','events.csv','levels.csv','matches.csv','metadata.json'}<=set(archive.namelist())
        metadata=json.loads(archive.read('metadata.json'))
        assert metadata['input_checksum']==data.checksum and metadata['synthetic'] is True
    assert len(calendar_rows(result.events,'1993-03'))==31


def test_streamlit_default_astronomy_only():
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    app=Path(__file__).parents[1]/'src/astrocalc/universal/app.py'
    at=AppTest.from_file(str(app),default_timeout=60).run()
    assert not at.exception
    assert at.title[0].value=='Universal Clock'
    assert len(at.tabs)==7
    at.button(key=None) if False else None
    next_button=next(b for b in at.button if b.label=='Next →')
    before=at.session_state['replay_day'];next_button.click().run()
    assert not at.exception and at.session_state['replay_day']>before
