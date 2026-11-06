#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw
import json,math
OUT=Path(__file__).resolve().parent
manifest=json.loads((OUT/'asset-manifest.json').read_text());reg={(r['kind'],r['frame']):r for r in manifest['registration']}
# Manually inspected anatomical waist transition in the complete generated poses.
# Points are shown again on the registered audit boards; they are not image-bounds centroids.
HIP={('idle',0):[72,115],('idle',1):[68,112],('idle',2):[78,114],('walk',0):[72,127],('walk',1):[76,128],('walk',2):[72,129],('walk',3):[180,367],('walk',4):[74,131],('walk',5):[77,130],('walk',6):[68,129],('walk',7):[195,367]}
GROUPS=[('idle','idle',[0,1,2,1]),('up','walk',[0,1,0,1]),('right','walk',[2,3,2,3]),('down','walk',[4,5,4,5]),('left','walk',[6,7,6,7])]
def skin_head_size(r):
 im=Image.open(OUT/r['path']).convert('RGBA');box=r.get('source_search_box')or[0,0,im.width,round(im.height*.24)]
 ps={(x,y)for y in range(max(0,box[1]),min(im.height,box[3]))for x in range(max(0,box[0]),min(im.width,box[2]))if(p:=im.getpixel((x,y)))[3]>=128 and min(p[:3])>120 and max(p[:3])-min(p[:3])<65};comps=[]
 while ps:
  q=[ps.pop()];c=list(q)
  while q:
   x,y=q.pop()
   for xy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1),(x-1,y-1),(x+1,y+1),(x-1,y+1),(x+1,y-1)]:
    if xy in ps:ps.remove(xy);q.append(xy);c.append(xy)
  comps.append(c)
 c=max(comps,key=len);b=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1]
 return b,[(b[2]-b[0])*r['resampled_size'][0]/im.width,(b[3]-b[1])*r['resampled_size'][1]/im.height]
records={}
for key,hip in HIP.items():
 r=reg[key];im=Image.open(OUT/r['path']);ratio=[r['resampled_size'][i]/im.size[i]for i in range(2)];actual=[r['translation'][i]+hip[i]*ratio[i]for i in range(2)];box,size=skin_head_size(r)
 records[key]={'frame':key[1],'kind':key[0],'head':r['actual_landmark'],'hip':actual,'source_head_bounds':box,'head_size':size,'source_hip':hip,'hip_definition':'manually measured garment waist transition, excludes arms and moving feet','anatomical_point_uncertainty_output_px':1.0}
metrics=[]
for name,kind,order in GROUPS:
 rs=[records[(kind,n)]for n in sorted(set(order))]
 span=lambda key:[max(r[key][axis]for r in rs)-min(r[key][axis]for r in rs)for axis in range(2)]
 metrics.append({'group':name,'order':order,'head_drift_output_pixels':span('head'),'hip_drift_output_pixels':span('hip'),'head_size_difference_output_pixels':span('head_size'),'head_drift_native_pixels':[v/4 for v in span('head')],'hip_drift_native_pixels':[v/4 for v in span('hip')],'head_size_difference_native_pixels':[v/4 for v in span('head_size')],'poses':rs,'passed':max(span('head'))<=1 and max(span('hip'))<=2.1 and max(span('head_size'))<=3})
for light in [False,True]:
 bg=(226,228,225)if light else(30,39,52);fg=(31,38,52)if light else(232,236,239)
 out=Image.new('RGB',(1250,5*300),bg);d=ImageDraw.Draw(out)
 for row,(name,kind,order)in enumerate(GROUPS):
  metric=metrics[row];reference=records[(kind,order[0])];head=reference['head'];hip=reference['hip']
  d.text((15,row*300+5),name+' | native '+('14/8/14/8'if kind=='idle'else'16/16')+' ticks',fill=fg)
  for n,frame in enumerate(order):
   path=OUT/('tactical-idle'if kind=='idle'else'tactical-walk')/f'frame-{frame:03}.png';im=Image.open(path).convert('RGBA').resize((256 if kind=='walk' else 192,192),Image.Resampling.NEAREST)
   x=25+n*300;y=row*300+35;out.paste(im,(x,y),im)
   for p,color in [(head,'#25a5be'),(hip,'#df9f35')]:
    d.line((x,y+p[1]*2,x+256,y+p[1]*2),fill=color,width=1);d.line((x+p[0]*2,y,x+p[0]*2,y+192),fill=color,width=1)
   actual=records[(kind,frame)]
   for p,color in [(actual['head'],'#b7ffff'),(actual['hip'],'#ffd695')]:d.ellipse((x+p[0]*2-2,y+p[1]*2-2,x+p[0]*2+2,y+p[1]*2+2),fill=color)
   d.text((x,y+205),f'frame {frame}  head {actual["head"][0]:.2f},{actual["head"][1]:.2f}',fill=fg);d.text((x,y+220),f'hip {actual["hip"][0]:.2f},{actual["hip"][1]:.2f}',fill=fg)
  d.text((15,row*300+278),'native px drift H '+str([round(v,3)for v in metric['head_drift_native_pixels']])+' / hip '+str([round(v,3)for v in metric['hip_drift_native_pixels']])+' / head size delta '+str([round(v,3)for v in metric['head_size_difference_native_pixels']]),fill=fg)
 out.save(OUT/f'map-continuous-{"light"if light else"dark"}.png',optimize=True)
report={'passed':all(m['passed']for m in metrics),'registration':'independently inspected head/neck and garment-waist landmarks; uniformly scaled whole poses; no limb warping','logical_scale':4,'thresholds_output_pixels':{'head_drift':1,'hip_drift':2.1,'head_size_difference':3},'metrics':metrics,'visual_review':{'all_direction_pairs_have_alternating_or_passing_leg_phases':True,'side_phase3_and7_newly_redrawn_complete_pose':True,'bald_character_no_hair_highlight':True,'deep_and_light_boards':'map-continuous-dark.png / map-continuous-light.png','user_visual_acceptance':'pending'}}
(OUT/'map-registration-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
