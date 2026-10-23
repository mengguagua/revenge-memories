#!/usr/bin/env python3
"""Static local report integrity. This does not emulate browser layout."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from PIL import Image
import json

O = Path(__file__).resolve().parents[1]/'reports/chapter5-environment-20261023'
errors, checks = [], []
def check(ok, text):
    checks.append(text)
    if not ok: errors.append(text)
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.links=[]; self.images=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        for k in ['href','src']:
            if k in a:self.links.append(a[k])
        if tag=='img':self.images.append(a)

for name in ['index.html','hubs/index.html']:
    path=O/name; text=path.read_text(); p=Page(); p.feed(text)
    check(len(p.ids)==len(set(p.ids)),name+' unique section IDs')
    check('<meta name="viewport"' in text,name+' responsive viewport')
    check(not any(x in text for x in ['undefined','NaN','None']),name+' no unresolved values')
    for link in p.links:
        u=urlsplit(link)
        if u.scheme or u.netloc:continue
        target=(path.parent/unquote(u.path)).resolve()if u.path else path
        check(target.exists(),name+' target '+link)
        if u.fragment and target.suffix=='.html' and target.exists():
            q=Page();q.feed(target.read_text());check(u.fragment in q.ids,name+' anchor '+link)
    for a in p.images:
        check(bool(a.get('alt')),name+' alt '+a['src'])
        im=Image.open(path.parent/a['src']);check(im.width>0 and im.height>0,name+' PNG '+a['src'])
    if name=='index.html':
        for code in ['M51','M52','F51','F52','S51','J53','J54']:check(code in p.ids,'map section '+code)
    else:
        for room in ['H51','H52','H53','H54','H55','H56']:check(room in p.ids,'hub section '+room)
summary=json.loads((O/'delivery-summary.json').read_text())
check(summary['native_viewports']==54,'54 actual current viewports')
check(summary['per_map_inputs']==25229,'14 selected final-version victories total')
result=dict(passed=not errors,checks=len(checks),errors=errors,scope='Static HTML link, anchor, image, alt and section integrity; no browser layout engine.',layout_verified=False)
(O/'page-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False));assert not errors
