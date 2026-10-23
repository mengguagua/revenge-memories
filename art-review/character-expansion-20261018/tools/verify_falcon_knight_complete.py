#!/usr/bin/env python3
"""Targeted native class5 motion, map registration, weapon and export checks."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,relative,pack_frame,matched_export
from export_gallery import render_frame
from export_knight_complete import export_one
from import_falcon_knight_complete import C,helmet_anchor
from prepare_falcon_knight_complete import OUT,REV,write

def verify(export=False):
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());now={a['id']:a for a in d['actions']};before={a['id']:a for a in b['gallery']['actions']};pp={p['id']:p for p in d['profiles']};actions=[a for a in now.values()if a['profile'].startswith('professions-class-5-ally-')]
 assert len(actions)==20 and all(a['ready']for a in actions)and len(d['profiles'])==97 and len(now)==775 and not d['validation']['structuralIssues']
 changed={k for k,a in now.items()if a['contentDigest']!=before[k]['contentDigest']};assert changed=={a['id']for a in actions}
 for k,a in now.items():
  for field in['frames','fps','origin','contactTick','duration']:assert a.get(field)==before[k].get(field),(k,field)
 audit=json.loads((OUT/'native-reference-audit.json').read_text())
 for row in audit['assets']:assert file_hash(ROOT/row['path'])==row['sha256']
 images={};assets=[]
 for kind,count,size in[('tactical-walk',8,(128,96)),('tactical-idle',6,(96,96)),('battle',12,(384,544))]:
  files=sorted((OUT/f'ally/{kind}').glob('frame-*.png'));assert len(files)==count
  for path in files:
   im=Image.open(path).convert('RGBA');i=int(path.stem.split('-')[1]);assert im.size==size and {p[:3]for p in im.getdata()if p[3]}<=set(C)and set(im.getchannel('A').getdata())=={0,255}
   images[kind,i]=im;assets.append({'path':relative(path),'size':list(size),'bytes':path.stat().st_size,'palette_colors':len({p[:3]for p in im.getdata()if p[3]}),'binary_alpha':True})
 for i,j in[(6,2),(7,3)]:assert images['tactical-walk',i].tobytes()==images['tactical-walk',j].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
 for i,j in enumerate([0,1,2,1,0,1]):assert images['tactical-idle',i].tobytes()==images['tactical-idle',j].tobytes()
 for i in[25,48]:assert images['battle',i].tobytes()==images['battle',0].tobytes()
 reg=json.loads((OUT/'registration.json').read_text())
 for row in reg['fixed_map_centers']:
  kind='tactical-idle'if row['group']=='idle'else'tactical-walk';assert helmet_anchor(images[kind,row['slot']],row['registered_helmet_region'])==row['fixed_helmet_anchor']and row['clipped_opaque_pixels']==0
 for i in range(8):
  native=Image.open(OUT/f'source/native-walk-{i:03}.png').convert('RGBA').crop((0,21,32,24)).resize((128,12),Image.Resampling.NEAREST);assert native.getchannel('A').tobytes()==images['tactical-walk',i].crop((0,84,128,96)).getchannel('A').tobytes()
 # Existing class5 feathers, limbs and body positions are retained; only the
 # explicit old/new weapon rectangles may change alpha in normal attack art.
 for row in reg['weapon_registrations']:
  if row['kind']!='battle':continue
  i=row['slot'];im=images['battle',i];old=Image.open((ROOT/'professions/class-5-ally/battle'/b['battle']['frame_mapping'][str(i)]).resolve()).convert('RGBA');boxes=[row['old_weapon_removal'],row['new_weapon_bounds']];gx,gy=row['grip'];boxes.append([gx-4,gy-5,gx+7,gy+6])
  for y in range(544):
   for x in range(384):
    if any(z[0]<=x<z[2]and z[1]<=y<z[3]for z in boxes):continue
    assert im.getpixel((x,y))[3]==(255 if old.getpixel((x,y))[3]>=128 else 0),(i,x,y,'nonweapon silhouette changed')
 old=Image.open((ROOT/'professions/class-5-ally/battle'/b['battle']['frame_mapping']['50']).resolve()).convert('RGBA');assert old.getchannel('A').point(lambda a:255 if a>=128 else 0).tobytes()==images['battle',50].getchannel('A').tobytes()
 ef=pp['professions-class-5-ally-battle']['revisedEffects']['1ecba259419456'];native=d['effects']['1ecba259419456']
 for k,v in native.items():
  if k!='path':assert ef[k]==v
 schedules=[]
 for a in actions:
  if a['kind']=='attack':
   v=b['variants'][a['key']];assert a['frames']==[pack_frame(f)for f in v['frames']]and v['contact_count']==1
   schedules.append({'actor_id':'class-5-ally','class_name':'隼骑士','source_action':a['key'],'hero_card_binding':None,'class_sample_card':'枪系普通攻击／投枪','program':v['source_program_address'],'release_tick':next((i for i,f in enumerate(a['frames'])if f['effects']),None),'contact_tick':a['contactTick'],'contact_count':1,'note':'职业动画样板，不新增卡牌、额外命中或对魔物特效；不接入业务结算。'})
 write(OUT/'action-effect-mapping.json',{'scope':'ally Falcon Knight only','setting':'docs2/完整游戏设定.md:94,271','class_id':5,'actions':schedules})
 manifest=json.loads((OUT/'asset-manifest.json').read_text())
 for a in manifest['assets']:assert file_hash(ROOT/a['path'])==a['sha256']and(ROOT/a['path']).stat().st_size==a['bytes']
 for n in['prepare_falcon_knight_complete.py','import_falcon_knight_complete.py','verify_falcon_knight_complete.py']:ast.parse((ROOT/'tools'/n).read_text())
 captures=[]
 for a in actions:
  p=pp[a['profile']];ticks=[0,14,22]if a['key']=='idle-cycle'else[0,16]if a['kind']=='map_walk'else[]
  if a['key']=='original_class_5_normal':ticks=[next(n for n,f in enumerate(a['frames'])if f['frame']==i)for i in range(8)]+[a['contactTick']]
  if a['key']=='class_5_ally_javelin':ticks=[0,18,21,51,54]
  for tick in ticks:
   for light in[False,True]:
    path=OUT/f'{a["key"]}-{tick:03}-{"light"if light else"dark"}.png';render_frame(d,p,a,tick,6,light,a['context']=='battle').save(path,optimize=True);captures.append(relative(path))
 report={'status':'assets_passed','revision':REV,'changed_actions':sorted(changed),'unrelated_actions_unchanged':755,'native_frames_fps_origins_contacts_unchanged':True,'map_helmet_centers':reg['fixed_map_centers'],'native_projection_rows_21_24_unchanged':True,'normal_battle_body_alpha_outside_weapon_unchanged':True,'six_matte_colors':True,'empty_hand_release_pose_preserved':True,'effect_metadata_unchanged':True,'asset_checks':assets,'offline_captures':captures,'browser_ui_checked':False,'runtime_integrated':False,'user_visual_acceptance':'pending'};write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','actions':20,'unchanged':755}),flush=True)
 if not export:return
 exports=[];decoded=[]
 for a in actions:
  exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
  if a['key']in['original_class_5_normal','class_5_ally_javelin']:exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  print('Exported '+a['key'],flush=True)
 for e in exports:
  info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
  assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
 for a in actions:
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
  assert a['video']and a['still']
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n');report.update(status='passed',decoded_videos=len(decoded));write(OUT/'verification.json',report);write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});print(json.dumps({'status':'passed','actions':20,'videos':len(decoded)}),flush=True)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');a=p.parse_args();verify(a.export)
