"""Package generated artwork with crop, uniform scale, translation and proven mirroring only."""
from pathlib import Path
from PIL import Image
import hashlib,json,shutil,subprocess

UNIT=Path(__file__).resolve().parents[1]
ROOT=UNIT.parents[1]
MAGICK='/opt/homebrew/bin/magick'
FONT='/System/Library/Fonts/STHeiti Medium.ttc'
def run(*args):subprocess.run([MAGICK,*map(str,args)],check=True)
def mask(im):return im.convert('RGBA').getchannel('A').point(lambda p:255 if p>=32 else 0)
def savej(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def info(p):
 im=Image.open(p);return {'size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'visible_bounds':mask(im).getbbox()}
unit=json.loads((UNIT/'reference/source-unit.json').read_text())
battle=UNIT/'battle';(battle/'frames').mkdir(exist_ok=True)
records=json.loads((battle/'candidate-v4/registration.json').read_text())
for r in records:
 f=r['frame'];dst=battle/f'frames/frame-{f:03}.png';shutil.copy2(battle/f'candidate-v4/frame-{f:03}.png',dst)
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(dst)],check=True,capture_output=True)
 r.update(info(dst));r.update({'path':f'frames/frame-{f:03}.png','source_frame':f,'status':'visual_review_pass'})
run(*[battle/f'frames/frame-{f:03}.png' for f in [0,4,5]],'+append',battle/'frames/arcanist-battle.png')
savej(battle/'frame_mapping.json',{'schema_version':1,'character_id':'enemy-arcanist','display_name':'敌方妖术师','original_class_id':15,'source_side':'enemy','status':'art_and_registration_verified','source_atlas':'../../../'+unit['source_atlas'],'source_atlas_base':'mapping directory','source_frame_size':[80,64],'output_frame_size':[320,256],'source_anchor':[40,64],'output_anchor':[160,256],'source_frame_count':6,'source_columns':16,'canonical_frames':[0,4,5],'frame_mapping':{str(f):f'frames/frame-{f:03}.png' for f in [0,4,5]},'records':records,'variant_keys':unit['bound_action_keys'],'source_idle_frame':0,'output_atlas':'frames/arcanist-battle.png','output_atlas_frame_order':[0,4,5],'batches':[{'id':'battle-final','frames':[0,4,5],'status':'visual_review_pass','review':'reviews/battle-v4-original-vs-new-dark.png'}],'source_semantics':{'0':'hooded robe with wide U fabric collar, arms concealed by sleeves','4':'arms raised unequally, robe continues hiding legs','5':'both arms project forward from wide sleeves'},'registration_basis':'visible continuous robe hem; no inferred pelvis, knees or feet','art_mode':'built-in imagegen; whole-image crop, uniform scale and translation only','runtime_integrated':False})

maps=UNIT/'maps';(maps/'frames').mkdir(exist_ok=True);(maps/'reviews').mkdir(exist_ok=True)
allrecords=[];scenarios=[]
for kind,fw,fh,aliases in [('walk',32,24,[0,1,0,1,0,1]),('idle',24,24,[0,1,2,1,0,1])]:
 out=maps/f'{kind}-frames';out.mkdir(exist_ok=True)
 rawp=maps/f'source/{kind}-v2-generated.png';raw=Image.open(rawp).convert('RGBA')
 records=[]
 for i in sorted(set(aliases)):
  native=Image.open(UNIT/f'reference/tactical-{kind}-{i:02}-native.png').convert('RGBA');nb=mask(native).getbbox()
  band=mask(native).crop((0,nb[3]-1,fw,nb[3])).getbbox();target=[2*(band[0]+band[2]),4*nb[3]]
  cell=(0,0,raw.width,raw.height) if kind=='walk' else (i*raw.width//3,0,(i+1)*raw.width//3,raw.height)
  art=raw.crop(cell);a=mask(art);b=a.getbbox();scale=4*(nb[3]-nb[1])/(b[3]-b[1])
  crop=(max(0,b[0]-3),max(0,b[1]-3),min(art.width,b[2]+3),min(art.height,b[3]+3))
  cut=maps/f'source/{kind}-cut-{i}.png';small=maps/f'source/{kind}-small-{i}.png'
  run(rawp,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut)
  args=[cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%']
  mirrored=kind=='walk' and i==1
  if mirrored:args+=['-flop']
  run(*args,small)
  sm=Image.open(small).convert('RGBA');ma=mask(sm);sb=ma.getbbox();hem=ma.crop((0,sb[3]-4,sm.width,sb[3])).getbbox();hx=(hem[0]+hem[2])/2
  tx=round(target[0]-hx);ty=target[1]-sb[3]
  dst=out/f'frame-{i:03}.png';run('-size',f'{fw*4}x{fh*4}','xc:none',small,'-geometry',f'{tx:+d}{ty:+d}','-compose','over','-composite',dst)
  subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(dst)],check=True,capture_output=True)
  records.append({'source_index':i,'source_frame':i,'representative_frame':i,'path':f'{kind}-frames/frame-{i:03}.png','output_path':f'{kind}-frames/frame-{i:03}.png','generated_source':f'source/{kind}-v2-generated.png','generated_cell':cell,'generated_content_bounds':b,'uniform_scale':scale,'registration_offset':[tx,ty],'target_visible_hem':target,'registered_visible_hem':[hx+tx,sb[3]+ty],'mirror_x':mirrored,'registration_basis':'visible robe hem; legs concealed','kind':'exact-source-mirror-derived' if mirrored else 'imagegen_from_native_pose',**info(dst)})
 base={r['source_index']:r for r in records};allslots=[]
 for i,alias in enumerate(aliases):
  r=dict(base[alias]);r['source_index']=r['source_frame']=i;r['representative_frame']=alias
  src=out/f'frame-{alias:03}.png';dst=out/f'frame-{i:03}.png'
  if src!=dst:shutil.copy2(src,dst)
  r['path']=r['output_path']=f'{kind}-frames/frame-{i:03}.png';allslots.append(r)
 atlas=maps/f'frames/tactical-{kind}.png';run(*[out/f'frame-{i:03}.png' for i in range(6)],'+append',atlas)
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(atlas)],check=True,capture_output=True)
 scenario={'id':f'tactical-{kind}','class_id':15,'source_side':'enemy','source_atlas':'../../../'+unit[f'map_{kind}_source'],'source_frame_size':[fw,fh],'source_anchor':[16,24] if kind=='walk' else [12,24],'output_frame_size':[fw*4,fh*4],'output_anchor':[64,96] if kind=='walk' else [48,96],'output_atlas':f'frames/tactical-{kind}.png','output_atlas_bytes':atlas.stat().st_size,'frame_mapping':allslots,'logical_render_scale':.25,'default_facing':'right'}
 if kind=='walk':scenario.update({'directions':{'down':[0,1],'up':[2,3],'right':[4,5],'left':[4,5]},'direction_mirror_x':{'left':True},'timing':{'native_fps':60.0988,'frame_ticks':16},'source_mirror_evidence':'Original slot1 tight RGBA equals exact horizontal mirror of slot0; new slot1 mirrors generated slot0 then independently registers the source hem. No invented extra limb phase.'})
 else:scenario.update({'static_facing':True,'directions':{'all':[0,1,2,1]},'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]}})
 scenarios.append(scenario);allrecords.extend(records)
 for color,label in [('#1d2932','dark'),('#eee8d8','light')]:
  originals=[]
  for i in range(len(base)):
   op=maps/f'source/{kind}-original4-{i}.png';run(UNIT/f'reference/tactical-{kind}-{i:02}-native.png','-filter','point','-resize','400%',op);originals.append(op)
  files=originals+[out/f'frame-{i:03}.png' for i in range(len(base))]
  board=maps/f'reviews/tactical-{kind}-{label}.png'
  run('montage','-font',FONT,*files,'-tile',f'{len(base)}x2','-geometry',f'{fw*4}x{fh*4}+20+10','-background',color,board)
  run(board,'-filter','point','-resize','300%',maps/f'reviews/tactical-{kind}-{label}-3x.png')
savej(maps/'frame_mapping.json',{'schema_version':1,'class_id':15,'source_side':'enemy','actor_id':'enemy-arcanist','character_id':'enemy-arcanist','display_name':'敌方妖术师','width_height_scale':4,'runtime_integrated':False,'art_mode':'built-in imagegen; ImageMagick technical crop, uniform scale, translation and proven source mirror only; oxipng lossless','status':'art_and_registration_verified','scenarios':scenarios})
savej(maps/'source/registration.json',allrecords)
print(json.dumps({'battle_frames':3,'map_unique_source_slots':5,'map_generated_drawings':4,'map_registered_records':allrecords},ensure_ascii=False))
