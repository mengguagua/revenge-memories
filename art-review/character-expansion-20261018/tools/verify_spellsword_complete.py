#!/usr/bin/env python3
"""Targeted native schedule, art integrity and offline playback checks for ally class11."""
from baseline_json import read_baseline
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,pack_frame,relative,matched_export,SPELL_NAMES
from export_gallery import render_frame
from export_knight_complete import export_one
from prepare_spellsword_complete import REV,OUT,write
from import_spellsword_complete import C,helper,box

def verify(export=False):
 b=read_baseline(OUT/'baseline.json');d=json.loads((ROOT/'demos/gallery-data.json').read_text());pp={p['id']:p for p in d['profiles']};now={a['id']:a for a in d['actions']};before={a['id']:a for a in b['gallery']['actions']};actions=[a for a in d['actions']if a['profile'].startswith('professions-class-11-ally-')];contracts=json.loads((OUT/'spell-sharing-contracts.json').read_text())['contracts']
 assert len(actions)==80 and len(now)==1098 and len(pp)==109 and len(contracts)==54 and all(a['ready']for a in actions),(len(actions),len(now),len(pp))
 assert not d['validation']['structuralIssues'] and set(now)-set(before)=={a['id']for a in actions}
 assert not any(p['id'].startswith('professions-class-11-enemy-')for p in d['profiles'])
 for k,a in before.items():assert a['contentDigest']==now[k]['contentDigest'],('unrelated action',k)
 assert d['effects']==b['gallery']['effects']
 schedules=[]
 for a in actions:
  p=pp[a['profile']];assert p['revision']==REV and not a.get('reviewTailFrames')
  if a['kind']=='attack':
   v=b['variants'][a['key']];assert a['frames']==[pack_frame(f)for f in v['frames']] and a['fps']==v['native_fps'] and a['origin']==v['actor_origin'] and a['contactTick']==v['contact_tick']
   if a.get('revisedFrames'):
    assert len(a['revisedFrames'])==len(a['frames'])
    for row,old in zip(a['revisedFrames'],a['frames']):assert {k:v for k,v in row.items()if k!='effects'}=={k:v for k,v in old.items()if k!='effects'}
   item=v.get('source_item_id');schedules.append({'actor_id':'class-11-ally','source_action':a['key'],'source_item_id':item,'spell_or_weapon':SPELL_NAMES.get(item,'普通剑击／雷剑'),'native_program':v['source_program_address'],'total_ticks':len(a['frames']),'effect_contact_tick':a['contactTick'],'contact_count':v['contact_count'],'native_actor_rows_exact':True,'campaign_hero_id':'eileen','note':'职业美术参考库，不改变个人法术、装备、解锁与主角专属职业规则；冰晶剑外观不增加冰冻或额外命中。'})
  elif a['key']=='idle-cycle':assert [f['frame']for f in a['frames']]==[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
  elif a['kind']=='map_walk':
   start={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']];assert [f['frame']for f in a['frames']]==[i for _ in range(3)for i in [start,start+1]for _ in range(16)]
   assert all(f['offset']==[0,0]and not f['flip']for f in a['frames'])
 assert len(schedules)==67
 for row in json.loads((OUT/'source-audit.json').read_text())['sources']:assert file_hash(ROOT/row['path'])==row['sha256']
 for row in json.loads((OUT/'shared-spell-assets.json').read_text())['effects']:assert file_hash(ROOT/row['metadata']['path'])==row['sha256']
 images={};checks=[]
 for kind,count,size in [('tactical-idle',6,(96,96)),('tactical-walk',8,(128,96)),('battle',44,(320,288))]:
  paths=sorted((OUT/'ally'/kind).glob('frame-*.png'));assert len(paths)==count
  for path in paths:
   i=int(path.stem.split('-')[-1]);im=Image.open(path).convert('RGBA');images[kind,i]=im
   assert im.size==size and set(im.getchannel('A').getdata())=={0,255}and{p[:3]for p in im.getdata()if p[3]}<=set(C)
   cs=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cs)==(2 if kind=='battle'and i==19 else 1),(kind,i,'detached',[(len(c),box(c))for c in cs])
   checks.append({'path':relative(path),'size':list(size),'bytes':path.stat().st_size,'sha256':file_hash(path),'connected_components':len(cs)})
 for i,j in enumerate([0,1,2,1,0,1]):assert images['tactical-idle',i].tobytes()==images['tactical-idle',j].tobytes()
 for i in [1,2]:
  for region in [[37,34,49,46],[25,70,67,81]]:assert images['tactical-idle',i].crop(region).tobytes()==images['tactical-idle',0].crop(region).tobytes(),('idle anchor',i,region)
 for ids,region in [([0,1],[53,45,65,64]),([2,3],[63,47,77,62]),([4,5],[56,46,70,65])]:
  assert images['tactical-walk',ids[0]].crop(region).tobytes()==images['tactical-walk',ids[1]].crop(region).tobytes(),('torso',ids)
  assert images['tactical-walk',ids[0]].crop((0,72,128,96)).tobytes()!=images['tactical-walk',ids[1]].crop((0,72,128,96)).tobytes()
 for i,j in [(6,2),(7,3)]:assert images['tactical-walk',i].tobytes()==images['tactical-walk',j].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
 for i in [50,97]:assert images['battle',i].tobytes()==images['battle',0].tobytes()
 manifest=json.loads((OUT/'asset-manifest.json').read_text());assert all(x['clipped_pixels']==0 for x in manifest['registrations'])
 for row in manifest['assets']:assert file_hash(ROOT/row['path'])==row['sha256']
 for name in ['prepare_spellsword_complete.py','import_spellsword_complete.py','share_spellsword_mage_spells.py','verify_spellsword_complete.py']:ast.parse((ROOT/'tools'/name).read_text())
 write(OUT/'action-effect-mapping.json',{'source_rules':['docs2/职业命名提案-0.9.0.md:18','docs2/完整游戏设定.md:104','docs2/完整游戏设定.md:431','actual/data/campaign.json:670'],'runtime_rules_changed':False,'enemy_excluded_by_user':True,'actions':schedules})
 report={'status':'assets_passed','revision':REV,'new_profiles':3,'new_actions':80,'native_attack_variants':67,'existing_actions_unchanged':1018,'native_actor_frames_fps_origins_contacts_and_lengths_exact':True,'shared_confirmed_spell_variants':54,'new_effect_images':0,'all_prior_effect_metadata_unchanged':True,'map_head_neck_torso_fixed':True,'map_idle_feet_fixed':True,'left_walk_exact_mirror_of_right':True,'body_sprite_files':58,'original_slash_arc_preserved':True,'source_assets_unchanged':True,'registrations_clipped_pixels':0,'assets':checks,'browser_ui_checked':False,'runtime_integrated':False,'enemy_excluded_by_user':True,'user_visual_acceptance':'pending'}
 write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','new_actions':80,'unchanged':1018}),flush=True)
 if not export:return
 exports=[];captures=[]
 for a in actions:
  p=pp[a['profile']];canonical=a['kind']=='attack'and not any(w in a['key']for w in ['far_','vs_heavy']);selected=canonical or a['kind']=='map_walk'or a['key']in['idle-cycle','idle']
  if not selected:continue
  exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
  if canonical and a['key'].endswith(('_normal','_levin','_item_23','_item_28')):exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  if a['kind']=='map_walk':ticks=[0,16]
  elif a['key']=='idle-cycle':ticks=[0,14,22]
  elif canonical and a['key'].endswith('_normal'):ticks=[0,56,64,110,116,123,128,145,183,232,266,310]
  elif canonical and a['key'].endswith(('_levin','_item_23','_item_28')):ticks=[0,36,71,a['contactTick']]
  else:ticks=[]
  for tick in sorted(set(ticks)):
   for light in[False,True]:
    close=a['kind']=='attack';path=OUT/f'ally-{a["key"]}-{tick:03}-{"light"if light else"dark"}.png';render_frame(d,p,a,tick,5 if close else 7,light,close).save(path,optimize=True);captures.append(relative(path))
  print('Exported '+a['key'],flush=True)
 decoded=[]
 for e in exports:
  info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
 for a in actions:
  for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   p=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
 report.update(status='passed',decoded_videos=len(decoded),offline_captures=captures);write(OUT/'verification.json',report);write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});print(json.dumps({'status':'passed','videos':len(decoded)}),flush=True)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');verify(p.parse_args().export)
