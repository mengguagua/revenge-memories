#!/usr/bin/env python3
"""A single review-only sonic release; preserve the native 507-tick program."""
import argparse,ast,copy,contextlib,hashlib,io,json,os,subprocess,tempfile
from pathlib import Path
from types import ModuleType,SimpleNamespace
from PIL import Image,ImageChops,ImageDraw
import build_gallery as G
import export_gallery as E
import import_bone_wing_beast_v1 as A
import integrate_enemy_11_14_review as S
from import_knight_redraw_v3 import parts
ROOT=G.ROOT;REV='bone-wing-sonic-v2-20261024';OUT=ROOT/REV;SRC=OUT/'source';BASE=A.OUT;BUNDLE=BASE/'gallery_bundle.json'
ID='professions-class-5-enemy-battle--original_class_5_enemy_normal';PID='professions-class-5-enemy-battle';ASSETS=[]
FX_PREFIX='review-bone-wing-sonic-v2-'
FX_PAL=[tuple(bytes.fromhex(c))for c in['586884','7885a5','9ba5bf','bac7d9','d7dfe5']]
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(im,path,purpose):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);colors=sorted(set(im.getdata()));assert len(colors)<=256
 q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));lut={c:i for i,c in enumerate(colors)};q.putdata([lut[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes();q.save(p,optimize=True)
 ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose});return p.relative_to(ROOT).as_posix()
def author():
 b=read(BUNDLE);baseline=read(SRC/'baseline.json');a=next(a for a in b['actions']if a['id']==ID);p=next(p for p in b['profiles']if p['id']==PID);assert a['frames']==baseline['target_action']['frames']
 # Reuse the already-authored jaw as a delta matte, never replace the wings.
 closed=Image.open(ROOT/p['newFrames']['18']).convert('RGBA');opened=Image.new('RGBA',closed.size);opened.alpha_composite(Image.open(ROOT/p['newFrames']['50']).convert('RGBA'),(64,0));delta=ImageChops.difference(closed,opened);mask=Image.new('L',closed.size);mask.putdata([255 if any(v)else 0 for v in delta.getdata()]);bb=mask.getbbox();assert bb and bb[0]>=62 and bb[2]<=188 and bb[1]>=312 and bb[3]<=404
 slots={};jaw_records=[]
 for source in range(17,24):
  body=Image.open(ROOT/p['newFrames'][str(source)]).convert('RGBA');im=body.copy();im.paste(opened,(0,0),mask);bg=Image.new('RGBA',im.size);bg.alpha_composite(im,(-64,0));assert sum(v[3]>0 for v in im.getdata())==sum(v[3]>0 for v in bg.getdata());slot=51+source-17;slots[source]=slot;p['newFrames'][str(slot)]=save(bg,f'battle/frame-{slot:03}.png','复用已绘张颚，只替换头部差分；双翼／爪／躯干保持当前原姿势');jaw_records.append({'source_pose':source,'open_pose':slot,'jaw_delta_bbox':list(bb),'background_shift':[-64,0]})
 raw=Image.open(SRC/'sonic-master.png').convert('RGBA');assert raw.size==(1536,1024);effects={};fx=[]
 for i,height in enumerate([32,56,88,128,152,160]):
  cell=raw.crop((i%3*512,i//3*512,i%3*512+512,i//3*512+512));threshold=245 if i<5 else 180;valid={(x,y)for y in range(512)for x in range(512)if cell.getpixel((x,y))[3]>=threshold};groups=parts(valid);keep=set().union(*(g for g in groups if len(g)>=18));cut=Image.new('RGBA',cell.size)
  for xy in keep:
   v=cell.getpixel(xy);rgb=min(FX_PAL,key=lambda q:sum((a-b)**2 for a,b in zip(q,v[:3])));cut.putpixel(xy,(*rgb,255))
  box=cut.getbbox();assert box;cut=cut.crop(box);size=[max(1,round(cut.width*height/cut.height)),height];cut=cut.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,256));at=(16,128-height//2);canvas.alpha_composite(cut,at);assert sum(v[3]>0 for v in cut.getdata())==sum(v[3]>0 for v in canvas.getdata());eid=f'review-bone-wing-sonic-v2-{i}';path=save(canvas,f'effects/wave-{i}.png','低饱和蓝紫音波；去掉生成源图透明光晕，保留清楚的弧形压力波')
  effects[eid]={'path':path,'frame_size':[64,64],'anchor':[4,32],'frames':1,'flip_origin_offset':[0,0],'default_facing':'right'};fx.append(eid)
 revised=copy.deepcopy(a['frames'])
 for t,row in enumerate(revised):
  if 236<=t<=276:row['frame']=slots[row['frame']]
  if 243<=t<=274:
   k=t-243;phase=0 if k<4 else 1 if k<9 else 2 if k<14 else 3 if k<21 else 4 if k<27 else 5;row['effects']=[{'sprite':fx[phase],'position':[101+row['offset'][0]+48*k/31,123+row['offset'][1]],'flip':False}]
 a['revisedFrames']=revised;a['effectRevision']=REV;a['_reviewCloseCamera']={'offset':[-64,-112],'size':[224,192],'purpose':'Complete wings, jaw, sonic wave and dissipation remain inside close preview'};a['notes']=baseline['target_action']['notes']+' 音波V2：显示第237至277帧张颚，保留双翼原拍动；第244帧单次释放低饱和蓝紫音波，向前扩散并在第275帧后消散，第278帧闭嘴后按原程序转身回位。原507帧、原位移、原节奏及第244帧单次结算保持，不新增伤害事件。'
 p['links']=[v for v in p['links']if v.get('href')!=REV+'/README.md']+[{'label':'普通攻击张颚／音波V2','href':REV+'/README.md'}];b.setdefault('effects',{}).update(effects);write(BUNDLE,b)
 write(OUT/'effect-contract.json',{'revision':REV,'target_action':ID,'mouth_open_ticks':[236,276],'sonic_release_tick':243,'display_contact_frame':244,'sonic_visible_ticks':[243,274],'clear_tick':275,'mouth_close_tick':277,'turn_back_tick':279,'single_sonic_event':True,'three_pressure_bands_one_pulse':True,'total_ticks':507,'native_fps':60.0988,'head_delta_bounds':list(bb),'jaw_poses':jaw_records,'effect_palette':[bytes(c).hex()for c in FX_PAL],'runtime_integrated':False});write(OUT/'asset-manifest.json',{'assets':ASSETS,'generator':'built-in image_gen; technical alpha extraction, low-saturation palette, pixel registration, existing jaw-delta compositing','prompt':'source/sonic-prompt.txt','runtime_integrated':False})
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
 Scope().visit(fn);assert removed.count('write_text')==3;m=ModuleType('scoped_bone_sonic_builder');m.__file__=str(path);m.OWN_BUNDLE=BUNDLE.resolve();exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),m.__dict__);before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=m.build()
 assert S.snapshot_shared()==before;write(OUT/'gallery-data.json',data);return data
def verify(d):
 base=read(SRC/'baseline.json');a=next(a for a in d['actions']if a['id']==ID);p=next(p for p in d['profiles']if p['id']==PID);c=read(OUT/'effect-contract.json');assert a['frames']==base['target_action']['frames']and a['contactTick']==243 and a['fps']==60.0988 and len(a['revisedFrames'])==507 and a['ready'];checks=5;errors=[]
 for k,h in base['body_hashes'].items():assert sha(ROOT/p['newFrames'][k])==h;checks+=1
 for row in c['jaw_poses']:
  old=Image.open(ROOT/p['newFrames'][str(row['source_pose'])]).convert('RGBA');new=Image.new('RGBA',old.size);new.alpha_composite(Image.open(ROOT/p['newFrames'][str(row['open_pose'])]).convert('RGBA'),(64,0));diff=ImageChops.difference(old,new);diff.paste((0,0,0,0),tuple(c['head_delta_bounds']));assert not any(ch.getbbox()for ch in diff.split());checks+=1
 for tick,(old,new)in enumerate(zip(a['frames'],a['revisedFrames'])):
  assert{k:v for k,v in old.items()if k not in['frame','effects']}=={k:v for k,v in new.items()if k not in['frame','effects']};checks+=1
  if not 236<=tick<=276:assert new['frame']==old['frame'];checks+=1
  assert len(new['effects'])==(1 if 243<=tick<=274 else 0);checks+=1
  for revised,row in[(False,old),(True,new)]:
   f=row['frame'];flip=True!=row['flip'];off=row['offset'];at=[a['origin'][i]+off[i]-p['anchor'][i]for i in(0,1)]
   if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in(0,1)]
   im=E.load(p['newFrames'][str(f)])if revised else E.body_image(p['sourceAtlas'],f,tuple(p['sourceFrameSize']),p['sourceColumns']);box=S.V.box_at(im,at,p['sourceFrameSize'],flip);cam=a['closeCamera'];view=[a['origin'][i]+off[i]+cam['offset'][i]for i in(0,1)]+cam['size'];checks+=2
   for mode,v in[('full',a['viewport']),('close',view)]:
    if S.V.outside(box,v):errors.append({'tick':tick,'kind':'body','mode':mode,'bounds':box})
   for fx in row['effects']:
    meta=d['effects'][fx['sprite']];im=E.load(meta['path']);point=[fx['position'][i]-meta['anchor'][i]for i in(0,1)];box=S.V.box_at(im,point,meta['frame_size'],False);checks+=2
    for mode,v in[('full',a['viewport']),('close',view)]:
     if S.V.outside(box,v):errors.append({'tick':tick,'kind':'sonic','mode':mode,'bounds':box})
 for file,h in base['runtime_hashes'].items():assert sha(ROOT.parents[1]/file)==h;checks+=1
 assert not d['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'target_action':ID,'native_all_rows_unchanged':True,'native_507_ticks_and_contact_244_unchanged':True,'only_jaw_delta_changes_body_pixels':True,'all_previous_body_frames_unchanged':True,'single_sonic_release':True,'no_additional_damage_events':True,'source_reference_unchanged':True,'runtime_files_unchanged':True,'errors':errors};write(OUT/'verification.json',report);assert not errors,errors[:3];return report
def previews(d):
 p=next(p for p in d['profiles']if p['id']==PID);a=next(a for a in d['actions']if a['id']==ID);ticks=[235,236,242,243,247,252,257,260,264,269,274,277]
 for light in[False,True]:
  out=Image.new('RGB',(4*480,3*400+52),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(out);fg=(35,51,74)if light else(235,243,242);dr.text((out.width/2,26),'骸翼兽 · 张颚 → 单次音波扩散 → 消散闭嘴 → 原节奏回位',font=E.font(21),anchor='mm',fill=fg)
  for i,t in enumerate(ticks):
   panel=E.render_panel(d,p,a,a['revisedFrames'][t],True,2,light,True);panel.thumbnail((472,344),Image.Resampling.NEAREST);x=i%4*480+(480-panel.width)//2;y=52+i//4*400;out.paste(panel,(x,y));dr.text((i%4*480+240,y+374),'第 '+str(t+1)+' 帧',font=E.font(17),anchor='mm',fill=fg)
  out.save(OUT/('phases-light.png'if light else'phases-dark.png'),optimize=True)
def export(d):
 a=next(a for a in d['actions']if a['id']==ID);records=[]
 for close in[False,True]:records.append(E.export(d,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False)))
 probes=[]
 for close in[False,True]:
  p=ROOT/'demos/videos'/(ID+('--close'if close else'')+'.mp4');v=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(p)]))['streams'][0];assert int(v['nb_read_frames'])==507 and abs(float(v['duration'])-507/60.0988)<.017;probes.append({'path':p.relative_to(ROOT).as_posix(),**v})
 write(OUT/'export-report.json',{'exports':records,'decoded_videos':probes,'scope':'Only the normal attack full/close video and stills'})
def merge(d):
 paths=S.source_paths();before=S.snapshot_shared();live=read(paths[1]);assert S.parse_js(paths[0])==live;combined=copy.deepcopy(live);mine=next(a for a in d['actions']if a['id']==ID);profile=next(p for p in d['profiles']if p['id']==PID);combined['actions']=S.merge_rows(live['actions'],[mine],lambda r:r['id']==ID);combined['profiles']=S.merge_rows(live['profiles'],[profile],lambda r:r['id']==PID)
 assert[a for a in combined['actions']if a['id']!=ID]==[a for a in live['actions']if a['id']!=ID];assert[p for p in combined['profiles']if p['id']!=PID]==[p for p in live['profiles']if p['id']!=PID]
 for k,v in d['effects'].items():
  if k.startswith(FX_PREFIX):combined['effects'][k]=v
 assert{k:v for k,v in combined['effects'].items()if not k.startswith(FX_PREFIX)}=={k:v for k,v in live['effects'].items()if not k.startswith(FX_PREFIX)};combined['builtAt']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();report=read(paths[2]);report['builtAt']=combined['builtAt'];report['actions']=S.merge_rows(report['actions'],[{k:mine[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}],lambda r:r['id']==ID);payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.bone-sonic-',dir=p.parent);os.close(fd);tmp=Path(name);tmp.write_text(text);staged.append((tmp,p))
  assert S.snapshot_shared()==before,'Concurrent gallery writer; retry merge against latest files'
  for temp,p in staged:os.replace(temp,p)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert sha(paths[3])==before['index.html'];write(OUT/'merge-report.json',{'only_action_changed':ID,'only_profile_extended':PID,'all_other_actions_profiles_effects_preserved':True,'runtime_integrated':False})
def main():
 p=argparse.ArgumentParser();p.add_argument('--author',action='store_true');p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args()
 if args.author:author()
 d=build();print(json.dumps(verify(d),ensure_ascii=False),flush=True);previews(d)
 if args.export:export(d);d=build()
 if args.merge:merge(d)
if __name__=='__main__':main()
