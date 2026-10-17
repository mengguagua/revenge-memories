#!/usr/bin/env python3
from pathlib import Path
import sys,json
from PIL import Image
R=Path(__file__).resolve().parents[1];S=R/'source/characters/original-motion';sys.path.insert(0,str(R.parent/'tools'))
from extract_full_graphics import Source,make_sheet,signed,color,VILLAGE_TABLES
src=Source(R.parent/'.reference/fe2-source-956365ef');b=src.b[10];records={}
# L0791BC: protagonists use sprite1/2. Others use L08A738/L08A779
# (class6→$31, class12→$34, class14→$30). L0FD3B5 sets CHR26.
for role,sid in [('hunapu',1),('otto',49),('daan',52),('civilian',48)]:
 frames=[]
 for table in VILLAGE_TABLES:
  raw=b[b[table]['dw'][sid-1]]['db'];entries=[]
  for j in reversed(range(raw[0])):
   y,t,a,x=raw[1+4*j:5+4*j];im=color(src.tiles[26][t],[15,32,34,15])
   if a&64:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   if a&128:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
   entries.append((signed(x)-8,signed(y),im))
  frames.append(entries)
 sheet,size,anchor,bounds=make_sheet(frames,ground=8,minimum=(24,24));path=S/f'tactical-walk-{role}.png';sheet.save(path,optimize=True)
 sheet.resize((sheet.width*6,sheet.height*6),Image.Resampling.NEAREST).save(path.with_name(f'tactical-guide-{role}.png'),optimize=True)
 records[role]={'path':str(path.relative_to(R)),'frame_size':size,'anchor':anchor,'source_oam':[b[t]['dw'][sid-1]for t in VILLAGE_TABLES],'source_chr':26,'source_sprite_id':sid,'source_class_lookup':'bank008:L08A779 and bank007:L0791BC','source_chr_lookup':'bank015:L0FD3B5','frame_ticks':16,'pixels_per_tick':1,'bounds':bounds}
(S/'tactical-walk-source.json').write_text(json.dumps(records,indent=2)+'\n')
print('ACTUAL_TACTICAL_WALK',records)
