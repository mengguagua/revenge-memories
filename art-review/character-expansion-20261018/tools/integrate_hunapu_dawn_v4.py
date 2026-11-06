#!/usr/bin/env python3
"""Publish only Dawn Warrior tactical walk art and preserve other review rows."""
import argparse,contextlib,copy,hashlib,io,json,os,re,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit
from PIL import Image,ImageDraw,ImageOps
import import_hunapu_dawn_v4 as A
import integrate_enemy_11_14_review as S
import export_gallery as E
import validate_gallery as V
ROOT=A.ROOT;OUT=A.OUT;PID=A.PID;REV=A.REV
def write(p,d):A.write(p,d)
def own(x):return x.get('profile',x.get('id'))==PID or str(x.get('id','')).startswith(PID+'--')
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def build():
 S.MAPS=[A.MP];m=S.isolated_builder();read=m.read
 def scoped(path):
  v=read(path)
  if Path(path).resolve()==A.MP.resolve():v=copy.deepcopy(v);v['scenarios']=[s for s in v['scenarios']if s['id']=='tactical-walk']
  return v
 m.read=scoped;before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):d=m.build()
 assert S.snapshot_shared()==before and len(d['profiles'])==1 and len(d['actions'])==8 and all(own(x)for x in d['profiles']+d['actions'])
 d['effects']={};write(OUT/'gallery-data.json',d);return d
def head(im):
 pts=[(x,y)for y in range(26,57)for x in range(40,88)if im.getpixel((x,y))==(*A.H.HAIR,255)]
 g=max(A.H.parts(pts),key=len);return[sum(p[i]for p in g)/len(g)for i in[0,1]]
def verify(d):
 p=d['profiles'][0];old=A.baseline();op=old['profiles'][0];oldactions={a['id']:a for a in old['actions']};checks=0;errors=[]
 assert p['heroProfession']=='dawn_warrior'and p['className']=='破晓勇士'and not p['frameErrors'];assert p['mapShadow']==op['mapShadow']
 ims={int(i):Image.open(ROOT/f).convert('RGBA')for i,f in p['newFrames'].items()}
 for i,im in ims.items():
  assert im.size==(128,96)and im.getbbox()and set(im.getchannel('A').getdata())<={0,255}
  if i in[0,1,4,5]:assert p['newFrames'][str(i)]==op['newFrames'][str(i)]and im.tobytes()==Image.open(ROOT/op['newFrames'][str(i)]).convert('RGBA').tobytes()
  checks+=1
 for a in d['actions']:
  assert a['ready']and not a.get('revisedFrames');oa=oldactions[a['id']]
  assert all(a[k]==oa[k]for k in['frames','fps','origin','contactTick','duration']);w,h=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas'])
  for t,row in enumerate(a['frames']):
   f=row['frame'];x=f%p['sourceColumns']*w;y=f//p['sourceColumns']*h;at=[a['origin'][i]+row['offset'][i]-p['anchor'][i]for i in[0,1]]
   for kind,im in[('original',atlas.crop((x,y,x+w,y+h))),('redraw',ims[f])]:
    box=V.box_at(im,at,[w,h],row.get('flip',False));checks+=1
    if V.outside(box,a.get('viewport',d['viewport'])):errors.append({'action':a['id'],'tick':t,'track':kind,'bounds':box})
 for left,right in[(6,3),(7,2)]:
  assert ims[left].tobytes()==ImageOps.mirror(ims[right]).tobytes()
  w,h=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas'])
  crop=lambda f:atlas.crop((f*w,0,(f+1)*w,h))
  assert crop(left).tobytes()==ImageOps.mirror(crop(right)).tobytes()
 roots=[]
 for ids in[[2,3],[6,7]]:
  centers=[head(ims[i])for i in ids];drift=[abs(centers[0][j]-centers[1][j])for j in[0,1]]
  assert max(drift)<2,(ids,centers)
  assert all(ims[i].getbbox()[3]==95 for i in ids)
  spans=[ims[i].crop((0,86,128,96)).getbbox()for i in ids];spans=[b[2]-b[0]for b in spans]
  assert spans[1 if ids==[2,3]else 0]>spans[0 if ids==[2,3]else 1]*1.4
  upper=sum(a!=b for a,b in zip(ims[ids[0]].crop((38,51,91,79)).getdata(),ims[ids[1]].crop((38,51,91,79)).getdata()))
  roots.append({'slots':ids,'head_centroids':centers,'head_centroid_drift_output_pixels':drift,'ground_y':95,'boot_spans':spans,'upper_pose_changed_pixels':upper})
 errors+=d['validation']['structuralIssues'];report={'revision':REV,'passed':not errors,'checks':checks,'profiles':1,'actions':8,'changed_character_slots':[2,3,6,7],'native_timeline_offsets_fps_preserved':True,'native_left_phase_mirror_verified':True,'root_checks':roots,'compact_shadow_and_vertical_walk_frames_preserved':True,'runtime_integrated':False,'visual_acceptance':'pending offline inspection and user review','errors':errors};write(OUT/'verification.json',report);assert not errors,errors;return report
def boards(d):
 p=d['profiles'][0]
 for direction in['right','left']:
  a=next(a for a in d['actions']if a['key']=='walk-'+direction)
  for light in[False,True]:
   ticks=[0,16,32,48];panels=[E.render_panel(d,p,a,a['frames'][t],True,8,light,False).convert('RGB')for t in ticks];w,h=panels[0].size
   out=Image.new('RGB',(w*4,h+38),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(out)
   for n,(t,panel)in enumerate(zip(ticks,panels)):
    out.paste(panel,(n*w,0));dr.text((n*w+w/2,h+19),f'第{t+1}帧 · 姿势{a["frames"][t]["frame"]}',font=E.font(17),anchor='mm',fill=A.H.NAVY if light else'white')
   out.save(OUT/('tactical-'+direction+('-light.png'if light else'-dark.png')),optimize=True)
 # Native geometry and final art share a logical frame and center.
 q=Image.new('RGB',(4*384,380),(32,45,53));dr=ImageDraw.Draw(q);atlas=V.image(p['sourceAtlas']);w,h=p['sourceFrameSize']
 for n,i in enumerate([2,3,6,7]):
  native=atlas.crop((i*w,0,(i+1)*w,h)).resize((384,288),Image.Resampling.NEAREST);art=V.image(p['newFrames'][str(i)]).resize((384,288),Image.Resampling.NEAREST)
  # Separate native and redraw into an uncluttered pair of contact sheets.
  q.paste(native,(n*384,40),native);dr.text((n*384+192,350),f'原作槽位 {i}',font=E.font(20),anchor='mm',fill='white')
 q.save(OUT/'native-reference.png',optimize=True)
def export(d):
 records=[];videos=[]
 for a in d['actions']:
  records.append(E.export(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not a.get('defaultVideo'))))
  if a.get('defaultVideo'):
   path=ROOT/'demos/videos'/(a['id']+'.mp4');info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(path)],text=True))['streams'][0]
   assert int(info['nb_read_frames'])==len(a['frames'])and abs(float(info['duration'])-len(a['frames'])/a['fps'])<1/a['fps'];videos.append({'path':path.relative_to(ROOT).as_posix(),'frames':int(info['nb_read_frames']),'duration':float(info['duration']),'size':[info['width'],info['height']]})
  print(json.dumps({'exported':a['id']}),flush=True)
 assert len(videos)==4;write(OUT/'export-report.json',{'records':records,'decoded_videos':videos,'scope':'one tactical walk profile; no battle or story media exported'});boards(d)
def merge(d):
 paths=S.source_paths();before=S.snapshot_shared();live=json.loads(paths[1].read_text());assert S.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=S.merge_rows(live[field],d[field],own);assert[x for x in live[field]if not own(x)]==[x for x in combined[field]if not own(x)]
 assert combined['effects']==live['effects'];combined['builtAt']=datetime.now(timezone.utc).isoformat()
 report=json.loads(paths[2].read_text());report['builtAt']=combined['builtAt'];report['actions']=S.merge_rows(report['actions'],[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in d['actions']],own)
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.hunapu-strafe-v4-',dir=p.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),p))
  assert S.snapshot_shared()==before,'Concurrent gallery writer; retry fresh'
  for tmp,p in staged:os.replace(tmp,p)
 finally:
  for tmp,_ in staged:tmp.unlink(missing_ok=True)
 assert S.parse_js(paths[0])==combined==json.loads(paths[1].read_text())and S.sha(paths[3])==before['index.html']
 write(OUT/'merge-report.json',{'target_profiles':1,'target_actions':8,'unrelated_rows_and_effects_preserved':True,'index_default_unchanged':True})
def finish(d):
 for a in d['actions']:assert a.get('still')and(a.get('video')if a.get('defaultVideo')else True)
 merge(d);page=ROOT/'index.html';old=page.read_text();default=re.search(r'data-default-action="([^"]+)"',old).group(1);m=re.search(r'<section\b[^>]*id="hunapu-dawn-progress".*?</section>',old,re.S);assert m
 section=m.group();section=section.replace('剧情全身联动、正面持盾横移 · 待验收','斜跨持剑、低位持盾横移 · 待验收')
 note='<p class="action-note" style="margin:0 0 16px">按确认的原作姿势重新制作战斗地图左右横移：脸朝前、胸面可见，肩胯略有错位；剑柄握于腹前，剑斜跨胸前，另一手低位持盾贴住腹部前侧。收腿略重叠与屈膝跨步交替，左右遵循原作镜像与原节奏，人物中心稳定。</p>'
 section=re.sub(r'<p class="action-note" style="margin:0 0 16px">.*?</p>',note,section,count=1,flags=re.S)
 section=section.replace('hunapu-dawn-map-body-v3-20261024/maps-light.png',REV+'/poses-light.png').replace('地图全身联动与正面持盾','斜跨持剑与低位持盾姿势').replace('hunapu-dawn-map-body-v3-20261024/README.md',REV+'/README.md')
 for direction,label in[('right','向右斜跨持剑横移'),('left','向左斜跨持剑横移')]:
  section=section.replace('hunapu-dawn-map-body-v3-20261024/tactical-'+direction+'-dark.png',REV+'/tactical-'+direction+'-dark.png').replace('正面向'+('右'if direction=='right'else'左')+'横移',label)
 new=old[:m.start()]+section+old[m.end():];new=re.sub(r'&hunapu_dawn=[^"&]+','',new);new=re.sub(r'(src="gallery-data\.js\?[^"]*)"',lambda m:m.group(1)+'&hunapu_dawn=strafe-v4-20261024"',new,count=1)
 assert re.search(r'data-default-action="([^"]+)"',new).group(1)==default
 for href in re.findall(r'href="([^"]+)"',section):
  u=urlsplit(href)
  if not u.query and not u.scheme:assert(ROOT/u.path).is_file(),href
 assert page.read_text()==old,'Concurrent page writer; retry fresh';page.write_text(new)
 mp=ROOT/'hunapu-promoted/manifest.json';manifest=json.loads(mp.read_text());manifest.update(revision=REV,tactical_walk_revision=REV,review_record='../'+REV+'/README.md');write(mp,manifest)
 cp=ROOT/'healer-saint-complete-v1-20261023/profession-catalog-sync.json';catalog=json.loads(cp.read_text());h=next(h for h in catalog['exclusive_heroes']if h['actor']=='胡纳普');h.update(art_status='专属进阶43项齐备；左右横移按确认的斜跨持剑与低位持盾重做，待验收',review_revision=REV,runtime_integrated=False);write(cp,catalog)
 live=json.loads((ROOT/'demos/gallery-data.json').read_text());dawn=[a for a in live['actions']if a['profile'].startswith('hunapu-promoted-')];assert len(dawn)==43 and all(a['ready']for a in dawn)
 changed=[]
 for f in['profiles','actions']:
  for row in live[f]:
   prior=A.baseline()['unrelated_row_hashes'][f].get(row['id'])
   if prior is not None and digest(row)!=prior:changed.append(row['id'])
 # Other chats may update their own rows; merge preservation is against latest live.
 for field in['profiles','actions']:
  for row in live[field]:
   if str(row.get('profile',row['id'])).startswith('hunapu-promoted-')and not own(row):
    assert digest(row)==A.baseline()['unrelated_row_hashes'][field][row['id']],row['id']
 files=[p for p in OUT.rglob('*.png')if 'source'not in p.relative_to(OUT).parts]+[ROOT/'demos/stills'/(a['id']+'.png')for a in d['actions']]
 inventory=[{'path':p.relative_to(ROOT).as_posix(),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':S.sha(p),'purpose':'character pose'if p.parent.name=='tactical-walk'else'lossless review or export'}for p in sorted(set(files))]
 sources=[{'path':p.relative_to(ROOT).as_posix(),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':S.sha(p),'purpose':'offline generation master or extraction input','quality_reason':'Original source retained at authored resolution; not loaded by the player or game.'}for p in sorted((OUT/'source').glob('*.png'))]
 write(OUT/'delivery-image-inventory.json',{'revision':REV,'images':inventory,'offline_sources':sources,'source_masters':'source/, retained offline and not loaded as characters'})
 write(OUT/'completion.json',{'revision':REV,'status':'review_candidate','changed_slots':[2,3,6,7],'tactical_walk_actions':8,'decoded_videos':4,'all_dawn_actions_ready':43,'native_cadence_and_offsets_preserved':True,'non_owned_changes_during_work':changed,'latest_live_unrelated_rows_preserved':True,'default_preserved':default,'runtime_integrated':False,'device_updated':False})
 print(json.dumps({'ready_dawn_actions':43,'updated_profile':PID,'new_character_frames':4,'page_default_preserved':default}),flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--finish',action='store_true');a=p.parse_args();d=build();v=verify(d);print(json.dumps({'checks':v['checks']}),flush=True)
 if a.export:export(d);d=build()
 if a.finish:finish(d)
if __name__=='__main__':main()
