#!/usr/bin/env python3
"""Scoped publish for the authored Vucub divine-body review bundle."""
import argparse,ast,copy,contextlib,io,json,os,tempfile
from datetime import datetime,timezone
from types import ModuleType
from PIL import Image,ImageChops,ImageDraw,ImageOps
import import_divine_body_v1 as A
import integrate_enemy_11_14_review as S
ROOT=A.ROOT;OUT=A.OUT;PREFIX='professions-class-21-enemy-'
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
 module=ModuleType('scoped_divine_body_builder');module.__file__=str(path);module.OWN_BUNDLE=(OUT/'gallery_bundle.json').resolve();exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),module.__dict__)
 before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert S.snapshot_shared()==before and len(data['profiles'])==3 and len(data['actions'])==17
 assert all(own(r)for r in data['profiles']+data['actions']);A.write(OUT/'gallery-data.json',data);return data
def verify(d):
 checks=0;errors=[];ps={p['id']:p for p in d['profiles']}
 for p in ps.values():
  for path in p['newFrames'].values():
   im=Image.open(ROOT/path).convert('RGBA');assert list(im.size)==p['outputFrameSize']and im.getbbox();assert{px[3]for px in im.getdata()}<={0,255};assert{px[:3]for px in im.getdata()if px[3]}<=set(A.PAL);checks+=1
 for r in json.loads((OUT/'fixed-core-contract.json').read_text())['walk']:
  ims=[Image.open(OUT/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA')for i in r['slots']];mask=Image.new('L',ims[0].size);ImageDraw.Draw(mask).polygon(r['mask_polygon'],fill=255);diff=ImageChops.difference(ims[0],ims[1]);assert all(not ImageChops.multiply(c,mask).getbbox()for c in diff.split());checks+=1
 for a,b in[(2,6),(3,7)]:assert ImageOps.mirror(Image.open(OUT/'tactical-walk'/f'frame-{a:03}.png').convert('RGBA')).tobytes()==Image.open(OUT/'tactical-walk'/f'frame-{b:03}.png').convert('RGBA').tobytes();checks+=1
 idle=[Image.open(OUT/'tactical-idle'/f'frame-{i:03}.png').convert('RGBA')for i in[0,1,2]];assert idle[0].tobytes()==idle[1].tobytes();assert idle[0].crop((26,0,70,31)).tobytes()==idle[2].crop((26,0,70,31)).tobytes() and idle[0].crop((35,38,61,63)).tobytes()==idle[2].crop((35,38,61,63)).tobytes();assert idle[0].crop((0,64,96,96)).tobytes()==idle[2].crop((0,64,96,96)).tobytes();checks+=3
 audit=json.loads((A.SRC/'native-audit.json').read_text());evidence=[]
 for r in audit['walk']['frame_mapping']:
  im=Image.open(A.SRC/f'native-walk-{r["source_slot"]:03}.png').convert('RGBA');actual=__import__('hashlib').sha256(im.tobytes()).hexdigest();assert actual==r['rgba_sha256'];evidence.append({'slot':r['source_slot'],'rgba_sha256':actual,'native_cpu_match':True});checks+=1
 A.write(OUT/'source-walk-verification.json',{'passed':True,'source_chr':28,'frames':evidence,'native_phase_ticks':16,'native_counterpart':'Duma generic map phase reference only; Vucub bird is custom','native_frozen_sources_unchanged':True})
 for a in d['actions']:
  assert a['ready'];p=ps[a['profile']];fw,fh=p['sourceFrameSize'];atlas=S.V.image(p['sourceAtlas'])
  if a['kind']=='attack':
   assert len(a['frames'])==54 and a['fps']==50 and a['contactTick']==34
   assert [r['frame']for r in a['frames']]==[4 if a['key']=='wing-beak'else 1]*20+[5 if a['key']=='wing-beak'else 2]*15+[3]*19
   assert all(len(r['effects'])<=1 for r in a['frames']);checks+=4
  if a['key']=='idle-cycle':assert len(a['frames'])==88 and[r['frame']for r in a['frames']]==[k for _ in range(2)for k,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
  if a['kind']=='map_walk':assert len(a['frames'])==96 and all(r['offset']==[0,0]for r in a['frames']);checks+=1
  for tick,r in enumerate(a['frames']):
   f=r['frame'];off=r['offset'];at=[a['origin'][i]+off[i]-p['anchor'][i]for i in(0,1)];flip=(p['context']=='battle')!=r['flip'];x=f%p['sourceColumns']*fw;y=f//p['sourceColumns']*fh
   for kind,im in[('reference',atlas.crop((x,y,x+fw,y+fh))),('redraw',S.V.image(p['newFrames'][str(f)]))]:
    box=S.V.box_at(im,at,[fw,fh],flip);checks+=1
    if S.V.outside(box,a.get('viewport',d['viewport'])):errors.append({'action':a['id'],'tick':tick,'kind':kind,'bounds':box})
   for e in r['effects']:
    meta=d['effects'][e['sprite']];point=[e['position'][i]-meta['anchor'][i]for i in(0,1)];box=S.V.box_at(S.V.image(meta['path']),point,meta['frame_size'],e['flip']);checks+=1
    if S.V.outside(box,a['viewport']):errors.append({'action':a['id'],'tick':tick,'kind':'effect','bounds':box})
 baseline=json.loads((A.SRC/'runtime-baseline.json').read_text());assert all(S.sha(ROOT.parents[1]/p)==h for p,h in baseline.items());checks+=len(baseline)
 errors+=d['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'profiles':3,'actions':17,'map_center_drift_pixels':0,'battle_uniform_source_scale':.90,'native_map_timing_exact':True,'current_innate_attack_contract_exact':True,'each_attack_resolves_once_at_tick':34,'native_bird_counterpart':False,'runtime_files_unchanged':True,'browser_visual_inspection':'not performed; offline compositing and encoded-video decoding only','user_acceptance':'pending','errors':errors};A.write(OUT/'verification.json',report);assert not errors,errors[:4];return report
def export(d):
 old=S.OUT;S.OUT=OUT
 try:S.export_local(d,'all')
 finally:S.OUT=old
 report=json.loads((OUT/'export-report.json').read_text());report['scope']='Only 17 divine-body actions and three battle close-ups; no unrelated media written';A.write(OUT/'export-report.json',report)
def merge(d):
 paths=S.source_paths();before=S.snapshot_shared();live=json.loads(paths[1].read_text());assert S.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=S.merge_rows(live[field],d[field],own);assert[r for r in combined[field]if not own(r)]==[r for r in live[field]if not own(r)]
 key='review-divine-body-sun-orb-v1';combined['effects'][key]=d['effects'][key];assert{k:v for k,v in combined['effects'].items()if k!=key}=={k:v for k,v in live['effects'].items()if k!=key}
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);report['actions']=S.merge_rows(report['actions'],[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in d['actions']],own)
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.divine-body-',dir=p.parent);os.close(fd);tmp=__import__('pathlib').Path(name);tmp.write_text(text);staged.append((tmp,p))
  assert S.snapshot_shared()==before,'Concurrent gallery writer; retry merge against latest files'
  for temp,p in staged:os.replace(temp,p)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert S.sha(paths[3])==before['index.html'];A.write(OUT/'merge-report.json',{'target_profiles':3,'target_actions':17,'all_unrelated_profiles_actions_effects_unchanged':True,'runtime_integrated':False,'summary':combined['summary']})
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args();d=build();r=verify(d);print(json.dumps(r,ensure_ascii=False),flush=True)
 if args.export:export(d);d=build()
 if args.merge:merge(d)
if __name__=='__main__':main()
