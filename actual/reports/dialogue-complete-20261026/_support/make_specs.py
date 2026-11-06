from pathlib import Path
import json
R=Path(__file__).resolve().parents[4];O=R/'actual/reports/dialogue-complete-20261026'
rooms={
 'P00':(0,'alm',101,['guard','altar','prologue']),
 'H01':(1,'alm',101,['grave','otto','daan']),
 'H02':(1,'alm',102,['grain','fula','crown']),
 'H03':(1,'alm',103,['orders','lena']),
 'H04':(1,'alm',103,['cooperate','lance','treatment']),
 'H05':(1,'alm',104,['camp']),
 'H06':(1,'alm',105,['treat','ceremony','ceremony_confirm']),
 'H07':(1,'alm',101,['invite','camp']),
 'H08':(1,'alm',111,['beck','mine_survivor','mine_apprentice','tools']),
 'H09':(1,'alm',112,['staff','hervi','transport','delivery']),
}
node_stage={17:201,18:201,19:202,20:203,21:204,22:205,23:206,6:301,7:302,8:303,24:305,25:306,35:311,36:312,9:303,10:401,11:402,12:403,13:404,26:405,27:406,28:407,29:408,37:411,38:412,14:502,30:504,39:511,15:533}
for chapter in [2,3,4,5]:
 data=json.loads((R/f'actual/data/chapter{chapter}_hubs.json').read_text())
 for room,d in data['rooms'].items():
  route='celica' if room in ['H21','H22','H23','H24','H25','H26','H27','H34','H35','H37','H45','H46','H47','H48','H50','H53','H54','H56'] else 'alm'
  stage={'H30':301,'H31':301,'H10':303,'H51':501,'H52':502,'H53':503,'H54':504,'H55':533,'H56':511}.get(room,node_stage.get(d.get('node',6),301))
  # Room data often omits the node; explicit battle associations are canonical.
  stage.update({}) if isinstance(stage,dict) else None
  stage={'H32':302,'H33':303,'H34':305,'H35':306,'H36':311,'H37':312,'H41':401,'H42':402,'H43':403,'H44':404,'H45':405,'H46':406,'H47':407,'H48':408,'H49':411,'H50':412}.get(room,stage)
  rooms[room]=(chapter,route,stage,[o['action'] for o in d['objects']])
extra={'H02':['recruit_fula'],'H03':['recruit_lena'],'H08':['recruit_beck'],'H09':['recruit_hervi'],'H23':['east_recruit_lord'],'H24':['east_recruit_roan'],'H25':['east_recruit_shia','east_magic_info'],'H26':['east_sail_confirm'],'H33':['third_recruit_german'],'H37':['third_recruit_noya'],'H50':['fourth_recruit_celine'],'H10':['third_relations'],'H48':[]}
for room,actions in extra.items():
 ch,route,stage,old=rooms[room];rooms[room]=(ch,route,stage,list(dict.fromkeys(old+actions)))
# The training-only menus have no authored character speech; their notices are kept in the common appendix.
milestones=['village_ready','korlan_defeated','grain_shared','cooperation_done','tools_reward','clinic_staffed','workers_treated','chapter1_complete','east_departure_ready','F21_confirmed','F22_confirmed','F23_confirmed','islanders_settled','islanders_survived','sea_chart_collected','harbor_patients_treated','east_departure_confirmed','chapter2_complete','carlo_promise_completed','R05_promise_seen','seen_R05','D31_done','D32_done','D33_done','seen_R01','seen_R02','seen_R03','seen_R04','seen_R06','seen_R07','seen_R08','S41_register_saved','obs_steps_ready','west_tower_safe','island_loop_safe','D42_done','chapter4_promoted_eileen','chapter4_promoted_hunapu','noya_brother_survived','celine_ready','chapter5_merged','final_access']
profiles=[('首次／常规条件',{}),('相关事项完成后再谈',{'flags':{k:True for k in milestones}}),('相关同伴濒死时',{'care':True}),('支线／前置事项尚未完成',{'uncleared':[101,103,111,112,204,211,212,301,304,311,312,402,408,411,412,511]})]
recruits={'fula':'fula','lena':'lena','beck':'beck','hervi':'hervi','lord':'lord','roan':'roan','shia':'shia','third_german':'german','third_noya':'noya','fourth_celine':'celine'}
specs=[]
for room,(ch,route,stage,actions) in rooms.items():
 for action in actions:
  for label,patch in profiles:
   item={'room':room,'chapter':max(1,ch),'route':route,'stage':stage,'action':action,'label':label,**patch}
   if action in recruits and not item.get('care'):item['remove']=[recruits[action]]
   if room=='H55':item['front']=True
   if action=='camp':item.update(object_name='投降兵' if room=='H05' else '村中老妇',object_text='塔工还在内院。将军要带粮走，没有给他们留车。' if room=='H05' else '凯尔把军粮分给了我们。科兰却说他通敌，把他杀了……我们想替他说句话，可谁也不敢去。')
   if action=='guard':item.update(object_name='教团守卫',object_text='这里刚恢复日光。请沿着广场走到传光台。')
   specs.append(item)
  if action in recruits:
   specs.append({'room':room,'chapter':max(1,ch),'route':route,'stage':stage,'action':action,'label':'已入队后再谈'})
   target=recruits[action];specs.append({'room':room,'chapter':max(1,ch),'route':route,'stage':stage,'action':action,'label':'未入队人物遇难／不可邀请','dead':[target],'flags':{'chapter3_recruits':{'german':False,'noya':False},'celine_ready':False}})
def add(room,action,label,**patch):
 ch,route,stage,_=rooms[room];specs.append({'room':room,'chapter':max(1,ch),'route':route,'stage':stage,'action':action,'label':label,**patch})
add('H01','grave','已谈墓前、尚未击败科兰',flags={'village_ready':True})
add('H01','grave','林路仍未完成时再看墓碑',flags={'village_ready':True},uncleared=[101])
add('H02','fula','分粮后、押送所未完成',flags={'grain_shared':True},uncleared=[103],remove=['fula'])
add('H09','hervi','医疗交接完成、尚未入队',flags={'clinic_staffed':True},remove=['hervi'])
add('H08','mine_survivor','贝克未能获救',dead=['beck'])
add('H25','r05','完成海洞承诺后首次谈话',flags={'carlo_promise_completed':True})
add('H25','r05','卡洛濒死、希雅在队',dead=['carlo'])
add('H31','third_reunion','米蕾濒死，其他同伴正常',care=True)
add('H10','third_council','另一队未到会合营站',not_arrived=True)
add('H10','third_relations','会谈后首次关系谈话',flags={'D33_done':True})
add('H10','third_relations','会谈后没有可进行的新关系事件',flags={'D33_done':True},care=True)
add('H43','fourth_tower_shutdown','已收到观测步骤，首次安全停塔',flags={'obs_steps_ready':True})
add('H48','fourth_d42','西塔及局部隔离均完成，首次两岸确认',flags={'west_tower_safe':True,'island_loop_safe':True})
add('H48','fourth_d42','首次确认，莉莎／米蕾濒死',flags={'west_tower_safe':True,'island_loop_safe':True},care=True)
add('H50','fourth_celine','病人已安置、赛琳可邀请',flags={'celine_ready':True},remove=['celine'])
add('H42','fourth_letters','米蕾在照护处，达恩正常',flags={'seen_R02':False},remove=[])
specs[-1]['injured']=['mireille']
add('H42','fourth_letters','蕾娜濒死、兰斯正常',flags={'seen_R02':True},injured=['lena'])
add('H42','fourth_letters','兰斯濒死、蕾娜正常',flags={'seen_R02':True},injured=['lance'])
add('H55','fifth_relationship','R01、R02完成，合军前首次约定',flags={'seen_R01':True,'seen_R02':True},front=True)
add('H21','east_departure','出航已确认、卡洛濒死',flags={'east_departure_ready':True},injured=['carlo'])
add('H24','invite_s22','海洞未完成、卡洛不能现场行动',uncleared=[212],injured=['carlo'])
add('H25','islanders_settle','岛民未能全部获救',flags={'islanders_survived':False})
add('H25','r05','卡洛正常、希雅不在队',remove=['shia'])
add('H34','third_route_e','向导存活并交出路线',flags={'salt_guide_survived':True})
add('H48','fourth_spring','三次力量泉已用完',flags={'fourth_strength_uses':3})
add('H42','fourth_letters','米蕾未入队时送布',remove=['mireille'])
add('H54','fifth_east_report','镇关枪已交付后再谈',flags={'story_armaments_claimed':{'7':True}})
add('H55','fifth_merge','已合流、前庭战尚未完成',flags={'chapter5_merged':True,'final_access':False},front=True)
add('H55','fifth_merge','另一队尚未到前庭',not_arrived=True)
add('H55','fifth_relationship','约定完成后，相关人物在照护处',flags={'seen_R03':True},care=True,front=True)
add('H36','third_families','只有一组家庭获救',flags={'S31_families':{'family0':True,'family1':False}})
for room,action,item,facts in [('H49','fourth_ring_keeper','55',['boss_defeated','register_protected','register_intact','refuge_confirmed']),('H51','fifth_shield_keeper','53',['boss_defeated','ward_1_open','ward_2_open','wounded_0_alive','wounded_1_alive','wounded_0_evacuated','wounded_1_evacuated'])]:
 add(room,action,'当场救援记录齐全，首次交付',flags={'story_accessory_results':{item:{f:True for f in facts}}})
 add(room,action,'已经领取后再谈',flags={'story_accessories_claimed':{item:True}})
for action in ['third_council','third_messenger','third_relations']:
 add('H10',action,'第四章回营站，前置未齐');specs[-1]['chapter']=4
 add('H10',action,'第四章两岸完成后回营站',flags={k:True for k in milestones});specs[-1]['chapter']=4
add('H55','treatment','有剩余份额且同伴濒死',flags={'D33_done':True,'cooperation_done':True,'islanders_settled':True},care=True,front=True)
# Accessory and armament delivery are captured from their actual helper methods separately.
(O/'hub-specs.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2)+'\n')
(O/'room-order.json').write_text(json.dumps({k:{'chapter':c,'route':r,'stage':s,'actions':a} for k,(c,r,s,a) in rooms.items()},ensure_ascii=False,indent=2)+'\n')
print('hub scenarios',len(specs),'rooms',len(rooms))
