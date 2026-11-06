#!/usr/bin/env python3
"""Slice generated identity sheets. No painting; ImageMagick crops and scales."""
from pathlib import Path
import collections,hashlib,json,shutil,subprocess
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source/recruit-npcs-20261025/images'
OUT=ROOT/'actual/assets/postbattle-npcs-20261025'
GENERATED=Path('/Users/gcc/.codex/generated_images/01a16951-edad-7a70-bf07-1ec480728be8')
JOBS={
 'village_elder_woman':'exec-b4ae0ace-b266-42fa-bd1a-6a126172833f.png',
 'village_man':'exec-a9bae444-5031-4728-b029-66869dc1e781.png',
 'miner_foreman':'exec-f6bebcd9-98f1-4f78-bc2b-20e33fb8a7c4.png',
 'miner_young_woman':'exec-71ca0aa2-f2e9-45a6-a278-78f63898e498.png'}

def components(image):
    w,h=image.size;mask=bytearray(1 if a>=128 else 0 for a in image.getchannel('A').getdata());out=[]
    for seed in range(w*h):
        if not mask[seed]:continue
        pending=[seed];mask[seed]=0;xs=[];ys=[]
        while pending:
            i=pending.pop();x=i%w;y=i//w;xs.append(x);ys.append(y)
            for j in ([i-1]if x else [])+([i+1]if x<w-1 else [])+([i-w]if y else [])+([i+w]if y<h-1 else []):
                if mask[j]:mask[j]=0;pending.append(j)
        if len(xs)>500:out.append({'pixels':len(xs),'box':[min(xs),min(ys),max(xs)+1,max(ys)+1]})
    return out

def crop(source,box,dest,portrait=False):
    x,y,right,bottom=box;args=['/opt/homebrew/bin/magick',str(source),'-crop',f'{right-x}x{bottom-y}+{x}+{y}','+repage','-filter','point']
    args+=['-resize','48x48','-background','none','-gravity','center','-extent','48x48']if portrait else ['-resize','84x84','-background','none','-gravity','south','-extent','96x88','-gravity','north','-extent','96x96']
    subprocess.run(args+[str(dest)],check=True)
    subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(dest)],check=True)

def main():
    SOURCE.mkdir(parents=True,exist_ok=True);(SOURCE.parent/'.gdignore').touch();OUT.mkdir(parents=True,exist_ok=True)
    records=[];profiles={}
    for key,filename in JOBS.items():
        source=SOURCE/(key+'-source.png');shutil.copyfile(GENERATED/filename,source)
        with Image.open(source)as im:
            assert im.mode=='RGBA';groups=components(im);portrait=max(groups,key=lambda c:c['pixels']);others=[g for g in groups if g['box'][1]>portrait['box'][3]]
            first_y=min(g['box'][1]for g in others);idle=min([g for g in others if g['box'][1]<first_y+80],key=lambda g:g['box'][0])
            def margin(box,n):return [max(0,box[0]-n),max(0,box[1]-n),min(im.width,box[2]+n),min(im.height,box[3]+n)]
            p=OUT/(key+'-portrait.png');s=OUT/(key+'-idle.png');crop(source,portrait['box'],p,True);crop(source,margin(idle['box'],4),s)
        profiles[key]={'portrait':'res://'+str(p.relative_to(ROOT/'actual')),'hub':{'path':'res://'+str(s.relative_to(ROOT/'actual')),'frame_size':[96,96],'frames':1,'columns':1,'anchor':[12,24],'tile_origin':[4,8],'native_density':4,'logical_frame_size':[24,24],'directions':{'down':[0],'up':[0],'side':[0],'left':[0],'right':[0]},'static_facing':True,'default_facing':'right'}}
        for path,purpose in [(p,'dialogue portrait'),(s,'front idle only')]:
            with Image.open(path)as im:size=list(im.size)
            records.append({'profile':key,'purpose':purpose,'path':str(path.relative_to(ROOT)),'pixels':size,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    data={'scope':'Peaceful post-battle hub NPCs and their portraits only; no battle sprites or movement changes.','profiles':profiles}
    (ROOT/'actual/data/postbattle_npcs_20261025.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    report=ROOT/'actual/reports/recruit-npcs-20261025';report.mkdir(parents=True,exist_ok=True);(report/'assets.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(records,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
