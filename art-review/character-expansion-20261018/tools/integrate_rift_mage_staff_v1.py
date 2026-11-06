#!/usr/bin/env python3
"""Scoped enemy16 rebuild, native-program verification, media and review merge."""
from baseline_json import read_baseline
import argparse,copy,contextlib,hashlib,io,json,os,tempfile,subprocess
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import integrate_enemy_11_14_review as shared
import import_rift_mage_staff_v1 as art
import export_gallery as E
import validate_gallery as V
ROOT=art.ROOT;OUT=art.OUT;PREFIX='professions-class-16-enemy-'
def write(p,d):art.write(p,d)
def digest(d):return hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def owns(row):return str(row.get('profile',row.get('id',''))).startswith(PREFIX)
def build():
 shared.MAPS=[art.MP,art.BP]
 module=shared.isolated_builder()
 # Enemy16 timelines share reviewed spell sprites with enemy15. Load the
 # current definitions without rebuilding or publishing those other profiles.
 live_effects=json.loads((ROOT/'demos/gallery-data.json').read_text())['effects']
 # Selected timelines declare their own effects below; keep those IDs out of
 # the shared preload so a later scoped rebuild cannot collide with itself.
 for mapping_path in shared.MAPS:
  mapping=json.loads(Path(mapping_path).read_text())
  if mapping.get('review_timeline'):
   timeline=json.loads((Path(mapping_path).parent/mapping['review_timeline']).resolve().read_text())
   for effect_id in timeline.get('effects',{}):live_effects.pop(effect_id,None)
 read=module.read
 def scoped_read(path):
  value=read(path)
  if Path(path)==ROOT/'source-input/effects.json':value={**value,**copy.deepcopy(live_effects)}
  return value
 module.read=scoped_read
 before=shared.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert shared.snapshot_shared()==before
 assert len(data['profiles'])==3 and all(p['side']=='enemy'and str(p['classId'])=='16'for p in data['profiles'])
 assert all(owns(a)for a in data['actions'])
 write(OUT/'gallery-data.json',data);return data
def verify(data):
 baseline=read_baseline(OUT/'baseline.json');old={a['id']:a for a in baseline['gallery']['actions']if owns(a)};profiles={p['id']:p for p in data['profiles']};errors=[];checks=0
 assert set(old)=={a['id']for a in data['actions']}
 for a in data['actions']:
  before=old[a['id']];checks+=1
  for key in['key','kind','frames','revisedFrames','reviewTailFrames','contactTick','fps','duration','origin']:
   if a.get(key)!=before.get(key):errors.append({'action':a['id'],'changed_native_field':key})
  if not a['ready']:errors.append({'action':a['id'],'missing':a['missingFrames']})
  p=profiles[a['profile']];fw,fh=p['sourceFrameSize']
  for tick,row in enumerate(a.get('revisedFrames',a['frames'])+a.get('reviewTailFrames',[])):
   path=p['newFrames'].get(str(row['frame']));assert path
   im=V.image(path);flip=(p['context']=='battle')!=row.get('flip',False);off=row.get('offset',[0,0]);origin=a['origin'];at=[origin[i]+off[i]-p['anchor'][i] for i in (0,1)];at[0]+=row.get('shake',0)
   if flip and row['frame']<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in(0,1)]
   box=V.box_at(im,at,[fw,fh],flip);checks+=1
   if V.outside(box,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'tick':tick,'clipped_scene':box})
   if a.get('closeCamera'):
    c=a['closeCamera'];view=[origin[i]+off[i]+c['offset'][i]for i in(0,1)]+c['size']
    if V.outside(box,view):errors.append({'action':a['id'],'tick':tick,'clipped_close':box,'camera':view})
 cores=[]
 groups=[('idle','tactical-idle',[0,1,2],[(41,14,69,34),(51,43,63,50)]),('up','tactical-walk',[0,1],[(50,25,77,48),(57,62,68,71)]),('right','tactical-walk',[2,3],[(55,25,83,49),(61,59,71,64)]),('down','tactical-walk',[4,5],[(47,25,82,49),(59,59,70,63)]),('left','tactical-walk',[6,7],[(45,25,73,49),(55,59,64,64)])]
 for name,kind,ids,boxes in groups:
  ims=[Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')for i in ids]
  for box in boxes:
   checks+=1
   if not all(im.crop(box).tobytes()==ims[0].crop(box).tobytes()for im in ims):errors.append({'group':name,'body_core_changed':box})
  cores.append({'direction':name,'frames':ids,'fixed_regions':boxes,'core_pixel_drift':0})
 for p in profiles.values():
  for slot,path in p['newFrames'].items():
   im=Image.open(ROOT/path).convert('RGBA');checks+=1
   if list(im.size)!=p['outputFrameSize']or im.getbbox()is None:errors.append({'path':path,'size_or_alpha':False})
   if {q[:3]for q in im.getdata()if q[3]}-set(art.C):errors.append({'path':path,'palette_changed':True})
 errors+=data['validation']['structuralIssues']
 write(OUT/'checks.json',{'passed':not errors,'checks':checks,'profiles':len(profiles),'actions':len(data['actions']),'errors':errors,'native_programs_and_spell_effect_tracks_unchanged':True,'fixed_body_core_measurements':cores,'runtime_integrated':False,'visual_acceptance':'Production preview inspected; user acceptance pending.'})
 if errors:raise ValueError(str(len(errors))+' target checks failed; see checks.json')
 return checks
def export(data):
 records=[];videos=[];profiles={p['id']:p for p in data['profiles']}
 for a in data['actions']:
  records.append(E.export(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not a.get('defaultVideo',False))))
  if a.get('defaultVideo')and a['kind']=='attack':records.append(E.export(data,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  if a.get('defaultVideo'):
   path=ROOT/'demos/videos'/(a['id']+'.mp4');info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(path)],text=True))['streams'][0]
   assert int(info['nb_read_frames'])==E.playback_count(a)
   videos.append({'path':path.relative_to(ROOT).as_posix(),'frames':int(info['nb_read_frames']),'seconds':float(info['duration'])})
 # Representative native phases, both backgrounds, independent of the page.
 for a in data['actions']:
  if not(a.get('defaultVideo')or a['kind']in['map_idle','map_walk']):continue
  tick=a['contactTick']if a['contactTick']is not None else 0
  for light in[False,True]:E.render_frame(data,profiles[a['profile']],a,tick,4,light,False).save(OUT/(a['key']+('-light.png'if light else'-dark.png')),optimize=True)
 write(OUT/'export-report.json',{'stills':len(data['actions']),'records':records,'decoded_main_videos':videos,'representative_videos_only':True,'all_canvas_actions_complete':True})
def merge(data):
 files=shared.source_paths();before=shared.snapshot_shared();live=json.loads(files[1].read_text());assert shared.parse_js(files[0])==live
 combined=copy.deepcopy(live);old={kind:[r for r in live[kind]if not owns(r)]for kind in['profiles','actions']}
 for kind in['profiles','actions']:
  new={r['id']:r for r in data[kind]};assert {r['id']for r in live[kind]if owns(r)}==set(new)
  combined[kind]=[new[r['id']]if owns(r)else r for r in live[kind]]
  assert [r for r in combined[kind]if not owns(r)]==old[kind]
 # Effects are reused; changing their global definitions is outside this art update.
 for a in data['actions']:
  for row in a['frames']+a.get('revisedFrames',[])+a.get('reviewTailFrames',[]):
   for e in row.get('effects',[]):assert combined['effects'][e['sprite']]==data['effects'][e['sprite']]
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])}
 report=json.loads(files[2].read_text());report['builtAt']=combined['builtAt'];report['summary']=combined['summary'];rows={a['id']:{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in data['actions']};report['actions']=[rows.get(r['id'],r)for r in report['actions']]
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));texts={files[0]:'window.GALLERY_DATA = '+payload+';\n',files[1]:payload+'\n',files[2]:json.dumps(report,ensure_ascii=False,indent=2)+'\n'};staged=[]
 try:
  for path,text in texts.items():fd,name=tempfile.mkstemp(prefix='.rift-mage-',dir=path.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),path))
  assert shared.snapshot_shared()==before,'concurrent shared writer; retry with latest files'
  for temp,path in staged:os.replace(temp,path)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert json.loads(files[1].read_text())==combined and shared.parse_js(files[0])==combined
 assert shared.sha(files[3])==before['index.html']
 write(OUT/'merge-report.json',{'target_profiles':3,'target_actions':len(data['actions']),'other_profile_count':len(old['profiles']),'other_action_count':len(old['actions']),'all_non_target_records_unchanged':True,'global_effects_unchanged':True,'index_default_unchanged':True})
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--export',action='store_true');parser.add_argument('--merge',action='store_true');args=parser.parse_args();data=build();checks=verify(data)
 print(json.dumps({'profiles':len(data['profiles']),'actions':len(data['actions']),'checks':checks,'default_videos':sum(bool(a.get('defaultVideo'))for a in data['actions'])}),flush=True)
 if args.export:export(data);data=build()
 if args.merge:merge(data)
if __name__=='__main__':main()
