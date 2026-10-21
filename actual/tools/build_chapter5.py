#!/usr/bin/env python3
"""Chapter five: explicit entrances, matched render/collision footprints, both armies."""
import json,copy,random,math
from collections import deque
from pathlib import Path
from PIL import Image
import build_chapter3 as base
R=base.R;read=base.read;write=base.write;PACK=base.PACK;SEA=base.SEA;WORLD=base.WORLD
PLAN={b['id']:b for b in json.loads((R.parent/'docs2/规划索引.json').read_text())['battles'] if b['chapter']==5}
IDS={'M51':501,'M52':502,'F51':503,'F52':504,'S51':511,'J53':533,'J54':534}
base.PLAN=PLAN
CAMPAIGN=read('data/campaign.json');base.CAMPAIGN=CAMPAIGN
OLD={**base.OLD,'p':208};MATERIAL={**base.MATERIAL,'p':'plaster'}
COUNTS={'M51':[(6,5),(2,3),(15,2)],'M52':[(1,4),(2,3),(12,3),(3,3)],'F51':[(2,4),(12,3),(15,3)],'F52':[(15,4),(12,3),(2,3)],'S51':[(2,3),(12,2),(15,1)],'J53':[(2,4),(12,3),(15,3),(3,3),(8,2)],'J54':[(3,4),(15,3),(2,2)]}
TEMPLATES={cid:min([u for u in base.samples if int(u['class_id'])==cid],key=lambda u:(u['level'],u['max_hp'])) for cid in [1,2,3,6,8,12,15]}
GOALS={'M51':'开放两处伤兵病房，撤离至少一组伤兵，并击败神军队长','M52':'依次解除三段桥锁，并击败桥卫统领','F51':'交接两处修复区，分别保护至下一己方回合，并击败守卫长','F52':'确认两处门阵，击败下层神官','S51':'取回旧事记录，击败书库守卫后在南门交接','J53':'确认两翼门阵，击败前庭统领','J54':'击败乌库布·卡基的实体；胡纳普和艾琳均须存活'}

def art(m,name,x,y,blocked=True):
 im=Image.open(R/f'assets/chapter5/{name}.png');w,h=(v//16 for v in im.size)
 cells={(xx,yy) for yy in range(y,y+h) for xx in range(x,x+w)}
 assert not cells&m.reserved,(m.code,name,'overlap')
 assert x+w<=m.w and y+h<=m.h
 m.reserved|=cells
 if blocked:m.rect(x,y,x+w-1,y+h-1,'#')
 m.props.append({'path':f'res://assets/chapter5/{name}.png','position':[x*16,y*16]})
 m.modules.append({'name':name,'origin':[x,y],'footprint':[w,h],'cells':[list(p) for p in sorted(cells)],'logic':'#' if blocked else 'inherits_ground'})
def point(m,id,at,label,front=None,**extra):
 o=m.object(id,'control',at,label,'orders_case',adjacent=False,**extra)
 if front:o['approach']=front
 o['name_zh']=label;o['completed_label']='已'+label
 return o

def layout(m):
 c=m.code;w=m.w;h=m.h;m.route='joint' if c.startswith('J') else 'alm' if c.startswith('M') else 'celica'
 m.rect(0,0,w-1,h-1,'p');m.rect(1,1,w-2,h-2,'b')
 m.deploy=[[x,y] for y in [h-5,h-4,h-3] for x in [2,3,4,5]][:10];m.exit=[4,h-2]
 if c=='M51':
  art(m,'palace',17,0);art(m,'infirmary',7,9);art(m,'infirmary',19,11)
  m.path([[4,23],[15,23],[15,8],[23,8]],3);m.path([[4,17],[25,17]],3)
  m.rect(3,3,12,6,'.');m.rect(3,4,7,5,'~');m.rect(8,19,10,20,'.')
  m.boss=[23,8];m.exit=[15,24]
  for i,(x,y) in enumerate([(10,15),(22,17)]):
   m.npc('royal_wounded'+str(i),[x,y],'王都伤兵'+str(i+1),'escort',True)
   point(m,'ward_'+str(i+1),[x,y-1],'开放'+('西' if i==0 else '东')+'病房',[x,y+1],unlock_units=['royal_wounded'+str(i)])
  m.notes=['两间病房均朝南开门。赫兰已打开南侧后撤门；南出口(15,24)连接医舍前的三格道路。至少一组撤离，两组均损失则失败。']
 elif c=='M52':
  m.rect(0,0,w-1,h-1,'~');m.rect(0,6,6,20,'p');m.rect(25,3,31,20,'p');m.rect(6,10,25,15,'=')
  m.deploy=[[x,y] for y in [11,12,13] for x in [1,2,3,4]][:10];m.boss=[28,12];m.exit=[30,12]
  for x in [7,15,23]:
   art(m,'column',x,4);art(m,'column',x,16)
  for i,x in enumerate([10,16,22]):point(m,'bridge_'+str(i+1),[x,12],'解除第'+str(i+1)+'段桥锁')
  m.notes=['三段桥面由六格宽石桥连续连接，桥两侧是不可步行的深谷；柱脚不侵入桥面。桥锁须依序确认，飞行绕行不能代替控制。']
 elif c=='F51':
  m.rect(0,0,w-1,h-1,'c');m.rect(3,4,24,23,'p');m.rect(12,6,15,18,'~');m.rect(12,12,15,14,'=')
  art(m,'regulator',5,7);art(m,'regulator',20,7);art(m,'stair',17,0)
  m.boss=[19,5];m.path([[4,23],[9,23],[9,13],[22,13],[22,20]],3)
  for i,(x,y) in enumerate([(7,11),(22,11)]):
   m.npc('repair_team'+str(i),[x,y],'第'+str(i+1)+'修复工班','witness',True).update(hp=44,max_hp=44,defence=8,resistance=8)
   point(m,'repair_'+str(i+1),[x,y-1],'交接第'+str(i+1)+'修复区',[x,y+1])
  m.notes=['地下水渠由中桥连通，两台完整装置的操作面均在南面。未交接工班在防护区内；开始工作后保护一轮，交接完成不会把正式角色锁在原地。']
 elif c=='F52':
  m.rect(14,8,17,20,'~');m.rect(14,12,17,15,'=');art(m,'palace',12,0);art(m,'regulator',5,6);art(m,'regulator',23,6)
  m.path([[4,23],[10,23],[10,13],[24,13],[24,21]],3)
  m.rect(4,16,7,19,'.');m.rect(25,16,28,19,'.');m.boss=[16,7]
  point(m,'lower_west',[7,9],'确认西门阵',[7,10]);point(m,'lower_east',[25,9],'确认东门阵',[25,10])
  m.notes=['左右装置门阵位于水渠两岸，中央石桥与南廊相接。必须站在各装置南面确认，不靠路过自动完成；不需要专属武器或携带钥匙。']
 elif c=='S51':
  art(m,'archive',9,1);art(m,'column',3,2);art(m,'column',19,2);m.path([[4,17],[12,17],[12,7]],3)
  m.rect(3,10,6,13,'.');m.rect(17,10,20,13,'.');m.boss=[15,8];m.exit=[12,18]
  point(m,'old_record',[12,6],'取回旧事记录',[12,7]);point(m,'archive_exit',[12,18],'南门交接记录')
  m.notes=['书库正门朝南，记录交接必须沿院道回到南门；两侧阅览庭与主路相连。错过本支线仍可理解主线并完成结局。']
 else:
  m.deploy=[[x,y] for y in [h-5,h-4,h-3] for x in [2,3,4,5]][:10]+[[x,y] for y in [h-5,h-4,h-3] for x in [26,27,28,29]][:10]
  m.path([[4,h-3],[16,h-3],[28,h-3]],3);m.path([[16,h-3],[16,7]],5)
  for x in [2,26]:m.rect(x,15,x+3,19,'~')
  if c=='J53':
   art(m,'palace',12,0);art(m,'regulator',4,8);art(m,'regulator',24,8);m.boss=[16,8]
   point(m,'court_west',[6,11],'确认前庭西阵',[6,12]);point(m,'court_east',[26,11],'确认前庭东阵',[26,12])
  else:
   art(m,'throne',13,1);m.boss=[16,8]
   for x in [5,25]:
    for y in [3,10]:art(m,'column',x,y)
  m.exit=[16,h-2];m.notes=['两队分别从西南与东南入口出阵，每队最多十人，胡纳普和艾琳均不可卸下。完整中轴通向神座，水池与柱脚明确阻挡步行。']
 # Authored court furnishing: broad walking lanes stay continuous around enclosed gardens.
 if c in ['J53','J54']:
  for x in [9,20]:
   m.rect(x,15,x+2,21,'.')
   for y in [16,19]:
    m.nature.append({'key':'pine_young','position':[x*16,y*16],'flip':False});m.grid[y][x]='f'
   m.module('flowers',x+1,20,False)
  for x in [1,29]:
   if c=='J53':art(m,'column',x,4)
  # South entrance garden beds are separated from both deployment blocks.
  for x in [8,21]:m.rect(x,h-7,x+2,h-6,'.');m.module('flowers',x+1,h-6,False)
  for x in [0,4,8,20,24,28]:m.module('north_wall',x,0)
  for x in [0,w-1]:
   for y in [9,13,17]:m.module('west_wall',x,y)
  for x in [10,21]:m.module('ritual_lamp',x,8)
 elif c=='M51':
  for x,y in [(8,3),(11,3),(8,20)]:m.nature.append({'key':'pine_young','position':[x*16,y*16],'flip':False});m.grid[y][x]='f'
  m.prop('quay_warehouse',2,8)
  for x in [0,4,8,12,24]:m.module('north_wall',x,0)
  for x in [0,w-1]:
   for y in [9,13,17]:m.module('west_wall',x,y)
  m.module('medicine_wagon',7,17);m.module('crates',2,12)
 elif c=='F51':
  for x in [0,w-1]:
   for y in [0,4,8,12,16,20]:m.module('west_wall',x,y)
  for x in [2,6,10,22]:m.module('rock_face',x,0)
  for x in [3,24]:
   for y in [6,15]:m.module('ritual_lamp',x,y)
 elif c=='F52':
  for x in [0,4,8,20,24,28]:m.module('north_wall',x,0)
  for x,y in [(4,17),(6,17),(25,17),(27,17)]:m.nature.append({'key':'pine_young','position':[x*16,y*16],'flip':False});m.grid[y][x]='f'
  for x in [2,28]:art(m,'column',x,10)
 elif c=='S51':
  for x in [0,4,16,20]:m.module('north_wall',x,0)
  for x in [3,18]:
   for y in [10,12]:m.nature.append({'key':'pine_young','position':[x*16,y*16],'flip':False});m.grid[y][x]='f'
  m.module('orders_case',8,8,False);m.module('orders_case',16,8,False)
 elif c=='M52':
  # Stone parapets flank the deck; six visible supporting columns explain the piers.
  for x in [6,10,14,18,22]:
   m.module('north_wall',x,9);m.module('north_wall',x,16) if x not in [6,14,22] else None
 # Recovery gardens are visible single-cell terrain; they never treat persistent dying members.
 for x,y in [(10,h-4),(20,h-4)]:
  if m.grid[y][x] not in '#^~':m.grid[y][x]='+';m.module('flowers',x,y,False)

def bake(m):
 c=m.code;b=m.card;rng=random.Random(IDS[c]);m.occupied|=set(map(tuple,m.deploy))
 for o in m.objects:
  m.occupied.add(tuple(o['position']))
  if 'approach' in o:m.occupied.add(tuple(o['approach']))
 def enemy(cid,at,i,boss=False):
  u=copy.deepcopy(TEMPLATES[cid]);hp=46 if boss else 31 if cid==2 else 27
  u.update(id=c+('_boss' if boss else '_e'+str(i)),position=m.free(at),side='enemy',acted=False,exp=0,item_id=0,group_id=0,raw_ai_flags=0,ai_flags=0,level=10 if boss else 7,hp=hp,max_hp=hp,strength=14 if boss else 11,skill=7,speed=5,defence=8 if boss or cid==2 else 5,resistance=5,luck=0,exp_value=60 if boss else 38,magic_flags=1 if cid==15 else 0,raw_magic_flags=1 if cid==15 else 0,behavior='guard' if boss or cid in [2,12,15] or i>4 else 'advance')
  u['name_zh']= {'M51':'神军队长','M52':'桥卫统领','F51':'祭所守卫长','F52':'下层神官','S51':'书库守卫','J53':'前庭统领','J54':'乌库布·卡基'}[c] if boss else {1:'神宫骑兵',2:'石像守卫',3:'天翼守军',6:'神宫士兵',8:'近卫',12:'神宫弓手',15:'日宫术士'}[cid]
  if boss:u['objective_boss']=True
  if c=='J54' and boss:
   # Dedicated campaign identity, ordinary source mage actions; no legacy Duma immunity.
   u.update(character_id=169,source_enemy_character_id=169,hp=112,max_hp=112,strength=15,defence=9,resistance=6,speed=4,move=0,campaign_final_boss=True)
  return u
 enemies=[enemy(15 if c in ['F52','J54'] else 2,m.boss,0,True)];m.boss=enemies[0]['position']
 anchors= {'M51':[[16,8],[17,12],[25,18],[11,8]],'M52':[[9,12],[15,12],[21,12],[27,8]],'F51':[[8,5],[22,5],[19,16],[6,17]],'F52':[[8,12],[24,12],[19,8],[11,8]],'S51':[[7,8],[17,8],[18,15],[6,15]],'J53':[[8,15],[24,15],[12,10],[20,10]],'J54':[[9,18],[23,18],[11,10],[21,10]]}[c]
 for cid,count in COUNTS[c]:
  for _ in range(count):enemies.append(enemy(cid,anchors[(len(enemies)-1)%4],len(enemies)))
 rein=[];rt={'M51':4,'M52':4,'F51':3}.get(c,0)
 if rt:
  for i in range(2):
   u=enemy(6,[2,7] if c=='M52' else [m.w-3,m.h-3],50+i);u.update(id=c+'_r'+str(i),behavior='advance');rein.append(u)
 for i,u in enumerate(m.npcs):u['player_slot']=len(m.deploy)+i
 terrain=read('assets/chapter5/terrain.json')['materials']
 layers=[[[None]*m.w for _ in range(m.h)] for _ in range(3)]
 for y in range(m.h):
  for x in range(m.w):
   ch=m.grid[y][x];v=(x+y)%4
   material='teal' if ch=='=' else 'ivory' if ch in 'bp#' else 'garden' if ch in '.f' else ''
   layers[0][y][x]=terrain[material][v] if material else PACK['base'][MATERIAL[ch]][rng.randrange(4)]
   # Whole pre-existing shore tiles close water edges without drawing fake walkable squares.
   if ch not in '~#' and any(0<=x+dx<m.w and 0<=y+dy<m.h and m.grid[y+dy][x+dx]=='~' for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]):
    peers=[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]
    mask=sum(bit for dx,dy,bit in peers if 0<=x+dx<m.w and 0<=y+dy<m.h and m.grid[y+dy][x+dx]!='~')
    for bit,a,z in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
     if not(mask&a and mask&z):mask &= ~bit
    layers[0][y][x]=SEA['coasts']['stone'][str(mask)][v]
 for mod in m.modules:
  if 'tiles' in mod:
   for dy,row in enumerate(mod['tiles']):
    for dx,t in enumerate(row):layers[2][mod['origin'][1]+dy][mod['origin'][0]+dx]=t
 seen={tuple(m.deploy[0])};q=deque(seen)
 while q:
  x,y=q.popleft()
  for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]:
   n=x+dx,y+dy
   if 0<=n[0]<m.w and 0<=n[1]<m.h and n not in seen and m.grid[n[1]][n[0]] not in '#^~':seen.add(n);q.append(n)
 for p in m.deploy+[m.exit]+[u['position'] for u in enemies+m.npcs+rein]+[o.get('approach',o['position']) for o in m.objects]:assert tuple(p) in seen,(c,'disconnected',p)
 d=dict(schema_version=4,id=IDS[c],code=c,name_zh=b['name'],chapter=5,route=m.route,node=next(int(k) for k,v in WORLD['nodes'].items() if v['id']==b['node']),map={'width':m.w,'height':m.h,'tiles':[OLD[ch] for row in m.grid for ch in row]},logic_grid=[''.join(row) for row in m.grid],art_atlas='res://assets/chapter5/temple-tiles.png',art_columns=32,art_layers=layers,art_modules=m.modules,art_props=m.props,natural_props=m.nature,tactical_review_version='0.10.0',surroundings='cave' if c=='F51' else 'sea' if c=='M52' else 'land',nature_layout={'biome':'rock' if c=='F51' else 'grass','props':[]},characters={},player_positions=m.deploy,enemies=enemies,npc_units=m.npcs,terrain=read('data/stages/M11.json')['terrain'],enemy_group_ids=[],objects=m.objects,reinforcements=rein,reinforcement_turn=rt,exit=m.exit,boss_id=c+'_boss',targets=[o['position'] for o in m.objects] or [m.boss],goal=GOALS[c]+'。',before=b['before'],during=b['during'],after=b['after'],optional=b['optional'],event_boats=[],clear_training_exp=20,visual_notes=m.notes,tactical_notes=m.notes)
 if m.route=='joint':d['player_positions_by_route']={'alm':m.deploy[:10],'celica':m.deploy[10:]}
 if c=='J54':
  u=enemy(3,[16,10],90);u.update(id='J54_summon_template',no_drop=True,name_zh='日宫援军');d['summon_template']=u
 write('data/stages/'+c+'.json',d);CAMPAIGN['stages'][str(IDS[c])]={'code':c,'path':'res://data/stages/'+c+'.json','node':d['node']}
 return dict(code=c,enemies=len(enemies),reinforcements=len(rein),reachable_cells=len(seen),entrances='passed',footprints='passed')

def hubs():
 rooms={}
 for id,title,asset,actions in [
 ('H51','王都内廷 · 伤兵照护处','infirmary',[('ward_report','赫兰与交接记录')]),
 ('H52','登天桥 · 西门营地','sun_gate',[('west_report','西门阵守卫')]),
 ('H53','祭所底层 · 修复间','regulator',[('repair_report','地方技术员')]),
 ('H54','日宫下层 · 东门廊','regulator',[('east_report','东门阵守卫'),('archive_invite','旧书库入口')]),
 ('H55','神宫前庭 · 两军整备','sun_gate',[('prepare','两军出阵名册'),('relationship','达恩与米蕾'),('merge','前庭出发点')]),
 ('H56','神宫旧书库 · 记录室','archive',[('archive_report','旧事记录')])]:
  floor=[list('.'*14) for _ in range(9)]
  for y in range(2,9):
   for x in range(2,13):floor[y][x]='i'
  for y in range(4,9):
   for x in range(5,8):floor[y][x]='p'
  for x in [2,3,4,8,9,10,11,12]:floor[7][x]='p'
  positions={'H51':[[11,6]],'H52':[[10,6]],'H53':[[10,5]],'H54':[[10,5],[3,4]],'H55':[[3,3],[6,3],[10,6]],'H56':[[11,6]]}[id]
  objects=[dict(action='fifth_'+a,name=n,position=pos,sprite='orders_case',source=5) for (a,n),pos in zip(actions,positions)]
  dimensions={'infirmary':[6,6],'sun_gate':[5,6],'regulator':[4,4],'archive':[6,6]}
  scenery=[dict(name=asset,position=[8,0] if asset!='regulator' else [8,1],footprint=dimensions[asset],blocking=True,sprite_path='res://assets/chapter5/'+asset+'.png')]
  if id in ['H51','H55']:objects.append(dict(action='treatment',name='伤员照护',position=[3,6],sprite='medicine_wagon',source=14))
  scenery.append(dict(name='flowers',position=[1,1],footprint=[1,1],blocking=True,sprite_path='res://assets/battle_tiles/modules/flowers.png'))
  rooms[id]=dict(title=title,hint='面对对象确认；南口返回地图',floor=[''.join(row) for row in floor],objects=objects,scenery=scenery,biome_override='rock' if id=='H53' else 'grass')
 write('data/chapter5_hubs.json',{'materials':{'i':'plaster'},'rooms':rooms})

if __name__=='__main__':
 reports=[]
 for c in IDS:
  m=base.Map(c);layout(m);reports.append(bake(m))
 CAMPAIGN['chapter_limit']=5;write('data/campaign.json',CAMPAIGN);hubs()
 supply=read('data/equipment_progression.json');supply['clear_rewards'].update({'502':[12],'504':[3],'511':[49]});write('data/equipment_progression.json',supply)
 write('reports/chapter5/map-build.json',reports);print(json.dumps(reports,ensure_ascii=False))
