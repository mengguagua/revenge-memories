from pathlib import Path
from PIL import Image
import json
SRC=Path(__file__).resolve().parent
native=json.loads((SRC/'native-landmarks.json').read_text())
boxes={33:[0,0,80,65],34:[0,0,80,65],35:[10,0,110,65],36:[20,0,130,60],37:[25,0,130,55],38:[20,0,120,60],39:[20,0,120,55],40:[20,0,110,55],43:[85,0,155,65],44:[55,0,125,65],45:[80,45,150,120],46:[30,65,110,140],48:[0,30,65,110]}
def components(points):
 ps=set(points);out=[]
 while ps:
  q=[ps.pop()];part=list(q)
  while q:
   x,y=q.pop()
   for xy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1),(x-1,y-1),(x+1,y+1),(x-1,y+1),(x+1,y-1)]:
    if xy in ps:ps.remove(xy);q.append(xy);part.append(xy)
  out.append(part)
 return sorted(out,key=len,reverse=True)
rows=[]
for kind,ids in [('idle',range(3)),('walk',range(8)),('battle',list(range(33,47))+[48])]:
 for i in ids:
  source_i={0:1,1:0,4:5,5:4}.get(i,i) if kind=='walk' else i
  file=f'fix-walk-{i:03}.png'if kind=='walk'and i in[3,7]else f'raw-{kind}-{source_i:03}.png'
  im=Image.open(SRC/file).convert('RGBA');landmark=native[kind][str(i)]
  if kind=='battle'and i in[41,42]:
   height=16 if i==41 else 4;scale=height/im.height;point=[im.width/2,im.height-1 if i==41 else im.height/2]
  else:
   box=boxes[i]if kind=='battle'else[0,0,im.width,round(im.height*.24)]
   ps=[(x,y)for y in range(max(0,box[1]),min(im.height,box[3]))for x in range(max(0,box[0]),min(im.width,box[2]))if (p:=im.getpixel((x,y)))[3]>=128 and min(p[:3])>120 and max(p[:3])-min(p[:3])<65]
   c=components(ps)[0];b=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1]
   point=[(b[0]+b[2])/2,(b[1]+b[3])/2];floor=64 if kind=='battle' else 20 if kind=='idle' else 24
   scale=(floor-landmark['point'][1])*4/(im.height-point[1])
  rows.append({'kind':kind,'frame':i,'generated_pose_index':source_i,'path':'source/'+file,'landmark_kind':landmark['landmark_kind'],'source_landmark':point,'target_native_landmark':landmark['point'],'scale':scale,'source_search_box':boxes.get(i)if kind=='battle'else[0,0,im.width,round(im.height*.24)],'registration_note':'Complete generated pose, source anatomical landmark and original ground line; uniform scale only. Passing phases3/7 were redrawn as full images. Up0/1 and down4/5 complete source drawings are assigned in the native planted-foot order, proven by lower calf pixels.'})
(SRC/'import-plan.json').write_text(json.dumps({'poses':rows,'new_art_provenance':'Built-in ImageGen complete posed bodies; no code-generated anatomy','native_reference':'native-baseline.json'},ensure_ascii=False,indent=2)+'\n')
print([(r['kind'],r['frame'],r['source_landmark'],round(r['scale'],3))for r in rows])
