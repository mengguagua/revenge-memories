extends "res://core/legacy_game_state.gd"
## New campaign. Inherit original combat formulas; isolate campaign/save semantics.
const ChapterTwo = preload("res://core/chapter2_rules.gd")
const CAMPAIGN_ID := "revenge-memories-1"
const SAVE_FIELDS := ["chapter","route","parties","route_positions","previous_world_node","convoy","hub_id","hub_position","battle_return","battle_settled","story_events","stage_id","world_node","cleared_stages","roster","battle_start_snapshot","victory_rewards","flags","party","mode","units","phase","turn","rng_state","frame_counter","kills","selected_id","cursor","move_origin","battle_outcome"]
var campaign: Dictionary
var formal_world: Dictionary
var hub_record := "P00"
var _guard_target_context := false

func _init() -> void:
	var original_classes=read_json("res://data/legacy/campaign.json").get("classes",{}).duplicate(true)
	campaign=read_json("res://data/campaign.json");formal_world=read_json("res://data/formal_world.json")
	characters=campaign.characters.duplicate(true);stages.clear()
	for key in campaign.stages:stages[int(key)]=read_json(str(campaign.stages[key].path))
	catalog={"characters":characters,"classes":original_classes,"world_nodes":formal_world.nodes,"routes":{},"chapter_armies":{},"enemy_groups":{},"stages":{}}
	battle_data=stages[101].duplicate(true);opening.characters=characters;save_path="user://revenge-memories-ch1.json"

func new_game() -> void:
	flags={"campaign_id":CAMPAIGN_ID,"hub_record":"P00","quest":{},"world_previous":1}
	chapter=1;route="alm";world_node=1;previous_world_node=1
	route_positions={"alm":1,"celica":17}
	party=campaign.initial_party.duplicate();parties={"alm":party.duplicate(),"celica":[]};roster.clear()
	for id in party:roster[id]=_initial_character(str(id))
	convoy={"alm":[],"celica":[]};world_armies.clear();units.clear();story_events.clear()
	cleared_stages.clear();battle_start_snapshot.clear();battle_return.clear();victory_rewards.clear()
	stage_id=101;battle_data=stages[101].duplicate(true);mode="hub";turn=1;phase="player";rng_state=0;frame_counter=0;kills=0
	battle_outcome="";battle_settled=false;selected_id="";hub_record="P00";hub_position=Vector2i(3,8)

func _initial_character(id: String) -> Dictionary:
	var u: Dictionary=characters.get(id,{}).duplicate(true);u.id=id;u.side="player";u.dead=false;u.acted=false;return u
func leader_id() -> String:return "eileen" if route=="celica" else "hunapu"
func can_switch_route() -> bool:return false
func can_return_to_final_preparation() -> bool:return false
func needs_terrain_recovery() -> bool:return false

func allowed_world_nodes() -> Array[int]:
	if chapter==2:return ChapterTwo.allowed_nodes(self)
	var result: Array[int]=[1]
	if flags.get("village_ready",false):result.append(2)
	if cleared_stages.has(101):
		result.append(3)
		if not flags.get("chapter1_complete",false) or cleared_stages.has(111):result.append(31)
		if not flags.get("chapter1_complete",false) or cleared_stages.has(112):result.append(32)
	if cleared_stages.has(102) and flags.get("grain_shared",false):result.append(4)
	if cleared_stages.has(103) and flags.get("orders_collected",false) and flags.get("cooperation_done",false):result.append(5)
	if cleared_stages.has(104):result.append(6)
	return result
func world_neighbors() -> Array[int]:
	var result: Array[int]=[];var allowed=allowed_world_nodes()
	if world_has_battle(world_node):
		if previous_world_node in allowed and previous_world_node!=world_node:result.append(previous_world_node)
		return result
	for n in formal_world.nodes.get(str(world_node),{}).get("neighbors",[]):
		if int(n) in allowed:result.append(int(n))
	return result
func route_between(a: int,b: int) -> Dictionary:
	var ai=str(formal_world.nodes[str(a)].id);var bi=str(formal_world.nodes[str(b)].id)
	for r in formal_world.routes:
		if (r.a==ai and r.b==bi) or (r.b==ai and r.a==bi):return r
	return {}
func travel_to(node: int) -> bool:
	if not node in world_neighbors():return false
	previous_world_node=world_node;world_node=node;flags.world_previous=previous_world_node;route_positions[route]=node;return true
func stage_for_node(node: int) -> int:
	for key in campaign.stages:
		if int(campaign.stages[key].node)==node:return int(key)
	return 0
func world_has_battle(node: int) -> bool:
	var id=stage_for_node(node);return id>0 and not stage_cleared(id)

func start_battle(id: int=101,_groups: Array=[],_from_hub: bool=false) -> bool:
	if not stages.has(id) or stage_cleared(id) or int(stages[id].node)!=world_node:return false
	if int(stages[id].get("chapter",2 if id>=200 else 1))!=chapter:return false
	stage_id=id;battle_data=stages[id].duplicate(true);encounter_groups=[]
	battle_return={"mode":"world","world_node":world_node,"previous_world_node":previous_world_node};units.clear();var slot=0
	for member in party:
		if not roster.has(member):continue
		var u: Dictionary=roster[member].duplicate(true)
		if bool(u.get("dead",false)) or int(u.hp)<=0:continue
		u.position=battle_data.player_positions[slot].duplicate();u.hp=int(u.max_hp);u.acted=false;u.side="player";u.player_slot=slot
		u.erase("weapon_index");u.route=route;units.append(u);slot+=1
	for i in range(battle_data.enemies.size()):
		var u: Dictionary=battle_data.enemies[i].duplicate(true);u.enemy_slot=i;units.append(u)
	for raw in battle_data.npc_units:
		var u: Dictionary=raw.duplicate(true);u.player_slot=slot;u.route=route
		if not u.get("battle_guard",false):u.move=2
		slot+=1;units.append(u)
	turn=1;phase="player";kills=0;selected_id="";battle_outcome="";battle_settled=false
	flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}
	ChapterTwo.initialize(self)
	flags.inventory_processed_deaths={}
	mode="battle";cursor=pos(find_unit(leader_id()));log_lines.clear();victory_rewards.clear()
	queue_lines(ChapterTwo.before_lines(self) if stage_id>=200 else str(battle_data.before),battle_data.code+"-BEGIN");battle_start_snapshot=_capture_battle_start();return true
func retry_battle() -> bool:
	if battle_start_snapshot.is_empty():return false
	var s: Dictionary=battle_start_snapshot.duplicate(true)
	for key in s:
		if key in SAVE_FIELDS and not key in ["hub_position","cursor","move_origin"]:set(key,s[key])
	stage_id=int(s.stage_id);world_node=int(s.world_node);previous_world_node=int(s.previous_world_node)
	cleared_stages=s.cleared_stages.map(func(v):return int(v));battle_data=stages[stage_id].duplicate(true)
	battle_settled=false;battle_outcome="";phase="player";turn=1;mode="battle";selected_id="";flags.erase("active_plot")
	cursor=pos(find_unit(leader_id()));victory_rewards.clear();return true

func queue_pages(pages: Array,key: String="") -> void:
	if not key.is_empty() and flags.get("seen_"+key,false):return
	if not key.is_empty():flags["seen_"+key]=true
	story_events.append({"kind":"new_story","pages":pages,"key":key})
func speaker_alive(name: String) -> bool:
	for id in characters:
		if characters[id].name_zh==name:
			var u: Dictionary=find_unit(id)
			if u.is_empty():u=roster.get(id,{})
			return not u.is_empty() and int(u.get("hp",0))>0 and not bool(u.get("dead",false))
	return true
func queue_lines(text: String,key: String="") -> void:
	var pages=[]
	for fragment in text.split("／"):
		var ix=fragment.find("：");var who=fragment.substr(0,ix).strip_edges() if ix>=0 else "旁白"
		var line=fragment.substr(ix+1).strip_edges() if ix>=0 else fragment
		if who.contains("或"):
			var names=who.split("或");who=names[0] if speaker_alive(names[0]) else names[-1]
		if not speaker_alive(who) and chapter==2:
			var replacement={"米蕾":"地方医者","莉莎":"甲板护卫","卡洛":"固定舵手","洛德":"引航者","罗恩":"渔村长者","希雅":"留守骑士"}
			who=replacement.get(who,"艾琳")
			if fragment.begins_with("卡洛：") and (fragment.contains("报酬") or fragment.contains("这次我去送")):line="遗物由我们交给家属。卡洛留下的船牌也会送回去。"
		elif not speaker_alive(who):
			who="村民" if who=="奥托" else "管理员" if who in ["芙拉","赫维"] else "教团兵" if who=="兰斯" else "胡纳普"
			if who=="胡纳普":line="路已查清。我们先把这里的人带回去。"
		pages.append({"speaker":who,"text":line})
	queue_pages(pages,key)

func movement_cost(unit: Dictionary,cell: Vector2i) -> int:
	var value=super.movement_cost(unit,cell)
	return 1 if unit.has("quest_kind") and value<255 else value
func unit_at(cell: Vector2i,alive_only: bool=true) -> Dictionary:
	for unit in units:
		if str(unit.side)=="evacuated" or bool(unit.get("hidden",false)):continue
		if pos(unit)==cell and (not alive_only or int(unit.hp)>0):return unit
	return {}
func _toward(unit: Dictionary,destination: Vector2i) -> Dictionary:
	var graph=reachable(unit);var best=pos(unit);var best_distance=999999
	var seen={destination:0};var q: Array[Vector2i]=[destination]
	while not q.is_empty():
		var p=q.pop_front()
		for d in DIRECTIONS:
			var n=p+d
			if not in_bounds(n) or seen.has(n) or movement_cost(unit,n)>=255:continue
			seen[n]=int(seen[p])+1;q.append(n)
	for cell in graph.costs:
		if not can_stop(unit,cell):continue
		var dist=int(seen.get(cell,999999))
		if dist<best_distance:best_distance=dist;best=cell
	return {"destination":best,"target":"","kind":"objective_move"}
func _held_captive(unit: Dictionary) -> bool:
	return stage_id in [103,105,202,205] and bool(unit.get("neutral",false)) and bool(unit.get("locked",false)) and str(unit.get("quest_kind","")) in ["escort","prisoner","witness"]

func living(side: String) -> Array:
	var result=super.living(side)
	if _guard_target_context and side=="player":return result.filter(func(u):return not _held_captive(u))
	return result

func can_attack(unit: Dictionary,other: Dictionary) -> bool:
	# A held captive belongs to the guard's own prison detail until released.
	# This controls target intent only; HP, damage and position stay ordinary.
	if unit.get("side","")=="enemy" and _held_captive(other):return false
	return super.can_attack(unit,other)

func ai_action(unit: Dictionary,gather: bool=false) -> Dictionary:
	var previous_context=_guard_target_context
	_guard_target_context=stage_id in [103,105,202,205] and unit.get("side","")=="enemy"
	var action=_campaign_ai_action(unit,gather)
	_guard_target_context=previous_context
	return action

func _campaign_ai_action(unit: Dictionary,gather: bool=false) -> Dictionary:
	if stage_id>=200:
		var override=ChapterTwo.ai_action(self,unit)
		if not override.is_empty():return override
	if unit.has("quest_kind"):
		if bool(unit.get("locked",false)) or str(unit.quest_kind)=="witness":return {"destination":pos(unit),"target":""}
		# Escorted groups wait at an enemy-held stretch instead of marching into it.
		var nearby=living("enemy").any(func(e):return absi(pos(e).x-pos(unit).x)+absi(pos(e).y-pos(unit).y)<=maxi(4,Rules.attack_range(e).y+1))
		if nearby:return {"destination":pos(unit),"target":""}
		var target=Vector2i(battle_data.exit[0],battle_data.exit[1])
		if str(unit.quest_kind)=="medicine":target=Vector2i(battle_data.targets[0][0],battle_data.targets[0][1])
		var action=_toward(unit,target);var safe=pos(unit)
		for step in path_to(unit,action.destination):
			if living("enemy").any(func(e):return absi(pos(e).x-step.x)+absi(pos(e).y-step.y)<=maxi(4,Rules.attack_range(e).y+1)):break
			safe=step
		action.destination=safe;return action
	if bool(unit.get("burner",false)):
		if turn<5:return {"destination":pos(unit),"target":""}
		return _toward(unit,Vector2i(battle_data.targets[0][0],battle_data.targets[0][1]))
	if str(unit.id)=="M15_boss" and ((turn>=6 and int(unit.hp)*2<int(unit.max_hp)) or turn>=8):
		if not flags.quest.get("escape_announced",false):flags.quest.escape_announced=true;queue_lines("科兰：去北门！撤离点就在旧塔后面。","M15-ESCAPE")
		return _toward(unit,Vector2i(battle_data.exit[0],battle_data.exit[1]))
	if bool(unit.get("offering_surrender",false)):return {"destination":pos(unit),"target":""}
	if unit.get("behavior","")=="guard":
		var previous=int(unit.move);unit.move=0
		var action=super.ai_action(unit,gather);unit.move=previous;return action
	return super.ai_action(unit,gather)
func mark_wait(id: String) -> void:
	super.mark_wait(id);var u=find_unit(id)
	if u.is_empty():return
	if stage_id>=200:ChapterTwo.after_wait(self,u)
	if u.has("quest_kind") and str(u.quest_kind) in ["escort","medicine"]:
		var goal=battle_data.targets[0] if str(u.quest_kind)=="medicine" else battle_data.exit
		if pos(u)==Vector2i(goal[0],goal[1]):
			if not flags.quest.evacuated.has(id):flags.quest.evacuated.append(id)
			u.side="evacuated";u.hidden=true;queue_lines(str(battle_data.during),str(battle_data.code)+"-MID")
	if bool(u.get("burner",false)) and turn>=5:
		var goal=Vector2i(battle_data.targets[0][0],battle_data.targets[0][1])
		flags.quest.burn_streak=int(flags.quest.burn_streak)+1 if pos(u)==goal else 0
		if int(flags.quest.burn_streak)==1:queue_lines("焚毁兵：下一轮就点火！／胡纳普：先阻止粮仓门口的人。","M12-BURN")
	check_outcome()
func next_phase() -> void:
	if not battle_outcome.is_empty():return
	ChapterTwo.before_phase(self)
	if not battle_outcome.is_empty():return
	var object_hp={}
	for unit in units:
		if unit.get("event_object",false):object_hp[str(unit.id)]=int(unit.hp)
	super.next_phase()
	for id in object_hp:find_unit(id).hp=object_hp[id]
	ChapterTwo.after_phase(self)
	if phase=="player" and turn==4 and stage_id==102:queue_lines("战场提示：焚毁兵下一回合从集合点出发。拦住他，别让他在门前连续点火。","M12-FIRE-WARNING")
	if phase=="enemy" and turn==int(battle_data.reinforcement_turn) and not flags.quest.reinforced:
		flags.quest.reinforced=true
		for raw in battle_data.reinforcements:
			if not find_unit(str(raw.id)).is_empty():continue
			var u: Dictionary=raw.duplicate(true);var at=pos(u)
			if not unit_at(at).is_empty():
				for d in DIRECTIONS:
					if in_bounds(at+d) and unit_at(at+d).is_empty() and movement_cost(u,at+d)<255:u.position=[at.x+d.x,at.y+d.y];break
			if not unit_at(pos(u)).is_empty():
				var free=ChapterTwo.free_spawn(self,u,at)
				if free==Vector2i(-1,-1):continue
				u.position=[free.x,free.y]
			u.enemy_slot=units.filter(func(z):return str(z.side)=="enemy").size();units.append(u)
	if phase=="player" and turn==maxi(1,int(battle_data.reinforcement_turn)-1) and int(battle_data.reinforcement_turn)>0:
		queue_lines("斥候：后方路口有援军。下一回合抵达，只有这一队。",str(battle_data.code)+"-REINFORCEMENT-WARNING")
	check_outcome()

func interactions_for(unit: Dictionary) -> Array:
	var result=[]
	if unit.is_empty() or unit.side!="player" or not bool(unit.get("controllable",true)) or bool(unit.get("acted",false)):return result
	for obj in battle_data.objects:
		if flags.quest.objects.get(str(obj.id),false):continue
		var p=Vector2i(obj.position[0],obj.position[1]);var d=absi(p.x-pos(unit).x)+absi(p.y-pos(unit).y)
		if d==0 or (obj.adjacent and d==1):result.append(obj)
	var boss=find_unit(str(battle_data.boss_id))
	if not boss.is_empty() and bool(boss.get("offering_surrender",false)) and absi(pos(boss).x-pos(unit).x)+absi(pos(boss).y-pos(unit).y)==1:result.append({"id":"surrender","label":"接受投降"})
	return result
func interact(id: String) -> bool:
	var actor=find_unit(selected_id);var choices=interactions_for(actor)
	if not choices.any(func(o):return str(o.id)==id):return false
	if stage_id>=200:
		ChapterTwo.interact(self,id)
		actor.acted=true;selected_id="";check_outcome();return true
	if id=="surrender":
		var boss=find_unit(str(battle_data.boss_id));boss.side="neutral";boss.surrendered=true
	else:
		flags.quest.objects[id]=true
		for o in battle_data.objects:
			if str(o.id)!=id:continue
			if o.kind in ["door","rescue"]:
				var index=battle_data.objects.find(o);flags.quest.freed.append(index)
				var x=int(o.position[0]);var y=int(o.position[1]);battle_data.map.tiles[y*int(battle_data.map.width)+x]=208
				for u in units:
					if str(u.id)==str(battle_data.code)+"_workers"+str(index) or (u.id=="lena" and index==0):u.locked=false
				queue_lines("劳工：门开了。我们沿着清出的路撤离。",id+"-OPEN")
				if index==0:queue_lines(str(battle_data.during),str(battle_data.code)+"-MID")
			if o.kind=="occupy":queue_lines(str(battle_data.during),"M12-MID")
			if o.kind=="tools" and not flags.get("tools_reward",false):convoy.alm.append(2);flags.tools_reward=true
	actor.acted=true;selected_id="";check_outcome();return true

func check_outcome() -> String:
	if battle_outcome=="defeat":return battle_outcome
	if stage_id>=200:return ChapterTwo.check_outcome(self)
	var leader=find_unit(leader_id());var q: Dictionary=flags.get("quest",{})
	if not leader.is_empty() and int(leader.hp)<=0:return _fail("胡纳普阵亡")
	if int(q.get("burn_streak",0))>=2:return _fail("粮仓被焚毁")
	for u in units:
		if str(u.get("quest_kind","")) in ["escort","medicine"] and int(u.hp)<=0 and stage_id in [101,111,112]:return _fail(str(u.name_zh)+"未能获救")
	var boss=find_unit(str(battle_data.get("boss_id","")))
	var workers=units.filter(func(u):return str(u.id).begins_with(str(battle_data.code)+"_workers") and int(u.hp)>0)
	if stage_id in [103,105] and workers.is_empty():return _fail("两组劳工均未能获救")
	if stage_id==105 and not boss.is_empty() and int(boss.hp)>0 and pos(boss)==Vector2i(battle_data.exit[0],battle_data.exit[1]):return _fail("科兰从北门逃离")
	if stage_id==104 and not boss.is_empty() and int(boss.hp)>0 and int(boss.hp)*2<=int(boss.max_hp) and not boss.get("offering_surrender",false):boss.offering_surrender=true;boss.no_counter=true;queue_lines(str(battle_data.during),"M14-SURRENDER")
	var defeated=not boss.is_empty() and (int(boss.hp)<=0 or bool(boss.get("surrendered",false)));var ready=false
	match stage_id:
		101,111:ready=q.get("evacuated",[]).size()>=2
		102,104:ready=q.get("objects",{}).size()>=battle_data.objects.size()
		103:ready=q.get("objects",{}).size()>=2 and workers.any(func(u):return not bool(u.get("locked",false)))
		105:ready=workers.any(func(u):return not bool(u.get("locked",false)))
		112:ready=q.get("evacuated",[]).has("medicine_wagon")
	if defeated and ready:battle_outcome="victory"
	return battle_outcome
func _fail(reason: String) -> String:flags.quest.failed_reason=reason;battle_outcome="defeat";return battle_outcome
func story_on_death(unit: Dictionary) -> void:
	if unit.id in characters and bool(unit.get("neutral",false)):
		var dead=_initial_character(unit.id);dead.hp=0;dead.dead=true;roster[unit.id]=dead
func story_on_victory() -> void:
	if stage_id>=200:
		ChapterTwo.on_victory(self);return
	flags["clear_"+str(battle_data.code)]=true
	if stage_id==101:flags.side_invites=true
	if stage_id==103:flags.labor_rescued=true
	if stage_id==105:queue_pages(campaign.scenes.D13,"D13");flags.korlan_defeated=true
	if stage_id in [104,105]:
		for unit in living("enemy"):
			unit.side="neutral";unit.surrendered=true;unit.no_counter=true
	var after="赫兰：军令已经交给记录官，我会公布凯尔的事。／胡纳普：塔里的人先带出来。" if stage_id==105 else str(battle_data.after).split(" M12-MYTH")[0]
	queue_lines(after,str(battle_data.code)+"-END")
	if stage_id==111 and not flags.get("S11_reward",false):convoy.alm.append(11);flags.S11_reward=true

func return_to_preparation() -> bool:
	if not retry_battle():return false
	world_node=previous_world_node;route_positions[route]=world_node;story_events.clear();mode="world";battle_outcome="";selected_id=""
	return true

func support_targets(caster: Dictionary,spell_id: int) -> Array:
	return super.support_targets(caster,spell_id).filter(func(u):return not bool(u.get("event_object",false)))

func finish_exchange(exchange: Dictionary) -> Dictionary:
	var reward=super.finish_exchange(exchange)
	if stage_id==105 and str(exchange.get("defender",""))=="M15_boss":queue_lines(str(battle_data.during),"M15-MID")
	if stage_id==205 and (str(exchange.get("defender",""))==str(battle_data.boss_id) or str(exchange.get("attacker",""))==str(battle_data.boss_id)):
		if campaign.scenes.has("D22_FIRST"):queue_pages(campaign.scenes.D22_FIRST,"D22-FIRST")
		else:queue_lines(str(battle_data.during),"F25-MID")
	return reward

func save_game() -> bool:
	var state={"schema":2,"campaign_id":CAMPAIGN_ID,"hub_record":hub_record}
	state.map_revision=str(battle_data.get("tactical_review_version","0.2.0"))
	for key in SAVE_FIELDS:
		var value=get(key);state[key]=[value.x,value.y] if value is Vector2i else value
	var file=FileAccess.open(save_path+".tmp",FileAccess.WRITE)
	if file==null:return false
	file.store_string(JSON.stringify(state));file.flush();file.close()
	return DirAccess.rename_absolute(ProjectSettings.globalize_path(save_path+".tmp"),ProjectSettings.globalize_path(save_path))==OK
func load_game() -> bool:
	var s=read_json(save_path)
	if not SaveValidation.campaign_valid(self,s,SAVE_FIELDS):return false
	for key in SAVE_FIELDS:
		if key in ["hub_position","cursor","move_origin"]:set(key,Vector2i(s[key][0],s[key][1]))
		elif key=="cleared_stages":cleared_stages=s[key].map(func(v):return int(v))
		else:set(key,s[key])
	stage_id=int(stage_id);world_node=int(world_node);previous_world_node=int(previous_world_node);chapter=int(chapter);turn=int(turn)
	# Canonical object identity also applies to developmental saves made before tags.
	for array in [units,battle_start_snapshot.get("units",[])]:
		for unit in array:
			if str(unit.id)=="medicine_wagon":unit.no_counter=true;unit.event_object=true
	hub_record=str(s.get("hub_record","H01"));battle_data=stages[stage_id].duplicate(true)
	# In-progress battles retain their geometry until a normal retry/re-entry.
	# New walls and cargo must never appear underneath an old saved formation.
	if str(s.get("map_revision","0.2.0"))=="0.2.0" and mode in ["battle","victory","defeat"]:
		var compatible="res://data/compat/0.2.0/"+str(battle_data.code)+".json"
		if FileAccess.file_exists(compatible):battle_data=read_json(compatible).duplicate(true)
	for o in battle_data.objects:
		if flags.get("quest",{}).get("objects",{}).get(str(o.id),false):
			if stage_id>=200:ChapterTwo.open_object(self,o)
			elif o.kind in ["door","rescue"]:battle_data.map.tiles[int(o.position[1])*int(battle_data.map.width)+int(o.position[0])]=208
	return true

func begin_chapter_two() -> bool:
	if chapter!=1 or not flags.get("chapter1_complete",false) or not stage_cleared(105):return false
	if not stages.has(201) or campaign.get("initial_east_party",[]).is_empty():return false
	parties.alm=party.duplicate();route_positions.alm=world_node
	flags.west_chapter1_snapshot={"party":party.duplicate(),"position":world_node}
	chapter=2;route="celica";party=campaign.initial_east_party.duplicate();parties.celica=party.duplicate()
	for id in party:
		if not roster.has(id):roster[id]=_initial_character(str(id))
		roster[id].route="celica"
	if not convoy.has("celica"):convoy.celica=[]
	world_node=17;previous_world_node=17;route_positions.celica=17;stage_id=201
	battle_data=stages[201].duplicate(true);units.clear();battle_start_snapshot.clear();battle_return.clear();victory_rewards.clear();story_events.clear()
	flags.erase("active_plot");flags.quest={};flags.chapter2_started=true;flags.east_recruit_ready={"lord":false,"roan":false,"shia":false}
	mode="hub";hub_record="H21";hub_position=Vector2i(6,7);battle_outcome="";battle_settled=false;selected_id="";phase="player";turn=1
	return true

func finish_chapter_two() -> bool:
	if chapter!=2 or route!="celica" or not stage_cleared(206) or flags.get("chapter2_complete",false):return false
	parties.celica=party.duplicate();previous_world_node=world_node;world_node=6;route_positions.celica=6;flags.world_previous=previous_world_node
	flags.chapter2_complete=true;flags.chapter3_pending=true
	mode="chapter_end";selected_id="";return true

func event_boats() -> Array:return ChapterTwo.event_boats(self)

func recruit(id: String) -> void:
	if id in ["lord","roan","shia"] and not flags.get("east_recruit_ready",{}).get(id,false):return
	super.recruit(id)
	if roster.has(id):roster[id].route=route

func objective_status() -> Array[String]:
	if stage_id>=200:return ChapterTwo.status(self)
	var result: Array[String]=[str(battle_data.get("goal","完成战场目标"))]
	var q: Dictionary=flags.get("quest",{})
	if not q.get("failed_reason","").is_empty():result.append(str(q.failed_reason))
	return result

func receive_equipment(item_id: int) -> Dictionary:
	var definition=Items.item(item_id)
	if item_id<=0 or definition.get("kind","") not in ["weapon","accessory"]:return {"valid":false,"reason":"unsupported_item"}
	for id in party:
		var recipient: Dictionary=roster.get(id,{})
		if recipient.is_empty() or recipient.get("dead",false) or int(recipient.get("hp",0))<=0:continue
		if int(recipient.get("item_id",0))==0 and Items.can_use(recipient,item_id):
			recipient.item_id=item_id
			return {"valid":true,"destination":"unit","recipient":id,"item_id":item_id,"route":route}
	if convoy[route].size()>=40:return {"valid":false,"reason":"convoy_full"}
	convoy[route].append(item_id)
	return {"valid":true,"destination":"convoy","item_id":item_id,"route":route}

func give_item(item_id: int) -> bool:
	return bool(receive_equipment(item_id).valid)
