#!/usr/bin/env python3
"""Solar charge -> scarlet flight -> single impact. Review only."""
import argparse,ast,copy,contextlib,gzip,hashlib,io,json,math,os,subprocess,tempfile
from functools import lru_cache
from pathlib import Path
from types import ModuleType,SimpleNamespace
from PIL import Image,ImageDraw
import build_gallery as G
import export_gallery as E
import integrate_enemy_11_14_review as S
from import_knight_redraw_v3 import parts

ROOT=G.ROOT;REV='divine-sun-vfx-v2-20261024';OUT=ROOT/REV;SRC=OUT/'source';BASE=ROOT/'divine-body-complete-v1-20261024';BUNDLE=BASE/'gallery_bundle.json'
IDS={'professions-class-21-enemy-battle--sun-crown','professions-class-21-enemy-battle--sun-crown-far'}
HEX=['7e4542','994b44','ac594c','be7056','cb8b60','d4a36f','dfb881','e8cd9c','f0dcba','f5e7ce']
GOLD=['97754e','ae8959','c49d68','d5b47f','e5c997','f0dcba','f5e7ce']
PAL=[tuple(bytes.fromhex(x))for x in HEX];GOLDPAL=[tuple(bytes.fromhex(x))for x in GOLD]
ASSETS=[];CELL_STATS=[]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@lru_cache(None)
def nearest(rgb,gold=False):return min(GOLDPAL if gold else PAL,key=lambda q:sum((a-b)**2 for a,b in zip(rgb,q)))
def clean(im):
 # A hard alpha contour and removal of isolated dust preserve deliberate rays
 # while preventing noisy spray from crossing the transparent cell gutters.
 valid={(x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]>=200};groups=parts(valid);kept=set().union(*(g for g in groups if len(g)>=20));out=Image.new('RGBA',im.size)
 for xy in kept:out.putpixel(xy,im.getpixel(xy)[:3]+(255,))
 return out
def cell(i):
 im=Image.open(SRC/'muted-master.png').convert('RGBA');row=i//4;col=i%4;xs=([0,315,630,930,1261]if row==1 else[0,315,610,948,1261]if row==2 else[0,315,630,945,1261]);ys=[0,350,575,915,1247];box=(xs[col],ys[row],xs[col+1],ys[row+1]);cut=clean(im.crop(box));bb=cut.getbbox();assert bb;cut=cut.crop(bb)
 # Align the actual bright core, not the changing outer corona or flame tail.
 if i<4 or 8<=i<=10:
  roi=(cut.width*.28,cut.height*.25,cut.width*.72,cut.height*.75)
 elif 4<=i<8:roi=(cut.width*.72,0,cut.width,cut.height)
 else:roi=None
 pts=[]
 if roi:
  for y in range(int(roi[1]),int(roi[3])):
   for x in range(int(roi[0]),int(roi[2])):
    p=cut.getpixel((x,y))
    if p[3]and min(p[:3])>190:pts.append((x+.5,y+.5))
 center=[sum(p[k]for p in pts)/len(pts)for k in(0,1)]if pts else[cut.width/2,cut.height/2]
 CELL_STATS.append({'source_cel':i,'extraction_region':box,'alpha_bounds':bb,'core_center':center,'complete_source_pixels':sum(p[3]>0 for p in cut.getdata())})
 return cut,center
def save(im,name,purpose):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA':
  colors=sorted(set(im.getdata()));assert len(colors)<=256;q=Image.new('P',im.size);q.putpalette([x for c in colors for x in c[:3]]+[0]*(768-len(colors)*3));lut={c:i for i,c in enumerate(colors)};q.putdata([lut[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors)
  assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True);rec={'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose};ASSETS.append(rec);return rec['path']
def make(cel,width,phase,fade=1,warm=0):
 cut,center=cel;ratio=width*4/cut.width;size=(round(cut.width*ratio),max(1,round(cut.height*ratio)));im=cut.resize(size,Image.Resampling.NEAREST)
 out=Image.new('RGBA',im.size);data=[]
 for p in im.getdata():
  if not p[3]:data.append((0,0,0,0));continue
  if phase=='charge':
   g=nearest(p[:3],True);red=nearest(p[:3]);rgb=tuple(round(g[k]*(1-warm)+red[k]*warm)for k in(0,1,2))
  else:rgb=nearest(p[:3])
  data.append((*rgb,round(255*fade)))
 out.putdata(data);canvas=Image.new('RGBA',(384,256)if phase=='flight'else(384,384)if phase=='impact'else(256,256));anchor=(256,128)if phase=='flight'else(192,192)if phase=='impact'else(128,128);at=(round(anchor[0]-center[0]*size[0]/cut.width),round(anchor[1]-center[1]*size[1]/cut.height));canvas.alpha_composite(out,at)
 assert sum(p[3]>0 for p in out.getdata())==sum(p[3]>0 for p in canvas.getdata()),('cropped VFX',phase,width,at,size)
 return canvas,{'frame_size':[canvas.width/4,canvas.height/4],'anchor':[x/4 for x in anchor],'frames':1,'flip_origin_offset':[0,0],'default_facing':'right'}
def author():
 cells=[cell(i)for i in range(16)];effects={};records=[];frames={}
 def add(key,i,width,phase,fade=1,warm=0):
  im,meta=make(cells[i],width,phase,fade,warm);eid='review-divine-sun-v2-'+key;meta['path']=save(im,'effects/'+key+'.png',phase+' authored VFX');effects[eid]=meta;frames[key]=im;records.append({'key':key,'sprite':eid,'source_cel':i,'width_logical':width,'phase':phase,'fade':fade,'warm_transition':warm,'core_anchor':meta['anchor']});return eid
 widths=[6,7,8,9,10,12,13,14,16,18,20,22,24,26,28,30,32,34,35,36]
 charge=[add(f'charge-{t:02}',min(3,t//5),w,'charge',warm=max(0,(t-15)/4)*.55)for t,w in enumerate(widths)]
 flight=[add(f'flight-{i}',4+i,44,'flight')for i in range(4)]
 explosion_spec=[(8,24,1),(8,34,1),(9,46,1),(9,58,1),(10,66,1),(10,70,1),(11,72,1),(11,72,1),(12,74,1),(12,74,1),(13,76,1),(13,76,1),(14,78,1),(14,78,.95),(15,80,.9),(15,80,.75),(15,82,.55),(15,82,.35),(15,82,.18)]
 impact=[add(f'impact-{t:02}',i,w,'impact',fade=fade)for t,(i,w,fade)in enumerate(explosion_spec)]
 baseline=json.loads((SRC/'baseline.json').read_text());bundle=json.loads(BUNDLE.read_text());before={a['id']:copy.deepcopy(a)for a in bundle['actions']if a['id']in IDS}
 for a in bundle['actions']:
  if a['id']not in IDS:continue
  old=next(x for x in baseline['target_actions']if x['id']==a['id']);assert a['frames']==old['frames']and len(a['frames'])==54 and a['contactTick']==34
  revised=copy.deepcopy(a['frames']);impact_at=a['frames'][34]['effects'][0]['position']
  for t,row in enumerate(revised):
   if t<20:eid=charge[t];point=[88,57]
   elif t<34:eid=flight[[0,0,1,1,2,2,1,1,2,2,3,3,3,3][t-20]];point=a['frames'][t]['effects'][0]['position']
   elif t<53:eid=impact[t-34];point=impact_at
   else:row['effects']=[];continue
   row['effects']=[{'sprite':eid,'position':point,'flip':False}]
  a['revisedFrames']=revised;a['effectRevision']=REV;a['_reviewCloseCamera']={'offset':[-64,-112],'size':[272,144],'purpose':'Keep complete charge, flight and target explosion visible in the close preview'}
  a['notes']=old['notes'].split(' 本次修改记录：')[0]+' 特效V2：第1至20帧聚光连续变大并逐渐转暖；第21至34帧为柔和赤红弹体，第35帧在目标处单次爆炸，之后扩散、碎焰与余烬消退，第54帧清空。特效适当降低饱和度。人物、原54帧／50fps和第35帧结算保持。'
 bundle.setdefault('effects',{}).update(effects);write(BUNDLE,bundle);write(OUT/'effect-contract.json',{'revision':REV,'charge_ticks':[0,19],'flight_ticks':[20,33],'single_impact_tick':34,'dissipation_ticks':[35,52],'clear_tick':53,'total_ticks':54,'fps':50,'target_ids':sorted(IDS),'palette':HEX,'charge_palette':GOLD,'source_cells':CELL_STATS,'frames':records,'runtime_integrated':False});write(OUT/'asset-manifest.json',{'assets':ASSETS,'prompts':['source/initial-prompt.txt','source/muted-prompt.txt'],'generator':'built-in image_gen; only technical extraction, registration, palette normalization and scale/fade in this script','runtime_integrated':False});return frames
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
 Scope().visit(fn);assert removed.count('write_text')==3;module=ModuleType('scoped_sun_vfx_builder');module.__file__=str(path);module.OWN_BUNDLE=BUNDLE.resolve();exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),module.__dict__);before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert S.snapshot_shared()==before;write(OUT/'gallery-data.json',data);return data
def verify(d):
 baseline=json.loads((SRC/'baseline.json').read_text());old={a['id']:a for a in baseline['target_actions']};ps={p['id']:p for p in d['profiles']};checks=0;errors=[]
 for a in d['actions']:
  if a['id']not in IDS:continue
  assert a['frames']==old[a['id']]['frames']and a['fps']==50 and a['contactTick']==34 and len(a['revisedFrames'])==54 and a['ready'];checks+=4
  for tick,row in enumerate(a['revisedFrames']):
   assert{k:v for k,v in row.items()if k!='effects'}=={k:v for k,v in a['frames'][tick].items()if k!='effects'};assert len(row['effects'])==(0 if tick==53 else 1);checks+=2
   if tick>=34 and tick<53:assert row['effects'][0]['position']==a['frames'][34]['effects'][0]['position'];checks+=1
   for e in row['effects']:
    meta=d['effects'][e['sprite']];im=E.load(meta['path']);at=[e['position'][i]-meta['anchor'][i]for i in(0,1)];box=S.V.box_at(im,at,meta['frame_size'],False);checks+=1
    if S.V.outside(box,a['viewport']):errors.append({'action':a['id'],'tick':tick,'bounds':box,'view':a['viewport']})
    c=a['closeCamera'];view=[a['origin'][i]+row['offset'][i]+c['offset'][i]for i in(0,1)]+c['size']
    if S.V.outside(box,view):errors.append({'action':a['id'],'tick':tick,'kind':'close clipping','bounds':box,'view':view})
 assert all(sha(ROOT/path)==baseline['body_hashes'][k]for k,path in baseline['profile']['newFrames'].items());assert all(sha(ROOT.parents[1]/p)==h for p,h in baseline['runtime_hashes'].items());checks+=11
 contract=json.loads((OUT/'effect-contract.json').read_text());charge=[r for r in contract['frames']if r['phase']=='charge'];assert all(a['width_logical']<b['width_logical']for a,b in zip(charge,charge[1:]));checks+=1
 report={'passed':not errors,'checks':checks,'only_actions':sorted(IDS),'source_timeline_and_all_body_rows_unchanged':True,'contact_tick':34,'display_contact_frame':35,'single_explosion_event':True,'clear_at_final_tick':53,'charge_grows_monotonically':True,'palette':'warm pale gold; reduced-saturation scarlet/copper/terracotta; cream core, no pure white','runtime_files_unchanged':True,'errors':errors};write(OUT/'verification.json',report);assert not errors,errors[:3];return report
def previews(d):
 p=next(p for p in d['profiles']if p['context']=='battle');a=next(a for a in d['actions']if a['id'].endswith('--sun-crown'));ticks=[0,5,10,15,19,20,26,33,34,36,39,42,46,49,52,53]
 for light in[False,True]:
  out=Image.new('RGB',(4*480,4*340+52),(220,222,216)if light else(32,45,53));draw=ImageDraw.Draw(out);fg=(28,39,52)if light else(235,243,242);draw.text((out.width/2,25),'日冠聚光 · 聚光变大 → 赤红发射 → 单次爆炸 → 余烬消散',font=E.font(21),fill=fg,anchor='mm')
  for i,t in enumerate(ticks):
   panel=E.render_panel(d,p,a,a['revisedFrames'][t],True,2,light,False);panel.thumbnail((472,288),Image.Resampling.NEAREST);x=i%4*480+(480-panel.width)//2;y=52+i//4*340;out.paste(panel,(x,y));draw.text((i%4*480+240,y+310),'第 '+str(t+1)+' 帧',font=E.font(17),fill=fg,anchor='mm')
  out.save(OUT/('phases-light.png'if light else'phases-dark.png'),optimize=True)
def export(d):
 records=[]
 for a in d['actions']:
  if a['id']not in IDS:continue
  for close in[False,True]:records.append(E.export(d,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False)))
 results=[]
 for a in d['actions']:
  if a['id']not in IDS:continue
  for close in[False,True]:
   p=ROOT/'demos/videos'/(a['id']+('--close'if close else'')+'.mp4');v=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(p)]))['streams'][0];assert int(v['nb_read_frames'])==54 and abs(float(v['duration'])-1.08)<.02;results.append({'path':p.relative_to(ROOT).as_posix(),**v})
 write(OUT/'export-report.json',{'exports':records,'decoded_videos':results,'only_two_actions_and_four_videos_written':True})
def merge(d):
 paths=S.source_paths();before=S.snapshot_shared();live=json.loads(paths[1].read_text());assert S.parse_js(paths[0])==live;combined=copy.deepcopy(live);mine=[a for a in d['actions']if a['id']in IDS];combined['actions']=S.merge_rows(live['actions'],mine,lambda r:r['id']in IDS)
 assert[a for a in combined['actions']if a['id']not in IDS]==[a for a in live['actions']if a['id']not in IDS];assert combined['profiles']==live['profiles']
 for key,meta in d['effects'].items():
  if key.startswith('review-divine-sun-v2-'):combined['effects'][key]=meta
 assert{k:v for k,v in combined['effects'].items()if not k.startswith('review-divine-sun-v2-')}=={k:v for k,v in live['effects'].items()if not k.startswith('review-divine-sun-v2-')}
 combined['builtAt']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();report=json.loads(paths[2].read_text());report['builtAt']=combined['builtAt'];report['actions']=S.merge_rows(report['actions'],[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in mine],lambda r:r['id']in IDS)
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.sun-vfx-',dir=p.parent);os.close(fd);tmp=Path(name);tmp.write_text(text);staged.append((tmp,p))
  assert S.snapshot_shared()==before,'Concurrent gallery writer; retry merge'
  for temp,p in staged:os.replace(temp,p)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert S.sha(paths[3])==before['index.html'];write(OUT/'merge-report.json',{'changed_action_ids':sorted(IDS),'other_actions_profiles_and_effects_preserved':True,'runtime_integrated':False})
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--author',action='store_true');ap.add_argument('--export',action='store_true');ap.add_argument('--merge',action='store_true');args=ap.parse_args()
 if args.author:author()
 d=build();r=verify(d);previews(d);print(json.dumps(r,ensure_ascii=False),flush=True)
 if args.export:export(d);d=build()
 if args.merge:merge(d)
if __name__=='__main__':main()
