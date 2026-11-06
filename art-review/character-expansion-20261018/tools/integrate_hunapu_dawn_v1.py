#!/usr/bin/env python3
"""Build only Hunapu's separate Dawn Warrior review, never game/runtime files."""
import argparse,contextlib,copy,io,json,os,subprocess,tempfile
from datetime import datetime,timezone
from types import SimpleNamespace
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import integrate_enemy_11_14_review as shared
import import_hunapu_dawn_v1 as art
import export_gallery as E
import validate_gallery as V
ROOT=art.ROOT;OUT=art.OUT;PREFIX='hunapu-promoted-'
def own(row):return str(row.get('profile',row.get('id',''))).startswith(PREFIX)
def write(p,d):art.write(p,d)
def build():
 shared.MAPS=[art.MP,art.BP];module=shared.isolated_builder();live=json.loads((ROOT/'demos/gallery-data.json').read_text());read=module.read
 def scoped_read(path):
  value=read(path)
  if Path(path)==ROOT/'source-input/effects.json':value={**value,**copy.deepcopy(live['effects'])}
  return value
 module.read=scoped_read;before=shared.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert shared.snapshot_shared()==before and all(own(row)for row in data['profiles']+data['actions'])
 for a in data['actions']:
  if a['kind']=='attack':
   kind='实际持弓时拉弦、单箭放出、回稳；剑盾不同时持有。'if 'bow'in a['key']else'实际携带引霆剑时沿用装备效果，不新增个人法术。'if 'levin'in a['key']else'加强跃起、蜷腿与单次重斩；保留原必杀程序。'if 'critical'in a['key']else'进阶前冲、低身蓄力、单次挥斩、收势回位。'
   a['notes']='胡纳普 · 破晓勇士。'+kind+'原帧序、位移、帧率、结算时刻和攻击次数保留。'
 write(OUT/'gallery-data.json',data);return data
def verify(data):
 profiles={p['id']:p for p in data['profiles']};baseline=json.loads((art.SRC/'base-gallery.json').read_text());old={a['key']:a for a in baseline['actions']if a['context']=='battle'};checks=0;errors=[];native=[]
 assert len(profiles)==5 and len(data['actions'])==43
 for p in profiles.values():
  assert p['actor']=='hunapu'and p['classId']=='21'and p['className']=='破晓勇士'and p['heroProfession']=='dawn_warrior';assert not p['frameErrors']
  for path in p['newFrames'].values():
   im=V.image(path);assert list(im.size)==p['outputFrameSize']and im.getbbox();assert {px[:3]for px in im.getdata()if px[3]}<=set(art.C);assert set(im.getchannel('A').getdata())<={0,255};checks+=1
 for a in data['actions']:
  assert a['ready'],(a['id'],a['missingFrames'],a['missingEffects']);p=profiles[a['profile']];fw,fh=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas'])
  if a['kind']=='attack':
   n=old[a['key']];assert all(a[k]==n[k]for k in['frames','fps','contactTick','origin']);assert not a.get('reviewTailFrames')and not a.get('revisedFrames');native.append({'key':a['key'],'ticks':len(a['frames']),'contact_tick':a['contactTick'],'actor_timeline_exact':True})
  elif a['context']=='battle':assert all(r['frame']==119 for r in a['frames'])
  for track in['native','redraw']:
   for t,row in enumerate(a['frames']):
    f=row['frame'];flip=(p['context']=='battle'and p.get('side')=='enemy')!=row.get('flip',False);off=row.get('offset',[0,0]);at=[a['origin'][i]+off[i]-p['anchor'][i]for i in(0,1)];at[0]+=row.get('shake',0)
    if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in(0,1)]
    x=f%p['sourceColumns']*fw;y=f//p['sourceColumns']*fh;im=atlas.crop((x,y,x+fw,y+fh))if track=='native'else V.image(p['newFrames'][str(f)]);box=V.box_at(im,at,[fw,fh],flip);checks+=1
    if V.outside(box,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'track':track,'tick':t,'body_bounds':box})
    if a.get('closeCamera'):
     c=a['closeCamera'];view=[a['origin'][i]+off[i]+c['offset'][i]for i in(0,1)]+c['size'];checks+=1
     if V.outside(box,view):errors.append({'action':a['id'],'track':track,'tick':t,'close_body_bounds':box})
    for e in row.get('effects',[]):
     meta=p.get('revisedEffects',{}).get(e['sprite'],data['effects'][e['sprite']])if track=='redraw'else data['effects'][e['sprite']];pos=[e['position'][i]-meta['anchor'][i]for i in(0,1)]
     if e.get('flip'):pos=[pos[i]+meta.get('flip_origin_offset',[0,0])[i]for i in(0,1)]
     eb=V.box_at(V.image(meta['path']),pos,meta['frame_size'],e.get('flip',False));checks+=1
     if V.outside(eb,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'track':track,'tick':t,'effect':e['sprite'],'effect_bounds':eb})
 story=profiles['hunapu-promoted-maps-story'];world=profiles['hunapu-promoted-maps-world'];assert story['newFrames']==world['newFrames']
 stable=[]
 for kind,pairs,region in [('tactical-walk',[[0,1],[2,3],[4,5]],(0,0,128,71)),('tactical-idle',[[0,1,2]],(0,61,96,96))]:
  for ids in pairs:
   ims=[Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')for i in ids];assert all(im.crop(region).tobytes()==ims[0].crop(region).tobytes()for im in ims);assert len({im.tobytes()for im in ims})==len(ims);checks+=1;stable.append({'context':kind,'slots':ids,'fixed_region':list(region),'fixed_pixels_exact':True,'authored_limb_phases_distinct':True})
 for a,b in[(2,6),(3,7)]:assert ImageOps.mirror(Image.open(OUT/'tactical-walk'/f'frame-{a:03}.png').convert('RGBA')).tobytes()==Image.open(OUT/'tactical-walk'/f'frame-{b:03}.png').convert('RGBA').tobytes()
 registrations=json.loads((OUT/'asset-manifest.json').read_text())['registrations'];assert all(r['clipped_pixels']==0 for r in registrations)
 errors+=data['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'profiles':5,'actions':43,'native_battle_actions':native,'world_reuses_story_exactly':True,'map_fixed_regions':stable,'authored_pixels_clipped':0,'palette_colors':len(art.C),'runtime_integrated':False,'errors':errors};write(OUT/'verification.json',report);assert not errors,errors[:5];return report
def boards(data):
 profiles={p['id']:p for p in data['profiles']}
 specs=[('normal-sequence','original_class_21_promoted',[31,33,34,35,36,37,38,39,40,119]),('critical-sequence','original_class_21_critical',[0,1,8,9,10,11,12,13,14,15,16,17]),('bow-sequence','class_21_ally_bow',[125,126,127,138])]
 for label,key,slots in specs:
  a=next(a for a in data['actions']if a['key']==key);ticks=[next(t for t,r in enumerate(a['frames'])if r['frame']==slot)for slot in slots if any(r['frame']==slot for r in a['frames'])]
  p=profiles[a['profile']]
  for light in[False,True]:
   panels=[]
   for tick in ticks:
    tick=min(tick,len(a['frames'])-1);panel=E.render_panel(data,p,a,a['frames'][tick],True,4,light,True).convert('RGB');panels.append((tick,panel))
   cols=4;w=panels[0][1].width;h=panels[0][1].height+34;q=Image.new('RGB',(w*cols,h*((len(panels)+cols-1)//cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(q)
   for n,(tick,panel)in enumerate(panels):
    x=n%cols*w;y=n//cols*h;q.paste(panel,(x,y));d.text((x+w/2,y+h-17),f'{tick+1} / {len(a["frames"])} · 姿势 {a["frames"][tick]["frame"]}',font=E.font(16),anchor='mm',fill=art.NAVY if light else(235,243,242))
   q.save(OUT/(label+('-light.png'if light else'-dark.png')),optimize=True)
def export(data):
 records=[];decoded=[];profiles={p['id']:p for p in data['profiles']}
 for a in data['actions']:
  default=a.get('defaultVideo',False);records.append(E.export(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not default)))
  if default and a['kind']=='attack':records.append(E.export(data,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  for close in([False,True]if default and a['kind']=='attack'else[False]if default else[]):
   path=ROOT/'demos/videos'/(a['id']+('--close'if close else'')+'.mp4');info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(path)],text=True))['streams'][0];n=E.playback_count(a);assert int(info['nb_read_frames'])==n and abs(float(info['duration'])-n/a['fps'])<=1/a['fps'];decoded.append({'path':path.relative_to(ROOT).as_posix(),'frames':n,'duration':float(info['duration']),'size':[info['width'],info['height']]})
  if default:
   for light in[False,True]:
    tick=a['contactTick']if a['contactTick']is not None else 0;path=OUT/'previews'/(a['id']+('-light.png'if light else'-dark.png'));path.parent.mkdir(exist_ok=True);E.render_frame(data,profiles[a['profile']],a,tick,4,light,False).save(path,optimize=True)
  print(json.dumps({'exported':a['key'],'video':bool(default)}),flush=True)
 write(OUT/'export-report.json',{'records':records,'decoded_videos':decoded,'all_canvas_actions_complete':True,'only_hunapu_promoted_exported':True});boards(data)
def merge(data):
 paths=shared.source_paths();before=shared.snapshot_shared();live=json.loads(paths[1].read_text());assert shared.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=shared.merge_rows(live[field],data[field],own);assert[r for r in combined[field]if not own(r)]==[r for r in live[field]if not own(r)]
 for a in data['actions']:
  for key in a['effectIds']:assert data['effects'][key]==live['effects'][key],key
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);rows=[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in data['actions']];report['actions']=shared.merge_rows(report['actions'],rows,own)
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.hunapu-dawn-',dir=p.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),p))
  assert shared.snapshot_shared()==before,'Concurrent shared writer; retry latest merge'
  for temp,p in staged:os.replace(temp,p)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert json.loads(paths[1].read_text())==combined and shared.parse_js(paths[0])==combined and shared.sha(paths[3])==before['index.html']
 write(OUT/'merge-report.json',{'target_profiles':5,'target_actions':43,'all_unrelated_profiles_and_actions_unchanged':True,'all_existing_effects_unchanged':True,'index_default_unchanged':True,'runtime_integrated':False})
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args();data=build();v=verify(data);print(json.dumps({'actions':43,'checks':v['checks']}),flush=True)
 if args.export:export(data);data=build()
 if args.merge:merge(data)
if __name__=='__main__':main()
