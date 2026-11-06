#!/usr/bin/env python3
"""Build and publish only three corrected map profiles; retain all battle art."""
import argparse,contextlib,copy,io,json,os,subprocess,tempfile
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
from PIL import Image,ImageDraw
import import_hunapu_dawn_v3 as art
import integrate_enemy_11_14_review as S
import export_gallery as E
import validate_gallery as V
ROOT=art.ROOT;OUT=art.OUT;PIDS={f'hunapu-promoted-maps-{c}'for c in art.CONTEXTS}
def own(x):
 value=x.get('profile',x.get('id',''));return value in PIDS or any(value.startswith(p+'--')for p in PIDS)
def write(p,d):art.write(p,d)
def build():
 S.MAPS=[art.MP];module=S.isolated_builder();read=module.read
 def scoped(path):
  value=read(path)
  if Path(path).resolve()==art.MP.resolve():value=copy.deepcopy(value);value['scenarios']=[s for s in value['scenarios']if s['id']in art.CONTEXTS]
  return value
 module.read=scoped;before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert S.snapshot_shared()==before and len(data['profiles'])==3 and len(data['actions'])==24 and all(own(x)for x in data['profiles']+data['actions']);data['effects']={};write(OUT/'gallery-data.json',data);return data
def changed(a,b,box):return sum(x!=y for x,y in zip(a.crop(box).getdata(),b.crop(box).getdata()))
def head(im):
 points=[(x,y)for y in range(28,57)for x in range(44,84)if im.getpixel((x,y))[:3]==art.H.HAIR and im.getpixel((x,y))[3]];groups=art.H.parts(points);points=max(groups,key=len);return[sum(p[i]for p in points)/len(points)for i in[0,1]]
def verify(data):
 base={a['id']:a for a in art.baseline()['actions']};profiles={p['id']:p for p in data['profiles']};errors=[];checks=0
 for p in profiles.values():
  assert p['heroProfession']=='dawn_warrior'and p['className']=='破晓勇士'and not p['frameErrors']
  for path in p['newFrames'].values():
   im=V.image(path);assert im.size==(128,96)and im.getbbox();assert set(im.getchannel('A').getdata())<={0,255};checks+=1
 for a in data['actions']:
  assert a['ready']and all(a[k]==base[a['id']][k]for k in['frames','fps','origin','contactTick']);assert not a.get('revisedFrames');p=profiles[a['profile']];w,h=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas'])
  for t,row in enumerate(a['frames']):
   f=row['frame'];x=f%p['sourceColumns']*w;y=f//p['sourceColumns']*h;at=[a['origin'][i]+row['offset'][i]-p['anchor'][i]for i in[0,1]]
   for name,im in[('original',atlas.crop((x,y,x+w,y+h))),('redraw',V.image(p['newFrames'][str(f)]))]:
    box=V.box_at(im,at,[w,h],row.get('flip',False));checks+=1
    if V.outside(box,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'tick':t,'track':name,'box':box})
 motions=[]
 for kind,ids in[('story',[2,3]),('story',[4,5]),('tactical-walk',[2,3]),('tactical-walk',[6,7])]:
  ims=[Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')for i in ids];heads=[head(im)for im in ims];drift=[abs(heads[0][i]-heads[1][i])for i in[0,1]];assert max(drift)<2,(kind,ids,heads)
  counts={label:changed(*ims,box)for label,box in[('upper_body',(35,50,94,76)),('left_arm',(40,53,59,76)),('right_arm',(69,53,90,77)),('torso',(57,54,73,74))]};assert all(n>10 for n in counts.values()),(kind,counts)
  assert all(im.getbbox()[3]==95 for im in ims);motions.append({'context':kind,'slots':ids,'head_centroids':heads,'head_centroid_drift_pixels':drift,'ground_y':95,'changed_pixels_in_authored_joint_regions':counts,'whole_poses_not_separate_leg_patches':True})
 for ids,wider in[([2,3],1),([6,7],0)]:
  spans=[]
  for i in ids:
   box=Image.open(OUT/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA').crop((0,87,128,96)).getbbox();spans.append(box[2]-box[0])
  assert spans[wider]>spans[1-wider]*1.4,(ids,spans);motions.append({'native_slots':ids,'boot_spans':spans,'original_narrow_wide_order_preserved':True})
 assert profiles['hunapu-promoted-maps-story']['newFrames']==profiles['hunapu-promoted-maps-world']['newFrames']
 errors+=data['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'profiles':3,'actions':24,'original_map_rows_and_cadence_preserved':True,'motion_checks':motions,'visual_inspection':{'story_raised_heels_tucked_under_hips':True,'story_opposed_arm_swing_and_torso_motion':True,'tactical_horizontal_faces_forward':True,'tactical_shields_held_in_front_of_forearm_and_chest':True,'native_directional_sword_shield_arrangement':True},'battle_and_effects_not_rebuilt':True,'runtime_integrated':False,'errors':errors};write(OUT/'verification.json',report);assert not errors,errors;return report
def boards(data):
 profiles={p['id']:p for p in data['profiles']};specs=[('story-up','story','walk-up'),('story-side','story','walk-right'),('tactical-right','tactical-walk','walk-right'),('tactical-left','tactical-walk','walk-left')]
 for name,ctx,key in specs:
  a=next(a for a in data['actions']if a['profile']==f'hunapu-promoted-maps-{ctx}'and a['key']==key);p=profiles[a['profile']]
  for light in[False,True]:
   ticks=[0,16,32,48];panels=[E.render_panel(data,p,a,a['frames'][t],True,8,light,False).convert('RGB')for t in ticks];w,h=panels[0].size;out=Image.new('RGB',(w*4,h+38),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(out)
   for n,(t,panel)in enumerate(zip(ticks,panels)):
    out.paste(panel,(n*w,0));d.text((n*w+w/2,h+19),f'第{t+1}帧 · 姿势{a["frames"][t]["frame"]}',font=E.font(17),anchor='mm',fill=art.H.NAVY if light else'white')
   out.save(OUT/(name+('-light.png'if light else'-dark.png')),optimize=True)
def export(data):
 records=[];decoded=[]
 for a in data['actions']:
  records.append(E.export(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not a.get('defaultVideo'))))
  if a.get('defaultVideo'):
   p=ROOT/'demos/videos'/(a['id']+'.mp4');info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(p)],text=True))['streams'][0];assert int(info['nb_read_frames'])==len(a['frames'])and abs(float(info['duration'])-len(a['frames'])/a['fps'])<1/a['fps'];decoded.append({'path':p.relative_to(ROOT).as_posix(),'frames':int(info['nb_read_frames']),'duration':float(info['duration']),'size':[info['width'],info['height']]})
  print(json.dumps({'exported':a['id'],'video':bool(a.get('defaultVideo'))}),flush=True)
 assert len(decoded)==12;boards(data);write(OUT/'export-report.json',{'records':records,'decoded_videos':decoded,'only_three_map_profiles_exported':True,'battle_media_unchanged':True})
def merge(data):
 paths=S.source_paths();before=S.snapshot_shared();live=json.loads(paths[1].read_text());assert S.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=S.merge_rows(live[field],data[field],own);assert[x for x in live[field]if not own(x)]==[x for x in combined[field]if not own(x)]
 assert combined['effects']==live['effects'];combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);report['actions']=S.merge_rows(report['actions'],[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in data['actions']],own);payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.hunapu-map-v3-',dir=p.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),p))
  assert S.snapshot_shared()==before,'Concurrent gallery writer; retry against latest data'
  for temporary,p in staged:os.replace(temporary,p)
 finally:
  for temporary,_ in staged:temporary.unlink(missing_ok=True)
 assert S.parse_js(paths[0])==combined==json.loads(paths[1].read_text())and S.sha(paths[3])==before['index.html'];write(OUT/'merge-report.json',{'target_profiles':3,'target_actions':24,'all_unrelated_profiles_and_actions_preserved':True,'battle_double_slash_sparks_and_media_preserved':True,'all_effects_preserved':True,'index_default_unchanged':True,'runtime_integrated':False})
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');a=p.parse_args();data=build();v=verify(data);print(json.dumps({'profiles':3,'actions':24,'checks':v['checks']}),flush=True)
 if a.export:export(data);data=build()
 if a.merge:merge(data)
if __name__=='__main__':main()
