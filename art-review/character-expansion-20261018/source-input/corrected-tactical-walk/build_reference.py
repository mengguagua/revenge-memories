#!/usr/bin/env python3
"""Read-only original CPU extraction. Outputs only isolated corrected references."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys,json,hashlib,math
HERE=Path(__file__).resolve().parent;EXP=HERE.parent.parent;REPO=EXP.parent.parent
sys.path.insert(0,str(REPO/'tools'))
from extract_full_graphics import Source,color,signed
from fe2_source_cpu import CPU
SRC=Source(REPO/'.reference/fe2-source-956365ef');B=SRC.b[11]
DIRS=['up','right','down','left'];FPS=60.0988
PALETTES={'ally':[15,32,34,15],'enemy':[15,54,37,15]}
ACTIVE_ENEMY={1,2,3,6,7,8,11,12,15,22}
class CaptureCPU(CPU):
 def __init__(self,rom):super().__init__(rom);self.chr_writes=[]
 def write(self,a,v):
  if a in [0xb000,0xc000]:self.chr_writes.append({'register':hex(a),'value':v})
  super().write(a,v)
def run(cid,side,direction,phase,name=None):
 c=CaptureCPU(SRC.rom);m=c.mem;m[0x7a]=0;m[0x7b]=0x60;m[0x6000]=(0x80 if side=='enemy' else 1)if name is None else name;m[0x505]=cid;m[0x504]=direction;m[0x502]=64;m[0x503]=80;m[0x36]=phase*16
 n=c.call(11,0xb5b1);oam=[list(m[0x200+i:0x204+i])for i in range(0,m[0x3d],4)]
 table='L0BB669'if side=='ally'else'L0BB745';chrtable='L0BB719'if side=='ally'else'L0BB7F5';fliptable='L0BB72F'if side=='ally'else'L0BB80B';index=B[table]['db'][(cid-1)*8+direction*2+phase];ref=SRC.b[8][SRC.ptr(8,0xbfd0)]['dw'][index]
 assert c.chr==B[chrtable]['db'][cid-1]
 return {'direction':DIRS[direction],'direction_code':direction,'phase':phase,'clock_value':phase*16,'frame_ticks':16,'source_chr':c.chr,'source_frame_index':index,'source_frame_address':ref,'oam':oam,'chr_writes':c.chr_writes,'cpu_instructions':n,'source_global_flip':bool(direction==1 and B[fliptable]['db'][cid-1]),'lookup':{'animation':table,'chr':chrtable,'right_mirror_flag':fliptable}}
def entries(row,side):
 out=[]
 for y,t,a,x in reversed(row['oam']):
  im=color(SRC.tiles[row['source_chr']][t],PALETTES[side])
  if a&64:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if a&128:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  out.append((x-64,(y+1)-80,im))
 return out
def digest(im):return hashlib.sha256(im.tobytes()).hexdigest()
records={};summary=[]
for side in ['ally','enemy']:
 for cid in range(1,23):
  rows=[run(cid,side,di,phase)for di in range(4)for phase in range(2)];allent=[entries(row,side)for row in rows];xs=[-16,16];ys=[-16,8]
  for es in allent:
   for x,y,i in es:
    box=i.getbbox()
    if box:xs.extend([x+box[0],x+box[2]]);ys.extend([y+box[1],y+box[3]])
  half=math.ceil(max(abs(min(xs)),abs(max(xs)))/8)*8;top=math.floor(min(ys)/8)*8;bottom=math.ceil(max(ys)/8)*8;size=[2*half,bottom-top];actor=[half,-top];anchor=[half,8-top];atlas=Image.new('RGBA',(size[0]*8,size[1]));seen={};aliases={};bounds=[]
  for f,(row,es)in enumerate(zip(rows,allent)):
   im=Image.new('RGBA',size)
   for x,y,tile in es:im.alpha_composite(tile,(x+half,y-top))
   row['source_slot']=f;row['source_alpha_bounds']=im.getbbox();row['rgba_sha256']=digest(im);seen.setdefault(digest(im),f);aliases[str(f)]=seen[digest(im)];atlas.alpha_composite(im,(f*size[0],0));bounds.append(im.getbbox())
  key=f'class-{cid}-{side}';atlas.save(HERE/(key+'.png'),optimize=True)
  oldpath=EXP/f'source-input/original-motion/original-walk-{cid}.png';old=Image.open(oldpath).convert('RGBA');oldfs=[old.crop((f*32,0,(f+1)*32,24))for f in range(6)];equal=[]
  for f in range(8):
   fr=atlas.crop((f*size[0],0,(f+1)*size[0],size[1]));equal.append([i for i,o in enumerate(oldfs)if o.size==fr.size and o.tobytes()==fr.tobytes()])
  records[key]={'class_id':cid,'source_side':side,'status':'native_cpu_reference','scope':'required_source'if side=='ally'or cid in ACTIVE_ENEMY else'reference_only','source_atlas':key+'.png','source_frame_size':size,'source_columns':8,'source_frame_count':8,'source_anchor':anchor,'native_actor_origin':actor,'anchor_note':'Rendering anchor is native actor origin+[0,8] matching map tile base; not inferred anatomical foot or wing tip. Native OAM Y adds hardware+1.','source_palette':PALETTES[side],'palette_evidence':'bank006:L06852C PPU palette payload sprite palette0(ally)/3(enemy), not BG palette.','source_chr':rows[0]['source_chr'],'frame_mapping':rows,'exact_pixel_aliases':aliases,'unique_source_slots':sorted(set(aliases.values())),'directions':{d:[2*i,2*i+1]for i,d in enumerate(DIRS)},'direction_mirror_x':{},'mirror_note':'Native whole-sprite right flip and individual tile flips are already applied by original CPU; do not apply an additional direction mirror.','timing':{'native_fps':FPS,'frame_ticks':16,'cycle_ticks':32,'phase_source':'$36 & $10 selects phase; L0BB62C','movement_pixels_per_tick':1,'movement_source':'L06BE42→L06BE5F updates X/Y by1 each movement tick; four codes0up1right2down3left'},'old_frozen_source':str(oldpath.relative_to(EXP)),'old_frozen_frame_rgba_matches_by_corrected_slot':equal,'old_reference_classification':'Old PNG is CHR26 combined with village OAM selected via L08A779; this is not the native tactical renderer. Native village initializes CHR30, so this hybrid is retained only as current-game frozen historical reference.'}
  summary.append({'id':key,'chr':rows[0]['source_chr'],'size':size,'unique_slots':len(set(aliases.values())),'old_exact_slot_matches':sum(bool(x)for x in equal)})
# Hero-name proof: tactical renderer branches only on sign(side); named protagonist has no story-sprite1 override here.
hero={}
for name in [1,2,42]:
 hero[str(name)]=[run(21,'ally',d,p,name)['oam']for d in range(4)for p in range(2)]
assert hero['1']==hero['2']==hero['42']
data={'schema_version':1,'source_revision':'956365ef33c63751e7afd03f05e600d7728549da','source_rom_sha256':hashlib.sha256(SRC.rom).hexdigest(),'entry':'bank011:L0BB5B1','caller':'bank006:L06BA0A→bank11 dispatch3 L0BB59D','native_render':'bank015:L0FE80F with bank8/0589=0','source_only':True,'runtime_integrated':False,'records':records,'hero_tactical_name_independence':{'names_tested':[1,2,42],'class_id':21,'all8_oam_equal':True,'note':'No hero personal sprite1 branch in tactical renderer; village L0791BC has a separate name/slot override.'},'old_source_audit':{'old_lookup':'bank008:L08A779 via village/world actor setup bank007:L0791BC','native_village_chr':'bank007:L079136/L079158 calls L0FD39A then overwrites sprite CHR with30 via L0FCA48/L0FCA50;26is only earlier default','old_png_status':'Hybrid extraction, not verified original scene imagery; freeze unchanged and compare visibly with corrected native references.'},'summary':summary}
(HERE/'overlay.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');(HERE/'audit-summary.json').write_text(json.dumps({'summary':summary,'hero_tactical_name_independence':data['hero_tactical_name_independence'],'old_source_audit':data['old_source_audit']},ensure_ascii=False,indent=2)+'\n')
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for cid,side in [(3,'ally'),(3,'enemy'),(21,'ally'),(14,'ally'),(6,'ally')]:
 r=records[f'class-{cid}-{side}'];a=Image.open(HERE/r['source_atlas']).convert('RGBA');w,h=r['source_frame_size'];board=Image.new('RGBA',(1088,704),(230,230,219,255));dr=ImageDraw.Draw(board)
 for i,d in enumerate(DIRS):
  dr.text((i*272+16,12),f'{d} 原CPU CHR{r["source_chr"]}',font=font,fill=(30,40,50))
  for ph in range(2):
   fr=a.crop(((i*2+ph)*w,0,(i*2+ph+1)*w,h));board.alpha_composite(fr.resize((w*8,h*8),Image.Resampling.NEAREST),(i*272+8,64+ph*272))
 board.convert('RGB').save(HERE/f'{cid}-{side}-directions-light.png',optimize=True)
print(json.dumps({'groups':len(records),'source_slots':sum(r['source_frame_count']for r in records.values()),'unique_slots':sum(len(r['unique_source_slots'])for r in records.values()),'output':str(HERE),'class3':records['class-3-ally']['source_chr'],'hero':True}))
