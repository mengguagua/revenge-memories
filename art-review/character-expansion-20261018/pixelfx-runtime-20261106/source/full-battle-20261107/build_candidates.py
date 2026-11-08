from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/'runtime-snapshot/data/reviewed_animations.json').read_text())
candidates=[]
for profile,art in D['battle'].items():
 side=art.get('reviewed_side','ally');cid=int(art['reviewed_class_id'])
 for alias,key in art.get('reviewed_variants',{}).items():
  match=re.search(r'_item_(\d+)',alias)
  weapon=int(match[1]) if match else 15 if 'levin' in alias else 4 if 'javelin' in alias else 22 if 'silver_bow' in alias else 1 if 'bow' in alias else 0
  innate={'stone-claw':1001,'stone-spit':1002,'stone-spit-far':1002,'bone-bite':1003,'innate-bone-bite':1003,'original_class_5_enemy_normal':1003,'eroding-breath':1004,'innate-eroding-breath':1004,'eroding-breath-far':1004,'wing-beak':1005,'sun-crown':1006,'sun-crown-far':1006}
  if alias in innate:weapon=innate[alias]
  far='ally' if '_far_ally' in alias or alias.endswith('-far') else 'enemy' if '_far_enemy' in alias else ''
  family='support' if weapon in [40,41,43,44] else 'magic' if 23<=weapon<=46 else 'archery' if weapon in [1,22] else 'javelin' if weapon in [4,7] else 'lightning-sword' if weapon==15 else 'monster' if side=='enemy' and cid in [3,5,11,17,18,21] else 'lance' if cid in [1,2,3,4,5,6,7,22] else 'sword'
  identity=profile+'|'+alias
  candidates.append({'id':hashlib.sha256(identity.encode()).hexdigest()[:12],'profile':profile,'class_id':cid,'side':side,'alias':alias,'expected_program':key,'weapon':weapon,'far':far,'heavy':alias.endswith('_vs_heavy'),'critical':alias.endswith('_critical'),'family':family})
(ROOT/'candidates.json').write_text(json.dumps({'raw_programs':len(D['variants']),'profiles':len(D['battle']),'candidates':candidates},ensure_ascii=False,indent=2))
print('Candidates',len(candidates),'profiles',len(D['battle']),'raw programs',len(D['variants']))
