from pathlib import Path
from PIL import Image
import json,subprocess,shutil
V=Path(__file__).resolve().parents[1];R=V.parent;MAG='/opt/homebrew/bin/magick'
PALS={
 'ally':['#172432','#173b4b','#2c6070','#4a7b84','#62412b','#9c693b','#c79b61','#cd9367','#efc797','#e8ddbb'],
 'enemy':['#1c2135','#343552','#5c5d95','#8b86bf','#60412d','#98663c','#c79b61','#ce9769','#efc797','#e4dcca']}
def run(args):subprocess.run([MAG,*map(str,args)],check=True)
def bbox(im,t=128):return im.convert('RGBA').getchannel('A').point(lambda v:255 if v>=t else 0).getbbox()
working=V/'source/working';working.mkdir(exist_ok=True)
records=[]
for row,(side,keys)in enumerate([('ally',[1,4,5]),('enemy',[1,5,6])]):
 out=V/'deliverables'/side;out.mkdir(exist_ok=True);mapping=json.loads((V/f'reference/{side}-mapping-before.json').read_text())
 palette=working/f'{side}-palette.png';cmd=['-size','1x1','xc:none']
 for color in PALS[side]:cmd.append('xc:'+color)
 run([*cmd,'+append',palette])
 for col,k in enumerate(keys):
  prev=Image.open(V/f'reference/{side}-{k}.png').convert('RGBA');old=bbox(prev,1)
  gen=Image.open(V/'source/generated-v1.png').crop((col*512,row*448,(col+1)*512,(row+1)*448));box=bbox(gen)
  x0,y0,x1,y1=box;width=old[2]-old[0];height=old[3]-old[1];crop=working/f'{side}-{k}.png'
  run([V/'source/generated-v1.png','-channel','A','-threshold','50%','+channel','-crop',f'{x1-x0}x{y1-y0}+{col*512+x0}+{row*448+y0}','+repage','-filter','box','-resize',f'{width}x{height}!','-channel','A','-threshold','25%','+channel','+dither','-remap',palette,crop])
  feet=bbox(Image.open(crop).crop((0,height-10,width,height)),1);center=(feet[0]+feet[2])/2
  original=next(rec for rec in mapping['records']if int(rec['source_frame'])==k);target=original['target_foot_anchor'];offset=[round(target[0]-center),target[1]-height]
  frame=out/f'frame-{k:03d}.png'
  run(['-size','320x256','xc:none',crop,'-geometry',f'+{offset[0]}+{offset[1]}','-composite','PNG32:'+str(frame)])
  records.append({'side':side,'source_frame':k,'representative_frame':k,'kind':'imagegen_light_armor_revision','generated_crop':list(box),'previous_bounds':list(old),'target_size':[width,height],'target_foot_anchor':target,'registered_foot_anchor':[offset[0]+center,target[1]],'registration_offset':offset,'main_armor_shades':3,'shared_character_palette':PALS[side]})
 # Clothing-only revision: retain the accepted arrows byte for byte.
 shutil.copyfile(V/f'reference/{side}-arrow.png',out/'flying-arrow.png')
 run([*[out/f'frame-{k:03d}.png'for k in keys],'+append',out/'battle-atlas.png'])
subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',*[str(p)for p in(V/'deliverables').rglob('*.png')if p.name!='flying-arrow.png']],check=True)
(V/'registration.json').write_text(json.dumps({'revision':V.name,'records':records,'palettes':PALS},ensure_ascii=False,indent=2)+'\n')
# Current faction pair, plus the six old/new poses for visual inspection.
for name,bg in [('dark','#202d35'),('light','#dcded8')]:
 cmd=['-size','1024x448','xc:'+bg]
 for col,side in enumerate(['ally','enemy']):
  cmd+=['(',V/f'deliverables/{side}/frame-001.png','-filter','point','-resize','480x384!',')','-geometry',f'+{16+512*col}+16','-composite']
  cmd+=['(',V/f'deliverables/{side}/flying-arrow.png','-trim','+repage','-filter','point','-resize','240x36!',')','-geometry',f'+{136+512*col}+400','-composite']
 run([*cmd,V/f'reviews/factions-{name}.png'])
cmd=['-size','1536x1216','xc:#202d35']
for group,(side,keys)in enumerate([('ally',[1,4,5]),('enemy',[1,5,6])]):
 for col,k in enumerate(keys):
  for row,p in enumerate([V/f'reference/{side}-{k}.png',V/f'deliverables/{side}/frame-{k:03d}.png']):cmd+=['(',p,'-filter','point','-resize','480x384!',')','-geometry',f'+{16+512*col}+{group*608+row*288-64}','-composite']
run([*cmd,V/'reviews/previous-and-new.png'])
run([V/'reviews/factions-dark.png','-crop','1024x324+0+124','+repage',V/'reviews/factions-close.png'])
print('6 light-armor frames, accepted 10-color palettes, accepted arrows unchanged')
