#!/usr/bin/env python3
"""Reuse confirmed spell VFX without changing native female-mage actor rows."""
import copy,json,re,hashlib
from build_gallery import ROOT,pack_frame,file_hash
from prepare_female_mage_complete import REV,OUT,write
COMMON=[23,24,25,26,27,28,29,31,32]
def sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 b=json.loads((OUT/'baseline.json').read_text());parents={a['key']:a for a in b['gallery']['actions']};contracts=[]
 for side in ['ally','enemy']:
  timeline={};ids=set()
  for key,v in b['variants'][side].items():
   spell=int(re.search(r'_item_(\d+)',key).group(1))
   if spell not in COMMON:continue
   parent=parents[key.replace('class_16_','class_15_',1)];native=[pack_frame(f)for f in v['frames']];contact=v['contact_tick'];assert contact==parent['contactTick'] and v['actor_origin']==parent['origin']
   template=parent['revisedFrames']+parent.get('reviewTailFrames',[]);last_active=max(i for i,f in enumerate(template)if f['effects']);end=min(len(template)-1,last_active+1);fit=last_active>=len(native)
   revised=copy.deepcopy(native);clock=[]
   for t,f in enumerate(revised):
    # Keep all native preparation and impact ticks. Approved VFX-only endings
    # fit inside this class's own recovery; no extension of actor cycle length.
    n=t if t<=contact or not fit else contact+round((t-contact)*(end-contact)/(len(native)-1-contact))
    clock.append(n);f['effects']=copy.deepcopy(template[n]['effects'] if n<len(template) else []);ids.update(e['sprite']for e in f['effects'])
   event={'parent_action':parent['id'],'native_actor_rows_exact':True,'native_contact_tick':contact,'native_total_ticks':len(native),'parent_template_ticks':len(template),'approved_tail_fitted_to_native_recovery':fit,'last_parent_effect_tick':last_active,'source_tick_by_frame':clock}
   timeline[key]={'source_frames_sha256':sha(native),'frames':revised,'events':event,'note':'女法师依双方原作三姿势程序施法，同名法术复用已确认的术法师／咒法师特效。保留人物帧、位移、释放、结算和总时长；特效收尾安排在原收势阶段内，不新增命中或能力。'};contracts.append({'key':key,'spell_id':spell,'side':side,**event})
  write(OUT/f'{side}-spell-motion.json',{'revision':REV,'effects':{},'actions':timeline,'runtime_integrated':False})
  p=ROOT/f'professions/class-16-{side}/battle/frame_mapping.json';m=json.loads(p.read_text());m.update(review_timeline=f'../../../{REV}/{side}-spell-motion.json',shared_spell_ids=COMMON);write(p,m)
  write(OUT/f'{side}-shared-spell-assets.json',{'effects':[{'id':i,'metadata':b['gallery']['effects'][i],'sha256':file_hash(ROOT/b['gallery']['effects'][i]['path'])}for i in sorted(ids)],'new_effect_assets':0})
 write(OUT/'spell-sharing-contracts.json',{'revision':REV,'contracts':contracts,'native_enemy_special_spell_ids':[33,34]});print(json.dumps({'shared_variants':len(contracts),'new_effect_images':0}),flush=True)
if __name__=='__main__':main()
