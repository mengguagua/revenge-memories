#!/usr/bin/env python3
"""Authored chapter-four maps; approved complete bitmap modules at native scale."""
from pathlib import Path
import json,copy,random,math
from collections import deque
import build_chapter3 as base
from PIL import Image
R=base.R;read=base.read;write=base.write;PACK=base.PACK;SEA=base.SEA;NATURE=base.NATURE
PLAN={b['id']:b for b in json.loads((R.parent/'docs2/规划索引.json').read_text())['battles'] if b['chapter']==4}
IDS={'M41':401,'M42':402,'M43':403,'M44':404,'F41':405,'F42':406,'F43':407,'F44':408,'S41':411,'S42':412}
base.PLAN=PLAN
CAMPAIGN=read('data/campaign.json');WORLD=base.WORLD
u=copy.deepcopy(read('data/legacy/campaign.json')['characters']['tatiana']);u.update(id='celine',key='celine',name_zh='赛琳',level=6,exp=0,hp=28,max_hp=28,item_id=0,dead=False,acted=False)
CAMPAIGN['characters']['celine']=u;CAMPAIGN['mapping']['celine']={'story_name':'赛琳','source_character':'tatiana'};base.CAMPAIGN=CAMPAIGN
OLD={**base.OLD,'n':48,'m':66};MATERIAL={**base.MATERIAL,'n':'snow','m':'marsh'}
COUNTS={'M41':[(6,5),(2,2),(12,3),(1,2)],'M42':[(1,7),(20,2),(6,3),(15,1)],'M43':[(2,4),(6,4),(12,3),(15,2)],'M44':[(1,4),(2,4),(12,3),(15,2)],'F41':[(8,4),(12,3),(15,2),(3,3)],'F42':[(15,4),(12,3),(2,6)],'F43':[(6,4),(3,3),(15,2)],'F44':[(2,5),(3,3),(15,3)],'S41':[(6,4),(12,3),(15,1)],'S42':[(3,3),(15,2),(6,3)]}
TEMPLATES={cid:min([u for u in base.samples if int(u['class_id'])==cid],key=lambda u:(u['level'],u['max_hp'])) for cid in [1,2,3,6,8,12,15,20]}

def control(m,id,pos,label):return m.object(id,'control',pos,label,'white_flag',adjacent=False)
def record(m,id,pos,label,approach):return m.object(id,'record',pos,label,'orders_case',approach=approach)
def house(m,name,x,y):m.prop(name,x,y)
def escorts(m,positions,prefix):
 for i,p in enumerate(positions):m.npc(prefix+str(i),p,['北村居民','山道伤者','南村居民'][i] if prefix=='snow_group' else '待转运居民'+str(i+1),'escort')
def layout(m):
 c=m.code;w=m.w;h=m.h;m.route='alm' if c.startswith('M') or c=='S41' else 'celica'
 if c=='M41':
  m.rect(0,0,w-1,h-1,'n');m.rect(0,0,1,h-1,'^');m.rect(29,0,31,h-1,'^')
  m.path([[5,4],[16,4],[16,24]],3,',');m.path([[4,22],[25,22],[25,6],[16,6]],3,',');m.path([[16,15],[25,15]],3,',')
  for x,y in [(5,1),(11,7),(20,1),(20,17)]:m.module('snow_cottage',x,y)
  house(m,'village_clinic',18,10);house(m,'command_pavilion',24,1)
  m.deploy=[[x,y] for y in [22,23,24] for x in [12,13,14,15]];m.boss=[23,22];m.exit=[16,24];control(m,'south_gate',[16,21],'疏通南口路障');control(m,'rest_station',[19,13],'安置伤者停靠点')
  escorts(m,[[5,4],[16,5],[18,19]],'snow_group');m.notes=['指挥官移至南侧封路点(23,22)，撤离南口(16,24)连接贯通村道。部署前移到南口接应阵地，北口追兵从(4,1)抵达；三组居民各自计数。']
 elif c=='M42':
  m.path([[4,24],[16,24],[16,4],[28,4]],3,',');m.path([[7,24],[7,12],[26,12],[26,22],[16,22]],3,',')
  m.rect(12,11,20,17,'b');house(m,'coastal_keep',23,0);house(m,'quay_warehouse',13,10);house(m,'command_pavilion',23,14)
  m.module('sun_altar',18,14);control(m,'transfer_station',[16,14],'切断神术投送站');control(m,'cavalry_camp',[25,17],'登记关卡营地')['optional']=True
  m.npc('old_comrade',[10,17],'兰斯的旧同袍','witness');m.npc('station_worker',[15,16],'投送站工匠','witness');m.notes=['两条宽阔侧路连接骑兵营地与投送站；旧同袍在西侧营外，兰斯须亲自邻接交涉。']
 elif c=='M43':
  m.rect(0,0,w-1,h-1,'n');m.rect(0,0,3,19,'^');m.rect(25,0,27,20,'^');m.rect(7,5,24,19,'b')
  m.path([[4,24],[10,24],[10,14],[21,14],[21,5]],3);m.path([[10,14],[10,8],[21,8]],3)
  house(m,'coastal_keep',18,0);m.module('tower_entry',22,5);house(m,'village_clinic',6,17);house(m,'quay_warehouse',18,17)
  control(m,'outer_court',[14,14],'控制外院关卡');record(m,'tower_control',[21,18],'接管控制室',[21,19]);m.boss=[21,8]
  m.npc('tower_worker',[9,20],'日塔工匠','witness');m.npc('tower_patients',[13,16],'塔下病人','witness');m.notes=['控制室位于东侧工房南门，主塔前场与看护院各有通路；未获观测步骤也能完成夺塔战。']
 elif c=='M44':
  m.exit=[28,5];m.boss=[27,5]
  m.rect(0,0,w-1,h-1,'b');m.path([[4,24],[16,24],[16,4],[28,4]],3)
  m.path([[6,18],[26,18],[26,6],[16,6]],3)
  for x in [0,4,8,12,20,24,28]:
   if x+4<=w:m.module('north_wall',x,8)
  for wall in m.modules:
   if wall['name']=='north_wall':
    x=wall['origin'][0];wall['tiles']=[[458 if x==0 else 459,459,460,461 if x==28 else 460]]
  m.module('open_gate',16,8,False);m.rect(16,8,19,9,'=')
  house(m,'coastal_keep',25,0);house(m,'village_clinic',22,13);house(m,'quay_warehouse',5,12);house(m,'fishing_cottage',9,19);house(m,'command_pavilion',20,20)
  control(m,'gatehouse',[16,10],'占领王都门楼');control(m,'wounded_gate',[25,16],'开放伤兵后撤门')['optional']=True
  m.npc('church_wounded0',[5,22],'教团伤者甲','witness');m.npc('church_wounded1',[24,18],'教团伤者乙','witness');m.notes=['城墙正门留四格宽通道；伤兵后撤门连通医舍，不把墙面或屋顶画成可走道路。']
 elif c=='F41':
  m.rect(0,0,w-1,h-1,'d');m.rect(3,7,27,22,'b');m.path([[5,21],[5,5],[25,5],[25,20],[5,20]],3,',');m.path([[5,13],[25,13]],3,',')
  m.deploy=[[x,y] for y in [21,22,23] for x in [16,17,18,19]]
  for x,y in [(4,9),(21,15),(12,4),(12,20)]:house(m,'fishing_cottage',x,y)
  m.module('well',5,5);m.module('well',19,19)
  control(m,'well_n',[5,6],'守住北井');control(m,'well_s',[19,20],'守住南井')
  m.npc('sand_resident',[7,18],'沙城居民','witness');m.npc('sand_guide',[15,15],'古道向导','witness');house(m,'command_pavilion',25,1)
  m.notes=['井口为实体，守井点在南侧取水台；部署设在南井接应阵地，首回合能够布防南井；可分兵北上夺回北井。井只在敌军连续占满一轮后失守，可站回夺回。']
 elif c=='F42':
  m.rect(0,0,w-1,h-1,'a');m.rect(6,5,24,21,'b');m.path([[4,24],[10,24],[10,14],[23,14],[23,4]],3);m.path([[10,14],[10,7],[22,7]],3)
  house(m,'quay_warehouse',21,9);m.module('sun_altar',14,12);house(m,'coastal_keep',19,0);m.module('ritual_lamp',18,17);house(m,'fishing_cottage',6,17)
  record(m,'observatory_record',[22,10],'保护东楼记录',[22,11]);record(m,'observation_device',[15,14],'复制观测设备',[15,15]);m.boss=[16,10]
  m.npc('copyist',[7,20],'抄录工','witness');m.npc('local_mage',[13,16],'地方技术员','witness');m.notes=['记录室实置东楼，门前(22,11)可读；中央观测阵台必须南面确认。焚毁兵第5回合预告，第6回合才向东楼出发。']
 elif c in ['F43','S42']:
  m.rect(0,0,w-1,h-1,'m')
  for x0,y0,x1,y1 in [(0,0,5,12),(20,8,w-1,14),(8,h-6,12,h-1)]:m.rect(x0,y0,x1,y1,'~')
  m.path([[3,h-3],[6,h-3],[6,17],[16,17],[16,8],[w-4,8],[w-4,3]],3,',');m.path([[6,17],[6,8],[16,8]],2,',')
  m.rect(2,h-6,7,h-2,'s');m.module('rowboat',3,h-6,False)
  if c=='F43':
   control(m,'dry_1',[7,24],'确认第一处干地');control(m,'dry_2',[16,14],'确认第二处干地');control(m,'dry_3',[25,7],'确认第三处干地')
   m.path([[6,24],[7,24],[16,17]],2,',');m.path([[16,8],[25,8],[25,7],[28,3]],3,',')
   escorts(m,[[5,22],[15,16],[18,21]],'marsh_group');m.path([[18,21],[18,17]],2,',');house(m,'ruined_watchtower',23,1);m.boss=[27,4];m.exit=[28,3]
  else:
   house(m,'village_clinic',15,10);m.path([[6,17],[18,17],[18,12]],3,',');m.path([[11,13],[16,13]],2,',')
   m.exit=[6,19];m.boss=[19,4];m.path([[16,8],[19,8],[19,4]],3,',');m.npc('celine',[18,13],'赛琳','witness');escorts(m,[[11,13],[17,14]],'island_group');m.path([[11,13],[11,17]],2,',')
   control(m,'landing',[6,18],'确认船边接应点');record(m,'clinic_note',[16,11],'查看维娅航行记录',[16,12])['optional']=True
  m.notes=['毒沼使用可见沼泽材质并保留原伤害；褐色高地与木栈桥全程相连。转运以逐组步行护送至实际船口/古道出口实现，不要求传送技能。']
 elif c=='F44':
  m.rect(0,0,w-1,h-1,'~');m.rect(4,3,28,23,'b');m.rect(1,21,7,26,'s');m.path([[4,24],[10,24],[10,9],[25,9],[25,4]],3)
  m.rect(12,6,18,10,'~');m.rect(19,18,24,23,'~');m.path([[10,14],[25,14],[25,22],[10,22]],3)
  house(m,'ancient_arch',23,0);m.module('sun_altar',15,11);m.module('ritual_lamp',24,15);m.module('ritual_lamp',9,8);m.module('rowboat',2,22,False)
  control(m,'regulator_1',[16,14],'交接中央调节点');control(m,'regulator_2',[25,16],'交接东调节点');control(m,'regulator_3',[10,10],'交接西调节点')
  m.npc('repairer0',[8,22],'修复工匠甲','witness');m.npc('repairer1',[13,16],'修复工匠乙','witness');m.notes=['祭所水池不可步行，三个调节点靠完整环廊相连；交接后维修者接手，正式角色无需永久站点。']
 else:
  m.rect(0,0,w-1,h-1,'n');m.path([[4,18],[12,18],[12,5],[20,5]],3,',');m.path([[6,15],[19,15],[19,8],[12,8]],2,',')
  house(m,'quay_warehouse',14,8);house(m,'village_clinic',4,11);house(m,'fishing_cottage',4,3);house(m,'fishing_cottage',15,17);m.module('tower_entry',18,1)
  record(m,'black_register',[15,9],'保护黑钟村名册',[15,10]);control(m,'refuge_court',[7,14],'确认避难院')['optional']=True
  m.npc('village_witness',[8,16],'黑钟村民','witness');m.npc('otto_comrade',[11,13],'奥托旧同袍','witness');m.notes=['名册屋与避难院由村道连接；名册被焚只失去支线收益，不封锁主线。']
 # Healer waystations are ordinary single-cell recovery terrain, not resurrection.
 p=[9,m.h-5]
 if m.grid[p[1]][p[0]] not in '#^~':m.grid[p[1]][p[0]]='+';m.module('flowers',p[0],p[1],False)

def bake(m):
    c=m.code;rng=random.Random(IDS[c]);b=m.card
    for p in m.deploy:assert m.grid[p[1]][p[0]] not in '#^~',(c,'deployment',p)
    m.occupied |= set(map(tuple,m.deploy))
    for o in m.objects:
        m.occupied.add(tuple(o['position']))
        if 'approach' in o:m.occupied.add(tuple(o['approach']))
    enemies=[]
    def enemy(cid,at,i,boss=False):
        u=copy.deepcopy(TEMPLATES[cid]);hp=38 if boss else 30 if cid==2 else 27
        u.update(id=c+('_boss' if boss else '_e'+str(i)),position=m.free(at),side='enemy',acted=False,exp=0,item_id=0,group_id=0,raw_ai_flags=0,ai_flags=0,level=8 if boss else 6,hp=hp,max_hp=hp,strength=14 if boss else 11,skill=7,speed=5,defence=8 if boss or cid==2 else 5,luck=0,exp_value=60 if boss else 38,magic_flags=1 if cid==15 else 0,raw_magic_flags=1 if cid==15 else 0,behavior='guard' if boss or cid in [2,12,15] or i>4 else 'advance')
        u['name_zh']={'M41':'封路指挥官','M42':'铁骑统领','M43':'塔卫统领','M44':'赫兰','F41':'强迁队长','F42':'萨弥','F43':'召唤神官','F44':'天翼守兽','S41':'焚毁队长','S42':'清洗队长'}[c] if boss else {1:'护日骑兵',2:'石像守卫' if c in ['F42','F44'] else '重装守军',3:'飞行魔物' if c in ['F43','F44','S42'] else '飞行守军',6:'泥沼魔物' if c=='F43' else '士兵',8:'佣兵',12:'弓手',15:'术士',20:'弓骑兵'}[cid]
        if boss:u.update(objective_boss=True)
        return u
    enemies.append(enemy(15 if c in ['F42','F43'] else 3 if c=='F44' else 1 if c in ['M42','M44'] else 6,m.boss,0,True));m.boss=enemies[0]['position']
    anchors=copy.deepcopy(b['enemy_anchors'])
    if c=='M41':anchors=[[25,19],[25,13],[26,8],[27,5]]
    if c=='F41':anchors=[[7,5],[23,17],[22,7],[16,5]]
    if c=='S42':anchors=[[20,2],[14,3],[8,2],[20,6]]
    for cid,count in COUNTS[c]:
        for _ in range(count):enemies.append(enemy(cid,anchors[(len(enemies)-1)%4],len(enemies)))
    if c=='M41':
        for u in enemies:u['behavior']='guard_exit'
    if c in ['F42','S41']:
        burner=next(u for u in enemies if u['class_id']==6) if c=='S41' else next(u for u in enemies if u['class_id']==15 and not u.get('objective_boss'))
        burner.update(ch4_burner=True,behavior='burn',name_zh='焚毁兵')
        burner['position']=m.free([20,6] if c=='F42' else [19,6])
    if c=='S42':
        for u in enemies:
            if u['class_id']==3:u['advance_after']=3
    if c=='M42':
        for u in [e for e in enemies if e['class_id']==1 and not e.get('objective_boss')][:2]:u['old_comrade_group']=True
    if c=='F41':
        for i,u in enumerate([e for e in enemies if not e.get('objective_boss')][:4]):u['well_target']='well_n' if i%2==0 else 'well_s'
    rein=[];rt={'M41':4,'M42':5,'M44':4,'F41':3,'F44':5}.get(c,0)
    if rt:
        for i in range(2):
            at=[4,1] if c=='M41' else [29,4] if c=='F41' else [27,21] if c=='F44' else b['reinforcement'][0] if 'reinforcement' in b else [m.w-3,m.h-4]
            u=enemy(1 if c in ['M41','M42'] else 6,at,50+i);u.update(id=c+'_r'+str(i),behavior='advance');rein.append(u)
    for i,u in enumerate(m.npcs):u['player_slot']=len(m.deploy)+i
    protect=set(m.occupied)|{tuple(m.exit)}|m.reserved
    for o in m.objects:
        x,y=o['position'];protect|={(x+dx,y+dy) for dx,dy in [(0,0),(0,1),(1,0),(-1,0),(0,-1)]}
    # Whole nature silhouettes are restricted to their terrain footprints.
    taken=set();keys=['pine_young','pine_broad']
    for y in range(m.h-2):
        for x in range(m.w-2):
            ch=m.grid[y][x]
            if ch not in ('.','^','n') or rng.random()>.18:continue
            key=rng.choice(['snow_young','snow_broad'] if ch=='n' else keys if ch=='.' else ['peak_low','outcrop']);s=NATURE[key];fw=math.ceil(s['size'][0]/16);fh=math.ceil(s['size'][1]/16)
            foot={(xx,yy) for yy in range(y,y+fh) for xx in range(x,x+fw)}
            if y+fh>m.h or x+fw>m.w or foot&(protect|taken) or any(m.grid[yy][xx]!=ch for xx,yy in foot):continue
            taken|=foot;m.nature.append({'key':key,'position':[x*16,y*16],'flip':rng.choice([True,False])})
            if ch=='.':
                for xx,yy in foot:m.grid[yy][xx]='f'
    layers=[[[None]*m.w for _ in range(m.h)] for _ in range(3)]
    peers=[(0,-1,1),(1,0,2),(0,1,4),(-1,0,8),(1,-1,16),(1,1,32),(-1,1,64),(-1,-1,128)]
    for y in range(m.h):
        for x in range(m.w):
            ch=m.grid[y][x];v=rng.randrange(4);layers[0][y][x]=PACK['base'][MATERIAL[ch]][v]
            if ch not in '~s#' and any(0<=x+dx<m.w and 0<=y+dy<m.h and m.grid[y+dy][x+dx]=='~' for dx,dy,_ in peers[:4]):
                mask=sum(bit for dx,dy,bit in peers if 0<=x+dx<m.w and 0<=y+dy<m.h and m.grid[y+dy][x+dx]!='~')
                for bit,a,z in [(16,1,2),(32,2,4),(64,4,8),(128,8,1)]:
                    if not(mask&a and mask&z):mask &= ~bit
                mat='stone' if ch in '=b' else 'sand'
                layers[0][y][x]=SEA['coasts'][mat][str(mask)][v]
    for mod in m.modules:
        if 'tiles' not in mod:continue
        ox,oy=mod['origin']
        for dy,row in enumerate(mod['tiles']):
            for dx,t in enumerate(row):layers[2][oy+dy][ox+dx]=t
    opens={tuple(p) for o in m.objects for p in o.get('opens',[])}
    def reach(opened):
        start=tuple(m.deploy[0]);seen={start};q=deque([start])
        while q:
            x,y=q.popleft()
            for dx,dy,_ in peers[:4]:
                n=x+dx,y+dy
                if 0<=n[0]<m.w and 0<=n[1]<m.h and n not in seen and (m.grid[n[1]][n[0]] not in '#^~' or (opened and n in opens)):seen.add(n);q.append(n)
        return seen
    opened=reach(True);closed=reach(False)
    for o in m.objects:
        x,y=o['position'];approaches=[tuple(o['approach'])] if 'approach' in o else [(x+dx,y+dy) for dx,dy,_ in peers[:4]] if o['adjacent'] else [(x,y)]
        assert any(p in closed for p in approaches),(c,'unreachable closed interaction',o['id'])
    for p in m.deploy+[m.exit]+[u['position'] for u in enemies+m.npcs+rein]:assert tuple(p) in opened,(c,'disconnected',p)
    d={'schema_version':4,'id':IDS[c],'code':c,'name_zh':b['name'],'chapter':4,'route':m.route,'node':next(int(k) for k,v in WORLD['nodes'].items() if v['id']==b['node']),'map':{'width':m.w,'height':m.h,'tiles':[OLD[ch] for row in m.grid for ch in row]},'logic_grid':[''.join(row) for row in m.grid],'art_atlas':'res://assets/chapter2/chapter2-tiles.png','art_columns':32,'art_layers':layers,'art_modules':m.modules,'art_props':m.props,'natural_props':m.nature,'tactical_review_version':'0.9.0','surroundings':'sea' if c in ['F44','S42'] else 'cave' if c=='S31' else 'land','nature_layout':{'biome':'snow' if c in ['M41','M43','S41'] else 'salt' if c in ['F41','F42'] else 'marsh' if c=='F43' else 'grass','props':[]},'characters':{},'player_positions':m.deploy,'enemies':enemies,'npc_units':m.npcs,'terrain':read('data/stages/M11.json')['terrain'],'enemy_group_ids':[],'objects':m.objects,'reinforcements':rein,'reinforcement_turn':rt,'exit':m.exit,'boss_id':c+'_boss','targets':[o['position'] for o in m.objects],'goal':b['goal'],'before':b['before'],'during':b['during'],'after':b['after'],'optional':b['optional'],'event_boats':[],'clear_training_exp':20,'visual_notes':m.notes,'tactical_notes':[]}

    if c in ['F42','S41']:
        d['burn_target']=[22,11] if c=='F42' else [15,10];d['burn_start']=6 if c=='F42' else 5
    if c=='F43':
        summon=enemy(6,[26,6],90);summon.update(id='F43_summon_template',summoner_id='F43_boss',name_zh='神官召唤物',no_drop=True);d['summon_template']=summon
    d['goal']={'M41':'疏通南口与停靠点，撤离至少两组居民并击败指挥官','M42':'控制投送站并击败铁骑统领','M43':'接管外院与控制室，击败塔卫统领','M44':'占领门楼，击败并解除赫兰指挥权','F41':'保住至少一井至第6己方回合，并击败强迁队长','F42':'保护东楼记录、复制设备，击败萨弥','F43':'依次确认三处干地、撤离至少两组居民并击败神官','F44':'交接三处调节点，保护工匠至下一回合并击败守兽','S41':'击败焚毁队长；尽力保护名册，失去记录不阻断主线','S42':'确认船口、护送两组病人撤离并击败清洗队长'}[c]
    d['goal']+='。'
    d['tactical_notes']=m.notes
    # Native logic uses the same object and entrance positions as rendered art.
    names={'south_gate':'南口路障','rest_station':'伤者停靠点','transfer_station':'神术投送站','cavalry_camp':'关卡营地','outer_court':'外院关卡','gatehouse':'王都门楼','wounded_gate':'伤兵后撤门','dry_1':'第一干地','dry_2':'第二干地','dry_3':'第三干地','regulator_1':'中央调节点','regulator_2':'东调节点','regulator_3':'西调节点','refuge_court':'避难院','landing':'船边接应点'}
    for o in d['objects']:
        if o['id'] in names:o['name_zh']=names[o['id']]
        o['completed_label']=o['label'].replace('确认','已确认').replace('控制','已控制').replace('交接','已交接').replace('保护','已保护').replace('复制','已复制')
    write('data/stages/'+c+'.json',d)
    CAMPAIGN['stages'][str(IDS[c])]={'code':c,'path':'res://data/stages/'+c+'.json','node':d['node']}
    return {'code':c,'size':[m.w,m.h],'enemies':len(enemies),'reinforcements':len(rein),'interactions':len(m.objects),'walkable_open':len(opened),'anchor_checks':'passed','notes':m.notes}

def story():
 CAMPAIGN['chapter_limit']=4
 CAMPAIGN['scenes']['D41']=base.pages(['赫兰：北面那几座村庄，是你亲自送粮过去的。停了塔，他们怎么办？','胡纳普：他们已经撤出来了。观测台的办法也试过了。','赫兰：一次试成，下一次未必还能成。','胡纳普：东边也有人这样等过你。你一直没有派船。','赫兰：……我的人守住了西岸。我不能拿他们再赌一次。'])
 write('data/campaign.json',CAMPAIGN)
 supply=read('data/equipment_progression.json');supply['starter_items']['celine']=0;supply['clear_rewards'].update({'401':[49],'402':[3],'403':[22],'404':[16],'405':[50],'406':[57],'408':[22],'411':[22],'412':[16]});write('data/equipment_progression.json',supply)
 rooms={}
 def obj(action,name,pos,sprite='actor',source=5):return dict(action=action,name=name,position=pos,sprite=sprite,source=source)
 titles=['雪峡村 · 南口安置处','铁骑关 · 投送站','北境日塔 · 控制室','王都 · 伤兵后撤门','沙城 · 井台','盐原观测台 · 东楼','亡潮沼泽 · 船口','沉没祭所 · 调节庭','黑钟村 · 避难院','沼泽孤岛 · 诊疗处']
 actions=[('snow_settle','居民名册'),('transfer_report','投送站工匠'),('tower_shutdown','安全停塔控制台'),('herlan','赫兰'),('well_report','古道向导'),('obs_report','观测记录'),('marsh_report','船团医者'),('island_verify','隔离试验台'),('black_report','黑钟村名册'),('celine','赛琳')]
 for i,(title,(act,label)) in enumerate(zip(titles,actions)):
  theme='n' if i in [0,2,8] else 'a' if i in [4,5] else '.'
  floor=[theme*14 for _ in range(9)]
  for y in range(9):floor[y]=floor[y][:5]+'ppp'+floor[y][8:]
  for y in [5,7]:floor[y]=floor[y][:3]+'p'*8+floor[y][11:]
  objects=[obj('fourth_'+act,label,[7,3],'orders_case' if i in [0,2,5,8] else 'sun_altar' if i==7 else 'actor',14 if i==9 else 4 if i==3 else 5)]
  if i==1:objects.append(obj('fourth_letters','信使与家书',[3,5],'orders_case'))
  if i==0:objects.append(obj('fourth_s41','黑钟村来信',[3,5],'orders_case'))
  if i==6:objects.append(obj('fourth_s42','孤岛求援',[3,5],'orders_case'))
  if i==7:objects.extend([obj('fourth_d42','两岸确认信',[3,5],'orders_case'),obj('fourth_spring','祭所力量泉',[10,5],'well')])
  if i==9:objects.append(obj('fourth_vya','维娅旧航行记录',[3,5],'orders_case'))
  if i==2:objects.append(obj('fourth_progress','各地进度',[3,5],'orders_case'))
  name='snow_cottage' if i in [0,2,8] else 'fishing_hut'
  mod=base.MODS[name];sc={'name':name,'position':[9,1],'footprint':mod['footprint'],'blocking':True,'sprite_path':mod['path'] if name=='fishing_hut' else 'res://assets/battle_tiles/modules/'+name+'.png'}
  if i in [6,7,9]:floor=['~~pppppppppp~~']*7+['~~~~pppp~~~~~~']*2
  if i==9:sc={'name':'village_clinic','position':[9,1],'footprint':[3,2],'blocking':True,'sprite_path':'res://assets/battlefield-0.3.0/modules/village_clinic.png'}
  if i==7:sc={'name':'sun_altar','position':[10,1],'footprint':[2,2],'blocking':True,'sprite_path':'res://assets/battle_tiles/modules/sun_altar.png'}
  rooms['H'+str(41+i)]=dict(title=title,hint='面对对象确认；南口返回地图',floor=floor,objects=objects,scenery=[sc],biome_override='sea' if i in [6,7,9] else 'snow' if theme=='n' else 'salt' if theme=='a' else 'grass')
 write('data/chapter4_hubs.json',{'materials':{'n':'snow'},'rooms':rooms})

if __name__=='__main__':
 reports=[]
 for c in IDS:
  m=base.Map(c);layout(m);reports.append(bake(m))
 story();write('reports/chapter4/map-build.json',reports)
 print(json.dumps(reports,ensure_ascii=False,indent=2))
