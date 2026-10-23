extends RefCounted
## Final campaign chapter. Joint deployment never changes original party ownership.
const STAGES=[501,502,503,504,511,533,534]
const ROOMS=["H51","H52","H53","H54","H55","H56"]
const Prior=preload("res://core/chapter3_rules.gd")
static func begin(g) -> bool:
 if g.chapter!=4 or not g.flags.get("chapter4_closed",false) or not g.flags.get("D42_done",false) or not g.stage_cleared(404) or not g.stage_cleared(408):return false
 g.parties[g.route]=g.party.duplicate();g.chapter=5;g.route="alm";g.party=g.parties.alm.duplicate()
 g.world_node=13;g.previous_world_node=13;g.route_positions={"alm":13,"celica":29};g.flags.chapter5_previous={"alm":13,"celica":29}
 g.flags.chapter5_started=true;g.flags.chapter5_pending=false;g.flags.chapter5_deployment={};g.flags.chapter5_ready={"alm":false,"celica":false};g.flags.erase("active_plot")
 Prior._reset(g,501);g.mode="world";g.hub_record="H51";return true
static func can_switch(g) -> bool:return g.chapter==5 and g.mode in ["world","hub"] and not g.flags.has("active_plot") and not g.flags.get("campaign_complete",false)
static func switch_route(g) -> bool:
 if not can_switch(g):return false
 g.parties[g.route]=g.party.duplicate();g.route_positions[g.route]=g.world_node;g.flags.chapter5_previous[g.route]=g.previous_world_node
 g.route="celica" if g.route=="alm" else "alm";g.party=g.parties[g.route].duplicate();g.world_node=int(g.route_positions[g.route]);g.previous_world_node=int(g.flags.chapter5_previous[g.route])
 Prior._reset(g,maxi(stage_for_node(g,g.world_node),501 if g.route=="alm" else 503));g.mode="world";g.hub_record=room_for(g);g.flags.world_previous=g.previous_world_node;return true
static func stage_for_node(g,node:int) -> int:
 if g.flags.get("chapter5_merged",false):return int({15:533,16:534}.get(node,0))
 return int(({13:501,14:502} if g.route=="alm" else {29:503,30:504,39:511}).get(node,0))
static func allowed_nodes(g) -> Array[int]:
 if g.flags.get("campaign_complete",false):return [16]
 if g.flags.get("chapter5_merged",false):
  var merged:Array[int]=[15]
  if g.flags.get("final_access",false):merged.append(16)
  return merged
 var result:Array[int]=[];result.append(13 if g.route=="alm" else 29)
 if g.route=="alm":
  if g.flags.get("M51_confirmed",false):result.append(14)
  if g.flags.get("west_palace_gate",false):result.append(15)
 else:
  if g.flags.get("east_network_ready",false):result.append(30)
  if g.flags.get("east_palace_gate",false):result.append(15)
  if g.flags.get("S51_invited",false):result.append(39)
 return result
static func room_for(g) -> String:return str({13:"H51",14:"H52",29:"H53",30:"H54",39:"H56",15:"H55",16:"H55"}.get(g.world_node,"H55"))
static func selection(g,side:String) -> Array:
 if not g.flags.chapter5_deployment.has(side):g.flags.chapter5_deployment[side]=g.parties[side].filter(func(id):return g.can_deploy(g.roster[id])).slice(0,10)
 return g.flags.chapter5_deployment[side]
static func merge(g) -> bool:
 if not g.flags.get("west_palace_gate",false) or not g.flags.get("east_palace_gate",false):return false
 if int(g.route_positions.alm)!=15 or int(g.route_positions.celica)!=15:return false
 for side in ["alm","celica"]:
  var chosen=selection(g,side);var hero="hunapu" if side=="alm" else "eileen"
  if not g.flags.chapter5_ready[side] or not chosen.has(hero) or chosen.is_empty() or chosen.size()>10:return false
  if not chosen.all(func(id):return g.parties[side].has(id) and g.can_deploy(g.roster[id])):return false
 g.flags.chapter5_merged=true;g.flags.S51_closed=not g.stage_cleared(511);g.route_positions={"alm":15,"celica":15};g.flags.chapter5_previous={"alm":15,"celica":15};g.previous_world_node=15
 Prior._reset(g,533);g.hub_record="H55";g.mode="hub";return true
static func can_start(g,id:int) -> bool:
 if not allowed_nodes(g).has(g.world_node) or stage_for_node(g,g.world_node)!=id:return false
 if id in [533,534]:
  for side in ["alm","celica"]:
   if not selection(g,side).has("hunapu" if side=="alm" else "eileen"):return false
  return g.can_deploy(g.roster.hunapu) and g.can_deploy(g.roster.eileen)
 return str(g.stages.get(id,{}).get("route",""))==g.route
static func lines(g,text:String,key:String="") -> void:Prior.lines(g,text,key)
static func done(g,id:String) -> bool:return Prior.done(g,id)
static func initialize(g) -> void:
 g.flags.quest.repair_since={"repair_1":-1,"repair_2":-1};g.flags.quest.final_phase=false;g.flags.quest.summon_wave=false
static func before_lines(g) -> void:
 var text={501:"赫兰：城门后还有伤兵。神军不肯让他们离开。／胡纳普：你让他们守在那里，现在得把他们带出来。／赫兰：我会去。你把南边那条路留下来。／蕾娜或投降军官：赫兰已打开南侧后撤门。我们会留下照护并记录责任；去两间病房的南门接应伤者。",502:"胡纳普：桥还连着。先从西段解除桥锁，再向东推进。／斥候：桥外不能步行；飞行者能绕过侧翼，但门阵仍要有人确认。",503:"艾琳：两处装置都要交到地方工班手里。／技术员：未开始的工班在防护区内。到装置南面交接后，保护到下一己方回合。接通以后，我们会接手当地循环。",504:"艾琳：西阵和东阵都在装置南面。核对以后再开门，不把群岛居民系在神座上。",511:"记录官：早年的救援和失败试验都在旧书库。把原件带到南门，不要只抄对我们有利的部分。",533:"胡纳普：西侧入口通往左庭。／艾琳：东侧也是。两翼门阵都确认后，沿中轴去神座。伤者留在整备处，两边的人一起接应。",534:"乌库布·卡基：我把你从裂缝里拉出来时，你一直抓着我的手。／胡纳普：我记得。凯尔也记得。／乌库布·卡基：你们本来都能留在我保护的地方。／艾琳：我们在那里也失去了家人。现在还有人等在岸边。／乌库布·卡基：回去。我会重新安排。／战场提示：普通武器与法术始终有效。实体半血后只增援一次，不会回复满血。"}.get(g.stage_id,"")
 lines(g,text,str(g.battle_data.code)+"-BEGIN")
 if g.stage_id==502:lines(g,"守卫：桥卫军械库还锁在通道后面。先解除桥锁，通路安全后再清点兵器。","M52-ARMAMENT-HINT")
 if g.stage_id==511:lines(g,"记录官：旁边的封存箱里还有镇关枪。把旧事记录带到南门完成交接，再让这把护送旧枪回到路上。","S51-ARMAMENT-HINT")
static func interact(g,id:String) -> void:
 if id.begins_with("bridge_"):
  var i=int(id.substr(7))
  if i>1 and not done(g,"bridge_"+str(i-1)):lines(g,"守桥工：从西向东，先解除前一段桥锁。","M52-ORDER");return
 if id=="archive_exit" and (not done(g,"old_record") or not Prior.boss_down(g)):
  lines(g,"记录官：先取回书库记录并击败守卫，再到南门交接。","S51-ORDER");return
 g.flags.quest.objects[id]=true
 if id.begins_with("ward_"):
  var u=g.find_unit("royal_wounded"+str(int(id.substr(5))-1));u.locked=false
  lines(g,"伤兵：门开了。我们沿医舍前的路去南口，遇敌会先等候。",id+"-OPEN")
 elif id.begins_with("repair_"):
  g.flags.quest.repair_since[id]=g.turn;g.find_unit("repair_team"+str(int(id.substr(7))-1)).locked=false
  lines(g,"工班：开始交接。请保护到下一己方回合，之后就由地方人员接手。",id+"-WORK")
 elif id=="old_record":lines(g,"记录官：他确实从裂缝中救过人，也试过让各地自我调节。早年的失败令他转向集中控制。／艾琳：这些救援是真的。后来被拒绝的船和被强迁的人，也是真的。","S51-TRUTH")
static func after_phase(g) -> void:
 if g.phase!="player" or g.stage_id!=503:return
 for i in range(2):
  var key="repair_"+str(i+1);var u=g.find_unit("repair_team"+str(i))
  if done(g,key) and g.turn>int(g.flags.quest.repair_since[key]) and int(u.hp)>0:
   u.locked=true;lines(g,"工班：这处循环已接通，地方人员接手。你们可以继续前进。",key+"-COMPLETE")
static func check_outcome(g) -> String:
 if not g.battle_outcome.is_empty():return g.battle_outcome
 for id in ["hunapu","eileen"]:
  var u=g.find_unit(id)
  if not u.is_empty() and int(u.hp)<=0:return g._fail(str(u.name_zh)+"濒死，无法继续作战")
 var ready=true;var q:Dictionary=g.flags.quest
 for o in g.battle_data.objects:
  if not o.get("optional",false) and not done(g,o.id):ready=false
 if g.stage_id==501:
  if not Prior.alive(g,"royal_wounded0") and not Prior.alive(g,"royal_wounded1"):return g._fail("两组王都伤兵均未能获救")
  ready=ready and q.evacuated.size()>=1
 if g.stage_id==503:
  for i in range(2):
   if not Prior.alive(g,"repair_team"+str(i)):return g._fail("修复区失守，工班未能完成交接")
   if not done(g,"repair_"+str(i+1)) or g.turn<=int(q.repair_since["repair_"+str(i+1)]):ready=false
 if g.stage_id==534:
  var boss=g.find_unit(g.battle_data.boss_id)
  if int(boss.hp)>0 and int(boss.hp)*2<=int(boss.max_hp) and not q.final_phase:
   q.final_phase=true;boss.strength=int(boss.strength)+3;q.summon_wave=true
   for i in range(3):
    if g.living("enemy").size()>=20:break
    var u=g.battle_data.summon_template.duplicate(true);u.id="J54_summon"+str(i)
    var p=g.ChapterTwo.free_spawn(g,u,Vector2i(16,10));if p==Vector2i(-1,-1):break
    u.position=[p.x,p.y];u.enemy_slot=g.units.filter(func(z):return z.side=="enemy").size();g.units.append(u)
   lines(g,"乌库布·卡基：你们还没有走到岸边。／战场提示：实体强化，三名援军抵达。此次仅一波，仍可用普通武器和法术攻击。","J54-PHASE")
 if ready and Prior.boss_down(g):g.battle_outcome="victory"
 return g.battle_outcome
static func on_victory(g) -> void:
 g.flags["clear_"+str(g.battle_data.code)]=true
 match g.stage_id:
  501:
   g.flags.M51_survivors={}
   for i in range(2):g.flags.M51_survivors["royal_wounded"+str(i)]=Prior.alive(g,"royal_wounded"+str(i))
  502:g.flags.west_palace_gate=true
  503:g.flags.east_network_ready=true
  504:g.flags.east_palace_gate=true;g.flags.S51_invited=true
  511:g.flags.S51_records_saved=true
  533:g.flags.final_access=true
  534:g.flags.campaign_complete=true;g.flags.chapter5_complete=true
 var ending={501:"赫兰：撤下来的伤兵已交给照护处。我留下来，把此前的命令逐条交代。／胡纳普：先去照护处确认交接，再去登天桥。",502:"信使：西门已打开。东门未开时可在这里等候，按S切换东队。两队分别抵达前庭，才能确认合流。",503:"技术员：两处地方循环已经接上。居民不再依赖神座持续调度，我们会留在此处照看。",504:"记录官：东门已打开，南侧支路通向旧书库。合流出发后就不能折返；可以先查旧事，也可以直接前往前庭。",511:"记录官：早年的救援、失败的试验与后来的强迁命令，已一同收入档案。没有被删改的部分。",533:"艾琳：两翼已经接通。先回前庭整备，看看伤者和装备，再沿中轴去神座。／胡纳普：两个人一起去。",534:"旁白：乌库布·卡基的实体倒下了。远处仍有晨光。／艾琳：岸边的循环还在运转。日光没有随着他消失。／胡纳普：去接等在那里的船。"}
 lines(g,ending[g.stage_id],str(g.battle_data.code)+"-END")
static func status(g) -> Array[String]:
 var result:Array[String]=[str(g.battle_data.goal)]
 for o in g.battle_data.objects:result.append(str(o.label)+("：已确认" if done(g,o.id) else "：未确认"))
 if g.stage_id==501:result.append("已撤离%d组；至少一组，两处病房都须开门。"%g.flags.quest.evacuated.size())
 if g.stage_id==503:result.append("交接后的每个工班分别保护到下一己方回合；未交接和已完成的工班由防护区接应。")
 if g.stage_id==534:result.append("普通武器与法术始终有效；半血仅一波增援，无回满血、复活或专属武器门槛。")
 return result
