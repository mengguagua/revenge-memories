"""Register first key drafts for review, not approved deliverables."""
from pathlib import Path
from PIL import Image
import json,subprocess
P=Path(__file__).resolve().parents[1];G='/opt/homebrew/bin/magick';O=P/'battle/candidate-motion-v1';O.mkdir(exist_ok=True)
def run(*a):subprocess.run([G,*map(str,a)],check=True)
def mask(i):return i.convert('RGBA').getchannel('A').point(lambda a:255 if a>=32 else 0)
p=P/'source/motion-4-5-6-v1-generated.png';raw=Image.open(p).convert('RGBA');spec=[(4,[0,0,741,724],94,33),(5,[741,0,1425,724],94,33),(6,[1425,0,2172,724],67,32)];records=[]
for f,cell,head,sy in spec:
 im=raw.crop(cell);a=mask(im);b=a.getbbox();sc=(256-sy*4)/(b[3]-head);crop=[max(0,b[0]-3),max(0,b[1]-3),min(im.width,b[2]+3),min(im.height,b[3]+3)];cut=O/f'cut-{f:03}.png';small=O/f'small-{f:03}.png'
 run(p,'-crop',f'{crop[2]-crop[0]}x{crop[3]-crop[1]}+{cell[0]+crop[0]}+{crop[1]}','+repage',cut);run(cut,'-filter','Lanczos','-resize',f'{sc*100:.10f}%',small)
 sm=Image.open(small).convert('RGBA');sa=mask(sm);sb=sa.getbbox();boot_roi=[int(im.width*.2),b[3]-140,im.width,b[3]];fb=a.crop(boot_roi).getbbox();fx=((fb[0]+fb[2])/2+boot_roi[0]-crop[0])*sm.width/(crop[2]-crop[0]);src=Image.open(P/f'reference/original-{f:03}.png');sf=mask(src).crop((30,61,65,64)).getbbox();target=[2*(sf[0]+sf[2]+60),256];dx=round(target[0]-fx);dy=256-sb[3];dst=O/f'frame-{f:03}.png';run('-size','320x256','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<320 and 0<=y+dy<256)]
 records.append({'frame':f,'raw':str(p.relative_to(P)),'cell':cell,'crop':crop,'head_top':head,'source_helmet_top':sy,'uniform_scale':sc,'translation':[dx,dy],'source_boot_roi':[30,61,65,64],'generated_boot_roi':boot_roi,'target_boot_span_center':target,'registered_boot_span_center':[fx+dx,256],'visible_clipped_pixels_alpha32':sum(a>=32 for a in outside),'status':'draft_needs_pose_corrections','note':'Foot-span center alone does not prove both boot locations. Native12 grip is(26,40), not chest pale band;30 overhead grip left of head.'})
for c,l in [('#1d2932','dark'),('#eee8d8','light')]:run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[P/f'reference/original4-{f:03}.png'for f,_,_,_ in spec],*[O/f'frame-{f:03}.png'for f,_,_,_ in spec],'-tile','3x2','-geometry','320x256+0+8','-background',c,P/f'battle/reviews/motion-4-5-6-v1-original-new-{l}.png')
(O/'registration.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records))
