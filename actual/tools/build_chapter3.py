#!/usr/bin/env python3
"""Chapter 3 authored geography. Reuse complete approved artwork at native scale.
Only writes the eight new stages, their hubs, and additive campaign metadata.
"""
from pathlib import Path
from collections import deque
import json, copy, math, random, importlib.util
from PIL import Image

R = Path(__file__).resolve().parents[1]
def read(p): return json.loads((R / p).read_text())
def write(p, v):
    p = R / p; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')

PACK = read('assets/battle_tiles/battle-tiles.json')
SEA = read('assets/chapter2/chapter2-tiles.json')
MODS = {m['name']: m for m in PACK['modules'] + SEA['modules']}
NATURE = {s['key']: s for s in read('assets/nature/nature.json')['sprites']}
CAMPAIGN = read('data/campaign.json')
PLAN = {b['id']: b for b in json.loads((R.parent/'docs2/规划索引.json').read_text())['battles'] if b['chapter'] == 3}
WORLD = read('data/formal_world.json')
IDS = {'M31':301, 'M32':302, 'M33':303, 'F31':304, 'F32':305, 'F33':306, 'S31':311, 'S32':312}
OLD = {'.':48, ',':48, 'f':172, '^':94, 'd':242, '~':96, '#':196, '=':208, 's':191, 'b':48, '+':218, 'c':208, 'a':48}
MATERIAL = {'.':'grass', ',':'dirt', 'f':'forest', '^':'rock', 'd':'sand', '~':'sea', '#':'stone', '=':'stone', 's':'timber', 'b':'cobble', '+':'sacred', 'c':'cave', 'a':'salt'}
COUNTS = {'M31':[(6,5),(12,3),(15,2)],'M32':[(1,4),(6,4),(12,2)],'M33':[(2,3),(6,5),(12,2),(15,1)],'F31':[(6,5),(12,3),(2,2)],'F32':[(8,4),(12,3),(15,2),(3,2)],'F33':[(2,2),(8,3),(15,3),(3,3)],'S31':[(6,4),(2,2),(12,2)],'S32':[(8,4),(12,2),(15,2)]}
samples = []
for p in (R.parent/'data/stages').glob('*.json'): samples += json.loads(p.read_text()).get('enemies', [])
TEMPLATES = {cid:min([u for u in samples if int(u['class_id']) == cid], key=lambda u:(u['level'],u['max_hp'])) for cid in [1,2,3,6,8,12,15]}
# Noya uses the current female mage body/animation; this chapter does not author animation.
if 'noya' not in CAMPAIGN['characters']:
    u = copy.deepcopy(CAMPAIGN['characters']['lisa'])
    u.update(id='noya', key='noya', name_zh='诺娅', source_character='sonya', character_id=25, level=5, hp=26, max_hp=26, strength=12, skill=6, speed=7, defence=5, luck=3, exp=0, item_id=0)
    CAMPAIGN['characters']['noya'] = u
    CAMPAIGN['mapping']['noya'] = {'story_name':'诺娅','source_character':'sonya'}

class Map:
    def __init__(self, code):
        self.code=code; self.card=copy.deepcopy(PLAN[code]); self.w=self.card['width']; self.h=self.card['height']
        self.grid=[list('.'*self.w) for _ in range(self.h)]; self.props=[]; self.modules=[]; self.nature=[]; self.objects=[]; self.npcs=[]
        self.deploy=copy.deepcopy(self.card['deployment_points_by_party'][0]); self.exit=copy.deepcopy(self.card['exit']); self.boss=copy.deepcopy(self.card['boss'])
        self.reserved=set(); self.occupied=set(); self.notes=[]; self.route='alm' if code.startswith('M') or code=='S31' else 'celica'
    def rect(self,x0,y0,x1,y1,ch):
        for y in range(max(0,y0),min(self.h,y1+1)):
            for x in range(max(0,x0),min(self.w,x1+1)):self.grid[y][x]=ch
    def path(self,points,width=2,ch='='):
        for a,b in zip(points,points[1:]):
            x,y=a
            while True:
                self.rect(x-width//2,y-width//2,x+(width-1)//2,y+(width-1)//2,ch)
                if [x,y]==list(b):break
                if x!=b[0]:x+=1 if x<b[0] else -1
                else:y+=1 if y<b[1] else -1
    def prop(self,name,x,y,blocked=True):
        path='assets/battlefield-0.3.0/modules/'+name+'.png'
        im=Image.open(R/path); w,h=im.size; assert w%16==0 and h%16==0
        cells={(xx,yy) for yy in range(y,y+h//16) for xx in range(x,x+w//16)}
        assert x>=0 and y>=0 and x+w//16<=self.w and y+h//16<=self.h
        assert not cells & self.reserved,(self.code,name,'overlap')
        self.reserved |= cells
        if blocked:self.rect(x,y,x+w//16-1,y+h//16-1,'#')
        self.props.append({'path':'res://'+path,'position':[x*16,y*16]})
        self.modules.append({'name':name,'origin':[x,y],'footprint':[w//16,h//16],'cells':[list(p) for p in sorted(cells)],'logic':'#' if blocked else 'inherits_ground'})
    def module(self,name,x,y,blocked=True):
        m=MODS[name];w,h=m['footprint'];cells={(xx,yy) for yy in range(y,y+h) for xx in range(x,x+w)}
        assert x>=0 and y>=0 and x+w<=self.w and y+h<=self.h
        assert not cells & self.reserved,(self.code,name,[x,y],'overlap')
        self.reserved |= cells
        if blocked:self.rect(x,y,x+w-1,y+h-1,'#')
        self.modules.append({'name':name,'origin':[x,y],'footprint':[w,h],'cells':[list(p) for p in sorted(cells)],'logic':'#' if blocked else 'inherits_ground','tiles':m['tiles']})
    def object(self,id,kind,at,label,sprite='orders_case',**extra):
        o={'id':id,'kind':kind,'position':list(at),'label':label,'adjacent':True,'sprite':sprite};o.update(extra)
        self.objects.append(o);return o
    def cell(self,id,x,y,npcs):
        # Actual walls surround a 3x2 interior; the only opening is a visible southern gate.
        self.module('jail_bars_h',x+1,y)
        self.module('jail_bars_h',x+1,y+3)
        for mod in self.modules[-2:]:
            mod['tiles']=[[MODS['jail_bars_h']['tiles'][0][1]]*3]
        for xx in [x,x+4]:
            self.module('jail_bars_v',xx,y)
            mod=self.modules[-1];t=MODS['jail_bars_v']['tiles']
            mod['tiles']=[t[0],t[1],t[1],t[2]];mod['footprint']=[1,4]
            mod['cells'].append([xx,y+3]);self.reserved.add((xx,y+3));self.grid[y+3][xx]='#'
        self.rect(x+1,y+1,x+3,y+2,'c' if self.code=='S31' else '=')
        gx=x+2;gy=y+3
        for mod in self.modules:
            if mod['name']=='jail_bars_h' and mod['origin']==[x+1,y+3]:
                mod['tiles']=copy.deepcopy(mod['tiles']);mod['tiles'][0][1]=None
        # Gate artwork is 1x2: upper transparent area is reserved clear of actors.
        o=self.object(id,'door',[gx,gy],'打开'+('拘押院门' if self.code=='M31' else '牢门' if self.code=='S31' else '营房门'),'jail_door',opens=[[gx,gy]],unlock_units=[n[0] for n in npcs],open_tile=208,open_art_cells=[{'position':[gx,gy],'base_tile':PACK['base']['stone'][0]}])
        for i,(key,name,kind) in enumerate(npcs):self.npc(key,[x+1+i*2,y+1],name,kind,True)
        return o
    def npc(self,key,at,name,kind='escort',locked=False):
        base=CAMPAIGN['characters'].get(key,CAMPAIGN['characters']['daan']);u=copy.deepcopy(base)
        u.update(id=key,name_zh=name,position=list(at),side='player',neutral=True,temporary=True,no_experience=True,controllable=False,acted=False,quest_kind=kind,locked=locked,no_counter=True,move=2,dead=False)
        if key not in CAMPAIGN['characters']:u.update(class_id=6,**{'class':'soldier'},item_id=0,hp=28,max_hp=28,defence=5,resistance=5,magic_flags=0)
        self.npcs.append(u);self.occupied.add(tuple(at));return u
    def free(self,at):
        q=deque([tuple(at)]);seen=set(q)
        while q:
            x,y=q.popleft()
            if 0<=x<self.w and 0<=y<self.h and self.grid[y][x] not in '#^~' and (x,y) not in self.occupied:
                self.occupied.add((x,y));return [x,y]
            for dx,dy in [(0,1),(1,0),(-1,0),(0,-1)]:
                n=x+dx,y+dy
                if 0<=n[0]<self.w and 0<=n[1]<self.h and n not in seen:seen.add(n);q.append(n)
        raise AssertionError('no free spawn')

def layout(m):
    c=m.code;w=m.w;h=m.h
    if c=='M31':
        m.rect(0,0,w-1,h-1,'b')
        for yy in range(0,h,4):m.module('west_wall',0,yy)
        for mod in m.modules:
            if mod['name']=='west_wall':
                mod['tiles']=[[MODS['west_wall']['tiles'][1][0]] for _ in range(4)]
                for row in range(4):
                    if mod['origin'][1]+row in [6,7,8]:mod['tiles'][row][0]=None; m.grid[mod['origin'][1]+row][0]='='
        # West gate really exits west. Two broad parallel streets join the detention court.
        m.exit=[1,7]; m.boss=[6,7]
        m.path([[3,20],[7,20],[7,7],[1,7]],3);m.path([[7,17],[21,17],[21,7],[7,7]],3)
        for name,x,y in [('quay_warehouse',2,12),('fishing_cottage',3,2),('fishing_cottage',10,2),('quay_warehouse',17,2),('fishing_cottage',23,9),('fishing_cottage',10,19),('fishing_cottage',17,20),('village_clinic',2,9)]:m.prop(name,x,y)
        m.rect(9,9,11,15,'.');m.rect(17,10,19,15,'.');m.rect(9,4,20,5,'.')
        m.cell('court',12,10,[('detained0','被拘押的居民','escort'),('detained1','被拘押的家属','escort')])
        m.object('barricade','bridge',[20,16],'移开侧街路障','crates',optional=True,opens=[[20,16]],open_tile=208,open_art_cells=[{'position':[20,16],'base_tile':PACK['base']['stone'][0]}]);m.grid[16][20]='#'
        m.npc('street_resident',[5,18],'撤离居民','escort')
        m.object('street_clinic','visit',[3,10],'访问街边医舍','orders_case',approach=[3,11],optional=True,dialogue='医者：拘押院的门在南侧。西门在左上方，那里有人接应撤离的居民。',reward_item=0,building='village_clinic')
        m.notes=['西门移至西侧(1,7)，追捕队长守门；两条街连接拘押院南门。原蓝图东北角“西门”不沿用。']
    elif c=='M32':
        m.path([[3,20],[9,20],[9,12],[16,12],[25,12],[28,4],[28,1]],3,',')
        m.path([[9,20],[20,20],[25,14],[25,4],[28,4]],2,',')
        m.rect(13,10,18,14,'b');m.rect(23,12,28,16,'b');m.exit=[28,1]
        for name,x,y in [('hill_granary',12,7),('quay_warehouse',24,8),('command_pavilion',24,1),('fishing_cottage',3,11)]:m.prop(name,x,y)
        m.path([[15,14],[28,14],[28,1]],2,',')
        m.object('station_w','control',[16,12],'控制西运输站','white_flag',adjacent=False)
        m.object('station_n','control',[25,14],'控制北运输站','white_flag',adjacent=False)
        m.npc('transport_cart',[15,14],'工匠运输车','transport',True).update(event_object=True,sprite_path='res://assets/battle_tiles/modules/grain_wagon.png',sprite_offset=[0,0])
        m.object('cart_release','release',[15,14],'打开运输车锁','orders_case',follows_unit='transport_cart',optional=False,sprite_path='res://assets/battle_tiles/modules/grain_sacks.png')
        m.npc('road_worker',[5,18],'运输工','witness')
    elif c=='M33':
        m.rect(24,0,w-1,h-1,'~');m.rect(0,0,2,17,'^');m.path([[4,23],[8,23],[8,16],[14,16],[14,8],[23,8],[23,4]],3)
        m.rect(10,6,23,19,'b');m.path([[6,13],[23,13]],2)
        m.prop('coastal_keep',18,1);m.prop('quay_warehouse',17,16);m.prop('village_clinic',8,6)
        m.module('rail_v',24,7);m.module('rail_v',24,15);m.rect(24,11,26,13,'s')
        m.object('dock_control','control',[23,12],'控制投送码头','white_flag',adjacent=False)
        m.object('workshop','record',[18,18],'取工房投送记录','orders_case',approach=[18,19])
        m.npc('fort_workers',[12,10],'工房工匠','witness',True)
    elif c=='F31':
        m.rect(0,0,w-1,h-1,'~');m.rect(10,1,w-2,h-3,'b');m.rect(2,14,7,20,'s');m.path([[5,17],[12,17]],2,'s');m.path([[12,17],[23,17],[23,4]],3)
        m.module('bow',3,12,False);m.module('stern',3,19,False);m.module('rail_v',2,15)
        for name,x,y in [('quay_warehouse',12,3),('quay_warehouse',18,3),('command_pavilion',23,1),('fishing_cottage',11,10)]:m.prop(name,x,y)
        m.exit=[5,18];m.deploy=[[x,y] for y in [17,18,19] for x in [3,4,6]]
        m.cell('ship_lock',17,6,[('dock_patients0','北码头伤者','patient')]);m.cell('mooring',19,12,[('dock_patients1','南码头伤者','patient')])
        m.objects[0]['label']='解除扣船所封锁';m.objects[1]['label']='打开停泊通道'
        m.notes=['部署调整到完整己方船甲板，登船点位于可见跳板内侧；南北两组伤者经码头主路返回。']
    elif c in ['F32','S32']:
        m.rect(0,0,w-1,h-1,'a')
        for cx,cy,rx,ry in [(4,6,3,4),(18,3,3,2),(24,18,2,2)]:
            for y in range(h):
                for x in range(w):
                    if ((x-cx)/rx)**2+((y-cy)/ry)**2<1:m.grid[y][x]='~' if cx==4 else '^'
        m.path([[4,h-4],[10,h-4],[10,12],[15,12],[21,8],[24,3]],3,',');m.path([[10,16],[23,16],[23,8]],2,',')
        if c=='F32':
            m.module('well',14,11);m.rect(13,12,15,13,'=');m.grid[12][13]='+'
            m.prop('fishing_cottage',7,8);m.prop('command_pavilion',23,1)
            m.object('salt_barrier','bridge',[21,14],'移开干道路障','crates',optional=True,opens=[[21,14]],open_tile=208,open_art_cells=[{'position':[21,14],'base_tile':PACK['base']['dirt'][0]}]);m.grid[14][21]='#'
            m.npc('salt_guide',[5,18],'盐路向导','guide');m.object('guide_notes','record',[8,16],'查看船民路线册','orders_case',optional=True)
        else:
            m.prop('command_pavilion',23,1);m.prop('fishing_cottage',7,5)
            m.cell('mage_barrack',11,8,[('noya','诺娅','witness')]);m.cell('civilian_barrack',18,12,[('noya_brother','诺娅的弟弟','witness'),('salt_residents','盐原居民','witness')])
            m.objects[0]['label']='打开术士营房';m.objects[1]['label']='打开居民营房'
    elif c=='F33':
        m.rect(0,0,w-1,h-1,'a');m.rect(5,4,25,18,'b')
        m.path([[4,21],[9,21],[9,15],[14,15],[22,15],[22,4]],3)
        m.path([[9,15],[9,8],[22,8]],2)
        m.prop('coastal_keep',19,0);m.prop('quay_warehouse',7,3);m.prop('quay_warehouse',15,4)
        m.cell('workers_gate',12,9,[('ritual_worker0','维持设施的术士甲','witness'),('ritual_worker1','维持设施的术士乙','witness')])
        m.objects[-1]['label']='打开术士工房'
        m.object('regulation_record','record',[16,6],'复制调节记录','orders_case',approach=[16,7])
        m.object('control_array','control',[21,14],'稳定控制阵台','white_flag',adjacent=False)
        m.module('sun_altar',23,10);m.module('ritual_lamp',18,14)
    else:
        m.rect(0,0,w-1,h-1,'^');m.rect(2,2,w-3,h-3,'c');m.path([[4,17],[10,17],[10,5],[18,5]],3,'=')
        m.cell('family_w',3,3,[('family0','山村家属甲','witness')]);m.cell('family_e',13,3,[('family1','山村家属乙','witness')])
        m.prop('mine_adit',3,10);m.module('brazier',10,9);m.module('brazier',17,11)
        m.notes=['地牢两间牢房独立开门，家属分别保存；南侧连廊可到两门前。']
    # Native healing landmarks are normal recovery terrain, never treatment resources.
    if c not in ['F32','M31']:
        p=[7,h-5] if c!='S31' else [10,15]
        if m.grid[p[1]][p[0]] not in '#^~':m.grid[p[1]][p[0]]='+';m.module('flowers',p[0],p[1],False)

def bake(m):
    c=m.code;rng=random.Random(IDS[c]);b=m.card
    for p in m.deploy:assert m.grid[p[1]][p[0]] not in '#^~',(c,'deployment',p)
    m.occupied |= set(map(tuple,m.deploy))
    # Preserve exact objective-facing cells and the gate queue for NPCs.
    for o in m.objects:m.occupied.add(tuple(o['position']))
    enemies=[]
    def enemy(cid,at,i,boss=False):
        u=copy.deepcopy(TEMPLATES[cid]);hp=32 if boss else 26 if cid==2 else 23
        u.update(id=c+('_boss' if boss else '_e'+str(i)),position=m.free(at),side='enemy',acted=False,exp=0,item_id=0,group_id=0,raw_ai_flags=0,ai_flags=0,level=6 if boss else 4,hp=hp,max_hp=hp,strength=12 if boss else 10,skill=6,speed=5 if cid in [1,8,3] else 4,defence=7 if boss or cid==2 else 4,luck=0,exp_value=55 if boss else 36,magic_flags=1 if cid==15 else 0,raw_magic_flags=1 if cid==15 else 0)
        u['name_zh']=dict(M31='追捕队长',M32='护送长',M33='石堡堡主',F31='扣船队长',F32='封路神官',F33='控制神官',S31='狱卒首领',S32='营长')[c] if boss else {1:'护送骑兵',2:'重装守军',3:'石像守卫' if c=='F33' else '飞行守军',6:'士兵',8:'佣兵',12:'弓手',15:'术士'}[cid]
        if boss:u.update(objective_boss=True,behavior='guard',item_id={'M32':3,'M33':50,'F33':51}.get(c,0))
        elif cid in [2,12,15] or i>4:u['behavior']='guard'
        if c in ['M31','F31']:u['no_drop']=True
        return u
    boss_cid=15 if c in ['F32','F33'] else 1 if c=='M32' else 6
    enemies.append(enemy(boss_cid,m.boss,0,True));m.boss=enemies[0]['position']
    anchors=copy.deepcopy(b['enemy_anchors'])
    if c=='M31':anchors=[[7,12],[20,9],[20,18],[10,7]]
    if c=='F31':anchors=[[13,17],[23,8],[24,17],[15,6]]
    for cid,count in COUNTS[c]:
        for _ in range(count):enemies.append(enemy(cid,anchors[(len(enemies)-1)%4],len(enemies)))
    if c=='M33':
        u=copy.deepcopy(CAMPAIGN['characters']['german']);u.update(position=m.free([16,18]),side='enemy',behavior='guard',no_drop=False,id='german',acted=False);enemies.append(u)
    if c=='F32':next(u for u in enemies if u['class_id']==12)['item_id']=20
    rein=[];rt={'M31':4,'F31':3}.get(c,0)
    if rt:
        for i in range(2):
            u=enemy(6,[25,20] if c=='M31' else [25,18],50+i);u.update(id=c+'_r'+str(i),behavior='advance');rein.append(u)
    for i,u in enumerate(m.npcs):u['player_slot']=len(m.deploy)+i
    protect=set(m.occupied)|{tuple(m.exit)}|m.reserved
    for o in m.objects:
        x,y=o['position'];protect|={(x+dx,y+dy) for dx,dy in [(0,0),(0,1),(1,0),(-1,0),(0,-1)]}
    # Whole nature silhouettes are restricted to their terrain footprints.
    taken=set();keys=['pine_young','pine_broad'] if c=='M32' else ['boulder','outcrop','peak_low']
    for y in range(m.h-2):
        for x in range(m.w-2):
            ch=m.grid[y][x]
            if ch not in ('.','^') or rng.random()>.18:continue
            key=rng.choice(keys if ch=='.' else ['peak_low','outcrop']);s=NATURE[key];fw=math.ceil(s['size'][0]/16);fh=math.ceil(s['size'][1]/16)
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
    d={'schema_version':4,'id':IDS[c],'code':c,'name_zh':b['name'],'chapter':3,'route':m.route,'node':next(int(k) for k,v in WORLD['nodes'].items() if v['id']==b['node']),'map':{'width':m.w,'height':m.h,'tiles':[OLD[ch] for row in m.grid for ch in row]},'logic_grid':[''.join(row) for row in m.grid],'art_atlas':'res://assets/chapter2/chapter2-tiles.png','art_columns':32,'art_layers':layers,'art_modules':m.modules,'art_props':m.props,'natural_props':m.nature,'tactical_review_version':'0.8.0','surroundings':'sea' if c in ['F31','M33'] else 'cave' if c=='S31' else 'land','nature_layout':{'biome':'salt' if c in ['F32','F33','S32'] else 'rock' if c=='S31' else 'grass','props':[]},'characters':{},'player_positions':m.deploy,'enemies':enemies,'npc_units':m.npcs,'terrain':read('data/stages/M11.json')['terrain'],'enemy_group_ids':[],'objects':m.objects,'reinforcements':rein,'reinforcement_turn':rt,'exit':m.exit,'boss_id':c+'_boss','targets':[o['position'] for o in m.objects],'goal':b['goal'],'before':b['before'],'during':b['during'],'after':b['after'],'optional':b['optional'],'event_boats':[],'clear_training_exp':20,'visual_notes':m.notes,'tactical_notes':[]}
    if c=='M32':
        d['transport_path']=[[15,14],[16,14],[17,14],[18,14],[19,14],[20,14],[21,14],[22,14],[23,14],[24,14],[25,14],[26,14],[27,14],[28,14]]+[[28,y] for y in range(13,0,-1)]
        for x,y in d['transport_path']:assert m.grid[y][x] in ',=bs',(c,'cart must follow visible road',[x,y])
        d['tactical_notes']=['运输车第5回合开始沿大道北撤，每次敌方行动结束前进一格；控制任一运输站会使车停下。打开车锁后工匠留在安全处；两站都须控制。']
    if c=='M31':d['before']='蕾娜或城外军官：西门在左上方，还没有封死。先打开街心拘押院的南门。／胡纳普：让居民从西门走，愿意放下武器的人留在街边。'
    if c=='F31':d['before']='米蕾或船医：他们把伤者扣在南北两处院里，还要拖走船。／艾琳：护卫守住西南跳板，我们打开两处通道，把人带回自己的船。'
    if c=='F32':d['tactical_notes']=['向导沿干道前进，近敌时等待；若向导遇难，取回船民路线册仍能继续调查。盐地没有隐形伤害。']
    if c=='F33':d['tactical_notes']=['先开术士工房，再复制北侧记录并稳定东侧阵台。两名维持设施的术士都必须存活。']
    if c=='M33':d['tactical_notes']=['堡主败北后，靠近工房旁的格曼可接受投降或只解除武装。控制码头、取回投送记录后结算。']
    complete_labels={'court':'拘押院门已打开','cart_release':'运输车锁已打开','workshop':'投送记录已取得','ship_lock':'扣船所已解锁','mooring':'停泊通道已打开','workers_gate':'术士工房已打开','regulation_record':'调节记录已复制','control_array':'控制阵台已稳定','family_w':'西牢门已打开','family_e':'东牢门已打开','mage_barrack':'术士营房已打开','civilian_barrack':'居民营房已打开','guide_notes':'路线册已取得'}
    for o in d['objects']:
        if o['id'] in complete_labels:o['completed_label']=complete_labels[o['id']]
        if o['kind']=='control':o['name_zh']=o['label'].removeprefix('控制')
    write('data/stages/'+c+'.json',d)
    CAMPAIGN['stages'][str(IDS[c])]={'code':c,'path':'res://data/stages/'+c+'.json','node':d['node']}
    return {'code':c,'size':[m.w,m.h],'enemies':len(enemies),'reinforcements':len(rein),'interactions':len(m.objects),'walkable_open':len(opened),'anchor_checks':'passed','notes':m.notes}

def pages(lines):return [{'speaker':s.split('：',1)[0],'text':s.split('：',1)[1]} for s in lines]

def story():
    CAMPAIGN['characters']['noya']['character_id']=25
    CAMPAIGN['chapter_limit']=3
    CAMPAIGN['scenes'].update({
      'D31':pages(['旁白：现在，海峡城庆典。胡纳普伸出的手仍停在两人之间，海峡另一岸的船还在等待靠岸。','胡纳普：先住手。让她把话说完。','艾琳：这是母亲的航图和裴萨的军令。你们说海上已经没人，可船上的伤者还活着。','赫兰：我听说群岛还有居民。我以为神会给迁徙留出时间。','乌库布·卡基：艾琳。那年你摔伤了腿，是你母亲背着你离开的。','艾琳：她的船后来被截住了。','乌库布·卡基：我让她留在受保护的海面。她没有听。','胡纳普：那现在船上的人呢？他们留在那里也活不下去。','乌库布·卡基：庇护将继续集中于西大陆。把他们送回去，大典以后，西岸能够接收的人会被列出来。','艾琳：他们等不到大典。','赫兰：这里的村庄刚刚有了日光。我不能让仪式停下来。','胡纳普：我不能让你们把她送回正在崩坏的海面。','乌库布·卡基：拘押阻止仪式的人。大典将完成转移。','旁白：守卫封住传光台。西队沿西街救出居民，东队返回码头接应伤者。']),
      'D32':pages(['旁白：两队在城外旧街暂时会合。获救者已经交给留守医者。','胡纳普：你去过眠谷吗？','艾琳：到了山口。东边的路已经不在了。','胡纳普：我记得你家门前有一棵树。','艾琳：母亲也一直记得。她画航图的时候，还在旁边画过那棵树。','胡纳普：……我本来想带你回去看看。','艾琳：先把船上的人安置好吧。还有人在等我们。','胡纳普：我借日塔保住了村庄，不能让他们再受冻。','艾琳：我见过另一岸失去庇护。不能继续扩大转移。','胡纳普：那就先截住军路和原料。我去查石堡，把运走的工匠带回来。','艾琳：我沿母亲的航图去盐路和提炼院。把记录查清，再谈怎样停塔。','旁白：两队约定由固定信使传递消息，分别行动。']),
      'D33':pages(['工匠：石堡的投送记录与提炼院的调节记录相符。断裂以前，各地地脉会互相调节，不必把所有庇护集中在神幕。','术士：现在的土地已经依赖日塔。还要找到完整观测记录，验证停用办法，不能直接拆塔。','艾琳：这是观测台的位置。拿到完整记录，我就送信回来。','胡纳普：日塔还在给北面的村庄供光。我不能现在拆掉它。','艾琳：我知道了。要是不能安全停用，我会告诉你。','胡纳普：那里的守军也会看见你。别只带几个术士过去。','艾琳：船长已经安排好护卫。你也把医者留在能照顾到人的地方。','医者：营站收到一份救治泉液。教堂和灯屋尚未使用的份额也已运来，今后两队共用。每人仍只能接受一次救治。','旁白：营站成为共同补给与传信处。下一步，西队护住北境村庄，东队寻找安全停用的观测记录。'])})
    write('data/campaign.json',CAMPAIGN)
    supply=read('data/equipment_progression.json');supply['starter_items']['noya']=66
    supply['clear_rewards'].update({'311':[3],'312':[51]});write('data/equipment_progression.json',supply)
    # Compact explorable rooms use the existing authored maritime/land room renderer.
    rooms={}
    def obj(action,name,pos,sprite='actor',source=5,**extra):return dict(action=action,name=name,position=pos,sprite=sprite,source=source,**extra)
    def room(id,title,hint,objects,theme='land',scenery=None):
        floor=[('a' if theme=='salt' else '.')*14 for _ in range(9)]
        for y in range(9):floor[y]=floor[y][:5]+'ppp' +floor[y][8:]
        for yy in [5,7]:floor[yy]=floor[yy][:3]+'p'*8+floor[yy][11:]
        if theme=='sea':floor=['~~pppppppppp~~']*7+['~~~~pppp~~~~~~','~~~~pppp~~~~~~']
        rooms[id]=dict(title=title,hint=hint,floor=floor,objects=objects,scenery=scenery or [],biome_override='grass' if theme=='land' else 'sand' if theme=='salt' else 'sea')
    def sc(name,x,y):
        m=MODS[name];return dict(name=name,position=[x,y],footprint=m['footprint'],blocking=True,sprite_path=m['path'] if name in [x['name'] for x in SEA['modules']] else 'res://assets/battle_tiles/modules/'+name+'.png')
    room('H30','第三章 · 海峡城庆典','面对赫兰，接续庆典', [obj('third_prologue','赫兰',[7,3],source=4),obj('third_altar','传光台',[10,4],'sun_altar')],scenery=[sc('barracks',1,0),sc('barracks',10,0)])
    room('H31','城外旧街 · 避难处','面对同伴确认下一步', [obj('third_reunion','会合约定',[7,3],source=2),obj('third_people','留守医者',[3,5],source=14)],scenery=[sc('fishing_hut',1,0),sc('fishing_hut',10,0)])
    room('H32','军需大道 · 转运站','登记工匠与物资，查看地牢求助', [obj('third_supply','获救工匠',[7,3]),obj('third_s31','山村来信',[3,5],'orders_case')],scenery=[sc('grain_store',1,0),sc('grain_wagon',10,3)])
    room('H33','沿海石堡 · 工房','确认投送记录，与格曼交谈', [obj('third_records_w','投送记录',[7,3],'orders_case'),obj('third_german','格曼',[3,5],source=12)],'sea',[sc('captain_cabin',9,1)])
    room('H34','盐路 · 船民井台','确认路线，查看盐原求助', [obj('third_route_e','船民',[7,3]),obj('third_s32','盐原求助',[3,5],'orders_case')],'salt',[sc('fishing_hut',1,0),sc('well',10,3)])
    room('H35','提炼院 · 记录庭','确认调节记录，前往营站', [obj('third_records_e','获救术士',[7,3],source=27)],'salt',[sc('barracks',1,0),sc('sun_altar',10,2)])
    room('H36','山村地牢 · 安置处','向家属确认救援结果',[obj('third_families','家属',[7,3])],scenery=[sc('cave_entry',1,0),sc('fishing_hut',10,0)])
    room('H37','盐原营地 · 安置处','问清经过，再决定是否同行',[obj('third_noya','诺娅',[7,3],source=25),obj('third_brother','留守医者',[3,5],source=14)],'salt',[sc('fishing_hut',1,0)])
    room('H10','沿海会合营站','会谈、整备与共享救治',[obj('third_council','会谈处',[7,3],source=2),obj('treatment','共享救治处',[3,5],'well'),obj('third_training','训练台',[10,5],'sun_altar'),obj('third_messenger','信使',[10,7]),obj('third_relations','营火旁',[3,7],'brazier')],scenery=[sc('fishing_hut',1,0),sc('captain_cabin',10,0)])
    write('data/chapter3_hubs.json',{'materials':{'p':'stone','a':'salt'},'rooms':rooms})

if __name__=='__main__':
    reports=[]
    for c in IDS:
        m=Map(c);layout(m);reports.append(bake(m))
    story();write('reports/chapter3/map-build.json',reports)
    print(json.dumps(reports,ensure_ascii=False,indent=2))
