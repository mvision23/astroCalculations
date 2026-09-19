from datetime import date
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from astrocalc.universal.astronomy import instant
from astrocalc.universal.bitcoin import normalize_bitcoin,bitcoin_market,local_price_path
from astrocalc.universal.geometry import Scale
from astrocalc.universal.market import load_prices,session_range,event_ranges
from astrocalc.universal.methods import contacts,ContactSettings
from astrocalc.universal.research import ladder_hit,holm,bootstrap_improvement,ridge_predict,turning_points

SOURCE=b'Start,End,Open,High,Low,Close,Volume,Market Cap\n2025-07-04,2025-07-05,109618,109737,107274,108023,45491863018.5993,2158317661288.68\n2025-07-03,2025-07-04,108974,110443,108561,109580,59640164758.3972,2176269493513.92\n'


def test_normalization_keeps_prices_and_delays_availability():
    content,report=normalize_bitcoin(SOURCE)
    data=load_prices(content,bitcoin_market())
    assert report['rows']==2 and report['filled_rows']==0 and report['missing_dates']==[]
    assert data.frame.timestamp.iloc[0]==instant('2025-07-03T00:00:00Z')
    assert data.frame.available_at.iloc[0]==instant('2025-07-04T00:00:00Z')
    assert len(data.completed(instant('2025-07-03T23:59:59Z')))==0
    assert data.frame.close.tolist()==[109580,108023]
    assert data.frame.high.tolist()==[110443,109737]
    spec=bitcoin_market()
    for stamp in ['2025-07-03T00:00:00Z','2025-07-03T12:00:00Z']:
        assert spec.assign(instant(stamp),'strict')==date(2025,7,4)
    assert session_range(data,date(2025,7,4),instant('2025-07-04T00:00:00Z'))['high']==110443
    ranges=event_ranges(data,instant('2025-07-03T12:00:00Z'),instant('2025-07-04T00:00:00Z'),'strict',1)
    assert [r['session'] for r in ranges['expanded']]==['2025-07-03','2025-07-04','2025-07-05']
    assert ranges['expanded'][1]['range']==ranges['strict']
    assert ranges['expanded'][2]['range'] is None  # Tomorrow's candle is not available.


def test_ladder_hit_matches_shared_scale_and_369_step():
    scale=Scale(369)
    assert scale.price(191,1)-scale.price(191,0)==8856
    assert scale.price(191,0,True)-scale.price(191,0)==4428
    for lon in [0.,23.5,191.,359.7]:
        for low,high in [(1,10),(70000,71000),(100000,110000)]:
            for opposite in [False,True]:
                assert bool(ladder_hit(low,high,lon,opposite=opposite))==bool(scale.ladder(lon,low,high,opposite))


def test_research_statistics_and_no_future_training():
    assert holm([.01,.04,.03]).tolist()==pytest.approx([.03,.06,.06])
    assert bootstrap_improvement([1.,2.,3.])['p'] is None
    x=np.arange(100,dtype=float).reshape(-1,1);y=2*x[:,0]
    train=np.arange(100)<50;test=~train
    expected=ridge_predict(x,y,train,test)
    y[test]=1e9
    assert np.array_equal(ridge_predict(x,y,train,test),expected)
    assert turning_points([2,1,3,2,4],1).tolist()==[1,2,3]


def test_static_interval_contacts_match_explicit_rows():
    data=load_prices(SOURCE.replace(b'Start,End,Open,High,Low,Close,Volume,Market Cap',b'timestamp,end,open,high,low,close,volume,market_cap'),bitcoin_market())
    times=list(data.frame.timestamp)
    template=dict(id='A',low=109000,high=109369,method='UC06-DIV')
    expanded=[dict(timestamp=t,**template) for t in times]
    compact=[dict(timestamp=times[0],valid_from=times[0],valid_until=times[-1],**template)]
    asof=instant('2025-07-06T00:00:00Z')
    assert contacts(data,compact,Scale(369),asof,ContactSettings())==contacts(data,expanded,Scale(369),asof,ContactSettings())


def test_local_dataset_cannot_escape_data_directory():
    with pytest.raises(ValueError):local_price_path('../pyproject.toml')
    with pytest.raises(ValueError):local_price_path('../../private.csv')


def test_bitcoin_workspace_loads_local_prices_in_app():
    from streamlit.testing.v1 import AppTest
    root=Path(__file__).parents[1]
    if not (root/'data/bitcoin-workspaces/short.json').exists():pytest.skip('Reproduce Bitcoin workspaces first')
    at=AppTest.from_file(str(root/'src/astrocalc/universal/app.py'),default_timeout=120).run()
    next(b for b in at.button if b.label=='Load Bitcoin · $369').click().run()
    assert not at.exception
    settings=at.session_state['workspace']
    assert settings['scale']['unit']==369 and settings['price_file']=='bitcoin_universal.csv'
    assert settings['market']['calendar']=='24/7' and settings['market']['timezone']=='UTC'
    assert any(m.label=='Observed price bars' and int(m.value)>5000 for m in at.metric)
