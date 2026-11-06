#!/usr/bin/env python3
"""Reuse confirmed spell artwork without changing saint actor rows or resolution."""
import copy,json,re
from build_gallery import ROOT
from prepare_healer_saint_complete import REV,OUT,write
from share_sage_mage_spells import COMMON,transfer,sha
from revise_spellsword_jump_heal_v3 import effect_center
def main():
 d=json.loads((ROOT/'demos/gallery-data.json').read_text());actions={a['key']:a for a in d['actions']if a['context']=='battle'and a['kind']=='attack'};mp=ROOT/'professions/class-15-ally/battle/frame_mapping.json';mm=json.loads(mp.read_text());mt=json.loads((mp.parent/mm['review_timeline']).resolve().read_text());revised={};contracts=[]
 for a in actions.values():
  if a['profile']!='professions-class-17-ally-battle':continue
  spell=int(re.search(r'_item_(\d+)',a['key']).group(1))
  if spell in COMMON:
   parent=actions[a['key'].replace('class_17_','class_15_',1)];row,contract=transfer(parent,a,mt['actions'][parent['key']]);row['note']='济世术师同名攻击法术与术法师共用已确认特效；宝瓶及施法手势按本职业原作程序，准备、释放、结算、收势和总时长保持，不增加命中或能力。';revised[a['key']]=row;contracts.append(contract)
  elif spell==40:
   rows=copy.deepcopy(a['frames']);contact=a['contactTick'];start=contact+12;end=start+36;assert end<=len(rows);target=effect_center(d,a['frames'][contact]['effects'][0]);count=0
   for t,row in enumerate(rows):
    if t<start:
     for e in row['effects']:
      nid='ally_heal_green_v3_'+e['sprite'];assert nid in d['effects'],(a['key'],e['sprite']);e['sprite']=nid;count+=1
    elif t<end:row['effects']=[{'sprite':'ally_heal_green_rain_v3_'+str((t-start)//6+1),'position':target,'flip':False}]
    else:row['effects']=[]
   assert count
   contract={'key':a['key'],'spell_id':40,'contact':contact,'native_total_ticks':len(rows),'rain_start':start,'rain_end_exclusive':end,'target':target,'additional_heals':0,'native_actor_rows_kept':True};revised[a['key']]={'source_frames_sha256':sha(a['frames']),'frames':rows,'events':contract,'note':'友方恢复共用已确认绿色光环，结尾化成绿色雨滴；济世术师原作人物动作、唯一恢复结算、目标、收势和总时长保持。'};contracts.append(contract)
 assert len(revised)==60
 write(OUT/'saint-shared-motion.json',{'revision':REV,'runtime_integrated':False,'effects':{},'actions':revised,'shared_effect_owners':['class-15-ally','class-11-ally']});write(OUT/'spell-contracts.json',{'contracts':contracts,'native_support_items_unchanged':[41,42,43,44],'new_spell_abilities':0,'new_effect_images':0})
 p=ROOT/'professions/class-17-ally/battle/frame_mapping.json';m=json.loads(p.read_text());m.update(review_timeline='../../../'+REV+'/saint-shared-motion.json',shared_spell_ids=COMMON,heal_effect_revision='spellsword-jump-heal-v3-20261023');write(p,m)
 drafts=json.loads((OUT/'mapping-drafts.json').read_text());drafts[str(p.relative_to(ROOT))]=m
 for c in[18,17]:drafts[f'professions/class-{c}-ally/maps/frame_mapping.json']=json.loads((ROOT/f'professions/class-{c}-ally/maps/frame_mapping.json').read_text())
 write(OUT/'mapping-drafts.json',drafts);print(json.dumps({'shared_attack_variants':54,'green_heal_variants':6,'native_other_support_variants':24}),flush=True)
if __name__=='__main__':main()
