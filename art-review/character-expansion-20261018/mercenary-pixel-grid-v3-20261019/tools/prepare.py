from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,shutil,subprocess,hashlib
V=Path(__file__).resolve().parents[1];R=V.parent;G=R.parents[1]/'actual';REPORT=G/'reports/playtest-fixes-20261019'
MAG='/opt/homebrew/bin/magick'
def read(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def digest(im):
 b=bytearray(im.convert('RGBA').tobytes())
 for i in range(0,len(b),4):
  if not b[i+3]:b[i:i+3]=b'\0\0\0'
 return hashlib.sha256(b).hexdigest()
g=read(R/'demos/gallery-data.json');d=read(G/'data/reviewed_animations.json');before=json.loads(json.dumps(d));ref=V/'reference';ref.mkdir(exist_ok=True);(V/'reviews').mkdir(exist_ok=True)
if (ref/'gallery-before.json').exists():raise RuntimeError('Already prepared; retain reference snapshot')
shutil.copy2(R/'demos/gallery-data.json',ref/'gallery-before.json')
rows=[];inventory=[]
for cid,side in [('8','ally'),('8','enemy'),('14','ally')]:
 key=cid+'_'+side;p=next(p for p in g['profiles'] if p['id']==f'professions-class-{cid}-{side}-battle');mp=R/p['mapping'];m=read(mp);shutil.copy2(mp,ref/f'{key}-mapping.json');out=V/'deliverables'/key;out.mkdir(parents=True,exist_ok=True)
 slots=sorted(map(int,p['newFrames']));old=Image.new('RGBA',(320*len(slots),256))
 for i,n in enumerate(slots):
  im=Image.open(R/p['newFrames'][str(n)]).convert('RGBA');old.paste(im,(i*320,0))
 old.save(ref/f'{key}-atlas.png',optimize=True)
 # 2x2 clusters, binary alpha and a fixed shared palette. Nearest sampling
 # preserves strong light/dark separation rather than blending outlines.
 palettes={'8_ally':['1b1e2a','342331','5d3649','4b3128','885737','bf825b','efbf90','feccc5','e7d4a7','90754c','b3975f','35333c','596776','c3cbd0'],'8_enemy':['1c2135','26334f','3e5074','5a6b8f','343552','5c5d95','8b86bf','49362c','8a6041','c08c62','efbd8b','f2d3a4','bcc0d6','e4dcca'],'14_ally':['1d202b','493025','7d4e2e','b17b43','b87950','e4ac77','f3d3a0','8b7867','cdbba2','f2e3c6','2a3444','516072','b04e25','d8ded8']}
 pal=Image.new('RGBA',(15,1));pal.putdata([(0,0,0,0)]+[tuple(bytes.fromhex(x))+(255,) for x in palettes[key]]);pal.save(out/'palette.png')
 subprocess.run([MAG,str(ref/f'{key}-atlas.png'),'-filter','point','-resize','50%','-channel','A','-threshold','50%','+channel','+dither','-remap',str(out/'palette.png'),'-filter','point','-resize','200%','PNG32:'+str(out/'battle-atlas.png')],check=True)
 atlas=Image.open(out/'battle-atlas.png').convert('RGBA');assert atlas.size==old.size
 assert set(atlas.getchannel('A').getdata())=={0,255}
 colors={c for c in atlas.getdata() if c[3]};assert len(colors)<=14
 art=d['battle'][key];target=G/art['path'].removeprefix('res://');shutil.copy2(target,REPORT/'before'/target.name)
 packed=Image.new('RGBA',Image.open(target).size);frame_hashes={};oldmeta=[]
 for i,n in enumerate(slots):
  im=atlas.crop((i*320,0,(i+1)*320,256));im.save(out/f'frame-{n:03d}.png',optimize=True);packed.paste(im,(n%art['columns']*320,n//art['columns']*256));frame_hashes[str(n)]=digest(im)
  previous=old.crop((i*320,0,(i+1)*320,256));ob=previous.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox();nb=im.getbbox();assert nb and max(abs(a-b) for a,b in zip(ob,nb))<=2
  oldmeta.append({'source_frame':n,'path':f'../../../{V.name}/deliverables/{key}/frame-{n:03d}.png','old_bounds':ob,'new_bounds':nb,'grid_4x_pixels':2,'palette_size':len(colors)})
 packed.save(target,optimize=True);art['art_revision']=V.name
 base=f'../../../{V.name}/deliverables/{key}/';m.update(revision=V.name,frame_mapping={str(n):base+f'frame-{n:03d}.png' for n in slots},records=oldmeta,output_atlas=base+'battle-atlas.png',output_atlas_frame_order=slots,status='runtime_integrated_for_device_review',runtime_integrated=True,qa_report=f'../../../{V.name}/verification.json',art_review='Pixel density correction requested by user; device review pending.',review_note='战斗角色统一2×2四倍画布像素块，移除细碎半透明像素，每组全部姿势共用至多14种不透明颜色。保留服装、身高、脚底、动作与刀光/雷电结算。含截图中的首关流民战斗形象。地图形象保持。已接入0.8.12测试包。',batches=[{'id':'枪兵与像素颗粒对照','review':f'../../../{V.name}/reviews/density-comparison-dark.png'}],runtime_integration={'version':'0.8.12','device_review_pending':True})
 save(mp,m)
 item={'profile':p['id'],'key':key,'revision':V.name,'path':art['path'],'frame_size':[320,256],'size':list(packed.size),'frame_hashes':frame_hashes,'effect_aliases':{},'effects':[],'attack_variants':len(art['reviewed_variants'])};inventory.append(item)
 rows.append({'key':key,'opaque_palette':sorted('#%02x%02x%02x'%c[:3] for c in colors),'grid_4x_pixels':2,'frames':oldmeta})
for section in ['maps','map_revisions','variants','sprites']:assert d[section]==before[section]
(G/'data/reviewed_animations.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
for p in [*V.joinpath('deliverables').rglob('*.png'),*(G/i['path'].removeprefix('res://') for i in inventory)]:subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
save(REPORT/'art-import.json',{'version':'0.8.12','inventory':inventory,'body_profiles':3,'source_frame_slots_checked':sum(len(i['frame_hashes']) for i in inventory),'source_attack_variants':sum(i['attack_variants'] for i in inventory),'scoped_arrow_textures':0})
save(V/'registration.json',{'revision':V.name,'rows':rows,'native_density':4,'pixel_cluster_native_size':.5,'all_timelines_effects_and_map_art_unchanged':True})
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for name,bg,fg in [('dark','#202d35','#e9f0f0'),('light','#dcded8','#27323c')]:
 canvas=Image.new('RGBA',(960,864),bg);draw=ImageDraw.Draw(canvas)
 for row,(cid,side,slot) in enumerate([('8','ally',15),('8','enemy',15),('14','ally',16)]):
  profile=next(p for p in g['profiles'] if p['id']==f'professions-class-{cid}-{side}-battle');gun=next(p for p in g['profiles'] if p['id']==f'professions-class-6-{side}-battle');oldim=Image.open(R/profile['newFrames'][str(slot)]).convert('RGBA');newim=Image.open(V/f'deliverables/{cid}_{side}/frame-{slot:03d}.png').convert('RGBA');gunim=Image.open(R/gun['newFrames']['12' if side=='ally' else '19']).convert('RGBA')
  for col,(im,label) in enumerate([(gunim,'枪兵参考'),(oldim,'流民' if cid=='14' else '佣兵'),(newim,'像素颗粒修正')]):
   box=im.getbbox();offset=160-(box[0]+box[2])//2;canvas.alpha_composite(im,(col*320+offset,row*288+30));draw.text((col*320+160,row*288+8),label,font=font,fill=fg,anchor='mt')
 canvas.convert('RGB').save(V/f'reviews/density-comparison-{name}.png',optimize=True)
print({'frames':sum(len(i['frame_hashes']) for i in inventory),'variants':sum(i['attack_variants'] for i in inventory),'profiles':3})
