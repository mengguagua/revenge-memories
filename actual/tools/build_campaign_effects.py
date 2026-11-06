#!/usr/bin/env python3
"""Replace exact source-pixel copies with approved campaign effects in runtime indexes."""
import collections,copy,hashlib,json,math,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/new-art-fallback-20261026'
def digest(path):
 im=Image.open(path).convert('RGBA');return (im.size,hashlib.sha256(im.tobytes()).hexdigest())
def dimensions(art):
 return art.get('logical_frame_size',[x/float(art.get('native_density',1)) for x in art['frame_size']])
def thunder_display(art):
 """Fit the existing tall review effect uniformly inside the battle field."""
 result=copy.deepcopy(art)
 result['logical_frame_size']=[round(v/float(art['native_density'])*.4,3) for v in art['frame_size']]
 result['anchor']=[round(art['anchor'][0]*.4,3),round(art['anchor'][1]*.4+3.2,3)]
 result['flip_origin_offset']=[0,0]
 result['campaign_anchor_role']='defender'
 result['campaign_thunder_display_scale']=.4
 return result
def lightning_stage(sprites,stage):
 """Reuse the confirmed Thunder art; never substitute newly generated bolts."""
 names=['ground-0','ground-1','fall-4','bolt',None,'ground-3','ground-4','fade-2']
 if stage==4:
  art={'path':'res://assets/thunder-reuse-20261026/bolt-ground.png','frame_size':[320,960],'frames':1,'columns':1,'native_density':4,'flip_origin_offset':[0,0]}
 else:
  eid='review-thunder-impact-'+names[stage]
  art=copy.deepcopy(next(row for row in sprites.values() if row.get('source_effect_id')==eid))
 factor=.25 if stage<2 else .4
 size=[round(v/float(art['native_density'])*factor,3) for v in art['frame_size']]
 art.update(logical_frame_size=size,anchor=[size[0]/2,size[1]/2 if stage<2 else size[1]],flip_origin_offset=[0,0],campaign_effect_fallback=True,campaign_lightning_reuse='thunder-ground-impact-v1-20261024',campaign_anchor_role='attacker_charge' if stage<2 else 'defender')
 return art
def fit(new,old):
 result=copy.deepcopy(new);w,h=dimensions(new);ow,oh=dimensions(old)
 ratio=min(max(8,min(ow,96))/max(1,w),max(8,min(oh,128))/max(1,h))
 size=[round(w*ratio,3),round(h*ratio,3)]
 result['logical_frame_size']=size
 result['anchor']=[round(old['anchor'][i]*size[i]/max(1,[ow,oh][i]),3) for i in range(2)]
 result['flip_origin_offset']=[round(old.get('flip_origin_offset',[0,0])[i]*size[i]/max(1,[ow,oh][i]),3) for i in range(2)]
 result['campaign_effect_fallback']=True
 return result
def category(name):
 name=name.rsplit('/',1)[-1]
 if '_item_' in name:return int(name.split('_item_',1)[1].split('_')[0])
 if 'levin' in name:return 15
 if 'javelin' in name:return 4
 if 'bow' in name:return 1
 return 0
def build():
 originals={digest(p) for p in (ROOT/'assets/original/graphics').rglob('*.png')}
 exact=[];hasher={}
 for p in sorted((ROOT/'assets').rglob('*.png')):
  if 'original' in p.parts:continue
  value=digest(p);hasher['res://'+p.relative_to(ROOT).as_posix()]=value
  if value in originals:exact.append(p.relative_to(ROOT).as_posix())
 bad={'res://'+p for p in exact}
 source=json.loads((ROOT/'data/reviewed_animations.json').read_text());sprites=source['sprites']
 good={key:row for key,row in sprites.items() if row['path'] not in bad}
 by_oam=collections.defaultdict(list);pools=collections.defaultdict(set)
 for key,row in good.items():
  if row.get('source_oam'):by_oam[row['source_oam']].append(key)
 for name,variant in source['variants'].items():
  for row in variant['frames']:
   for effect in row.get('effects',[]):
    if effect['sprite'] in good:pools[category(name)].add(effect['sprite'])
 def custom(path,anchor):
  im=Image.open(ROOT/path);return {'path':'res://'+path,'frame_size':list(im.size),'frames':1,'columns':1,'anchor':anchor,'native_density':4.0,'flip_origin_offset':[0,0]}
 light=[lightning_stage(good,i) for i in range(8)]
 spear=custom('assets/fallback-effects-20261026/javelin.png',[25,7])
 arrow=custom('assets/party-0.7.0/party4_arrow_m11_wooden_arrow.png',[24,8])
 neutral=good['review-halo-ally-charge-8198b40abef726']
 def nearest(old,candidates):
  ow,oh=dimensions(old)
  return min(candidates,key=lambda k:abs(math.log((dimensions(good[k])[0]+1)/(ow+1)))+abs(math.log((dimensions(good[k])[1]+1)/(oh+1))))
 clean=copy.deepcopy(good)
 for key,row in list(clean.items()):
  if row.get('source_effect_id','').startswith('review-thunder-impact-'):clean[key]=thunder_display(row)
 for key,row in sprites.items():
  if key in good:continue
  choices=by_oam.get(row.get('source_oam',''),[])
  clean[key]=fit(good[nearest(row,choices)] if choices else neutral,row)
 variants={};changes=0
 for name,var in source['variants'].items():
  used={e['sprite'] for f in var['frames'] for e in f.get('effects',[])}
  old_ids=used-set(good)
  cat=category(name)
  if cat==4:old_ids=used
  if not old_ids:continue
  replacements={}
  local=sorted(used&set(good))
  for key in sorted(old_ids):
   old=sprites[key];first=next(i for i,f in enumerate(var['frames']) if any(e['sprite']==key for e in f.get('effects',[])))
   if cat==15:
    contact=int(var.get('contact_tick',len(var['frames'])//2))
    stage=0 if first<contact*.25 else 1 if first<contact*.5 else 3 if first<contact-2 else 4 if first<=contact+2 else 5 if first<contact+12 else 6 if first<contact+25 else 7
    art=light[stage]
   elif cat==4:art=spear
   elif cat==1:art=arrow
   else:
    choices=by_oam.get(old.get('source_oam',''),[]) or local or sorted(pools[cat])
    art=good[nearest(old,choices)] if choices else neutral
   replacement=copy.deepcopy(art) if cat==15 else fit(art,old)
   if cat==4:
    replacement['logical_frame_size']=[48,13.44];replacement['anchor']=[24,6.72];replacement['flip_origin_offset']=[0,0]
   replacements[key]=replacement;changes+=1
  variants[name]=replacements
 data={'revision':'campaign-effects-20261026','sprites':clean,'variants':variants,'excluded_exact_copy_paths':['res://'+p for p in exact]}
 (ROOT/'data/campaign_effects.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
 # The indexed originals remain offline for provenance; no renamed copies ship.
 cfg=ROOT/'export_presets.cfg';text=cfg.read_text();prior=OUT/'effect-replacements.json'
 previous=set(json.loads(prior.read_text()).get('excluded_paths',[])) if prior.exists() else set()
 lines=[]
 for line in text.splitlines():
  if line.startswith('exclude_filter='):
   values=[v for v in line.split('"')[1].split(',') if v not in previous]
   values.extend(p for p in exact if p not in values);line='exclude_filter="'+','.join(values)+'"'
  lines.append(line)
 cfg.write_text('\n'.join(lines)+'\n')
 report={'all_images_scanned':len(hasher),'original_reference_images':len(originals),'exact_copies_excluded':len(exact),'excluded_paths':exact,'retargeted_variant_bindings':changes,'affected_variants':len(variants),'body_frame_arrays_modified':False,'contacts_modified':False,'audio_modified':False}
 prior.write_text(json.dumps(report,indent=2))
 print({k:v for k,v in report.items() if k!='excluded_paths'})
if __name__=='__main__':build()
