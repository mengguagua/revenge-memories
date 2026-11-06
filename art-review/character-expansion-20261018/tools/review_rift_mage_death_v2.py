#!/usr/bin/env python3
"""Six native wisps and a skull shatter, scoped to enemy16 Death review VFX."""
import argparse,copy,hashlib,json,math,os,subprocess,tempfile
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
import integrate_rift_mage_staff_v1 as scoped
import integrate_enemy_11_14_review as shared
import export_gallery as E
import validate_gallery as V

ROOT=scoped.ROOT;REV='rift-mage-death-vfx-v2-20261024';OUT=ROOT/REV
MP=ROOT/'professions/class-16-enemy/battle/frame_mapping.json'
PREFIX='professions-class-16-enemy-battle--class_16_enemy_item_33'
BLUE={'native-1f904126982541','native-c4a2ded520a271','native-7f8a58368f756d'}
SKULL={'native-508a940a32b46e','native-a4e93261c9bfb7'}
def owns(a):return a['id'].startswith(PREFIX)
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def body(row):return{k:v for k,v in row.items()if k!='effects'}

def baseline():
 p=OUT/'baseline.json'
 if not p.exists():
  data=json.loads((ROOT/'demos/gallery-data.json').read_text());mapping=json.loads(MP.read_text())
  write(p,{'mapping':mapping,'timeline':json.loads((MP.parent/mapping['review_timeline']).resolve().read_text()),'actions':[a for a in data['actions']if owns(a)],'profiles':[p for p in data['profiles']if p['id']=='professions-class-16-enemy-battle'],'effects':{k:data['effects'][k]for k in BLUE|SKULL},'body_files':{p:shared.sha(ROOT/p)for profile in data['profiles']if profile['id']=='professions-class-16-enemy-battle'for p in profile['newFrames'].values()}})
 return json.loads(p.read_text())

def pieces(base):
 source=ROOT/base['effects']['native-508a940a32b46e']['path'];im=Image.open(source).convert('RGBA');parts=[];effects={};inventory=[]
 for y0,y1 in[(0,8),(8,16),(16,24)]:
  for x0,x1 in[(0,5),(5,11),(11,16)]:
   tile=im.crop((x0,y0,x1,y1))
   if not tile.getbbox():continue
   n=len(parts);path=OUT/'effects'/f'skull-piece-{n:02}.png';path.parent.mkdir(exist_ok=True,parents=True);tile.save(path,optimize=True)
   parts.append({'n':n,'box':[x0,y0,x1,y1],'size':list(tile.size),'path':rel(path)})
   inventory.append({'path':rel(path),'purpose':'无重绘：现有红骷髅原像素切片','size':list(tile.size),'bytes':path.stat().st_size,'sha256':shared.sha(path),'source':rel(source),'source_box':[x0,y0,x1,y1]})
   for level,scale in enumerate([1,.75,.5,.25]):
    size=[max(1,round(t*scale))for t in tile.size];key=f'review-c16-death-piece-{n:02}-{level}'
    effects[key]={'path':'../../../'+rel(path),'frame_size':size,'frames':1,'anchor':[s/2 for s in size],'flip_origin_offset':[0,0],'native_skull_crop':[x0,y0,x1,y1]}
 for native in sorted(BLUE):
  for level,size in enumerate([16,12,8,4]):
   effects[f'review-c16-death-wisp-{native[7:]}-{level}']={'path':'../../../'+base['effects'][native]['path'],'frame_size':[size,size],'frames':1,'anchor':[size/2,size/2],'flip_origin_offset':[0,0]}
 write(OUT/'asset-manifest.json',{'revision':REV,'new_painted_assets':0,'native_pixel_crops':inventory,'source_pixels_preserved':True,'runtime_integrated':False});return parts,effects

def six_wisps(row):
 skull=next((e for e in row['effects']if e['sprite']in SKULL),None)
 if not skull:return []
 result=[]
 for e in row['effects']:
  if e['sprite']not in BLUE:continue
  result.append(copy.deepcopy(e));opposite=copy.deepcopy(e)
  opposite['position']=[2*skull['position'][i]-e['position'][i]for i in(0,1)];result.append(opposite)
 return result

def shatter(skull,age,parts):
 pos=skull['position'];flipped=skull.get('flip',False);left=pos[0]-8+(16 if flipped else 0);top=pos[1]-8;center=[left+8,top+12];rows=[]
 for p in parts:
  n=p['n'];life=21+n%5
  if age>=life:continue
  x0,y0,x1,y1=p['box'];cx=(x0+x1)/2;cy=(y0+y1)/2
  if flipped:cx=16-cx
  dx,dy=cx-8,cy-12;length=math.hypot(dx,dy)
  if length<1:dx,dy=math.cos(n*2.4),math.sin(n*2.4);length=1
  distance=age*(.95+.12*(n%3));level=0 if age<life-6 else 1 if age<life-4 else 2 if age<life-2 else 3
  at=[left+cx+dx/length*distance,top+cy+dy/length*distance+age*age/180]
  rows.append({'sprite':f'review-c16-death-piece-{n:02}-{level}','position':[round(x,2)for x in at],'flip':flipped,'priority':0})
 return rows

def camera(action,rows,all_effects):
 origin=action['origin'];b=action['closeCamera']['bodyBoundsUnion'];bounds=[[b[0]+origin[0],b[1]+origin[1],b[2]+origin[0],b[3]+origin[1]]]
 for row in action['frames']+rows:
  for e in row['effects']:
   m=all_effects[e['sprite']];at=[e['position'][i]-m['anchor'][i]for i in(0,1)]
   if e.get('flip'):at=[at[i]+m.get('flip_origin_offset',[0,0])[i]for i in(0,1)]
   box=V.box_at(V.image(m['path']),at,m['frame_size'],e.get('flip',False))
   if box:bounds.append(box)
 union=[min(b[0]for b in bounds),min(b[1]for b in bounds),max(b[2]for b in bounds),max(b[3]for b in bounds)];sizes=[max(m,math.ceil((union[i+2]-union[i]+24)/8)*8)for i,m in enumerate([144,112])]
 return {'offset':[math.floor((union[i]+union[i+2]-sizes[i])/2)-origin[i]for i in(0,1)],'size':sizes,'bodyBoundsUnion':b,'effectBoundsIncluded':True,'padding':12}

def prepare():
 b=baseline();parts,defs=pieces(b);timeline=copy.deepcopy(b['timeline']);timeline.update(revision=REV,runtime_integrated=False);timeline.setdefault('effects',{}).update(defs)
 all_effects=json.loads((ROOT/'demos/gallery-data.json').read_text())['effects'];all_effects.update({k:{**v,'path':rel((MP.parent/v['path']).resolve())}for k,v in defs.items()})
 for a in b['actions']:
  rows=copy.deepcopy(a['frames']);contact=a['contactTick']
  for tick,row in enumerate(rows):
   native=a['frames'][tick];wisps=six_wisps(native);row['effects']=[copy.deepcopy(e)for e in native['effects']if e['sprite']not in BLUE]
   if tick<contact:row['effects']+=wisps;continue
   row['effects']=[e for e in row['effects']if e['sprite']not in SKULL];age=tick-contact;skull=next(e for e in native['effects']if e['sprite']in SKULL)
   if age<8:
    pivot=[skull['position'][0]+(16 if skull.get('flip')else 0),skull['position'][1]+4];f=age/7
    for e in wisps:
     meta=b['effects'][e['sprite']];p=[e['position'][0]+(meta.get('flip_origin_offset',[0,0])[0]if e.get('flip')else 0),e['position'][1]]
     row['effects'].append({'sprite':f'review-c16-death-wisp-{e["sprite"][7:]}-{age//2}','position':[round(p[i]*(1-f)+pivot[i]*f,2)for i in(0,1)],'flip':False,'priority':0})
   row['effects']+=shatter(skull,age,parts)
  timeline['actions'][a['key']]={'source_frames_sha256':digest(a['frames']),'frames':rows,'close_camera':camera(a,rows,all_effects),'events':{'blue_wisps':6,'native_build_up_ticks':[51,65,79],'burst_start_tick':contact,'last_effect_tick':max(i for i,row in enumerate(rows)if row['effects']),'native_actor_rows_unchanged':True,'native_contact_unchanged':True,'new_hits':0},'note':'死亡：蓝色鬼火成六点环绕；原结算时刻红色骷髅向外炸裂，碎片与鬼火在原收势结束前消散。保留持杖人物、原动作、原时长和一次结算，仅修改本法术特效。'}
 write(OUT/'enemy-spell-motion.json',timeline);mapping=json.loads(MP.read_text());mapping.update(review_timeline='../../../'+REV+'/enemy-spell-motion.json',effect_revision=REV);write(MP,mapping)

def build():
 previous=scoped.OUT;scoped.OUT=OUT
 try:return scoped.build()
 finally:scoped.OUT=previous

def verify(data):
 b=baseline();old={a['id']:a for a in b['actions']};checks=0;errors=[];records=[]
 for a in data['actions']:
  if not owns(a):continue
  original=old[a['id']];rows=a['revisedFrames'];assert len(rows)==len(a['frames'])==258 and a['contactTick']==231
  for field in['frames','origin','fps','duration','contactTick','reviewTailFrames']:
   assert a.get(field)==original.get(field),(a['id'],field)
  for tick,row in enumerate(rows):
   assert body(row)==body(a['frames'][tick]);count=sum(e['sprite']in BLUE for e in row['effects']);checks+=1
   if 79<=tick<a['contactTick']:assert count==6,(tick,count)
   if tick>=a['contactTick']:assert not any(e['sprite']in SKULL for e in row['effects'])
   for e in row['effects']:
    m=data['effects'][e['sprite']];at=[e['position'][i]-m['anchor'][i]for i in(0,1)]
    if e.get('flip'):at=[at[i]+m.get('flip_origin_offset',[0,0])[i]for i in(0,1)]
    box=V.box_at(V.image(m['path']),at,m['frame_size'],e.get('flip',False));checks+=1
    if V.outside(box,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'tick':tick,'scene':box})
    c=a['closeCamera'];view=[a['origin'][i]+c['offset'][i]for i in(0,1)]+c['size']
    if V.outside(box,view):errors.append({'action':a['id'],'tick':tick,'close':box})
  assert not rows[-1]['effects'] and a['ready'];records.append({'id':a['id'],'ticks':len(rows),'contact_tick':a['contactTick'],'six_wisps_during_full_orbit':True,'intact_skull_removed_at_contact':True,'last_frame_empty':True,'body_rows_exact':True,'close_camera':a['closeCamera']})
 assert len(records)==6
 for path,sha in b['body_files'].items():assert shared.sha(ROOT/path)==sha
 write(OUT/'checks.json',{'passed':not errors,'checks':checks,'actions':records,'errors':errors,'body_assets_unchanged':True,'runtime_integrated':False})
 assert not errors,errors[:4]

def export(data):
 records=[];videos=[]
 for a in data['actions']:
  if not owns(a):continue
  for close in[False,True]:
   records.append(E.export(data,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False)));suffix='--close'if close else'';p=ROOT/'demos/videos'/(a['id']+suffix+'.mp4')
   probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(p)],text=True))['streams'][0];assert int(probe['nb_read_frames'])==258;videos.append({'path':rel(p),'frames':258,'seconds':float(probe['duration'])})
 write(OUT/'export-report.json',{'exports':records,'decoded_videos':videos,'scope':'six enemy16 Death variants, full and close views'})

def previews(data):
 a=next(a for a in data['actions']if a['id']==PREFIX+'_vs_heavy');p=next(p for p in data['profiles']if p['id']==a['profile']);ticks=[186,230,234,240,248,257]
 for light in[False,True]:
  panels=[]
  for tick in ticks:
   panel=E.render_panel(data,p,a,a['revisedFrames'][tick],True,2,light,True).convert('RGB');panels.append((tick,panel))
  w,h=panels[0][1].size;bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242);board=Image.new('RGB',(w*3,(h+44)*2),bg);draw=ImageDraw.Draw(board)
  for n,(tick,panel)in enumerate(panels):
   x=n%3*w;y=n//3*(h+44);board.paste(panel,(x,y+38));draw.text((x+w/2,y+18),f'{tick+1} / 258  ·  '+('六鬼火环绕'if tick<231 else'骷髅炸裂'if tick<250 else'结束清场'),font=E.font(16),anchor='mm',fill=fg)
  board.save(OUT/('phases-light.png'if light else'phases-dark.png'),optimize=True)

def merge(data):
 files=shared.source_paths();before=shared.snapshot_shared();live=json.loads(files[1].read_text());assert shared.parse_js(files[0])==live;combined=copy.deepcopy(live);new={a['id']:a for a in data['actions']if owns(a)};assert len(new)==6
 combined['actions']=[new.get(a['id'],a)for a in live['actions']]
 assert [a for a in combined['actions']if not owns(a)]==[a for a in live['actions']if not owns(a)]
 timeline=json.loads((OUT/'enemy-spell-motion.json').read_text());effect_ids=set(timeline['effects'])
 for key in effect_ids:
  value=data['effects'][key]
  if key in combined['effects']:assert combined['effects'][key]==value
  else:combined['effects'][key]=value
 assert all(combined['effects'][key]==value for key,value in live['effects'].items())
 from datetime import datetime,timezone
 combined['builtAt']=datetime.now(timezone.utc).isoformat();report=json.loads(files[2].read_text());report['builtAt']=combined['builtAt'];rows={a['id']:{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in new.values()};report['actions']=[rows.get(a['id'],a)for a in report['actions']]
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for path,text in[(files[0],'window.GALLERY_DATA = '+payload+';\n'),(files[1],payload+'\n'),(files[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.rift-death-',dir=path.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),path))
  assert shared.snapshot_shared()==before,'concurrent shared writer; retry latest merge'
  for temp,path in staged:os.replace(temp,path)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert combined['profiles']==live['profiles']and shared.sha(files[3])==before['index.html']
 write(OUT/'merge-report.json',{'target_actions':6,'all_other_actions_unchanged':True,'all_profiles_and_body_art_unchanged':True,'all_previous_effect_definitions_unchanged':True,'new_effect_definitions':len(effect_ids),'index_default_preserved':True})

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--export',action='store_true');parser.add_argument('--merge',action='store_true');args=parser.parse_args()
 if args.prepare:prepare()
 data=build();verify(data);previews(data);print(json.dumps({'checked_variants':6,'six_wisps':True,'shatter_at_tick':231,'final_tick':257,'runtime_integrated':False}),flush=True)
 if args.export:export(data);data=build()
 if args.merge:merge(data)
if __name__=='__main__':main()
