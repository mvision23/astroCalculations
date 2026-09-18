import pytest
from astrocalc.universal.geometry import *

def test_book_arithmetic():
    assert rounded(305+51/60)==306
    dow=Scale(10)
    assert {3060,3300}<={x['price'] for x in dow.ladder(305.85,2800,3500)}
    pound=Scale(.01)
    assert pound.price(304,-6)==pytest.approx(1.60)
    assert pound.price(304,-5)==pytest.approx(1.84)
    assert pound.price(304,-6,True)==pytest.approx(1.72)
    sugar=Scale(.1)
    assert sugar.price(191,-3)==pytest.approx(11.9)
    assert sugar.price(191,-3,True)==pytest.approx(13.1)
    assert [x%24 for x in [98,194,290]]==[2,2,2]

def test_rounding_labels_wrap_and_units():
    assert [rounded(x) for x in (1.49,1.5,2.5,359.5)]==[1,2,3,360]
    assert label_position(24)==(0,352.5)
    assert label_position(25)==(1,7.5)
    assert Scale(.01).price(500)==pytest.approx(Scale(1).price(500)/100)
    assert Scale(1,rounding='continuous').price(360.1,-15)==pytest.approx(.1)
    assert band_contains(144) and band_contains(145) and not band_contains(145.001)
    assert band_contains(360) and not band_contains(359.999)
    assert BOOK_BANDS[-1]==(336,337)
    assert price_label(.035,.01)==.03

def test_intervals_and_static_bands():
    assert project_interval(23,26)==[(23,24),(0,2)]
    assert project_interval(0,24)==[(0,24)]
    assert wheel_overlap((23,26),(1,3))
    assert wheel_overlap((23,24),(0,1))
    assert intersects((1,2),(2,3)) and overlap((1,2),(2,3))==0
    bands=static_bands(Scale(.01),1.6,1.7,True,True)
    assert any(b['kind']=='A' and b['low']==pytest.approx(1.68) and b['high']==pytest.approx(1.69) for b in bands)
    assert any(b['kind']=='halfway' and b['low']==pytest.approx(1.655) for b in bands)
    assert any(b.get('side')=='support' and b['low']==pytest.approx(1.655) and b['high']==pytest.approx(1.68) for b in bands)
    assert not intersects((599,609),(557,565)) and wheel_overlap((599,609),(557,565))

@pytest.mark.parametrize('args',[{'unit':0},{'unit':-1},{'unit':float('nan')},{'rounding':'bankers'}])
def test_invalid_scales(args):
    with pytest.raises(ValueError):Scale(**args)
