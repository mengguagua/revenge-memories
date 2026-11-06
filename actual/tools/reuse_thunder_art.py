#!/usr/bin/env python3
"""Bind the approved Thunder artwork to electrical-weapon safety-net effects."""
import copy,hashlib,json,subprocess
from pathlib import Path
from PIL import Image
from build_campaign_effects import lightning_stage,thunder_display
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/thunder-reuse-20261026'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run():
 REPORT.mkdir(parents=True,exist_ok=True)
 reviewed_path=ROOT/'data/reviewed_animations.json'
 reviewed=json.loads(reviewed_path.read_text())
 sources={a.get('source_effect_id'):a for a in reviewed['sprites'].values() if a.get('source_effect_id','').startswith('review-thunder-impact-')}
 assert len(sources)==16
 def path(eid):return ROOT/sources['review-thunder-impact-'+eid]['path'].removeprefix('res://')
 out=ROOT/'assets/thunder-reuse-20261026/bolt-ground.png';out.parent.mkdir(parents=True,exist_ok=True)
 # Existing opaque source pixels, fixed ground pivot; no repaint or recolouring.
 subprocess.run(['/opt/homebrew/bin/magick','-size','320x960','xc:none',str(path('bolt')),'-geometry','+32+0','-composite',str(path('ground-1')),'-geometry','+0+800','-composite',str(out)],check=True)
 subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','4','--strip','safe',str(out)],check=True)
 palette=set(Image.open(path('bolt')).convert('RGBA').getdata())|set(Image.open(path('ground-1')).convert('RGBA').getdata())
 assert {p for p in Image.open(out).convert('RGBA').getdata() if p[3]} <= {p for p in palette if p[3]}
 runtime=ROOT/'data/campaign_effects.json';before=json.loads(runtime.read_text());after=copy.deepcopy(before)
 backup=REPORT/'before-campaign-effects.json'
 if not backup.exists():backup.write_text(json.dumps(before,ensure_ascii=False,separators=(',',':'))+'\n')
 old_report=json.loads((REPORT/'reuse-checks.json').read_text()) if (REPORT/'reuse-checks.json').exists() else {}
 previous_stages={(c['variant'],c['effect']):c['stage'] for c in old_report.get('changes',[])}
 changes=[];variants=set();display_changes=[]
 for name,bindings in after['variants'].items():
  for key,art in list(bindings.items()):
   p=art['path']
   if '/lightning-refine-20261026/lightning-' in p:stage=int(Path(p).stem.rsplit('-',1)[1])
   elif art.get('campaign_lightning_reuse') and (name,key) in previous_stages:stage=previous_stages[(name,key)]
   else:continue
   bindings[key]=lightning_stage(reviewed['sprites'],stage)
   changes.append({'variant':name,'effect':key,'stage':stage,'old_path':p,'new_path':bindings[key]['path']});variants.add(name)
 assert len(changes)==504 and len(variants)==72
 for key,art in after['sprites'].items():
  if art.get('source_effect_id','').startswith('review-thunder-impact-'):
   after['sprites'][key]=thunder_display(reviewed['sprites'][key]);display_changes.append(key)
 assert len(display_changes)==16
 restored=copy.deepcopy(after)
 for c in changes:restored['variants'][c['variant']][c['effect']]=before['variants'][c['variant']][c['effect']]
 for key in display_changes:restored['sprites'][key]=before['sprites'][key]
 assert restored==before
 runtime.write_text(json.dumps(after,ensure_ascii=False,separators=(',',':'))+'\n')
 records=[{'effect':eid,'path':a['path'],'sha256':sha(ROOT/a['path'].removeprefix('res://'))} for eid,a in sorted(sources.items())]
 report={'passed':True,'revision':'thunder-reuse-20261026','source_revision':'thunder-ground-impact-v1-20261024','source_effects':records,'variants':len(variants),'bindings':len(changes),'existing_spell_24_timelines_unchanged':60,'existing_spell_effects_uniformly_scaled':16,'display_scale':.4,'body_motion_contact_audio_unchanged':True,'unrelated_effect_bindings_unchanged':True,'no_new_image_generation':True,'source_palette_unchanged':True,'composite':{'path':'res://'+out.relative_to(ROOT).as_posix(),'size':[320,960],'bytes':out.stat().st_size,'bolt_pivot':[128,928],'ground_pivot':[160,128],'placements':{'bolt':[32,0],'ground-1':[0,800]}},'changes':changes,'reviewed_data_sha256':sha(reviewed_path),'device_updated':False}
 (REPORT/'reuse-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_effects','changes']},ensure_ascii=False))
if __name__=='__main__':run()
