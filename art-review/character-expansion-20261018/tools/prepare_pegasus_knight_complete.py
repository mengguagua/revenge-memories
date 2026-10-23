#!/usr/bin/env python3
"""Extract class3 native anatomy/pose references without touching source data."""
import json,math
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font

REV='pegasus-knight-complete-v1-20261023';OUT=ROOT/REV;SRC=OUT/'source'

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def sheet(filename,kind,ids,side='ally',cols=4):
    size=(80,96)if kind=='battle'else(32,24)if kind=='walk'else(24,24)
    scale=4 if kind=='battle'else 12;cw,ch=size[0]*scale+32,size[1]*scale+52
    q=Image.new('RGB',(cols*cw,math.ceil(len(ids)/cols)*ch),(220,222,216));d=ImageDraw.Draw(q)
    for n,i in enumerate(ids):
        im=Image.open(SRC/f'native-{side}-{kind}-{i:03}.png').convert('RGBA').resize((size[0]*scale,size[1]*scale),Image.Resampling.NEAREST)
        x=n%cols*cw+16;y=n//cols*ch+12;q.paste(im,(x,y),im);d.text((n%cols*cw+cw//2,y+im.height+19),f'{side} {kind} {i}',font=font(16),anchor='mm',fill=(23,38,56))
    q.save(SRC/filename,optimize=True)

def main():
    SRC.mkdir(parents=True,exist_ok=True);path=OUT/'baseline.json'
    if not path.exists():
        d=json.loads((ROOT/'demos/gallery-data.json').read_text());ally=json.loads((ROOT/'source-input/original-motion/full-original-motion.json').read_text());ally['variants'].update(json.loads((ROOT/'source-input/corrected-ally-motion/overlay.json').read_text())['variants']);enemy=json.loads((ROOT/'source-input/enemy-motion/full-enemy-motion.json').read_text())
        write(path,{'actions':{a['id']:a for a in d['actions']},'profiles':d['profiles'],'bodies':{s:m['original_bodies']['3']for s,m in [('ally',ally),('enemy',enemy)]},'variants':{s:{k:v for k,v in m['variants'].items()if str(v['source_class_id'])=='3'}for s,m in [('ally',ally),('enemy',enemy)]},'ally_maps':json.loads((ROOT/'professions/class-3-ally/maps/frame_mapping.json').read_text()),'ally_battle':json.loads((ROOT/'professions/class-3-ally/battle/frame_mapping.json').read_text())})
    b=json.loads(path.read_text());assets=[];timelines=[]
    for side in ['ally','enemy']:
        ids=sorted({f['frame']for v in b['variants'][side].values()for f in v['frames']}|set(b['bodies'][side]['sequences']['idle']))
        for kind,p,size,indices in [('idle',ROOT/f'source-input/legacy-assets/assets/original/graphics/map_units/class_3_{side}.png',(24,24),range(6)),('walk',ROOT/f'source-input/corrected-tactical-walk/class-3-{side}.png',(32,24),range(8)),('battle',ROOT/('source-input/original-motion/class-3.png'if side=='ally'else'source-input/enemy-motion/class-3-enemy.png'),(80,96),ids)]:
            im=Image.open(p).convert('RGBA');cols=im.width//size[0]
            for i in indices:
                x=i%cols*size[0];y=i//cols*size[1];im.crop((x,y,x+size[0],y+size[1])).save(SRC/f'native-{side}-{kind}-{i:03}.png',optimize=True)
            sheet(f'native-{side}-{kind}-guide.png',kind,list(indices),side)
            assets.append({'side':side,'kind':kind,'path':str(p.relative_to(ROOT)),'sha256':file_hash(p),'size':list(im.size),'poses':list(indices)})
        for key,v in b['variants'][side].items():
            runs=[]
            for tick,f in enumerate(v['frames']):
                if not runs or runs[-1]['frame']!=f['frame']:runs.append({'frame':f['frame'],'start':tick,'ticks':1})
                else:runs[-1]['ticks']+=1
            timelines.append({'key':key,'side':side,'ticks':len(v['frames']),'fps':v['native_fps'],'contact':v['contact_tick'],'contact_count':v['contact_count'],'origin':v['actor_origin'],'program':v['source_program_address'],'runs':runs})
    sheet('map-idle-target.png','idle',[0,1,2],cols=3)
    sheet('map-up-target.png','walk',[0,1],cols=2);sheet('map-down-target.png','walk',[4,5],cols=2);sheet('map-side-target.png','walk',[6,7,2,3],cols=4)
    sheet('battle-flight-target.png','battle',[0,1,2,3,4,5],cols=3);sheet('battle-thrust-target.png','battle',[6,7,16,33,34,35],cols=3)
    sheet('enemy-battle-target.png','battle',[9,10,11,12,13,14,15,25],side='enemy',cols=4)
    write(OUT/'native-reference-audit.json',{'class_id':3,'assets':assets,'timelines':timelines,'runtime_integrated':False})
    print(json.dumps({'baseline_actions':len(b['actions']),'attack_variants':{s:len(v)for s,v in b['variants'].items()}}),flush=True)

if __name__=='__main__':main()
