#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import sys,json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent.parent;REPO=EXP.parent.parent
sys.path.insert(0,str(REPO/'tools'));from extract_full_graphics import Source,signed
from fe2_source_cpu import CPU
S=Source(REPO/'.reference/fe2-source-956365ef');data=json.loads((HERE/'overlay.json').read_text());audit=[];oldshape=[]
def static_oam(row,side):
 frame=S.rw(8,0x8000+row['source_frame_index']*2);layout=S.rw(8,frame);out=[];j=0;flip=row['source_global_flip'];pal=0 if side=='ally' else 3
 while j<64:
  a=S.rb(8,layout+j*3)
  if a&0xf0==0xf0:break
  y=signed(S.rb(8,layout+j*3+1));x=signed(S.rb(8,layout+j*3+2));tile=S.rb(8,frame+2+j)
  if flip:a^=64;x=-x-8
  out.append([(80+y-1)&255,tile,a|pal,(64+x)&255]);j+=1
 assert j<64
 return out
for key,r in data['records'].items():
 atlas=Image.open(HERE/r['source_atlas']).convert('RGBA');w,h=r['source_frame_size'];fs=[atlas.crop((f*w,0,(f+1)*w,h))for f in range(8)];mirrors={};art=[]
 for i,fr in enumerate(fs):
  match=next((j for j in art if fs[j].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==fr.tobytes()),None)
  if match is None:art.append(i)
  else:mirrors[str(i)]={'source_slot':match,'transform':'horizontal-mirror-full-canvas','rgba_exact':True}
 r['exact_mirror_aliases']=mirrors;r['unique_art_source_slots_after_exact_mirror']=art
 for row in r['frame_mapping']:
  expected=static_oam(row,r['source_side']);assert expected==row['oam'],(key,row['source_slot']);audit.append({'id':key,'slot':row['source_slot'],'static_rom_oam_matches_cpu':True})
 old=Image.open(EXP/r['old_frozen_source']).convert('RGBA');ofs=[old.crop((i*32,0,(i+1)*32,24))for i in range(6)];matches=[]
 for i,fr in enumerate(fs):
  bb=fr.getbbox();tight=fr.crop(bb)
  for j,o in enumerate(ofs):
   ob=o.getbbox();ot=o.crop(ob)
   if ot.size!=tight.size:continue
   rgba=ot.tobytes()==tight.tobytes();alpha=ot.getchannel('A').tobytes()==tight.getchannel('A').tobytes()
   if rgba or alpha:matches.append({'corrected_slot':i,'old_slot':j,'rgba_exact_after_translation':rgba,'alpha_exact_after_translation':alpha,'old_to_corrected_offset':[bb[0]-ob[0],bb[1]-ob[1]]})
 r['old_frozen_tight_shape_matches']=matches;oldshape.append({'id':key,'matches':matches,'native_art_slots_after_mirror':len(art)})
classes=json.loads((EXP/'catalog/class-catalog.json').read_text())['classes'];data['current_game_class_bindings']=[{'class_id':r['class_id'],'display_name':r['name'],'source_class_id':r['source_class_id'],'ally_reference':f'class-{r["source_class_id"]}-ally','enemy_reference':f'class-{r["source_class_id"]}-enemy','note':'Current game maps this class to the listed native source; classes23/24 are not passed out-of-range into original22-class table.'}for r in classes]
# Run exact original phase branch across boundaries for representative named hero and flying class.
clocks=[]
for cid in [3,21]:
 for clock in [0,15,16,31,32,47,48,63]:
  c=CPU(S.rom);m=c.mem;m[0x7a]=0;m[0x7b]=0x60;m[0x6000]=1;m[0x505]=cid;m[0x504]=1;m[0x502]=64;m[0x503]=80;m[0x36]=clock;c.call(11,0xb5b1);o=[list(m[0x200+i:0x204+i])for i in range(0,m[0x3d],4)];expected=data['records'][f'class-{cid}-ally']['frame_mapping'][2+int(bool(clock&16))]['oam'];assert o==expected;clocks.append({'class_id':cid,'clock':clock,'phase':int(bool(clock&16)),'oam_match':True})
(HERE/'overlay.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');report={'passed':True,'cpu_oam_slots':len(audit),'independent_rom_table_decoder_matches':len(audit),'clock_boundaries':clocks,'frame_count':352,'native_art_slots_after_exact_mirror':sum(len(r['unique_art_source_slots_after_exact_mirror'])for r in data['records'].values()),'old_shape_reuse_candidates':oldshape,'classes_in_current_game_bindings':len(classes),'byte_comparison':'RGBA comparisons use image.size and image.tobytes(), alpha-only comparisons explicitly labeled.','not_run':'No game/browser execution, no edits to actual or frozen references.'};(HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'slots':len(audit),'native_art_slots':report['native_art_slots_after_exact_mirror'],'old_groups_with_any_matching_shape':sum(bool(r['matches'])for r in oldshape),'bindings':len(classes)}))
