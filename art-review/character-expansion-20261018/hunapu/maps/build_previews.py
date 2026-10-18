"""Read-only artwork QA montages and animation previews; no game execution."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,subprocess
R=Path(__file__).resolve().parent
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',19)
small=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',15)
data=json.loads((R/'frame_mapping.json').read_text())
BG={'dark':'#1d2b35','light':'#ece6d8'}

def canvas(size,bg):return Image.new('RGBA',size,bg)
def text(im,pos,value,bg,small_font=False):ImageDraw.Draw(im).text(pos,value,font=small if small_font else font,fill='#e8edf0' if bg=='dark' else '#263341')
def paste(im,item,pos):im.alpha_composite(item,pos)

for s in data['scenarios']:
    if s['id']=='world':continue
    fw,fh=s['output_frame_size'];sw,sh=s['source_frame_size']
    src=Image.open(R/s['source_atlas']).convert('RGBA')
    new=Image.open(R/s['output_atlas']).convert('RGBA')
    width=6*fw+80;height=2*(fh*2+94)+30
    out=canvas((width,height),BG['dark'])
    for n,bg in enumerate(['dark','light']):
        y=n*(fh*2+94)
        out.paste(BG[bg],(0,y,width,y+fh*2+94))
        text(out,(24,y+12),f"{s['id']} · 源帧 ×4 / 新帧（逻辑尺寸不变）",bg)
        for i in range(6):
            x=40+i*fw
            orig=src.crop((i*sw,0,(i+1)*sw,sh)).resize((fw,fh),Image.Resampling.NEAREST)
            cur=new.crop((i*fw,0,(i+1)*fw,fh))
            paste(out,orig,(x,y+46));paste(out,cur,(x,y+fh+58))
            text(out,(x+fw//2-10,y+fh*2+64),str(i),bg,True)
    out.convert('RGB').save(R/'previews'/f"{s['id']}-dark-light.png",optimize=True)

for s in data['scenarios']:
    sid=s['id'];fw,fh=s['output_frame_size'];sw,sh=s['source_frame_size']
    src=Image.open(R/s['source_atlas']).convert('RGBA');new=Image.open(R/s['output_atlas']).convert('RGBA')
    idle=sid=='tactical-idle';dirs=['all'] if idle else ['down','up','right','left']
    cycle=[0,1,2,1] if idle else [0,1]
    ticks=[14,8,14,8] if idle else [16,16]
    for bg in ['dark','light']:
        frames=[]
        for phase in cycle:
            out=canvas((440,len(dirs)*(fh+32)+82),BG[bg]);text(out,(24,15),f"{sid} · 原始节奏 / 4倍新图",bg)
            text(out,(122,48),'原作',bg,True);text(out,(290,48),'新图',bg,True)
            for row,d in enumerate(dirs):
                idx=phase if idle else s['directions'][d][phase]
                a=src.crop((idx*sw,0,(idx+1)*sw,sh)).resize((fw,fh),Image.Resampling.NEAREST)
                b=new.crop((idx*fw,0,(idx+1)*fw,fh))
                if d=='left':a=a.transpose(Image.Transpose.FLIP_LEFT_RIGHT);b=b.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                y=76+row*(fh+32);text(out,(16,y+fh//2-10),d,bg,True);paste(out,a,(100,y));paste(out,b,(270,y))
            frames.append(out.convert('RGB'))
        duration=[round(t/60.0988*1000) for t in ticks]
        frames[0].save(R/'previews'/f'{sid}-{bg}.gif',save_all=True,append_images=frames[1:],duration=duration,loop=0,disposal=2,optimize=True)
        frames[0].save(R/'previews'/f'{sid}-{bg}-frame0.png',optimize=True)

for s in data['scenarios']:
    if s['id'] not in ['story','tactical-walk']:continue
    paths=[]
    for i in [4,5]:
        p=R/s['frame_mapping'][i]['path'];out=p.with_name(p.stem+'-left.png')
        subprocess.run(['/opt/homebrew/bin/magick',str(p),'-flop',str(out)],check=True)
        subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--strip','safe',str(out)],check=True,capture_output=True)
        paths.append({'path':str(out.relative_to(R)),'source_index':i,'derived_from':s['frame_mapping'][i]['path'],'transform':'horizontal-mirror-about-frame-center','bytes':out.stat().st_size,'size':s['output_frame_size']})
    s['explicit_left_frames']=paths
    if s['id']=='story':
        next(x for x in data['scenarios'] if x['id']=='world')['explicit_left_frames']=paths
for s in data['scenarios']:
    s['preview_dark']=f"previews/{s['id']}-dark.gif";s['preview_light']=f"previews/{s['id']}-light.gif"
    if not s['static_facing']:
        s['timing']['source_timing_evidence']=['actual/core/story_hub.gd:315','actual/core/main.gd:592','actual/core/legacy_main.gd:1190']
data['approved_identity_reference']='../../../hunapu-20261018-v1/deliverables/pose-000.png'
(R/'frame_mapping.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('QA previews and explicit original-rule left mirror frames written.')
