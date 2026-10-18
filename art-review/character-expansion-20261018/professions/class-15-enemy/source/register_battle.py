"""Technical extraction/whole-image registration of ImageGen artwork only."""
from pathlib import Path
import json
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAGICK = '/opt/homebrew/bin/magick'
RAW = ROOT/'source/battle-v1-generated.png'
VERSION = 'v4' if '--pose4-v4' in sys.argv else ('v2' if '--pose4-v2' in sys.argv else 'v1')
V2 = VERSION != 'v1'
TAG = VERSION
OUT = ROOT/f'battle/candidate-{TAG}'
OUT.mkdir(parents=True,exist_ok=True)


def alpha(im):
    return im.convert('RGBA').getchannel('A').point(lambda p:255 if p>=32 else 0)


def run(*args):
    subprocess.run([MAGICK,*map(str,args)],check=True)


records=[]
raw=Image.open(RAW).convert('RGBA')
for frame,cell,hood_top in [(0,(0,0,570,878),276),(4,(570,0,1155,878),286),(5,(1155,0,1790,878),302)]:
    art_file = RAW
    if V2 and frame==4:
        art_file=ROOT/f'source/battle-pose004-{VERSION}-generated.png'
        edited=Image.open(art_file).convert('RGBA')
        cell=(0,0,edited.width,edited.height)
        hood_top=488
        art=edited
    else:
        art=raw.crop(cell)
    mask=alpha(art);b=mask.getbbox()
    source=Image.open(ROOT/'reference'/f'original-battle-{frame:03}.png').convert('RGBA')
    sm=alpha(source);sb=sm.getbbox()
    # Robe occludes the feet: register the visible robe hem, never inferred knees/hips.
    source_band=sm.crop((0,sb[3]-4,source.width,sb[3])).getbbox()
    target_x=(source_band[0]+source_band[2])/2;target_y=sb[3]
    body_height=128
    scale=body_height/(b[3]-hood_top)
    hem_depth=max(1,round(4/scale))
    hem=mask.crop((0,b[3]-hem_depth,art.width,b[3])).getbbox()
    hem_x=(hem[0]+hem[2])/2
    crop=(max(0,b[0]-3),max(0,b[1]-3),min(art.width,b[2]+3),min(art.height,b[3]+3))
    global_crop=(crop[0]+cell[0],crop[1],crop[2]+cell[0],crop[3])
    cut=OUT/f'crop-{frame:03}.png';resized=OUT/f'resized-{frame:03}.png';dst=OUT/f'frame-{frame:03}.png'
    run(art_file,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{global_crop[0]}+{global_crop[1]}','+repage',cut)
    run(cut,'-filter','Lanczos','-resize',f'{scale*100:.10f}%',resized)
    scaled=Image.open(resized).convert('RGBA');rw,rh=scaled.size
    sx=rw/(crop[2]-crop[0]);sy=rh/(crop[3]-crop[1])
    scaled_mask=alpha(scaled);scaled_bounds=scaled_mask.getbbox()
    scaled_hem=scaled_mask.crop((0,scaled_bounds[3]-4,rw,scaled_bounds[3])).getbbox()
    x=round(target_x-(scaled_hem[0]+scaled_hem[2])/2);y=round(target_y-scaled_bounds[3])
    run('-size','320x256','xc:none',resized,'-geometry',f'{x:+d}{y:+d}','-compose','over','-composite',dst)
    records.append({'frame':frame,'raw':str(art_file.relative_to(ROOT)),'cell':cell,'content_bounds':b,'hood_top':hood_top,'uniform_scale':scale,'crop_global':global_crop,'resampled_size':[rw,rh],'translation':[x,y],'target_visible_hem':[target_x,target_y],'registration_basis':'visible robe hem; legs hidden by robe','status':'candidate_review'})
(OUT/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
review=ROOT/'battle/reviews';review.mkdir(parents=True,exist_ok=True)
for color,name in [('#1d2932','dark'),('#eee8d8','light')]:
    files=[ROOT/'reference'/f'original-battle-{i:03}.png'for i in [0,4,5]]+[OUT/f'frame-{i:03}.png'for i in [0,4,5]]
    run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*files,'-tile','3x2','-geometry','320x256+0+8','-background',color,review/f'battle-{TAG}-original-vs-new-{name}.png')
print(json.dumps(records,ensure_ascii=False))
