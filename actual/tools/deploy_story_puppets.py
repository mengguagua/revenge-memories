#!/usr/bin/env python3
"""Approved 2026-11-07 roster: 15 puppets / 10 stages, no mechanical reinforcements."""
from pathlib import Path
import json,copy
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
review=read(ROOT.parent/'art-review/character-expansion-20261018/puppet-trio-v3-20261105/design.json')
water=next(u for u in read(ROOT/'data/stages/F21.json')['enemies'] if u.get('mechanical_model')=='water_monkey')
titan=next(u for u in read(ROOT/'data/stages/F25.json')['enemies'] if u.get('mechanical_model')=='pseudo_titan')
def build(model,id,position):
 if model in ['water_monkey','pseudo_titan']:u=copy.deepcopy(water if model=='water_monkey' else titan)
 else:
  d=review['units'][model];u=copy.deepcopy(water)
  u.update(d['stats']);u['max_hp']=u['hp'];u['class_id']={'cyclops':27,'owl':28,'prometheus':29}[model]
  u.update({'name_zh':d['name'],'class_name_zh':d['name'],'class':model,'mechanical_model':model,'mechanical_base_move':d['stats']['move'],'exp_value':d['experience']['level_value']})
  u['parts']={p['id']:{'hp':p['hp'],'max_hp':p['hp'],'defence':p['defence'],'resistance':p['resistance']} for p in d['parts']}
 u['id']=id;u['position']=position;return u
plan={'F24':[('F24_e10','cyclops',[22,8])], 'F26':[('F26_e3','owl',[35,21])], 'F32':[('F32_e3','water_monkey',[22,19]),('F32_e7','cyclops',[25,16])], 'F33':[('F33_e1','pseudo_titan',[21,10]),('F33_e5','owl',[25,11])], 'F41':[('F41_e5','pseudo_titan',[12,6]),('F41_e9','cyclops',[12,7])], 'F42':[('F42_e6','owl',[20,12]),('F42_e9','cyclops',[24,15])], 'F43':[('F43_e4','water_monkey',[8,20]),('F43_e7','owl',[25,18])], 'F44':[('F44_boss','prometheus',[24,7])]}
for code,replacements in plan.items():
 p=ROOT/f'data/stages/{code}.json';j=read(p)
 for id,model,position in replacements:
  i=next(i for i,u in enumerate(j['enemies']) if u['id']==id)
  j['enemies'][i]=build(model,id,position)
  if id==j['boss_id']:j['enemies'][i]['objective_boss']=True
 j['mechanical_revision']='story-20261107';write(p,j)
p=ROOT/'data/stages/F44.json';j=read(p)
# Viser occupies an existing human guard slot on the western side route.
i=next(i for i,u in enumerate(j['enemies']) if u['id'] in ['F44_e4','F44_viser'])
v=copy.deepcopy(next(u for u in j['enemies'] if u['id']=='F44_e10'))
v.update({'id':'F44_viser','name_zh':'维瑟','position':[10,12],'behavior':'guard','move':0,'no_drop':True});j['enemies'][i]=v
j['objects']=[o for o in j['objects'] if o['id']!='maintenance_panel']+[{'id':'maintenance_panel','kind':'control','position':[8,12],'label':'请求普罗米修斯检修','optional':True,'approaches':[[8,13],[9,12],[7,12]],'sprite':'control_panel'}]
for u in j['enemies']:
 if u['id'] in ['F44_e10','F44_e11']:u['viser_guard']=True
j['goal']='制服维瑟，接管三处调节点并保护工匠完成试验；最终击毁或请求自愿检修，并击退其余守军。'
write(p,j)
p=ROOT/'data/stages/M51.json';j=read(p);next(u for u in j['enemies'] if u['id']==j['boss_id'])['name_zh']='雷蒙';j['goal']=j['goal'].replace('队长','雷蒙');write(p,j)
p=ROOT/'data/enemy_experience_20261104.json';j=read(p)
for model,cid in [('cyclops',27),('owl',28),('prometheus',29)]:j['class_bases'][str(cid)]={'name_zh':review['units'][model]['name'],'base':review['units'][model]['experience']['base_value']}
j['bosses']['408']['base']=90;write(p,j)
# Runtime content uses the new named boss everywhere the map summary names him.
p=ROOT/'data/campaign.json';j=read(p);j['stages']['501']['boss_name']='雷蒙';write(p,j)
report=[]
for p in sorted((ROOT/'data/stages').glob('*.json')):
 j=read(p);units=[u for u in j['enemies'] if u.get('unit_kind')=='mechanical_puppet']
 if units:report.append({'stage':j['code'],'units':[{k:u[k] for k in ['id','name_zh','level','hp','strength','skill','speed','defence','resistance','move','exp_value','position','parts']} for u in units]})
assert sum(len(r['units']) for r in report)==15
(ROOT/'reports/dialogue-ch2-5-20261107/deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('15 puppets in',len(report),'stages')
