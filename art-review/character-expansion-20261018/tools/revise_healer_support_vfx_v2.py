#!/usr/bin/env python3
"""Four allied support-spell VFX revisions; native actor rows and contacts stay exact."""
from baseline_json import read_baseline
import argparse,copy,json,math,re,hashlib
from functools import lru_cache
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
from share_sage_mage_spells import sha
from revise_spellsword_jump_heal_v3 import effect_center
import import_knight_redraw_v3 as helper
import import_sniper_complete as io
REV='healer-support-vfx-v2-20261023';OUT=ROOT/REV;SRC=OUT/'source';io.OUT=OUT
G=[(53,110,78),(112,182,125),(196,233,181)]
R=[(126,54,65),(189,88,96),(237,167,157)]
B=[(52,119,187),(121,185,216),(200,233,236)]
REG=[]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def box(p):return[min(x for x,y in p),min(y for x,y in p),max(x for x,y in p)+1,max(y for x,y in p)+1]
def center(b):return[(b[0]+b[2])/2,(b[1]+b[3])/2]
@lru_cache(maxsize=100000)
def material(rgb,palette):return min(palette,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))
def quant(im,palette):
 p=tuple(palette);q=Image.new('RGBA',im.size);q.putdata([(*material(v[:3],p),255)if v[3]>=240 else(0,0,0,0)for v in im.getdata()]);return q
def groups(name,cols,rows,palette):
 raw=Image.open(SRC/name).convert('RGBA');px=raw.load();parts=helper.parts((x,y)for y in range(raw.height)for x in range(raw.width)if px[x,y][3]>=240);bins=[[]for _ in range(cols*rows)];cw,ch=raw.width/cols,raw.height/rows
 # Assign complete connected motifs/particles to their nearest cell. A ripple
 # crossing an artificial grid boundary must never be cut in half.
 for p in parts:
  if len(p)<2:continue
  x,y=center(box(p));col=min(cols-1,max(0,int(x/cw)));row=min(rows-1,max(0,int(y/ch)));bins[row*cols+col].extend(p)
 result=[]
 for i,p in enumerate(bins):
  assert p,(name,i);bb=box(p);q=Image.new('RGBA',(bb[2]-bb[0],bb[3]-bb[1]))
  for x,y in p:q.putpixel((x-bb[0],y-bb[1]),px[x,y])
  q=quant(q,palette);result.append(q);REG.append({'source':name,'cell':i,'source_bounds':bb,'source_opaque_pixels':len(p),'complete_components_kept':True,'alpha_threshold':240,'source_sha256':file_hash(SRC/name)})
 return result
def register(im,size,scaled,floor,label):
 dims=[max(1,round(im.width*scaled)),max(1,round(im.height*scaled))];small=im.resize(dims,Image.Resampling.NEAREST);q=Image.new('RGBA',size);at=[(size[0]-dims[0])//2,floor-dims[1]];q.alpha_composite(small,at);assert sum(p[3]>0 for p in q.getdata())==sum(p[3]>0 for p in small.getdata()),(label,'clipping',dims,at);return q
def board(entries,name):
 cw,ch=300,390;cols=4
 for light in[False,True]:
  q=Image.new('RGB',(cw*cols,52+ch*math.ceil(len(entries)/cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,243,242);d.text((q.width//2,25),'辅助法术 · 红色抽取 / 绿色泉水 / 蓝色传送',font=font(20),anchor='mm',fill=fg)
  for n,(label,im)in enumerate(entries):
   scale=min(1,(cw-32)/im.width,(ch-48)/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);x=n%cols*cw+(cw-im.width)//2;y=52+n//cols*ch+(ch-48-im.height)//2;q.paste(im,(x,y),im);d.text((n%cols*cw+cw//2,52+(n//cols+1)*ch-20),label,font=font(16),anchor='mm',fill=fg)
  io.save(q,name+('-light.png'if light else'-dark.png'),'generated VFX art review on both backgrounds')
def assets(data):
 red=groups('red-drain-master.png',4,2,R);pool=groups('green-spring-master.png',3,2,G);blue=groups('blue-pillar-master.png',3,2,B);defs={};entries=[]
 def add(eid,im,frame,anchor,purpose):
  path=io.save(im,'effects/'+eid+'.png',purpose);defs[eid]={'path':path,'frame_size':frame,'frames':1,'anchor':anchor,'default_facing':'left','flip_origin_offset':[0,0]};return eid
 for i,im in enumerate(red):
  q=register(im,(192,192),160/max(im.size),176,'red-art'+str(i));io.save(q,f'components/red-{i}.png','generated red energy component');entries.append(('红色 '+str(i),q))
 for i,im in enumerate(pool):
  q=register(im,(192,160),136/max(x.width for x in pool),144,'pool'+str(i));add('support_v2_spring_'+str(i),q.resize((384,320),Image.Resampling.NEAREST),[96,80],[48,64],'one broad green spring receives rain from the original group effect area; uniform scale');entries.append(('泉水 '+str(i),q))
 for i,im in enumerate(blue):
  q=register(im,(192,352),min(320/max(x.height for x in blue),160/max(x.width for x in blue)),336,'pillar'+str(i));add('support_v2_pillar_'+str(i),q,[48,88],[24,84],'blue teleport column, common ground base, open pixel strands');entries.append(('光柱 '+str(i),q))
 # All native drain orbs retain their exact old transparent envelope/anchor.
 a=next(a for a in data['actions']if a['key']=='class_17_ally_item_42');ids=list(dict.fromkeys(e['sprite']for f in a['frames']for e in f['effects']));replacements={}
 for n,eid in enumerate(ids):
  meta=data['effects'][eid];old=Image.open(ROOT/meta['path']).convert('RGBA');bb=old.getbbox()
  if bb is None:
   nid='support_v2_drain_'+eid;defs[nid]={**meta,'path':io.save(Image.new('RGBA',(old.width*4,old.height*4)),f'effects/{nid}.png','native empty orb slot; extraction flow remains a separate effect')};replacements[eid]=nid;continue
  art=red[7]if eid=='417803ca18cf79'else red[0 if n<5 else 1 if n<7 else 2 if n<12 else 3];w,h=meta['frame_size'];q=Image.new('RGBA',(w*4,h*4));scale=min((bb[2]-bb[0])*4/art.width,(bb[3]-bb[1])*4/art.height);small=art.resize((max(1,round(art.width*scale)),max(1,round(art.height*scale))),Image.Resampling.NEAREST);at=[round((bb[0]+bb[2])*2-small.width/2),round((bb[1]+bb[3])*2-small.height/2)];q.alpha_composite(small,at);nid='support_v2_drain_'+eid;defs[nid]={**meta,'path':io.save(q,f'effects/{nid}.png','red orb in original envelope; native position and flip unchanged')};replacements[eid]=nid
 for i,art in enumerate(red[4:]):
  size=(112,112)if i==0 else(96,48);q=register(art,size,min((size[0]-8)/art.width,(size[1]-8)/art.height),size[1]-4,'drain motion'+str(i));add('support_v2_extract_'+str(i),q,[size[0]/4,size[1]/4],[size[0]/8,size[1]/8],'red target suction spiral / directional energy wisp')
 # Group-heal has three extra native sparkle/ring sprites. Reuse the already
 # approved green ring bitmap, preserving their old position and envelope.
 ring=Image.open(ROOT/data['effects']['ally_heal_green_v3_f19761b48fda82']['path']).convert('RGBA');ring=ring.crop(ring.getbbox());greens={k:'ally_heal_green_v3_'+k for k in data['effects']if'ally_heal_green_v3_'+k in data['effects']}
 heal44=next(a for a in data['actions']if a['key']=='class_17_ally_item_44')
 for eid in{e['sprite']for f in heal44['frames']for e in f['effects']}:
  if eid in greens:continue
  meta=data['effects'][eid];old=Image.open(ROOT/meta['path']).convert('RGBA');bb=old.getbbox();q=Image.new('RGBA',(old.width*4,old.height*4));scale=min((bb[2]-bb[0])*4/ring.width,(bb[3]-bb[1])*4/ring.height);small=ring.resize((round(ring.width*scale),round(ring.height*scale)),Image.Resampling.NEAREST);q.alpha_composite(small,(round((bb[0]+bb[2])*2-small.width/2),round((bb[1]+bb[3])*2-small.height/2)));nid='support_v2_green_'+eid;defs[nid]={**meta,'path':io.save(q,f'effects/{nid}.png','approved green ring in native group-heal sparkle envelope')};greens[eid]=nid
 board(entries,'effect-poses');write(OUT/'asset-manifest.json',{'revision':REV,'tool':'built-in image_gen','palettes':{'red':R,'green':G,'blue':B},'assets':io.ASSETS,'registrations':REG,'new_effect_ids':list(defs)});return defs,replacements,greens
def center_of(data,e):
 meta=data['effects'][e['sprite']];im=Image.open(ROOT/meta['path']).convert('RGBA')
 if im.getbbox():return effect_center(data,e)
 return[e['position'][i]-meta['anchor'][i]+meta['frame_size'][i]/2+(meta.get('flip_origin_offset',[0,0])[i]if e.get('flip')else 0)for i in range(2)]
def event(eid,position,flip=False):return{'sprite':eid,'position':[round(v,3)for v in position],'flip':flip}
def rows_extended(a,end):
 rows=copy.deepcopy(a['frames']);last=copy.deepcopy(rows[-1]);last['effects']=[];rows.extend(copy.deepcopy(last)for _ in range(max(0,end-len(rows))));return rows
def revise(a,data,native,redmap,greens):
 key=a['key'];spell=int(re.search(r'_item_(\d+)',key).group(1));contact=a['contactTick'];original=a['frames'];count=len(original);contract={'key':key,'spell_id':spell,'native_ticks':count,'native_contact':contact,'additional_resolutions':0,'actor_rows_kept':True};end=count;rows=copy.deepcopy(original)
 if spell==41:
  heal=next(x for x in data['actions']if x['key']==key.replace('_item_41','_item_40'));target=center_of(data,heal['frames'][heal['contactTick']]['effects'][0]);end=max(count,contact+72);rows=rows_extended(a,end);rain_start=contact+12;rain_end=rain_start+54
  for t,row in enumerate(rows):
   if t<rain_start:row['effects']=copy.deepcopy(heal.get('revisedFrames',heal['frames'])[min(t,len(heal['frames'])-1)]['effects'])
   elif t<rain_end:row['effects']=[event('ally_heal_green_rain_v3_'+str((t-rain_start)//9+1),target)]
   else:row['effects']=[]
  contract.update(rain_start=rain_start,rain_end=rain_end,rain_ticks=54,restore40_rain_ticks=36,target_center=target)
 elif spell==42:
  start=next(t for t,r in enumerate(original)if r['effects']);first=original[start]['effects'][0];source=center_of(data,first);jump=next(t for t in range(start+1,count)if original[t]['effects']and original[t]['effects'][0]['position']!=first['position']);destination=center_of(data,original[jump]['effects'][0]);flip=destination[0]<source[0]
  for t,row in enumerate(rows):
   for e in row['effects']:e['sprite']=redmap[e['sprite']]
   if start<=t<start+24:row['effects'].append(event('support_v2_extract_0',source,flip))
   if start<=t<=contact:
    for j in range(3):
     age=t-start-j*7
     if age<0:continue
     u=(age%32)/31;pos=[source[0]+(destination[0]-source[0])*u,source[1]+(destination[1]-source[1])*u-8*math.sin(math.pi*u)];row['effects'].append(event('support_v2_extract_'+str(1+j%3),pos,flip))
  contract.update(extraction_start=start,target=source,caster_energy_center=destination,flow_direction='target_to_caster',native_orb_positions_unchanged=True)
 elif spell==43:
  target=native['source_actor_origins']['enemy'];raised=next(t for t,r in enumerate(original)if r['frame'] in([20,19]if native['source_class_id']==17 else[8]));start=raised+8;finish=min(count,contact+42)
  for t,row in enumerate(rows):
   if t<start or t>=finish:row['effects']=[]
   elif t<start+18:row['effects']=[event('support_v2_pillar_'+str(min(2,(t-start)//6)),target)]
   elif t<contact+6:row['effects']=[event('support_v2_pillar_'+str(2+((t-start)//8)%2),target)]
   else:row['effects']=[event('support_v2_pillar_'+str(4 if t<contact+24 else 5),target)]
  contract.update(column_start=start,column_end=finish,target_ground=target,recipient_location_from_native_formation=True,no_extra_action=True)
 elif spell==44:
  start=next(t for t,r in enumerate(original)if r['effects']);charge=original[start]['effects'][0]['position'];targets=[]
  visible={eid for eid in{e['sprite']for r in original for e in r['effects']}if Image.open(ROOT/data['effects'][eid]['path']).convert('RGBA').getbbox()}
  for row in original:
   for e in row['effects']:
    if e['sprite']in visible and e['position']!=charge and e['position']not in targets:targets.append(e['position'])
  assert len(targets)>=3,(key,targets)
  last= max(t for t,r in enumerate(original)if r['effects']);rain_start=contact+8;rain_end=rain_start+54;pool_end=rain_end+60;end=max(count,pool_end);rows=rows_extended(a,end);centers=[];grounds=[]
  for pos in targets:
   e={'sprite':'f19761b48fda82','position':pos,'flip':original[start]['effects'][0].get('flip',False)};centers.append(center_of(data,e));grounds.append([centers[-1][0],pos[1]+8])
  basin=[(min(p[0]for p in grounds)+max(p[0]for p in grounds))/2,max(p[1]for p in grounds)]
  for t,row in enumerate(rows):
   if t<=last:
    for e in row['effects']:e['sprite']=greens[e['sprite']]
   elif t<rain_start:row['effects']=[event('ally_heal_green_v3_f19761b48fda82',pos,original[start]['effects'][0].get('flip',False))for pos in targets]
   elif t<rain_end:
    u=(t-rain_start)/53;row['effects']=[event('ally_heal_green_rain_v3_'+str((t-rain_start)//9+1),[p[0],p[1]+max(0,basin[1]-(p[1]+26))*u*u])for p in centers]
   elif t<pool_end:
    phase=min(5,(t-rain_end)//10);row['effects']=[event('support_v2_spring_'+str(phase),basin)]
   else:row['effects']=[]
  contract.update(original_visible_effect_slots=targets,rain_centers=centers,pool_ground=basin,rain_start=rain_start,rain_end=rain_end,pool_start=rain_end,pool_end=pool_end,rain_ticks=54,one_coalesced_basin=True)
 else:raise ValueError(spell)
 assert all({k:v for k,v in r.items()if k!='effects'}=={k:v for k,v in o.items()if k!='effects'}for r,o in zip(rows,original))
 note={41:'远程恢复沿用恢复的绿色光环与雨滴，雨滴延长至54帧，收尾只延长展示，不追加治疗结算。',42:'吸血统一柔和红色；起始目标处出现抽取旋纹，红色能量持续由目标牵引至施法者。原伤害与吸血结算保持。',43:'传送增加目标处蓝色光柱，由地面光环升起，在原结算后化为蓝色光丝；不增加行动或修改落点规则。',44:'全体恢复统一绿色，多目标光环收尾化成绿色雨滴，继而在下方汇聚同色泉水；收尾只延长展示，不增加恢复次数。'}[spell]
 row={'source_frames_sha256':sha(original),'frames':rows[:count],'events':contract,'note':note}
 if len(rows)>count:row.update(tail_frames=rows[count:],tail_label='绿色雨滴与泉水收尾'if spell==44 else'较长绿色雨滴收尾')
 contract.update(review_tail_ticks=len(rows)-count,display_ticks=len(rows));return row,contract
def main(publish=False,art_only=False):
 b=json.loads((OUT/'baseline.json').read_text());d=b['gallery'];defs,redmap,greens=assets(d)
 if art_only:print(json.dumps({'art_assets':len(io.ASSETS),'effect_ids':len(defs)}),flush=True);return
 native=read_baseline(ROOT/'healer-saint-complete-v1-20261023/baseline.json')['classes'];drafts={};contracts=[]
 for c in[17,18]:
  path=f'professions/class-{c}-ally/battle/frame_mapping.json';m=copy.deepcopy(b['mappings'][path]);old=(ROOT/path).parent.joinpath(m['review_timeline']).resolve();timeline=json.loads(old.read_text());timeline=copy.deepcopy(timeline);timeline.update(revision=REV,runtime_integrated=False)
  if c==17:timeline.setdefault('effects',{}).update(defs)
  for a in d['actions']:
   if a['profile']!=f'professions-class-{c}-ally-battle'or a['kind']!='attack':continue
   spell=int(re.search(r'_item_(\d+)',a['key']).group(1))
   if spell not in[41,42,43,44]:continue
   row,contract=revise(a,d,native[str(c)]['variants'][a['key']],redmap,greens);timeline.setdefault('actions',{})[a['key']]=row;contracts.append(contract)
  write(OUT/f'class-{c}-motion.json',timeline);m.update(revision=REV,review_timeline=f'../../../{REV}/class-{c}-motion.json',qa_report=f'../../../{REV}/verification.json',review_note='疗愈师／济世术师辅助法术修订：吸血红色抽取，远程恢复绿色长雨滴，全体恢复绿色雨滴汇成泉水，传送蓝色光柱。人物、宝瓶与法杖、原始动作、目标及结算保持；绿色雨滴和泉水只延长展示收尾。');drafts[path]=m
 assert len(contracts)==48;write(OUT/'mapping-drafts.json',drafts);write(OUT/'spell-contracts.json',{'revision':REV,'actions':contracts,'affected_classes':[17,18],'affected_spells':[41,42,43,44],'mechanics_changed':False,'runtime_integrated':False})
 if publish:
  for path,m in drafts.items():write(ROOT/path,m)
 print(json.dumps({'effect_ids':len(defs),'variants':len(contracts),'published':publish,'max_review_tail_ticks':max(c['review_tail_ticks']for c in contracts)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');p.add_argument('--art-only',action='store_true');a=p.parse_args();main(a.publish,a.art_only)
