#!/usr/bin/env python3
"""Keep the old stone-wing battle bitmap/poses; leave the new map art intact."""
import argparse,ast,contextlib,copy,hashlib,io,json,math,re
from pathlib import Path
from types import ModuleType
from PIL import Image,ImageDraw
import integrate_stone_wing_v1 as I
import integrate_enemy_11_14_review as S
import export_gallery as E
ROOT=I.ROOT;REV='stone-wing-legacy-battle-v2-20261024';OUT=ROOT/REV;SRC=OUT/'source';BUNDLE=ROOT/'stone-wing-complete-v1-20261024/gallery_bundle.json';PID='professions-class-3-enemy-battle';FX='review-stone-wing-legacy-stone'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def own(x):return x.get('profile',x.get('id'))==PID or str(x.get('id','')).startswith(PID+'--')
def h(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def row(f,off=(0,0),effects=None,**extra):return{'frame':f,'offset':list(off),'flip':True,'effects':effects or[],**extra}
def prepare():
 bundle=json.loads((SRC/'before-bundle.json').read_text());p=next(p for p in bundle['profiles']if p['id']==PID);cfg=json.loads((ROOT.parents[1]/'actual/data/innate_attack_art.json').read_text())['3'];source=ROOT.parents[1]/'actual'/cfg['path'].removeprefix('res://');atlas=Image.open(source).convert('RGBA');paths={};sizes=[]
 for i in range(8):
  im=atlas.crop((256*i,0,256*(i+1),256));out=im.resize((512,512),Image.Resampling.NEAREST);path=OUT/'battle'/f'frame-{i:03}.png';path.parent.mkdir(parents=True,exist_ok=True);out.save(path,optimize=True);assert out.resize((256,256),Image.Resampling.NEAREST).tobytes()==im.tobytes();paths[str(i)]=path.relative_to(ROOT).as_posix();sizes.append(path.stat().st_size)
 ref=SRC/'legacy-reference.png';atlas.resize((1024,128),Image.Resampling.NEAREST).save(ref,optimize=True);atlas.resize((4096,512),Image.Resampling.NEAREST).save(OUT/'battle-atlas.png',optimize=True)
 p.update(revision=REV,reviewNote='按用户要求，战斗全动作与形象保留旧版。直接复用现行旧八姿势与原石块位图，仅做最近邻技术放大；没有重绘或重新调色。地图仍使用已完成的新稿。',sourceAtlas=ref.relative_to(ROOT).as_posix(),sourceFrameSize=[128,128],sourceAtlasSize=[1024,128],sourceColumns=8,sourceFrameCount=8,anchor=cfg['anchor'],sourceOamCutoff=0,flipOriginOffset=[0,0],outputFrameSize=[512,512],newFrames=paths,frameErrors={},links=[{'label':'旧版战斗完整八姿势','href':REV+'/battle-poses.png'},{'label':'保留旧版记录','href':REV+'/README.md'}])
 bitmap=ROOT.parents[1]/'actual/assets/nature/stone_low.png';ep=OUT/'effects/legacy-stone.png';ep.parent.mkdir(parents=True,exist_ok=True);ep.write_bytes(bitmap.read_bytes());bundle['effects']={FX:{'path':ep.relative_to(ROOT).as_posix(),'frame_size':[16,8],'frames':1,'anchor':[8,4],'flip_origin_offset':[0,0],'default_facing':'right'}}
 old={a['key']:a for a in bundle['actions']if own(a)};actions=[]
 for key,melee,distance in[('stone-claw',True,112),('stone-spit',False,112),('stone-spit-far',False,176)]:
  a=copy.deepcopy(old[key]);prep=12 if melee else 20;contact=prep+14;rows=[];impact=[64+distance-10,100]
  for t in range(contact+20):
   eff=[];dx=dy=0
   if t<prep:f=1 if melee else 4;dx=-3*t/prep;dy=-2 if melee else 0
   elif t<=contact:
    f=2 if melee else 5;v=(t-prep)/14
    if melee:dx=(distance-42)*v;dy=-math.sin(v*math.pi)*12
    else:eff=[{'sprite':FX,'position':[96+(impact[0]-96)*v,84+(impact[1]-84)*v],'flip':True}]
   else:
    f=3
    if melee:dx=(distance-42)*(1-(t-contact)/20)
    if t<contact+5:eff=[{'sprite':FX,'position':[impact[0]+t-contact,impact[1]+2*(t-contact)],'flip':True}]
   rows.append(row(f,(dx,dy),eff))
  a.update(frames=rows,revision=REV,referenceLabel='旧版形象与动作 · 保留',notes='直接复用现行旧版八姿势、50fps、准备与接触时刻、位移和原石块效果；不使用本轮重绘战斗素材。',origin=[64,128],viewport=[-16,-16,320,208])
  # Keep the complete large legacy model and old stone effect in close view.
  a['_reviewCloseCamera']={'offset':[-76,-116],'size':[224 if melee or distance==112 else 272,152]};actions.append(a)
 for key,frames in[('idle',[row(0)for _ in range(60)]),('hit',[row(6,tint=.65 if t<14 else 1)for t in range(28)]),('miss',[row(0)for _ in range(23)]),('exit',[row(6,alpha=max(0,1-(t//8+1)/4))for t in range(32)]),('thick-stone',[row(7)for _ in range(60)])]:
  a=copy.deepcopy(old[key]);a.update(frames=frames,revision=REV,referenceLabel='旧版形象与动作 · 保留',notes='保留旧版对应姿势与材质，不使用新战斗人物。',origin=[64,128],viewport=[-16,-16,320,208]);actions.append(a)
 maps=[a for a in bundle['actions']if not own(a)];bundle['actions']=maps+actions;write(BUNDLE,bundle);write(OUT/'restored-battle-profile.json',{'profile':p,'actions':actions,'effects':bundle['effects']})
 q=Image.new('RGB',(1440,800),(32,45,53));dr=ImageDraw.Draw(q)
 for i in range(8):
  im=Image.open(ROOT/paths[str(i)]).convert('RGBA');im=im.resize((320,320),Image.Resampling.NEAREST);x=i%4*360+20;y=i//4*400;q.paste(im,(x,y),im);dr.text((i%4*360+180,y+365),['旧待机','旧俯冲准备','旧伸爪','旧回收','旧喷吐准备','旧喷吐释放','旧受击','旧厚石甲'][i],font=E.font(20),anchor='mm',fill='white')
 q.save(OUT/'battle-poses.png',optimize=True);print(json.dumps({'legacy_frames':8,'max_frame_bytes':max(sizes),'battle_actions':8,'new_map_actions_retained':len(maps)}),flush=True)
def build():
 path=ROOT/'tools/build_gallery.py';tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='build')
 class Scope(ast.NodeTransformer):
  def visit_For(self,n):
   n=self.generic_visit(n)
   if isinstance(n.target,ast.Name)and n.target.id=='mapping_path':n.body.insert(0,ast.Continue())
   if isinstance(n.target,ast.Name)and n.target.id=='bundle_path':n.body.insert(0,ast.parse('if bundle_path.resolve()!=OWN_BUNDLE: continue').body[0])
   return n
  def visit_Expr(self,n):
   if isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr in['write_text','mkdir']:return None
   return self.generic_visit(n)
 Scope().visit(fn);m=ModuleType('stone_legacy_builder');m.__file__=str(path);m.OWN_BUNDLE=BUNDLE.resolve();exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),m.__dict__);before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):d=m.build()
 assert S.snapshot_shared()==before;d['profiles']=[p for p in d['profiles']if own(p)];d['actions']=[a for a in d['actions']if own(a)];assert len(d['profiles'])==1 and len(d['actions'])==8;write(OUT/'gallery-data.json',d);return d
def verify(d):
 p=d['profiles'][0];atlas=Image.open(ROOT.parents[1]/'actual/assets/innate-enemies-20261023/class-3-battle.png').convert('RGBA');checks=0;errors=[]
 for i,path in p['newFrames'].items():
  i=int(i);im=S.V.image(path);assert im.size==(512,512)and im.resize((256,256),Image.Resampling.NEAREST).tobytes()==atlas.crop((i*256,0,(i+1)*256,256)).tobytes();checks+=1
 for a in d['actions']:
  assert a['ready']
  for t,r in enumerate(a['frames']):
   f=r['frame'];off=r['offset'];at=[a['origin'][i]+off[i]-p['anchor'][i]for i in[0,1]];im=S.V.image(p['newFrames'][str(f)]);box=S.V.box_at(im,at,[128,128],False);checks+=1
   if S.V.outside(box,a['viewport']):errors.append((a['key'],t,'scene',box))
   if a.get('closeCamera'):
    c=a['closeCamera'];view=[a['origin'][i]+off[i]+c['offset'][i]for i in[0,1]]+c['size']
    if S.V.outside(box,view):errors.append((a['key'],t,'close',box))
   for e in r['effects']:
    meta=d['effects'][e['sprite']];point=[e['position'][i]-meta['anchor'][i]for i in[0,1]];box=S.V.box_at(S.V.image(meta['path']),point,meta['frame_size'],True);checks+=1
    if S.V.outside(box,a['viewport']):errors.append((a['key'],t,'effect',box))
    if a.get('closeCamera')and S.V.outside(box,view):errors.append((a['key'],t,'close effect',box))
 base=json.loads((SRC/'before-bundle.json').read_text());now=json.loads(BUNDLE.read_text());assert[p for p in base['profiles']if not own(p)]==[p for p in now['profiles']if not own(p)];assert[a for a in base['actions']if not own(a)]==[a for a in now['actions']if not own(a)]
 for path,expected in json.loads((SRC/'runtime-baseline.json').read_text()).items():assert S.sha(ROOT.parents[1]/path)==expected
 v={'passed':not errors,'checks':checks,'legacy_frames_pixel_exact':8,'legacy_battle_actions':8,'new_maps_exactly_preserved':True,'runtime_unchanged':True,'removed_rejected_208_frame_review_action':True,'errors':errors};write(OUT/'verification.json',v);assert not errors,errors[:4];return v
def export(d):
 old=S.OUT;S.OUT=OUT
 try:S.export_local(d,'all')
 finally:S.OUT=old
 r=json.loads((OUT/'export-report.json').read_text());r['scope']='Stone-wing legacy battle only: eight action videos and three attack close-ups; no map media or unrelated media regenerated.';write(OUT/'export-report.json',r)
def finish(d):
 assert (OUT/'README.md').is_file()and(OUT/'decoded-legacy.png').is_file()
 assert all(a['video']and a['still']and(a['closeVideo']if a['kind']=='attack'else True)for a in d['actions']);I.OUT=OUT;I.own=own;I.merge(d)
 mr=json.loads((OUT/'merge-report.json').read_text());mr.update(target_profiles=1,target_actions=8);write(OUT/'merge-report.json',mr)
 page=ROOT/'index.html';old=page.read_text();m=re.search(r'<section\b[^>]*id="stone-wing-progress".*?</section>',old,re.S);assert m;section=m.group();section=section.replace('柔和蓝紫石甲 · 待验收','地图使用新稿 · 战斗保留旧版')
 note='<p class="action-note" style="margin:0 0 16px">战斗场景的全部动作与形象按要求保留旧版，包含旧版裂石爪、碎岩喷吐、待机、受击、退场与石甲姿势。地图待机和四向行走继续使用本轮蓝紫石翼兽。战斗旧八姿势与原石块效果直接复用，未重新绘制或调色。</p>'
 section=re.sub(r'<p class="action-note" style="margin:0 0 16px">.*?</p>',note,section,count=1,flags=re.S);section=re.sub(r'<a href="\?action=professions-class-3-enemy-battle--original_class_3_enemy_normal#motion-player">.*?</a>','',section)
 for before,after in[('stone-wing-complete-v1-20261024/battle-light.png',REV+'/battle-poses.png'),('stone-wing-complete-v1-20261024/decoded-actions.png',REV+'/decoded-legacy.png'),('stone-wing-complete-v1-20261024/README.md',REV+'/README.md')]:section=section.replace(before,after)
 new=old[:m.start()]+section+old[m.end():];new=re.sub(r'&stone_wing=[^"&]+','',new);new=re.sub(r'(src="gallery-data\.js\?[^"]*)"',lambda m:m.group(1)+'&stone_wing=legacy-battle-v2-20261024"',new,count=1);assert page.read_text()==old;page.write_text(new)
 cp=ROOT/'healer-saint-complete-v1-20261023/profession-catalog-sync.json';c=json.loads(cp.read_text());e=next(x for x in c['classes']if x['class_id']==3);e.update(enemy_art_revision='stone-wing-complete-v1-20261024',enemy_battle_revision=REV,enemy_identity='地图蓝紫新稿；战斗动作及形象按要求保留旧版八姿势',enemy_review_actions=17);write(cp,c)
 live=json.loads((ROOT/'demos/gallery-data.json').read_text());before=json.loads((SRC/'before-live.json').read_text());changed=[]
 for field in['profiles','actions']:
  for x in live[field]:
   if not own(x)and x['id']in before['unrelated_row_hashes'][field]and h(x)!=before['unrelated_row_hashes'][field][x['id']]:changed.append(x['id'])
 assert not any('professions-class-3-enemy-maps-'in x for x in changed)
 files=list(OUT.rglob('*.png'))+[ROOT/'demos/stills'/(a['id']+suffix+'.png')for a in d['actions']for suffix in(['','--close']if a['kind']=='attack'else[''])];inventory=[]
 for p in sorted(set(files)):inventory.append({'path':p.relative_to(ROOT).as_posix(),'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':S.sha(p),'purpose':'legacy exact bitmap or offline comparison/export'})
 write(OUT/'image-inventory.json',{'revision':REV,'images':inventory});write(OUT/'completion.json',{'revision':REV,'battle_retained':'legacy bitmap, eight poses and existing innate sequences/effect','battle_actions':8,'total_stone_actions':17,'map_profiles_and_actions_exactly_preserved':True,'unrelated_live_changes_during_work':changed,'runtime_integrated':False,'device_updated':False});print(json.dumps({'battle_restored':True,'actions':8,'maps_preserved':True}),flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--export',action='store_true');p.add_argument('--finish',action='store_true');a=p.parse_args()
 if a.prepare:prepare()
 d=build();verify(d)
 if a.export:export(d);d=build()
 if a.finish:finish(d)
if __name__=='__main__':main()
