"""Reproducible, chronological Bitcoin research; no assumed planetary causality."""
from dataclasses import asdict
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path
import hashlib
import json
import math
import zipfile

import numpy as np
import pandas as pd

from .astronomy import BODIES, EphemProvider, instant, series
from .bitcoin import UNIT, bitcoin_market, normalize_bitcoin
from .events import Event, aspects, body_events, combinations as occupancy_combinations
from .exports import dumps
from .geometry import Scale
from .methods import compare_events, evaluation
from .market import load_prices
from .workspace import Settings

ALL_BODIES=BODIES+('Moon',)
HORIZONS={'short':7,'intermediate':90,'long':365}
PROTOCOL=dict(version=1,unit=UNIT,cycle=24*UNIT,opposite=12*UNIT,
              analysis_start='2014-01-01',train_end='2019-01-01',validation_end='2022-01-01',
              horizons=HORIZONS,pivot_half_windows={'short':7,'intermediate':30,'long':180},
              pivot_event_windows={'short':2,'intermediate':7,'long':30},
              ridge_penalty=10.,bootstrap_replicates=1999,bootstrap_block=2,seed=369,
              minimum_nonoverlap_cases=20,holm_family=30,
              selection='Rank single-body increments by validation MSE skill, then evaluate frozen choices on 2022 onward.',
              channel_tolerance_usd=0.,channel_controls=239,
              phase_features='Longitude and 24-degree phase harmonics, speed, retrograde, band occupancy, closed-price phase relative to direct/opposite ladders.',
              caveat='Observational extension, not a deterministic book rule. Test ranks are descriptive; the validation winner is the preselected candidate.')


def records(frame):
    return json.loads(frame.to_json(orient='records',date_format='iso'))


def write_table(path,frame):
    frame.to_csv(path,index=False)


def ridge_predict(x,y,train,evaluate,penalty=10.):
    mean=x[train].mean(axis=0);sd=x[train].std(axis=0)
    sd=np.where(sd>1e-10,sd,1.)
    transform=lambda a:np.column_stack([np.ones(len(a)),np.clip((a-mean)/sd,-5,5)])
    a=transform(x[train]);b=transform(x[evaluate])
    regularizer=np.eye(a.shape[1])*penalty;regularizer[0,0]=0
    beta=np.linalg.solve(a.T@a+regularizer,a.T@y[train])
    return b@beta


def bootstrap_improvement(differences,seed=369):
    """Circular two-case blocks of already non-overlapping forecast losses."""
    differences=np.asarray(differences);n=len(differences)
    if n<PROTOCOL['minimum_nonoverlap_cases']:
        return dict(p=None,ci_low=None,ci_high=None)
    rng=np.random.default_rng(seed)
    starts=rng.integers(n,size=(PROTOCOL['bootstrap_replicates'],math.ceil(n/2)))
    indices=np.stack([starts,(starts+1)%n],axis=-1).reshape(len(starts),-1)[:,:n]
    means=differences[indices].mean(axis=1)
    # Bootstrap under the centered null. Monte Carlo +1 prevents zero p-values.
    p=(1+np.count_nonzero(means-differences.mean()>=differences.mean()))/(len(means)+1)
    return dict(p=float(p),ci_low=float(np.quantile(means,.025)),ci_high=float(np.quantile(means,.975)))


def holm(pvalues):
    values=np.asarray([1. if p is None else p for p in pvalues],float)
    order=np.argsort(values);adjusted=np.maximum.accumulate(values[order]*(len(values)-np.arange(len(values))))
    result=np.empty(len(values));result[order]=np.minimum(1,adjusted)
    return result


def baseline_features(close):
    log=pd.Series(np.log(close));r=log.diff()
    features=[log.diff(k).to_numpy() for k in (7,30,90,365)]
    features.append(r.rolling(30).std().to_numpy())
    days=np.arange(len(close),dtype=float)
    features.extend([days/365.2425,np.sin(2*np.pi*days/365.2425),np.cos(2*np.pi*days/365.2425),
                     np.sin(2*np.pi*days/7),np.cos(2*np.pi*days/7)])
    return np.column_stack(features)


def body_features(longitude,speed,close):
    phi=longitude*2*np.pi/360;clock=longitude*2*np.pi/24
    price_phase=(close/UNIT-np.floor(longitude+.5))*2*np.pi/24
    return np.column_stack([np.sin(phi),np.cos(phi),np.sin(clock),np.cos(clock),speed,
                            speed<0,longitude%24<=1,np.sin(price_phase),np.cos(price_phase),
                            np.sin(2*price_phase),np.cos(2*price_phase)])


def forecast_study(frame,positions):
    close=frame.close.to_numpy();n=len(frame);times=pd.DatetimeIndex(frame.available_at)
    base=baseline_features(close);log=np.log(close);rows=[];prediction_rows=[]
    valid=np.isfinite(base).all(axis=1)&(times>=PROTOCOL['analysis_start'])
    for term,h in HORIZONS.items():
        y=np.full(n,np.nan);y[:-h]=log[h:]-log[:-h]
        target_times=times+pd.Timedelta(days=h)
        train=valid&np.isfinite(y)&(target_times<pd.Timestamp(PROTOCOL['train_end'],tz='UTC'))
        validation=valid&np.isfinite(y)&(times>=PROTOCOL['train_end'])&(target_times<pd.Timestamp(PROTOCOL['validation_end'],tz='UTC'))
        fit_final=valid&np.isfinite(y)&(target_times<pd.Timestamp(PROTOCOL['validation_end'],tz='UTC'))
        test=valid&np.isfinite(y)&(times>=PROTOCOL['validation_end'])
        idx=np.flatnonzero(test);nonoverlap=np.arange(0,len(idx),h)
        base_val=ridge_predict(base,y,train,validation)
        base_test=ridge_predict(base,y,fit_final,test)
        zero_loss=float(np.mean(y[test]**2))
        baseline_loss=float(np.mean((base_test-y[test])**2))
        for body in ALL_BODIES:
            p=positions[body]
            x=np.column_stack([base,body_features(p.longitude.to_numpy(),p.speed.to_numpy(),close)])
            pv=ridge_predict(x,y,train,validation);pt=ridge_predict(x,y,fit_final,test)
            vl=float(np.mean((pv-y[validation])**2));bl=float(np.mean((base_val-y[validation])**2))
            loss=(pt-y[test])**2;difference=(base_test-y[test])**2-loss
            stat=bootstrap_improvement(difference[nonoverlap])
            rows.append(dict(term=term,horizon_days=h,body=body,extension=body=='Moon',train_cases=int(train.sum()),
                             validation_cases=int(validation.sum()),test_cases=len(idx),nonoverlap_cases=len(nonoverlap),
                             validation_skill=1-vl/bl,test_skill=1-float(loss.mean())/baseline_loss,
                             test_rmse_logreturn=float(np.sqrt(loss.mean())),baseline_rmse=float(np.sqrt(baseline_loss)),
                             zero_return_rmse=float(np.sqrt(zero_loss)),nonoverlap_mean_loss_gain=float(difference[nonoverlap].mean()),
                             **stat))
            for j in range(len(idx)):
                prediction_rows.append(dict(term=term,body=body,timestamp=times[idx[j]],target_time=target_times[idx[j]],
                                            actual_log_return=y[idx[j]],baseline=base_test[j],prediction=pt[j],nonoverlap=j%h==0))
    results=pd.DataFrame(rows)
    results['holm_p']=holm([None if pd.isna(v) else v for v in results.p])
    results['validation_rank']=results.groupby('term').validation_skill.rank(ascending=False,method='min').astype(int)
    results['supported']=(results.validation_rank==1)&(results.validation_skill>0)&(results.test_skill>0)&(results.holm_p<.05)&(results.nonoverlap_cases>=20)
    return results,pd.DataFrame(prediction_rows)


def ladder_hit(low,high,longitude,offset=0.,opposite=False):
    """Existence of an intersecting fixed ladder branch; never splices trajectories."""
    origin=UNIT*(np.floor(longitude+.5)+(12 if opposite else 0)+offset)
    return np.ceil((low-origin)/(24*UNIT))<=np.floor((high-origin)/(24*UNIT))


def channel_study(frame,positions):
    low=frame.low.to_numpy();high=frame.high.to_numpy();times=pd.DatetimeIndex(frame.available_at)
    rows=[];rng=np.random.default_rng(369);offsets=rng.uniform(0,24,PROTOCOL['channel_controls'])
    for body in ALL_BODIES:
        # Positions at the candle OPEN, whose astronomy is known before its OHLC.
        longitude=positions[body].longitude.to_numpy()
        direct=ladder_hit(low,high,longitude);opposite=ladder_hit(low,high,longitude,opposite=True)
        controls=np.array([ladder_hit(low,high,longitude,o)|ladder_hit(low,high,longitude,o,True) for o in offsets])
        for name,a,b in [('train','2014-01-01','2019-01-01'),('validation','2019-01-01','2022-01-01'),('test','2022-01-01','2100-01-01')]:
            mask=(times>=a)&(times<b)&(low<high)
            actual=float((direct|opposite)[mask].mean());null=controls[:,mask].mean(axis=1)
            rows.append(dict(body=body,split=name,bars=int(mask.sum()),direct_hit_rate=float(direct[mask].mean()),
                             opposite_hit_rate=float(opposite[mask].mean()),either_hit_rate=actual,
                             shifted_control_mean=float(null.mean()),excess_percentage_points=100*(actual-null.mean()),
                             control_percentile=float((null<actual).mean()),
                             saturated_bars=int(((high-low)[mask]>=12*UNIT).sum())))
    return pd.DataFrame(rows)


def turning_points(close,window):
    """Retrospective extrema, explicitly unavailable until window later bars exist."""
    values=pd.Series(close);width=2*window+1
    maxima=values.rolling(width,center=True).max();minima=values.rolling(width,center=True).min()
    return np.flatnonzero(((values==maxima)|(values==minima)).to_numpy())


def event_associations(frame,events):
    times=pd.DatetimeIndex(frame.available_at);close=frame.close.to_numpy();groups={}
    for event in events:
        if event.exact is None:
            stamps=[event.start,event.end] if event.kind=='24_band' else [event.start]
        else:stamps=[event.exact]
        family=event.details.get('family','')
        key=(event.kind,'/'.join(event.bodies),family)
        groups.setdefault(key,[]).extend(stamps)
    result=[];pivot_rows=[]
    for term,window in PROTOCOL['pivot_half_windows'].items():
        ids=turning_points(close,window)
        radius=PROTOCOL['pivot_event_windows'][term]
        near=np.zeros(len(times),bool)
        for i in ids:
            near[max(0,i-radius):min(len(times),i+radius+1)]=True
            pivot_rows.append(dict(term=term,timestamp=times[i],close=close[i],confirmed_at=times[i+window],retrospective=True))
        for split,start,end in [('validation','2019-01-01','2022-01-01'),('test','2022-01-01','2100-01-01')]:
            usable=(times>=start)&(times<end)&(np.arange(len(times))>=window)&(np.arange(len(times))<len(times)-window)
            base=float(near[usable].mean())
            for (kind,bodies,family),stamps in groups.items():
                # Map event to the closing instant of the UTC candle containing it.
                indices=np.unique(times.searchsorted(pd.DatetimeIndex(stamps),side='right'))
                indices=indices[indices<len(times)];indices=indices[usable[indices]]
                if len(indices)==0:continue
                result.append(dict(term=term,split=split,kind=kind,bodies=bodies,family=family,events=len(indices),
                                   pivot_matches=int(near[indices].sum()),match_rate=float(near[indices].mean()),
                                   calendar_baseline=base,lift=float(near[indices].mean()/base) if base else None,
                                   interpretation='Descriptive retrospective association; no significance claim'))
    return pd.DataFrame(result),pd.DataFrame(pivot_rows)


def load_events(path,start,end,provider,require_cache=False):
    """Cache exact shared-engine events independently of research model changes."""
    from . import events as engine
    signature=hashlib.sha256((Path(engine.__file__).read_bytes()+Path(__file__).with_name('astronomy.py').read_bytes())).hexdigest()
    key=dict(start=start.isoformat(),end=end.isoformat(),bodies=list(ALL_BODIES),engine=signature,provider=provider.metadata())
    if path.exists():
        saved=json.loads(path.read_text())
        if saved['key']==key:
            def restore(r):
                r=dict(r);r['bodies']=tuple(r['bodies'])
                for field in ('start','end','exact'):
                    if r[field]:r[field]=instant(r[field])
                return Event(**r)
            return [restore(r) for r in saved['events']]
    if require_cache:raise ValueError('A complete, matching exact-event cache is required to resume')
    result=[]
    for body in ALL_BODIES:
        print('Exact stations, ingresses and 24-band intervals:',body,flush=True)
        result.extend(body_events(provider,body,start,end))
    for i,(a,b) in enumerate(combinations(ALL_BODIES,2),1):
        print(f'Exact aspect families {i}/45: {a}/{b}',flush=True)
        result.extend(aspects(provider,a,b,start,end))
    result.extend(aspects(provider,'Mars','Saturn',start,end,clock=True))
    result.extend(occupancy_combinations(result))
    result.sort(key=lambda e:e.exact or e.start)
    path.write_text(dumps(dict(key=key,events=result)))
    return result


def motion_summary(positions):
    rows=[]
    for body,p in positions.items():
        net=float(p.unwrapped.iloc[-1]-p.unwrapped.iloc[0]);days=(p.timestamp.iloc[-1]-p.timestamp.iloc[0]).total_seconds()/86400
        rows.append(dict(body=body,net_degrees=net,net_zodiac_turns=abs(net)/360,net_clock_turns=abs(net)/24,
                         clock_drift_days=24*days/abs(net) if net else None,
                         retrograde_fraction=float((p.speed<0).mean()),
                         note='Net travel in this observed interval, not a measured full orbital period'))
    return pd.DataFrame(rows)


def legacy_audit(path):
    from astrocalc.calculations import calculate as old_calculate
    from astrocalc.models import Query,WORKFLOWS
    from astrocalc.exporters import render_export
    rows=[]
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for workflow in WORKFLOWS:
            result=old_calculate(Query(workflow,year=2024,month=12,date=date(2024,12,31),body='Sun',other='Jupiter'))
            archive.writestr(workflow+'.csv',render_export(result,'csv'))
            rows.append(dict(workflow=workflow,rows=len(result.rows),sampling=result.sampling,notes=result.notes))
    return rows


def save_workspaces(root,frame,scores):
    root.mkdir(parents=True,exist_ok=True);latest=pd.Timestamp(frame.available_at.max()).to_pydatetime()
    configs={}
    for term,days in [('short',90),('intermediate',365),('long',4*365)]:
        chosen=scores[(scores.term==term)&(scores.body!='Moon')].sort_values('validation_rank').head(3).body.tolist()
        recent=frame[frame.timestamp>=latest-timedelta(days=days)]
        low=max(0.,math.floor((float(recent.low.min())-24*UNIT)/UNIT)*UNIT)
        high=math.ceil((float(recent.high.max())+24*UNIT)/UNIT)*UNIT
        s=Settings(start=(latest-timedelta(days=days)).isoformat(),end=latest.isoformat(),selected=latest.isoformat(),
                   bodies=chosen,pair=chosen[:2],low=low,high=high,future_days=30,step_hours=24 if term=='short' else 72 if term=='intermediate' else 168,
                   preset='Bitcoin · $369',price_file='bitcoin_universal.csv',market=asdict(bitcoin_market()),
                   session_policy='strict',window_days=1,shifts=[0,.5,1,-.5,-1],last_family_dates=3)
        s.scale.update(unit=UNIT,quote_units='USD/BTC');s.contacts.update(tolerance_ticks=0)
        s.annotations=[dict(timestamp=latest.isoformat(),text=f'{term.title()} research view. Bodies selected on 2019–2021 validation, not on test-period fit. These are exploratory candidates; see reports/bitcoin/report.md. Data ends July 2025.',classification='research interpretation')]
        (root/(term+'.json')).write_text(dumps(s.validate()));configs[term]=s
    return configs


def run(source,output,workspace_dir,finish_only=False):
    output.mkdir(parents=True,exist_ok=True)
    if finish_only:
        content=(source.parent/'bitcoin_universal.csv').read_bytes()
        audit=json.loads((output/'data-audit.json').read_text())
        if hashlib.sha256(content).hexdigest()!=audit['normalized_sha256'] or hashlib.sha256(source.read_bytes()).hexdigest()!=audit['source_sha256']:
            raise ValueError('Source or normalized data changed; rerun the full study')
        if json.loads((output/'protocol.json').read_text())!=PROTOCOL:raise ValueError('Protocol changed; rerun the full study')
        data=load_prices(content,bitcoin_market());provider=EphemProvider()
        events=load_events(output/'events.json',instant(PROTOCOL['analysis_start']+'T00:00:00Z'),data.frame.available_at.max().to_pydatetime(),provider,require_cache=True)
        scores=pd.read_csv(output/'planet-scores.csv')
        finish_study(output,data,events,provider,audit,scores)
        return save_workspaces(workspace_dir,data.frame,scores)
    content,audit=normalize_bitcoin(source.read_bytes())
    normalized=source.parent/'bitcoin_universal.csv';normalized.write_bytes(content)
    (output/'data-audit.json').write_text(dumps(audit))
    (output/'protocol.json').write_text(dumps(PROTOCOL))
    if audit['missing_dates']:raise ValueError('The daily research protocol requires consecutive bars; resolve missing source dates without inventing OHLC before analysis.')
    data=load_prices(content,bitcoin_market());frame=data.frame
    print('Normalized',len(frame),'bars. Computing daily geocentric positions.',flush=True)
    provider=EphemProvider()
    # Include first open and all close instants, allowing exact open/close alignment.
    times=[frame.timestamp.iloc[0].to_pydatetime()]+[t.to_pydatetime() for t in frame.available_at]
    position_frame=pd.DataFrame(series(provider,ALL_BODIES,times))
    write_table(output/'positions.csv',position_frame)
    end_positions={b:position_frame[position_frame.body==b].iloc[1:].reset_index(drop=True) for b in ALL_BODIES}
    open_positions={b:position_frame[position_frame.body==b].iloc[:-1].reset_index(drop=True) for b in ALL_BODIES}
    scores,predictions=forecast_study(frame,end_positions)
    write_table(output/'planet-scores.csv',scores);write_table(output/'test-predictions.csv',predictions)
    write_table(output/'channel-controls.csv',channel_study(frame,open_positions))
    write_table(output/'motion-summary.csv',motion_summary({b:p[p.timestamp>=instant('2014-01-01T00:00:00Z')] for b,p in end_positions.items()}))
    configs=save_workspaces(workspace_dir,frame,scores)
    print('Chronological forecasts and randomized channel controls complete.',flush=True)
    events=load_events(output/'events.json',instant('2014-01-01T00:00:00Z'),times[-1],provider)
    finish_study(output,data,events,provider,audit,scores)
    return configs


def finish_study(output,data,events,provider,audit,scores):
    frame=data.frame;asof=frame.available_at.max().to_pydatetime()
    associations,pivots=event_associations(frame,events)
    write_table(output/'event-associations.csv',associations);write_table(output/'retrospective-pivots.csv',pivots)
    # Pairwise family overlap uses the shared causal/session comparison implementation.
    summaries=[]
    for i,pair in enumerate(combinations(ALL_BODIES,2),1):
        print(f'Causal range comparisons {i}/45: {"/".join(pair)}',flush=True)
        selected=[e for e in events if e.kind=='aspect' and e.bodies==pair]
        matches=compare_events(data,selected,Scale(UNIT),asof,policy='strict',shifts=[0,.5,1,-.5,-1])
        for split,a,b in [('validation','2019-01-01','2022-01-01'),('test','2022-01-01','2100-01-01')]:
            group=[r for r in matches if a<=r['target_time'].date().isoformat()<b]
            for shift in [0,.5,1,-.5,-1]:
                stats=evaluation([r for r in group if r['shift']==shift])
                summaries.append(dict(pair='/'.join(pair),split=split,shift=shift,**stats))
    (output/'aspect-range-comparisons.json').write_text(dumps(summaries))
    paired=compare_events(data,[e for e in events if set(e.bodies)=={'Mercury','Sun'}],Scale(UNIT),asof,policy='strict',conjunction_pairs=True)
    (output/'mercury-conjunction-ranges.json').write_text(dumps(paired))
    (output/'legacy-workflows.json').write_text(dumps(legacy_audit(output/'legacy-2024.zip')))
    (output/'summary.json').write_text(dumps(dict(protocol=PROTOCOL,audit=audit,scores=records(scores),
                                                 astronomy=provider.metadata(),event_count=len(events),source_sha256=audit['source_sha256'])))
    print('All event, range-comparison and legacy workflow exports complete.',flush=True)
