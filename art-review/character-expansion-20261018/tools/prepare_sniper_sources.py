#!/usr/bin/env python3
"""Extract unchanged class13 native references for pose interpretation."""
import json, math
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font

OUT=ROOT/'sniper-complete-v1-20261022'
SRC=OUT/'source'

def sheet(ids,kind,name,columns=3,scale=8,side='ally'):
    w,h=(32,24) if kind=='walk' else (24,24) if kind=='idle' else (80,64)
    cw,ch=(w*scale+32,h*scale+32)
    canvas=Image.new('RGBA',(columns*cw,math.ceil(len(ids)/columns)*ch))
    for n,i in enumerate(ids):
        im=Image.open(SRC/f'native-{side}-{kind}-{i:03}.png').convert('RGBA').resize((w*scale,h*scale),Image.Resampling.NEAREST)
        canvas.alpha_composite(im,(n%columns*cw+16,n//columns*ch+16))
    canvas.save(SRC/name,optimize=True)

def main():
    b=json.loads((OUT/'baseline.json').read_text())
    for side in ['ally','enemy']:
        for kind,path,size,count in [
            ('walk',ROOT/f'source-input/corrected-tactical-walk/class-13-{side}.png',(32,24),8),
            ('idle',ROOT/f'source-input/legacy-assets/assets/original/graphics/map_units/class_13_{side}.png',(24,24),6),
            ('battle',ROOT/('source-input/original-motion/class-13.png' if side=='ally' else 'source-input/enemy-motion/class-13-enemy.png'),(80,64),b['source_bodies'][side]['frames'])]:
            atlas=Image.open(path).convert('RGBA');cols=atlas.width//size[0]
            ids=list(range(count)) if kind!='battle' else sorted({f['frame'] for v in b['variants'][side].values() for f in v['frames']})
            cw,ch=(240,235) if kind!='battle' else (360,295)
            board=Image.new('RGB',(cw*4,44+ch*math.ceil(len(ids)/4)),(220,222,216));d=ImageDraw.Draw(board)
            d.text((board.width//2,22),side+' native '+kind,anchor='mm',font=font(18),fill=(23,38,56))
            for n,i in enumerate(ids):
                x=i%cols*size[0];y=i//cols*size[1]
                im=atlas.crop((x,y,x+size[0],y+size[1]));im.save(SRC/f'native-{side}-{kind}-{i:03}.png',optimize=True)
                scale=8 if kind!='battle' else 4
                q=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
                xx=n%4*cw+(cw-q.width)//2;yy=44+n//4*ch;board.paste(q,(xx,yy),q)
                d.text((n%4*cw+cw//2,yy+ch-22),f'{kind} {i}',anchor='mm',font=font(16),fill=(23,38,56))
            board.save(SRC/f'native-{side}-{kind}-guide.png',optimize=True)
    sheet([0,1,4,5],'walk','map-front-back-target.png',2,16)
    sheet([2,3,6,7],'walk','map-sides-target.png',2,16)
    sheet([0,1,2],'idle','map-idle-target.png',3,16)
    sheet([1,2,10,11,12,13],'battle','battle-prepare-target.png',3,5)
    sheet([14,15,16],'battle','battle-release-target.png',3,5)
    sheet([1,16,17,18,19,20],'battle','enemy-prepare-target.png',3,5,'enemy')
    sheet([21,22,23,24,25,26],'battle','enemy-aim-target.png',3,5,'enemy')
    sheet([27],'battle','enemy-release-target.png',1,5,'enemy')
    im=Image.open(ROOT/'body-volume-motion-20261018/deliverables/class-12-ally/idle-00.png').convert('RGBA')
    im.resize((768,768),Image.Resampling.NEAREST).save(SRC/'approved-archer-reference.png',optimize=True)
    print('Archer palette',im.size,sorted({p[:3] for p in im.getdata() if p[3]}),flush=True)

if __name__=='__main__':main()
