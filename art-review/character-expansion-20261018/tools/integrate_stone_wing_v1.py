#!/usr/bin/env python3
"""Scoped stone-wing bundle build, verification/export and append-only merge."""
import argparse,ast,contextlib,copy,io,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
from types import ModuleType
from PIL import Image,ImageOps
import import_stone_wing_v1 as A
import integrate_enemy_11_14_review as S
import build_gallery as G
ROOT=A.ROOT;OUT=A.OUT;PREFIX='professions-class-3-enemy-'
def own(x):return str(x.get('profile',x.get('id',''))).startswith(PREFIX)
def build():
 path=ROOT/'tools/build_gallery.py';tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='build');removed=[]
 class Scope(ast.NodeTransformer):
  def visit_For(self,n):
   n=self.generic_visit(n)
   if isinstance(n.target,ast.Name)and n.target.id=='mapping_path':n.body.insert(0,ast.Continue())
   if isinstance(n.target,ast.Name)and n.target.id=='bundle_path':n.body.insert(0,ast.parse('if bundle_path.resolve() != OWN_BUNDLE: continue').body[0])
   return n
  def visit_Expr(self,n):
   if isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr in['write_text','mkdir']:removed.append(n.value.func.attr);return None
   return self.generic_visit(n)
 Scope().visit(fn);assert removed.count('write_text')==3
 m=ModuleType('scoped_stone_wing_builder');m.__file__=str(path);m.OWN_BUNDLE=(OUT/'gallery_bundle.json').resolve();exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),m.__dict__);before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):d=m.build()
 assert S.snapshot_shared()==before and len(d['profiles'])==3 and len(d['actions'])==18 and all(own(x)for x in d['profiles']+d['actions']);A.write(OUT/'gallery-data.json',d);return d
def verify(d):
 ps={p['id']:p for p in d['profiles']};checks=0;errors=[];audit=json.loads((A.SRC/'native-audit.json').read_text());native=audit['variant'];a=next(a for a in d['actions']if a['key']=='original_class_3_enemy_normal');assert a['frames']==[G.pack_frame(r)for r in native['frames']]and len(a['frames'])==208 and a['contactTick']==103 and a['fps']==60.0988;checks+=4
 atlas=Image.open(ROOT/audit['body']['path']).convert('RGBA');ref=Image.open(OUT/'source/battle-reference-atlas.png').convert('RGBA')
 for i in range(36):
  box=(i%16*80,i//16*96,(i%16+1)*80,(i//16+1)*96);assert atlas.crop(box).tobytes()==ref.crop(box).tobytes();checks+=1
 walk=json.loads((A.SRC/'native-walk-record.json').read_text());proof=[]
 for r in walk['frame_mapping']:
  im=Image.open(A.SRC/f'native-walk-{r["source_slot"]:03}.png').convert('RGBA');actual=__import__('hashlib').sha256(im.tobytes()).hexdigest();assert actual==r['rgba_sha256'];proof.append({'slot':r['source_slot'],'rgba_sha256':actual,'native_cpu_match':True});checks+=1
 A.write(OUT/'source-walk-verification.json',{'passed':True,'source_chr':28,'native_cpu_records':proof,'original_two_phases_ticks':16,'anatomy_retarget':'Original biped to established quadruped; wing-phase intent retained'})
 for p in d['profiles']:
  assert p['className']=='石翼兽'and p['side']=='enemy'and not p['frameErrors']
  for path in p['newFrames'].values():
   im=S.V.image(path);assert list(im.size)==p['outputFrameSize']and im.getbbox();assert{px[:3]for px in im.getdata()if px[3]}<=set(A.PAL)and{px[3]for px in im.getdata()}<={0,255};checks+=1
 for a in d['actions']:
  assert a['ready']and not a.get('revisedFrames')and not a.get('reviewTailFrames');p=ps[a['profile']];w,h=p['sourceFrameSize'];atlas=S.V.image(p['sourceAtlas'])
  if a['key']=='idle-cycle':assert len(a['frames'])==88 and[r['frame']for r in a['frames']]==[k for _ in range(2)for k,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
  if a['kind']=='map_walk':assert len(a['frames'])==96 and all(r['offset']==[0,0]for r in a['frames']);checks+=1
  if a['key']in['stone-claw','stone-spit','stone-spit-far']:
   melee=a['key']=='stone-claw';prep=12 if melee else 20;contact=26 if melee else 34;assert a['fps']==50 and a['contactTick']==contact and len(a['frames'])==contact+20
   assert[r['frame']for r in a['frames']]==[37 if melee else 40]*prep+[38 if melee else 41]*15+[39]*19
   assert all(len(r['effects'])<=1 for r in a['frames']);assert all(not r['effects']for r in a['frames'][:prep]);checks+=5
   if not melee:assert all(r['effects'][0]['sprite']=='review-stone-wing-fx-0'for r in a['frames'][prep:contact])
  for t,r in enumerate(a['frames']):
   f=r['frame'];off=r['offset'];at=[a['origin'][i]+off[i]-p['anchor'][i]for i in[0,1]];flip=(p['context']=='battle')!=r['flip']
   if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in[0,1]]
   x=f%p['sourceColumns']*w;y=f//p['sourceColumns']*h
   for track,im in[('reference',atlas.crop((x,y,x+w,y+h))),('redraw',S.V.image(p['newFrames'][str(f)]))]:
    box=S.V.box_at(im,at,[w,h],flip);checks+=1
    if S.V.outside(box,a.get('viewport',d['viewport'])):errors.append({'action':a['id'],'tick':t,'track':track,'bounds':box})
    if a.get('closeCamera'):
     c=a['closeCamera'];view=[a['origin'][i]+off[i]+c['offset'][i]for i in[0,1]]+c['size'];checks+=1
     if S.V.outside(box,view):errors.append({'action':a['id'],'tick':t,'track':track,'close_bounds':box})
   for e in r['effects']:
    meta=d['effects'][e['sprite']];point=[e['position'][i]-meta['anchor'][i]for i in[0,1]];box=S.V.box_at(S.V.image(meta['path']),point,meta['frame_size'],e['flip']);checks+=1
    if S.V.outside(box,a['viewport']):errors.append({'action':a['id'],'tick':t,'effect':e['sprite'],'bounds':box})
    if a.get('closeCamera'):
     c=a['closeCamera'];view=[a['origin'][i]+off[i]+c['offset'][i]for i in[0,1]]+c['size'];checks+=1
     if S.V.outside(box,view):errors.append({'action':a['id'],'tick':t,'effect':e['sprite'],'close_bounds':box})
 reg=json.loads((OUT/'asset-manifest.json').read_text())['registration'];landmarks=[]
 for prefix,ids in[('walk',[0,1]),('walk',[2,3]),('walk',[4,5]),('idle',[0,1,2])]:
  rows=[next(r for r in reg if r['label']==prefix+'-'+str(i))for i in ids];points=[r['registered_pivot']for r in rows];drift=[max(p[j]for p in points)-min(p[j]for p in points)for j in[0,1]];assert max(drift)<1;landmarks.append({'group':prefix,'slots':ids,'registered_landmarks':points,'drift_output_pixels':drift,'method':'whole pose fixed head landmark; no per-frame root offsets'})
 for a,b in[(2,6),(3,7)]:assert ImageOps.mirror(S.V.image(A.REV+f'/tactical-walk/frame-{a:03}.png')).tobytes()==S.V.image(A.REV+f'/tactical-walk/frame-{b:03}.png').tobytes();checks+=1
 base=json.loads((A.SRC/'runtime-baseline.json').read_text());assert all(S.sha(ROOT.parents[1]/p)==h for p,h in base.items());errors+=d['validation']['structuralIssues'];v={'passed':not errors,'checks':checks,'profiles':3,'actions':18,'native_attack_frames':208,'native_attack_contact_tick':103,'native_attack_rows_exact':True,'innate_attacks':{'1001':{'frames':46,'contact_tick':26,'fps':50,'resolution_count':1},'1002':{'frames':54,'contact_tick':34,'fps':50,'projectiles':1,'resolution_count':1}},'map_landmarks':landmarks,'source_native_chr':28,'runtime_files_unchanged':True,'visual_acceptance':'pending offline review and user acceptance','errors':errors};A.write(OUT/'verification.json',v);assert not errors,errors[:5];return v
def export(d):
 old=S.OUT;S.OUT=OUT
 try:S.export_local(d,'all')
 finally:S.OUT=old
 r=json.loads((OUT/'export-report.json').read_text());r['scope']='Stone-wing only: 18 action videos and four attack close-ups; no unrelated media';A.write(OUT/'export-report.json',r)
def merge(d):
 paths=S.source_paths();before=S.snapshot_shared();live=json.loads(paths[1].read_text());assert S.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for f in['profiles','actions']:
  combined[f]=S.merge_rows(live[f],d[f],own);assert[x for x in combined[f]if not own(x)]==[x for x in live[f]if not own(x)]
 keys={k for k in d['effects']if k.startswith('review-stone-wing-')}
 for k in keys:
  assert k not in live['effects']or live['effects'][k]==d['effects'][k];combined['effects'][k]=d['effects'][k]
 assert{k:v for k,v in combined['effects'].items()if k not in keys}=={k:v for k,v in live['effects'].items()if k not in keys}
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);report['actions']=S.merge_rows(report['actions'],[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in d['actions']],own);payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.stone-wing-',dir=p.parent);os.close(fd);tmp=Path(name);tmp.write_text(text);staged.append((tmp,p))
  assert S.snapshot_shared()==before,'Concurrent writer; retry with latest data'
  for tmp,p in staged:os.replace(tmp,p)
 finally:
  for tmp,_ in staged:tmp.unlink(missing_ok=True)
 assert S.sha(paths[3])==before['index.html']and S.parse_js(paths[0])==combined;A.write(OUT/'merge-report.json',{'target_profiles':3,'target_actions':18,'latest_live_unrelated_rows_effects_preserved':True,'runtime_integrated':False,'summary':combined['summary']})
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');a=p.parse_args();d=build();v=verify(d);print(json.dumps({'checks':v['checks'],'profiles':3,'actions':18}),flush=True)
 if a.export:export(d);d=build()
 if a.merge:merge(d)
if __name__=='__main__':main()
