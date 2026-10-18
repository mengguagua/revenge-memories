#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];B=R/'battle';O=B/'candidate-motion-v4';O.mkdir(exist_ok=True)
spec=[{'frame': 1, 'raw': 'pose001-v2-generated.png', 'head_y': 286, 'foot': [649, 1270], 'target_head_y': 144, 'target_foot': [194, 256]}, {'frame': 2, 'raw': 'pose002-v2-generated.png', 'head_y': 506, 'foot': [850, 1498], 'target_head_y': 144, 'target_foot': [200, 248]}, {'frame': 3, 'raw': 'pose003-v3-generated.png', 'head_y': 325, 'foot': [590, 1088], 'target_head_y': 136, 'target_foot': [154, 228]}, {'frame': 4, 'raw': 'pose004-v4-generated.png', 'head_y': 418, 'foot': [220, 1301], 'target_head_y': 136, 'target_foot': [118, 240]}, {'frame': 5, 'raw': 'pose005-v3-generated.png', 'head_y': 458, 'foot': [207, 1320], 'target_head_y': 136, 'target_foot': [118, 240]}]
rr=[]
for s in spec:
 im=Image.open(B/'source'/s['raw']).convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(s['target_foot'][1]-s['target_head_y'])/(s['foot'][1]-s['head_y']);sz=[round(v*sc)for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_foot'][i]-s['foot'][i]*sc)for i in range(2)];o=Image.new('RGBA',(320,256));o.alpha_composite(im,xy);o.save(O/f'frame-{s["frame"]:03d}.png');rr.append({**s,'scale':sc,'resized':sz,'paste':xy,'alpha_bounds':o.getbbox(),'registration_basis':'Selected clearly visible support/leading boot and head top, not sword or full-alpha center. Not a claim all limbs match.'})
(O/'registration.json').write_text(json.dumps(rr,indent=2)+'\n');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for th,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 board=Image.new('RGBA',(1648,624),bg+(255,));d=ImageDraw.Draw(board);fg=(235,242,244)if th=='dark'else(34,43,47);d.text((24,14),'我方佣兵 · 原作1 / 2 / 3 / 4 / 5',font=font,fill=fg);d.text((24,326),'连续动作候选 · 支撑／收腿／延伸相位逐帧复核',font=font,fill=fg)
 for j,f in enumerate(range(1,6)):
  board.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+j*320,44));board.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+j*320,356))
 board.convert('RGB').save(B/f'reviews/motion-v4-original-vs-new-{th}.png',optimize=True)
print(rr)
