from pathlib import Path
import json,hashlib,re
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter1-climate-20261022'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];errors=[]
def check(ok,text):
 checks.append(text)
 if not ok:errors.append(text)
allowed={'art_atlas','art_layers','art_props','natural_props','nature_layout','visual_ground','material_review_version','climate_review','climate_notes','location_theme','tactical_notes','visual_notes'}
old=read(O/'baseline/maps.json');changed=[];maps={}
for c,h in old.items():
 p=R/f'data/stages/{c}.json';d=read(p);current=sha(p);maps[c]=current
 if current!=h:changed.append(c)
 if c in ['M12','M13','M14','M15','S12']:
  a=read(O/f'baseline/{c}.json');diff={k for k in a.keys()|d.keys()if a.get(k)!=d.get(k)}
  check(diff<=allowed,c+' only approved art and descriptive fields change')
  for k in ['map','logic_grid','objects','player_positions','enemies','npc_units','reinforcements','exit']:
   check(a.get(k)==d.get(k),c+' exact gameplay '+k)
  for prop in ['art_props','natural_props']:
   check(len(a[prop])==len(d[prop]),c+' exact '+prop+' count')
   for i,(before,after)in enumerate(zip(a[prop],d[prop])):
    check({k:v for k,v in before.items()if k not in ['path','key']}=={k:v for k,v in after.items()if k not in ['path','key']},c+' exact prop placement '+prop+str(i))
 else:check(current==h,c+' byte-identical outside winter art correction')
check(set(changed)=={'M12','M13','M14','M15','S12'},'exactly five exterior maps change')
check(sha(R/'data/formal_world.json')==sha(O/'baseline/formal_world.json'),'original world nodes/routes/data byte-identical')
oldnature=read(O/'baseline/nature.json');newnature=read(R/'assets/nature/nature.json')
check(newnature['sprites'][:len(oldnature['sprites'])]==oldnature['sprites'],'all old nature resources unchanged')
check(len(newnature['sprites'])==len(oldnature['sprites'])+4,'only four new winter rock keys')
core=read(O/'baseline/core.json');changedcore=[]
for path,h in core.items():
 if sha(R/path)!=h:changedcore.append(path)
check(set(changedcore)=={'core/main.gd','core/story_hub.gd'},'only world and hub display scripts changed; other core scripts exact')
assets=[]
for p in sorted((R/'assets/chapter1-climate-20261022').rglob('*.png')):
 im=Image.open(p);assets.append({'path':str(p.relative_to(R)),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p)})
 check(im.width>0 and im.height>0,'image decodes '+str(p.relative_to(R)))
world=read(R/'data/chapter1_world_climate.json');atlas=Image.open(R/world['atlas'].removeprefix('res://')).convert('RGBA')
for x,y in read(O/'world/design.json')['ground_changed_cells']:
 t=world['layers'][0][y][x];check(atlas.crop((t%32*16,t//32*16,t%32*16+16,t//32*16+16)).getextrema()[3]==(255,255),'opaque winter terrain edge '+str((x,y)))
result={'passed':not errors,'check_count':len(checks),'errors':errors,'changed_maps':sorted(changed),'unchanged_maps':[c for c in old if c not in changed],'map_hashes':maps,'changed_core':changedcore,'checks':checks,'assets':assets,'scope':'Compare this-turn immutable baseline, not Git which includes earlier approved work. No map logic, actor/object position, route or animation changes.'}
(O/'invariants-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k]for k in ['passed','check_count','errors','changed_maps','changed_core']},ensure_ascii=False));raise SystemExit(0 if not errors else 1)
