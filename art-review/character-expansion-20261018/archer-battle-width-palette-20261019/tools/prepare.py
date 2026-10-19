"""Register and palette-optimize ImageGen sprites; no generated game logic."""
from pathlib import Path
from PIL import Image
import json, subprocess
V=Path(__file__).resolve().parents[1];R=V.parent
MAG='/opt/homebrew/bin/magick'
def run(args):subprocess.run([MAG,*map(str,args)],check=True)
def bbox(im,threshold=128):return im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=threshold else 0).getbbox()
records=[]
for row,(side,keys) in enumerate([('ally',[1,4,5]),('enemy',[1,5,6])]):
    out=V/'deliverables'/side;out.mkdir(exist_ok=True)
    mapping=json.loads((V/f'reference/{side}-mapping-before.json').read_text())
    temps=[]
    for col,k in enumerate(keys):
        original=Image.open(V/f'reference/{side}-{k}.png').convert('RGBA');old=bbox(original,1)
        generated=Image.open(V/'source/generated-v1.png').crop((col*512,row*448,(col+1)*512,(row+1)*448))
        box=bbox(generated);x0,y0,x1,y1=box
        width=round((old[2]-old[0])*1.10);height=old[3]-old[1]
        temp=out/f'crop-{k}.png'
        run([V/'source/generated-v1.png','-channel','A','-threshold','50%','+channel','-crop',f'{x1-x0}x{y1-y0}+{col*512+x0}+{row*448+y0}','+repage','-filter','box','-resize',f'{width}x{height}!','-channel','A','-threshold','25%','+channel',temp])
        rendered=Image.open(temp).convert('RGBA');foot=bbox(rendered.crop((0,height-10,width,height)),1)
        center=(foot[0]+foot[2])/2
        rec=next(x for x in mapping['records']if int(x['source_frame'])==k)
        target=rec['target_foot_anchor'];offset=[round(target[0]-center),target[1]-height]
        frame=out/f'frame-{k:03d}.png'
        run(['-size','320x256','xc:none',temp,'-geometry',f'+{offset[0]}+{offset[1]}','-composite',frame])
        temps.append(frame)
        records.append({'side':side,'frame':k,'original_bounds':list(old),'generated_crop':list(box),'target_size':[width,height],'offset':offset,'target_foot_anchor':target,'registered_foot_anchor':[offset[0]+center,target[1]],'width_factor':width/(old[2]-old[0]),'height_preserved':True})
    palette=out/'shared-palette.png'
    run([*temps,'+append','+dither','-colors','33','-unique-colors',palette])
    for frame in temps:run([frame,'+dither','-remap',palette,'PNG32:'+str(frame)])
    arrow_temp=out/'arrow-crop.png'
    run([V/'source/generated-v1.png','-channel','A','-threshold','50%','+channel','-crop',f'512x128+{row*512}+896','+repage','-trim','+repage','-filter','box','-resize','80x12!','-channel','A','-threshold','25%','+channel','+dither','-remap',palette,arrow_temp])
    run(['-size','192x64','xc:none',arrow_temp,'-geometry','+104+40','-composite','PNG32:'+str(out/'flying-arrow.png')])
    # Preserve a one-native-pixel light shaft after the generated projectile is
    # registered at 4x density; its untouched outline/feathers remain in place.
    arrow=out/'flying-arrow.png'
    run([arrow,'(',arrow,'-crop','44x1+119+45','+repage','-filter','point','-resize','44x4!',')','-geometry','+119+44','-composite','PNG32:'+str(arrow)])
(V/'registration.json').write_text(json.dumps({'revision':'archer-battle-width-palette-20261019','records':records},ensure_ascii=False,indent=2)+'\n')
# A sheet for visual review. Rows: previous redraw / current redraw, ally then enemy.
cmd=['-size','1536x1152','xc:#202d35']
for group,(side,keys)in enumerate([('ally',[1,4,5]),('enemy',[1,5,6])]):
 for col,k in enumerate(keys):
  for revision,path in enumerate([V/f'reference/{side}-{k}.png',V/f'deliverables/{side}/frame-{k:03d}.png']):
   cmd+=['(',path,'-filter','point','-resize','480x384!',')','-geometry',f'+{col*512+16}+{group*576+revision*272-80}','-composite']
cmd+=[V/'reviews/previous-and-new.png'];run(cmd)
print(json.dumps(records,ensure_ascii=False))
