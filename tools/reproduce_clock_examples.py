"""Regenerate examples locally; add --images with Kaleido and Chrome installed."""
import argparse
from dataclasses import asdict
from pathlib import Path

from astrocalc.universal.astronomy import EphemProvider, instant
from astrocalc.universal.demo import synthetic_csv
from astrocalc.universal.exports import dumps, bundle, html_chart
from astrocalc.universal.geometry import Scale
from astrocalc.universal.market import MarketSpec, book_ranges
from astrocalc.universal.methods import PRESETS
from astrocalc.universal.pine import build_tables, generate_pine
from astrocalc.universal.plotting import price_chart, wheel
from astrocalc.universal.workspace import Settings, calculate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('samples'))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    s = Settings()
    s.market.update(synthetic=True, symbol='SYNTHETIC sugar-scale demonstration')
    s.selected = '1993-04-19T21:00:00Z'
    (out / 'synthetic.csv').write_text(synthetic_csv())
    (out / 'workspace.json').write_text(dumps(s))

    sugar = Settings(start='1993-03-17T00:00:00Z', end='1993-04-20T00:00:00Z',
                     selected='1993-04-19T21:00:00Z', future_days=7)
    sugar.bodies = PRESETS['Sugar']['bodies']
    sugar.scale['quote_units'] = 'cents/lb'
    sugar.market.update(symbol='Book sugar: selected low/high only', quote_units='cents/lb')
    (out / 'sugar-book.json').write_text(dumps(sugar))
    for name, start, end in [('october-1987', '1987-10-01', '1987-11-01'),
                             ('december-1993', '1993-12-01', '1994-01-01')]:
        cfg = Settings(start=start+'T00:00:00Z', end=end+'T00:00:00Z', selected=start+'T12:00:00Z',
                       bodies=sugar.bodies, future_days=0)
        (out / (name+'.json')).write_text(dumps(cfg))
    dow = Settings(start='1992-01-01T00:00:00Z', end='1993-01-01T00:00:00Z',
                   selected='1992-06-01T00:00:00Z', bodies=['Saturn'], pair=['Sun','Jupiter'],
                   low=2400, high=3600, future_days=0, monthly_sample=True, preset='Dow')
    dow.scale.update(unit=10, quote_units='index points')
    (out / 'saturn-dow-monthly.json').write_text(dumps(dow))

    # A compact export configuration includes Mercury's two stations and zodiac wrap.
    pine_settings = Settings(start='1993-02-20T00:00:00Z', end='1993-04-20T00:00:00Z',
                             selected='1993-04-19T21:00:00Z', bodies=['Jupiter','Mercury'],
                             low=11, high=13.5, future_days=10)
    pine_settings.scale['quote_units'] = 'cents/lb'
    (out / 'pine-workspace.json').write_text(dumps(pine_settings))
    provider = EphemProvider()
    result = calculate(pine_settings, provider=provider)
    tables = build_tables(provider, pine_settings.bodies, instant(pine_settings.start),
                          pine_settings.horizon,
                          Scale(**pine_settings.scale), error_degrees=.001)
    pine_dir = out / 'pine'
    pine_dir.mkdir(exist_ok=True)
    for pane, name in [(False, 'overlay'), (True, 'degrees')]:
        source, metadata = generate_pine(tables, result.events, pine_settings, result.metadata, pane)
        if not pane:overlay_metadata=metadata
        (pine_dir / f'universal_clock_{name}.pine').write_text(source)
    (pine_dir / 'ephemeris.json').write_text(dumps(dict(tables=[asdict(t) for t in tables], metadata=overlay_metadata)))
    print('Generated both Pine indicators and independent interpolation measurements', flush=True)

    data = book_ranges('sugar_daily', MarketSpec(**sugar.market))
    result = calculate(sugar, data)
    metadata = dict(result.metadata, settings=asdict(sugar))
    chart = price_chart(result, data)
    (out / 'sugar-price.html').write_text(html_chart(chart, metadata))
    (out / 'sugar-results.zip').write_bytes(bundle(result))
    if args.images:
        chart.write_image(out / 'sugar-price.png', width=1400, height=800, scale=1)
        clock = wheel(result, data, dates=['1993-03-17','1993-04-19'])
        clock.write_image(out / 'sugar-clock.png', width=1100, height=1000, scale=1)
    print(f'Examples written to {out.resolve()}', flush=True)


if __name__ == '__main__':
    main()
