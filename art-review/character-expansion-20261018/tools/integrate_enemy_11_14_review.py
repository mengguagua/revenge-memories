#!/usr/bin/env python3
"""Scoped art-review build/export/validation for enemy11/14. Never touch actual.
The shared builder/export/validator entry points are intentionally not invoked.
--merge is explicit; it preserves unrelated latest records and the page default.
"""
from pathlib import Path
from types import SimpleNamespace, ModuleType
from datetime import datetime, timezone
import argparse, ast, contextlib, copy, hashlib, io, json, os, subprocess, tempfile
from PIL import Image
import build_gallery as G
import export_gallery as E
import validate_gallery as V
ROOT=G.ROOT
OUT=ROOT/'enemy-11-14-review-20261023'
PREFIXES=('professions-class-11-enemy-','professions-class-14-enemy-')
MAPS=[ROOT/f'professions/class-{cid}-enemy/{part}/frame_mapping.json' for cid in (11,14) for part in ('maps','battle')]
def own_profile(p):return str(p.get('id','')).startswith(PREFIXES)
def own_action(a):return str(a.get('profile','')).startswith(PREFIXES)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def source_paths():
 return [ROOT/'gallery-data.js',ROOT/'demos/gallery-data.json',ROOT/'demos/build-report.json',ROOT/'index.html']
def snapshot_shared():return {str(p.relative_to(ROOT)):sha(p) if p.exists() else None for p in source_paths()}

def isolated_builder():
 """Reuse the current builder logic, limiting its mapping reads and removing all outputs."""
 path=ROOT/'tools/build_gallery.py';tree=ast.parse(path.read_text(),filename=str(path))
 fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='build')
 removed=[];filtered=[]
 class Scope(ast.NodeTransformer):
  def visit_For(self,node):
   node=self.generic_visit(node)
   if isinstance(node.target,ast.Name) and node.target.id=='mapping_path':
    node.body.insert(0,ast.parse("if str(mapping_path.resolve()) not in SCOPED_MAPPING_PATHS: continue").body[0]);filtered.append('mappings')
   if isinstance(node.target,ast.Name) and node.target.id=='bundle_path':
    node.body.insert(0,ast.Continue());filtered.append('bundles')
   return node
  def visit_Expr(self,node):
   if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr in ['write_text','mkdir']:
    removed.append(node.value.func.attr);return None
   return self.generic_visit(node)
 Scope().visit(fn)
 if removed.count('write_text')!=3 or sorted(filtered)!=['bundles','mappings']:
  raise RuntimeError('Shared builder changed: review scoped transformation before using it.')
 # A renamed module cannot execute the original __main__ entry point.
 module=ModuleType('scoped_enemy_11_14_builder');module.__file__=str(path)
 module.SCOPED_MAPPING_PATHS={str(p.resolve()) for p in MAPS}
 exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),module.__dict__)
 return module

def build_local():
 absent=[str(p.relative_to(ROOT)) for p in MAPS if not p.is_file()]
 if absent:raise ValueError('Required enemy mappings not yet ready: '+', '.join(absent))
 before=snapshot_shared()
 module=isolated_builder()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert data['profiles'] and all(own_profile(p) and p.get('side')=='enemy' for p in data['profiles'])
 assert all(own_action(a) for a in data['actions'])
 assert {p['classId'] for p in data['profiles']}=={'11','14'}
 assert snapshot_shared()==before,'Scoped build unexpectedly altered shared files'
 write(OUT/'gallery-data.json',data)
 return data

def verify(data):
 profiles={p['id']:p for p in data['profiles']};errors=[];checks=0
 for p in profiles.values():
  if p.get('frameErrors'):errors.append({'profile':p['id'],'frameErrors':p['frameErrors']})
  for k,filename in p['newFrames'].items():
   im=Image.open(ROOT/filename).convert('RGBA');checks+=1
   legal_blank=False
   if p.get('classId')=='11' and p.get('side')=='enemy' and p.get('context')=='battle' and str(k)=='49':
    baseline=json.loads((ROOT/'enemy-revenant-brigand-v1-20261023/source/native-baseline.json').read_text())
    fw,fh=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas']);f=49
    src=atlas.crop((f%p['sourceColumns']*fw,f//p['sourceColumns']*fh,(f%p['sourceColumns']+1)*fw,(f//p['sourceColumns']+1)*fh))
    legal_blank=49 in baseline['classes']['11'].get('native_blank_frames',[]) and src.getbbox() is None
   if list(im.size)!=p['outputFrameSize'] or (im.getbbox() is None and not legal_blank):errors.append({'profile':p['id'],'frame':k,'error':'empty or incorrect dimensions'})
 for cid in ('11','14'):
  expected={f'professions-class-{cid}-enemy-battle':{f'original_class_{cid}_enemy_normal','idle','miss','hit','exit'},f'professions-class-{cid}-enemy-maps-tactical-idle':{'idle-cycle'},f'professions-class-{cid}-enemy-maps-tactical-walk':{'walk-'+d for d in ('up','right','down','left')}|{'idle-'+d for d in ('up','right','down','left')}}
  for pid,keys in expected.items():
   actual={a['key'] for a in data['actions'] if a['profile']==pid};checks+=1
   if actual!=keys:errors.append({'profile':pid,'expected_keys':sorted(keys),'actual_keys':sorted(actual)})
 for a in data['actions']:
  p=profiles[a['profile']];fw,fh=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas'])
  if a['kind']=='attack':
   cid=p['classId'];expected={'11':(472,274),'14':(181,84)}[cid];checks+=1
   if len(a['frames'])!=expected[0] or a['contactTick']!=expected[1]:errors.append({'action':a['id'],'error':'native attack timing changed'})
   if '_ally' in a['key'] or a['key']!=f'original_class_{cid}_enemy_normal':errors.append({'action':a['id'],'error':'unexpected allied or spell variant'})
  if not a['ready']:errors.append({'action':a['id'],'missingFrames':a['missingFrames'],'missingEffects':a['missingEffects'],'sourceReviewPending':a.get('sourceReviewPending')})
  tracks=[('original',a['frames']),('redraw',a.get('revisedFrames',a['frames']))]
  if a.get('reviewTailFrames'):tracks.append(('redraw-tail',a['reviewTailFrames']))
  for kind,rows in tracks:
   for tick,row in enumerate(rows):
    f=row['frame'];flip=(p['context']=='battle' and p.get('side')=='enemy')!=row.get('flip',False)
    offset=row.get('offset',[0,0]);origin=a['origin'];view=a.get('viewport',data['viewport'])
    at=[origin[i]+offset[i]-p['anchor'][i] for i in range(2)];at[0]+=row.get('shake',0)
    if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i] for i in range(2)]
    if kind=='original':
     if not 0<=f<p['sourceFrameCount']:errors.append({'action':a['id'],'error':'source frame out of range','frame':f});continue
     x=f%p['sourceColumns']*fw;y=f//p['sourceColumns']*fh;im=atlas.crop((x,y,x+fw,y+fh))
    else:
     if str(f) not in p['newFrames']:continue
     im=V.image(p['newFrames'][str(f)])
    box=V.box_at(im,at,[fw,fh],flip);checks+=1
    if V.outside(box,view):errors.append({'action':a['id'],'tick':tick,'track':kind,'mode':'scene','bounds':box,'viewport':view})
    if a.get('closeCamera'):
     cam=a['closeCamera'];cv=[origin[i]+offset[i]+cam['offset'][i] for i in range(2)]+cam['size'];checks+=1
     if V.outside(box,cv):errors.append({'action':a['id'],'tick':tick,'track':kind,'mode':'close','bounds':box,'viewport':cv})
    for effect in row.get('effects',[]):
     meta=p.get('revisedEffects',{}).get(effect['sprite'],data['effects'][effect['sprite']]) if kind!='original' else data['effects'][effect['sprite']]
     xy=[effect['position'][i]-meta['anchor'][i] for i in range(2)]
     if effect.get('flip'):xy=[xy[i]+meta.get('flip_origin_offset',[0,0])[i] for i in range(2)]
     eb=V.box_at(V.image(meta['path']),xy,meta['frame_size'],effect.get('flip',False));checks+=1
     if V.outside(eb,view):errors.append({'action':a['id'],'tick':tick,'track':kind,'effect':effect['sprite'],'bounds':eb})
 errors+=data['validation']['structuralIssues']
 report={'passed':not errors,'checks':checks,'profiles':len(profiles),'actions':len(data['actions']),'errors':errors,'scope':'Only enemy11/14; original and revised alpha extents, map source audit, effect paths, timeline readiness. No game integration.','visual_acceptance':'Requires actual dark/light and motion inspection; not inferred from these assertions.'}
 write(OUT/'verification.json',report)
 if errors:raise ValueError(f'Enemy11/14 verification failed: {len(errors)} errors; see local verification.json')
 return report

def export_local(data,video_mode):
 records=[];before=snapshot_shared()
 for action in data['actions']:
  if not action['ready']:raise ValueError('Cannot export incomplete action '+action['id'])
  args=SimpleNamespace(close=False,scale=4,light=False,stills_only=True)
  records.append(E.export(data,action,args))
  if video_mode=='all' or (video_mode=='default' and action.get('defaultVideo')):
   args.stills_only=False;record=E.export(data,action,args);records.append(record)
   if action['context']=='battle' and action['kind']=='attack':
    args.close=True;records.append(E.export(data,action,args))
 # Render dark/light stills into task-owned folder; do not overwrite dark demo metadata.
 profiles={p['id']:p for p in data['profiles']};previews=OUT/'previews';previews.mkdir(parents=True,exist_ok=True)
 for a in data['actions']:
  p=profiles[a['profile']];tick=a['contactTick'] if a['contactTick'] is not None else min(8,len(a['frames'])-1)
  for light in (False,True):
   filename=previews/(a['id']+('-light.png' if light else '-dark.png'))
   E.render_frame(data,p,a,tick,4,light,False).save(filename,optimize=True)
 shared_after=snapshot_shared() # Other tasks may legitimately publish during a long export.
 decoded=[]
 for action in data['actions']:
  for close in (False,True):
   video=ROOT/'demos/videos'/(action['id']+('--close' if close else '')+'.mp4')
   if not video.exists():continue
   metadata=video.with_suffix('.json')
   if not metadata.exists() or json.loads(metadata.read_text()).get('contentDigest')!=action['contentDigest']:continue
   result=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(video)],capture_output=True,text=True,check=True)
   info=json.loads(result.stdout)['streams'][0];n=E.playback_count(action)
   if int(info['nb_read_frames'])!=n or abs(float(info['duration'])-n/action['fps'])>1/action['fps']:raise ValueError('Video timing mismatch '+str(video))
   decoded.append({'file':video.relative_to(ROOT).as_posix(),'frames':n,'duration':float(info['duration']),'dimensions':[info['width'],info['height']]})
 write(OUT/'export-report.json',{'exports':records,'decoded_videos':decoded,'shared_before_hashes':before,'shared_after_hashes':shared_after,'external_shared_changes_during_export':before!=shared_after,'shared_outputs_written_by_this_export':False,'scope':'Only action IDs owned by enemy11/14; all other demo media untouched.'})
 return decoded

def parse_js(path):
 text=path.read_text();prefix='window.GALLERY_DATA = '
 if not text.startswith(prefix):raise ValueError('Unexpected shared JS wrapper')
 return json.loads(text[len(prefix):].strip().rstrip(';'))
def merge_rows(old,new,owns):
 byid={r['id']:r for r in new};out=[]
 for row in old:
  if not owns(row):out.append(row)
  elif row['id'] in byid:out.append(byid.pop(row['id']))
 out.extend(row for row in new if row['id'] in byid)
 return out

def merge(data):
 """Read the latest live files, refuse concurrent changes, replace only owned IDs.
 Other tools do not share this lock; the hash checks detect changes before writes.
 Never roll back by overwriting a subsequently changed shared file.
 """
 verify(data);shared=source_paths();before=snapshot_shared()
 current=json.loads(shared[1].read_text())
 if parse_js(shared[0])!=current:raise RuntimeError('Shared JS/JSON differ, likely another writer; retry after it finishes')
 combined=copy.deepcopy(current)
 combined['profiles']=merge_rows(current['profiles'],data['profiles'],own_profile)
 combined['actions']=merge_rows(current['actions'],data['actions'],own_action)
 effect_ids={e['sprite'] for a in data['actions'] for row in a['frames']+a.get('revisedFrames',[])+a.get('reviewTailFrames',[]) for e in row.get('effects',[])}
 other_effects={e['sprite'] for a in current['actions'] if not own_action(a) for row in a['frames']+a.get('revisedFrames',[])+a.get('reviewTailFrames',[]) for e in row.get('effects',[])}
 for key in effect_ids:
  value=data['effects'][key]
  if key in other_effects and current['effects'].get(key)!=value:raise ValueError('Shared effect changed by another profile: '+key)
  combined['effects'][key]=value
 combined['summary']={**current['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready'] for a in combined['actions']),'pending':sum(not a['ready'] for a in combined['actions'])}
 combined['builtAt']=datetime.now(timezone.utc).isoformat()
 # Keep unrelated warnings and all unknown top-level metadata as they are.
 def own_issue(x):return str(x.get('profile',x.get('action',''))).startswith(PREFIXES) or any(f'class-{cid}-enemy/' in str(x.get('path','')) for cid in (11,14))
 combined['validation']['structuralIssues']=[x for x in current['validation']['structuralIssues'] if not own_issue(x)]+data['validation']['structuralIssues']
 report=json.loads(shared[2].read_text());report['builtAt']=combined['builtAt'];report['summary']=combined['summary'];report['validation']=combined['validation']
 local_rows=[{k:a[k] for k in ['id','name','ready','missingFrames','missingEffects','duration']} for a in data['actions']]
 report['actions']=merge_rows(report.get('actions',[]),local_rows,lambda x:str(x.get('id','')).startswith(PREFIXES))
 for key,owns in [('profiles',own_profile),('actions',own_action)]:assert [x for x in current[key] if not owns(x)]==[x for x in combined[key] if not owns(x)]
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'))
 texts={shared[0]:'window.GALLERY_DATA = '+payload+';\n',shared[1]:payload+'\n',shared[2]:json.dumps(report,ensure_ascii=False,indent=2)+'\n'}
 temp=[]
 try:
  for path,text in texts.items():
   fd,name=tempfile.mkstemp(prefix='.enemy-11-14-',dir=path.parent);os.close(fd);Path(name).write_text(text);temp.append((Path(name),path))
  if snapshot_shared()!=before:raise RuntimeError('Another writer changed shared files; no merge performed. Rerun against the latest data.')
  for staging,path in temp:os.replace(staging,path)
 finally:
  for staging,_ in temp:
   if staging.exists():staging.unlink()
 assert sha(ROOT/'index.html')==before['index.html'],'Page/default changed concurrently; do not restore an older index'
 assert json.loads(shared[1].read_text())==combined and parse_js(shared[0])==combined,'Concurrent writer detected after merge; investigate without rollback'
 write(OUT/'merge-report.json',{'merged_at':combined['builtAt'],'target_profiles':[p['id'] for p in data['profiles']],'target_actions':len(data['actions']),'before_hashes':before,'after_hashes':snapshot_shared(),'unrelated_profiles_actions_preserved':True,'index_and_default_unchanged':True,'concurrency_note':'Unrelated tools do not honor this helper lock. Fresh-read/hash checks and post-merge comparison detect concurrent mutation; shared writes should be serialized where possible.'})

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inspect',action='store_true');parser.add_argument('--export',choices=['none','default','all'],default='none');parser.add_argument('--merge',action='store_true');args=parser.parse_args()
 if args.inspect:
  isolated_builder();print(json.dumps({'required_mappings':[str(p.relative_to(ROOT)) for p in MAPS],'available':[p.is_file() for p in MAPS],'shared_outputs':'untouched','default_action':'untouched'},ensure_ascii=False));return
 OUT.mkdir(parents=True,exist_ok=True)
 lock=OUT/'integration.lock'
 fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 try:
  os.write(fd,str(os.getpid()).encode());os.close(fd)
  data=build_local();verification=verify(data)
  if args.export!='none':export_local(data,args.export);data=build_local()
  if args.merge:merge(data)
  print(json.dumps({'profiles':len(data['profiles']),'actions':len(data['actions']),'checks':verification['checks'],'export':args.export,'merged':args.merge,'report':str(OUT)},ensure_ascii=False))
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':main()
