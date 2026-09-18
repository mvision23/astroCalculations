"""Explicit local serialization. JSON metadata travels with every CSV bundle."""
from dataclasses import asdict, is_dataclass
from datetime import datetime,date
from pathlib import Path
import csv
import io
import json
import zipfile


def json_default(value):
    if isinstance(value,(datetime,date)):return value.isoformat()
    if is_dataclass(value):return asdict(value)
    if hasattr(value,'item'):return value.item()
    raise TypeError(f'Not serializable: {type(value)}')

def dumps(value):
    return json.dumps(value,default=json_default,indent=2,allow_nan=False)

def csv_text(rows,metadata):
    rows=[asdict(r) if is_dataclass(r) else r for r in rows]
    fields=list(dict.fromkeys(k for r in rows for k in r))
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=['_metadata']+fields)
    writer.writeheader()
    meta=json.dumps(metadata,default=json_default,separators=(',',':'))
    for r in rows:
        values={k:json.dumps(v,default=json_default) if isinstance(v,(dict,list,tuple)) else v.isoformat() if isinstance(v,(datetime,date)) else v for k,v in r.items()}
        writer.writerow(dict(_metadata=meta,**values))
    return out.getvalue()

def result_dict(result):
    return asdict(result)

def bundle(result):
    stream=io.BytesIO();metadata=dict(result.metadata,settings=asdict(result.settings))
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('metadata.json',dumps(metadata));z.writestr('workspace.json',dumps(result.settings))
        for name in ('positions','events','levels','matches','contacts','confluences'):
            z.writestr(name+'.csv',csv_text(getattr(result,name),metadata))
        z.writestr('results.json',dumps(result))
    return stream.getvalue()

def html_chart(fig,metadata):
    import html
    content=fig.to_html(full_html=True,include_plotlyjs=True)
    return content.replace('</body>','<details><summary>Research provenance</summary><pre>'+html.escape(dumps(metadata))+'</pre></details></body>')

def save(path,content,overwrite=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    mode=('w' if overwrite else 'x')+('b' if isinstance(content,bytes) else '')
    with path.open(mode) as f:f.write(content)
    return path.resolve()
