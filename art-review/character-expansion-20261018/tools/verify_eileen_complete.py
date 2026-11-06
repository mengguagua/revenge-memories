#!/usr/bin/env python3
"""Targeted source, identity, anchor and offline playback QA for Eileen's two forms."""
import argparse,ast,json,subprocess
from types import SimpleNamespace
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame,playback_count,font
from export_knight_complete import export_one
from prepare_eileen_complete import REV,OUT,SRC,write
from import_eileen_complete import C,HAIR

def verify(export=False):
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());byid={a['id']:a for a in d['actions']};profiles={p['id']:p for p in d['profiles']};old={a['key']:a for a in b['actions']};selected=[a for a in d['actions']if profiles[a['profile']]['actor']=='eileen'];assert len(selected)==144,len(selected)
 assert not d['validation']['structuralIssues']and all(a['ready']for a in selected)
 unchanged=0;concurrent=[]
 for aid,digest in b['digests'].items():
  assert aid in byid
  if byid[aid]['contentDigest']==digest:unchanged+=1
  else:concurrent.append(aid)
 assert all(not x.startswith('professions-class-11-ally-')for x in concurrent)
 assert d['effects']==b['effects'],'Shared effects changed'
 art=json.loads((OUT/'asset-manifest.json').read_text());assets=[]
 for record in art['assets']:
  p=ROOT/record['path'];assert file_hash(p)==record['sha256']
  with Image.open(p)as im:
   assert list(im.size)==record['size']
   if im.mode in['RGBA','P']:
    q=im.convert('RGBA');assert{v[:3]for v in q.getdata()if v[3]}<=set(C);assert set(q.getchannel('A').getdata())<={0,255}
  assets.append(record)
 def load(form,kind,i):return Image.open(OUT/f'{form}/{kind}/frame-{i:03}.png').convert('RGBA')
 for form,folder,job in [('base','eileen','女魔剑士'),('promoted','eileen-promoted','引光剑使')]:
  pp=[p for p in d['profiles']if p['id'].startswith(folder+'-')and p['actor']=='eileen'and p['className']==job];assert len(pp)==5,(folder,len(pp))
  story=profiles[folder+'-maps-story'];world=profiles[folder+'-maps-world'];assert story['newFrames']==world['newFrames']and story['mapShadow']==world['mapShadow']
  for p in pp:
   assert p['revision']==REV
   if p['context']!='battle':assert p['mapShadow']and p['mapShadow']['alpha']>0
   if form=='promoted':assert p['heroProfession']=='light_guide'
   for i,path in p['newFrames'].items():
    q=Image.open(ROOT/path).convert('RGBA');assert any(v[:3]==HAIR and v[3]for v in q.getdata()),(p['id'],i,'red hair missing')
  for kind,ids,seam in [('story',[0,1],77),('story',[2,3],77),('story',[4,5],76),('tactical-walk',[0,1],74),('tactical-walk',[4,5],74),('tactical-walk',[2,3],70)]:
   a,z=[load(form,kind,i)for i in ids];assert a.crop((0,0,a.width,seam)).tobytes()==z.crop((0,0,z.width,seam)).tobytes(),(form,kind,ids,'upper body moved');assert a.tobytes()!=z.tobytes(),(form,kind,ids,'leg phases identical')
   if ids in[[0,1],[2,3]]and kind=='story'or kind=='tactical-walk'and ids in[[0,1],[4,5]]:
    assert a.crop((0,seam,a.width,a.height)).getbbox()==z.crop((0,seam,z.width,z.height)).getbbox(),(form,kind,'lower body shifts laterally')
  for i in[1,2]:
   for region in[(37,27,96,96),(0,60,96,96)]:assert load(form,'tactical-idle',0).crop(region).tobytes()==load(form,'tactical-idle',i).crop(region).tobytes()
  assert load(form,'tactical-idle',0).crop((0,0,37,55)).tobytes()!=load(form,'tactical-idle',2).crop((0,0,37,55)).tobytes(),'Arm/sword must change together'
  for ids,seam in [([2,3,4,5,6,7],112),([8,9],112),([25,26],184),([27,28],184)]:
   master=load(form,'battle',ids[0]).crop((0,seam,320,288)).tobytes()
   for i in ids[1:]:assert load(form,'battle',i).crop((0,seam,320,288)).tobytes()==master,(form,ids,'jump legs')
  battle=[a for a in selected if a['profile']==folder+'-battle'];assert len(battle)==47
  for a in battle:
   ref=old[a['key']]
   for field in['frames','fps','origin','contactTick','revisedFrames','reviewTailFrames']:
    assert a.get(field)==ref.get(field),(a['id'],field)
   if '_item_'in a['key']:assert int(a['key'].split('_item_')[1].split('_')[0])in[23,24,25,26,27,40]
 assert file_hash(OUT/'base/battle/frame-000.png')!=file_hash(OUT/'promoted/battle/frame-000.png')
 assert all(r['clipped_pixels']==0 for r in art['registrations'])
 for name in['prepare_eileen_complete.py','import_eileen_complete.py','verify_eileen_complete.py']:ast.parse((ROOT/'tools'/name).read_text())
 report={'status':'assets_passed','revision':REV,'profiles':10,'actions':144,'battle_programs_per_form':43,'reaction_previews_per_form':4,'all_prior_actions_unchanged':unchanged,'concurrent_external_changes_preserved':concurrent,'source_actor_schedules_fps_origins_and_contacts_exact':True,'all_shared_effects_unchanged':True,'world_reuses_story_exactly':True,'fixed_map_upper_bodies_and_alternating_legs':True,'stable_airborne_leg_regions':True,'hair_present_in_every_frame':True,'single_matte_hair_material':'9e4247','promoted_design_independent':True,'new_effect_assets':0,'runtime_integrated':False,'browser_ui_checked':False,'user_visual_acceptance':'pending'};write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','actions':144,'prior_unchanged':unchanged}),flush=True)
 if not export:return
 exports=[]
 for a in selected:exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=True)))
 print('Saved 144 action stills',flush=True)
 movies=[]
 for folder in['eileen','eileen-promoted']:
  for context in['story','tactical-walk']:
   for direction in['up','right','down','left']:movies.append(byid[f'{folder}-maps-{context}--walk-{direction}'])
  for suffix in['maps-tactical-idle--idle-cycle','battle--original_class_11_normal','battle--class_11_ally_item_23','battle--class_11_ally_item_40']:movies.append(byid[folder+'-'+suffix])
 for key in['class_11_ally_levin_far_ally','class_11_ally_item_26']:movies.append(byid['eileen-promoted-battle--'+key])
 for a in movies:
  exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)));print('Exported '+a['id'],flush=True)
 for folder in['eileen','eileen-promoted']:
  a=byid[folder+'-battle--original_class_11_normal'];exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)));print('Exported '+folder+' close combat',flush=True)
 captures=[]
 for folder in['eileen','eileen-promoted']:
  a=byid[folder+'-battle--original_class_11_normal'];p=profiles[a['profile']]
  for tick in[64,94,128,194]:
   for light in[False,True]:
    path=OUT/(f'{folder}-attack-{tick:03}-'+('light.png'if light else'dark.png'))
    render_frame(d,p,a,tick,4,light,True).save(path,optimize=True);captures.append(relative(path))
 decoded=[]
 for e in exports:
  if not e.get('video'):continue
  a=byid[e['action']];s=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
  assert int(s['nb_read_frames'])==playback_count(a)and abs(float(s['duration'])-playback_count(a)/a['fps'])<1/a['fps'];decoded.append({'path':e['video'],**s})
 # Build one compact portrait / three-context identity inspection board.
 q=Image.new('RGB',(1440,750),(32,45,53));dr=ImageDraw.Draw(q)
 for row,(form,job)in enumerate([('base','女魔剑士'),('promoted','引光剑使')]):
  dr.text((720,28+row*360),'艾琳 · '+job+' · 画像与三个场景一致性',anchor='mm',font=font(22),fill=(235,243,242))
  ims=[Image.open(SRC/'eileen_departure.png').convert('RGBA').resize((192,192),Image.Resampling.NEAREST),load(form,'story',0).resize((256,192),Image.Resampling.NEAREST),load(form,'tactical-idle',0).resize((192,192),Image.Resampling.NEAREST),load(form,'battle',0)]
  for col,(im,label)in enumerate(zip(ims,['现行画像','剧情 / 大地图复用','战斗地图','战斗场景'])):
   x=col*360+(360-im.width)//2;y=row*360+55+(288-im.height)//2;q.paste(im,(x,y),im);dr.text((col*360+180,row*360+336),label,anchor='mm',font=font(18),fill=(235,243,242))
 q.save(OUT/'identity-comparison.png',optimize=True)
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for a in latest['actions']:
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});report.update(status='passed',decoded_videos=len(decoded),stills=144,offline_captures=captures,offline_visual_scope='Both forms, all map and combat pose boards; portrait-context comparison; light/dark jump/landing captures.');write(OUT/'verification.json',report);print(json.dumps({'status':'passed','videos':len(decoded),'stills':144}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');verify(p.parse_args().export)
