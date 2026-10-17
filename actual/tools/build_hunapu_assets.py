#!/usr/bin/env python3
"""Register generated sprites into the existing native cells; no new motion."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'source/hunapu-0.5.1'
OUT=ROOT/'assets/hunapu-0.5.1'
REPORT=ROOT/'reports/hunapu-0.5.1'
contract=json.loads((SOURCE/'contract.json').read_text())
graphics=json.loads((ROOT/'data/legacy/graphics.json').read_text())
colors=[tuple(bytes.fromhex(c[1:])) for c in contract['palette'].values()]
palette=Image.new('P',(1,1));palette.putpalette([v for c in (colors+[colors[0]]*(256-len(colors)))for v in c])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def reduce(im):
    im=im.convert('RGBA');alpha=im.getchannel('A').point(lambda a:255 if a>=128 else 0)
    im=im.convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE).convert('RGBA');im.putalpha(alpha)
    return im
def sprite(path,size,box,contain=False):
    im=Image.open(path).convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:255 if a>=128 else 0))
    bounds=im.getbbox();assert bounds, path
    im=im.crop(bounds);w,h=box[2]-box[0],box[3]-box[1]
    if contain:
        factor=min(w/im.width,h/im.height);im=im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.NEAREST)
        at=(box[0]+(w-im.width)//2,box[3]-im.height)
    else:im=im.resize((w,h),Image.Resampling.NEAREST);at=box[:2]
    result=Image.new('RGBA',size);result.alpha_composite(reduce(im),at)
    return result
def save(im,path):
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
    subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(path)],check=True)
def plate(cells,columns,scale=5):
    fw=max(c.width for _,c in cells);fh=max(c.height for _,c in cells)
    im=Image.new('RGB',(columns*(fw*scale+8),((len(cells)+columns-1)//columns)*(fh*scale+24)),(43,58,66));draw=ImageDraw.Draw(im)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',11)
    for i,(label,c) in enumerate(cells):
        x=(i%columns)*(fw*scale+8);y=(i//columns)*(fh*scale+24)
        image=c.resize((c.width*scale,c.height*scale),Image.Resampling.NEAREST)
        im.paste(image,(x,y),image);draw.text((x+4,y+fh*scale+2),label,fill='white',font=font)
    return im
REPORT.mkdir(parents=True,exist_ok=True)
maps=[];hubs=[];source_ids=['map-0','hub-1','hub-2','hub-3','hub-4','hub-5']
for i,key in enumerate(source_ids):
    path=SOURCE/(key+'.png');assert path.exists(),path
    maps.append(sprite(path,(24,24),(4,4,20,20),True));hubs.append(sprite(path,(32,24),(8,8,24,24),True))
save(plate([(str(i),im)for i,im in enumerate(maps)],3,7),REPORT/'map-design.png')
save(plate([(str(i),im)for i,im in enumerate(hubs)],3,7),REPORT/'hub-design.png')
if '--preview' in sys.argv:
    print('12-color map/hub design preview only');sys.exit(0)
required=list(range(8))+[9]+list(range(120,124))
missing=[f for f in required if not (SOURCE/f'battle-{f}.png').exists()]
assert not missing, f'Generated battle poses missing: {missing}'
original=Image.open(ROOT/'assets/original/graphics/battle/class_21_ally.png').convert('RGBA')
sheet=reduce(original);frames={}
for f in required:
    old=original.crop((f*80,0,(f+1)*80,72));box=old.getbbox()
    frames[f]=sprite(SOURCE/f'battle-{f}.png',(80,72),box)
frames[60]=frames[0].copy()
frames[8]=frames[9].copy();old8=original.crop((8*80,0,9*80,72));old9=original.crop((9*80,0,10*80,72));trail=0
for y in range(72):
    for x in range(80):
        if old8.getpixel((x,y))[3] and not old9.getpixel((x,y))[3]:frames[8].putpixel((x,y),(*colors[11],255));trail+=1
assert trail==97,'Source slash trail contract changed'
# The original Levin program temporarily shows only the ascending blade.
effect=original.crop((124*80,0,125*80,72));frames[124]=Image.new('RGBA',(80,72))
for y in range(72):
    for x in range(80):
        if effect.getpixel((x,y))[3]:frames[124].putpixel((x,y),(*colors[11],255))
for f,im in frames.items():
    sheet.paste(im,(f*80,0));save(im,OUT/'frames'/f'battle-{f}.png')
save(sheet,OUT/'battle.png')
for kind,cells,fw in [('map',maps,24),('hub',hubs,32)]:
    sheet=Image.new('RGBA',(fw*6,24))
    for i,im in enumerate(cells):sheet.alpha_composite(im,(i*fw,0));save(im,OUT/'frames'/f'{kind}-{i}.png')
    save(sheet,OUT/(kind+'.png'))
data={'version':'0.5.1','identity':'hunapu','palette':contract['palette'],'max_opaque_colors':12,'active_battle_frames':sorted(frames),'source_timeline_sha256':contract['timeline_sha256'],'source_contact_tick':len(contract['timeline']['before_contact']),'source_slash_trail_pixels':97,'registration':'Native source bounding boxes and foot baselines retained; town/map use fixed cell foot anchors, nearest-neighbour only. The retained original slash and Levin blade are visual source effects, not extra strikes.','map':dict(graphics['map_units']['class_21_ally'],path='res://assets/hunapu-0.5.1/map.png'),'hub':dict(graphics['village_sprites']['1'],path='res://assets/hunapu-0.5.1/hub.png'),'battle':{'path':'res://assets/hunapu-0.5.1/battle.png','frame_size':[80,72],'anchor':[40,64],'frames':133}}
data['map'].pop('acted_variant',None)
write(ROOT/'data/hunapu_visuals.json',data)
save(plate([(str(f),frames[f])for f in sorted(frames)if f!=60],4,4),REPORT/'battle-design.png')
records=[]
for p in sorted(OUT.rglob('*.png')):
    im=Image.open(p).convert('RGBA');visible={c[:3]for c in im.getdata()if c[3]};assert visible<=set(colors),(p,visible-set(colors));assert {c[3]for c in im.getdata()}<={0,255}
    records.append({'path':str(p.relative_to(ROOT)),'width':im.width,'height':im.height,'bytes':p.stat().st_size,'colors':len(visible),'sha256':sha(p),'purpose':'personal Hunapu native animation asset'})
write(REPORT/'asset-manifest.json',records)
write(REPORT/'source-contract.json',{'timeline_sha256':contract['timeline_sha256'],'contact_tick':len(contract['timeline']['before_contact']),'before_ticks':85,'after_ticks':104,'native_fps':60.0988,'motion_changed':False,'contact_count_changed':False,'source_slash_pixels':97,'mapped_frames':sorted(frames),'other_actors_changed':False})
print('Built native Hunapu profile:',len(frames),'battle poses, six map/hub frames, twelve opaque colors')
