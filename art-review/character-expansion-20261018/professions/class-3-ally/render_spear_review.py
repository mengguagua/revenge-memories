from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
r=Path(__file__).resolve().parent/'maps';font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',18)
for group,folder,ids,w in [('native','tactical-native-frames',[0,1,4,5,6,7],128),('idle','idle-frames',[0,1,2],96)]:
    for theme,bg,fg in [('light','#e9e4d9','#26333a'),('dark','#1d2b35','#edf0e7')]:
        b=Image.new('RGBA',(24+(w*2+16)*len(ids),460),bg);d=ImageDraw.Draw(b);d.text((16,8),'天马地图枪端纠正 · 修前 / 修后（上钝尾，下钢刃）',font=font,fill=fg)
        for col,i in enumerate(ids):
            x=16+col*(w*2+16);b.alpha_composite(Image.open(r/f'source/spear-end-patches/{folder}-{i:03}-before.png').convert('RGBA').resize((w*2,192),Image.Resampling.NEAREST),(x,38));b.alpha_composite(Image.open(r/f'{folder}/frame-{i:03}.png').convert('RGBA').resize((w*2,192),Image.Resampling.NEAREST),(x,244));d.text((x+w-8,438),str(i),font=font,fill=fg)
        b.convert('RGB').save(r/f'reviews/spear-end-corrected-{group}-{theme}.png',optimize=True)
b=Image.new('RGBA',(1080,450),'#e9e4d9')
for col,(folder,i)in enumerate([('tactical-native-frames',6),('idle-frames',1)]):
    b.alpha_composite(Image.open(r/f'{folder}/frame-{i:03}.png').convert('RGBA').resize((512 if col==0 else 384,384),Image.Resampling.NEAREST),(16+col*540,24))
b.convert('RGB').save(r/'reviews/spear-end-closeup.png',optimize=True)
