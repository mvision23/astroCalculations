"""Finite embedded ephemerides for Pine v6. No Pine-side orbital model or network."""
from dataclasses import dataclass, asdict
from datetime import timedelta, datetime
from bisect import bisect_right
import json
import math
from .astronomy import instant, delta, UTC
from .events import scalar_roots, Event
from .geometry import Scale

@dataclass
class EphemerisTable:
    body: str
    timestamps: list
    longitudes: list
    max_error_degrees: float
    rms_error_degrees: float
    max_step_hours: float
    station_count: int

    def lookup(self,t):
        t=instant(t).timestamp()
        if t<self.timestamps[0] or t>self.timestamps[-1]:return None
        i=min(bisect_right(self.timestamps,t)-1,len(self.timestamps)-2)
        f=(t-self.timestamps[i])/(self.timestamps[i+1]-self.timestamps[i])
        return self.longitudes[i]+f*(self.longitudes[i+1]-self.longitudes[i])


def build_table(provider,body,start,end,error_degrees=.002,max_step_hours=24,max_knots=5000):
    start,end=instant(start),instant(end)
    if end<=start or not 1e-7<=error_degrees<=1 or not .25<=max_step_hours<=48:raise ValueError('Invalid ephemeris interval, error or spacing')
    stations=scalar_roots(lambda t:provider.speed(body,t),start,end,tolerance=1.,tangent_epsilon=1e-8)
    boundaries={start,end,*stations};t=start
    while t<end:
        boundaries.add(t);t+=timedelta(hours=max_step_hours)
        if len(boundaries)>max_knots:raise ValueError('Pine knot budget exceeded; reduce interval/bodies or relax sampling target')
    boundaries=sorted(boundaries);points=[(start,provider.longitude(body,start))]
    def refine(a,la,b,lb,depth=0):
        probes=[]
        for f in (.2113248654,.5,.7886751346):
            t=a+(b-a)*f;raw=provider.longitude(body,t);actual=la+delta(raw,la%360)
            probes.append((t,actual,abs(actual-(la+f*(lb-la)))))
        if max(p[2] for p in probes)>error_degrees*.7:
            if depth>=22:raise ValueError('Cannot meet interpolation tolerance; relax target')
            t,l,_=probes[1];refine(a,la,t,l,depth+1);refine(t,l,b,lb,depth+1)
        else:points.append((b,lb))
        if len(points)>max_knots:raise ValueError('Pine knot budget exceeded; reduce coverage or relax tick/error target')
    for a,b in zip(boundaries,boundaries[1:]):
        la=points[-1][1];lb=la+delta(provider.longitude(body,b),la%360)
        refine(a,la,b,lb)
    errors=[]
    # Independent validation points, distinct from recursive subdivision probes.
    for (a,la),(b,lb) in zip(points,points[1:]):
        for f in (.125,.3333333333,.625,.875):
            t=a+(b-a)*f;actual=la+delta(provider.longitude(body,t),la%360)
            errors.append(abs(actual-(la+f*(lb-la))))
    maximum=max(errors,default=0)
    if maximum>error_degrees:raise ValueError('Independent interpolation validation failed; reduce maximum sample spacing')
    return EphemerisTable(body,[t.timestamp() for t,_ in points],[round(l,9) for _,l in points],maximum,
                          math.sqrt(sum(e*e for e in errors)/max(1,len(errors))),
                          max((b-a).total_seconds()/3600 for (a,_),(b,_) in zip(points,points[1:])),len(stations))


def build_tables(provider,bodies,start,end,scale,tick_size=.01,tick_fraction=.25,error_degrees=.002,max_step_hours=24):
    if tick_size<=0 or not 0<tick_fraction<=1:raise ValueError('Tick size/fraction must be positive')
    target=min(error_degrees,tick_size*tick_fraction/scale.unit)
    return [build_table(provider,b,start,end,target,max_step_hours) for b in bodies]

PINE_FUNCTIONS = '''
f_load(string encoded) =>
    array<float> values = array.new_float()
    for item in str.split(encoded, ",")
        array.push(values, str.tonumber(item))
    values
f_upper(array<float> xs, float t) =>
    int lo = 0
    int hi = array.size(xs)
    while lo < hi
        int mid = int(math.floor((lo + hi) / 2))
        if array.get(xs, mid) <= t
            lo := mid + 1
        else
            hi := mid
    lo
f_lookup(array<float> ts, array<float> ls, int stamp) =>
    float t = (stamp - epoch) / 1000.0
    float value = na
    int n = array.size(ts)
    if t >= array.get(ts, 0) and t <= array.get(ts, n - 1)
        int i = math.min(math.max(f_upper(ts, t) - 1, 0), n - 2)
        float a = array.get(ts, i)
        float b = array.get(ts, i + 1)
        value := array.get(ls, i) + (t - a) / (b - a) * (array.get(ls, i + 1) - array.get(ls, i))
    value
f_mod(float x, float p) =>
    ((x % p) + p) % p
f_price(float longitude, int k, bool opposite) =>
    float l = bookRound ? math.floor(longitude + 0.5) : longitude
    anchorPrice + units * (l - anchorLongitude + 24 * k + (opposite ? 12 : 0))
f_curve(array<float> ts, array<float> ls, int k, bool opposite, color c) =>
    array<chart.point> pts = array.new<chart.point>()
    int begin = math.max(time, coverageStart)
    float current = f_lookup(ts, ls, begin)
    if not na(current)
        array.push(pts, chart.point.from_time(begin, f_price(current, k, opposite)))
    int first = f_upper(ts, (begin - epoch) / 1000.0)
    if first < array.size(ts)
        for i = first to array.size(ts) - 1
            int stamp = epoch + int(array.get(ts, i) * 1000)
            if stamp <= coverageEnd
                float longitude = array.get(ls, i)
                // Add every half-degree rounding boundary on this linear segment.
                if bookRound and i > 0
                    int oldStamp = epoch + int(array.get(ts, i - 1) * 1000)
                    float oldL = array.get(ls, i - 1)
                    float newL = longitude
                    int count = int(math.abs(math.floor(newL + 0.5) - math.floor(oldL + 0.5)))
                    if count > 0
                        for j = 1 to count
                            float boundary = newL > oldL ? math.floor(oldL + 0.5) + j - 0.5 : math.floor(oldL + 0.5) - j + 0.5
                            int jumpTime = oldStamp + int((stamp - oldStamp) * (boundary - oldL) / (newL - oldL))
                            if jumpTime > begin
                                float before = boundary + (newL > oldL ? -0.000001 : 0.000001)
                                float after = boundary + (newL > oldL ? 0.000001 : -0.000001)
                                array.push(pts, chart.point.from_time(jumpTime, f_price(before, k, opposite)))
                                array.push(pts, chart.point.from_time(jumpTime, f_price(after, k, opposite)))
                array.push(pts, chart.point.from_time(stamp, f_price(longitude, k, opposite)))
    if array.size(pts) >= 2 and array.size(pts) < 9500
        polyline.new(pts, xloc=xloc.bar_time, line_color=c, line_style=futureStyle, line_width=1)
'''


def generate_pine(tables,events,settings,metadata,pane=False):
    scale=Scale(**settings.scale)
    if not tables:raise ValueError('Choose at least one body')
    if settings.monthly_sample:raise ValueError('Pine uses adaptive samples; turn off monthly reproduction mode')
    count=sum(len(t.timestamps) for t in tables)
    if count>12000:raise ValueError('More than 12000 total knots; reduce bodies, coverage or sampling precision')
    epoch=int(min(t.timestamps[0] for t in tables)*1000)
    end=int(min(t.timestamps[-1] for t in tables)*1000)
    markers=list(events)
    for e in events:
        if e.exact is None and e.kind!='aspect':
            for suffix,t in [('entry',e.start),('exit',e.end)]:
                markers.append(Event(e.kind+'_'+suffix,e.bodies,t,t,t,e.target,e.direction,e.method,e.details))
    exact=sorted([e for e in markers if e.exact and epoch/1000<=e.exact.timestamp()<=end/1000],key=lambda e:e.exact)
    if len(exact)>400:raise ValueError('More than 400 event markers; shorten coverage or select fewer bodies')
    branches=[]
    for i,table in enumerate(tables):
        if not pane:
            future_points=len(table.longitudes)+2*sum(abs(math.floor(b+.5)-math.floor(a+.5)) for a,b in zip(table.longitudes,table.longitudes[1:]))
            if future_points>9000:raise ValueError('Future drawing point budget exceeded; shorten interval/horizon or split coverage')
        if pane:continue
        for opposite in ([False,True] if settings.opposite else [False]):
            for k in scale.branches(table.longitudes,settings.low,settings.high,opposite=opposite):branches.append((i,k,opposite))
    plots=len(tables) if pane else len(branches)+12+1
    if plots>56 or (not pane and len(branches)>40):raise ValueError('Pine plot/drawing budget exceeded; narrow price range, increase scale, turn off opposite lines or split bodies')
    details=dict(metadata,export_version=1,coverage_start=epoch,coverage_end=end,knots=count,plot_budget=plots,
                 interpolation=[dict(body=t.body,max_error_degrees=t.max_error_degrees,rms_error_degrees=t.rms_error_degrees,
                                     smooth_price_error=t.max_error_degrees*scale.unit,max_step_hours=t.max_step_hours,stations=t.station_count) for t in tables],
                 rounding_caveat='Book rounding can differ by one wheel unit near half-degree thresholds despite small angular error.')
    title='Universal Clock — degrees' if pane else 'Universal Clock — price'
    lines=['//@version=6',f'// Generated locally. {json.dumps(details,separators=(",",":"))}',
           f'indicator("{title}", overlay={str(not pane).lower()}, max_polylines_count=50, max_lines_count=450, max_labels_count=450)',
           f'int epoch = {epoch}',f'int coverageStart = {epoch}',f'int coverageEnd = {end}',
           f'float units = input.float({scale.unit}, "Quoted units per wheel step", minval=0.000000001)',
           f'bool bookRound = input.bool({str(scale.rounding=="book").lower()}, "Nearest degree (half up)")',
           f'float anchorPrice = {scale.anchor_price if scale.anchored else 0.0}',f'float anchorLongitude = {scale.anchor_longitude if scale.anchored else 0.0}',
           'bool showEvents = input.bool(true, "Embedded exact astronomical events")',
           'bool showFuture = input.bool(true, "Future astronomical trajectories")',
           'bool showOpposite = input.bool(true, "Opposite / midpoint channels")',
           'string styleChoice = input.string("Dashed", "Future line style", options=["Solid", "Dashed", "Dotted"])',
           'string futureStyle = styleChoice == "Solid" ? line.style_solid : styleChoice == "Dotted" ? line.style_dotted : line.style_dashed',
           PINE_FUNCTIONS]
    palette=['#ecb34b','#68c4cc','#e288a0','#8ba6ff','#c6a2ed','#9fca91','#db956f','#ded18b','#a3b3b8','#dddddd']
    for i,t in enumerate(tables):
        seconds=','.join(f'{x-epoch/1000:.3f}' for x in t.timestamps)
        values=','.join(f'{x:.9f}' for x in t.longitudes)
        for name,encoded in [(f't{i}',seconds),(f'l{i}',values)]:
            parts=encoded.split(',')
            lines.extend([f'var array<float> {name} = array.new_float()','if barstate.isfirst'])
            for begin in range(0,len(parts),500):
                chunk=','.join(parts[begin:begin+500])
                lines.append(f'    array.concat({name}, f_load("{chunk}"))')
        lines.extend([f'color c{i} = input.color({palette[i%len(palette)]}, "{t.body} color")',
                      f'bool enabled{i} = input.bool(true, "Show {t.body}")',f'float lon{i} = f_lookup(t{i}, l{i}, time)'])
    if pane:
        lines.append('string displayMode = input.string("Unwrapped", "Display", options=["Unwrapped", "Wrapped degrees", "Clock phase"])')
        for i,t in enumerate(tables):
            lines.extend([f'float v{i} = displayMode == "Unwrapped" ? lon{i} : f_mod(lon{i}, displayMode == "Clock phase" ? 24 : 360)',
                          f'bool bridge{i} = displayMode != "Unwrapped" and math.abs(v{i} - v{i}[1]) > (displayMode == "Clock phase" ? 12 : 180)',
                          f'plot(enabled{i} and not bridge{i} ? v{i} : na, "{t.body}", color=c{i}, style=plot.style_linebr)'])
    else:
        lines.extend(['bool anyContact = false','float tolerance = input.float(1.0, "Contact tolerance (chart ticks)", minval=0) * syminfo.mintick'])
        for j,(i,k,opposite) in enumerate(branches):
            lines.extend([f'int k{j} = input.int({k}, "{tables[i].body} {"opposite" if opposite else "channel"} branch {j}")',
                          f'float p{j} = enabled{i} and {"showOpposite" if opposite else "true"} ? f_price(lon{i}, k{j}, {str(opposite).lower()}) : na',
                          f'plot(p{j}, "{tables[i].body} {"opposite" if opposite else "channel"} {k}", color=color.new(c{i}, {55 if opposite else 0}), style=bookRound ? plot.style_stepline : plot.style_linebr)',
                          f'anyContact := anyContact or (not na(p{j}) and low <= p{j} + tolerance and high >= p{j} - tolerance)'])
        lines.extend(['alertcondition(barstate.isconfirmed and anyContact, "Confirmed price contact", "Completed bar touches an embedded planetary price channel")',
                      'bool staticOn = input.bool(true, "Static divisions A–D")',
                      f'int staticCycle = input.int({math.floor(settings.low/(24*scale.unit))}, "Static division cycle index")'])
        for j,offset in enumerate((0,6,12,18)):
            for edge in (0,1):lines.append(f'static{j}_{edge} = plot(staticOn and time >= coverageStart and time <= coverageEnd ? units * (24 * staticCycle + {offset+edge}) : na, "{chr(65+j)} {edge}", color=color.new(color.gray, 45), style=plot.style_linebr)')
            lines.append(f'fill(static{j}_0, static{j}_1, color=color.new(color.gray, 90), title="{chr(65+j)} band")')
            lines.append(f'plot(staticOn and time >= coverageStart and time <= coverageEnd ? units * (24 * staticCycle + {offset+3.5}) : na, "Halfway {j}", color=color.new(color.gray, 70), style=plot.style_linebr)')
        lines.append('if barstate.islast')
        lines.append('    for drawing in polyline.all\n        polyline.delete(drawing)')
        lines.append('    if showFuture and time <= coverageEnd')
        if not branches:lines.append('        int unused = 0')
        for j,(i,k,opposite) in enumerate(branches):
            lines.extend([f'        if enabled{i} and {"showOpposite" if opposite else "true"}',f'            f_curve(t{i}, l{i}, k{j}, {str(opposite).lower()}, c{i})'])
    # Events use exact UTC time drawings, not a marker inferred from visual ephemeris samples.
    if exact:
        encoded=','.join(str(round(e.exact.timestamp()*1000)-epoch) for e in exact)
        names=[f'{e.kind} {"/".join(e.bodies)} {e.target if e.target is not None else ""}' for e in exact]
        labels='|'.join(names).replace('"','')
        lines.extend([f'var array<float> eventTimes = f_load("{encoded}")',f'var array<string> eventNames = str.split("{labels}", "|")',
                      'if barstate.islast','    for mark in line.all\n        line.delete(mark)',
                      '    for tag in label.all\n        label.delete(tag)','    if showEvents',
                      '        for i = 0 to array.size(eventTimes) - 1',
                      '            int stamp = epoch + int(array.get(eventTimes, i))',
                      '            line.new(stamp, 0, stamp, 1, xloc=xloc.bar_time, extend=extend.both, color=color.new(color.gray, 80), style=line.style_dotted)',
                      '            label.new(stamp, '+('0' if pane else 'close')+', array.get(eventNames, i), xloc=xloc.bar_time, style=label.style_label_down, size=size.tiny, color=color.new(color.gray, 85), textcolor=color.gray)'])
    lines.extend(['var table coverage = table.new(position.top_right, 1, 1)','if barstate.islast',
                  '    table.cell(coverage, 0, 0, "Finite ephemeris: " + str.format_time(coverageStart, "yyyy-MM-dd", "UTC") + " → " + str.format_time(coverageEnd, "yyyy-MM-dd", "UTC") + (time < coverageStart or time > coverageEnd ? "\\nOUTSIDE COVERAGE" : "\\nUTC / '+settings.coordinate_mode+'"), text_color=color.white, bgcolor=color.new(color.black, 20))'])
    source='\n'.join(lines)+'\n'
    if len(source.encode())>350000:raise ValueError('Pine source exceeds conservative 350 KB budget; reduce coverage/bodies or relax error')
    return source,details
