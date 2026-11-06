"""Add own class-6 enemy throwing poses without changing any existing frame slot."""
from pathlib import Path
import copy
import json
import subprocess
import tempfile
import zlib
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
GAME=ROOT/'actual'
SOURCE=ROOT/'source/ranged-counter-20261029'
OUT=GAME/'assets/ranged-counter-20261029'
OUT.mkdir(parents=True,exist_ok=True)
MAGICK='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([MAGICK,*map(str,args)],check=True)
def variant(group,key):
    index=json.loads((GAME/f'data/animation_runtime/{group}.json').read_text())['variants'][key]
    with (GAME/f'data/animation_runtime/{group}.bin').open('rb') as stream:
        stream.seek(index[0]);return json.loads(zlib.decompress(stream.read(index[1])))
meta=json.loads((GAME/'data/animation_runtime/reviewed.json').read_text())['metadata']
original=meta['battle']['6_enemy']
source=SOURCE/'spearman-throw-source.png'
with Image.open(source) as im:w,h=im.size
measurements=[]
with tempfile.TemporaryDirectory(prefix='counter-art-') as folder:
    frames=[]
    for n in range(4):
        raw=Path(folder)/f'raw-{n}.png';body=Path(folder)/f'body-{n}.png';frame=OUT/f'throw-{n}.png'
        x0,x1=round(n%2*w/2),round((n%2+1)*w/2);y0,y1=round(n//2*h/2),round((n//2+1)*h/2)
        # The first handle ends slightly past the generated center line;
        # retain it intact and exclude that tip from the second cell.
        if n==0:x1+=24
        elif n==1:x0+=24
        run(source,'-crop',f'{x1-x0}x{y1-y0}+{x0}+{y0}','+repage','-channel','A','-threshold','25%','+channel',raw)
        with Image.open(raw) as im:
            left,top,right,bottom=im.getchannel('A').getbbox()
        # Head-to-heel scale matches the existing 128px-high soldier. The
        # overhead javelin remains above the head with its natural proportions.
        head_top=[155,148,119,118][n]*h/1124
        scale=128/(bottom-head_top)
        run(raw,'-crop',f'{right-left}x{bottom-top}+{left}+{top}','+repage','-resize',f'{round((right-left)*scale)}x{round((bottom-top)*scale)}!',body)
        with Image.open(body) as im:
            a=im.getchannel('A');bw,bh=im.size
            feet=[x for y in range(bh-5,bh) for x in range(bw) if a.getpixel((x,y))>=160]
            foot_x=(min(feet)+max(feet))/2
        x,y=round(160-foot_x),256-bh
        assert x>=0 and x+bw<=320 and y>=0
        run('-size','320x256','canvas:none',body,'-geometry',f'+{x}+{y}','-composite',frame)
        subprocess.run(['/opt/homebrew/bin/pngquant','--quality=90-100','--nofs','--force','--output',str(frame),str(frame)],check=True)
        subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(frame)],check=True)
        frames.append(frame);measurements.append({'pose':n,'path':str(frame.relative_to(ROOT)),'dimensions':[320,256],'bytes':frame.stat().st_size,'head_to_heel':128,'foot_anchor':[160,256]})
    target=OUT/'spearman-enemy-javelin.png'
    # Original atlas has 16 columns and 27 slots. Slots 27–30 are new only.
    args=[GAME/original['path'][6:]]
    for n,frame in enumerate(frames):args.extend([frame,'-geometry',f'+{(27+n)%16*320}+{(27+n)//16*256}','-composite'])
    run(*args,target)
    subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(target)],check=True)
sprite=copy.deepcopy(original)
sprite.update(path='res://'+str(target.relative_to(GAME)),frames=31,counter_javelin=True,art_revision='spearman-enemy-javelin-20261029')
programs={}
for suffix in ['', '_vs_heavy','_far_ally','_far_ally_vs_heavy','_far_enemy','_far_enemy_vs_heavy']:
    key='class_6_enemy_javelin'+suffix;program=variant('legacy',key)
    for tick,frame in enumerate(program['frames']):
        frame['frame']=19 if tick<7 or tick>=68 else 27 if tick<14 else 28 if tick<21 else 29 if tick<40 else 30
        frame['background']=False
        for effect in frame.get('effects',[]):effect['sprite']='character-sync-f6d150fc0fb7ba04b2cf'
    program['art_revision']='spearman-enemy-javelin-20261029'
    programs[key]=program
(GAME/'data/counter_animation_20261029.json').write_text(json.dumps({'sprite':sprite,'variants':programs},ensure_ascii=False,separators=(',',':'))+'\n')
manifest={'new_poses':measurements,'atlas':{'path':str(target.relative_to(ROOT)),'dimensions':list(Image.open(target).size),'bytes':target.stat().st_size,'quality_reason':'Existing approved ordinary/reaction slots preserved pixel-for-pixel; four own throwing poses appended. Atlas is a shared animation sheet.'},'source':'built-in imagegen','source_file':str(source.relative_to(ROOT)),'contact_policy':'Original six javelin timelines, projectile path and one contact tick retained; own drawn throw/release/recovery replaces missing body frames.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False))
