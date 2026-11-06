#!/usr/bin/env python3
"""Single-action art-review integration: brigand map idle only. No game or page edits."""
from pathlib import Path
from types import SimpleNamespace
import argparse,contextlib,copy,hashlib,io,json,os,subprocess,tempfile
from datetime import datetime,timezone
from PIL import Image
import build_gallery as G
import export_gallery as E
from integrate_enemy_11_14_review import isolated_builder,parse_js
ROOT=G.ROOT
OUT=ROOT/'brigand-idle-shoulders-v2-20261023'
PID='professions-class-14-enemy-maps-tactical-idle'
AID=PID+'--idle-cycle'
MAPPING=ROOT/'professions/class-14-enemy/maps/frame_mapping.json'
def digest(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def file_hash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def targets():return [ROOT/'gallery-data.js',ROOT/'demos/gallery-data.json',ROOT/'demos/build-report.json',ROOT/'index.html']
def shared_hashes():return {str(p.relative_to(ROOT)):file_hash(p) for p in targets()}
def selected_build():
 module=isolated_builder();module.SCOPED_MAPPING_PATHS={str(MAPPING.resolve())}
 with contextlib.redirect_stdout(io.StringIO()):full=module.build()
 pp=[p for p in full['profiles'] if p['id']==PID];aa=[a for a in full['actions'] if a['id']==AID]
 assert len(pp)==len(aa)==1,'Missing or duplicate target'
 data={**full,'profiles':pp,'actions':aa,'effects':{}}
 data['summary']={'profiles':1,'actions':1,'ready':int(aa[0]['ready']),'pending':int(not aa[0]['ready'])}
 data['validation']['structuralIssues']=[x for x in full['validation']['structuralIssues'] if x.get('profile')==PID or x.get('action')==AID]
 write(OUT/'gallery-data.json',data);return data

def verify(data):
 p=data['profiles'][0];a=data['actions'][0];checks=[]
 def check(condition,label):
  if not condition:raise ValueError(label)
  checks.append(label)
 check(p['id']==PID and p['classId']=='14' and p['side']=='enemy' and p['context']=='tactical-idle','Exact enemy14 idle profile')
 check(a['id']==AID and a['profile']==PID and a['key']=='idle-cycle','Exact idle-cycle action')
 expected=[]
 for _ in range(2):
  for frame,n in zip([0,1,2,1],[14,8,14,8]):expected.extend([{'frame':frame,'offset':[0,0],'flip':False,'effects':[]} for _ in range(n)])
 check(a['frames']==expected,'Native 0/1/2/1 holds14/8/14/8 repeated twice: 88 frames')
 check(a['fps']==60.0988 and a['contactTick'] is None,'Original fps and no gameplay contact')
 check(abs(a['duration']-88/60.0988)<1e-10,'Original duration')
 check(not a.get('revisedFrames') and not a.get('reviewTailFrames') and not a.get('effectIds'),'No timeline, tail or effect change')
 check(a['ready'] and not p.get('frameErrors') and not data['validation']['structuralIssues'],'Paths and readiness complete')
 with Image.open(ROOT/p['sourceAtlas']) as im:im.load();check(im.width>=p['sourceFrameSize'][0]*3,'Native reference image loads')
 assets=[]
 for slot,raw in p['newFrames'].items():
  path=ROOT/raw
  with Image.open(path) as image:
   im=image.convert('RGBA');im.load();check(list(im.size)==p['outputFrameSize'] and im.getbbox() is not None,'Pose '+slot+' loads with complete output canvas')
   assets.append({'slot':slot,'path':raw,'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path)})
 report={'passed':True,'checks':len(checks),'labels':checks,'profile':PID,'action':AID,'frames':88,'fps':a['fps'],'duration':a['duration'],'assets':assets,'scope':'Only the changed map idle action. No walking, battle, other characters or game integration checks run.','visual_acceptance':'Shoulder amplitude and neck/collar continuity require the production visual review.'}
 write(OUT/'integration-checks.json',report);return report

def export_one(data):
 p=data['profiles'][0];a=data['actions'][0]
 result=E.export(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False))
 video=ROOT/'demos/videos'/(AID+'.mp4');info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(video)],text=True))['streams'][0]
 assert int(info['nb_read_frames'])==88 and abs(float(info['duration'])-a['duration'])<1/a['fps']
 # One representative output frame per native pose, on both backgrounds.
 for tick in [0,14,22]:
  for light in [False,True]:
   image=E.render_frame(data,p,a,tick,4,light,False)
   image.save(OUT/(f'idle-{a["frames"][tick]["frame"]}-'+('light' if light else 'dark')+'.png'),optimize=True)
 write(OUT/'export-report.json',{'action':AID,'export':result,'video':str(video.relative_to(ROOT)),'decoded_frames':int(info['nb_read_frames']),'duration':float(info['duration']),'dimensions':[info['width'],info['height']],'passed':True,'scope':'One idle-cycle video and six representative dark/light stills only.'})

def merge_one(data):
 verify(data);p=data['profiles'][0];a=data['actions'][0]
 assert a['video'] and a['still'],'Export this exact digest before merging'
 files=targets();before=shared_hashes();live=json.loads(files[1].read_text());assert parse_js(files[0])==live,'Parallel bundle write in progress; retry'
 assert sum(x['id']==PID for x in live['profiles'])==sum(x['id']==AID for x in live['actions'])==1
 others_before={'profiles':{x['id']:digest(x) for x in live['profiles'] if x['id']!=PID},'actions':{x['id']:digest(x) for x in live['actions'] if x['id']!=AID}}
 combined=copy.deepcopy(live)
 combined['profiles']=[p if x['id']==PID else x for x in combined['profiles']]
 combined['actions']=[a if x['id']==AID else x for x in combined['actions']]
 combined['builtAt']=datetime.now(timezone.utc).isoformat()
 combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(x['ready'] for x in combined['actions']),'pending':sum(not x['ready'] for x in combined['actions'])}
 # All effects, validation, unrelated metadata and unknown fields retain the latest values.
 others_after={'profiles':{x['id']:digest(x) for x in combined['profiles'] if x['id']!=PID},'actions':{x['id']:digest(x) for x in combined['actions'] if x['id']!=AID}}
 assert others_before==others_after
 report=json.loads(files[2].read_text());report['builtAt']=combined['builtAt'];report['summary']=combined['summary']
 row={k:a[k] for k in ['id','name','ready','missingFrames','missingEffects','duration']}
 assert sum(x['id']==AID for x in report['actions'])==1
 report['actions']=[row if x['id']==AID else x for x in report['actions']]
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'))
 texts={files[0]:'window.GALLERY_DATA = '+payload+';\n',files[1]:payload+'\n',files[2]:json.dumps(report,ensure_ascii=False,indent=2)+'\n'}
 staged=[]
 try:
  for path,text in texts.items():
   fd,name=tempfile.mkstemp(prefix='.brigand-idle-',dir=path.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),path))
  assert shared_hashes()==before,'Concurrent writer changed shared files; no merge performed. Retry against latest.'
  for tmp,path in staged:os.replace(tmp,path)
 finally:
  for tmp,_ in staged:tmp.unlink(missing_ok=True)
 assert file_hash(files[3])==before['index.html'],'Page changed concurrently; never restore an older page'
 after=json.loads(files[1].read_text());assert after==combined and parse_js(files[0])==combined,'Concurrent writer after merge; investigate without rollback'
 write(OUT/'merge-report.json',{'passed':True,'exact_profile':PID,'exact_action':AID,'non_target_profiles_verified':len(others_before['profiles']),'non_target_actions_verified':len(others_before['actions']),'non_target_hashes_before':others_before,'non_target_hashes_after':others_after,'all_other_profile_action_hashes_unchanged':True,'effects_unchanged':combined['effects']==live['effects'],'index_and_default_unchanged':True,'before_shared_hashes':before,'after_shared_hashes':shared_hashes(),'single_file_atomic_writes':True,'concurrency_note':'Unrelated writers do not honor this helper lock; pre/post hash checks detect overlap, no automatic stale rollback.'})

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inspect',action='store_true');parser.add_argument('--export',action='store_true');parser.add_argument('--merge',action='store_true');args=parser.parse_args()
 if args.inspect:
  isolated_builder();print(json.dumps({'profile':PID,'action':AID,'mapping':str(MAPPING.relative_to(ROOT)),'planned_video_frames':88,'shared_outputs_written':False},ensure_ascii=False));return
 OUT.mkdir(parents=True,exist_ok=True);lock=OUT/'integration.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 try:
  os.write(fd,str(os.getpid()).encode());os.close(fd);data=selected_build();report=verify(data)
  if args.export:export_one(data);data=selected_build()
  if args.merge:merge_one(data)
  print(json.dumps({'checks':report['checks'],'exported':args.export,'merged':args.merge,'profile':PID,'action':AID},ensure_ascii=False))
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':main()
