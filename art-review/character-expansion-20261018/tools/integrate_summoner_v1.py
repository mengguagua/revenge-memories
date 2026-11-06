#!/usr/bin/env python3
"""Scoped enemy19 build, media and merge. No runtime or unrelated art writes."""
import argparse,ast,contextlib,copy,io,json,os,subprocess,tempfile
from datetime import datetime,timezone
from types import ModuleType,SimpleNamespace
from pathlib import Path
from PIL import Image,ImageOps
import integrate_enemy_11_14_review as shared
import import_summoner_v1 as art
import build_gallery as G
import export_gallery as E
import validate_gallery as V
ROOT=art.ROOT;OUT=art.OUT;PREFIX='professions-class-19-enemy-'
def own(row):return str(row.get('profile',row.get('id',''))).startswith(PREFIX)
def write(p,d):art.write(p,d)
def isolated_builder():
 path=ROOT/'tools/build_gallery.py';tree=ast.parse(path.read_text(),filename=str(path));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='build');removed=[];filtered=[]
 class Scope(ast.NodeTransformer):
  def visit_For(self,node):
   node=self.generic_visit(node)
   if isinstance(node.target,ast.Name)and node.target.id=='mapping_path':node.body.insert(0,ast.parse('if str(mapping_path.resolve()) not in SCOPED_MAPPING_PATHS: continue').body[0]);filtered.append('mapping')
   if isinstance(node.target,ast.Name)and node.target.id=='bundle_path':node.body.insert(0,ast.parse('if str(bundle_path.resolve()) not in SCOPED_BUNDLE_PATHS: continue').body[0]);filtered.append('bundle')
   return node
  def visit_Expr(self,node):
   if isinstance(node.value,ast.Call)and isinstance(node.value.func,ast.Attribute)and node.value.func.attr in['write_text','mkdir']:removed.append(node.value.func.attr);return None
   return self.generic_visit(node)
 Scope().visit(fn);assert removed.count('write_text')==3 and sorted(filtered)==['bundle','mapping']
 module=ModuleType('scoped_summoner_builder');module.__file__=str(path);module.SCOPED_MAPPING_PATHS={str(p.resolve())for p in[art.MP,art.BP]};module.SCOPED_BUNDLE_PATHS={str((OUT/'gallery_bundle.json').resolve())};exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),module.__dict__);return module
def build():
 module=isolated_builder();live_effects=json.loads((ROOT/'demos/gallery-data.json').read_text())['effects'];declared=json.loads((OUT/'enemy-motion.json').read_text())['effects']
 for key in declared:live_effects.pop(key,None)
 read=module.read
 def scoped_read(path):
  value=read(path)
  if Path(path)==ROOT/'source-input/effects.json':value={**value,**copy.deepcopy(live_effects)}
  return value
 module.read=scoped_read;before=shared.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert shared.snapshot_shared()==before and len(data['profiles'])==3 and len(data['actions'])==80
 assert all(own(row)for row in data['profiles']+data['actions']);write(OUT/'gallery-data.json',data);return data
def verify(data):
 audit=json.loads((art.SRC/'native-audit.json').read_text());profiles={p['id']:p for p in data['profiles']};errors=[];checks=0;nativechecks=[]
 for a in data['actions']:
  assert a['ready'],(a['id'],a['missingFrames'],a['missingEffects']);p=profiles[a['profile']];fw,fh=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas'])
  if a['key']in audit['variants']:
   v=audit['variants'][a['key']];native=[G.pack_frame(r)for r in v['frames']];assert a['frames']==native and a['contactTick']==v['contact_tick']and a['origin']==v['actor_origin']and a['fps']==v['native_fps']
   assert not a.get('reviewTailFrames')
   assert all({k:v for k,v in r.items()if k!='effects'}=={k:v for k,v in n.items()if k!='effects'}for r,n in zip(a.get('revisedFrames',native),native))
   nativechecks.append({'key':a['key'],'frames':len(native),'contact_tick':a['contactTick'],'actor_rows_exact':True});checks+=1
  if a['kind']=='map_walk':assert len(a['frames'])==96 and all(r['offset']==[0,0]for r in a['frames'])
  if a['key']=='idle-cycle':assert [r['frame']for r in a['frames']]==[k for _ in range(2)for k,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
  for track,rows in[('native',a['frames']),('redraw',a.get('revisedFrames',a['frames']))]:
   for t,row in enumerate(rows):
    f=row['frame'];flip=(p['context']=='battle')!=row.get('flip',False);off=row.get('offset',[0,0]);at=[a['origin'][i]+off[i]-p['anchor'][i]for i in(0,1)];at[0]+=row.get('shake',0)
    if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in(0,1)]
    x=f%p['sourceColumns']*fw;y=f//p['sourceColumns']*fh;im=atlas.crop((x,y,x+fw,y+fh))if track=='native'else V.image(p['newFrames'][str(f)]);box=V.box_at(im,at,[fw,fh],flip);checks+=1
    if V.outside(box,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'track':track,'tick':t,'body_bounds':box})
    if a.get('closeCamera'):
     c=a['closeCamera'];view=[a['origin'][i]+off[i]+c['offset'][i]for i in(0,1)]+c['size'];checks+=1
     if V.outside(box,view):errors.append({'action':a['id'],'track':track,'tick':t,'close_body_bounds':box})
    for e in row.get('effects',[]):
     meta=data['effects'][e['sprite']];pos=[e['position'][i]-meta['anchor'][i]for i in(0,1)]
     if e.get('flip'):pos=[pos[i]+meta.get('flip_origin_offset',[0,0])[i]for i in(0,1)]
     eb=V.box_at(V.image(meta['path']),pos,meta['frame_size'],e.get('flip',False));checks+=1
     if V.outside(eb,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'track':track,'tick':t,'effect':e['sprite'],'effect_bounds':eb})
     if a['kind']=='skill'and a.get('closeCamera'):
      c=a['closeCamera'];cv=[a['origin'][i]+off[i]+c['offset'][i]for i in(0,1)]+c['size'];checks+=1
      if V.outside(eb,cv):errors.append({'action':a['id'],'track':track,'tick':t,'close_effect':e['sprite'],'bounds':eb})
 cores=[]
 for name,kind,ids in[('idle','tactical-idle',[0,1,2]),('up','tactical-walk',[0,1]),('right','tactical-walk',[2,3]),('down','tactical-walk',[4,5])]:
  ims=[Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')for i in ids]
  for box in art.CORES[name]:assert all(im.crop(box).tobytes()==ims[0].crop(box).tobytes()for im in ims),(name,box);checks+=1
  assert len({im.tobytes()for im in ims})==len(ims);cores.append({'direction':name,'fixed_regions':art.CORES[name],'core_drift_pixels':0,'limbs_and_hem_phases_distinct':True})
 for a,b in[(2,6),(3,7)]:assert ImageOps.mirror(Image.open(OUT/'tactical-walk'/f'frame-{a:03}.png').convert('RGBA')).tobytes()==Image.open(OUT/'tactical-walk'/f'frame-{b:03}.png').convert('RGBA').tobytes()
 for p in profiles.values():
  for path in p['newFrames'].values():
   im=V.image(path);assert list(im.size)==p['outputFrameSize']and im.getbbox();assert {px[:3]for px in im.getdata()if px[3]}<=set(art.PALETTE);checks+=1
 assert len(nativechecks)==66
 summon=next(a for a in data['actions']if a['kind']=='skill');assert summon['contactTick']==80 and len(summon['frames'])==160
 assert all(not r['effects']for r in summon['frames'])
 assert max(sum(e['sprite'].startswith('review-c19-summon-guard-')for e in r['effects'])for r in summon['revisedFrames'])==2
 errors+=data['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'profiles':3,'actions':80,'native_variants':nativechecks,'fixed_map_cores':cores,'source_oam_cutoff':0,'native_actor_rows_and_timing_exact':True,'custom_summon_max_units':2,'runtime_integrated':False,'errors':errors};write(OUT/'verification.json',report);assert not errors,errors[:4];return report
def export(data):
 records=[];decoded=[];profiles={p['id']:p for p in data['profiles']}
 for a in data['actions']:
  records.append(E.export(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not a.get('defaultVideo',False))))
  if a.get('defaultVideo')and a['kind']in['attack','skill']:records.append(E.export(data,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  if a.get('defaultVideo'):
   for close in[False,True]if a['kind']in['attack','skill']else[False]:
    path=ROOT/'demos/videos'/(a['id']+('--close'if close else'')+'.mp4');info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(path)],text=True))['streams'][0];assert int(info['nb_read_frames'])==E.playback_count(a);decoded.append({'path':path.relative_to(ROOT).as_posix(),'frames':int(info['nb_read_frames']),'duration':float(info['duration']),'size':[info['width'],info['height']]})
  if a.get('defaultVideo')or a['kind']in['map_idle','map_walk']:
   for light in[False,True]:
    tick=a['contactTick']if a['contactTick']is not None else 0;path=OUT/'previews'/(a['key']+('-light.png'if light else'-dark.png'));path.parent.mkdir(exist_ok=True);E.render_frame(data,profiles[a['profile']],a,tick,4,light,False).save(path,optimize=True)
  print(json.dumps({'exported':a['key'],'video':bool(a.get('defaultVideo'))}),flush=True)
 write(OUT/'export-report.json',{'records':records,'decoded_videos':decoded,'all_canvas_actions_complete':True,'only_enemy19_exported':True})
def merge(data):
 paths=shared.source_paths();before=shared.snapshot_shared();live=json.loads(paths[1].read_text());assert shared.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=shared.merge_rows(live[field],data[field],own);assert[r for r in combined[field]if not own(r)]==[r for r in live[field]if not own(r)]
 added=[]
 for a in data['actions']:
  for key in a['effectIds']:
   if key in live['effects']:assert data['effects'][key]==live['effects'][key],key
   else:assert key.startswith('review-c19-summon-');combined['effects'][key]=data['effects'][key];added.append(key)
 assert all(combined['effects'][k]==v for k,v in live['effects'].items())
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);rows=[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in data['actions']];report['actions']=shared.merge_rows(report['actions'],rows,own)
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.summoner-',dir=p.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),p))
  assert shared.snapshot_shared()==before,'concurrent shared writer; retry latest merge'
  for temp,p in staged:os.replace(temp,p)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert json.loads(paths[1].read_text())==combined and shared.parse_js(paths[0])==combined and shared.sha(paths[3])==before['index.html']
 write(OUT/'merge-report.json',{'target_profiles':3,'target_actions':80,'all_unrelated_profiles_and_actions_unchanged':True,'all_existing_spell_effects_unchanged':True,'added_effects':sorted(set(added)),'index_default_unchanged':True,'runtime_integrated':False})
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args();data=build();v=verify(data);print(json.dumps({'actions':80,'checks':v['checks']}),flush=True)
 if args.export:export(data);data=build()
 if args.merge:merge(data)
if __name__=='__main__':main()
