"""Plotly research views with separate astronomical and price coordinate systems."""
import math
from collections import defaultdict
from datetime import timedelta
import plotly.graph_objects as go
from .astronomy import instant
from .geometry import Scale, label_position, project_interval, price_label

COLORS=['#e8b65b','#77c5ca','#d78daf','#8eabec','#b3a0db','#9fc993','#cf916e','#d6d198','#c4b4a3','#d3dadb']
BACKGROUND='#101824'

def theme(fig,title):
    fig.update_layout(template='plotly_dark',paper_bgcolor=BACKGROUND,plot_bgcolor=BACKGROUND,
                      title=dict(text=title,font=dict(size=19)),font=dict(family='Inter, sans-serif',color='#dce5ef'),
                      margin=dict(l=35,r=25,t=60,b=35),legend=dict(orientation='h'),hovermode='closest')
    return fig


def price_chart(result,data=None,show_static=True,show_events=True,show_ranges=True,replay=True):
    fig=go.Figure();s=result.settings;selected=instant(s.selected)
    if data is not None:
        frame=data.completed(selected) if replay else data.frame
        if data.ohlc:
            fig.add_trace(go.Candlestick(x=frame.timestamp,open=frame.open,high=frame.high,low=frame.low,close=frame.close,
                                        name=data.spec.symbol,increasing_line_color='#83cfb0',decreasing_line_color='#e58c8c'))
        elif 'close' in frame:fig.add_trace(go.Scatter(x=frame.timestamp,y=frame.close,name=f'{data.spec.symbol} close',line_color='#e5e7ef'))
        else:fig.add_trace(go.Bar(x=frame.timestamp,y=frame.high-frame.low,base=frame.low,width=3600000*8,name='Transcribed low/high only',marker_color='#83cfb0'))
    groups=defaultdict(list)
    for level in result.levels:groups[level['id']].append(level)
    colors={b:COLORS[i%len(COLORS)] for i,b in enumerate(s.bodies)};legend_bodies=set()
    for name,rows in groups.items():
        first=rows[0]
        if not first.get('body'):
            if show_static:
                fig.add_hrect(y0=first['low'],y1=first['high'],fillcolor='#b7bcca',opacity=.08,line_width=.4,
                              line_dash='dot' if first['kind'] in ('halfway','adjoining') else 'solid')
            continue
        future=[r['timestamp']>selected for r in rows]
        for is_future in (False,True):
            chosen=[r for r,f in zip(rows,future) if f==is_future]
            if is_future:
                before=[r for r in rows if r['timestamp']<=selected]
                if before:chosen=before[-1:]+chosen
            if not chosen:continue
            show_legend=not is_future and first['body'] not in legend_bodies
            if show_legend:legend_bodies.add(first['body'])
            fig.add_trace(go.Scatter(x=[r['timestamp'] for r in chosen],y=[r['low'] for r in chosen],name=first['body'],mode='lines',
                        legendgroup=first['body'],showlegend=show_legend,line=dict(color=colors[first['body']],width=1.2,
                        dash='dot' if is_future else 'dash' if first['opposite'] else 'solid',shape='hv' if s.scale['rounding']=='book' and not s.monthly_sample else 'linear'),
                        opacity=.55 if first['opposite'] else .9,hovertemplate=name+'<br>%{x}<br>%{y:.6f}<extra></extra>'))
    if show_events:
        markers=[e for e in result.events if e.exact]
        fig.add_trace(go.Scatter(x=[e.exact for e in markers],y=[s.high]*len(markers),mode='markers',name='Exact astronomy',
                      marker=dict(symbol='triangle-down',size=7,color='#a9b5cc'),text=[f'{e.kind}: {" / ".join(e.bodies)} {e.target}' for e in markers],
                      hovertemplate='%{text}<br>%{x}<extra></extra>'))
    if show_ranges:
        for r in result.matches:
            if r['eligible'] and r['source_low'] is not None:
                fig.add_shape(type='rect',x0=r['source_time'],x1=r['target_time'],y0=r['source_low'],y1=r['source_high'],line=dict(width=1,color='#b6a2d9'),fillcolor='rgba(180,155,215,.035)')
                fig.add_vrect(x0=r['target_time']-timedelta(days=s.window_days),x1=r['target_time']+timedelta(days=s.window_days),fillcolor='#8ba3cb',opacity=.04,line_width=0)
    fig.add_shape(type='line',x0=selected,x1=selected,y0=s.low,y1=s.high,line=dict(color='#eeeeee',width=1,dash='dot'))
    fig.update_layout(xaxis_rangeslider_visible=False,height=650,yaxis_title=s.scale.get('quote_units','price'),yaxis_range=[s.low,s.high],
                      xaxis_range=[instant(s.start),s.horizon])
    return theme(fig,'Price · planetary channels & clock divisions')


def astronomy_chart(result,mode='unwrapped'):
    fig=go.Figure();period=24 if mode=='phase' else 360
    for i,body in enumerate(result.settings.bodies):
        rows=[r for r in result.positions if r['body']==body];x=[];y=[];previous=None
        for r in rows:
            v=r['speed'] if mode=='speed' else r['unwrapped'] if mode=='unwrapped' else r['longitude']%period
            if previous is not None and mode in ('wrapped','phase') and abs(v-previous)>period/2:x.append(r['timestamp']);y.append(None)
            x.append(r['timestamp']);y.append(v);previous=v
        fig.add_trace(go.Scatter(x=x,y=y,name=body,line=dict(color=COLORS[i%len(COLORS)]),connectgaps=False))
    stations=[e for e in result.events if e.kind=='station']
    for e in stations:fig.add_shape(type='line',x0=e.exact,x1=e.exact,y0=0,y1=1,yref='paper',line=dict(width=.7,dash='dot',color='#a0aabb'))
    aspects=[e for e in result.events if e.kind in ('aspect','clock_alignment') and e.exact]
    if aspects:
        marker_y=max((v for trace in fig.data for v in trace.y if v is not None),default=0)
        fig.add_trace(go.Scatter(x=[e.exact for e in aspects],y=[marker_y]*len(aspects),mode='markers',name='Exact aspects / clock matches',marker=dict(symbol='triangle-down',size=7),text=[f'{e.kind}: {"/".join(e.bodies)} {e.target}' for e in aspects],hovertemplate='%{text}<br>%{x}<extra></extra>'))
    selected=instant(result.settings.selected)
    fig.add_shape(type='line',x0=selected,x1=selected,y0=0,y1=1,yref='paper',line=dict(color='white',dash='dash'))
    fig.update_layout(height=470,yaxis_title='degrees/day' if mode=='speed' else 'wheel units modulo 24' if mode=='phase' else 'ecliptic degrees (separate from price)')
    return theme(fig,f'Astronomy · {mode}')


def wheel(result,data=None,labels=True,dates=None,zodiac=False,range_shift=0.,discrete_ranges=False,radial_range=None):
    s=result.settings;scale=Scale(**s.scale);selected=instant(s.selected)
    fig=go.Figure();rows=[r for r in result.positions if r['timestamp']==selected]
    if not rows:
        available=sorted({r['timestamp'] for r in result.positions if r['timestamp']<=selected})
        rows=[r for r in result.positions if available and r['timestamp']==available[-1]]
    if zodiac:
        from astrocalc.models import SIGNS
        fig.add_trace(go.Scatterpolar(r=[1]*361,theta=list(range(361)),mode='lines',line_color='#536078',showlegend=False))
        fig.add_trace(go.Scatterpolar(r=[1.15]*12,theta=[15+30*i for i in range(12)],text=list(SIGNS),mode='text',showlegend=False))
        for i,r in enumerate(rows):fig.add_trace(go.Scatterpolar(r=[.65+i*.035],theta=[r['longitude']],mode='markers+text',text=[r['body']],textposition='top center',name=r['body'],marker=dict(size=10,color=COLORS[i%10])))
        limit=1.3
    else:
        # Fifteen time rings. Label sectors are centered between their boundaries.
        for ring in range(15):
            radius=2+ring*.48
            fig.add_trace(go.Scatterpolar(r=[radius]*49,theta=[i*7.5 for i in range(49)],mode='lines',line=dict(color='#374459',width=.5),showlegend=False,hoverinfo='skip'))
            if labels:
                ns=list(range(1+24*ring,25+24*ring))
                fig.add_trace(go.Scatterpolar(r=[radius]*24,theta=[label_position(n)[1] for n in ns],text=list(map(str,ns)),mode='text',textfont=dict(size=8,color='#91a0b3'),hoverinfo='text',showlegend=False))
        # Outer price rings follow the chosen scale; price labels use the same sector centers.
        base=math.floor(s.low/(24*scale.unit));outer=math.ceil((s.high-s.low)/(24*scale.unit))+1
        for j in range(outer):
            ns=[24*(base+j)+n for n in range(1,25)];radius=9.5+j*.48
            fig.add_trace(go.Scatterpolar(r=[radius]*49,theta=[n*7.5 for n in range(49)],mode='lines',line=dict(color='#536279',width=.6),showlegend=False,hoverinfo='skip'))
            if labels:fig.add_trace(go.Scatterpolar(r=[radius]*24,theta=[(n%24-.5)%24*15 for n in ns],text=[f'{n*scale.unit:g}' for n in ns],mode='text',textfont=dict(size=8,color='#d2b57d'),showlegend=False))
        limit=10+outer*.48
        for phase in range(24):fig.add_trace(go.Scatterpolar(r=[1.5,limit],theta=[phase*15]*2,mode='lines',line=dict(color='#8590a0' if phase==0 else '#263448',width=2 if phase==0 else .4),showlegend=False,hoverinfo='skip'))
        groups=defaultdict(list)
        for r in rows:groups[scale.coordinate(r['longitude'])%24].append(r)
        for phase,members in groups.items():
            for j,r in enumerate(members):
                n=scale.coordinate(r['longitude'])%360 or 360
                radius=2+((max(1,n)-1)//24)*.48
                # Continuous phase and label-centering are deliberately distinct overlays.
                fig.add_trace(go.Scatterpolar(r=[radius],theta=[phase*15],mode='markers+text',text=[r['body']],name=r['body'],
                    textposition='top center' if j%2==0 else 'bottom center',marker=dict(size=11,color=COLORS[s.bodies.index(r['body'])%10]),
                    hovertemplate=f"{r['body']} · {r['longitude']:.6f}°<br>clock phase {phase:g}<extra></extra>"))
                fig.add_trace(go.Scatterpolar(r=[radius,limit],theta=[phase*15]*2,mode='lines',line=dict(color=COLORS[s.bodies.index(r['body'])%10],width=.7),showlegend=False,hoverinfo='skip'))
        if data is not None and data.has_ranges:
            frame=data.completed(selected)
            wanted=dates or [selected.astimezone(__import__('zoneinfo').ZoneInfo(data.spec.timezone)).date().isoformat()]
            arcs=[]
            for i,d in enumerate(wanted):
                bars=frame[frame.session==str(d)]
                if bars.empty:continue
                low=float(bars.low.min());high=float(bars.high.max())
                if discrete_ranges:low=price_label(low,scale.unit);high=price_label(high,scale.unit)
                lo=low/scale.unit+24*range_shift;hi=high/scale.unit+24*range_shift
                radius=9.5+(math.floor(lo/24)-base)*.48
                radius=max(9.3,min(limit,radius))
                for a,b in project_interval(lo,hi):
                    theta=[15*(a+(b-a)*j/80) for j in range(81)]
                    fig.add_trace(go.Scatterpolar(r=[radius]*81,theta=theta,mode='lines',line=dict(color=COLORS[i%10],width=6),name=str(d),hovertemplate=f'{d}<br>{lo*scale.unit:g}–{hi*scale.unit:g}<extra></extra>'))
                arcs.append((lo,hi,radius))
            # Link overlapping phase portions of each pair of dated ranges.
            for i,(lo,hi,r) in enumerate(arcs):
                for ll,hh,rr in arcs[i+1:]:
                    for a,b in project_interval(lo,hi):
                        for c,d in project_interval(ll,hh):
                            if max(a,c)<=min(b,d):
                                theta=15*(max(a,c)+min(b,d))/2
                                fig.add_trace(go.Scatterpolar(r=[r,rr],theta=[theta]*2,mode='lines',line=dict(color='#eeeeee',width=2),showlegend=False))
    fig.update_layout(height=800,polar=dict(bgcolor=BACKGROUND,radialaxis=dict(visible=False,range=[0,limit]),
                                           angularaxis=dict(direction='counterclockwise',rotation=0,showticklabels=False,showgrid=False)),showlegend=True)
    if radial_range is not None:fig.update_layout(polar_radialaxis_range=radial_range)
    return theme(fig,'Zodiac · 360°' if zodiac else 'Universal Clock · 15 time rings / outer price rings')


def calendar_rows(events,month,zone='UTC',bodies=None):
    from zoneinfo import ZoneInfo
    from datetime import datetime
    zone=ZoneInfo(zone);start=datetime.fromisoformat(month+'-01').replace(tzinfo=zone)
    end=(start.replace(day=28)+timedelta(days=4)).replace(day=1)
    result=[];t=start
    bodies=sorted(set(bodies or ())|{b for e in events for b in e.bodies})
    while t<end:
        r={'date':t.date().isoformat()}
        for body in bodies:
            found=[e for e in events if body in e.bodies and ((e.exact and t<=e.exact<t+timedelta(days=1)) or (not e.exact and e.start<t+timedelta(days=1) and e.end>t))]
            r[body]='; '.join(f'{e.kind} {e.direction} [{e.start.astimezone(zone):%d %H:%M}–{e.end.astimezone(zone):%d %H:%M}]' for e in found)
        result.append(r);t+=timedelta(days=1)
    return result


def event_timeline(events):
    fig=go.Figure()
    for kind in sorted({e.kind for e in events}):
        x=[];y=[];text=[]
        for e in events:
            if e.kind!=kind:continue
            label='/'.join(e.bodies)
            for t in ([e.exact] if e.exact else [e.start,e.end]):
                x.append(t);y.append(label);text.append(f'{kind} · {e.direction}')
            x.append(None);y.append(None);text.append('')
        fig.add_trace(go.Scatter(x=x,y=y,mode='markers+lines',name=kind,text=text,hovertemplate='%{text}<br>%{x}<extra></extra>'))
    fig.update_layout(height=450)
    return theme(fig,'Event timeline · exact contacts and occupancy intervals')
