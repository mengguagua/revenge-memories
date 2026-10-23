#!/usr/bin/env python3
"""Extract immutable class20 reference sprites and timing records."""
import json, math
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font

REV='bow-knight-complete-v1-20261023';OUT=ROOT/REV;SRC=OUT/'source'

def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def sheet(name,kind,ids,side='ally',cols=3):
    size=(80,64)if kind=='battle'else(32,24)if kind=='walk'else(24,24)
    scale=6 if kind=='battle'else 14;cw,ch=size[0]*scale+32,size[1]*scale+60
    q=Image.new('RGB',(cw*cols,ch*math.ceil(len(ids)/cols)),(220,222,216));d=ImageDraw.Draw(q)
    for n,i in enumerate(ids):
        im=Image.open(SRC/f'native-{side}-{kind}-{i:03}.png').convert('RGBA').resize((size[0]*scale,size[1]*scale),Image.Resampling.NEAREST)
        x=n%cols*cw+16;y=n//cols*ch+16;q.paste(im,(x,y),im)
        d.text((n%cols*cw+cw//2,y+im.height+20),f'{kind} {i}',anchor='mm',font=font(20),fill=(23,38,56))
    q.save(SRC/name,optimize=True)

def main():
    SRC.mkdir(parents=True,exist_ok=True)
    bpath=OUT/'baseline.json'
    if not bpath.exists():
        data=json.loads((ROOT/'demos/gallery-data.json').read_text());ally=json.loads((ROOT/'source-input/original-motion/full-original-motion.json').read_text());overlay=json.loads((ROOT/'source-input/corrected-ally-motion/overlay.json').read_text());ally['variants'].update(overlay['variants']);enemy=json.loads((ROOT/'source-input/enemy-motion/full-enemy-motion.json').read_text())
        write(bpath,{'actions':{a['id']:a for a in data['actions']},'source_bodies':{s:d['original_bodies']['20']for s,d in [('ally',ally),('enemy',enemy)]},'variants':{s:{k:v for k,v in d['variants'].items()if str(v['source_class_id'])=='20'}for s,d in [('ally',ally),('enemy',enemy)]}})
    b=json.loads(bpath.read_text());records=[]
    for side in ['ally','enemy']:
        for kind,path,size,ids in [('idle',ROOT/f'source-input/legacy-assets/assets/original/graphics/map_units/class_20_{side}.png',(24,24),range(6)),('walk',ROOT/f'source-input/corrected-tactical-walk/class-20-{side}.png',(32,24),range(8)),('battle',ROOT/('source-input/original-motion/class-20.png'if side=='ally'else'source-input/enemy-motion/class-20-enemy.png'),(80,64),sorted({f['frame']for v in b['variants'][side].values()for f in v['frames']}))]:
            atlas=Image.open(path).convert('RGBA');columns=atlas.width//size[0]
            for i in ids:
                x=i%columns*size[0];y=i//columns*size[1];atlas.crop((x,y,x+size[0],y+size[1])).save(SRC/f'native-{side}-{kind}-{i:03}.png',optimize=True)
            sheet(f'native-{side}-{kind}-guide.png',kind,list(ids),side,3 if kind=='battle'else 4)
            records.append({'side':side,'kind':kind,'path':str(path.relative_to(ROOT)),'sha256':file_hash(path),'poses':list(ids)})
    sheet('idle-target.png','idle',[0,1,2],cols=3)
    sheet('front-back-target.png','walk',[0,1,4,5],cols=2)
    sheet('ally-prepare-target.png','battle',[1,13,14,15],cols=2)
    sheet('ally-release-target.png','battle',[16,17,18],cols=3)
    sheet('enemy-target.png','battle',[1,5,6],'enemy',3)
    timelines=[]
    for side,variants in b['variants'].items():
        for key,v in variants.items():
            runs=[]
            for n,f in enumerate(v['frames']):
                if not runs or runs[-1]['frame']!=f['frame']:runs.append({'frame':f['frame'],'start':n,'ticks':1})
                else:runs[-1]['ticks']+=1
            timelines.append({'side':side,'key':key,'ticks':len(v['frames']),'contact_tick':v['contact_tick'],'program':v['source_program_address'],'pose_runs':runs})
    write(OUT/'native-reference-audit.json',{'class_id':20,'name':'弓骑士','source_assets':records,'native_timelines':timelines,'map_idle':{'slots':[0,1,2,1],'ticks':[14,8,14,8]},'map_walk':{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7],'ticks':[16,16]},'side_walk_idle_whole_pose_aliases':{'left6':'idle0 plus [4,4] logical pixels','left7':'idle2 plus [4,4] logical pixels','right2_3':'exact full-sprite horizontal mirrors of left6_7'},'runtime_integrated':False})
    print(json.dumps({'baseline_actions':len(b['actions']),'variants':{s:len(v)for s,v in b['variants'].items()},'assets':len(records)}),flush=True)

if __name__=='__main__':main()
