import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'reports/enemy-deployment-20261023'
base=json.loads((out/'baseline.json').read_text());checks=[];errors=[];changed=[];classes=set()
def check(value,label):
 checks.append(label)
 if not value:errors.append(label)
for code,b in base.items():
 d=json.loads((root/f'data/stages/{code}.json').read_text())
 check(hashlib.sha256(json.dumps(d['map'],sort_keys=True).encode()).hexdigest()==b['map_sha256'],code+' layout unchanged')
 for k in ['goal','boss_id','objects','npcs','exit','deployment']:
  check(d.get(k)==b[k],code+' preserves '+k)
 for field in ['enemies','reinforcements']:
  old={u['id']:u for u in b[field]};new={u['id']:u for u in d.get(field,[])}
  check(list(old)==list(new),code+' enemy counts and identities '+field)
  check(all(new[i]['position']==old[i]['position'] for i in old),code+' authored positions '+field)
  for uid,u in new.items():
   if u['class_id']!=old[uid]['class_id']:changed.append({'stage':code,'id':uid,'class_before':old[uid]['class_id'],'class_after':u['class_id'],'name':u['name_zh'],'move':u['move'],'strength':u['strength'],'hp':u['max_hp']})
for p in (root/'data/stages').glob('*.json'):
 d=json.loads(p.read_text())
 for u in d.get('enemies',[])+d.get('reinforcements',[]):classes.add(u['class_id'])
check(classes==set(range(1,23)),'all 22 defined enemy classes deployed; reserved23/24 absent')
(out/'deployment-checks.json').write_text(json.dumps(dict(passed=not errors,checks=checks,errors=errors,changed=changed,classes=sorted(classes)),ensure_ascii=False,indent=2)+'\n')
print(len(checks),'deployment checks;',errors)
assert not errors
