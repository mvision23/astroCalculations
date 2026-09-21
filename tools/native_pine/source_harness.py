"""Translate the scalar subset of THIS repository's Pine source for headless tests.

This is deliberately not a Pine compiler or platform emulator. It checks actual
source expressions, not just a second hand-maintained set of orbital constants.
Unsupported syntax fails loudly. Rendering, qualifiers and rollback need TradingView.
"""
import math,re
from pathlib import Path
PINE=Path(__file__).resolve().parents[2]/'pine/bitcoin_universal_clock_native.pine'

def expression(s):
    s=s.strip()
    if s.startswith('[') and s.endswith(']'):
        return '['+expression(s[1:-1])+']'
    # Rewrite nested parentheses first, respecting quoted strings.
    def matching(text,start):
        depth=0;quote=None
        for i in range(start,len(text)):
            c=text[i]
            if quote:
                if c==quote and text[i-1]!='\\':quote=None
            elif c in "\"'":quote=c
            elif c=='(':depth+=1
            elif c==')':
                depth-=1
                if depth==0:return i
        raise ValueError(text)
    out='';i=0
    while i<len(s):
        if s[i] in "\"'":
            q=s[i];j=i+1
            while j<len(s) and (s[j]!=q or s[j-1]=='\\'):j+=1
            out+=s[i:j+1];i=j+1
        elif s[i]=='(':
            j=matching(s,i);out+='('+expression(s[i+1:j])+')';i=j+1
        else:out+=s[i];i+=1
    depth=0; quote=None; cuts=[]
    for index,c in enumerate(out):
        if quote:
            if c==quote and out[index-1]!='\\':quote=None
        elif c in "\"'":quote=c
        elif c in '([':depth+=1
        elif c in ')]':depth-=1
        elif c==',' and depth==0:cuts.append(index)
    if cuts:
        bounds=[-1]+cuts+[len(out)]
        return ','.join(expression(out[a+1:b]) for a,b in zip(bounds,bounds[1:]))
    # Top-level ternary; Pine binds right to left. Parenthesized ones are gone.
    depth=0;quote=None;q=None;nested=0
    for i,c in enumerate(out):
        if quote:
            if c==quote and out[i-1]!='\\':quote=None
            continue
        if c in "\"'":quote=c;continue
        if c in '([':depth+=1
        elif c in ')]':depth-=1
        elif depth==0 and c=='?':
            if q is None:q=i
            else:nested+=1
        elif depth==0 and c==':' and q is not None:
            if nested:nested-=1
            else:
                return '('+expression(out[q+1:i])+' if '+expression(out[:q])+' else '+expression(out[i+1:])+')'
    out=re.sub(r'array\.new<[^>]+>', 'array.new', out)
    out=re.sub(r'\btrue\b','True',out);out=re.sub(r'\bfalse\b','False',out)
    out=re.sub(r'\bna\(','isna(',out);out=re.sub(r'\bna\b','nan',out)
    out=out.replace('math.min(','min(').replace('math.max(','max(').replace('math.abs(','abs(')
    return out

def compile_functions(names,extra=None,source=None):
    source=PINE.read_text() if source is None else source
    functions={}
    for match in re.finditer(r'^(f_\w+)\(([^\n]*)\) =>\n((?:(?:    .*|)\n)+)',source,re.M):
        name,args,body=match.groups()
        if name not in names:continue
        arguments=[]
        for a in args.split(','):
            if a.strip():arguments.append(a.strip().split()[-1])
        lines=body.rstrip().splitlines();code=['def '+name+'('+','.join(arguments)+'):']
        if lines[0].strip().startswith('switch '):
            key=lines[0].strip()[7:]
            for line in lines[1:]:
                left,right=line.strip().split('=>')
                code.append('    '+('if '+key+' == '+left.strip()+':' if left.strip() else 'if True:'))
                code.append('        return '+expression(right))
        else:
            for index,line in enumerate(lines):
                if not line.strip() or line.strip().startswith('//'):continue
                indent=line[:len(line)-len(line.lstrip())];stmt=line.strip()
                stmt=re.sub(r'^(?:float|int|bool|string|Contact|SessionRange|Comparison|array<[^>]+>)\s+','',stmt)
                if stmt.startswith('if '):stmt='if '+expression(stmt[3:])+':'
                elif stmt.startswith('else if '):stmt='elif '+expression(stmt[8:])+':'
                elif stmt=='else':stmt='else:'
                elif stmt.startswith('for '):
                    loop=re.match(r'for (\w+) = (.+) to (.+)',stmt)
                    if loop:
                        var,start,end=loop.groups()
                        stmt=f'for {var} in pine_range({expression(start)}, {expression(end)}):'
                    else:
                        var,items=re.match(r'for (\w+) in (.+)',stmt).groups()
                        stmt=f'for {var} in {expression(items)}:'
                elif stmt in ('break','continue'):pass
                else:
                    assignment=re.match(r'([\w.\[\], ]+?)\s*(:=|\+=|-=|\*=|(?<![<>=!])=(?!=))\s*(.+)',stmt)
                    if assignment:
                        lhs,op,rhs=assignment.groups();stmt=lhs+' '+('=' if op==':=' else op)+' '+expression(rhs)
                    else:stmt=('return ' if index==len(lines)-1 and len(indent)==4 else '')+expression(stmt)
                code.append(indent+stmt)
        functions[name]='\n'.join(code)
    missing=set(names)-functions.keys()
    if missing:raise ValueError(f'Functions not found: {missing}')
    env=dict(pine_range=lambda a,b:range(a,b+(1 if b>=a else -1),1 if b>=a else -1),math=math,nan=math.nan,isna=lambda x:x is None or (isinstance(x,float) and math.isnan(x)),MIN_TIME=1230768000000,MAX_TIME=2556144000000)
    env.update(extra or {})
    for name,code in functions.items():
        try:exec(compile(code,str(PINE)+':'+name,'exec'),env)
        except Exception:raise RuntimeError(code)
    return env

CORE=('f_mod','f_s','f_c','f_atan','f_delta','f_valid','f_day','f_elements','f_orbit','f_polar','f_guide','f_geo','f_position','f_longitude','f_speed')
if __name__=='__main__':
    ns=compile_functions(CORE)
    print(ns['f_position'](8,1789862400000))
