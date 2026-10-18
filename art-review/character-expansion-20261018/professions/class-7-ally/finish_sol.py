# -*- coding: utf-8 -*-
"""Select final21/22, preserving all earlier approved battle pixels."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
P=Path(__file__).resolve().parent;B=P/'battle';O=B/'sol-frames';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def mask(im,t=128):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def info(p):return {'size':list(Image.open(p).size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
raw=Image.open(B/'source/sol-spin-21-22-v3-generated.png').convert('RGBA');regs=[]
for i,f in enumerate([21,22]):
 cell=[i*raw.width//2,0,(i+1)*raw.width//2,raw.height];im=raw.crop(cell);s=184/370;sm=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS);dx=[-38,-23][i];dy=320-mask(sm,5).getbbox()[3];out=Image.new('RGBA',(448,320));out.alpha_composite(sm,(dx,dy));out.save(O/f'frame-{f:03}.png',optimize=True);outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<448 and 0<=y+dy<320)];assert max(outside,default=0)<=4
 regs.append({'revision':'sol','frame':f,'raw':'source/sol-spin-21-22-v3-generated.png','cell':cell,'uniform_scale':s,'translation':[dx,dy],'visible_clipped_alpha_gt4':0,'maximum_cropped_alpha':max(outside,default=0),'chosen_hand_source_target':[196,[124,164][i]],'chosen_hand_observed_approx':[191 if f==21 else 197,126 if f==21 else 164],'notes':'21 retains a clearly separated vertical fragment. Hand silhouette/gap has a few output pixels of redraw variation; not a per-pixel source match.22 gripping hand brought back beside face; tip/lower horse retained.'})
write(B/'source/sol-final-registration.json',regs)
for bg,label in [('#eee8d8','light'),('#1d2932','dark')]:
 out=Image.new('RGB',(896,640),bg)
 for i,f in enumerate([21,22]):
  a=Image.open(B/f'reference/pose-{f:03}.png').convert('RGBA');b=Image.open(O/f'frame-{f:03}.png');out.paste(a,(448*i,0),a);out.paste(b,(448*i,320),b)
 out.save(B/f'reviews/sol-final-21-22-{label}.png',optimize=True)
m=read(B/'frame_mapping.json');m['frame_mapping'].update({str(f):f'sol-frames/frame-{f:03}.png'for f in [21,22]});m.update(status='complete_art_review_passed',missing_source_frames=[],canonical_frames=list(range(23))+[50,52],review_note='sol：0–20、50、52保留既有通过稿；21/22局部修稿已选定。21分离短竖段与拳之间保留透明间隔，22握手收回面侧；握点约5/2输出像素重绘残差及21手套/间隔轮廓变化保留。');m['records_sol']=regs;m['batches']=[{'id':'sol21-22','review':'reviews/sol-final-21-22-light.png','frames':[21,22]}];write(B/'frame_mapping.json',m)
M=P/'maps';mm=read(M/'frame_mapping.json');mm.update(status='complete_art_review_passed',display_name='黄金骑士（地图） · sol',review_note='sol：本轮地图登记与深浅底复核完成。8个CPU原生槽（6新绘+2精确镜像）、3相静止；原脚相、武器端及马体遮挡按本类源核对。静止整体等比登记保留完整枪尖，头顶约低3输出像素的已记录轮廓差异保留。')
for scenario in mm['scenarios']:
 for r in scenario['frame_mapping']:r['art_status']='reviewed_selected'
write(M/'frame_mapping.json',mm)
write(P/'manifest.json',{'id':'class-7-ally','revision':'sol','status':'complete_art_review_passed','battle_mapping':'battle/frame_mapping.json','maps_mapping':'maps/frame_mapping.json','qa':'qa-report.json','inventory':'image-inventory.json','runtime_integrated':False})
write(P/'qa-report.json',{'revision':'sol','status':'passed','battle_source_slots':27,'battle_canonical':25,'previous_approved_retained':23,'newly_selected':[21,22],'battle_registration':regs,'maps':{'source':'verified native CHR19','walk_slots':8,'redraw_count':6,'exact_full_rgba_mirrors':[{'from':2,'to':6},{'from':3,'to':7}],'idle_poses':3,'registration':'maps/source/sol-registration.json','review_sheets':'maps/reviews/sol-*'},'limitations':['21 fist/fragment shape remains a few output pixels different from source; release gap preserved.','Static map silhouettes fitted by uniform scale; head about3outputpixels lower than source.','Only selected visible hoof/hand landmarks checked, no every-joint exactness claim.'],'runtime_integrated':False})
write(P/'image-inventory.json',{'revision':'sol','images':[{'path':str(p.relative_to(P)),**info(p)}for p in sorted(P.rglob('*.png'))]})
print('Gold knight selected all battle27slots and maps8+3; see recorded redraw limits.')
