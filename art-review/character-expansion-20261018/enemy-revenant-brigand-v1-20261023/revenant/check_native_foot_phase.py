#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
OUT=Path(__file__).resolve().parent
META=json.loads((OUT/'asset-manifest.json').read_text());REG={(r['kind'],r['frame']):r for r in META['registration']}
SKIN={(170,166,188),(187,193,214)}
rows=[]
for i in range(8):
 old=Image.open(OUT/'source'/f'native-walk-{i:03}.png').convert('RGBA');new=Image.open(OUT/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA')
 old_skin=[(x,y)for y in range(19,24)for x in range(32)if old.getpixel((x,y))==(254,204,197,255)]
 new_skin=[(x,y)for y in range(80,96)for x in range(128)if (p:=new.getpixel((x,y)))[3]and p[:3]in SKIN]
 old_y=max(y for x,y in old_skin);new_y=max(y for x,y in new_skin)
 old_bottom=[x for x,y in old_skin if y==old_y];new_bottom=[x for x,y in new_skin if y>=new_y-1]
 record={'slot':i,'direction':['up','up','right','right','down','down','left','left'][i],'native_lower_calf_skin_pixels':old_skin,'native_lowest_skin_y':old_y,'native_lowest_skin_x':old_bottom,'redraw_lowest_skin_y':new_y,'redraw_lowest_skin_x':new_bottom,'redraw_head_x':REG[('walk',i)]['actual_landmark'][0],'native_lower_leg_span':max(x for x,y in old_skin)-min(x for x,y in old_skin)+1,'redraw_lower_leg_span_output_px':max(x for x,y in new_skin)-min(x for x,y in new_skin)+1,'output_sha256':hashlib.sha256((OUT/'tactical-walk'/f'frame-{i:03}.png').read_bytes()).hexdigest()}
 if i in[0,1,4,5]:
  record['native_screen_support_side']='left'if sum(old_bottom)/len(old_bottom)<16 else'right'
  record['redraw_screen_support_side']='left'if sum(new_bottom)/len(new_bottom)<record['redraw_head_x']else'right'
  record['support_phase_matches']=record['native_screen_support_side']==record['redraw_screen_support_side']
 else:record['native_phase']='open_stride'if i in[2,6]else'passing_close'
 rows.append(record)
assert all(r.get('support_phase_matches',True)for r in rows)
for a,b in [(2,3),(6,7)]:
 assert rows[a]['native_lower_leg_span']>rows[b]['native_lower_leg_span']
 assert rows[a]['redraw_lower_leg_span_output_px']>rows[b]['redraw_lower_leg_span_output_px']
report={'passed':True,'scope':'native slot identity and planted-foot phase, not merely alternating new drawings','correction':'complete generated poses assigned up0<-old1/up1<-old0 and down4<-old5/down5<-old4; native source/timing unchanged','side_order':'source2/6 open stride -> source3/7 passing close, verified lower leg span contraction','native_timing':{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7],'ticks_per_phase':16},'slots':rows}
(OUT/'native-foot-phase-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for light in [False,True]:
 bg=(234,236,232)if light else(30,39,52);fg=(27,34,48)if light else(235,238,240)
 out=Image.new('RGB',(4*320,4*310),bg);d=ImageDraw.Draw(out)
 for direction,ids in enumerate([[0,1],[2,3],[4,5],[6,7]]):
  for phase,i in enumerate(ids):
   for version in ['native','redraw']:
    col=phase*2+(version=='redraw');path=OUT/'source'/f'native-walk-{i:03}.png'if version=='native'else OUT/'tactical-walk'/f'frame-{i:03}.png';im=Image.open(path).convert('RGBA').resize((320,240),Image.Resampling.NEAREST);x=col*320;y=direction*310+30;out.paste(im,(x,y),im)
    line=rows[i].get('native_screen_support_side')if version=='native'else rows[i].get('redraw_screen_support_side')
    text=f'{version} slot{i} '+(f'support {line}'if line else rows[i]['native_phase'])
    d.text((x+5,direction*310+6),text,fill=fg)
    d.text((x+5,y+245),'same native 16-tick phase order',fill=fg)
 out.save(OUT/f'native-foot-phase-{"light"if light else"dark"}.png',optimize=True)
print('NATIVE_FOOT_PHASE passed',[(r['slot'],r.get('native_screen_support_side',r.get('native_phase')),r.get('redraw_screen_support_side'))for r in rows])
