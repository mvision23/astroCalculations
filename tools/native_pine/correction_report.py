"""Rebuild correction fixtures headlessly; see correction-report.md for setup."""
import csv,json,math,hashlib
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime,timezone
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import swisseph as swe
from render_check import DAY,stamp,environment,longitude,build,source_paths,PineArray
from source_harness import PINE
from model import BODIES,delta
from astrocalc.universal.workspace import Settings,calculate
from astrocalc.universal.geometry import Scale
OUT=Path('reports/bitcoin-native');OUT.mkdir(exist_ok=True)
env=environment()
def date(t):return datetime.fromtimestamp(t/1000,timezone.utc)
def write(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2)+'\n')
# Reproduce original diagnostics, not constants used by the indicator.
ref=stamp('2026-09-01');diagnostics={}
for body in (0,9,3,7):
    center=math.floor((100000-env['f_price'](env['f_q'](longitude(body,ref)),0,False))/8856+.5)
    observations=[(t,env['f_price'](env['f_q'](longitude(body,t)),center,False)) for t in range(ref-365*DAY,ref+1,DAY)]
    positive=[(t,p) for t,p in observations if p>0]
    minimum=min(positive,key=lambda row:row[1])
    diagnostics[BODIES[body]]=dict(k=center,reference_price=observations[-1][1],minimum_positive_price=minimum[1],minimum_date=date(minimum[0]).isoformat())
# Compare actual headless application output, not a new imitation of the app.
s=Settings(start='2025-06-05T00:00:00+00:00',end='2025-07-05T00:00:00+00:00',selected='2025-07-05T00:00:00+00:00',bodies=list(BODIES),scale=asdict(Scale(unit=369)),low=70000,high=125000,step_hours=6,future_days=0,halfway=False,adjoining=False)
app=calculate(s,include_events=False)
lookup={(r['body'],r['timestamp'],r['k'],r['opposite']):r['low'] for r in app.levels if 'body' in r}
windings={};rows=[];app_errors=defaultdict(list);model_errors=defaultdict(list);price_errors=defaultdict(list)
ids=[swe.SUN,swe.MERCURY,swe.VENUS,swe.MARS,swe.JUPITER,swe.SATURN,swe.URANUS,swe.NEPTUNE,swe.PLUTO,swe.MOON]
for pos in app.positions:
    body=BODIES.index(pos['body']);t=int(pos['timestamp'].timestamp()*1000);lon=longitude(body,t)
    m=windings.setdefault(pos['body'],round((lon-pos['unwrapped'])/360))
    aligned=pos['unwrapped']+360*m
    reference=swe.calc(env['f_day'](t)+2451543.5,ids[body],swe.FLG_MOSEPH|swe.FLG_TRUEPOS|swe.FLG_NONUT)[0][0]
    app_errors[pos['body']].append(lon-aligned);model_errors[pos['body']].append(delta(lon,reference))
    q=env['f_q'](lon)
    for side in (False,True):
        k=env['f_selected_k'](q,70000,125000,1,0,0,side);ak=k+15*m
        price=env['f_price'](q,k,side);app_price=lookup[(pos['body'],pos['timestamp'],ak,side)]
        price_errors[pos['body']].append(price-app_price)
        rows.append(dict(utc=pos['timestamp'].isoformat(),body=pos['body'],wrapped=lon%360,canonical=lon,speed=env['f_speed'](body,t),q=q,k=k,opposite=side,price=price,reference_wrapped=reference,reference_error_deg=delta(lon,reference),app_wrapped=pos['longitude'],app_unwrapped=pos['unwrapped'],winding_m=m,app_aligned=aligned,app_k=ak,app_price=app_price,price_difference=price-app_price))
with (OUT/'correction-comparison.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
comparisons={body:dict(winding_m=windings[body],app_max_deg=max(map(abs,app_errors[body])),app_rms_deg=math.sqrt(sum(x*x for x in app_errors[body])/len(app_errors[body])),matching_reference_max_deg=max(map(abs,model_errors[body])),book_max_price_difference=max(map(abs,price_errors[body]))) for body in BODIES}
# Resource examples include optional Moon, >3 Mars/Neptune, and >one lunar revolution.
cases=[('default_nine_full_history',6452,7,dict.fromkeys(range(9),1)),('all_ten_full_history',6452,7,dict.fromkeys(range(10),1)),('dense_mars_neptune',6452,7,{3:8,7:8}),('sun_moon_full_history',6452,7,{0:3,9:3}),('default_nine_120_future',120,120,dict.fromkeys(range(9),1)),('dense_mars_neptune_120_future',120,120,{3:8,7:8}),('sun_700_future',120,700,{0:1}),('mars_neptune_700_future',120,700,{3:1,7:1})]
resources={}
for name,h,f,counts in cases:
    a=ref-h*DAY;b=ref+f*DAY
    paths,stats,samples=build(a,ref,b,counts)
    actual,vertices=source_paths(a,ref,b,counts)
    assert paths==actual and vertices==stats['vertices']
    resources[name]=dict(stats,start=date(a).isoformat(),split=date(ref).isoformat(),end=date(b).isoformat(),counts={BODIES[k]:n for k,n in counts.items()},source_builder_matches=True)
# Empirical interpolation checks: quarter/mid/three-quarter interval samples,
# including all ten bodies. Separate smooth rendering error from book jumps.
render_errors={}
for body in range(10):
    h=math.floor(env['f_sample_hours'](body)*3600000);errors=[];steps=[]
    for t in range(stamp('2024-01-01'),stamp('2027-01-01'),DAY):
        a=longitude(body,t);b=longitude(body,t+h);steps.append(abs(b-a))
        for fraction in (.25,.5,.75):errors.append(abs(longitude(body,t+int(h*fraction))-(a+(b-a)*fraction)))
    render_errors[BODIES[body]]=dict(sample_hours=h/3600000,max_step_deg=max(steps),max_interpolation_deg=max(errors),max_interpolation_price=max(errors)*369)
# Figures use shared fixture assumptions, not guessed screenshot metadata.
cut=stamp('2025-07-05');begin=cut-30*DAY;end=cut+7*DAY
prices=[]
with Path('data/bitcoin_universal.csv').open() as f:
    for r in csv.DictReader(f):
        t=stamp(r['timestamp'].replace('Z','+00:00'))
        if begin<=t<=end:prices.append((date(t),float(r['close'])))
colors={0:'#d29400',3:'#d94b4b',7:'#1b8c97',9:'#7979ab'}
figure_stats={}
for title,counts in [('mars-neptune',{3:8,7:8}),('sun-moon',{0:3,9:3})]:
    paths,stats,_=build(begin,cut,end,counts)
    actual,_=source_paths(begin,cut,end,counts);assert actual==paths
    figure_stats[title]=stats
    # Use actual app's default apparent frame and headless calculator on a fine grid.
    app_settings=Settings(start=date(begin).isoformat(),end=date(cut).isoformat(),selected=date(cut).isoformat(),bodies=[BODIES[b] for b in counts],scale=asdict(Scale(unit=369)),low=70000,high=125000,step_hours=.25,future_days=7,halfway=False,adjoining=False)
    app_result=calculate(app_settings,include_events=False)
    app_groups=defaultdict(list)
    initial={}
    app_keys={}
    for row in app_result.positions:
        b=BODIES.index(row['body']);t=int(row['timestamp'].timestamp()*1000)
        m=initial.setdefault(b,round((longitude(b,t)-row['unwrapped'])/360))
        q=env['f_q'](row['unwrapped']+m*360)
        # Match daily historical chart samples; futures use the app's fine grid.
        if t <= cut and t % DAY != 0:continue
        for side in (False,True):
            keys=app_keys.setdefault((b,side),PineArray([math.nan]*counts[b]))
            env['f_replenish'](keys,q,70000,125000,counts[b],0,side)
            for k in keys:
                if not math.isnan(k):app_groups[(b,k,side)].append((t,env['f_price'](q,k,side)))
    fig,axes=plt.subplots(1,3,figsize=(18,5.3),sharex=True)
    for ax,mode in zip(axes,['Native · linear','App apparent-of-date · linear','Native · logarithmic']):
        if mode.startswith('App'):
            for (b,k,side),points in app_groups.items():
                # Split any selection gap, not just NaNs at the chart edges.
                pieces=[[]]
                for t,y in points:
                    if pieces[-1] and t-pieces[-1][-1][0]>(DAY if t<=cut else 900000):pieces.append([])
                    pieces[-1].append((t,y))
                for piece in pieces:
                    ax.step([date(t) for t,y in piece],[y for t,y in piece],where='post',color=colors[b],alpha=.3 if side else .8,lw=.8)
        else:
            for p in paths:ax.plot([date(t) for t,y in p.points],[y for t,y in p.points],color=colors[p.body],alpha=.3 if p.side else .85,lw=.8,ls='--' if p.future else '-')
        if 'logarithmic' in mode:ax.set_yscale('log')
        if prices:ax.plot(*zip(*prices),color='#17202a',lw=1.8,label='Supplied BTC close (history)')
        ax.set_ylim(70000,125000);ax.set_xlim(date(begin),date(end));ax.axvline(date(cut),color='#555555',ls=':',lw=.8)
        ax.set_title(mode);ax.grid(alpha=.15);ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'));ax.tick_params(axis='x',rotation=25)
    axes[0].set_ylabel('Quote units per BTC');axes[0].legend(fontsize=8)
    fig.suptitle(f'{title}: 2025-06-05 to 2025-07-12 UTC · u=369 · book · band 70,000–125,000\nUnanchored; keep/replenish branches. Daily history; fine future. App frame differs. Future begins July 5.')
    fig.tight_layout();fig.savefig(OUT/f'{title}-comparison.png',dpi=150);plt.close(fig)
# Strong scale counterexample reproduces near-zero old solar branch, identical prices.
center=diagnostics['Sun']['k'];points=[(t,env['f_price'](longitude(0,t),center,False)) for t in range(stamp('2025-11-24'),ref+1,DAY)]
fig,axes=plt.subplots(1,2,figsize=(12,4))
for ax,mode in zip(axes,['linear','log']):
    ax.plot([date(t) for t,p in points],[p for t,p in points],color='#c89900');ax.set_yscale(mode);ax.set_title('Same native solar prices · '+mode);ax.grid(alpha=.2);ax.tick_params(axis='x',rotation=25)
fig.tight_layout();fig.savefig(OUT/'same-prices-linear-log.png',dpi=150);plt.close(fig)
# Multi-year history has no drawing/day cap; use a dense family like webapp.png.
long_start=stamp('2022-01-01');long_split=stamp('2026-09-01')
fig,axes=plt.subplots(2,1,figsize=(15,8),sharex=True)
for ax,counts,title in zip(axes,[{3:8,7:8},{0:3,9:3}],['Mars / Neptune: 8 mains each, plus opposites','Sun / Moon: 3 mains each, plus opposites']):
    paths,stats,_=build(long_start,long_split,long_split+7*DAY,counts)
    for path in paths:
        ax.plot([date(t) for t,y in path.points],[y for t,y in path.points],color=colors[path.body],alpha=.23 if path.side else .65,lw=.55)
    ax.set_ylim(70000,125000);ax.set_title(title);ax.set_ylabel('Quote units / BTC');ax.grid(alpha=.15)
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.suptitle('Full loaded history with stable, replenished branches · daily bars · 70,000–125,000 · u=369')
fig.tight_layout();fig.savefig(OUT/'full-history-replenishment.png',dpi=150);plt.close(fig)
write('correction-numerics.json',dict(source_sha256=hashlib.sha256(PINE.read_bytes()).hexdigest(),diagnostics=diagnostics,app_interval=[s.start,s.end],app_metadata=app.metadata['astronomy'],comparison= comparisons,render_errors=render_errors,resources=resources,figure_resources=figure_stats,pine_compiled=False,pine_runtime_verified=False))
print(json.dumps(dict(diagnostics=diagnostics,resources=resources,render_errors=render_errors),indent=2))
