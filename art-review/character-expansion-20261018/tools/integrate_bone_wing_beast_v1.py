#!/usr/bin/env python3
"""Scoped original bone-wing beast audit and publish."""
import argparse,ast,copy,contextlib,io,json,os,tempfile
from datetime import datetime,timezone
from types import ModuleType
from PIL import Image,ImageChops,ImageDraw,ImageOps
import import_bone_wing_beast_v1 as A
import build_gallery as G
import integrate_enemy_11_14_review as S
ROOT=A.ROOT;OUT=A.OUT;PREFIX='professions-class-5-enemy-'
def own(r):return str(r.get('profile',r.get('id',''))).startswith(PREFIX)
def build():
 path=ROOT/'tools/build_gallery.py';tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='build');removed=[]
 class Scope(ast.NodeTransformer):
  def visit_For(self,n):
   n=self.generic_visit(n)
   if isinstance(n.target,ast.Name)and n.target.id=='mapping_path':n.body.insert(0,ast.Continue())
   if isinstance(n.target,ast.Name)and n.target.id=='bundle_path':n.body.insert(0,ast.parse("if bundle_path.resolve() != OWN_BUNDLE: continue").body[0])
   return n
  def visit_Expr(self,n):
   if isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr in['write_text','mkdir']:removed.append(n.value.func.attr);return None
   return self.generic_visit(n)
 Scope().visit(fn);assert removed.count('write_text')==3
 module=ModuleType('scoped_bone_wing_builder');module.__file__=str(path);module.OWN_BUNDLE=(OUT/'gallery_bundle.json').resolve();exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),module.__dict__)
 before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert S.snapshot_shared()==before and len(data['profiles'])==3 and len(data['actions'])==16
 assert all(own(r)for r in data['profiles']+data['actions']);A.write(OUT/'gallery-data.json',data);return data
def verify(d):
 baseline=__import__('json').loads((A.SRC/'baseline.json').read_text());audit=json.loads((A.SRC/'native-audit.json').read_text());checks=0;errors=[];ps={p['id']:p for p in d['profiles']}
 for p in ps.values():
  for path in p['newFrames'].values():
   im=Image.open(ROOT/path).convert('RGBA');assert list(im.size)==p['outputFrameSize']and im.getbbox();assert{px[3]for px in im.getdata()}<={0,255};assert{px[:3]for px in im.getdata()if px[3]}<=set(A.PAL);checks+=1
 core=json.loads((OUT/'fixed-core-contract.json').read_text())
 for r in core['walk']+[core['idle']]:
  kind='tactical-idle'if len(r['slots'])==3 else'tactical-walk';ims=[Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')for i in r['slots']];mask=A.core_mask(ims[0].size,r['polygons'])
  for im in ims[1:]:
   diff=ImageChops.difference(ims[0],im);assert all(not ImageChops.multiply(c,mask).getbbox()for c in diff.split());checks+=1
 for a,b in[(2,6),(3,7)]:assert ImageOps.mirror(Image.open(OUT/'tactical-walk'/f'frame-{a:03}.png').convert('RGBA')).tobytes()==Image.open(OUT/'tactical-walk'/f'frame-{b:03}.png').convert('RGBA').tobytes();checks+=1
 im=Image.open(OUT/'battle/frame-016.png').convert('RGBA');bg=Image.new('RGBA',im.size);bg.alpha_composite(im,(-64,0));assert bg.tobytes()==Image.open(OUT/'battle/frame-041.png').convert('RGBA').tobytes()==Image.open(OUT/'battle/frame-048.png').convert('RGBA').tobytes();checks+=1
 evidence=[]
 for r in audit['walk']['frame_mapping']:
  im=Image.open(A.SRC/f'native-walk-{r["source_slot"]:03}.png').convert('RGBA');actual=__import__('hashlib').sha256(im.tobytes()).hexdigest();assert actual==r['rgba_sha256'];evidence.append({'slot':r['source_slot'],'rgba_sha256':actual,'native_cpu_match':True});checks+=1
 A.write(OUT/'source-walk-verification.json',{'passed':True,'source_chr':28,'frames':evidence,'phase_ticks':16,'native_frozen_sources_unchanged':all(S.sha(ROOT/p)==audit['inputs_sha256'][k]for k,p in audit['inputs'].items())})
 for a in d['actions']:
  assert a['ready'];p=ps[a['profile']];fw,fh=p['sourceFrameSize'];atlas=S.V.image(p['sourceAtlas'])
  if a['key']=='original_class_5_enemy_normal':assert a['frames']==[G.pack_frame(r)for r in audit['variant']['frames']]and len(a['frames'])==507 and a['contactTick']==243 and not a.get('revisedFrames');checks+=4
  if a['key'].startswith('innate-'):
   bite=a['key']=='innate-bone-bite';assert a['fps']==50 and len(a['frames'])==(58 if bite else 54)and a['contactTick']==(38 if bite else 34);assert len(a['revisedFrames'])==len(a['frames']);checks+=3
   for tick,(old,new)in enumerate(zip(a['frames'],a['revisedFrames'])):
    skip=['frame']if bite else['frame','effects'];assert{k:v for k,v in old.items()if k not in skip}=={k:v for k,v in new.items()if k not in skip};checks+=1
    if not bite:
     assert len(old['effects'])==len(new['effects'])
     for ref,redraw in zip(old['effects'],new['effects']):
      assert{k:v for k,v in ref.items()if k!='position'}=={k:v for k,v in redraw.items()if k!='position'};u=(tick-20)/14;assert redraw['position']==[101+97*u,123-23*u];checks+=1
  if a['key']=='idle-cycle':assert len(a['frames'])==88 and[r['frame']for r in a['frames']]==[k for _ in range(2)for k,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)];checks+=1
  if a['kind']=='map_walk':assert len(a['frames'])==96 and all(r['offset']==[0,0]for r in a['frames']);checks+=1
  for track,rows in [('reference',a['frames']),('redraw',a.get('revisedFrames',a['frames']))]:
   for tick,r in enumerate(rows):
    f=r['frame'];off=r['offset'];flip=(p['context']=='battle')!=r['flip'];at=[a['origin'][i]+off[i]-p['anchor'][i]for i in(0,1)];at[0]+=r.get('shake',0)
    if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in(0,1)]
    x=f%p['sourceColumns']*fw;y=f//p['sourceColumns']*fh;im=atlas.crop((x,y,x+fw,y+fh))if track=='reference'else S.V.image(p['newFrames'][str(f)]);box=S.V.box_at(im,at,[fw,fh],flip);checks+=1
    if S.V.outside(box,a.get('viewport',d['viewport'])):errors.append({'action':a['id'],'tick':tick,'track':track,'bounds':box})
    if a.get('closeCamera'):
     c=a['closeCamera'];view=[a['origin'][i]+off[i]+c['offset'][i]for i in(0,1)]+c['size'];checks+=1
     if S.V.outside(box,view):errors.append({'action':a['id'],'tick':tick,'track':track,'mode':'close','bounds':box})
    for e in r['effects']:
     meta=d['effects'][e['sprite']];point=[e['position'][i]-meta['anchor'][i]for i in(0,1)];box=S.V.box_at(S.V.image(meta['path']),point,meta['frame_size'],e['flip']);checks+=1
     if S.V.outside(box,a['viewport']):errors.append({'action':a['id'],'tick':tick,'kind':'effect','bounds':box})
     if a['key']=='innate-eroding-breath':
      c=a['closeCamera'];view=[a['origin'][i]+off[i]+c['offset'][i]for i in(0,1)]+c['size'];checks+=1
      if S.V.outside(box,view):errors.append({'action':a['id'],'tick':tick,'kind':'close-effect','bounds':box})
 assert all(S.sha(ROOT.parents[1]/p)==h for p,h in baseline['runtime_hashes'].items());checks+=len(baseline['runtime_hashes']);errors+=d['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'profiles':3,'actions':16,'fixed_map_core_drift_pixels':0,'native_attack_ticks':507,'native_contact_tick':243,'native_display_contact_frame':244,'native_all_actor_rows_exact':True,'native_map_timing_exact':True,'current_innate_bite':{'fps':50,'ticks':58,'contact':38},'current_innate_breath':{'fps':50,'ticks':54,'contact':34},'runtime_files_unchanged':True,'browser_visual_inspection':False,'user_acceptance':'pending','errors':errors};A.write(OUT/'verification.json',report);assert not errors,errors[:4];return report
def export(d):
 old=S.OUT;S.OUT=OUT
 try:S.export_local(d,'all')
 finally:S.OUT=old
 report=json.loads((OUT/'export-report.json').read_text());report['scope']='Only 16 bone-wing beast actions and three battle close-ups; no unrelated media written';A.write(OUT/'export-report.json',report)
def merge(d):
 paths=S.source_paths();before=S.snapshot_shared();live=json.loads(paths[1].read_text());assert S.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=S.merge_rows(live[field],d[field],own);assert[r for r in combined[field]if not own(r)]==[r for r in live[field]if not own(r)]
 key='review-bone-wing-eroding-breath-v1';combined['effects'][key]=d['effects'][key];assert{k:v for k,v in combined['effects'].items()if k!=key}=={k:v for k,v in live['effects'].items()if k!=key}
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);report['actions']=S.merge_rows(report['actions'],[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in d['actions']],own)
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.bone-wing-',dir=p.parent);os.close(fd);tmp=__import__('pathlib').Path(name);tmp.write_text(text);staged.append((tmp,p))
  assert S.snapshot_shared()==before,'Concurrent gallery writer; retry merge against latest files'
  for temp,p in staged:os.replace(temp,p)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert S.sha(paths[3])==before['index.html'];A.write(OUT/'merge-report.json',{'target_profiles':3,'target_actions':16,'all_unrelated_profiles_actions_effects_unchanged':True,'runtime_integrated':False,'summary':combined['summary']})
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args();d=build();r=verify(d);print(json.dumps(r,ensure_ascii=False),flush=True)
 if args.export:export(d);d=build()
 if args.merge:merge(d)
if __name__=='__main__':main()
