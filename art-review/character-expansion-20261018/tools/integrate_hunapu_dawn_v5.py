#!/usr/bin/env python3
"""Scoped synchronization of tactical walk/idle; keep the confirmed v4 side art."""
import argparse,contextlib,copy,io,json,re,subprocess
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit
from PIL import Image,ImageDraw
import import_hunapu_dawn_v5 as A
import integrate_hunapu_dawn_v4 as I
import integrate_enemy_11_14_review as S
import export_gallery as E
import validate_gallery as V
ROOT=A.ROOT;OUT=A.OUT;REV=A.REV
def own(x):return x.get('profile',x.get('id'))in A.PIDS or any(str(x.get('id','')).startswith(p+'--')for p in A.PIDS)
I.A=A;I.OUT=OUT;I.REV=REV;I.own=own
def write(p,d):A.write(p,d)
def build():
 S.MAPS=[A.MP];m=S.isolated_builder();read=m.read
 def scoped(path):
  v=read(path)
  if Path(path).resolve()==A.MP.resolve():v=copy.deepcopy(v);v['scenarios']=[s for s in v['scenarios']if s['id']in A.CONTEXTS]
  return v
 m.read=scoped;before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):d=m.build()
 assert S.snapshot_shared()==before and len(d['profiles'])==2 and len(d['actions'])==9 and all(own(x)for x in d['profiles']+d['actions'])
 d['effects']={};write(OUT/'gallery-data.json',d);return d
def hair_center(im,idle):
 pts=[(x,y)for y in range(8 if idle else 23,47 if idle else 62)for x in range(24 if idle else 40,72 if idle else 88)if im.getpixel((x,y))==(*A.H.HAIR,255)]
 g=max(A.H.parts(pts),key=len);return[sum(p[i]for p in g)/len(g)for i in[0,1]]
def verify(d):
 old=A.baseline();op={p['id']:p for p in old['profiles']};oa={a['id']:a for a in old['actions']};ps={p['id']:p for p in d['profiles']};errors=[];checks=0;root=[]
 for p in d['profiles']:
  assert p['heroProfession']=='dawn_warrior'and p['className']=='破晓勇士'and not p['frameErrors'];assert p['mapShadow']==op[p['id']]['mapShadow'];idle=p['context']=='tactical-idle';ims={int(i):V.image(f)for i,f in p['newFrames'].items()};sz=(96,96)if idle else(128,96)
  for i,im in ims.items():
   assert im.size==sz and im.getbbox()and set(im.getchannel('A').getdata())<={0,255};checks+=1
   if not idle and i in[2,3,6,7]:assert p['newFrames'][str(i)]==op[p['id']]['newFrames'][str(i)]and im.tobytes()==V.image(op[p['id']]['newFrames'][str(i)]).tobytes()
  groups=[[0,1,2]]if idle else[[0,1],[4,5]]
  for ids in groups:
   centers=[hair_center(ims[i],idle)for i in ids];drift=[max(c[j]for c in centers)-min(c[j]for c in centers)for j in[0,1]]
   assert max(drift)<2,(p['id'],ids,centers);ground=80 if idle else 95
   assert all(ims[i].getbbox()[3]==ground for i in ids)
   root.append({'context':p['context'],'slots':ids,'head_centroids':centers,'head_centroid_drift_output_pixels':drift,'ground_y':ground})
  if idle:
   assert all(ims[i].tobytes()==ims[j].tobytes()for i,j in[(3,1),(4,0),(5,1)])
 for a in d['actions']:
  p=ps[a['profile']];assert a['ready']and not a.get('revisedFrames');assert all(a[k]==oa[a['id']][k]for k in['frames','fps','origin','contactTick','duration']);w,h=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas'])
  for t,row in enumerate(a['frames']):
   f=row['frame'];x=f%p['sourceColumns']*w;y=f//p['sourceColumns']*h;at=[a['origin'][i]+row['offset'][i]-p['anchor'][i]for i in[0,1]]
   for kind,im in[('original',atlas.crop((x,y,x+w,y+h))),('redraw',V.image(p['newFrames'][str(f)]))]:
    checks+=1;box=V.box_at(im,at,[w,h],row.get('flip',False))
    if V.outside(box,a.get('viewport',d['viewport'])):errors.append({'action':a['id'],'tick':t,'track':kind,'bounds':box})
 errors+=d['validation']['structuralIssues'];v={'revision':REV,'passed':not errors,'checks':checks,'profiles':2,'actions':9,'new_complete_poses':7,'new_walk_slots':[0,1,4,5],'idle_slots':[0,1,2,3,4,5],'confirmed_horizontal_v4_pixels_and_paths_preserved':True,'native_frames_offsets_fps_and_cadence_preserved':True,'root_checks':root,'compact_shadow_preserved':True,'runtime_integrated':False,'visual_acceptance':'pending offline inspection and user acceptance','errors':errors};write(OUT/'verification.json',v);assert not errors,errors;return v
def boards(d):
 ps={p['id']:p for p in d['profiles']}
 for name,ctx,key,ticks in[('up','tactical-walk','walk-up',[0,16,32,48]),('down','tactical-walk','walk-down',[0,16,32,48]),('idle','tactical-idle','idle-cycle',[0,14,22,36])]:
  a=next(a for a in d['actions']if a['profile'].endswith(ctx)and a['key']==key);p=ps[a['profile']]
  for light in[False,True]:
   panels=[E.render_panel(d,p,a,a['frames'][t],True,8,light,False).convert('RGB')for t in ticks];w,h=panels[0].size;q=Image.new('RGB',(w*4,h+38),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(q)
   for n,(t,im)in enumerate(zip(ticks,panels)):q.paste(im,(n*w,0));dr.text((n*w+w/2,h+19),f'第{t+1}帧 · 姿势{a["frames"][t]["frame"]}',font=E.font(17),anchor='mm',fill=A.H.NAVY if light else'white')
   q.save(OUT/(name+('-light.png'if light else'-dark.png')),optimize=True)
def export(d):
 records=[];videos=[]
 for a in d['actions']:
  records.append(E.export(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not a.get('defaultVideo'))))
  if a.get('defaultVideo'):
   path=ROOT/'demos/videos'/(a['id']+'.mp4');info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(path)],text=True))['streams'][0]
   assert int(info['nb_read_frames'])==len(a['frames'])and abs(float(info['duration'])-len(a['frames'])/a['fps'])<1/a['fps'];videos.append({'path':path.relative_to(ROOT).as_posix(),'frames':int(info['nb_read_frames']),'duration':float(info['duration']),'size':[info['width'],info['height']]})
  print(json.dumps({'exported':a['id']}),flush=True)
 assert len(videos)==5;write(OUT/'export-report.json',{'records':records,'decoded_videos':videos,'scope':'two tactical map profiles only'});boards(d)
def finish(d):
 for a in d['actions']:assert a.get('still')and(a.get('video')if a.get('defaultVideo')else True)
 I.merge(d);write(OUT/'merge-report.json',{'target_profiles':2,'target_actions':9,'latest_live_unrelated_rows_and_effects_preserved':True,'index_default_preserved':True})
 page=ROOT/'index.html';old=page.read_text();default=re.search(r'data-default-action="([^"]+)"',old).group(1);m=re.search(r'<section\b[^>]*id="hunapu-dawn-progress".*?</section>',old,re.S);assert m;section=m.group()
 section=section.replace('斜跨持剑、低位持盾横移 · 待验收','战斗地图形象统一 · 待验收')
 note='<p class="action-note" style="margin:0 0 16px">战斗地图向上、向下行走与待机已同步到已确认的左右横移形象：统一发型、脸型、头身比例、浅蓝护甲厚度、深蓝衣靴及剑盾。上下交替换腿、待机举剑循环沿用原作；完整发型与脚底基准定位，保持人物中心和大小稳定。</p>'
 section=re.sub(r'<p class="action-note" style="margin:0 0 16px">.*?</p>',note,section,count=1,flags=re.S)
 section=section.replace('hunapu-dawn-strafe-v4-20261024/poses-light.png',REV+'/model-comparison-light.png').replace('斜跨持剑与低位持盾姿势','统一形象 · 上下、待机与横移对照').replace('hunapu-dawn-strafe-v4-20261024/README.md',REV+'/README.md')
 nav='<nav class="links" aria-label="统一战斗地图形象" style="margin-top:14px">'+''.join(f'<a href="{REV}/{file}">{label}</a>'for label,file in[('向上 · 连续帧','up-dark.png'),('向下 · 连续帧','down-dark.png'),('待机 · 连续帧','idle-dark.png')])+'</nav>'
 if 'aria-label="统一战斗地图形象"'not in section:section=section.replace('</section>',nav+'\n</section>')
 new=old[:m.start()]+section+old[m.end():];new=re.sub(r'&hunapu_dawn=[^"&]+','',new);new=re.sub(r'(src="gallery-data\.js\?[^"]*)"',lambda m:m.group(1)+'&hunapu_dawn=map-unify-v5-20261024"',new,count=1);assert re.search(r'data-default-action="([^"]+)"',new).group(1)==default
 for href in re.findall(r'href="([^"]+)"',section):
  u=urlsplit(href)
  if not u.query and not u.scheme:assert(ROOT/u.path).is_file(),href
 assert page.read_text()==old,'Concurrent page writer; retry latest';page.write_text(new)
 mp=ROOT/'hunapu-promoted/manifest.json';manifest=json.loads(mp.read_text());manifest.update(revision=REV,tactical_walk_revision=REV,tactical_idle_revision=REV,review_record='../'+REV+'/README.md');write(mp,manifest)
 cp=ROOT/'healer-saint-complete-v1-20261023/profession-catalog-sync.json';catalog=json.loads(cp.read_text());h=next(h for h in catalog['exclusive_heroes']if h['actor']=='胡纳普');h.update(art_status='专属进阶43项齐备；战斗地图上下、待机与已确认横移统一形象，待验收',review_revision=REV,runtime_integrated=False);write(cp,catalog)
 live=json.loads((ROOT/'demos/gallery-data.json').read_text());dawn=[a for a in live['actions']if a['profile'].startswith('hunapu-promoted-')];assert len(dawn)==43 and all(a['ready']for a in dawn)
 for field in['profiles','actions']:
  for row in live[field]:
   if str(row.get('profile',row['id'])).startswith('hunapu-promoted-')and not own(row):assert I.digest(row)==A.baseline()['unrelated_row_hashes'][field][row['id']],row['id']
 files=[p for p in OUT.rglob('*.png')if 'source'not in p.relative_to(OUT).parts]+[ROOT/'demos/stills'/(a['id']+'.png')for a in d['actions']]
 inventory=[{'path':p.relative_to(ROOT).as_posix(),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':S.sha(p),'purpose':'character pose'if p.parent.name in A.CONTEXTS else'lossless review or export'}for p in sorted(set(files))]
 sources=[{'path':p.relative_to(ROOT).as_posix(),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':S.sha(p),'purpose':'offline source/master','quality_reason':'Source retained at original authored resolution; not loaded as a character.'}for p in sorted((OUT/'source').glob('*.png'))];write(OUT/'delivery-image-inventory.json',{'revision':REV,'images':inventory,'offline_sources':sources})
 write(OUT/'completion.json',{'revision':REV,'status':'review_candidate','new_complete_poses':7,'updated_profiles':2,'updated_actions':9,'decoded_videos':5,'all_dawn_actions_ready':43,'confirmed_horizontal_frames_preserved':True,'native_cadence_offsets_preserved':True,'default_preserved':default,'runtime_integrated':False,'device_updated':False})
 print(json.dumps({'dawn_actions_ready':43,'updated_profiles':2,'new_complete_poses':7,'horizontal_preserved':True,'default_preserved':default}),flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--finish',action='store_true');a=p.parse_args();d=build();v=verify(d);print(json.dumps({'checks':v['checks']}),flush=True)
 if a.export:export(d);d=build()
 if a.finish:finish(d)
if __name__=='__main__':main()
