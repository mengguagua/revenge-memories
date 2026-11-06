#!/usr/bin/env python3
"""Sequential petrifying gaze pulses; retain the approved Death VFX and actor."""
import argparse,copy,json,subprocess
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
import review_rift_mage_death_v2 as common

ROOT=common.ROOT;REV='rift-mage-medusa-vfx-v3-20261024';OUT=ROOT/REV
MP=common.MP;PREFIX='professions-class-16-enemy-battle--class_16_enemy_item_34'
HEADS={'native-5871fa30fecadf','native-821fd20dcf1e02','native-007073f98642b3'}
STARTS=[92,145,198,251,304,357,410,463]
def owns(a):return a['id'].startswith(PREFIX)
def write(p,d):common.write(p,d)
def call(name,*args):
 previous=common.OUT,common.PREFIX;common.OUT,common.PREFIX=OUT,PREFIX
 try:return getattr(common,name)(*args)
 finally:common.OUT,common.PREFIX=previous

def baseline():
 p=OUT/'baseline.json'
 if not p.exists():
  d=json.loads((ROOT/'demos/gallery-data.json').read_text());m=json.loads(MP.read_text());profile=next(p for p in d['profiles']if p['id']=='professions-class-16-enemy-battle')
  write(p,{'mapping':m,'timeline':json.loads((MP.parent/m['review_timeline']).resolve().read_text()),'actions':[a for a in d['actions']if owns(a)],'head_effects':{k:d['effects'][k]for k in HEADS},'body_files':{p:common.shared.sha(ROOT/p)for p in profile['newFrames'].values()},'confirmed_death_digests':{a['id']:a['contentDigest']for a in d['actions']if a['key'].startswith('class_16_enemy_item_33')}})
 return json.loads(p.read_text())

def rays(row,age,defs):
 if age>=25:return []
 head=next(e for e in row['effects']if e['sprite']in HEADS);left=head['position'][0]-24;top=head['position'][1]-16
 front=min(1,(age+1)/13);tail=max(0,(age-18)/7);effects=[]
 # The native face is tilted; the lower opening is its mouth. Register the
 # visible eye separately for the final open-mouth pose.
 eye=(27.5,23.5)if head['sprite']=='native-007073f98642b3'else(27,24)
 for eye,target in[(eye,(176,112))]:
  start=[left+eye[0],top+eye[1]]
  a=[start[i]+(target[i]-start[i])*tail for i in(0,1)];b=[start[i]+(target[i]-start[i])*front for i in(0,1)]
  at=[round(x*4)/4 for x in a];size=[max(.25,round((b[i]-a[i])*4)/4)for i in(0,1)];key='review-c16-medusa-ray-'+str(round(size[0]*4))+'-'+str(round(size[1]*4))
  defs[key]={'path':'../../../'+REV+'/effects/petrifying-ray.png','frame_size':size,'frames':1,'anchor':[0,0],'flip_origin_offset':[0,0],'source':'code-native petrifying-ray.svg; native Medusa three-color palette'}
  effects.append({'sprite':key,'position':at,'flip':False,'priority':0})
 return effects

def prepare():
 b=baseline();timeline=copy.deepcopy(b['timeline']);timeline.update(revision=REV,runtime_integrated=False);defs={};pending=[]
 for a in b['actions']:
  rows=copy.deepcopy(a['frames'])
  for tick,row in enumerate(rows):
   for start in STARTS:
    if 0<=tick-start<25:row['effects']+=rays(a['frames'][tick],tick-start,defs)
  pending.append((a,rows))
 timeline.setdefault('effects',{}).update(defs);effects=json.loads((ROOT/'demos/gallery-data.json').read_text())['effects'];effects.update({k:{**v,'path':REV+'/effects/petrifying-ray.png'}for k,v in defs.items()})
 for a,rows in pending:
  timeline['actions'][a['key']]={'source_frames_sha256':common.digest(a['frames']),'frames':rows,'close_camera':common.camera(a,rows,effects),'events':{'petrifying_gaze_pulse_start_ticks':STARTS,'pulse_duration_ticks':25,'pulse_count':8,'rays_per_pulse':1,'emitter':'visible eye; native lower opening identified as mouth','last_gaze_arrival_tick':475,'native_total_ticks':502,'native_actor_and_head_tracks_unchanged':True,'damage_settlements':1,'runtime_petrification_status_added':False},'note':'美杜莎：攻击过程中由蛇首可见眼部陆续射出八轮石化光线，光线依次伸出、到达目标并收尾；最后一道在原第476帧结算时刻到达。保留原蛇首、持杖人物、502帧程序及一次结算，仅补充本法术视觉。'}
 write(OUT/'enemy-spell-motion.json',timeline);mapping=json.loads(MP.read_text());mapping.update(review_timeline='../../../'+REV+'/enemy-spell-motion.json',effect_revision=REV);write(MP,mapping)
 asset=OUT/'effects/petrifying-ray.png'
 with Image.open(asset)as im:record={'path':common.rel(asset),'size':list(im.size),'bytes':asset.stat().st_size,'sha256':common.shared.sha(asset),'purpose':'石化光线：SVG矢量母稿栅格化，按光线起终点登记','source':'effects/petrifying-ray.svg','palette':['#007c8d','#9290ff','#ffffff']}
 write(OUT/'asset-manifest.json',{'revision':REV,'assets':[record],'new_effect_definitions':len(defs),'source_head_pixels_unchanged':True,'runtime_integrated':False})
 write(OUT/'action-effect-mapping.json',{'actor_id':'class-16-enemy','card_id':34,'card_name':'美杜莎','current_gameplay_effect':'命中按目标当前生命减至1计算，现未投放；未新增石化状态或多次伤害','actions':[{'id':a['id'],'visual_pulse_start_ticks':STARTS,'visual_gaze_arrival_tick':475,'effect_contact_tick':a['contactTick'],'contact_count':1,'total_ticks':502}for a,_ in pending]})

def verify(data):
 b=baseline();original={a['id']:a for a in b['actions']};errors=[];checks=0;records=[]
 for a in data['actions']:
  if a['id']in b['confirmed_death_digests']:assert a['contentDigest']==b['confirmed_death_digests'][a['id']]
  if not owns(a):continue
  old=original[a['id']];rows=a['revisedFrames']
  for field in['frames','origin','fps','duration','contactTick','reviewTailFrames']:assert a.get(field)==old.get(field),(a['id'],field)
  assert len(rows)==502 and a['contactTick']==475 and a['ready'];active=[]
  for tick,row in enumerate(rows):
   native=a['frames'][tick];assert common.body(row)==common.body(native);assert[e for e in row['effects']if e['sprite']in HEADS]==native['effects'];checks+=1
   ray_count=sum(e['sprite'].startswith('review-c16-medusa-ray-')for e in row['effects']);expected=1 if any(0<=tick-start<25 for start in STARTS)else 0;assert ray_count==expected,(tick,ray_count)
   if ray_count:active.append(tick)
   for e in row['effects']:
    m=data['effects'][e['sprite']];at=[e['position'][i]-m['anchor'][i]for i in(0,1)];box=common.V.box_at(common.V.image(m['path']),at,m['frame_size'],e.get('flip',False));checks+=1
    if common.V.outside(box,a.get('viewport',data['viewport'])):errors.append({'id':a['id'],'tick':tick,'scene':box})
    c=a['closeCamera'];view=[a['origin'][i]+c['offset'][i]for i in(0,1)]+c['size']
    if common.V.outside(box,view):errors.append({'id':a['id'],'tick':tick,'close':box})
  assert len(active)==200 and active[-1]==487;records.append({'id':a['id'],'source_actor_and_head_exact':True,'pulse_count':8,'pulse_starts':STARTS,'last_gaze_arrival_tick':475,'contact_tick':475,'total_ticks':502,'final_ray_tick':487})
 assert len(records)==6
 for path,sha in b['body_files'].items():assert common.shared.sha(ROOT/path)==sha
 write(OUT/'checks.json',{'passed':not errors,'checks':checks,'actions':records,'errors':errors,'confirmed_death_tracks_unchanged':True,'body_assets_unchanged':True,'runtime_integrated':False});assert not errors,errors[:3]

def export(data):
 records=[];videos=[]
 for a in data['actions']:
  if not owns(a):continue
  for close in[False,True]:
   records.append(common.E.export(data,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False)));suffix='--close'if close else'';p=ROOT/'demos/videos'/(a['id']+suffix+'.mp4')
   v=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,duration','-of','json',str(p)],text=True))['streams'][0];assert int(v['nb_read_frames'])==502;videos.append({'path':common.rel(p),'frames':502,'seconds':float(v['duration'])})
 write(OUT/'export-report.json',{'exports':records,'decoded_videos':videos,'scope':'six enemy16 Medusa variants, scene and close views'})

def previews(data):
 a=next(a for a in data['actions']if a['id']==PREFIX);profile=next(p for p in data['profiles']if p['id']==a['profile']);ticks=[100,120,206,365,475,501]
 for light in[False,True]:
  panels=[common.E.render_panel(data,profile,a,a['revisedFrames'][tick],True,3,light,True).convert('RGB')for tick in ticks];w,h=panels[0].size;fg=(23,38,56)if light else(235,243,242);board=Image.new('RGB',(w*3,(h+44)*2),(220,222,216)if light else(32,45,53));draw=ImageDraw.Draw(board)
  for n,(tick,panel)in enumerate(zip(ticks,panels)):
   x=n%3*w;y=n//3*(h+44);board.paste(panel,(x,y+38));label='光线陆续射出'if tick in[100,206,365]else'发射间隔'if tick==120 else'原结算时刻'if tick==475 else'光线收尾后'
   draw.text((x+w/2,y+18),f'{tick+1} / 502 · '+label,font=common.E.font(16),anchor='mm',fill=fg)
  board.save(OUT/('phases-light.png'if light else'phases-dark.png'),optimize=True)

def merge(data):
 before=json.loads((ROOT/'demos/gallery-data.json').read_text());old_ids=set(before['effects']);approved=baseline()['confirmed_death_digests']
 assert all(a['contentDigest']==approved[a['id']]for a in before['actions']if a['id']in approved)
 call('merge',data)
 report=json.loads((OUT/'merge-report.json').read_text());effects=json.loads((OUT/'enemy-spell-motion.json').read_text())['effects']
 report.update(new_effect_definitions=len(set(effects)-old_ids),confirmed_death_actions_unchanged=True,accepted_death_action_count=len(approved),scope='Enemy16 Medusa VFX only');write(OUT/'merge-report.json',report)

def main():
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args()
 if args.prepare:prepare()
 data=call('build');verify(data);previews(data);print(json.dumps({'checked_variants':6,'successive_gaze_pulses':8,'total_ticks':502,'contact_tick':475,'confirmed_death_unchanged':True}),flush=True)
 if args.export:export(data);data=call('build')
 if args.merge:merge(data)
if __name__=='__main__':main()
