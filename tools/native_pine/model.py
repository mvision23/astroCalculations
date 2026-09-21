"""Development-only mirror of the native Pine model, never an indicator feed.

Independent implementation of Paul Schlyter's published low-precision elements,
perturbations and Pluto Fourier terms: https://stjarnhimlen.se/comp/ppcomp.html
UTC approximates UT1; NASA piecewise delta-T polynomials supplies approximate TT.
Output: geometric geocentric mean ecliptic/equinox of date, NOT apparent positions.
"""
from datetime import datetime, timezone
import math

BODIES = ('Sun','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto','Moon')
DAY = 86400000
MIN_TIME = int(datetime(2009,1,1,tzinfo=timezone.utc).timestamp()*1000)
MAX_TIME = int(datetime(2051,1,1,tzinfo=timezone.utc).timestamp()*1000)
sin = lambda x: math.sin(math.radians(x))
cos = lambda x: math.cos(math.radians(x))
atan = lambda y,x: math.degrees(math.atan2(y,x))
delta = lambda a,b: (a-b+180)%360-180

def day(ts):
    jd=ts/DAY+2440587.5
    y=(jd-2451545.)/365.2425
    dt=62.92+.32217*y+.005589*y*y if y<50 else -20+32*((y+180)/100)**2-.5628*(150-y)
    return jd+dt/86400-2451543.5

def elements(body,d):
    return [
        (0,0,282.9404+4.70935e-5*d,1,.016709-1.151e-9*d,356.0470+.9856002585*d),
        (48.3313+3.24587e-5*d,7.0047+5e-8*d,29.1241+1.01444e-5*d,.387098,.205635+5.59e-10*d,168.6562+4.0923344368*d),
        (76.6799+2.46590e-5*d,3.3946+2.75e-8*d,54.8910+1.38374e-5*d,.723330,.006773-1.302e-9*d,48.0052+1.6021302244*d),
        (49.5574+2.11081e-5*d,1.8497-1.78e-8*d,286.5016+2.92961e-5*d,1.523688,.093405+2.516e-9*d,18.6021+.5240207766*d),
        (100.4542+2.76854e-5*d,1.3030-1.557e-7*d,273.8777+1.64505e-5*d,5.20256,.048498+4.469e-9*d,19.8950+.0830853001*d),
        (113.6634+2.38980e-5*d,2.4886-1.081e-7*d,339.3939+2.97661e-5*d,9.55475,.055546-9.499e-9*d,316.9670+.0334442282*d),
        (74.0005+1.3978e-5*d,.7733+1.9e-8*d,96.6612+3.0565e-5*d,19.18171-1.55e-8*d,.047318+7.45e-9*d,142.5905+.011725806*d),
        (131.7806+3.0173e-5*d,1.7700-2.55e-7*d,272.8461-6.027e-6*d,30.05826+3.313e-8*d,.008606+2.15e-9*d,260.2471+.005995147*d),
        (0,0,0,0,0,0), # Pluto has its own model below.
        (125.1228-.0529538083*d,5.1454,318.0634+.1643573223*d,60.2666,.054900,115.3654+13.0649929509*d),
    ][body]

def orbit(body,d):
    n,i,w,a,e,m=elements(body,d)
    mr=math.radians(m%360)
    E=mr+e*math.sin(mr)*(1+e*math.cos(mr))
    for _ in range(6):E-=(E-e*math.sin(E)-mr)/(1-e*math.cos(E))
    xv=a*(math.cos(E)-e);yv=a*math.sqrt(1-e*e)*math.sin(E)
    v=atan(yv,xv);r=math.hypot(xv,yv)
    x=r*(cos(n)*cos(v+w)-sin(n)*sin(v+w)*cos(i))
    y=r*(sin(n)*cos(v+w)+cos(n)*sin(v+w)*cos(i))
    z=r*sin(v+w)*sin(i)
    return atan(y,x),atan(z,math.hypot(x,y)),r

def polar(body,d):
    if body==8:
        s=50.03+.033459652*d;p=238.95+.003968789*d
        lon=238.9508+.00400703*d-19.799*sin(p)+19.848*cos(p)+.897*sin(2*p)-4.956*cos(2*p)+.610*sin(3*p)+1.211*cos(3*p)-.341*sin(4*p)-.190*cos(4*p)+.128*sin(5*p)-.034*cos(5*p)-.038*sin(6*p)+.031*cos(6*p)+.020*sin(s-p)-.010*cos(s-p)
        lat=-3.9082-5.453*sin(p)-14.975*cos(p)+3.527*sin(2*p)+1.673*cos(2*p)-1.051*sin(3*p)+.328*cos(3*p)+.179*sin(4*p)-.292*cos(4*p)+.019*sin(5*p)+.100*cos(5*p)-.031*sin(6*p)-.026*cos(6*p)+.011*cos(s-p)
        r=40.72+6.68*sin(p)+6.90*cos(p)-1.18*sin(2*p)-.03*cos(2*p)+.15*sin(3*p)-.14*cos(3*p)
        return lon,lat,r
    lon,lat,r=orbit(body,d)
    j=19.8950+.0830853001*d;s=316.9670+.0334442282*d;u=142.5905+.011725806*d
    if body==4:
        lon+=-.332*sin(2*j-5*s-67.6)-.056*sin(2*j-2*s+21)+.042*sin(3*j-5*s+21)-.036*sin(j-2*s)+.022*cos(j-s)+.023*sin(2*j-3*s+52)-.016*sin(j-5*s-69)
    if body==5:
        lon+=.812*sin(2*j-5*s-67.6)-.229*cos(2*j-4*s-2)+.119*sin(j-2*s-3)+.046*sin(2*j-6*s-69)+.014*sin(j-3*s+32)
        lat+=-.020*cos(2*j-4*s-2)+.018*sin(2*j-6*s-49)
    if body==6:lon+=.040*sin(s-2*u+6)+.035*sin(s-3*u+33)-.015*sin(j-u+20)
    if body==9:
        n,i,w,a,e,m=elements(9,d);_,_,ws,_,_,ms=elements(0,d)
        lm=m+w+n;ls=ms+ws;D=lm-ls;F=lm-n
        lon+=-1.274*sin(m-2*D)+.658*sin(2*D)-.186*sin(ms)-.059*sin(2*m-2*D)-.057*sin(m-2*D+ms)+.053*sin(m+2*D)+.046*sin(2*D-ms)+.041*sin(m-ms)-.035*sin(D)-.031*sin(m+ms)-.015*sin(2*F-2*D)+.011*sin(m-4*D)
        lat+=-.173*sin(F-2*D)-.055*sin(m-F-2*D)-.046*sin(m+F-2*D)+.033*sin(F+2*D)+.017*sin(2*m+F)
        r+=-.58*cos(m-2*D)-.46*cos(2*D)
        r*=6378.14/149597870.7
    return lon,lat,r

def guide(body,d):
    if body==8:return 238.9508+.00400703*d
    n,_,w,_,_,m=elements(0 if body in (1,2) else body,d)
    return n+w+m

def sky(ts):
    if not MIN_TIME<=ts<MAX_TIME:return [(math.nan,math.nan,math.nan)]*10
    d=day(ts);sl,_,sr=polar(0,d);sx=sr*cos(sl);sy=sr*sin(sl)
    out=[]
    for body in range(10):
        lon,lat,r=polar(body,d)
        if body not in (0,9):
            x=r*cos(lon)*cos(lat)+sx;y=r*sin(lon)*cos(lat)+sy;z=r*sin(lat)
            lon=atan(y,x);r=math.sqrt(x*x+y*y+z*z)
        lon%=360
        out.append((lon,guide(body,d)+delta(lon,guide(body,d)),r))
    return out

def speed(body,ts):
    a=max(MIN_TIME,ts-1800000);b=min(MAX_TIME-1,ts+1800000)
    return delta(sky(b)[body][0],sky(a)[body][0])/((b-a)/DAY)

def root(function,a,b,tolerance_ms=1000):
    fa=function(a);fb=function(b)
    if fa*fb>0:raise ValueError('Root is not bracketed')
    for _ in range(32):
        if b-a<=tolerance_ms:break
        m=(a+b)//2;fm=function(m)
        if fa*fm<=0:b=m
        else:a=m;fa=fm
    return (a+b)//2
