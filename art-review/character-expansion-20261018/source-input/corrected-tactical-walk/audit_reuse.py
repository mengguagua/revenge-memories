#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json,sys,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent.parent;REPO=EXP.parent.parent
sys.path.insert(0,str(REPO/'tools'));from extract_full_graphics import Source
D=json.loads((HERE/'overlay.json').read_text());summ=[]
def palette_isomorphic(a,b):
 if a.size!=b.size or a.getchannel('A').tobytes()!=b.getchannel('A').tobytes():return False,[]
 pairs=set((x,y)for x,y in zip(a.getdata(),b.getdata())if x[3]);forward={};back={}
 for x,y in pairs:
  if x in forward and forward[x]!=y or y in back and back[y]!=x:return False,[]
  forward[x]=y;back[y]=x
 return True,[{'old':list(x),'new':list(y)}for x,y in sorted(pairs)]
for key,r in D['records'].items():
 cid=r['class_id'];side=r['source_side'];staticpath=EXP/f'source-input/legacy-assets/assets/original/graphics/map_units/class_{cid}_{side}.png';static=Image.open(staticpath).convert('RGBA');old=[static.crop((i*24,0,(i+1)*24,24))for i in range(6)];atlas=Image.open(HERE/r['source_atlas']).convert('RGBA');w,h=r['source_frame_size'];matches=[]
 for i in range(8):
  f=atlas.crop((i*w,0,(i+1)*w,h));fb=f.getbbox();ft=f.crop(fb)
  for j,o in enumerate(old):
   for mirrored in [False,True]:
    q=o.transpose(Image.Transpose.FLIP_LEFT_RIGHT)if mirrored else o;ob=q.getbbox();ot=q.crop(ob)
    if ot.size!=ft.size:continue
    rgba=ot.tobytes()==ft.tobytes();alpha=ot.getchannel('A').tobytes()==ft.getchannel('A').tobytes();pal,mapping=palette_isomorphic(ot,ft)
    if rgba or alpha and pal:matches.append({'corrected_slot':i,'direction':r['frame_mapping'][i]['direction'],'phase':r['frame_mapping'][i]['phase'],'idle_source_frame':j,'mirror_static_full_canvas':mirrored,'translation_after_mirror':[fb[0]-ob[0],fb[1]-ob[1]],'rgba_exact':rgba,'alpha_exact':alpha,'palette_structure_bijective':pal,'palette_mapping':mapping})
 r['verified_static_idle_reuse']=matches;r['static_idle_source']=str(staticpath.relative_to(EXP));summ.append({'id':key,'slots_with_idle_reuse':sorted(set(m['corrected_slot']for m in matches)),'match_count':len(matches),'matches':matches})
S=Source(REPO/'.reference/fe2-source-956365ef');ff={str(ch):{'nonzero_2bpp_pixels':sum(v!=0 for v in S.tiles[ch][255].getdata()),'tile_sha256':hashlib.sha256(S.tiles[ch][255].tobytes()).hexdigest()}for ch in [19,26,30]};D['old_ff_tile_correction']={'source_tile_id':255,'banks':ff,'conclusion':'$FF is a CHR tile index, not an empty-tile instruction. Earlier class6 missing-head conclusion used wrong CHR26 with village OAM. Correct tactical mover usesCHR19 and different layouts; old semantic missing-head repair is historical, not original tactical evidence.'}
(HERE/'overlay.json').write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n');(HERE/'static-idle-reuse.json').write_text(json.dumps({'strict_proof':'size+fullRGBA bytes after permitted exact full-frame mirror and integer translation, or exactalpha plus globally bijective palette mapping','groups':summ,'ff_tile_correction':D['old_ff_tile_correction']},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'matched_groups':sum(bool(r['matches'])for r in summ),'matched_slots':sum(len(r['slots_with_idle_reuse'])for r in summ),'required_matched_slots':sum(len(r['slots_with_idle_reuse'])for r in summ if D['records'][r['id']]['scope']=='required_source'),'matches':[(r['id'],r['slots_with_idle_reuse'])for r in summ if r['matches']],'ff':ff}))
