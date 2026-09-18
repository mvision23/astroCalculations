"""Book wheel formalization. Label centering never changes price coordinates."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
import math

BOOK_BANDS = tuple((n,n+1) for n in range(0,360,24))

def finite(*values):
    if not all(math.isfinite(v) for v in values): raise ValueError('Values must be finite')

def rounded(value):
    """Nearest integer; exact half-degree ties toward increasing longitude."""
    finite(value)
    return math.floor(value+.5)

def price_label(price,unit):
    """Printed p61: nearest outer-wheel number, exact half-step ties downward."""
    finite(price,unit)
    if unit<=0:raise ValueError('Unit must be positive')
    coordinate=Decimal(str(price))/Decimal(str(unit))-Decimal('0.5')
    return float(coordinate.to_integral_value(rounding=ROUND_CEILING)*Decimal(str(unit)))

def label_position(n):
    if not isinstance(n,int) or not 1<=n<=360: raise ValueError('Label must be 1–360')
    return (n-1)//24, ((n-1)%24+.5)*15

def band_contains(lon):
    """Closed book bands; 360 is identified with zero."""
    finite(lon)
    return lon%24 <= 1

def project_interval(low,high,cycle=24):
    finite(low,high,cycle)
    if high<low or cycle<=0: raise ValueError('Require low <= high and positive cycle')
    if high-low>=cycle: return [(0.,cycle)]
    a=low%cycle;b=a+high-low
    # A closed endpoint at one full turn is also the origin.
    return [(a,b)] if b<cycle else [(a,cycle),(0.,b-cycle)]

def overlap(a,b):
    return max(0.,min(a[1],b[1])-max(a[0],b[0]))

def intersects(a,b):
    return max(a[0],b[0])<=min(a[1],b[1])

def wheel_overlap(a,b,cycle=24):
    return any(intersects(x,y) for x in project_interval(*a,cycle) for y in project_interval(*b,cycle))

@dataclass(frozen=True)
class Scale:
    unit: float = .1
    rounding: str = 'book'
    quote_units: str = 'quoted units'
    anchor_price: float = 0
    anchor_longitude: float = 0
    anchored: bool = False

    def __post_init__(self):
        finite(self.unit,self.anchor_price,self.anchor_longitude)
        if self.unit<=0: raise ValueError('Price units per step must be positive')
        if self.rounding not in ('book','continuous'): raise ValueError('Rounding must be book or continuous')

    def coordinate(self,lon):
        return rounded(lon) if self.rounding=='book' else lon

    def price(self,lon,k=0,opposite=False):
        return (self.anchor_price if self.anchored else 0)+self.unit*(self.coordinate(lon)-(self.anchor_longitude if self.anchored else 0)+24*k+(12 if opposite else 0))

    def branches(self,longitudes,low,high,margin=0,opposite=False):
        finite(low,high,margin)
        if high<low or margin<0: raise ValueError('Invalid price range/margin')
        values=[self.price(l,0,opposite) for l in longitudes]
        if not values: return []
        first=math.ceil((low-margin-max(values))/(24*self.unit))
        last=math.floor((high+margin-min(values))/(24*self.unit))
        if last-first>1000: raise ValueError('More than 1000 branches; narrow price range or increase scale')
        return list(range(first,last+1))

    def ladder(self,lon,low,high,opposite=False):
        return [dict(k=k,price=self.price(lon,k,opposite),opposite=opposite) for k in self.branches([lon],low,high,opposite=opposite)]


def static_bands(scale,low,high,halfway=True,adjoining=False):
    """A–D closed one-unit bands; halfway lines and adjoining areas are source-audited."""
    if high<low: raise ValueError('Invalid range')
    first=math.floor(low/(24*scale.unit))-1;last=math.ceil(high/(24*scale.unit))+1
    if last-first>1000: raise ValueError('Too many static bands; narrow range')
    result=[]
    for k in range(first,last+1):
        for name,offset in zip('ABCD',(0,6,12,18)):
            a=scale.unit*(24*k+offset);b=a+scale.unit
            if b>=low and a<=high: result.append(dict(id=f'{name}:{k}',kind=name,low=a,high=b,method='UC06-DIV'))
        if halfway:
            # Chart 16D: halfway through the open gap between one-unit bands,
            # e.g. (1.63 + 1.68)/2 = 1.655, not a universal tolerance orb.
            for offset in (3.5,9.5,15.5,21.5):
                a=scale.unit*(24*k+offset)
                if low<=a<=high: result.append(dict(id=f'H{offset}:{k}',kind='halfway',low=a,high=a,method='UC06-HALF'))
        if adjoining:
            for offset in (0,6,12,18):
                for side,left,right in [('support',offset-2.5,offset),('resistance',offset+1,offset+3.5)]:
                    a=scale.unit*(24*k+left);b=scale.unit*(24*k+right)
                    if b>=low and a<=high:
                        result.append(dict(id=f'{side}{offset}:{k}',kind='adjoining',low=a,high=b,method='UC06-AREA',side=side))
    return result
