"""Whole-image registration of generated native tactical poses; no inferred limbs."""
from pathlib import Path
from PIL import Image
import json,subprocess,hashlib
M=Path(__file__).resolve().parents[1];G='/opt/homebrew/bin/magick';O=M/'tactical-native-frames';O.mkdir(exist_ok=True)
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def mask(i):return i.convert('RGBA').getchannel('A').point(lambda a:255 if a>=32 else 0)
recs=[]
right='native-right-collar-v2-generated.png'
if not (M/'source'/right).exists():right='native-right-v1-generated.png'
for f,tag,slot,n in [(0,'native-up-back-v2-generated.png',0,2),(1,'native-up-back-v2-generated.png',1,2),(2,right,0,2),(3,right,1,2),(5,'native-down1-v1-generated.png',0,1)]:
 p=M/'source'/tag;raw=Image.open(p).convert('RGBA');cell=[raw.width*slot//n,0,raw.width*(slot+1)//n,raw.height];im=raw.crop(cell);a=mask(im);b=a.getbbox();scale=64/(b[3]-b[1]);crop=[max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3)]
 cut=M/f'source/native-cut-{f:03}.png';small=M/f'source/native-small-{f:03}.png';run(p,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');sa=mask(sm);sb=sa.getbbox();hem=sa.crop((0,sb[3]-3,sm.width,sb[3])).getbbox();hx=(hem[0]+hem[2])/2;target=[60 if f in [2,3]else 62,96];dx=round(target[0]-hx);dy=96-sb[3]
 out=O/f'frame-{f:03}.png';run('-size','128x96','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',out)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<128 and 0<=y+dy<96)]
 recs.append({'source_index':f,'source_frame':f,'path':f'tactical-native-frames/frame-{f:03}.png','output_path':f'tactical-native-frames/frame-{f:03}.png','raw':f'source/{tag}','cell':cell,'crop':crop,'uniform_scale':scale,'translation':[dx,dy],'target_hem_anchor':target,'registered_hem_anchor':[hx+dx,96],'visible_clipped_pixels_alpha32':sum(a>=32 for a in outside),'outside_nonzero_alpha_pixels':sum(a>0 for a in outside),'registration_basis':'Visible robe hem; no inferred hidden hips, knees or feet. All in-canvas generated alpha retained.'})
# Source slot4 is byte-exact static idle0 translated [+4,+4] native pixels.
run('-size','128x96','xc:none',M/'idle-frames/frame-000.png','-geometry','+16+16','-compose','over','-composite',O/'frame-004.png')
recs.append({'source_index':4,'source_frame':4,'path':'tactical-native-frames/frame-004.png','output_path':'tactical-native-frames/frame-004.png','kind':'verified_static_idle_reuse','input':'idle-frames/frame-000.png','translation':[16,16],'proof':'native-reference/source-record.json'})
for f,src in [(6,2),(7,3)]:
 run(O/f'frame-{src:03}.png','-flop',O/f'frame-{f:03}.png');recs.append({'source_index':f,'source_frame':f,'path':f'tactical-native-frames/frame-{f:03}.png','output_path':f'tactical-native-frames/frame-{f:03}.png','kind':'exact_full_canvas_mirror','representative_frame':src,'proof':'native-reference/source-record.json'})
for r in recs:
 p=M/r['path'];subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe',str(p)],capture_output=True,check=True);im=Image.open(p);r.update({'size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'visible_bounds':mask(im).getbbox()})
(M/'tactical-native-registration.json').write_text(json.dumps(sorted(recs,key=lambda r:r['source_index']),indent=2)+'\n')
run(*[O/f'frame-{f:03}.png'for f in range(8)],'+append',M/'frames/tactical-native-walk.png')
for f in range(8):run(M/f'native-reference/frame-{f:03}.png','-filter','point','-resize','400%',O/f'source4-{f:03}.png')
for c,l in [('#1d2932','dark'),('#eee8d8','light')]:
 run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'source4-{f:03}.png'for f in range(8)],*[O/f'frame-{f:03}.png'for f in range(8)],'-tile','8x2','-geometry','128x96+8+8','-background',c,M/f'reviews/native-walk-{l}.png')
print(json.dumps({'drawings':5,'static_reuse':1,'mirrors':2,'clipped_visible':sum(r.get('visible_clipped_pixels_alpha32',0)for r in recs)}))
