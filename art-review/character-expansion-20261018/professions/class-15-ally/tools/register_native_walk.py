#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];M=R/'maps';O=M/'tactical-native-frames';O.mkdir(exist_ok=True)
spec=[{'slot':0,'raw':'up-v1.png','crop':[200,120,800,850],'head_y':175,'body_anchor':[490,818],'target_head_y':32,'target_body_anchor':[62,92]}, {'slot':1,'raw':'up-v1.png','crop':[1020,120,1590,850],'head_y':175,'body_anchor':[1280,818],'target_head_y':32,'target_body_anchor':[64,96]}, {'slot':2,'raw':'right-v1.png','crop':[180,80,810,870],'head_y':126,'body_anchor':[650,827],'target_head_y':32,'target_body_anchor':[64,92]}, {'slot':3,'raw':'right-phase1-v2.png','crop':[0,0,1092,1440],'head_y':85,'body_anchor':[430,1364],'target_head_y':32,'target_body_anchor':[54,92]}, {'slot':4,'raw':'down-v1.png','crop':[240,80,830,870],'head_y':125,'body_anchor':[558,848],'target_head_y':32,'target_body_anchor':[66,96]}, {'slot':5,'raw':'down-v1.png','crop':[1020,90,1540,880],'head_y':136,'body_anchor':[1254,855],'target_head_y':32,'target_body_anchor':[64,96]}]
records=[]
for s in spec:
 im=Image.open(M/'source/tactical-native'/s['raw']).convert('RGBA').crop(s['crop']);im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(s['target_body_anchor'][1]-s['target_head_y'])/(s['body_anchor'][1]-s['head_y']);sz=[round(v*sc)for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_body_anchor'][i]-(s['body_anchor'][i]-s['crop'][i])*sc)for i in range(2)];out=Image.new('RGBA',(128,96));out.alpha_composite(im,xy);out.save(O/f'frame-{s["slot"]:03d}.png');records.append({**s,'scale':sc,'resized_size':sz,'paste':xy,'alpha_bounds':out.getbbox(),'registration_basis':'Visible boot/lower cloak envelope and hat top. Hidden legs are not inferred, no whole-cape bbox centering or clamping.'})
for i,j in [(6,2),(7,3)]:Image.open(O/f'frame-{j:03d}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(O/f'frame-{i:03d}.png')
a=Image.new('RGBA',(1024,96))
for f in range(8):a.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(f*128,0))
a.save(M/'frames/tactical-native-walk.png');(M/'tactical-native-registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');old=Image.open(M/'reference/tactical-native-original.png').convert('RGBA');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg,fg in [('dark',(30,44,53),(235,242,244)),('light',(229,230,220),(34,43,47))]:
 board=Image.new('RGBA',(1248,384),bg+(255,));d=ImageDraw.Draw(board);d.text((24,16),'原作校正：上0 / 上1 / 右0 / 右1 / 下0 / 下1 / 左0 / 左1',font=font,fill=fg);d.text((24,194),'男魔道士 · 原生四向步相与披风遮挡',font=font,fill=fg)
 for f in range(8):board.alpha_composite(old.crop((f*32,0,(f+1)*32,24)).resize((128,96),Image.Resampling.NEAREST),(24+f*152,58));board.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+f*152,236))
 board.convert('RGB').save(M/f'reviews/tactical-native/native-v1-{theme}.png',optimize=True)
print('registered six generated source poses and two verified mirrors')
