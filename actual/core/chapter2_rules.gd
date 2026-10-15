extends RefCounted
## Chapter-two objectives use explicit event state, never fabricated formal units.
static func allowed_nodes(g) -> Array[int]:
	if g.flags.get("chapter2_complete",false):return [6]
	var nodes: Array[int]=[17]
	if g.flags.get("east_departure_ready",false):nodes.append(18)
	if g.stage_cleared(201) and g.flags.get("F21_confirmed",false):
		nodes.append(19)
		if g.flags.get("S21_invited",false) and (not g.flags.get("east_departure_confirmed",false) or g.stage_cleared(211)):nodes.append(33)
	if g.stage_cleared(202) and g.flags.get("F22_confirmed",false):nodes.append(20)
	if g.stage_cleared(203) and g.flags.get("F23_confirmed",false):
		nodes.append(21)
		if g.flags.get("S22_invited",false) and (not g.flags.get("east_departure_confirmed",false) or g.stage_cleared(212)):nodes.append(34)
	if g.stage_cleared(204) and g.flags.get("islanders_settled",false):nodes.append(22)
	if g.stage_cleared(205) and g.flags.get("sea_chart_collected",false) and g.flags.get("east_departure_confirmed",false):nodes.append(23)
	return nodes

static func initialize(g) -> void:
	if g.stage_id<200:return
	g.flags.quest.beacon_since=-1;g.flags.quest.beacon_contested=false
	g.flags.quest.boats=[]
	for raw in g.battle_data.get("event_boats",[]):
		var boat: Dictionary=raw.duplicate(true)
		boat.path_index=0;boat.arrived=false;boat.stopped=false;boat.position=boat.path[0].duplicate()
		g.flags.quest.boats.append(boat)

static func free_spawn(g,u: Dictionary,at: Vector2i) -> Vector2i:
	var seen={at:true};var queue: Array[Vector2i]=[at]
	while not queue.is_empty():
		var p=queue.pop_front()
		if g.in_bounds(p) and g.unit_at(p).is_empty() and g.movement_cost(u,p)<255:return p
		for d in g.DIRECTIONS:
			var n=p+d
			if g.in_bounds(n) and not seen.has(n):seen[n]=true;queue.append(n)
	return Vector2i(-1,-1)

static func ai_action(g,u: Dictionary) -> Dictionary:
	if bool(u.get("battle_guard",false)) and u.side=="player":
		# Volunteer guards protect their existing posts. Class, weapon, counter
		# and HP costs use ordinary combat; they never chase enemies off-island.
		var saved_move=int(u.move);u.move=0
		var choice=g.TacticalAI.action(g,u,false);u.move=saved_move
		return choice
	if u.get("objective_role","")=="seize_beacon" and u.side=="enemy" and g.stage_id==204:
		var beacon=Vector2i(g.battle_data.targets[0][0],g.battle_data.targets[0][1])
		var old_move=int(u.move)
		if g.pos(u)==beacon:u.move=0
		var choice=g.TacticalAI.action(g,u,false);u.move=old_move
		if not str(choice.get("target","")).is_empty() or g.pos(u)==beacon:return choice
		return g._toward(u,beacon)
	if not u.has("quest_kind"):return {}
	var kind=str(u.quest_kind)
	if bool(u.get("locked",false)) or kind in ["witness","ship","camp","islanders"]:
		return {"destination":g.pos(u),"target":""}
	if kind not in ["prisoner","patient","sailor"]:return {}
	var nearby=g.living("enemy").any(func(e):return _distance(g.pos(e),g.pos(u))<=maxi(4,g.Rules.attack_range(e).y+1))
	if nearby:return {"destination":g.pos(u),"target":""}
	var destination=Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]);var action=g._toward(u,destination);var safe=g.pos(u)
	for step in g.path_to(u,action.destination):
		if g.living("enemy").any(func(e):return _distance(g.pos(e),step)<=maxi(4,g.Rules.attack_range(e).y+1)):break
		safe=step
	action.destination=safe;return action

static func after_wait(g,u: Dictionary) -> void:
	if str(u.get("quest_kind","")) in ["prisoner","patient","sailor"] and not bool(u.get("locked",false)) and g.pos(u)==Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]):
		if not g.flags.quest.evacuated.has(str(u.id)):g.flags.quest.evacuated.append(str(u.id))
		u.side="evacuated";u.hidden=true
	if g.stage_id==203 and u.side=="player" and not u.get("neutral",false) and g.pos(u).y<=13:
		g.queue_lines(_mid_lines(g),"F23-MID")

static func open_object(g,o: Dictionary) -> void:
	if o.kind in ["door","rescue","bridge"]:
		var opens: Array=o.get("opens",[o.position] if o.kind in ["door","rescue"] else [])
		for cell in opens:
			var p=Vector2i(cell[0],cell[1])
			if g.in_bounds(p):g.battle_data.map.tiles[p.y*int(g.battle_data.map.width)+p.x]=int(o.get("open_tile",208))
	for id in o.get("unlock_units",[]):
		var u=g.find_unit(str(id))
		if not u.is_empty():u.locked=false

static func interact(g,id: String) -> void:
	for o in g.battle_data.objects:
		if str(o.id)!=id:continue
		g.flags.quest.objects[id]=true;open_object(g,o)
		if o.kind in ["door","rescue"]:g.queue_lines(_mid_lines(g),str(g.battle_data.code)+"-MID")
		if g.stage_id==205 and id=="myth_box":g.flags.quest.myth_box_secured=true
		if g.stage_id==204 and id=="shelter":g.flags.quest.shelter_open=true
		return

static func _distance(a: Vector2i,b: Vector2i) -> int:return absi(a.x-b.x)+absi(a.y-b.y)
static func _boats(g) -> Array:return g.flags.get("quest",{}).get("boats",[])
static func event_boats(g) -> Array:
	var result=[]
	for boat in _boats(g):
		result.append({"id":str(boat.id),"position":boat.position.duplicate(),"hp":int(boat.hp),"max_hp":int(boat.max_hp),"arrived":bool(boat.arrived),"stopped":bool(boat.stopped),"waiting":g.turn<=int(boat.get("delay",0))})
	return result

static func before_phase(g) -> void:
	if g.stage_id!=206:return
	for boat in _boats(g):
		if int(boat.hp)<=0 or bool(boat.arrived):continue
		boat.stopped=false
		if g.turn<=int(boat.get("delay",0)):continue
		if g.phase=="player":
			for _step in range(int(boat.get("speed",4))):
				var index=mini(int(boat.path_index)+1,boat.path.size()-1);var cell=Vector2i(boat.path[index][0],boat.path[index][1])
				if g.living("enemy").any(func(e):return _distance(g.pos(e),cell)<=maxi(3,g.Rules.attack_range(e).y+1)):
					boat.stopped=true;break
				boat.path_index=index;boat.position=boat.path[index].duplicate()
				if index>=boat.path.size()-1:boat.arrived=true;break
			if int(boat.path_index)>=boat.path.size()/2:g.queue_lines(_mid_lines(g),"F26-MID")
		else:
			var at=Vector2i(boat.position[0],boat.position[1]);var damage=0
			for enemy in g.living("enemy"):
				var reach=g.Rules.attack_range(enemy)
				var distance=_distance(g.pos(enemy),at)
				if distance>=maxi(1,reach.x) and distance<=reach.y:damage+=maxi(1,int(enemy.strength)/3)
			if damage>0:
				boat.hp=maxi(0,int(boat.hp)-damage)
				g.queue_lines("舵手：岸上的敌人正在射击居民船。请先清出沿岸的通路！","F26-BOAT-HIT")
	g.check_outcome()

static func _beacon_enemy(g) -> Dictionary:
	if g.stage_id!=204:return {}
	var target=g.battle_data.targets[0];var u=g.unit_at(Vector2i(target[0],target[1]))
	return u if not u.is_empty() and u.side=="enemy" and int(u.hp)>0 else {}

static func after_phase(g) -> void:
	if g.stage_id<200:return
	if g.stage_id==201 and g.phase=="enemy" and g.turn==3:g.queue_lines(_mid_lines(g),"F21-MID")
	if g.stage_id==204:
		var occupied=not _beacon_enemy(g).is_empty();g.flags.quest.beacon_contested=occupied
		if not occupied:g.flags.quest.beacon_since=-1
		elif g.phase=="player":
			if int(g.flags.quest.beacon_since)>=0 and g.turn>int(g.flags.quest.beacon_since):g._fail("航灯被敌军连续占据一整回合")
			else:
				g.flags.quest.beacon_since=g.turn
				g.queue_lines("留守骑士：敌人占住航灯了！下一回合前必须把他们赶走。","F24-BEACON-WARNING")
		if g.phase=="player" and g.turn==4:g.queue_lines(_mid_lines(g),"F24-MID")

static func _alive(g,id: String) -> bool:
	var u=g.find_unit(id);return not u.is_empty() and int(u.hp)>0
static func _units_of_kind(g,kind: String) -> Array:return g.units.filter(func(u):return str(u.get("quest_kind",""))==kind)
static func _all_dead(values: Array) -> bool:return not values.is_empty() and values.all(func(u):return int(u.hp)<=0)
static func _boss_defeated(g) -> bool:
	var boss=g.find_unit(str(g.battle_data.boss_id));return not boss.is_empty() and (int(boss.hp)<=0 or bool(boss.get("surrendered",false)))

static func check_outcome(g) -> String:
	if g.battle_outcome=="defeat":return g.battle_outcome
	for id in ["hunapu","eileen"]:
		var hero=g.find_unit(id)
		if not hero.is_empty() and int(hero.hp)<=0:return g._fail(str(hero.name_zh)+"阵亡")
	var q: Dictionary=g.flags.quest;var objects: Dictionary=q.objects;var evacuated: Array=q.evacuated;var ready=false
	match g.stage_id:
		201:
			if not _alive(g,"friendly_ship"):return g._fail("己方船损毁")
			ready=true
		202:
			var prisoners=_units_of_kind(g,"prisoner").filter(func(u):return str(u.id)!="lord")
			if prisoners.filter(func(u):return int(u.hp)>0).size()<3:return g._fail("无法救出三名普通俘虏")
			ready=objects.get("prison_door",false) and prisoners.filter(func(u):return evacuated.has(str(u.id))).size()>=3
			# A rescue reaching the shared exit must not cut off later friendly
			# slots in this same phase. They receive only their ordinary action;
			# Lord need not survive or arrive for the main objective to count.
			q.pending_friendly_actions=false
			if ready and g.phase=="player" and _units_of_kind(g,"prisoner").any(func(u):return int(u.hp)>0 and u.side=="player" and not u.get("locked",false) and not u.get("hidden",false) and not u.get("acted",false)):
				q.pending_friendly_actions=true;ready=false
		203:
			if _all_dead(_units_of_kind(g,"camp")):return g._fail("渔民营地陷落")
			ready=g.living("enemy").is_empty()
		204:
			if _beacon_enemy(g).is_empty():q.beacon_since=-1;q.beacon_contested=false
			ready=g.turn>=6 and g.phase=="player" and _beacon_enemy(g).is_empty()
		205:ready=objects.get("myth_box",false) and objects.get("pilot_prison",false)
		206:
			if _all_dead(_boats(g)):return g._fail("居民船队全部损毁")
			ready=_boats(g).any(func(b):return int(b.hp)>0 and bool(b.arrived))
		211:
			var patients=_units_of_kind(g,"patient")
			if patients.any(func(u):return int(u.hp)<int(u.max_hp)):g.queue_lines(_mid_lines(g),"S21-MID")
			if _all_dead(patients):return g._fail("载病人的船组均未能获救")
			ready=g.living("enemy").is_empty() and patients.any(func(u):return int(u.hp)>0 and evacuated.has(str(u.id)))
		212:
			var sailor=g.find_unit("old_sailor")
			ready=g.living("enemy").is_empty() and objects.get("relics",false) and (not sailor.is_empty() and (int(sailor.hp)<=0 or evacuated.has("old_sailor")))
	if _boss_defeated(g) and ready:g.battle_outcome="victory"
	return g.battle_outcome

static func on_victory(g) -> void:
	var code=str(g.battle_data.code);g.flags["clear_"+code]=true
	if not g.flags.has("east_recruit_ready"):g.flags.east_recruit_ready={}
	match g.stage_id:
		202:g.flags.east_recruit_ready.lord=_alive(g,"lord") and g.flags.quest.evacuated.has("lord")
		203:g.flags.east_recruit_ready.roan=_alive(g,"roan")
		204:
			g.flags.east_recruit_ready.shia=_alive(g,"shia")
			g.flags.islanders_survived=not _all_dead(_units_of_kind(g,"islanders"))
		205:
			g.flags.pesa_defeated=true
			if g.campaign.scenes.has("D22_DEFEAT"):g.queue_pages(g.campaign.scenes.D22_DEFEAT,"D22-DEFEAT")
		206:g.flags.east_boats_arrived=_boats(g).filter(func(b):return int(b.hp)>0 and bool(b.arrived)).size()
		211:
			g.flags.drifting_fishers_rescued=true
		212:
			g.flags.old_sailor_rescued=_alive(g,"old_sailor") and g.flags.quest.evacuated.has("old_sailor");g.flags.sailor_rescued=g.flags.old_sailor_rescued
			g.flags.carlo_promise_completed=g.flags.old_sailor_rescued and g.speaker_alive("卡洛")
			g.flags.relics_recovered=true
	if g.stage_id==205:
		for enemy in g.living("enemy"):enemy.side="neutral";enemy.surrendered=true;enemy.no_counter=true
	g.queue_lines(_end_lines(g),code+"-END")

static func status(g) -> Array[String]:
	var result: Array[String]=[];var q: Dictionary=g.flags.get("quest",{});var objects: Dictionary=q.get("objects",{});var evacuated: Array=q.get("evacuated",[])
	var boss=g.find_unit(str(g.battle_data.get("boss_id","")))
	var boss_state="已击败" if not boss.is_empty() and int(boss.hp)<=0 else "未击败"
	match g.stage_id:
		201:
			var ship=g.find_unit("friendly_ship")
			result.append("击败指挥官并保住己方船。指挥官："+boss_state)
			result.append("船体耐久：%d/%d。敌人可以攻击船体，船体不能反击或接受治疗。" % [int(ship.get("hp",0)),int(ship.get("max_hp",0))])
			result.append("步兵沿甲板和两块跳板通行，海面不可落脚。")
		202:
			var count=_units_of_kind(g,"prisoner").filter(func(u):return str(u.id)!="lord" and evacuated.has(str(u.id))).size()
			result.append("打开囚舱、击败舰长，并让三名普通俘虏从己方船撤离。")
			result.append("囚舱：%s；舰长：%s；普通俘虏：%d/3。" % ["已打开" if objects.get("prison_door",false) else "未打开",boss_state,count])
			var lord=g.find_unit("lord");var lord_state="已撤离，可在据点交谈招募" if evacuated.has("lord") else "阵亡，失去招募" if not lord.is_empty() and int(lord.hp)<=0 else "尚未撤离，保护他沿安全路线走向出口"
			result.append("洛德："+lord_state+"。他单独记录，不替代三名普通俘虏。")
			result.append("获救者每次己方行动结束走两格，附近有敌人时停下。")
			if q.get("pending_friendly_actions",false):result.append("三名普通俘虏已经撤离，等待本轮其余获救者行动结束后结算。")
		203:
			var camp=g.find_unit("fishers")
			result.append("清除全部魔物并保护渔民营地；仅击败首领不算胜利。")
			result.append("剩余魔物：%d；营地：%d/%d。" % [g.living("enemy").size(),int(camp.get("hp",0)),int(camp.get("max_hp",0))])
			result.append("罗恩存活可在渔村招募；他的阵亡不影响长者提供航路。")
		204:
			result.append("保住航灯至第6己方回合，并击败首领。当前第%d回合；首领：%s。" % [g.turn,boss_state])
			result.append("警告：敌人占住航灯，下一己方回合开始前必须夺回！" if q.get("beacon_contested",false) else "航灯尚未失守。敌军连续占据一整回合才会失败。")
			result.append("希雅的生死和岛民安置分别记录，战后前往灯屋交谈。")
		205:
			result.append("击败裴萨、打开引航者牢门，并亲自确认神教箱。")
			result.append("裴萨：%s；牢门：%s；箱子：%s。" % [boss_state,"已打开" if objects.get("pilot_prison",false) else "未打开","已确认" if objects.get("myth_box",false) else "未确认"])
			result.append("箱子是剧情证物，战斗胜利后还需在军港面对神教箱取回航图。")
		206:
			result.append("护送至少一艘居民船抵达西岸，并击败封航首领。首领："+boss_state)
			for b in event_boats(g):result.append("%s：%d/%d，%s。" % ["居民船一" if str(b.id).ends_with("0") else "居民船二",b.hp,b.max_hp,"已抵达" if b.arrived else "损毁" if b.hp<=0 else "等候前船出发" if b.waiting else "前方有敌，暂时停船" if b.stopped else "沿指定水路前进"])
			result.append("每次己方行动结束船队前进；先清除沿岸敌人。敌方回合结束，射程内的敌人会损伤船体。")
		211:
			var survivors=_units_of_kind(g,"patient").filter(func(u):return int(u.hp)>0).size()
			var arrived=_units_of_kind(g,"patient").filter(func(u):return int(u.hp)>0 and evacuated.has(str(u.id))).size()
			result.append("清除全部海上魔物，护送至少一组病人抵达安全停泊口。")
			result.append("剩余魔物：%d；存活病人组：%d；已靠岸：%d。" % [g.living("enemy").size(),survivors,arrived])
			result.append("病人组会避开近敌，先清出甲板。治疗仍支付施法者正常生命消耗。")
		212:
			result.append("清除洞内魔物、取遗物箱，并护送旧船员到出口。")
			result.append("剩余魔物：%d；遗物箱：%s；船员：%s。" % [g.living("enemy").size(),"已取得" if objects.get("relics",false) else "未取得","已撤离" if evacuated.has("old_sailor") else "阵亡，将记录遗憾后日谈" if not _alive(g,"old_sailor") else "等待救援"])
			result.append("船员死亡不阻断清场和取回遗物，卡洛的承诺按真实存活结果记录。")
	return result


static func _mid_lines(g) -> String:
	match g.stage_id:
		201:return "莉莎：另一条船的弓手换到右边了。"
		202:return "洛德：我能把右边的跳板放下。后面的人跟我走。" if _alive(g,"lord") else "引航者：右边的跳板还能放下。后面的人沿甲板跟我走。"
		203:return "莉莎：那几只硬甲的，我来试。你们看住天上的。"
		204:
			if not _alive(g,"islanders"):return "米蕾：东边那条船在靠岸。我们还得守住航灯。"
			return "米蕾：伤者都进屋了。希雅，东边那条船在靠岸。" if _alive(g,"shia") else "米蕾：伤者已经进屋，东边那条船在靠岸。我们要守住航灯。"
		205:return "引航者：牢门开了。箱子还在主楼，别忘了把它带走。"
		206:return "卡洛：已经能看见西岸了。后面的船跟紧。"
		211:return "米蕾或艾琳：让前排护住跳板，先清出病人前面的路。"
		212:
			return "旧船员：我不敢回去见他们的家属。／卡洛：遗物不能留在这里。把路清出来，我陪你走。" if g.speaker_alive("卡洛") else "旧船员：那是卡洛的船牌……这些遗物，请替我交给他们的家属。／艾琳：先离开这里。家属也该知道你还活着。"
	return str(g.battle_data.during)

static func _end_lines(g) -> String:
	match g.stage_id:
		203:
			if not _alive(g,"roan"):return "渔村长者：军港的岸线我们熟悉。我会把航路交给你们，别走外面的礁道。"
		204:
			if not _alive(g,"shia"):return "留守骑士：岛上的航灯由我们看守。安全的军港航路已经记下，去灯屋确认吧。"
		205:return "艾琳：先带引航者离开牢房。我去确认箱里的航图。"
		206:return "舵手：西岸到了，居民船已经安全靠岸。／艾琳：让伤者先上岸，我们去海峡城。"
		211:return "渔民：风灯岛东侧还有一处避风泊位。你们救了船上的人，这条路我会给你们标清。"
		212:
			if not _alive(g,"old_sailor"):
				return "卡洛：没来得及带他回去。这些遗物，我会交给家属。" if g.speaker_alive("卡洛") else "艾琳：把遗物带回去。至少让家属知道他们的下落。"
	return str(g.battle_data.after)


static func before_lines(g) -> String:
	var line=str(g.battle_data.before)
	if g.stage_id==202:
		if not g.speaker_alive("米蕾"):line=line.replace("米蕾：先打开舱门", "艾琳：先打开舱门")
		if not g.speaker_alive("卡洛"):line=line.replace("艾琳：卡洛，你挡住舰长那边。", "艾琳：护卫守住舰长一侧，其他人去开门。")
	if g.stage_id==212 and not g.speaker_alive("卡洛"):return "艾琳：先清出通往洞室的路，里面还有人。"
	return line
