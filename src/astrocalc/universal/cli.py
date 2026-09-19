"""Local launcher and headless calculation / export command."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from .workspace import Settings,calculate
from .astronomy import EphemProvider,instant
from .geometry import Scale
from .market import MarketSpec,load_prices,book_ranges
from .exports import dumps,bundle,html_chart,save


def main(argv=None):
    p=argparse.ArgumentParser(prog='universal-clock',description='Universal Clock research application and offline exports')
    sub=p.add_subparsers(dest='command',required=True)
    ui=sub.add_parser('ui',help='Launch local Streamlit interface');ui.add_argument('--port',type=int,default=8501)
    for command in ('calculate','chart','pine'):
        q=sub.add_parser(command);q.add_argument('--config',type=Path);q.add_argument('--prices',type=Path)
        q.add_argument('--book-ranges',choices=['sugar_daily','sp_trines_june_1991','sp_trines_march_1992','dow_trines'])
        q.add_argument('--start');q.add_argument('--end');q.add_argument('--bodies',nargs='+');q.add_argument('--unit',type=float)
        q.add_argument('--output',type=Path,required=True);q.add_argument('--overwrite',action='store_true')
        if command=='chart':q.add_argument('--view',choices=['price','clock','zodiac','astronomy'],default='price');q.add_argument('--image',action='store_true')
        if command=='pine':q.add_argument('--error-degrees',type=float,default=.002);q.add_argument('--tick-fraction',type=float,default=.25);q.add_argument('--max-step-hours',type=float,default=24)
    q=sub.add_parser('demo',help='Write a synthetic dataset and example workspace');q.add_argument('--output',type=Path,default=Path('clock-demo'))
    args=p.parse_args(argv)
    if args.command=='ui':
        import subprocess
        script=Path(__file__).with_name('app.py')
        return subprocess.call([sys.executable,'-m','streamlit','run',str(script),'--server.address=127.0.0.1',f'--server.port={args.port}','--browser.gatherUsageStats=false'])
    if args.command=='demo':
        from .demo import synthetic_csv
        s=Settings();s.market.update(symbol='SYNTHETIC sugar-scale demonstration',synthetic=True)
        s.selected='1993-04-19T21:00:00+00:00'
        save(args.output/'synthetic.csv',synthetic_csv());save(args.output/'workspace.json',dumps(s))
        print(args.output.resolve());return 0
    try:
        s=Settings.from_dict(json.loads(args.config.read_text())) if args.config else Settings()
        if args.start:s.start=instant(args.start).isoformat()
        if args.end:s.end=instant(args.end).isoformat();s.selected=s.end
        if args.bodies:s.bodies=args.bodies
        if args.unit is not None:s.scale['unit']=args.unit
        if not args.prices and not args.book_ranges and s.price_file:
            from .bitcoin import local_price_path
            args.prices=local_price_path(s.price_file)
        if args.prices and args.book_ranges:raise ValueError('Select one price source: --prices or --book-ranges')
        data=load_prices(args.prices.read_bytes(),MarketSpec(**s.market),s.column_mapping,parquet=args.prices.suffix=='.parquet') if args.prices else None
        if args.book_ranges:data=book_ranges(args.book_ranges,MarketSpec(**s.market))
        provider=EphemProvider(s.coordinate_mode);result=calculate(s,data,provider)
        if args.command=='calculate':content=bundle(result) if args.output.suffix=='.zip' else dumps(result)
        elif args.command=='chart':
            from .plotting import price_chart,wheel,astronomy_chart
            fig=price_chart(result,data) if args.view=='price' else astronomy_chart(result) if args.view=='astronomy' else wheel(result,data,zodiac=args.view=='zodiac')
            content=fig.to_image(format=args.output.suffix.lstrip('.')) if args.image else html_chart(fig,dict(result.metadata,settings=asdict(s)))
        else:
            from .pine import build_tables,generate_pine
            tables=build_tables(provider,s.bodies,instant(s.start),s.horizon,Scale(**s.scale),MarketSpec(**s.market).tick_size,args.tick_fraction,args.error_degrees,args.max_step_hours)
            overlay,meta=generate_pine(tables,result.events,s,result.metadata)
            pane,_=generate_pine(tables,result.events,s,result.metadata,pane=True)
            save(args.output/'universal_clock_overlay.pine',overlay,args.overwrite)
            save(args.output/'universal_clock_degrees.pine',pane,args.overwrite)
            save(args.output/'ephemeris.json',dumps(dict(tables=[asdict(t) for t in tables],metadata=meta)),args.overwrite)
            print(args.output.resolve());return 0
        print(save(args.output,content,args.overwrite));return 0
    except (ValueError,OSError,RuntimeError) as exc:
        p.exit(2,f'Error: {exc}\n')

if __name__=='__main__':raise SystemExit(main())
