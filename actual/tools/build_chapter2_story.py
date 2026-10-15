#!/usr/bin/env python3
"""Incrementally add chapter two. Never regenerate chapter-one gameplay or art."""
from pathlib import Path
import json, copy
ROOT=Path(__file__).resolve().parents[1]
def read(p): return json.loads((ROOT/p).read_text())
def write(p,d):
 q=ROOT/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def page(who,text):return {'speaker':who,'text':text}
def pages(*lines):return [page(*line.split('：',1)) for line in lines]
campaign=read('data/campaign.json');source=read('data/legacy/campaign.json')['characters']
cast={'eileen':('艾琳','celica'),'mireille':('米蕾','genny'),'lisa':('莉莎','mae'),'carlo':('卡洛','saber'),'lord':('洛德','valbar'),'roan':('罗恩','atlas'),'shia':('希雅','catria')}
for key,(name,old) in cast.items():
 u=copy.deepcopy(source[old]);u.update(id=key,key=key,name_zh=name,source_character=old,side='player',dead=False,acted=False)
 # The approved story makes Roan a fisherman who fights with a bow. His face
 # stays distinct from Daan; combat class and full animation follow Archer.
 if key=='roan':
  for stat in ['level','hp','max_hp','strength','skill','speed','luck','defence','move','class','class_id']:
   u[stat]=copy.deepcopy(source['leo'][stat])
  u['level']=3;u['class']='archer';u['class_id']=12;u['item_id']=0
  u['adaptation']='Atlas portrait/village identity; Archer class and weapon animation per approved Roan role.'
 if key=='shia':u['item_id']=0 # Starting Catria ring is not a second unlisted chapter reward.
 campaign['characters'][key]=u;campaign['mapping'][key]={'story_name':name,'source_character':old}
campaign['initial_east_party']=['eileen','mireille','lisa','carlo']
for i in range(1,7):campaign['stages'][str(200+i)]={'code':f'F2{i}','path':f'res://data/stages/F2{i}.json','node':17+i}
for i in range(1,3):campaign['stages'][str(210+i)]={'code':f'S2{i}','path':f'res://data/stages/S2{i}.json','node':32+i}
sc=campaign['scenes']
sc['D21']=pages('艾琳：这块船牌，你留了两年？','卡洛：有人拿它抵债。我看见的时候，你母亲的船已经没了。','艾琳：那天你为什么不在船上？','卡洛：我提前走了。有人在下一座港口等我讨债。','艾琳：这次的船钱我付。到了押送舰，你带我上去。','卡洛：好。到了那里，我不会再先走。')
sc['D22_FIRST']=pages('艾琳：我母亲的船上有你认识的人。她上次还替你带过药。','裴萨：我劝过她回去。她偏要把船开到神幕边上。','艾琳：所以你连伤者的船也不放过？','裴萨：船一旦过去，后面的人就都会跟着过去。')
sc['D22_DEFEAT']=pages('艾琳：她留下的航图在哪里？','旁白：裴萨指向主楼的神教箱。牢门边传来船员的呼喊，撤离还没有结束。')
sc['D22']=sc['D22_FIRST']+sc['D22_DEFEAT']
sc['F25_MYTH']=pages('旁白：航图夹在七羽日冠的封印下。薇娅的边记记着：相邻两岛，曾在同一天得到不同的照明。','艾琳：这是母亲写的日期。那一天，我们的船还在这里。','引航者：命令也在箱里：禁止西渡，日光的转移交由神裁定。裴萨不是私下画的封航线。','艾琳：古道的石门还在图上。先把伤者带上船，再去西岸问清楚。')
sc['D26_ARRIVAL']=pages('旁白：船团终于抵达海峡城。广场正在为西大陆的日返举行庆典，船上的伤者仍在等候靠岸。','教团守卫：传光设施不得接近。破坏封印的人，带到台前。','艾琳：海上还有人。现在把船拖回去，他们没有地方停。','赫兰：先将她拘押。仪式结束后再安排船团。','旁白：艾琳在告示上看见了胡纳普的名字。那枚旧绳结仍系在她手上。','艾琳：胡纳普……你真的在这里？','旁白：广场的钟声响起。她被押到传光台前，故事回到庆典上的那一刻。')
campaign['chapter_limit']=2
campaign['chapter2']={'title':'没有归来的船','route':'celica','start_node':17,'start_hub':'H21','end_node':23,'end_hub':'H27','hubs':'res://data/chapter2_hubs.json','stage_ids':[201,202,203,204,205,206,211,212],'scope':'Second memory chapter; preserve both armies and stop before Chapter 3.','portrait_mapping':{k:{'name':v[0],'character_id':source[v[1]]['character_id']} for k,v in cast.items()},'limited_rewards':{'F23_holy_sword_taken':16,'F25_holy_bow_taken':21,'lighthouse_spring':{'stat':'resistance','amount':1,'uses':1,'cap':40}}}
write('data/campaign.json',campaign)

# These are complete, reusable image modules at integer native dimensions.
new_sizes={'bow':[3,2],'stern':[3,2],'rail_h':[4,1],'rail_v':[1,4],'captain_cabin':[3,2],'mast':[2,4],'hatch':[2,2],'gangplank':[3,1],'lighthouse':[3,5],'fishing_hut':[3,2],'bollard':[1,1],'rowboat':[2,3]}
old={m['name']:m['footprint'] for m in read('assets/battle_tiles/battle-tiles.json')['modules']}
def decor(name,x,y,block=True):
 return {'name':name,'position':[x,y],'footprint':new_sizes.get(name,old.get(name)), 'sprite_path':f"res://assets/{'chapter2' if name in new_sizes else 'battle_tiles'}/modules/{name}.png",'blocking':block}
def actor(action,x,y,name,source,**extra):return {'action':action,'position':[x,y],'name':name,'sprite':'actor','source':source,'text':'',**extra}
def obj(action,x,y,name,sprite,**extra):
 m=decor(sprite,x,y);return {'action':action,'position':[x,y],'name':name,'sprite':sprite,'source':0,'text':'','sprite_path':m['sprite_path'],'footprint':m['footprint'],**extra}
def hub(node,title,hint,rows,objects,scenery,**extra):
 assert len(rows)==9 and all(len(r)==14 for r in rows),(title,[(r,len(r))for r in rows])
 return {'node':node,'title':title,'hint':hint,'biome':'sea','floor':rows,'spawn':[6,7],'exit':[6,8],'objects':objects,'scenery':scenery,**extra}
shore=['~~~ss....sss~~','~sss........s~','ss...........s','s............s','s............s','~s..........s~','~ss........ss~','~~ssss=ssss~~~','~~~~~~=~~~~~~~']
deck=['~~~========~~~','~============~','~============~','~============~','~============~','~============~','~============~','~~==========~~','~~~~~~=~~~~~~~']
rooms={}
rooms['H21']=hub(17,'半年前 · 风灯岛船坞','与卡洛谈船牌，确认出航',shore,[actor('east_departure',8,5,'卡洛',27),actor('east_mireille',3,4,'米蕾',15,party='mireille'),actor('east_lisa',6,2,'莉莎',13,party='lisa'),obj('east_chart_start',5,1,'母亲的残图','orders_case')],[decor('fishing_hut',0,0),decor('lighthouse',10,0),decor('bollard',4,7),decor('rowboat',11,6,False)])
rooms['H22']=hub(18,'船团甲板 · 停泊','向船长确认灯线，查看求助',deck,[actor('sea_route',6,2,'船长',5),actor('invite_s21',4,4,'求救船员',7),actor('s21_report',9,5,'地方医者',15)],[decor('captain_cabin',1,0),decor('bow',11,0,False),decor('stern',0,6,False),decor('mast',10,2),decor('bollard',3,6)])
rooms['H23']=hub(19,'押送舰 · 获救甲板','安置全部伤者，再与洛德交谈',deck,[obj('prisoners_treat',3,4,'伤者安置处','medicine_wagon'),actor('lord',9,5,'洛德',18,recruit='lord'),actor('captives_route',6,2,'引航者',7)],[decor('captain_cabin',1,0),decor('hatch',10,0),decor('rail_h',9,7),decor('bollard',2,6)])
rooms['H24']=hub(20,'礁岛 · 渔村岸边','向长者问路，海洞可先行',shore,[actor('reef_route',6,2,'渔村长者',7),actor('roan',3,5,'罗恩',22,recruit='roan'),actor('invite_s22',10,5,'旧船员',7),obj('holy_sword',8,3,'岸上宝箱','orders_case')],[decor('fishing_hut',0,0),decor('boulders',10,0),decor('rowboat',11,6,False),decor('bollard',4,7)])
rooms['H25']=hub(21,'海灯岛 · 航灯院','先安置岛民，可训练与取泉',shore,[actor('islanders_settle',6,2,'留守骑士',10),actor('shia',9,5,'希雅',31,recruit='shia'),obj('east_training',3,4,'训练台','sun_altar'),obj('resistance_spring',3,6,'抗性泉 · 剩余一次','well'),actor('r05',8,6,'卡洛',27,party='carlo')],[decor('fishing_hut',0,0),decor('lighthouse',10,0),decor('bollard',4,7)])
rooms['H26']=hub(22,'潮狩军港 · 神教仓院','查看航图，确认伤者再西渡',['~~~cccccccc~~~','~cccccccccccc~','sccccccccccccs','sccccccccccccs','sccccccccccccs','~cccccccccccc~','~sccccccccccs~','~~ssss=ssss~~~','~~~~~~=~~~~~~~'],[obj('chart_recover',6,2,'神教箱','orders_case'),obj('holy_bow',3,4,'军港武器箱','crates'),actor('ancient_departure',10,5,'船长',5),obj('harbor_patients',6,5,'撤离者安置处','medicine_wagon'),actor('r05',9,3,'卡洛',27,party='carlo')],[decor('barracks',1,0),decor('captain_cabin',10,0),decor('bollard',4,7),decor('rowboat',11,6,False)])
rooms['H27']=hub(23,'现在 · 海峡城广场外','与守卫交涉，接回庆典', ['cccccccccccccc']*9,[actor('east_finale',7,3,'教团守卫',5),actor('arrival_captain',3,5,'船长',5),obj('arrival_altar',6,1,'传光台','sun_altar')],[decor('barracks',1,0),decor('barracks',10,0)],biome_override='cobble')
# Curved coastlines and small, whole natural props keep safe-room silhouettes
# distinct. The logical grid remains the source of truth for walking.
rooms['H22']['title']='船团停泊栈桥'
rooms['H23']['title']='押送舰旁 · 救护栈桥'
rooms['H22']['scenery']=[d for d in rooms['H22']['scenery'] if d['name'] not in ['bow','stern']]
rooms['H22']['scenery'] += [decor('rail_h',5,0),decor('rail_v',0,2),decor('rail_h',7,7),decor('rowboat',12,5,False)]
rooms['H23']['scenery'] += [decor('rail_h',5,0),decor('rail_v',0,2),decor('rowboat',12,4,False)]
rooms['H24']['floor']=['~~~~sss.sss~~~','~~sss......ss~','~ss.........ss','ss...........s','s............s','ss..........ss','~ss........ss~','~~~sss=ssss~~~','~~~~~~=~~~~~~~']
rooms['H25']['floor']=['~~sss.....ssss','~ss..........s','ss...........s','s............s','s...........ss','ss.........ss~','~ss.......sss~','~~~sss=ssss~~~','~~~~~~=~~~~~~~']
def nature(name,x,y,w,h):return {'name':name,'position':[x,y],'footprint':[w,h],'sprite_path':f'res://assets/nature/{name}.png','blocking':True}
rooms['H21']['scenery'] += [nature('pine_broad',8,0,2,2),nature('brush',2,6,1,1)]
rooms['H24']['scenery'] += [nature('pine_tall',10,1,2,2),nature('brush',11,3,1,1)]
rooms['H25']['scenery'] += [nature('brush',2,5,1,1),nature('pine_young',8,0,1,1)]
rooms['H25']['scenery']=[item for item in rooms['H25']['scenery'] if item['name']!='bollard']
for room in ['H21','H24','H25']:
 for item in rooms[room]['scenery']:
  if item['name']=='fishing_hut':item['position']=[2,0]
for room,cells in {'H21':[(6,6),(6,5),(6,4),(7,4),(8,4),(7,3)],'H24':[(6,6),(6,5),(6,4),(5,4),(5,3)],'H25':[(6,6),(6,5),(6,4),(5,4),(5,3),(6,3)]}.items():
 rows=[list(r) for r in rooms[room]['floor']]
 for x,y in cells:rows[y][x]='d'
 rooms[room]['floor']=[''.join(r) for r in rows]
for room in ['H25','H26']:rooms[room]['environment_tint']=[.75,.8,.9]
write('data/chapter2_hubs.json',{'schema':1,'native_tile_size':16,'size':[14,9],'origin':[16,8],'rooms':rooms,'materials':{'~':'sea','s':'sand','.':'grass','=':'timber','c':'cobble','d':'dirt'},'logic':'Water is impassable; complete objects and modules block their full footprints; all interactions have a reachable adjacent cell.'})
print('Incremental chapter-two story:',len(cast),'characters,',len(rooms),'hubs, 8 stage registrations. Chapter-one records retained.')
