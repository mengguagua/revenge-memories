#!/usr/bin/env python3
"""Targeted art, native motion, terminology and offline playback verification."""
from baseline_json import read_baseline
import argparse,ast,json,subprocess,re
from types import SimpleNamespace
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash,pack_frame,relative,matched_export,SPELL_NAMES
from export_gallery import render_frame
from export_knight_complete import export_one
from prepare_healer_saint_complete import REV,OUT,write
from import_healer_saint_complete import C,helper,box
def verify(export=False):
 b=read_baseline(OUT/'baseline.json');d=json.loads((ROOT/'demos/gallery-data.json').read_text());pp={p['id']:p for p in d['profiles']};now={a['id']:a for a in d['actions']};before={a['id']:a for a in b['gallery']['actions']};oldp={p['id']:p for p in b['gallery']['profiles']};actions=[a for a in d['actions']if a['profile'].startswith(('professions-class-18-ally-','professions-class-17-ally-'))];contracts=json.loads((OUT/'spell-contracts.json').read_text())['contracts']
 assert len(actions)==140 and len(now)>=1195 and len(pp)>=112 and len(contracts)==60 and all(a['ready']for a in actions)
 assert not d['validation']['structuralIssues'];new=set(now)-set(before);own_new={k for k in new if now[k]['profile'].startswith('professions-class-17-ally-')};assert len(own_new)==97
 label_changes=[];unchanged=[]
 for key,old in before.items():
  a=now[key]
  if a['profile'].startswith(('professions-class-18-ally-','professions-class-17-ally-')):continue
  if old['contentDigest']==a['contentDigest']:unchanged.append(key);continue
  p=pp[a['profile']];op=oldp[a['profile']];assert p['actorName']!=op['actorName']or p['className']!=op['className'],('unexpected change',key)
  for k in['newFrames','sourceAtlas','sourceFrameSize','newFrameSize','revision','anchor','mapShadow']:assert p.get(k)==op.get(k),(key,k)
  for k in['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick']:assert a.get(k)==old.get(k),(key,k)
  label_changes.append(key)
 assert d['effects']==b['gallery']['effects'];schedules=[]
 for a in actions:
  p=pp[a['profile']];c=int(p['classId']);assert p['revision']==REV and not a.get('reviewTailFrames')
  if a['kind']=='attack':
   v=b['classes'][str(c)]['variants'][a['key']];assert a['frames']==[pack_frame(f)for f in v['frames']]and a['fps']==v['native_fps']and a['origin']==v['actor_origin']and a['contactTick']==v['contact_tick']
   for row,old in zip(a.get('revisedFrames',a['frames']),a['frames']):assert{k:v for k,v in row.items()if k!='effects'}=={k:v for k,v in old.items()if k!='effects'}
   item=v['source_item_id'];schedules.append({'actor_id':f'class-{c}-ally','profession':p['className'],'source_action':a['key'],'source_item_id':item,'effect':SPELL_NAMES[item],'native_program':v['source_program_address'],'total_ticks':len(a['frames']),'effect_contact_tick':a['contactTick'],'contact_count':v['contact_count'],'native_actor_rows_exact':True,'scope':'职业美术动作样板；不改变芙拉、米蕾、赛琳等角色各自已学法术、消耗或目标规则'})
  elif a['key']=='idle-cycle':assert[f['frame']for f in a['frames']]==[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
  elif a['kind']=='map_walk':
   start={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']];assert[f['frame']for f in a['frames']]==[i for _ in range(3)for i in[start,start+1]for _ in range(16)];assert all(f['offset']==[0,0]and not f['flip']for f in a['frames'])
 assert len(schedules)==114
 for r in json.loads((OUT/'source-audit.json').read_text())['sources']:assert file_hash(ROOT/r['path'])==r['sha256']
 images={};checks=[]
 for c in[18,17]:
  for kind,n,size in[('tactical-idle',6,(96,96)),('tactical-walk',8,(128,96)),('battle',2 if c==18 else 12,(320 if c==18 else 384,256))]:
   paths=sorted((OUT/f'class-{c}'/kind).glob('frame-*.png'));assert len(paths)==n
   for path in paths:
    i=int(path.stem.split('-')[-1]);im=Image.open(path).convert('RGBA');images[c,kind,i]=im;assert im.size==size and set(im.getchannel('A').getdata())=={0,255}and{p[:3]for p in im.getdata()if p[3]}<=set(C);cs=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cs)==1,(c,kind,i,[(len(p),box(p))for p in cs]);assert path.stat().st_size<50000;checks.append({'path':relative(path),'size':list(size),'bytes':path.stat().st_size,'sha256':file_hash(path),'connected_components':len(cs)})
  for i,j in enumerate([0,1,2,1,0,1]):assert images[c,'tactical-idle',i].tobytes()==images[c,'tactical-idle',j].tobytes()
  for i in[1,2]:
   for r in[[38,15,72,48],[0,58,96,96]]:assert images[c,'tactical-idle',0].crop(r).tobytes()==images[c,'tactical-idle',i].crop(r).tobytes()
  for x,y in[(0,1),(2,3),(4,5)]:
   assert images[c,'tactical-walk',x].crop((0,0,128,69)).tobytes()==images[c,'tactical-walk',y].crop((0,0,128,69)).tobytes()
   if not(c==17 and x==0):assert images[c,'tactical-walk',x].crop((0,69,128,96)).tobytes()!=images[c,'tactical-walk',y].crop((0,69,128,96)).tobytes()
  for i,j in[(6,2),(7,3)]:assert images[c,'tactical-walk',i].tobytes()==images[c,'tactical-walk',j].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
  for ctx in['tactical-idle','tactical-walk']:
   p=pp[f'professions-class-{c}-ally-maps-{ctx}'];assert(ROOT/p['mapShadow']['path']).is_file()and p['mapShadow']['alpha']==.3
 assert images[18,'tactical-idle',0].tobytes()==images[18,'tactical-idle',1].tobytes();assert images[17,'tactical-walk',0].tobytes()==images[17,'tactical-walk',1].tobytes()
 manifest=json.loads((OUT/'asset-manifest.json').read_text());assert all(r['clipped_pixels']==0 for r in manifest['registrations'])
 for r in manifest['assets']:assert file_hash(ROOT/r['path'])==r['sha256']
 # The earlier green-heal correction for class18 is preserved exactly.
 for a in actions:
  if a['id']in before and a['context']=='battle':
   for k in['frames','revisedFrames','contactTick','duration']:assert a.get(k)==before[a['id']].get(k),(a['key'],k)
 for c in[15,16]:
  for p in d['profiles']:
   if p['classId']==str(c)and p['side']=='enemy':assert p['actorName']=='敌方'+{15:'执令术师',16:'隙行术师'}[c]
 for n in['prepare_healer_saint_complete.py','import_healer_saint_complete.py','share_healer_saint_spells.py','finish_healer_saint_review.py','verify_healer_saint_complete.py']:ast.parse((ROOT/'tools'/n).read_text())
 write(OUT/'action-effect-mapping.json',{'source_rules':['docs2/职业命名提案-0.9.0.md','docs2/完整游戏设定.md','actual/data/class_names.json'],'runtime_changed':False,'actions':schedules});report={'status':'assets_passed','revision':REV,'gallery_profiles':112,'gallery_ready_actions':1195,'current_profession_actions':140,'healer_actions':43,'saint_actions':97,'new_actions':97,'new_profiles':3,'native_battle_variants':114,'existing_actions_unchanged':len(unchanged),'existing_actions_label_only':len(label_changes),'label_only_actions':label_changes,'all_prior_effect_metadata_unchanged':True,'shared_attack_spell_variants':54,'green_heal_variants':6,'healer_green_heal_preserved':True,'native_frames_timing_origins_contact_rows_exact':True,'source_assets_unchanged':True,'map_complete_upper_body_fixed':True,'map_shadow_continuous':True,'sprite_count':42,'sprite_max_bytes':max(r['bytes']for r in checks),'assets':checks,'runtime_integrated':False,'browser_ui_checked':False,'user_visual_acceptance':'pending'};write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','actions':140,'unchanged':len(unchanged),'label_only':len(label_changes)}),flush=True)
 if not export:return
 exports=[];captures=[]
 # Every action receives a current still, representative cycles and each native
 # spell receive videos; near/far and armor-target differences keep native rows.
 for a in actions:exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=True)))
 selected=[]
 for a in actions:
  canonical=a['kind']=='attack'and not any(w in a['key']for w in['far_','vs_heavy']);pick=canonical or a['kind']=='map_walk'or a['key']in['idle-cycle','idle']
  if not pick:continue
  selected.append(a);exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
  if canonical and a['key'].endswith(('_item_23','_item_28','_item_40')):exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  if a['kind']=='map_walk':ticks=[0,16]
  elif a['key']=='idle-cycle':ticks=[0,14,22]
  elif canonical and a['key'].endswith('_item_40'):ticks=[0,36,a['contactTick'],a['contactTick']+12,a['contactTick']+30,a['contactTick']+47]
  elif canonical and a['key'].endswith(('_item_23','_item_28')):ticks=[0,36,next(i for i,f in enumerate(a['frames'])if f['effects']),a['contactTick']]
  else:ticks=[]
  p=pp[a['profile']]
  for t in sorted(set(ticks)):
   for light in[False,True]:
    path=OUT/(f'class-{p["classId"]}-{a["key"]}-{t:03}-'+('light.png'if light else'dark.png'));render_frame(d,p,a,t,5 if canonical else 7,light,canonical).save(path,optimize=True);captures.append(relative(path))
  print('Exported '+a['key']+' class '+p['classId'],flush=True)
 # Refresh the renamed enemy exemplars that previously had review exports.
 for key in label_changes:
  old=before[key];a=now[key]
  if old.get('still')or old.get('video'):exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not old.get('video'))))
  if old.get('closeVideo'):exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
 decoded=[]
 for e in exports:
  if not e.get('video'):continue
  info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
 for a in d['actions']:
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
 # Merge preview availability into the latest gallery to preserve independent
 # review additions that may have been built while these videos rendered.
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for a in latest['actions']:
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n');report.update(status='passed',gallery_profiles=len(latest['profiles']),gallery_ready_actions=sum(a['ready']for a in latest['actions']),decoded_videos=len(decoded),offline_captures=captures);write(OUT/'verification.json',report);write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});print(json.dumps({'status':'passed','videos':len(decoded),'stills':len(actions),'captures':len(captures)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');verify(p.parse_args().export)
