#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];M=R/'maps';O=M/'tactical-native-frames';O.mkdir(exist_ok=True)
spec=[{'slot': 0, 'raw': 'up-phase0-v4.png', 'crop': [400, 260, 1080, 1120], 'head_y': 318, 'body_anchor': [798, 1075], 'target_head_y': 32, 'target_body_anchor': [66, 96]}, {'slot': 1, 'raw': 'up-phase1-v4.png', 'crop': [300, 260, 950, 1140], 'head_y': 319, 'body_anchor': [540, 1097], 'target_head_y': 32, 'target_body_anchor': [50, 96]}, {'slot': 2, 'raw': 'right-v2.png', 'crop': [220, 130, 800, 800], 'head_y': 178, 'body_anchor': [500, 759], 'target_head_y': 32, 'target_body_anchor': [60, 96]}, {'slot': 3, 'raw': 'right-v2.png', 'crop': [1000, 130, 1580, 800], 'head_y': 178, 'body_anchor': [1165, 753], 'target_head_y': 32, 'target_body_anchor': [48, 96]}, {'slot': 4, 'raw': 'down-v2.png', 'crop': [220, 70, 810, 850], 'head_y': 120, 'body_anchor': [583, 806], 'target_head_y': 32, 'target_body_anchor': [68, 96]}, {'slot': 5, 'raw': 'down-v2.png', 'crop': [990, 70, 1570, 850], 'head_y': 120, 'body_anchor': [1257, 806], 'target_head_y': 32, 'target_body_anchor': [60, 96]}]
records=[]
for s in spec:
 im=Image.open(M/'source/tactical-native'/s['raw']).convert('RGBA').crop(s['crop']);im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(s['target_body_anchor'][1]-s['target_head_y'])/(s['body_anchor'][1]-s['head_y']);sz=[round(v*sc)for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_body_anchor'][i]-(s['body_anchor'][i]-s['crop'][i])*sc)for i in range(2)];out=Image.new('RGBA',(128,96));out.alpha_composite(im,xy);out.save(O/f'frame-{s["slot"]:03d}.png');records.append({**s,'scale':sc,'resized_size':sz,'paste':xy,'alpha_bounds':out.getbbox(),'registration_basis':'Selected visible support boot and hair top. No blade bbox centering, clamping or inference of hidden joints; selected anchor does not assert all limb pixels match.'})
for i,j in [(6,2),(7,3)]:Image.open(O/f'frame-{j:03d}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(O/f'frame-{i:03d}.png')
a=Image.new('RGBA',(1024,96))
for f in range(8):a.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(f*128,0))
a.save(M/'frames/tactical-native-walk.png');(M/'tactical-native-registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');old=Image.open(M/'reference/tactical-native-original.png').convert('RGBA');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg,fg in [('dark',(30,44,53),(235,242,244)),('light',(229,230,220),(34,43,47))]:
 board=Image.new('RGBA',(1248,384),bg+(255,));d=ImageDraw.Draw(board);d.text((24,16),'原作校正：上0 / 上1 / 右0 / 右1 / 下0 / 下1 / 左0 / 左1',font=font,fill=fg);d.text((24,194),'村民 · 原生四向步相与短刃握姿',font=font,fill=fg)
 for f in range(8):board.alpha_composite(old.crop((f*32,0,(f+1)*32,24)).resize((128,96),Image.Resampling.NEAREST),(24+f*152,58));board.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+f*152,236))
 board.convert('RGB').save(M/f'reviews/tactical-native/native-v4-{theme}.png',optimize=True)
print('registered six generated source poses and two verified mirrors')
