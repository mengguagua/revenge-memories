#!/usr/bin/env python3
"""Reuse approved spell effects while preserving class11 native actor programs."""
from baseline_json import read_baseline
import json,copy,re
from build_gallery import ROOT,pack_frame,file_hash
from prepare_spellsword_complete import REV,OUT,write
from share_sage_mage_spells import COMMON,transfer

def main():
 b=read_baseline(OUT/'baseline.json');d=b['gallery'];parents={a['key']:a for a in d['actions']};mp=ROOT/'professions/class-15-ally/battle/frame_mapping.json';mm=json.loads(mp.read_text());mt=json.loads((mp.parent/mm['review_timeline']).resolve().read_text());revised={};contracts=[]
 for key,v in b['variants'].items():
  match=re.search(r'_item_(\d+)',key)
  if not match or int(match[1])not in COMMON:continue
  mk=key.replace('class_11_','class_15_',1);mage=parents[mk];own={'key':key,'id':'professions-class-11-ally-battle--'+key,'frames':[pack_frame(f)for f in v['frames']],'contactTick':v['contact_tick'],'origin':v['actor_origin']};row,c=transfer(mage,own,mt['actions'][mk]);row['note']='与术法师同名法术共用已确认特效。女魔剑士人物姿势、原始准备／释放阶段、结算、回位与总时长保持；冰晶剑仅改变武器外观，不增加冰冻能力。';revised[key]=row;contracts.append({'key':key,**c})
 assert len(revised)==54
 ids=sorted({e['sprite']for a in revised.values()for f in a['frames']for e in f['effects']})
 write(OUT/'shared-spell-motion.json',{'revision':REV,'runtime_integrated':False,'effects':{},'actions':revised});write(OUT/'spell-sharing-contracts.json',{'revision':REV,'contracts':contracts,'new_effect_images':0});write(OUT/'shared-spell-assets.json',{'effects':[{'id':i,'metadata':d['effects'][i],'sha256':file_hash(ROOT/d['effects'][i]['path'])}for i in ids]})
 p=ROOT/'professions/class-11-ally/battle/frame_mapping.json';m=json.loads(p.read_text());m.update(review_timeline='../../../'+REV+'/shared-spell-motion.json',shared_spell_ids=COMMON);write(p,m);print(json.dumps({'shared_spell_variants':54,'shared_assets':len(ids)}),flush=True)
if __name__=='__main__':main()
