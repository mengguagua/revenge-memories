"""Technical crop/uniform registration and proven mirror; no sprite painting."""
from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib,shutil,subprocess
P=Path(__file__).resolve().parents[1];D=P/'maps';M='/opt/homebrew/bin/magick';F='/System/Library/Fonts/STHeiti Medium.ttc'
def run(*a):subprocess.run([M,*map(str,a)],check=True)
def mask(im):return im.convert('RGBA').getchannel('A').point(lambda a:255 if a>=32 else 0)
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def info(p):
 im=Image.open(p);return {'size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'visible_bounds':mask(im).getbbox()}
def tight(im):return im.crop(im.getchannel('A').getbbox())
unit=json.loads((P/'reference/source-unit.json').read_text());scenarios=[];allrec=[];proof=[]
for kind,fw,aliases in [('walk',32,[0,1,0,1,4,5]),('idle',24,[0,1,2,1,0,1])]:
 out=D/f'{kind}-frames';out.mkdir(exist_ok=True);(D/'frames').mkdir(exist_ok=True);(D/'reviews').mkdir(exist_ok=True)
 base={}
 for i in sorted(set(aliases)):
  native=Image.open(P/f'reference/map-{kind}-{i:02}-native.png').convert('RGBA');nb=mask(native).getbbox()
  if kind=='walk' and i in [4,5]:
   original=Image.open(P/f'reference/map-walk-{i-4:02}-native.png').convert('RGBA')
   ok=tight(original).transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==tight(native).tobytes()
   assert ok
   im=Image.open(out/f'frame-{i-4:03}.png').convert('RGBA');sourcebounds=mask(original).getbbox();destbounds=nb
   # Full frame mirror about native x=16 is exact for these source pairs.
   assert original.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==native.tobytes()
   dst=out/f'frame-{i:03}.png';im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(dst)
   r={**base[i-4],'source_index':i,'source_frame':i,'representative_frame':i,'path':f'{kind}-frames/frame-{i:03}.png','output_path':f'{kind}-frames/frame-{i:03}.png','kind':'exact_source_full_frame_mirror','mirror_x':True,'mirror_of':i-4,**info(dst)}
   proof.append({'from':i-4,'to':i,'native_full_frame_RGBA_mirror_exact':True,'new_full_frame_RGBA_mirror_exact':True});base[i]=r;continue
  if kind=='idle':rawp=D/'source/idle-v1-generated.png';cell=[i*724,0,(i+1)*724,724];target=[[62,80],[52,80],[42,80]][i]
  else:rawp=D/'source/walk-clean-v2-generated.png';cell=[i*1024,0,(i+1)*1024,768];target=[70,96] if i==0 else [64,92]
  raw=Image.open(rawp).convert('RGBA');art=raw.crop(cell);b=mask(art).getbbox();scale=(nb[3]-nb[1])*4/(b[3]-b[1])
  crop=[max(0,b[0]-3),max(0,b[1]-3),min(art.width,b[2]+3),min(art.height,b[3]+3)]
  cut=D/f'source/{kind}-cut-{i}.png';small=D/f'source/{kind}-small-{i}.png'
  run(rawp,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut)
  run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
  sm=Image.open(small).convert('RGBA');ma=mask(sm);sb=ma.getbbox();foot=ma.crop((0,sb[3]-3,sm.width,sb[3])).getbbox();fx=(foot[0]+foot[2])/2
  tx=round(target[0]-fx);ty=target[1]-sb[3];dst=out/f'frame-{i:03}.png'
  run('-size',f'{fw*4}x96','xc:none',small,'-geometry',f'{tx:+d}{ty:+d}','-compose','over','-composite',dst)
  subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(dst)],check=True,capture_output=True)
  lost=sum(1 for y in range(sm.height)for x in range(sm.width)if not(0<=x+tx<fw*4 and 0<=y+ty<96)and sm.getpixel((x,y))[3]>=32)
  base[i]={'source_index':i,'source_frame':i,'representative_frame':i,'path':f'{kind}-frames/frame-{i:03}.png','output_path':f'{kind}-frames/frame-{i:03}.png','kind':'imagegen_native_pose','generated_source':str(rawp.relative_to(D)),'generated_cell':cell,'uniform_scale':scale,'registration_offset':[tx,ty],'target_visible_hoof_anchor':target,'registered_visible_hoof_anchor':[fx+tx,sb[3]+ty],'registration_basis':'continuous visible horse legs; idle0 grounded hind, idle1 both pairs, idle2 grounded front; shadow/lance excluded','visible_clipped_pixels':lost,'mirror_x':False,**info(dst)}
 rec=[]
 for i,a in enumerate(aliases):
  r={**base[a],'source_index':i,'source_frame':i,'representative_frame':a};dst=out/f'frame-{i:03}.png'
  if i!=a:shutil.copy2(out/f'frame-{a:03}.png',dst)
  r['path']=r['output_path']=f'{kind}-frames/frame-{i:03}.png';rec.append(r)
 atlas=D/f'frames/tactical-{kind}.png';run(*[out/f'frame-{i:03}.png'for i in range(6)],'+append',atlas)
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(atlas)],check=True,capture_output=True)
 sc={'id':f'tactical-{kind}','class_id':1,'source_side':'ally','source_atlas':'../../../'+unit[f'map_{kind}_source'],'source_frame_size':[fw,24],'source_anchor':[fw//2,24],'output_frame_size':[fw*4,96],'output_anchor':[fw*2,96],'output_atlas':f'frames/tactical-{kind}.png','output_atlas_bytes':atlas.stat().st_size,'frame_mapping':rec,'logical_render_scale':.25,'default_facing':'right'}
 if kind=='walk':sc.update(directions={'down':[0,1],'up':[2,3],'right':[4,5],'left':[4,5]},direction_mirror_x={'left':True},timing={'native_fps':60.0988,'frame_ticks':16},source_mirror_evidence=proof)
 else:sc.update(static_facing=True,directions={'all':[0,1,2,1]},timing={'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]})
 scenarios.append(sc);allrec.extend(rec)
 inds=sorted(base)
 for i in inds:run(P/f'reference/map-{kind}-{i:02}-native.png','-filter','point','-resize','400%',D/f'source/{kind}-original4-{i}.png')
 for color,label in [('#1d2932','dark'),('#eee8d8','light')]:
  review=D/f'reviews/{kind}-{label}.png';run('montage','-font',F,*[D/f'source/{kind}-original4-{i}.png'for i in inds],*[out/f'frame-{i:03}.png'for i in inds],'-tile',f'{len(inds)}x2','-geometry',f'{fw*4}x96+12+8','-background',color,review)
  run(review,'-filter','point','-resize','300%',D/f'reviews/{kind}-{label}-3x.png')
save(D/'frame_mapping.json',{'schema_version':1,'class_id':1,'source_side':'ally','actor_id':'ally-cavalry','character_id':'ally-cavalry','display_name':'盟军骑兵','width_height_scale':4,'runtime_integrated':False,'status':'pending_final_visual_review','art_mode':'built-in ImageGen; crop, uniform scale, translation, exact-source mirror, lossless compression only','scenarios':scenarios})
save(D/'source/registration.json',allrec);save(D/'source/mirror-proof.json',proof)
print(json.dumps({'source_slots':len(allrec),'drawings':5,'clipped':sum(r.get('visible_clipped_pixels',0)for r in allrec),'proof':proof}))
