extends RefCounted
## Fourth chapter: independent routes, reversible waiting points, explicit objective state.
const STAGES=[401,402,403,404,405,406,407,408,411,412]
const ROOMS=["H10","H41","H42","H43","H44","H45","H46","H47","H48","H49","H50"]
const Prior=preload("res://core/chapter3_rules.gd")
static func begin(g) -> bool:
 if g.chapter!=3 or not g.flags.get("chapter3_complete",false) or not g.flags.get("D33_done",false):return false
 g.parties[g.route]=g.party.duplicate();g.chapter=4;g.route="alm";g.party=g.parties.alm.duplicate()
 g.world_node=9;g.previous_world_node=9;g.route_positions={"alm":9,"celica":9};g.flags.chapter4_previous={"alm":9,"celica":9}
 g.flags.chapter4_started=true;g.flags.chapter4_pending=false;g.flags.erase("active_plot")
 Prior._reset(g,401);g.mode="world";g.hub_record="H10"
 return true
static func can_switch(g) -> bool:return g.chapter==4 and g.mode in ["world","hub","chapter_end"] and not g.flags.has("active_plot")
static func switch_route(g) -> bool:
 if not can_switch(g):return false
 g.parties[g.route]=g.party.duplicate();g.route_positions[g.route]=g.world_node;g.flags.chapter4_previous[g.route]=g.previous_world_node
 g.route="celica" if g.route=="alm" else "alm";g.party=g.parties[g.route].duplicate();g.world_node=int(g.route_positions[g.route]);g.previous_world_node=int(g.flags.chapter4_previous[g.route])
 Prior._reset(g,maxi(stage_for_node(g,g.world_node),401 if g.route=="alm" else 405));g.mode="world";g.hub_record=room_for(g);g.flags.world_previous=g.previous_world_node
 return true
static func stage_for_node(g,node:int) -> int:return int(({10:401,11:402,12:403,13:404,37:411} if g.route=="alm" else {26:405,27:406,28:407,29:408,38:412}).get(node,0))
static func allowed_nodes(g) -> Array[int]:
 var result:Array[int]=[9]
 if g.route=="alm":
  result.append(10)
  if g.flags.get("M41_confirmed",false):result.append(11)
  if g.flags.get("S41_invited",false):result.append(37)
  if g.stage_cleared(402):result.append(12)
  if g.flags.get("west_tower_safe",false):result.append(13)
 else:
  result.append(26)
  if g.flags.get("F41_confirmed",false):result.append(27)
  if g.flags.get("obs_steps_ready",false):result.append(28)
  if g.flags.get("F43_confirmed",false):result.append(29)
  if g.flags.get("S42_invited",false):result.append(38)
 return result
static func room_for(g) -> String:return str({9:"H10",10:"H41",11:"H42",12:"H43",13:"H44",26:"H45",27:"H46",28:"H47",29:"H48",37:"H49",38:"H50"}.get(g.world_node,"H10"))
static func lines(g,text:String,key:String="") -> void:Prior.lines(g,text,key)
static func done(g,id:String) -> bool:return Prior.done(g,id)
static func alive(g,id:String) -> bool:return Prior.alive(g,id)
static func boss_down(g) -> bool:return Prior.boss_down(g)
static func initialize(g) -> void:
 var q:Dictionary=g.flags.quest
 q.wells={"well_n":true,"well_s":true};q.well_since={"well_n":-1,"well_s":-1};q.record_lost=false;q.burn_count=0;q.summon_wave=false;q.repair_since=-1;q.old_comrades_talked=false
 q.transfer_cut_snapshot=bool(g.flags.get("transfer_cut",false))
 if g.stage_id==408 and q.transfer_cut_snapshot:g.battle_data.reinforcements=[];g.battle_data.reinforcement_turn=0
static func before_lines(g) -> void:
 if g.stage_id==404:g.queue_pages(g.campaign.scenes.D41,"D41")
 var text={401:"奥托或居民：北村的人沿村道向南撤。先疏通南口，再去接山道上的伤者。／胡纳普：我们挡住封路的人，至少带回两组居民。",402:"胡纳普：投送站还在往群岛运兵。先截断这里，再进北境。",403:"胡纳普：先夺控制室，谁都别拆塔。／芙拉或工匠：下面还有病人。控制室缺的步骤在东岸观测台；可以先守住这里，再等来信。",404:"蕾娜或投降军官：留下医舍旁的后撤门，让伤兵退到安全处。",405:"莉莎或艾琳：他们要把井封上。南北井台都留人接应，先让居民把水取够。／战场提示：守至第6己方回合并击败队长。敌军连续占井整轮才失守，可夺回；两井同时失守则失败。",406:"艾琳：记录在东楼，别让拿火把的人进去。先保护记录，再到中央设备南面复制。／地方技术员：焚毁兵第6回合才出发，会先警告。两次连续点火才烧毁，我们还有时间。",407:"米蕾或船团医者：有几个人走不快。把三处干地依次确认，再分组送往东北古道口。／卡洛或舵手：船留在南侧接应；不要把居民赶进毒沼。",408:"艾琳：三个调节点都要交给工匠，正式队员可以继续向前。先做局部隔离试验，再等两岸确认。",411:"奥托或村民：名字都在村中那间屋里。他们说要把村里腾空。／胡纳普：先护住名册屋。屋在村道东侧，门朝南。",412:"赛琳：我不能把病人留在这里。你们有能靠岸的船吗？／艾琳：船在西南，先守住诊疗处，让两组病人依次上船。／战场提示：北端飞行敌第3回合开始压近。先接住病人，不要直接冲向北面的队长。"}.get(g.stage_id,"")
 lines(g,text,str(g.battle_data.code)+"-BEGIN")
 if g.stage_id==402 and g.speaker_alive("兰斯"):lines(g,"兰斯：营地西侧有人曾与我共事。让我到他旁边谈谈。／胡纳普：可以，但别一个人走进弓手面前。","M42-LANCE")
 if g.stage_id==408:lines(g,"信使：西队已切断投送站，本次不会有投送援军。" if g.flags.quest.transfer_cut_snapshot else "信使：投送站仍在运行，第5回合东侧平台会有两名援军。这次战斗按当前军情应对。","F44-SNAPSHOT")
static func ai_action(g,u:Dictionary) -> Dictionary:
 if u.has("advance_after") and g.turn<int(u.advance_after):
  var guard=u.duplicate(true);guard.behavior="guard_exit";return g.CampaignTactics.action(g,guard)
 if u.get("quest_kind","")=="escort":
  var target=Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]);var action=g._safe_escort_move(u,target)
  var before=999;var after=999
  for e in g.living("enemy"):
   before=mini(before,Prior._distance(g.pos(e),g.pos(u)));after=mini(after,Prior._distance(g.pos(e),action.destination))
  # Retreat away from nearby pursuers; never freeze a safe southward evacuation.
  if before>4 or after>before:return action
  return {"destination":g.pos(u),"target":""}
 if u.get("ch4_burner",false):
  if done(g,"observatory_record") or done(g,"black_register") or g.flags.quest.record_lost:return {"destination":g.pos(u),"target":""}
  if g.turn<int(g.battle_data.burn_start):return {"destination":g.pos(u),"target":""}
  return g._toward(u,Vector2i(g.battle_data.burn_target[0],g.battle_data.burn_target[1]))
 if u.has("well_target"):
  for o in g.battle_data.objects:
   if o.id==u.well_target:
    var at=Vector2i(o.position[0],o.position[1]);var occupant=g.unit_at(at)
    if occupant.is_empty() or occupant.side=="enemy":return g._toward(u,at)
 if u.get("surrendered",false):return {"destination":g.pos(u),"target":""}
 return {}
static func extra_interactions(g,u:Dictionary) -> Array:
 if g.stage_id==402 and u.id=="lance" and not g.flags.quest.old_comrades_talked and alive(g,"old_comrade") and Prior._distance(g.pos(u),g.pos(g.find_unit("old_comrade")))==1:
  return [{"id":"lance_parley","kind":"parley","label":"与旧同袍交涉"}]
 return []
static func interact(g,id:String) -> void:
 if id=="lance_parley":
  g.flags.quest.old_comrades_talked=true
  for u in g.living("enemy"):
   if u.get("old_comrade_group",false):u.side="neutral";u.surrendered=true;u.no_counter=true
  lines(g,"兰斯：投送过去的军队会把船上的人赶回海里。交出武器，留下来作证。／旧同袍：我们这一队停手。统领还在北营，不肯接受。","M42-PARLEY");return
 if id=="observation_device" and not done(g,"observatory_record"):
  lines(g,"技术员：先到东楼门前保护记录，才能核对设备参数。","F42-ORDER");return
 if id.begins_with("dry_"):
  var index=int(id.substr(4))
  if index>1 and not done(g,"dry_"+str(index-1)):
   lines(g,"舵手：先确认前一处干地，后面的病人才能沿线跟上。","F43-ORDER");return
 g.flags.quest.objects[id]=true
 match id:
  "transfer_station":g.flags.transfer_cut=true;lines(g,"工匠：投送已停止。信件送往东岸，已抵达的敌军不会因此消失。","M42-CUT")
  "tower_control":lines(g,"工匠：控制室归我们了。战后到这里核对观测步骤，不能直接拆塔。","M43-CONTROL")
  "observatory_record":lines(g,"艾琳：完整记录保住了。去中央设备南面核对，再把副本交给固定信使。","F42-RECORD")
  "observation_device":
   lines(g,"技术员：断裂以前，各地的循环会互相调节。先隔离远端，再分段降流，最后核对村庄的光源。／艾琳：我曾以为西岸只要停塔就好。现在知道，下面还有靠它过冬的人。","F42-MYTH")
   if g.speaker_alive("诺娅"):lines(g,"诺娅：我曾把藏船的地方告诉他们。这次我会把完整记录交出来，也继续接受船团的追问。","F42-NOYA")
  "black_register":lines(g,"村民：这张军令上有凯尔的名字。他起初也执行迁徙命令，后来见到孩子被押走，才违令救人。／胡纳普：把前后都留下。他救过人，也确实参与过这些事。","S41-TRUTH")
  "clinic_note":lines(g,"医者：维娅当年急着证明航线，带准备不足的船队离港。后来她一趟趟接人，也没能把所有人带回来。／艾琳：把失去的人也记在航图旁。不能只留下成功的那一趟。","S42-TRUTH")
static func after_wait(g,u:Dictionary) -> void:
 var q:Dictionary=g.flags.quest
 if u.get("ch4_burner",false) and g.turn>=int(g.battle_data.burn_start) and not done(g,"observatory_record") and not done(g,"black_register"):
  q.burn_count=int(q.burn_count)+1 if u.position==g.battle_data.burn_target else 0
  if int(q.burn_count)==1:lines(g,"焚毁兵：下一轮就点火！／战场提示：截住门前的焚毁兵，或抢先保护记录。","CH4-FIRE-FIRST")
  if int(q.burn_count)>=2:q.record_lost=true
static func after_phase(g) -> void:
 var q:Dictionary=g.flags.quest
 if g.phase=="player" and g.battle_data.has("burn_start") and g.turn==int(g.battle_data.burn_start)-1:lines(g,"战场提示：焚毁兵下一回合出发，目标是记录室南门。需要连续两次点火才能焚毁。",str(g.battle_data.code)+"-FIRE-WARNING")
 if g.stage_id==405:
  for o in g.battle_data.objects:
   var u=g.unit_at(Vector2i(o.position[0],o.position[1]))
   if not u.is_empty() and u.side=="enemy":
    if g.phase=="player":
     if int(q.well_since[o.id])>=0:q.wells[o.id]=false
     else:q.well_since[o.id]=g.turn
   else:
    q.well_since[o.id]=-1
    if not u.is_empty() and u.side=="player":q.wells[o.id]=true
 if g.stage_id==407 and g.phase=="enemy" and g.turn>=3 and not q.summon_wave and alive(g,str(g.battle_data.boss_id)):
  q.summon_wave=true
  for i in range(3):
   if g.living("enemy").size()>=20:break
   var u=g.battle_data.summon_template.duplicate(true);u.id="F43_summon"+str(i)
   var p=g.ChapterTwo.free_spawn(g,u,Vector2i(26,6));if p==Vector2i(-1,-1):break
   u.position=[p.x,p.y];u.enemy_slot=g.units.filter(func(z):return z.side=="enemy").size();g.units.append(u)
  lines(g,"神官：让亡潮守住古道。／战场提示：这些召唤物与神官相连；天然魔物不会随他退去。","F43-SUMMON")
static func check_outcome(g) -> String:
 if g.battle_outcome=="defeat":return g.battle_outcome
 for id in ["hunapu","eileen"]:
  var u=g.find_unit(id)
  if not u.is_empty() and int(u.hp)<=0:return g._fail(str(u.name_zh)+"濒死，无法继续作战")
 var q:Dictionary=g.flags.quest;var ready=false
 if g.stage_id==404:
  var herlan=g.find_unit(str(g.battle_data.boss_id))
  if int(herlan.hp)*2<=int(herlan.max_hp) and not q.mid_done:
   q.mid_done=true;lines(g,"赫兰：伤兵先退到医舍！后撤门留开。／胡纳普：愿意放下武器的人，不要再攻击。","M44-MID")
  if int(herlan.hp)<=0 and not herlan.get("surrendered",false):
   herlan.hp=1;herlan.dead=false;herlan.side="neutral";herlan.surrendered=true;herlan.no_counter=true
   for e in g.living("enemy"):e.side="neutral";e.surrendered=true;e.no_counter=true
   g.battle_data.reinforcements=[];q.reinforced=true
   lines(g,"赫兰：我交出指挥权。／胡纳普：先照看你带来的伤兵。投降不等于此前的责任就过去了。","M44-SURRENDER")
 if g.stage_id in [401,407,412]:
  var prefix="snow_group" if g.stage_id==401 else "marsh_group" if g.stage_id==407 else "island_group"
  var total=2 if g.stage_id==412 else 3;var living_count=0;var evacuated=0
  for i in range(total):
   var id=prefix+str(i)
   if alive(g,id):living_count+=1
   if q.evacuated.has(id):evacuated+=1
  if living_count<2:return g._fail("能够获救的居民不足两组")
  ready=evacuated>=2
  if g.stage_id==401:ready=ready and done(g,"south_gate") and done(g,"rest_station")
  if g.stage_id==407:ready=ready and done(g,"dry_1") and done(g,"dry_2") and done(g,"dry_3")
  if g.stage_id==412:ready=ready and done(g,"landing")
 match g.stage_id:
  402:ready=done(g,"transfer_station")
  403:ready=done(g,"outer_court") and done(g,"tower_control")
  404:ready=done(g,"gatehouse")
  405:
   if not q.wells.well_n and not q.wells.well_s:return g._fail("两处水井均已失守")
   ready=g.turn>=6
  406:
   if q.record_lost:return g._fail("观测记录已焚毁，无法安全停塔")
   ready=done(g,"observatory_record") and done(g,"observation_device")
  408:
   if not alive(g,"repairer0") and not alive(g,"repairer1"):return g._fail("修复人员全部遇难")
   ready=done(g,"regulator_1") and done(g,"regulator_2") and done(g,"regulator_3")
   if ready and int(q.repair_since)<0:q.repair_since=g.turn;lines(g,"工匠：三个调节点已接通。再保护到下一己方回合，完成局部隔离试验。","F44-TEST")
   ready=ready and g.turn>int(q.repair_since)
  411:ready=q.record_lost or done(g,"black_register")
 if g.stage_id==407 and boss_down(g):
  for u in g.units:
   if u.get("summoner_id","")==g.battle_data.boss_id:u.side="evacuated";u.hidden=true
 if ready and boss_down(g):g.battle_outcome="victory"
 return g.battle_outcome
static func on_victory(g) -> void:
 g.flags["clear_"+str(g.battle_data.code)]=true
 var survivors={}
 for u in g.units:
  if u.get("neutral",false):survivors[u.id]=int(u.hp)>0
 g.flags["survivors_"+str(g.battle_data.code)]=survivors
 match g.stage_id:
  403:g.flags.m43_seized=true
  406:g.flags.obs_steps_ready=true
  408:g.flags.island_loop_safe=true
  411:g.flags.S41_register_saved=done(g,"black_register") and not g.flags.quest.record_lost
  412:g.flags.celine_ready=alive(g,"celine");g.flags.S42_settled=true
 var ending={401:"居民：活着的组别和伤亡分别登记。先到南口安置处确认，再沿山道去铁骑关。",402:"信使：投送站停止的消息已发往东岸。若祭所战斗已经结束，这封信会保护后面的船队。",403:"工匠：日塔已由我们驻守。请到控制室核对东岸的观测步骤；没收到信也不用重新作战。",404:"胡纳普：赫兰已失去指挥权。把伤兵交给照护处，我们回营站核对两岸结果。",405:"居民：水已经取够，古道路线就在井台。我们会留下多份路线册。",406:"信使：完整的停用步骤已送往北境日塔；祭所坐标也记下了。西队在控制室就能接续，不必重打。",407:"船团医者：获救居民已逐组交接。古道通向祭所，船口还收到孤岛的求援。",408:"技术员：局部隔离试验成功。再到调节庭核对西塔停用后的灯光，不能把局部成功当成两岸验证。",411:"村民：完整名册保住了，军令的前后都记下了。" if g.flags.get("S41_register_saved",false) else "村民：名册被烧掉了。我们仍会留下在场者的证言，但不把失去的记录补回来。",412:"医者：两组病人已上船，地方医者会接手。到诊疗处与赛琳交谈，再决定是否同行。"}
 lines(g,ending[g.stage_id],str(g.battle_data.code)+"-END")
static func status(g) -> Array[String]:
 var q:Dictionary=g.flags.quest;var result:Array[String]=[str(g.battle_data.goal)]
 if g.stage_id in [401,407,412]:result.append("已撤离%d组；至少2组。居民遇敌等待，请清出连续通路；组别生死分别保存。"%q.evacuated.size())
 if g.stage_id==405:
  result.append("北井："+("控制中" if q.wells.well_n else "失守")+"；南井："+("控制中" if q.wells.well_s else "失守")+"。至少保住一井，守至第6己方回合且击败队长。")
 if g.stage_id in [406,411]:result.append("记录已毁。" if q.record_lost else "记录已保护。" if done(g,"observatory_record") or done(g,"black_register") else "焚毁兵连续两次在门前点火才毁记录。第%d回合开始，提前一回合预告。"%int(g.battle_data.burn_start))
 if g.stage_id==403:result.append("先完成夺塔即可返回控制室。安全停塔需要东队在盐原观测台取得步骤，不必重战。")
 if g.stage_id==408:result.append(("投送援军已取消。" if q.transfer_cut_snapshot else "第5回合东侧平台来援军2名；当前战斗军情已固定。")+"三点交接后保护至下一己方回合，且至少一名工匠存活。")
 for o in g.battle_data.objects:
  if g.stage_id!=405 and not o.get("optional",false):result.append(str(o.label)+("：已完成" if done(g,str(o.id)) else "：未完成"))
 return result
static func missing(g) -> Array[String]:
 var result:Array[String]=[]
 if not g.flags.get("west_tower_safe",false):result.append("西队：北境日塔控制室，确认安全停用" if g.flags.get("obs_steps_ready",false) else "东队：盐原观测台，取得停用步骤；西队再到日塔控制室确认")
 if not g.stage_cleared(404):result.append("西队：王都城门，击败赫兰并占领门楼")
 if not g.flags.get("island_loop_safe",false):result.append("东队：沉没祭所，完成三点隔离试验")
 if not g.flags.get("D42_done",false):result.append("东队：沉没祭所调节庭，两岸确认信")
 return result
static func promote_hero(g,id:String) -> void:
 var key="chapter4_promoted_"+id
 if g.flags.get(key,false):return
 var u:Dictionary=g.roster[id]
 if g.is_dying(u):return
 # Narrative advancement uses established weapon/spell permissions, preserves all training and HP.
 if id=="hunapu":
  var result=g.Progression.promote(u,23,true)
  if result.valid:
   var next:Dictionary=result.unit;next.level=u.level;next.exp=u.exp;next.hp=u.hp;g.roster[id]=next
 else:g.roster[id].promoted=true;g.flags.eileen_local_cycle_understood=true
 g.flags[key]=true
