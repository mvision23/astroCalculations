"""Run with universal-clock ui. Optional Streamlit imports stay outside legacy UI."""
from dataclasses import asdict
from datetime import datetime,date,time,timedelta
from importlib.resources import files
import io,json
import pandas as pd
import streamlit as st
from astrocalc.universal.astronomy import BODIES,MODES,EphemProvider,instant,UTC
from astrocalc.universal.workspace import Settings,calculate
from astrocalc.universal.geometry import Scale
from astrocalc.universal.market import MarketSpec,load_prices,book_ranges
from astrocalc.universal.methods import PRESETS,evaluation,validate_sequence
from astrocalc.universal.plotting import price_chart,astronomy_chart,wheel,calendar_rows,event_timeline
from astrocalc.universal.exports import dumps,bundle,html_chart,csv_text
from astrocalc.universal.pine import build_tables,generate_pine
from astrocalc.universal.demo import synthetic_csv

st.set_page_config(page_title='Universal Clock · AstroCalc',page_icon='◷',layout='wide')
st.markdown('''<style>
.stApp {background:#101824;color:#dce5ef} [data-testid="stSidebar"]{background:#172131}
[data-testid="stMetric"]{background:#192536;border:1px solid #2b3b50;padding:16px;border-radius:9px}
h1 {letter-spacing:-.04em} .block-container{padding-top:2rem}
</style>''',unsafe_allow_html=True)
if 'workspace' not in st.session_state:st.session_state.workspace=asdict(Settings())
s=Settings.from_dict(st.session_state.workspace)

with st.sidebar:
    st.markdown('### ◷ Universal Clock')
    st.caption('ASTROCALC · LOCAL RESEARCH')
    workspace_file=st.file_uploader('Reopen workspace',type=['json'],key='workspace_file')
    if workspace_file and st.button('Load workspace'):
        try:
            loaded=Settings.from_dict(json.loads(workspace_file.getvalue()))
            st.session_state.workspace=asdict(loaded)
            st.session_state.pop('replay_day',None)
            st.session_state.pop('replay_time',None)
            st.rerun()
        except (ValueError,TypeError) as exc:st.error(str(exc))
    preset=st.selectbox('Historical example',list(PRESETS),index=list(PRESETS).index(s.preset) if s.preset in PRESETS else 0)
    locked=st.checkbox('Lock price scale',s.scale_locked)
    s.scale_locked=locked
    if st.button('Apply example settings'):
        p=PRESETS[preset];s.preset=preset;s.bodies=p['bodies'];s.pair=p['pair'];s.low=p['low'];s.high=p['high']
        s.scale.update(unit=p['unit'],quote_units=p['quote_units']);s.market.update(quote_units=p['quote_units']);s.conjunction_pairs=preset=='Soybeans'
        st.session_state.workspace=asdict(s);st.rerun()
    with st.form('parameters'):
        a=st.date_input('Start (UTC)',instant(s.start).date(),min_value=date(1900,1,1),max_value=date(2100,12,31))
        b=st.date_input('End (UTC)',instant(s.end).date(),min_value=date(1900,1,1),max_value=date(2100,12,31))
        bodies=st.multiselect('Planets · Moon is an extension',BODIES+('Moon',),default=s.bodies)
        coord=st.selectbox('Coordinates',MODES,index=MODES.index(s.coordinate_mode))
        unit=st.number_input('Quoted units per wheel step',min_value=.000000001,value=float(s.scale['unit']),format='%.9f',disabled=locked)
        rounding=st.selectbox('Longitude plotting',('book','continuous'),index=0 if s.scale['rounding']=='book' else 1)
        quote=st.text_input('Quote units',s.scale['quote_units'])
        low=st.number_input('Price panel minimum',value=float(s.low),format='%.6f');high=st.number_input('Price panel maximum',value=float(s.high),format='%.6f')
        future=st.number_input('Future astronomy (days)',min_value=0,max_value=730,value=s.future_days)
        step=st.number_input('Position spacing (hours)',min_value=.25,max_value=744.,value=float(s.step_hours))
        pair1=st.selectbox('Aspect body',BODIES+('Moon',),index=(BODIES+('Moon',)).index(s.pair[0]))
        pair2=st.selectbox('Aspect counterpart',BODIES+('Moon',),index=(BODIES+('Moon',)).index(s.pair[1]))
        orb=st.number_input('Event orb (degrees / clock units)',min_value=0.,max_value=5.9,value=float(s.orb))
        opposite=st.checkbox('Opposite / midpoint channels',s.opposite)
        monthly=st.checkbox('Monthly Saturn-style reproduction',s.monthly_sample)
        if st.form_submit_button('Calculate',type='primary'):
            try:
                s.start=datetime.combine(a,time(),UTC).isoformat();s.end=datetime.combine(b,time(),UTC).isoformat()
                s.bodies=bodies;s.coordinate_mode=coord;s.scale.update(unit=unit,rounding=rounding,quote_units=quote)
                s.low=low;s.high=high;s.future_days=future;s.step_hours=step;s.pair=[pair1,pair2];s.orb=orb;s.opposite=opposite;s.monthly_sample=monthly
                s.validate();st.session_state.workspace=asdict(s);st.rerun()
            except ValueError as exc:st.error(str(exc))

st.title('Universal Clock')
st.caption('Explore time, planetary motion and price · Jeanne Long, Book I (1993)')
st.info('Astronomical positions are calculations. Market relationships are research hypotheses. Historical presets have not been validated as forecasts.')

with st.expander('Price data & market sessions',expanded=False):
    source=st.radio('Price source',['No prices · astronomy only','Upload CSV / Parquet','Synthetic demonstration','Book transcribed ranges'],horizontal=True)
    book_name=st.selectbox('Source range fixture',['sugar_daily','sp_trines_june_1991','sp_trines_march_1992','dow_trines']) if source=='Book transcribed ranges' else None
    uploaded=st.file_uploader('Historical price file',type=['csv','parquet']) if source=='Upload CSV / Parquet' else None
    c1,c2,c3=st.columns(3)
    with c1:
        zone=st.text_input('Session IANA timezone',s.market['timezone'])
        timestamp_kind=st.selectbox('Timestamp meaning',['daily_label','instant'],index=0 if s.market['timestamp_kind']=='daily_label' else 1)
        convention=st.selectbox('Bar timestamp labels',['close','open'],index=0 if s.market['bar_convention']=='close' else 1)
        calendar=st.selectbox('Session calendar',['weekdays','24/7'],index=0 if s.market['calendar']=='weekdays' else 1)
    with c2:
        opens=st.text_input('Session opens (local HH:MM)',s.market['session_open']);closes=st.text_input('Session closes (local HH:MM)',s.market['session_close'])
        holidays=st.text_input('Excluded holiday dates (comma separated)',','.join(s.market['holidays']))
        duration=st.number_input('Intraday bar duration, minutes',min_value=1,value=s.market['bar_minutes'])
    with c3:
        tick=st.number_input('Tick size',min_value=.000000001,value=float(s.market['tick_size']),format='%.9f')
        adjustments=st.text_input('Corporate-action adjustments',s.market['adjustments'])
        roll=st.text_input('Contract / roll convention',s.market['contract_roll'])
        symbol=st.text_input('Asset / contract',s.market['symbol'])
    st.caption('Weekdays excludes only the holidays you provide. Overnight daily labels name the closing date. No prices are filled or synthesized during import.')
    remove=st.checkbox('Explicitly remove invalid rows and show rejection report',False)
    mapping={};content=None;parquet=False
    if uploaded:
        content=uploaded.getvalue();parquet=uploaded.name.endswith('.parquet')
        try:
            preview=pd.read_parquet(io.BytesIO(content)) if parquet else pd.read_csv(io.BytesIO(content),nrows=5)
            cols=['(none)']+list(preview.columns);mapping_cols=st.columns(4)
            for i,key in enumerate(['timestamp','open','high','low','close','volume','symbol']):
                default=key if key in cols else 'date' if key=='timestamp' and 'date' in cols else '(none)'
                if s.column_mapping.get(key) in cols:default=s.column_mapping[key]
                mapped=mapping_cols[i%4].selectbox(f'Map {key}',cols,index=cols.index(default),key='mapping_'+key)
                if mapped!='(none)':mapping[key]=mapped
            s.column_mapping=mapping
        except Exception as exc:st.error(f'Could not read input: {exc}')
    elif source=='Synthetic demonstration':content=synthetic_csv().encode()
    data=None
    try:
        market=MarketSpec(timezone=zone,timestamp_kind=timestamp_kind,bar_convention=convention,session_open=opens,session_close=closes,
                          calendar=calendar,holidays=tuple(x.strip() for x in holidays.split(',') if x.strip()),tick_size=tick,quote_units=s.scale['quote_units'],
                          adjustments=adjustments,contract_roll=roll,symbol='SYNTHETIC demonstration' if source=='Synthetic demonstration' else symbol,
                          synthetic=source=='Synthetic demonstration',bar_minutes=duration)
        s.market=asdict(market)
        if content:data=load_prices(content,market,mapping,reject_invalid=not remove,parquet=parquet);st.json(data.report,expanded=False)
        elif book_name:data=book_ranges(book_name,market);st.json(data.report,expanded=False)
    except (ValueError,TypeError) as exc:st.error(str(exc))

if data is not None and data.spec.synthetic:st.warning('Synthetic prices — demonstration only. No statistics here measure the book’s historical claims.')
start_day=instant(s.start).date();last_day=(instant(s.end)+timedelta(days=s.future_days)).date()
if 'replay_day' not in st.session_state or not start_day<=st.session_state.replay_day<=last_day:
    st.session_state.replay_day=min(last_day,max(start_day,instant(s.selected).date()))
if 'replay_time' not in st.session_state:st.session_state.replay_time=instant(s.selected).time().replace(tzinfo=None)
def move_day(offset):
    st.session_state.replay_day=min(last_day,max(start_day,st.session_state.replay_day+timedelta(days=offset)))
c1,c2,c3,c4=st.columns([1,1,6,2])
c1.button('← Previous',on_click=move_day,args=(-1,));c2.button('Next →',on_click=move_day,args=(1,))
selected_day=c3.slider('Replay day · focus slider and use arrow keys',min_value=start_day,max_value=last_day,key='replay_day',step=timedelta(days=1))
selected_time=c4.time_input('UTC time',key='replay_time')
s.selected=datetime.combine(selected_day,selected_time,UTC).isoformat()
st.session_state.workspace=asdict(s)

@st.cache_data(show_spinner=False,max_entries=12)
def compute(config,content,mapping,remove,parquet,book_name):
    cfg=Settings.from_dict(json.loads(config));data=load_prices(content,MarketSpec(**cfg.market),mapping,reject_invalid=not remove,parquet=parquet) if content else None
    if book_name:data=book_ranges(book_name,MarketSpec(**cfg.market))
    return calculate(cfg,data)

try:
    with st.spinner('Calculating positions, refined events and price comparisons…'):
        result=compute(dumps(s),content if data is not None else None,mapping,remove,parquet,book_name)
except (ValueError,RuntimeError) as exc:st.error(str(exc));st.stop()
cols=st.columns(4)
cols[0].metric('Selected UTC',f'{selected_day:%d %b %Y}')
cols[1].metric('Price cycle',f'{24*s.scale["unit"]:g} {s.scale["quote_units"]}')
cols[2].metric('Astronomical events',str(len(result.events)))
cols[3].metric('Observed price bars',str(len(data.completed(instant(s.selected)))) if data else 'No dataset')
tabs=st.tabs(['Price & replay','Astronomy','Universal Clock','Events & calendar','Aspect families','Methods & settings','Export & Pine'])
with tabs[0]:
    c1,c2,c3=st.columns(3)
    show_static=c1.checkbox('Static divisions',True);show_events=c2.checkbox('Event markers',True);show_ranges=c3.checkbox('Source ranges / target windows',True)
    fig=price_chart(result,data,show_static,show_events,show_ranges)
    st.plotly_chart(fig,width='stretch',key='price')
    if data is None:st.caption('Planetary trajectories work without prices. Import prices to enable observed ranges and contacts.')
    st.markdown('**Candidate levels at the selected instant**')
    candidates=[r for r in result.levels if r['timestamp']==instant(s.selected) and r.get('body') and s.low<=r['low']<=s.high]
    st.dataframe(pd.DataFrame(candidates),hide_index=True,width='stretch')
    st.caption('Candidates include both directions; no future OHLC or automatic trade direction is implied.')
    st.dataframe(pd.DataFrame(result.contacts),hide_index=True,width='stretch')
    note=st.text_input('Daily observation / movement between planets',key='daily_note')
    if st.button('Save daily annotation') and note:
        s.annotations.append(dict(timestamp=s.selected,text=note,classification='manual interpretation'));st.session_state.workspace=asdict(s);st.rerun()
    st.dataframe(pd.DataFrame(s.annotations),hide_index=True,width='stretch')
with tabs[1]:
    mode=st.radio('Astronomy scale',['unwrapped','wrapped','phase','speed'],horizontal=True)
    st.plotly_chart(astronomy_chart(result,mode),width='stretch')
    st.dataframe(pd.DataFrame([r for r in result.positions if r['timestamp']==instant(s.selected)]),hide_index=True,width='stretch')
    st.json(result.metadata['astronomy'],expanded=False)
with tabs[2]:
    labels=st.checkbox('Show ring labels',True)
    dates=st.multiselect('Compare completed price-range dates',list(data.completed(instant(s.selected)).session.unique()) if data is not None else [],default=[])
    view=st.radio('Wheel',['Universal Clock','Ordinary zodiac'],horizontal=True)
    shift=st.number_input('Price-range shift in cycles · 0.5 is opposite',value=0.,step=.5)
    discrete=st.checkbox('Book price labels · nearest step, exact ties down',False)
    radial=None
    if view=='Universal Clock':
        import math
        extent=10+(math.ceil((s.high-s.low)/(24*s.scale['unit']))+1)*.48
        radial=st.slider('Radial zoom · time rings 2–9, price rings above 9',0.,float(extent),(0.,float(extent)),step=.1)
    st.plotly_chart(wheel(result,data,labels,dates,zodiac=view=='Ordinary zodiac',range_shift=shift,discrete_ranges=discrete,radial_range=radial),width='stretch')
    st.caption('UC04-WHEEL · printed 41–49 / PDF 44–52. Numbers run counterclockwise; a separate continuous phase locates channels. Opposite = 12 wheel units. Zodiac aspects use 360 degrees.')
    st.dataframe(pd.DataFrame(result.confluences),hide_index=True,width='stretch')
with tabs[3]:
    st.plotly_chart(event_timeline(result.events),width='stretch')
    kinds=sorted({e.kind for e in result.events});chosen=st.multiselect('Event types',kinds,default=kinds)
    display_zone=st.text_input('Display IANA timezone',s.market['timezone'])
    try:
        from zoneinfo import ZoneInfo
        z=ZoneInfo(display_zone)
        rows=[dict(e.record(),start_local=e.start.astimezone(z).isoformat(),exact_local=e.exact.astimezone(z).isoformat() if e.exact else None,end_local=e.end.astimezone(z).isoformat()) for e in result.events if e.kind in chosen]
        st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
        month=st.text_input('Calendar month YYYY-MM',selected_day.strftime('%Y-%m'))
        st.dataframe(pd.DataFrame(calendar_rows(result.events,month,display_zone,s.bodies)),hide_index=True,width='stretch')
    except (ValueError,KeyError) as exc:st.error(str(exc))
    st.caption('Band visits are intervals; simultaneous occupancy is grouped. Mars/Saturn matches search the whole 24-step clock. Entry/exit timestamps remain astronomical UTC instants.')
with tabs[4]:
    st.caption('UC01-PAIR / UC03-REPEAT / UC04-FAMILY · all configured shifts remain visible, including misses and unavailable cases.')
    if data is not None:
        st.dataframe(pd.DataFrame(result.matches),hide_index=True,width='stretch');st.json(evaluation(result.matches,data.spec.synthetic))
    else:st.info('Load OHLC prices for range comparison. Close-only series cannot provide historical trading ranges.')
    aspect_options={str(i):f'{e.exact:%Y-%m-%d %H:%M} {e.details.get("family","")}' for i,e in enumerate(result.events) if e.kind=='aspect' and e.exact}
    selected_events=st.multiselect('Manual sequence (select 2–4 events in order)',list(aspect_options),format_func=aspect_options.get)
    sequence_label=st.text_input('Sequence label',value='1–2')
    if st.button('Save sequence'):
        try:
            sequence=validate_sequence([result.events[int(i)].exact.isoformat() for i in selected_events],sequence_label)
            s.sequences.append(sequence);st.session_state.workspace=asdict(s);st.rerun()
        except ValueError as exc:st.error(str(exc))
    st.dataframe(pd.DataFrame(s.sequences),hide_index=True,width='stretch')
with tabs[5]:
    with st.form('method_settings'):
        policy=st.selectbox('Non-session event-date assignment',['next','previous','strict'],index=['next','previous','strict'].index(s.session_policy))
        window=st.number_input('Expanded window ± calendar days',0,10,s.window_days)
        previous=st.number_input('Previous dates from same aspect family',1,100,s.last_family_dates)
        compare_mode=st.selectbox('Comparison selection',['family','consecutive','manual'],index=['family','consecutive','manual'].index(s.comparison_mode))
        shifts=st.text_input('Preselected cycle shifts (comma separated; 0.5 = opposite)',','.join(map(str,s.shifts)))
        pairs=st.checkbox('Superior → following inferior Mercury/Sun pairs',s.conjunction_pairs)
        occupancy_mode=st.selectbox('24-line occupancy',['continuous','rounded_labels','degree_buckets'],index=['continuous','rounded_labels','degree_buckets'].index(s.occupancy_mode),help='Continuous uses the stated closed bands. Other choices are labeled interpretations for comparison with approximate book calendars.')
        alignment_mode=st.selectbox('Additional clock alignment interpretation',['exact_phase','rounded_sector'],index=['exact_phase','rounded_sector'].index(s.clock_alignment_mode))
        halfway=st.checkbox('Halfway divisions',s.halfway);adjoining=st.checkbox('Source-derived adjoining areas',s.adjoining)
        tol=st.number_input('Contact tolerance, ticks',0.,100.,float(s.contacts['tolerance_ticks']))
        sep=st.number_input('Minimum bars between tests',1,100,int(s.contacts['separation_bars']))
        cong=st.number_input('Consecutive contact bars for congestion',1,100,int(s.contacts['congestion_bars']))
        confirm=st.number_input('Consecutive closes for confirmation',1,100,int(s.contacts['confirmation_bars']))
        field=st.selectbox('Touch field',['range','close'],index=0 if s.contacts['field']=='range' else 1)
        anchored=st.checkbox('Extension: anchored price transform',s.scale['anchored'])
        anchor_p=st.number_input('Anchor price P0',value=float(s.scale['anchor_price']));anchor_l=st.number_input('Anchor longitude L0',value=float(s.scale['anchor_longitude']))
        if st.form_submit_button('Apply method settings'):
            try:
                s.session_policy=policy;s.window_days=window;s.last_family_dates=previous;s.shifts=[float(x) for x in shifts.split(',')];s.comparison_mode=compare_mode
                s.conjunction_pairs=pairs;s.halfway=halfway;s.adjoining=adjoining
                s.occupancy_mode=occupancy_mode;s.clock_alignment_mode=alignment_mode
                s.contacts=dict(tolerance_ticks=tol,separation_bars=sep,congestion_bars=cong,confirmation_bars=confirm,field=field)
                s.scale.update(anchored=anchored,anchor_price=anchor_p,anchor_longitude=anchor_l)
                s.validate();st.session_state.workspace=asdict(s);st.rerun()
            except ValueError as exc:st.error(str(exc))
    registry=files('astrocalc.universal').joinpath('method-registry.json')
    if registry.is_file():st.dataframe(pd.DataFrame(json.loads(registry.read_text())),hide_index=True,width='stretch')
    st.caption('Automated contacts are causal interpretations with explicit parameters. Manual sequences and annotations do not imply deterministic book rules.')
    st.markdown('**Inspect scale alternatives**')
    st.caption('These calculations do not select or optimize a scale. Unlock and edit the scale explicitly to change it.')
    alternatives=[]
    for multiplier in (.25,.5,1.,2.,10.):
        alternative=Scale(**dict(s.scale,unit=s.scale['unit']*multiplier))
        for r in result.positions:
            if r['timestamp']==instant(s.selected):
                alternatives.append(dict(body=r['body'],unit=alternative.unit,cycle=24*alternative.unit,levels=[x['price'] for x in alternative.ladder(r['longitude'],s.low,s.high)]))
    st.dataframe(pd.DataFrame(alternatives),hide_index=True,width='stretch')
with tabs[6]:
    st.download_button('Save workspace',dumps(s),'workspace.json','application/json')
    st.download_button('Export results · CSV + JSON + metadata',bundle(result),'universal-clock-results.zip','application/zip')
    st.download_button('Self-contained interactive price chart',html_chart(fig,dict(result.metadata,settings=asdict(s))),'universal-clock.html','text/html')
    st.download_button('Self-contained clock chart',html_chart(wheel(result,data),dict(result.metadata,settings=asdict(s))),'clock.html','text/html')
    image_format=st.selectbox('Static image format',['svg','png'])
    if st.button('Prepare static image'):
        try:st.download_button('Download image',fig.to_image(format=image_format),'clock-price.'+image_format,'image/'+('svg+xml' if image_format=='svg' else 'png'))
        except Exception as exc:st.error(f'Static export requires Kaleido and local Chrome/Chromium: {exc}')
    st.markdown('**TradingView · generated ephemeris**')
    error=st.number_input('Maximum measured interpolation error, degrees',.000001,1.,.002,format='%.6f')
    fraction=st.number_input('Maximum smooth price error, fraction of a tick',.001,1.,.25)
    spacing=st.number_input('Maximum knot spacing, hours',.25,48.,24.)
    st.caption('Finite UTC coverage includes the configured future horizon. Regenerate and replace scripts to extend it. Book rounding can differ by a full wheel unit near a half-degree boundary.')
    if st.button('Generate Pine v6 indicators'):
        try:
            with st.spinner('Adapting knots and independently measuring interpolation error…'):
                tables=build_tables(EphemProvider(s.coordinate_mode),s.bodies,instant(s.start),instant(s.end)+timedelta(days=s.future_days),Scale(**s.scale),market.tick_size,fraction,error,spacing)
                overlay,meta=generate_pine(tables,result.events,s,result.metadata);pane,_=generate_pine(tables,result.events,s,result.metadata,True)
            st.download_button('Price overlay .pine',overlay,'universal_clock_overlay.pine','text/plain',on_click='ignore')
            st.download_button('Degrees / phase .pine',pane,'universal_clock_degrees.pine','text/plain',on_click='ignore')
            st.json(meta)
        except ValueError as exc:st.error(str(exc))
    st.caption('No TradingView compiler is connected here. See docs/tradingview.md for compilation and runtime verification steps.')
