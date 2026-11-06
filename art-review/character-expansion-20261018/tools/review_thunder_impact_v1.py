#!/usr/bin/env python3
"""Shared ally/enemy Thunder ground-impact art; scoped reversible gallery update."""
import argparse,ast,contextlib,copy,hashlib,io,json,os,subprocess,tempfile
from functools import lru_cache
from pathlib import Path
from types import ModuleType,SimpleNamespace
from datetime import datetime,timezone
from PIL import Image,ImageDraw
import build_gallery as G
import export_gallery as E
import validate_gallery as V
import integrate_enemy_11_14_review as shared

ROOT=G.ROOT;REV='thunder-ground-impact-v1-20261024';OUT=ROOT/REV;SRC=OUT/'source'
OLD_BOLTS={'5e1412fe31db9b','8dc40f656364b7','7c0b1ad93316d1','5289f8723b8123'}
HEX=['eef2f1','b5c9e4','898cca','566ca4','35435f','1e2e48'];COLORS=[tuple(bytes.fromhex(h))for h in HEX]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def target(a):return '_item_24'in a.get('key','')
@lru_cache(maxsize=None)
def color(rgb):return min(COLORS,key=lambda c:sum((a-b)**2 for a,b in zip(rgb,c)))
def quant(im,threshold):
 q=Image.new('RGBA',im.size);q.putdata([(*color(p[:3]),255)if p[3]>=threshold else(0,0,0,0)for p in im.getdata()]);return q
def save(im,path,purpose):
 p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);colors=sorted(set(im.getdata()));assert len(colors)<=256;q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));ix={c:i for i,c in enumerate(colors)};q.putdata([ix[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes();q.save(p,optimize=True)
 return {'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p)}
def prepare_assets():
 assets=[];effects={};raw=quant(Image.open(SRC/'bolt-master.png').convert('RGBA'),240);bb=raw.getbbox();cut=raw.crop(bb);s=896/cut.height;q=cut.resize((round(cut.width*s),896),Image.Resampling.NEAREST)
 pts=[(x+.5,y+.5)for y in range(q.height-24,q.height)for x in range(q.width)if q.getpixel((x,y))[3]];tip=sum(x for x,y in pts)/len(pts);full=Image.new('RGBA',(256,960));at=[round(128-tip),32];full.alpha_composite(q,at);assert sum(p[3]>0 for p in full.getdata())==sum(p[3]>0 for p in q.getdata())
 def add(key,im,path,frame_size,anchor,purpose):
  rec=save(im,path,purpose);assets.append(rec);effects[key]={'path':'../../../'+rec['path'],'frame_size':frame_size,'frames':1,'anchor':anchor,'flip_origin_offset':[0,0]}
 add('review-thunder-impact-bolt',full,'effects/bolt-full.png',[64,240],[32,232],'单股未分叉落雷；尖端注册于落地点')
 for i,u in enumerate([.18,.36,.54,.72,.87,.96]):
  im=full.copy();end=32+round(896*u);im.paste((0,0,0,0),(0,end,256,960));add(f'review-thunder-impact-fall-{i}',im,f'effects/fall-{i}.png',[64,240],[32,232],'由上到下揭示落雷，落地前不分叉')
 master=Image.open(SRC/'ground-impact-master.png').convert('RGBA');pivots=[(250,444),(240,444),(252,444),(249,369),(242,369),(253,369)]
 phases=[]
 for i in range(6):
  col=i%3;row=i//3;cut=quant(master.crop((col*512,row*512,(col+1)*512,(row+1)*512)),215);small=cut.resize((287,287),Image.Resampling.NEAREST);ratio=287/512;pos=[round(160-pivots[i][0]*ratio),round(128-pivots[i][1]*ratio)];im=Image.new('RGBA',(320,160));im.alpha_composite(small,pos)
  assert sum(p[3]>0 for p in im.getdata())==sum(p[3]>0 for p in small.getdata()),(i,'clipped impact pixels');phases.append(im)
  add(f'review-thunder-impact-ground-{i}',im,f'effects/ground-{i}.png',[80,40],[40,32],'落地冲击阶段'+str(i)+'；共用固定地面点')
 for i,alpha in enumerate([192,128,64]):
  im=phases[5].copy();im.putalpha(im.getchannel('A').point(lambda n:round(n*alpha/255)));add(f'review-thunder-impact-fade-{i}',im,f'effects/fade-{i}.png',[80,40],[40,32],'残余电屑渐隐，不再次爆闪')
 write(OUT/'assets.json',{'revision':REV,'effects':effects,'assets':assets,'palette':HEX,'compression':'lossless indexed PNG, decoded RGBA exact','bolt_uniform_scale':s,'ground_uniform_scale':287/512,'raw_ground_pivots':pivots})
 for light in[False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242);board=Image.new('RGB',(3*352,2*220+56),bg);dr=ImageDraw.Draw(board);dr.text((board.width/2,26),'雷电 · 先冲击地面，再电弧分裂',font=E.font(20),anchor='mm',fill=fg)
  for i,im in enumerate(phases):
   x=i%3*352+16;y=i//3*220+56;board.paste(im,(x,y),im);label=['落地爆闪','冲击扩散','压力环与碎屑','随后分叉','电弧分裂','余电消退'][i];dr.text((x+160,y+185),label,font=E.font(16),anchor='mm',fill=fg)
  board.save(OUT/('phases-light.png'if light else'phases-dark.png'),optimize=True)
 print(json.dumps({'prepared_assets':len(assets)}),flush=True)

def adapt(a,data):
 rows=copy.deepcopy(a.get('revisedFrames',a['frames']));hits=[(t,e)for t,row in enumerate(rows)for e in row.get('effects',[])if e['sprite'].removeprefix('native-')in OLD_BOLTS];assert hits,a['id'];first=hits[0][0];e=hits[0][1];contact=a['contactTick'];assert first==contact-1 and not e.get('flip'),a['id']
 meta=data['effects'][e['sprite']];im=Image.open(ROOT/meta['path']).convert('RGBA');bb=im.getbbox();pts=[x+.5 for y in range(bb[3]-4,bb[3])for x in range(im.width)if im.getpixel((x,y))[3]];delta=round(sum(pts)/len(pts)-meta['anchor'][0]);point=[e['position'][0]+delta,e['position'][1]-meta['anchor'][1]+bb[3]];assert point[1]==128
 start=contact-6;end=contact+24;assert start>=0 and end<=len(rows)
 for t,row in enumerate(rows):
  row['effects']=[f for f in row.get('effects',[])if f['sprite'].removeprefix('native-')not in OLD_BOLTS]
  age=t-contact;ids=[]
  if -6<=age<0:ids=[f'review-thunder-impact-fall-{age+6}']
  elif 0<=age<2:ids=['review-thunder-impact-bolt','review-thunder-impact-ground-0']
  elif 2<=age<5:ids=['review-thunder-impact-bolt','review-thunder-impact-ground-1']
  elif 5<=age<8:ids=['review-thunder-impact-bolt','review-thunder-impact-ground-2']
  elif 8<=age<12:ids=['review-thunder-impact-ground-3']
  elif 12<=age<17:ids=['review-thunder-impact-ground-4']
  elif 17<=age<20:ids=['review-thunder-impact-ground-5']
  elif 20<=age<24:ids=[f'review-thunder-impact-fade-{min(2,age-20)}']
  row['effects'].extend({'sprite':k,'position':point,'flip':False}for k in ids)
 note='双方共用雷电落地演出：单股闪电先下落，原结算帧冲击地面，爆闪、冲击扩散和碎屑持续8帧后才开始分叉电弧；随后碎裂与渐隐。落地点按原雷电底端注册。近景展示地面与施法者。人物、施法动作、原结算次数和总时长保持。'
 return {'source_frames_sha256':digest(a['frames']),'frames':rows,'note':note,'close_camera':{'offset':[-8-a['origin'][0],24-a['origin'][1]],'size':[280,120]},'events':{'revision':REV,'spell_id':24,'descent_start':start,'impact_tick':contact,'branch_start':contact+8,'end_exclusive':end,'ground_point':point,'native_bottom_x_offset':delta,'additional_hits':0}}, {'id':a['id'],'key':a['key'],'profile':a['profile'],'side':next(p['side']for p in data['profiles']if p['id']==a['profile']),'total_ticks':len(rows),'fps':a['fps'],'contact_tick':contact,'original_target_first_tick':first,'descent_start':start,'impact_tick':contact,'branch_start':contact+8,'end_exclusive':end,'ground_point':point,'caster_rows_unchanged':True,'additional_hits':0}

def prepare_timelines():
 if (OUT/'scope.json').exists():
  print('Prepared scope already exists; keeping its original baseline.',flush=True);return
 live=json.loads((ROOT/'demos/gallery-data.json').read_text());assert shared.parse_js(ROOT/'gallery-data.js')==live;actions=[a for a in live['actions']if target(a)];assert len(actions)==60;profiles={p['id']:p for p in live['profiles']};asset=json.loads((OUT/'assets.json').read_text());maps=[];records=[];baseline={'actions':{a['id']:a for a in actions},'profiles':{pid:profiles[pid]for pid in {a['profile']for a in actions}},'mapping_before':{},'body_assets':{},'all_action_digests':{a['id']:a['contentDigest']for a in live['actions']},'runtime_integrated':False}
 for pid in sorted({a['profile']for a in actions}):
  p=profiles[pid];mp=ROOT/p['mapping'];before=mp.read_text();mapping=json.loads(before);baseline['mapping_before'][p['mapping']]=copy.deepcopy(mapping);previous=(mp.parent/mapping['review_timeline']).resolve()if mapping.get('review_timeline')else None;timeline=copy.deepcopy(json.loads(previous.read_text()))if previous else{'effects':{},'actions':{}}
  # An effect registry has one owner. Existing declarations are retained at
  # their old owner profile so unrelated spells remain byte-for-byte equal.
  if pid=='professions-class-15-ally-battle':
   assert not set(asset['effects'])&set(timeline.get('effects',{}));timeline.setdefault('effects',{}).update(asset['effects'])
  timeline['thunder_impact_revision']=REV;timeline['thunder_impact_previous_timeline']=str(previous.relative_to(ROOT))if previous else None
  for a in actions:
   if a['profile']!=pid:continue
   revision,contract=adapt(a,live);timeline.setdefault('actions',{})[a['key']]=revision;records.append(contract)
  tp=OUT/'timelines'/(pid+'.json');write(tp,timeline);mapping['review_timeline']=os.path.relpath(tp,mp.parent);mapping['shared_thunder_effect_revision']=REV;maps.append({'mapping':p['mapping'],'timeline':tp.relative_to(ROOT).as_posix()});assert mp.read_text()==before;write(mp,mapping)
  for path in p['newFrames'].values():baseline['body_assets'][path]=sha(ROOT/path)
 write(OUT/'baseline.json',baseline);write(OUT/'scope.json',{'revision':REV,'profiles':sorted(baseline['profiles']),'actions':[a['id']for a in actions],'mappings':maps,'effect_registry_owner':'professions-class-15-ally-battle','runtime_integrated':False});write(OUT/'action-effect-mapping.json',{'revision':REV,'spell_id':24,'cards_and_actions':records,'unchanged':['caster/body art','actor frame order/offset/flip/alpha','contactTick','single spell resolution','fps','action length','all non-Thunder actions'],'runtime_integrated':False});print(json.dumps({'prepared_profiles':len(maps),'actions':len(records)}),flush=True)

def isolated_builder(scope):
 path=ROOT/'tools/build_gallery.py';tree=ast.parse(path.read_text(),filename=str(path));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='build');removed=[];filters=[]
 class Scope(ast.NodeTransformer):
  def visit_For(self,node):
   node=self.generic_visit(node)
   if isinstance(node.target,ast.Name)and node.target.id=='mapping_path':node.body.insert(0,ast.parse('if str(mapping_path.resolve()) not in SCOPED_MAPPING_PATHS: continue').body[0]);filters.append('mapping')
   if isinstance(node.target,ast.Name)and node.target.id=='bundle_path':node.body.insert(0,ast.Continue());filters.append('bundle')
   if isinstance(node.target,ast.Name)and node.target.id=='key'and isinstance(node.iter,ast.Name)and node.iter.id=='keys':node.body.insert(0,ast.parse("if '_item_24' not in key: continue").body[0]);filters.append('variants')
   if isinstance(node.iter,ast.Call)and isinstance(node.iter.func,ast.Name)and node.iter.func.id=='reactions':node.body.insert(0,ast.Continue());filters.append('reactions')
   return node
  def visit_Expr(self,node):
   if isinstance(node.value,ast.Call)and isinstance(node.value.func,ast.Attribute)and node.value.func.attr in['write_text','mkdir']:removed.append(node.value.func.attr);return None
   return self.generic_visit(node)
 Scope().visit(fn);assert removed.count('write_text')==3 and sorted(filters)==['bundle','mapping','reactions','variants'];m=ModuleType('scoped_thunder_builder');m.__file__=str(path);m.SCOPED_MAPPING_PATHS={str((ROOT/x['mapping']).resolve())for x in scope['mappings']};exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),m.__dict__);return m
def build():
 scope=json.loads((OUT/'scope.json').read_text());m=isolated_builder(scope);live=json.loads((ROOT/'demos/gallery-data.json').read_text());effects=copy.deepcopy(live['effects'])
 for x in scope['mappings']:
  for key in json.loads((ROOT/x['timeline']).read_text()).get('effects',{}):effects.pop(key,None)
 read=m.read
 def scoped_read(path):
  value=read(path)
  if Path(path)==ROOT/'source-input/effects.json':value={**value,**effects}
  return value
 m.read=scoped_read;before=shared.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=m.build()
 assert shared.snapshot_shared()==before
 assert all(a['id']in scope['actions']for a in data['actions']),'Scoped builder created an unrelated action.'
 data['actions']=[a for a in data['actions']if a['id']in scope['actions']];assert len(data['actions'])==60 and all(a['ready']for a in data['actions']);write(OUT/'gallery-data.json',data);return data

def verify(data):
 base=json.loads((OUT/'baseline.json').read_text());contracts={a['id']:a for a in json.loads((OUT/'action-effect-mapping.json').read_text())['cards_and_actions']};errors=[];checks=0;profiles={p['id']:p for p in data['profiles']};effects=data['effects']
 for path,h in base['body_assets'].items():assert sha(ROOT/path)==h,path
 for a in data['actions']:
  old=base['actions'][a['id']];c=contracts[a['id']];assert a['frames']==old['frames'] and len(a['revisedFrames'])==len(old['frames'])
  for key in['contactTick','fps','origin','duration']:assert a[key]==old[key],(a['id'],key)
  before=old.get('revisedFrames',old['frames']);assert all({k:v for k,v in x.items()if k!='effects'}=={k:v for k,v in y.items()if k!='effects'}for x,y in zip(a['revisedFrames'],before))
  p=profiles[a['profile']];fw,fh=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas'])
  for t,row in enumerate(a['revisedFrames']):
   native_rest=[e for e in before[t]['effects']if e['sprite'].removeprefix('native-')not in OLD_BOLTS];revised_rest=[e for e in row['effects']if not e['sprite'].startswith('review-thunder-impact-')];assert native_rest==revised_rest
   own=[e for e in row['effects']if e['sprite'].startswith('review-thunder-impact-')]
   assert all(e['position']==c['ground_point']and not e['flip']for e in own)
   if t<c['impact_tick']:assert all('ground-'not in e['sprite']for e in own)
   if t<c['branch_start']:assert all(e['sprite']not in['review-thunder-impact-ground-3','review-thunder-impact-ground-4']for e in own)
   if t<c['descent_start']or t>=c['end_exclusive']:assert not own
   for e in own:
    meta=effects[e['sprite']];im=V.image(meta['path']);at=[e['position'][i]-meta['anchor'][i]for i in(0,1)];box=V.box_at(im,at,meta['frame_size'],False);checks+=1
    if V.outside(box,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'tick':t,'effect':e['sprite'],'bounds':box})
    if 'ground-'in e['sprite']or 'fade-'in e['sprite']:
     cam=a['closeCamera'];cv=[a['origin'][i]+row['offset'][i]+cam['offset'][i]for i in(0,1)]+cam['size'];checks+=1
     if V.outside(box,cv):errors.append({'action':a['id'],'tick':t,'close_effect':e['sprite'],'bounds':box})
   checks+=1
  at=a['revisedFrames'][a['contactTick']]['effects'];assert any(e['sprite']=='review-thunder-impact-ground-0'for e in at)
 errors+=data['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'actions':60,'profiles':10,'both_sides':True,'impact_before_branch_ticks':8,'descent_ticks':6,'original_actor_rows_exact':True,'non_target_effect_rows_exact':True,'native_resolution_and_duration_unchanged':True,'body_asset_hashes_unchanged':True,'errors':errors,'runtime_integrated':False};write(OUT/'verification.json',report);assert not errors,errors[:5];return report

def export(data):
 records=[];decoded=[]
 for a in data['actions']:
  records.append(E.export(data,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not a.get('defaultVideo'))))
  if a.get('defaultVideo'):
   records.append(E.export(data,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
   for close in[False,True]:
    p=ROOT/'demos/videos'/(a['id']+('--close'if close else'')+'.mp4');info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(p)],text=True))['streams'][0];assert int(info['nb_read_frames'])==E.playback_count(a);decoded.append({'path':p.relative_to(ROOT).as_posix(),'frames':int(info['nb_read_frames']),'duration':float(info['duration']),'size':[info['width'],info['height']]})
  print(json.dumps({'exported':a['id'],'video':bool(a.get('defaultVideo'))}),flush=True)
 write(OUT/'export-report.json',{'records':records,'decoded_videos':decoded,'all_60_live_actions_complete':True,'representative_near_videos':True})

def merge(data):
 ids={a['id']for a in data['actions']};paths=shared.source_paths();before=shared.snapshot_shared();live=json.loads(paths[1].read_text());assert shared.parse_js(paths[0])==live;combined=copy.deepcopy(live);new={a['id']:a for a in data['actions']};old={a['id']:a for a in live['actions']};baseline=json.loads((OUT/'baseline.json').read_text())
 assert all(old[i]['contentDigest']in[baseline['actions'][i]['contentDigest'],new[i]['contentDigest']]for i in ids),'A target action changed in another chat; rebase this art update before merging.'
 combined['actions']=[new.get(a['id'],a)for a in live['actions']];assert[a for a in combined['actions']if a['id']not in ids]==[a for a in live['actions']if a['id']not in ids]
 # Profiles stay byte-for-byte current; only 60 action records and new FX.
 for a in data['actions']:
  for key in a['effectIds']:
   if key in live['effects']:assert data['effects'][key]==live['effects'][key]
   else:assert key.startswith('review-thunder-impact-');combined['effects'][key]=data['effects'][key]
 combined['builtAt']=datetime.now(timezone.utc).isoformat();report=json.loads(paths[2].read_text());report['builtAt']=combined['builtAt'];rows={a['id']:{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in data['actions']};report['actions']=[rows.get(a['id'],a)for a in report['actions']]
 staged=[];payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'))
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.thunder-impact-',dir=p.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),p))
  assert shared.snapshot_shared()==before,'Concurrent shared writer: retry merge against latest snapshot.'
  for tmp,p in staged:os.replace(tmp,p)
 finally:
  for tmp,_ in staged:tmp.unlink(missing_ok=True)
 assert shared.parse_js(paths[0])==json.loads(paths[1].read_text())and sha(paths[3])==before['index.html'];write(OUT/'merge-report.json',{'target_actions':60,'profiles_unchanged':True,'all_non_Thunder_actions_unchanged':True,'existing_effect_definitions_unchanged':True,'default_action_unchanged':True,'runtime_integrated':False})
def main():
 p=argparse.ArgumentParser();p.add_argument('--assets',action='store_true');p.add_argument('--prepare',action='store_true');p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args()
 if args.assets:prepare_assets()
 if args.prepare:prepare_timelines()
 if not(OUT/'scope.json').exists():return
 data=build();v=verify(data);print(json.dumps({'verified_actions':60,'checks':v['checks']}),flush=True)
 if args.export:export(data);data=build()
 if args.merge:merge(data)
if __name__=='__main__':main()
