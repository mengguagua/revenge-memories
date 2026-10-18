#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
R=Path(__file__).resolve().parents[1]; M=R/'maps'
spec=[]
for d,raw,heads,targets in [('up','up-v1.png',[189,193],[58,66]),('right','right-v2.png',[213,215],[70,42]),('down','down-v2.png',[193,194],[70,54]),('left','left-v2.png',[205,212],[86,58])]:
    n=['up','right','down','left'].index(d)*2
    for phase in range(2):
        spec.append({'slot':n+phase,'kind':'walk','raw':raw,'crop':[887*phase,0,887*(phase+1),887], 'head_y':heads[phase], 'target_head_y':32,'target_body_anchor':[targets[phase],96]})
for f in range(3):
    spec.append({'slot':f,'kind':'idle','raw':'idle-v2.png','crop':[661*f,0,661*(f+1) if f<2 else 1984,793],'head_y':143,'target_head_y':16,'target_body_anchor':[48,80]})
for slot,head in [(3,306),(6,277),(5,274)]:
    version=4 if slot==5 else 3
    size=Image.open(M/f'source/native-{slot:03d}-v{version}.png').size
    spec[slot].update({'raw':f'native-{slot:03d}-v{version}.png','crop':[0,0,*size],'head_y':head})
records=[]
for s in spec:
    im=Image.open(M/'source'/s['raw']).convert('RGBA').crop(s['crop']); im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a))
    bbox=im.getbbox(); bottom=bbox[3]
    if s['kind']=='walk':
        # Visually identified lowest supporting boot. No blade or cloth centering.
        a=im.getchannel('A'); xs=[x for x in range(im.width) if any(a.getpixel((x,y)) for y in range(bottom-8,bottom))]
        ax=(min(xs)+max(xs)+1)/2
    else:
        a=im.getchannel('A'); xs=[x for x in range(im.width) if any(a.getpixel((x,y)) for y in range(bottom-64,bottom))]
        groups=[]
        for x in xs:
            if not groups or x>groups[-1][-1]+1:groups.append([x])
            else:groups[-1].append(x)
        groups=[g for g in groups if len(g)>8]
        assert len(groups)==2,(s['slot'],groups)
        ax=sum((g[0]+g[-1]+1)/2 for g in groups)/2
    ay=bottom
    scale=(s['target_body_anchor'][1]-s['target_head_y'])/(ay-s['head_y'])
    size=[round(v*scale) for v in im.size]; small=im.resize(size,Image.Resampling.NEAREST)
    xy=[round(s['target_body_anchor'][0]-ax*scale),round(s['target_body_anchor'][1]-ay*scale)]
    out=Image.new('RGBA',(128,96) if s['kind']=='walk' else(96,96));out.alpha_composite(small,xy)
    name=f'tactical-native-frames/frame-{s["slot"]:03d}.png' if s['kind']=='walk' else f'frames/idle-{s["slot"]:03d}.png';out.save(M/name)
    records.append({**s,'raw_selected_anchor':[ax+s['crop'][0],ay],'scale':scale,'resized_size':size,'paste':xy,'alpha_bounds':out.getbbox(),'anchor_basis':'Visually selected lowest support boot or paired idle boots. Excludes sword, cloth tips and original ground projection. Accuracy applies only to chosen registration point, not every foot/joint.'})
walk=Image.new('RGBA',(1024,96))
for f in range(8):walk.alpha_composite(Image.open(M/f'tactical-native-frames/frame-{f:03d}.png'),(f*128,0))
walk.save(M/'frames/tactical-native-walk.png')
idle=Image.new('RGBA',(576,96))
for f,c in enumerate([0,1,2,1,0,1]):
    im=Image.open(M/f'frames/idle-{c:03d}.png');im.save(M/f'frames/idle-{f:03d}.png');idle.alpha_composite(im,(96*f,0))
idle.save(M/'deliverables/tactical-idle.png')
(M/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
    fg=(235,242,244) if theme=='dark' else(34,43,47)
    board=Image.new('RGBA',(1248,384),bg+(255,));dr=ImageDraw.Draw(board);dr.text((24,16),'原作校正：上0 / 上1 / 右0 / 右1 / 下0 / 下1 / 左0 / 左1',font=font,fill=fg);dr.text((24,194),'佣兵 · 八个独立原生步相（左右不镜像）',font=font,fill=fg)
    original=Image.open(M/'reference/tactical-native-original.png').convert('RGBA')
    for f in range(8):board.alpha_composite(original.crop((32*f,0,32*(f+1),24)).resize((128,96),Image.Resampling.NEAREST),(24+152*f,58));board.alpha_composite(Image.open(M/f'tactical-native-frames/frame-{f:03d}.png'),(24+152*f,236))
    board.convert('RGB').save(M/f'reviews/native-v4-{theme}.png',optimize=True)
    board=Image.new('RGBA',(960,672),bg+(255,));dr=ImageDraw.Draw(board);dr.text((24,16),'原作静态：0 / 1 / 2',font=font,fill=fg);dr.text((24,348),'佣兵 · 静态持剑三相',font=font,fill=fg);original=Image.open(M/'reference/original-idle.png').convert('RGBA')
    for f in range(3):board.alpha_composite(original.crop((24*f,0,24*(f+1),24)).resize((288,288),Image.Resampling.NEAREST),(24+312*f,54));board.alpha_composite(Image.open(M/f'frames/idle-{f:03d}.png').resize((288,288),Image.Resampling.NEAREST),(24+312*f,378))
    board.convert('RGB').save(M/f'reviews/idle-v2-{theme}.png',optimize=True)
print(json.dumps(records))
