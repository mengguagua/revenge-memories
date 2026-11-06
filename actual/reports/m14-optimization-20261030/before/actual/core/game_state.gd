extends "res://core/legacy_game_state.gd"
signal character_recruited(id:String)
## New campaign. Inherit original combat formulas; isolate campaign/save semantics.
const ChapterFive = preload("res://core/chapter5_rules.gd")
const ChapterFour = preload("res://core/chapter4_rules.gd")
const ChapterThree = preload("res://core/chapter3_rules.gd")
const ChapterTwo = preload("res://core/chapter2_rules.gd")
const Equipment = preload("res://core/equipment_supply.gd")
const Casualties = preload("res://core/casualty_rules.gd")
const EnemyRoles = preload("res://core/campaign_enemy_roles.gd")
const CampaignTactics = preload("res://core/campaign_tactics.gd")
const CampaignExperience = preload("res://core/campaign_experience.gd")
const RefugeeTactics = preload("res://core/refugee_tactics.gd")
const Medicine = preload("res://core/clinic_medicine.gd")
const EnemyBalance = preload("res://core/enemy_balance.gd")
const MineEscort = preload("res://core/mine_escort.gd")
const Journals = preload("res://core/journey_slots.gd")
const EquipmentComparison = preload("res://core/equipment_comparison.gd")
const HeroProfessions = preload("res://core/hero_professions.gd")
const Armaments = preload("res://core/story_armaments.gd")
const Accessories = preload("res://core/story_accessories.gd")
const Cover = preload("res://core/cover_rules.gd")
const Knockback = preload("res://core/knockback_rules.gd")
const Battlefield = preload("res://core/battlefield_tactics.gd")
const Training = preload("res://core/training_rules.gd")
const MapSkills = preload("res://core/map_skills.gd")
const CAMPAIGN_ID := "revenge-memories-1"
const SAVE_FIELDS := ["chapter","route","parties","route_positions","previous_world_node","convoy","hub_id","hub_position","battle_return","battle_settled","story_events","stage_id","world_node","cleared_stages","roster","battle_start_snapshot","victory_rewards","flags","party","mode","units","phase","turn","rng_state","frame_counter","kills","selected_id","cursor","move_origin","battle_outcome"]
var campaign: Dictionary
var formal_world: Dictionary
var hub_record := "P00"
var _guard_target_context := false
var _casualty_legacy_path := ""
var slot_directory := "user://"
var active_slot := 1
var play_seconds := 0.0
var _escort_hint_stamp:Array=[]
var _escort_hint_value:=""

func _init() -> void:
	var original_classes=read_json("res://data/legacy/campaign.json").get("classes",{}).duplicate(true)
	# Campaign display names are separate from source classes and saved class IDs.
	var class_names=read_json("res://data/class_names.json")
	for class_id in class_names:
		for name_key in class_names[class_id]:
			original_classes[class_id][name_key]=class_names[class_id][name_key]
	campaign=read_json("res://data/campaign.json");formal_world=read_json("res://data/formal_world.json")
	characters=campaign.characters.duplicate(true);stages.clear()
	for key in campaign.stages:stages[int(key)]=read_json(str(campaign.stages[key].path))
	catalog={"characters":characters,"classes":original_classes,"world_nodes":formal_world.nodes,"routes":{},"chapter_armies":{},"enemy_groups":{},"stages":{}}
	Training.register(self)
	battle_data=stages[101].duplicate(true);opening.characters=characters;save_path=Journals.path_for(slot_directory,active_slot)

func new_game() -> void:
	play_seconds=0.0
	flags={"campaign_id":CAMPAIGN_ID,"hub_record":"P00","quest":{},"world_previous":1}
	chapter=1;route="alm";world_node=1;previous_world_node=1
	route_positions={"alm":1,"celica":17}
	party=campaign.initial_party.duplicate();parties={"alm":party.duplicate(),"celica":[]};roster.clear()
	for id in party:roster[id]=_initial_character(str(id))
	convoy={"alm":[],"celica":[]};world_armies.clear();units.clear();story_events.clear()
	cleared_stages.clear();battle_start_snapshot.clear();battle_return.clear();victory_rewards.clear()
	stage_id=101;battle_data=stages[101].duplicate(true);mode="hub";turn=1;phase="player";rng_state=0;frame_counter=0;kills=0
	battle_outcome="";battle_settled=false;selected_id="";hub_record="P00";hub_position=Vector2i(3,8)
	Equipment.reconcile(self)
	ensure_treatment_sources()

func _initial_character(id: String) -> Dictionary:
	var u: Dictionary=characters.get(id,{}).duplicate(true);u.id=id;u.side="player";u.dead=false;u.acted=false;Casualties.initialize_unit(u);return u

func ensure_treatment_sources() -> void:
	Casualties.ensure_sources({"flags":flags,"cleared_stages":cleared_stages})

func is_dying(unit: Dictionary) -> bool:
	return not unit.is_empty() and (bool(unit.get("dying",false)) or (not Casualties.owner({"parties":parties},str(unit.get("id",""))).is_empty() and int(unit.get("hp",1))<=0))

func can_deploy(unit: Dictionary) -> bool:
	return not unit.is_empty() and not is_dying(unit) and not bool(unit.get("dead",false)) and int(unit.get("hp",0))>0

func _restore_preparation_hp() -> void:
	# Recover after settlement (including HP growth), never revive casualties or
	# alter the pre-battle snapshot used to retry the encounter.
	for id in roster:
		var unit: Dictionary=roster[id]
		if Casualties.owner({"parties":parties},str(id)).is_empty():continue
		if unit.get("side","player")!="player" or unit.get("temporary",false) or unit.get("neutral",false):continue
		if can_deploy(unit):unit.hp=int(unit.max_hp)
	for unit in units:
		var member: Dictionary=roster.get(str(unit.id),{})
		if Casualties.owner({"parties":parties},str(unit.id)).is_empty() or not can_deploy(member):continue
		if unit.side!="player" or unit.get("temporary",false) or unit.get("neutral",false):continue
		if can_deploy(unit):unit.hp=int(unit.max_hp)

func treatment_remaining() -> int:
	ensure_treatment_sources()
	return Casualties.available(flags,route)

func treat_member(id: String) -> Dictionary:
	return Casualties.treat(self,id)

func exchange_items(first_id: String,second_id: String) -> bool:
	if not can_deploy(roster.get(first_id,{})) or not can_deploy(roster.get(second_id,{})):return false
	return super.exchange_items(first_id,second_id)

func equipment_preview(member_id: String,index: int) -> Dictionary:
	if mode not in ["world","hub"] or not party.has(member_id) or not roster.has(member_id):return {}
	var stored: Array=convoy.get(route,[])
	if index<0 or index>=stored.size():return {}
	var result=EquipmentComparison.compare(roster[member_id],int(stored[index]),catalog.classes)
	if not can_deploy(roster[member_id]):result.can_equip=false;result.reason="濒死或无法出阵，暂不能分配装备"
	return result

func equip_from_convoy(member_id: String,index: int,expected_item: int) -> Dictionary:
	var preview=equipment_preview(member_id,index)
	if preview.is_empty() or int(preview.target_id)!=expected_item:return {"valid":false,"message":"道具已变化，请重新选择"}
	if not preview.can_equip:return {"valid":false,"message":preview.reason}
	var previous_unit: Dictionary=roster[member_id];var previous_stored: Array=convoy[route];var previous_flags=flags.duplicate(true)
	var updated=previous_unit.duplicate(true);var stored=previous_stored.duplicate()
	updated.item_id=expected_item;updated.erase("weapon_index")
	if int(previous_unit.get("item_id",0))>0:stored[index]=int(previous_unit.item_id)
	else:stored.remove_at(index)
	roster[member_id]=updated;convoy[route]=stored
	if not save_game():
		roster[member_id]=previous_unit;convoy[route]=previous_stored;flags=previous_flags
		return {"valid":false,"message":"保存失败，原装备与行囊已保留"}
	return {"valid":true,"message":"已换装，原装备退回本队行囊" if int(previous_unit.get("item_id",0))>0 else "已领取并装备"}

func leader_id() -> String:return "eileen" if route=="celica" else "hunapu"
func can_switch_route() -> bool:return ChapterFive.can_switch(self) if chapter==5 else ChapterFour.can_switch(self) if chapter==4 else ChapterThree.can_switch(self)
func switch_route() -> bool:return ChapterFive.switch_route(self) if chapter==5 else ChapterFour.switch_route(self) if chapter==4 else ChapterThree.switch_route(self)
func begin_chapter_five() -> bool:return ChapterFive.begin(self)
func begin_chapter_four() -> bool:return ChapterFour.begin(self)
func begin_chapter_three() -> bool:return ChapterThree.begin(self)
func can_return_to_final_preparation() -> bool:return false
func needs_terrain_recovery() -> bool:return false

func exit_marker() -> Dictionary:
	if Training.active(self):return {"position":battle_data.training_target.duplicate(),"label":"演习据点"}
	if stage_id==501:return {"position":battle_data.exit,"label":"南侧后撤门"}
	if stage_id==511:return {"position":battle_data.exit,"label":"南门交接点"}
	if stage_id in [401,407,412]:return {"position":battle_data.exit,"label":"南口接应" if stage_id==401 else "古道出口" if stage_id==407 else "己方船口"}
	if stage_id in [301,302,304,305]:return {"position":battle_data.exit,"label":"西门出口" if stage_id==301 else "运输车北口" if stage_id==302 else "己方船口" if stage_id==304 else "盐路出口"}
	if stage_id==112:return {"position":battle_data.targets[0],"label":"药车目的地"}
	if stage_id==105:return {"position":battle_data.exit,"label":"北门敌军退路"}
	if stage_id in [101,111,202,211,212]:return {"position":battle_data.exit,"label":"护送出口"}
	return {}

func allowed_world_nodes() -> Array[int]:
	if chapter==5:return ChapterFive.allowed_nodes(self)
	if chapter==4:return ChapterFour.allowed_nodes(self)
	if chapter==3:return ChapterThree.allowed_nodes(self)
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
	previous_world_node=world_node;world_node=node;flags.world_previous=previous_world_node;route_positions[route]=node
	if chapter==5 and flags.get("chapter5_merged",false):
		for side in ["alm","celica"]:route_positions[side]=node;flags.chapter5_previous[side]=previous_world_node
	return true
func stage_for_node(node: int) -> int:
	if chapter==5:return ChapterFive.stage_for_node(self,node)
	if chapter==4:return ChapterFour.stage_for_node(self,node)
	if chapter==3:return ChapterThree.stage_for_node(self,node)
	for key in campaign.stages:
		if int(campaign.stages[key].node)==node and int(stages[int(key)].get("chapter",1))==chapter:return int(key)
	return 0
func world_has_battle(node: int) -> bool:
	var id=stage_for_node(node);return id>0 and not stage_cleared(id) and (chapter!=3 or flags.get("D31_done",false))

func start_battle(id: int=101,_groups: Array=[],_from_hub: bool=false) -> bool:
	if chapter==5 and not ChapterFive.can_start(self,id):return false
	if chapter==4 and (str(stages.get(id,{}).get("route",""))!=route or not allowed_world_nodes().has(world_node)):return false
	if chapter==3 and (not flags.get("D31_done",false) or str(stages.get(id,{}).get("route",""))!=route):return false
	if not stages.has(id) or stage_cleared(id) or int(stages[id].node)!=world_node:return false
	if int(stages[id].get("chapter",2 if id>=200 else 1))!=chapter:return false
	stage_id=id;battle_data=stages[id].duplicate(true);encounter_groups=[]
	Equipment.reconcile(self)
	battle_return={"mode":"world","world_node":world_node,"previous_world_node":previous_world_node};units.clear();var slot=0
	var battle_party=party.duplicate()
	if id in [533,534]:battle_party=ChapterFive.selection(self,"alm").duplicate()+ChapterFive.selection(self,"celica").duplicate()
	var route_slots={"alm":0,"celica":0}
	for member in battle_party:
		if not roster.has(member):continue
		var u: Dictionary=roster[member].duplicate(true)
		if not can_deploy(u):continue
		if slot>=battle_data.player_positions.size():break
		var owner=Casualties.owner({"parties":parties},member)
		var positions=battle_data.player_positions_by_route[owner] if id in [533,534] else battle_data.player_positions
		var local_slot=int(route_slots[owner]) if id in [533,534] else slot
		u.position=positions[local_slot].duplicate();route_slots[owner]+=1;u.hp=int(u.max_hp);u.acted=false;u.side="player";u.player_slot=slot
		u.erase("weapon_index");u.route=owner;units.append(u);slot+=1
		Cover.clear(u)
		MapSkills.clear(u)
	for i in range(battle_data.enemies.size()):
		var u: Dictionary=battle_data.enemies[i].duplicate(true);u.enemy_slot=i;units.append(u)
	for raw in battle_data.npc_units:
		if ((id==112 and str(raw.id)=="hervi") or (id==111 and str(raw.id)=="beck")) and battle_party.has(str(raw.id)):continue
		var u: Dictionary=raw.duplicate(true);u.player_slot=slot;u.route=route
		if not u.get("battle_guard",false):u.move=int(battle_data.get("escort_move",2))
		slot+=1;units.append(u)
	turn=1;phase="player";kills=0;selected_id="";battle_outcome="";battle_settled=false
	flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}
	Medicine.prepare(self,units)
	EnemyBalance.prepare(stage_id,units);MineEscort.prepare(self,units)
	ChapterTwo.initialize(self)
	if chapter==5:ChapterFive.initialize(self)
	elif chapter==4:ChapterFour.initialize(self)
	else:ChapterThree.initialize(self)
	flags.inventory_processed_deaths={}
	mode="battle";cursor=pos(find_unit(leader_id()));log_lines.clear();victory_rewards.clear()
	if stage_id>=500:ChapterFive.before_lines(self)
	elif stage_id>=400:ChapterFour.before_lines(self)
	elif stage_id>=300:ChapterThree.lines(self,ChapterThree.before_lines(self),battle_data.code+"-BEGIN")
	else:queue_lines(ChapterTwo.before_lines(self) if stage_id>=200 else str(battle_data.before),battle_data.code+"-BEGIN")
	if battle_data.has("enemy_role_hint"):queue_lines(str(battle_data.enemy_role_hint),str(battle_data.code)+"-ENEMY-ROLES")
	Battlefield.initialize(self)
	battle_start_snapshot=_capture_battle_start();return true
func retry_battle() -> bool:
	if Training.active(self):return Training.retry(self)
	if battle_start_snapshot.is_empty():return false
	var previous_map_revision=str(battle_data.get("tactical_review_version","0.2.0"))
	var s: Dictionary=battle_start_snapshot.duplicate(true)
	for key in s:
		if key in SAVE_FIELDS and not key in ["hub_position","cursor","move_origin"]:set(key,s[key])
	stage_id=int(s.stage_id);world_node=int(s.world_node);previous_world_node=int(s.previous_world_node)
	cleared_stages=s.cleared_stages.map(func(v):return int(v));battle_data=stages[stage_id].duplicate(true)
	# Restore the genuine pre-battle roster, then redeploy through the ordinary
	# entry path when geometry changed. Old coordinates must not land in a cliff.
	var starting_enemies=s.get("units",[]).filter(func(u):return str(u.side)=="enemy").map(func(u):return str(u.id))
	# Preserve a loaded battle's live formation. A retry redeploys newly authored
	# initial enemies from the restored entry roster rather than spawning mid-turn.
	var added_deployment=battle_data.enemies.any(func(u):return not starting_enemies.has(str(u.id)))
	if previous_map_revision!=str(battle_data.get("tactical_review_version","0.2.0")) or added_deployment:
		return start_battle(stage_id)
	battle_settled=false;battle_outcome="";phase="player";turn=1;kills=0;mode="battle";selected_id="";flags.erase("active_plot")
	cursor=pos(find_unit(leader_id()));victory_rewards.clear();Battlefield.restore(self);Cover.refresh(self);return true

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
		if who in battle_data.get("dialogue_require_speaker_alive",[]) and not speaker_alive(who):continue
		if not speaker_alive(who) and chapter==2:
			var replacement={"米蕾":"地方医者","莉莎":"甲板护卫","卡洛":"固定舵手","洛德":"引航者","罗恩":"渔村长者","希雅":"留守骑士"}
			who=replacement.get(who,"艾琳")
			if fragment.begins_with("卡洛：") and (fragment.contains("报酬") or fragment.contains("这次我去送")):line="卡洛正在接受照护。遗物由我们代为交给家属，等他恢复再继续履行承诺。"
		elif not speaker_alive(who):
			if stage_id==101 and who=="奥托" and line=="我来突破前面的路口。":line="我去看出口，不能再让人把路堵住。"
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
func can_stop(unit: Dictionary,cell: Vector2i) -> bool:
	# Inspect every occupant, including old saves where unit_at may return self
	# before another living unit sharing the cell.
	return not units.any(func(other):return int(other.hp)>0 and not other.get("hidden",false) and other.side!="evacuated" and str(other.id)!=str(unit.id) and pos(other)==cell)

func _safe_escort_move(unit: Dictionary,target: Vector2i) -> Dictionary:
	var action=_toward(unit,target);var safe=pos(unit)
	for step in path_to(unit,action.destination):
		# Forecast the next enemy move and attack, including blockers. A flat
		# four-tile distance lets fast troops intercept an automatic escort.
		if int(RefugeeTactics.evaluate(self,unit,step).incoming)>0:break
		# Allies may be crossed, but a route shortened by danger still needs an
		# empty landing cell. Otherwise the escort disappears under its ally.
		if can_stop(unit,step):safe=step
	action.destination=safe
	if safe==pos(unit):
		var retreat=RefugeeTactics.disengage(self,unit)
		if not retreat.is_empty():return retreat
	return action

func _repair_overlapped_escorts() -> void:
	if mode!="battle" or not battle_outcome.is_empty():return
	# Older safe-route truncation could save two friendly units on one cell.
	# Keep earlier units in place and move only the later automatic escort.
	var ordered=units.duplicate();ordered.reverse()
	for unit in ordered:
		if int(unit.hp)<=0 or unit.side!="player" or unit.get("hidden",false) or unit.get("locked",false):continue
		if not unit.get("neutral",false) or unit.get("controllable",true):continue
		if str(unit.get("quest_kind","")) not in ["escort","medicine","prisoner","patient","sailor"]:continue
		var occupants=units.filter(func(other):return int(other.hp)>0 and not other.get("hidden",false) and other.side!="evacuated" and str(other.id)!=str(unit.id) and pos(other)==pos(unit))
		if occupants.is_empty() or occupants.any(func(other):return other.side!=unit.side):continue
		var graph=reachable(unit);var cells=graph.costs.keys();var enemies=living("enemy")
		cells.sort_custom(func(a,b):
			if int(graph.costs[a])!=int(graph.costs[b]):return int(graph.costs[a])<int(graph.costs[b])
			var distance_a=999999;var distance_b=999999
			for enemy in enemies:
				distance_a=mini(distance_a,absi(pos(enemy).x-a.x)+absi(pos(enemy).y-a.y))
				distance_b=mini(distance_b,absi(pos(enemy).x-b.x)+absi(pos(enemy).y-b.y))
			if distance_a!=distance_b:return distance_a>distance_b
			return a.y<b.y if a.y!=b.y else a.x<b.x)
		for cell in cells:
			if not can_stop(unit,cell) or movement_cost(unit,cell)>=255:continue
			unit.position=[cell.x,cell.y];break

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
	return ChapterThree.held_captive(self,unit) or (stage_id in [103,105,202,205] and bool(unit.get("neutral",false)) and bool(unit.get("locked",false)) and str(unit.get("quest_kind","")) in ["escort","prisoner","witness"])

func _prepare_prison_rescue(actors: Array,released: bool=false) -> void:
	if stage_id!=103:return
	for unit in actors:
		if str(unit.id)!="lena" or not unit.get("neutral",false) or unit.get("controllable",true):continue
		if str(unit.get("quest_kind","")) not in ["witness","escort"]:continue
		# Older saves unlocked the cell but kept the witness AI's permanent wait.
		# Preserve HP/action/position and the post-battle invitation; release only
		# the live rescued NPC, never the still-locked retry snapshot.
		unit.quest_kind="escort"
		if released:unit.locked=false

func living(side: String) -> Array:
	var result=super.living(side)
	if _guard_target_context and side=="player":return result.filter(func(u):return not _held_captive(u))
	return result

func can_attack(unit: Dictionary,other: Dictionary) -> bool:
	if stage_id==112 and Medicine.is_staff(other):return false
	# A held captive belongs to the guard's own prison detail until released.
	# This controls target intent only; HP, damage and position stay ordinary.
	if unit.get("side","")=="enemy" and _held_captive(other):return false
	return super.can_attack(unit,other)

func ai_action(unit: Dictionary,gather: bool=false) -> Dictionary:
	var previous_context=_guard_target_context
	_guard_target_context=(stage_id in [103,105,202,205] or stage_id>=300) and unit.get("side","")=="enemy"
	var action=_campaign_ai_action(unit,gather)
	_guard_target_context=previous_context
	return action

func _campaign_ai_action(unit: Dictionary,gather: bool=false) -> Dictionary:
	if Training.active(self):return super.ai_action(unit,gather)
	var battlefield_action=Battlefield.action(self,unit,gather)
	if not battlefield_action.is_empty():return battlefield_action
	if stage_id==112 and Medicine.is_staff(unit):return {"destination":pos(unit),"target":""}
	if MineEscort.applies(self,unit):return MineEscort.action(self,unit,gather)
	var role_action=EnemyRoles.action(self,unit,gather)
	if not role_action.is_empty():return role_action
	if unit.get("quest_kind","") in ["escort","medicine","prisoner","patient","sailor"] and not unit.get("locked",false):
		if living("enemy").is_empty() and (battle_data.reinforcements.is_empty() or flags.quest.get("reinforced",false)):
			unit.move=maxi(5,int(unit.move))
	if stage_id>=400:
		var fourth_override=ChapterFour.ai_action(self,unit)
		if not fourth_override.is_empty():return fourth_override
	if stage_id>=300 and stage_id<400:
		var third_override=ChapterThree.ai_action(self,unit)
		if not third_override.is_empty():return third_override
	if stage_id>=200:
		var override=ChapterTwo.ai_action(self,unit)
		if not override.is_empty():return override
	if unit.has("quest_kind"):
		if bool(unit.get("locked",false)) or str(unit.quest_kind)=="witness":return {"destination":pos(unit),"target":""}
		# The two armed M11 refugees can fight during their automatic friendly
		# action. Keep escort routing when no attack is available this turn.
		if (stage_id==101 and not gather and unit.get("side","")=="player"
			and bool(unit.get("neutral",false)) and str(unit.quest_kind)=="escort"
			and str(unit.id) in ["M11_refugees0","M11_refugees1"]
			and pos(unit)!=Vector2i(battle_data.exit[0],battle_data.exit[1])):
			var attack=RefugeeTactics.safe_attack(self,unit)
			if not str(attack.get("target","")).is_empty():return attack
			var retreat=RefugeeTactics.disengage(self,unit)
			if not retreat.is_empty():return retreat
		var target=Vector2i(battle_data.exit[0],battle_data.exit[1])
		if str(unit.quest_kind)=="medicine":target=Vector2i(battle_data.targets[0][0],battle_data.targets[0][1])
		return _safe_escort_move(unit,target)
	if bool(unit.get("burner",false)):
		if turn<int(battle_data.get("burner_departure_turn",5)):return {"destination":pos(unit),"target":""}
		return _toward(unit,Vector2i(battle_data.targets[0][0],battle_data.targets[0][1]))
	if str(unit.id)=="M15_boss" and ((turn>=6 and int(unit.hp)*2<int(unit.max_hp)) or turn>=8):
		if not flags.quest.get("escape_announced",false):flags.quest.escape_announced=true;queue_lines("科兰：去北门！撤离点就在旧塔后面。","M15-ESCAPE")
		return _toward(unit,Vector2i(battle_data.exit[0],battle_data.exit[1]))
	if bool(unit.get("offering_surrender",false)):return {"destination":pos(unit),"target":""}
	var ranged=CampaignTactics.action(self,unit,gather)
	if not ranged.is_empty():return ranged
	return super.ai_action(unit,gather)
func apply_ai_special(caster: Dictionary,action: Dictionary) -> Dictionary:
	if str(action.get("special",""))=="battlefield_release":return Battlefield.apply_special(self,caster,action)
	if str(action.get("special","")) in ["campaign_blink","campaign_summon"]:return EnemyRoles.apply_special(self,caster,action)
	return super.apply_ai_special(caster,action)

func commit_strike(event: Dictionary) -> void:
	# Even a missed arrow reveals an attack. Remember it before phase recovery
	# can erase a small wound, without changing damage or granting a counter.
	var target=find_unit(str(event.get("defender","")))
	var target_hp=int(target.get("hp",0))
	var source=find_unit(str(event.get("attacker","")))
	if source.get("side","")=="player" and target.get("side","")=="enemy" and str(target.get("behavior","")) in ["guard","guard_exit"]:
		target.guard_alerted=true
		target.guard_ai_revision=2
	super.commit_strike(event)
	Battlefield.record_damage(self,str(target.get("id","")),maxi(0,target_hp-int(target.get("hp",0))))
	var cover:Dictionary=event.get("cover",{})
	if not cover.is_empty():
		var guard=find_unit(str(cover.unit))
		Cover.clear(guard)
		super.commit_strike({"attacker":str(event.attacker),"defender":str(cover.unit),"hp_after":int(cover.hp_after)})
		log_lines.append(str(guard.get("name_zh","同伴"))+"掩护分担"+str(int(cover.damage))+"伤害")
	Cover.refresh(self)

func plan_cover_damage(target:Dictionary,damage:int,shadow:Dictionary)->Dictionary:
	return Cover.split(self,target,damage,shadow)

func cover_targets(actor:Dictionary)->Array:
	return Cover.targets(self,actor)

func begin_cover(target_id:String)->bool:
	return Cover.start(self,find_unit(selected_id),target_id)

func apply_tactical_damage(source:Dictionary,target:Dictionary,damage:int,kind:String)->Dictionary:
	if int(target.get("hp",0))<=0:return {}
	var cover=Cover.split(self,target,maxi(0,damage),{})
	var remaining=int(cover.get("remaining_damage",maxi(0,damage)))
	var before=int(target.hp)
	var event={"attacker":str(source.id),"defender":str(target.id),"hit":true,"critical":false,
		"damage":mini(before,remaining),"hp_before":before,"hp_after":maxi(0,before-remaining),"cover":cover,
		"kind":kind,"source_hp_before":int(source.hp),"source_hp_after":int(source.hp)}
	commit_strike(event)
	return event

func use_support(caster_id:String,spell_id:int,target_id:String="",destination:Vector2i=Vector2i(-1,-1))->Dictionary:
	var result=super.use_support(caster_id,spell_id,target_id,destination)
	if not result.is_empty() and not Training.active(self) and str(result.action) in ["recover","physic","fortify"]:
		var caster=find_unit(caster_id);var restored=0
		for change in result.changed:restored+=maxi(0,int(change.get("after",0))-int(change.get("before",0)))
		if caster.get("side","")=="player" and party.has(caster_id) and not caster.get("temporary",false) and not caster.get("neutral",false):
			var gain=Rules.healing_experience_gain(caster,restored)
			if gain>0:
				# Commit HP, action cost and EXP together. Reloading cannot re-award
				# the already consumed action; the UI presents this receipt later.
				result.source_hp_after_support=int(caster.hp)
				result.reward=CampaignExperience.award(self,caster,gain)
				result.reward.victory_training=false;result.reward.support_training=true
	Cover.refresh(self)
	return result

func mark_wait(id: String) -> void:
	super.mark_wait(id);var u=find_unit(id)
	Cover.refresh(self)
	if u.is_empty():return
	if Training.active(self):check_outcome();return
	if stage_id>=400 and stage_id<500:ChapterFour.after_wait(self,u)
	elif stage_id>=300:ChapterThree.after_wait(self,u)
	if stage_id>=200:ChapterTwo.after_wait(self,u)
	if u.has("quest_kind") and str(u.quest_kind) in ["escort","medicine"]:
		var goal=battle_data.targets[0] if str(u.quest_kind)=="medicine" else battle_data.exit
		if pos(u)==Vector2i(goal[0],goal[1]):
			if not flags.quest.evacuated.has(id):flags.quest.evacuated.append(id)
			u.side="evacuated";u.hidden=true
			if stage_id>=300:ChapterThree.lines(self,"居民：接应的人到了。我们先到安全处等候。",str(battle_data.code)+"-EVACUEE")
			else:queue_lines(str(battle_data.during),str(battle_data.code)+"-MID")
	if bool(u.get("burner",false)) and turn>=int(battle_data.get("burner_departure_turn",5)):
		var goal=Vector2i(battle_data.targets[0][0],battle_data.targets[0][1])
		flags.quest.burn_streak=int(flags.quest.burn_streak)+1 if pos(u)==goal else 0
		if int(flags.quest.burn_streak)==1:queue_lines("战场提示：敌方已在粮仓门前点火一次。若敌方连续两次在粮仓门前点火，战斗失败。／胡纳普：快拦住拿火把的人，别让火烧进仓里！","M12-BURN")
	check_outcome()
func next_phase() -> void:
	if not battle_outcome.is_empty():return
	MapSkills.expire_after_player_phase(self)
	if Training.active(self):
		Training.before_phase(self);super.next_phase();Cover.refresh(self,phase=="player");check_outcome();return
	ChapterTwo.before_phase(self)
	if not battle_outcome.is_empty():return
	var object_hp={}
	for unit in units:
		if unit.get("event_object",false):object_hp[str(unit.id)]=int(unit.hp)
	super.next_phase()
	Cover.refresh(self,phase=="player")
	for id in object_hp:find_unit(id).hp=object_hp[id]
	ChapterTwo.after_phase(self)
	if stage_id>=500:ChapterFive.after_phase(self)
	elif stage_id>=400:ChapterFour.after_phase(self)
	elif stage_id>=300:ChapterThree.after_phase(self)
	if phase=="player" and stage_id==102 and turn==int(battle_data.get("burner_departure_turn",5))-1:queue_lines("战场提示：焚毁兵下一回合从集合点出发。若敌方连续两次在粮仓门前点火，战斗失败。","M12-FIRE-WARNING")
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
			u.enemy_slot=units.filter(func(z):return str(z.side)=="enemy").size()
			if stage_id==103:EnemyBalance.prepare(stage_id,[u])
			units.append(u)
	if phase=="player" and turn==maxi(1,int(battle_data.reinforcement_turn)-1) and int(battle_data.reinforcement_turn)>0:
		queue_lines("斥候：后方路口有援军。下一回合抵达，只有这一队。",str(battle_data.code)+"-REINFORCEMENT-WARNING")
	Battlefield.after_phase(self)
	check_outcome()

func visit_fronts(object: Dictionary) -> Array:
	var points: Array=object.get("approaches",[object.approach] if object.has("approach") else [])
	return points.map(func(p):return Vector2i(p[0],p[1]))

func escort_hint(unit: Dictionary) -> String:
	if str(unit.get("quest_kind",""))!="medicine":return "自动护送"
	if unit.get("hidden",false) or unit.side=="evacuated":return "药车已交付"
	# The hover card asks on every draw. Snapshot the small tactical state,
	# never rerun pathfinding/threat scans until something relevant changes.
	var stamp=[stage_id,turn,phase,str(unit.id),battle_data.map.tiles.hash(),JSON.stringify(battle_data.targets),JSON.stringify(flags.get("quest",{}))]
	for actor in units:
		var row=[]
		for field in ["id","side","hp","max_hp","class_id","item_id","move","strength","defence","resistance","speed","skill","luck","magic_flags","weapon_index","body_attack","hidden","locked","acted"]:row.append(actor.get(field,null))
		row.append(pos(actor));stamp.append(row)
	if stamp==_escort_hint_stamp:return _escort_hint_value
	var destination=Vector2i(battle_data.targets[0][0],battle_data.targets[0][1])
	var action=_safe_escort_move(unit,destination);var hint="运药员送药 · 自动前进"
	if action.get("reason","")=="escort_disengage":hint="避开敌锋 · 暂向后撤"
	elif action.destination==pos(unit) and pos(unit)!=destination:
		hint="前路受阻 · 请让路" if _toward(unit,destination).destination==pos(unit) else "敌军可达 · 等待清路"
	_escort_hint_stamp=stamp;_escort_hint_value=hint
	return hint

func interaction_hint(cell: Vector2i) -> Dictionary:
	var tactical_hint=Battlefield.hint(self,cell)
	if not tactical_hint.is_empty():return tactical_hint
	# Read the same objects/approaches as interactions_for, without selecting an
	# actor, mutating follows_unit positions, consuming RNG or awarding anything.
	var modules=battle_data.get("art_modules",[])
	for object in battle_data.get("objects",[]):
		var p=Vector2i(object.position[0],object.position[1])
		if object.has("follows_unit"):
			var followed=find_unit(str(object.follows_unit))
			if not followed.is_empty():p=pos(followed)
		var kind=str(object.get("kind",""))
		var matches=cell==p or visit_fronts(object).has(cell)
		for point in object.get("entrance_cells",[]):
			if cell==Vector2i(point[0],point[1]):matches=true
		if kind=="visit":
			for module in modules:
				var cells=module.get("cells",[])
				if cells.any(func(point):return Vector2i(point[0],point[1])==p) and cells.any(func(point):return Vector2i(point[0],point[1])==cell):matches=true
		if not matches:continue
		var done=flags.get("quest",{}).get("objects",{}).get(str(object.id),false)
		if stage_id==405:done=flags.get("quest",{}).get("wells",{}).get(str(object.id),false)
		if stage_id in [406,411] and flags.get("quest",{}).get("record_lost",false) and object.id in ["observatory_record","black_register"]:
			return {"object_id":str(object.id),"text":"记录已焚毁","available":false}
		if done:return {"object_id":str(object.id),"text":"已访问" if kind=="visit" else "已完成","available":false}
		var text="可访问 · 门前行动" if kind=="visit" else "可占领 · 格上行动" if kind=="occupy" else "可开门 · 邻格行动" if kind=="door" else "可救援 · 邻格行动" if kind=="rescue" else "可交互 · 行动菜单"
		return {"object_id":str(object.id),"text":text,"available":true}
	for module in modules:
		if module.get("cells",[]).any(func(point):return Vector2i(point[0],point[1])==cell):return {"text":"仅作地形","available":false}
	return {}

func interactions_for(unit: Dictionary) -> Array:
	var result=[]
	if unit.is_empty() or unit.side!="player" or not bool(unit.get("controllable",true)) or bool(unit.get("acted",false)):return result
	if Training.active(self):
		if pos(unit)==Vector2i(battle_data.training_target[0],battle_data.training_target[1]):result.append(battle_data.objects[0])
		return result
	result.append_array(Battlefield.interactions_for(self,unit))
	if stage_id>=400 and stage_id<500:result.append_array(ChapterFour.extra_interactions(self,unit))
	elif stage_id>=300:result.append_array(ChapterThree.extra_interactions(self,unit))
	for obj in battle_data.objects:
		if stage_id in [406,411] and flags.quest.get("record_lost",false) and obj.id in ["observatory_record","black_register"]:continue
		if obj.has("follows_unit"):
			var followed=find_unit(str(obj.follows_unit))
			if not followed.is_empty():obj.position=followed.position.duplicate()
		if flags.quest.objects.get(str(obj.id),false):continue
		if obj.has("approach") or obj.has("approaches"):
			if visit_fronts(obj).has(pos(unit)):result.append(obj)
			continue
		var p=Vector2i(obj.position[0],obj.position[1]);var d=absi(p.x-pos(unit).x)+absi(p.y-pos(unit).y)
		if d==0 or (obj.adjacent and d==1):result.append(obj)
	var boss=find_unit(str(battle_data.boss_id))
	if not boss.is_empty() and bool(boss.get("offering_surrender",false)) and absi(pos(boss).x-pos(unit).x)+absi(pos(boss).y-pos(unit).y)==1:result.append({"id":"surrender","label":"接受投降"})
	return result
func interact(id: String) -> bool:
	if Training.active(self):
		var done=Training.interact(self,id)
		if done:Cover.refresh(self)
		return done
	var actor=find_unit(selected_id);var choices=interactions_for(actor)
	if not choices.any(func(o):return str(o.id)==id):return false
	var object=choices.filter(func(o):return str(o.id)==id)[0]
	if str(object.get("kind",""))=="breakable":return Battlefield.interact(self,id)
	if str(object.get("kind",""))=="visit":
		var reward=int(object.get("reward_item",0));var receipt={}
		if reward>0:
			if int(actor.get("item_id",0))==0 and Items.can_use(actor,reward):
				roster[actor.id].item_id=reward
				receipt={"valid":true,"destination":"unit","recipient":actor.id}
			else:receipt=receive_equipment(reward)
			if not bool(receipt.valid):
				queue_lines("旁白：运输队已满。整理装备后，可以再来领取。")
				return false
			if str(receipt.destination)=="unit":
				var recipient=find_unit(str(receipt.recipient))
				if not recipient.is_empty():recipient.item_id=reward
		flags.quest.objects[id]=true
		queue_lines(str(object.dialogue),id+"-VISIT")
		if reward>0:
			var destination=str(roster[receipt.recipient].name_zh)+"装备" if str(receipt.destination)=="unit" else "收入运输队"
			queue_lines("旁白：获得"+str(Items.item(reward).name_zh)+"，"+destination+"。",id+"-REWARD")
		actor.acted=true;selected_id="";check_outcome();return true
	if stage_id>=500:
		ChapterFive.interact(self,id)
		actor.acted=true;selected_id="";check_outcome();return true
	if stage_id>=400:
		ChapterFour.interact(self,id)
		actor.acted=true;selected_id="";check_outcome();return true
	if stage_id>=300:
		ChapterThree.interact(self,id)
		actor.acted=true;selected_id="";check_outcome();return true
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
				var x=int(o.position[0]);var y=int(o.position[1]);battle_data.map.tiles[y*int(battle_data.map.width)+x]=int(o.get("open_tile",208))
				for u in units:
					if str(u.id)==str(battle_data.code)+"_workers"+str(index) or (u.id=="lena" and index==0):u.locked=false
				queue_lines("劳工：门开了。我们沿着清出的路撤离。",id+"-OPEN")
				if index==0:queue_lines(str(battle_data.during),str(battle_data.code)+"-MID")
			if o.kind=="occupy":queue_lines(str(battle_data.during),"M12-MID")
			if o.kind=="tools" and not flags.get("tools_reward",false):convoy.alm.append(2);flags.tools_reward=true
	actor.acted=true;selected_id="";check_outcome();return true

func check_outcome() -> String:
	Cover.refresh(self)
	if Training.active(self):return Training.check_outcome(self)
	if battle_outcome=="defeat":return battle_outcome
	if stage_id>=500:return ChapterFive.check_outcome(self)
	if stage_id>=400:return ChapterFour.check_outcome(self)
	if stage_id>=300:return ChapterThree.check_outcome(self)
	if stage_id>=200:return ChapterTwo.check_outcome(self)
	var leader=find_unit(leader_id());var q: Dictionary=flags.get("quest",{})
	if not leader.is_empty() and int(leader.hp)<=0:return _fail("胡纳普濒死，无法继续作战")
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
		101:ready=q.get("evacuated",[]).size()>=2
		111:ready=q.get("evacuated",[]).has("S11_miners0") and q.get("evacuated",[]).has("S11_miners1")
		102,104:ready=battle_data.objects.filter(func(o):return not bool(o.get("optional",false))).all(func(o):return bool(q.get("objects",{}).get(str(o.id),false)))
		103:ready=battle_data.objects.filter(func(o):return str(o.kind) in ["door","rescue"]).all(func(o):return bool(q.get("objects",{}).get(str(o.id),false))) and workers.any(func(u):return not bool(u.get("locked",false)))
		105:ready=workers.any(func(u):return not bool(u.get("locked",false)))
		112:ready=q.get("evacuated",[]).has("medicine_wagon")
	if defeated and ready:battle_outcome="victory"
	return battle_outcome
func _fail(reason: String) -> String:flags.quest.failed_reason=reason;battle_outcome="defeat";return battle_outcome
func story_on_death(unit: Dictionary) -> void:
	if Training.active(self):return
	if not Casualties.owner({"parties":parties},str(unit.id)).is_empty():
		Casualties.enter_dying(self,unit)
		return
	if unit.id in characters and bool(unit.get("neutral",false)):
		var dead=_initial_character(unit.id);dead.hp=0;dead.dead=true;roster[unit.id]=dead
func story_on_victory() -> void:
	if Training.active(self):return
	if stage_id>=500:
		ChapterFive.on_victory(self);Equipment.award_clear(self,stage_id);return
	if stage_id>=400:
		ChapterFour.on_victory(self)
		if stage_id!=411 or flags.get("S41_register_saved",false):Equipment.award_clear(self,stage_id)
		return
	if stage_id>=300:
		ChapterThree.on_victory(self);Equipment.award_clear(self,stage_id);return
	if stage_id>=200:
		ChapterTwo.on_victory(self);Equipment.award_clear(self,stage_id);return
	flags["clear_"+str(battle_data.code)]=true
	if stage_id==101:flags.side_invites=true
	if stage_id==103:flags.labor_rescued=true
	if stage_id==105:queue_pages(campaign.scenes.D13,"D13");flags.korlan_defeated=true
	if stage_id in [104,105]:
		for unit in living("enemy"):
			unit.side="neutral";unit.surrendered=true;unit.no_counter=true
	var after=str(battle_data.after).split(" M12-MYTH")[0]
	if stage_id==104 and not units.any(func(u):return int(u.hp)>0 and bool(u.get("surrendered",false))):
		after=str(battle_data.get("after_no_survivors",after))
	if stage_id in [111,112]:
		var companion="beck" if stage_id==111 else "hervi"
		if not party.has(companion) and speaker_alive(str(characters[companion].name_zh)):
			var fragments=after.split("／")
			for page in campaign.scenes[str(battle_data.code)+"_COMPANION_AFTER"]:
				fragments.insert(fragments.size()-1 if stage_id==112 else fragments.size(),str(page.speaker)+"："+str(page.text))
			after="／".join(fragments)
	queue_lines(after,str(battle_data.code)+"-END")
	if stage_id==111 and not flags.get("S11_reward",false):convoy.alm.append(11);flags.S11_reward=true
	Equipment.award_clear(self,stage_id)

func complete_battle() -> bool:
	if Training.active(self):return Training.complete(self)
	if battle_outcome!="victory" or battle_settled:return false
	if stage_id==112:
		var clinic_npc=find_unit("hervi")
		if not clinic_npc.is_empty() and int(clinic_npc.hp)<=0:flags.clinic_hervi_unavailable=true
	victory_rewards.clear()
	for unit in units:
		if unit.side!="player" or unit.get("temporary",false) or unit.get("neutral",false):continue
		if Casualties.owner({"parties":parties},str(unit.id)).is_empty():continue
		if int(unit.hp)<=0:
			Casualties.enter_dying(self,unit)
			Inventory.on_death(self,unit)
		else:
			var gain=Rules.victory_experience_gain(unit)
			if int(unit.level)<20 and not unit.get("no_experience",false):gain+=int(stages[stage_id].get("clear_training_exp",0))
			if gain>0:victory_rewards.append(CampaignExperience.award(self,unit,gain))
		var persistent: Dictionary=unit.duplicate(true)
		Cover.clear(persistent)
		MapSkills.clear(persistent)
		persistent.dead=false;persistent.acted=false;Casualties.initialize_unit(persistent)
		roster[str(unit.id)]=persistent
	if not stage_cleared(stage_id):cleared_stages.append(stage_id)
	battle_settled=true
	Scenario.on_victory(self);Inventory.on_victory(self)
	parties[route]=party.duplicate()
	_restore_preparation_hp()
	ensure_treatment_sources()
	return true

func return_to_preparation() -> bool:
	if Training.active(self):return Training.leave(self)
	if not retry_battle():return false
	world_node=15 if stage_id in [533,534] else previous_world_node;route_positions[route]=world_node;story_events.clear();mode="world";battle_outcome="";selected_id=""
	if stage_id in [533,534]:route_positions={"alm":15,"celica":15};flags.chapter5_previous={"alm":15,"celica":15};previous_world_node=15
	Equipment.reconcile(self)
	return true

func support_targets(caster: Dictionary,spell_id: int) -> Array:
	return super.support_targets(caster,spell_id).filter(func(u):return not bool(u.get("event_object",false)))

func finish_exchange(exchange: Dictionary) -> Dictionary:
	Cover.refresh(self)
	var pushed=Knockback.apply_exchange(self,exchange)
	if pushed.get("valid",false):
		Cover.refresh(self)
		queue_lines("战场提示："+str(find_unit(str(pushed.target)).get("name_zh","目标"))+"被击退一格。")
	var reward=super.finish_exchange(exchange)
	if stage_id==105 and str(exchange.get("defender",""))=="M15_boss":queue_lines(str(battle_data.during),"M15-MID")
	if stage_id==205 and (str(exchange.get("defender",""))==str(battle_data.boss_id) or str(exchange.get("attacker",""))==str(battle_data.boss_id)):
		if campaign.scenes.has("D22_FIRST"):queue_pages(campaign.scenes.D22_FIRST,"D22-FIRST")
		else:queue_lines(str(battle_data.during),"F25-MID")
	return reward

func save_game() -> bool:
	if mode=="title" or flags.is_empty():return false
	ensure_treatment_sources()
	var state={"schema":3,"campaign_id":CAMPAIGN_ID,"hub_record":hub_record}
	state.journal={"saved_unix":int(Time.get_unix_time_from_system()),"play_seconds":play_seconds}
	state.map_revision=str(battle_data.get("tactical_review_version","0.2.0"))
	for key in SAVE_FIELDS:
		var value=get(key);state[key]=[value.x,value.y] if value is Vector2i else value
	# Never replace a usable checkpoint with a state the loader cannot resume.
	# Validate the actual JSON representation: runtime dictionary keys may be
	# StringName values, which JSON correctly converts to ordinary strings.
	var contents=JSON.stringify(state)
	if not SaveValidation.campaign_valid(self,JSON.parse_string(contents),SAVE_FIELDS):return false
	# Preserve schema-1/2 originals, including an older recovered backup that
	# would otherwise be rotated away by a later successful save.
	var upgrading=_casualty_legacy_path in [save_path,save_path+".bak"]
	if upgrading and FileAccess.file_exists(_casualty_legacy_path) and not FileAccess.file_exists(save_path+".pre-casualty.bak"):
		if not _copy_checkpoint_atomic(_casualty_legacy_path,save_path+".pre-casualty.bak"):return false
	var file=FileAccess.open(save_path+".tmp",FileAccess.WRITE)
	if file==null:return false
	file.store_string(contents);file.flush()
	var write_error=file.get_error();file.close()
	if write_error!=OK:return false
	if FileAccess.file_exists(save_path):
		# The recovery copy has the same atomic-replace guarantee as the main
		# journal. An interrupted copy must not destroy the previous backup.
		if SaveValidation.campaign_valid(self,read_json(save_path),SAVE_FIELDS):
			if not _copy_checkpoint_atomic(save_path,save_path+".bak"):return false
		else:
			# Recovery is visible in the slot picker; retain the damaged original
			# before normal autosaves replace it. Content-addressing avoids loss
			# of a different corrupt record on a subsequent recovery.
			var preserved=save_path+".damaged-"+FileAccess.get_sha256(save_path).left(16)
			if not FileAccess.file_exists(preserved) and not _copy_checkpoint_atomic(save_path,preserved):return false
	var saved=DirAccess.rename_absolute(ProjectSettings.globalize_path(save_path+".tmp"),ProjectSettings.globalize_path(save_path))==OK
	if saved and upgrading:_casualty_legacy_path=""
	return saved

func _copy_checkpoint_atomic(source: String,destination: String) -> bool:
	var temporary=destination+".tmp"
	if DirAccess.copy_absolute(ProjectSettings.globalize_path(source),ProjectSettings.globalize_path(temporary))!=OK:return false
	return DirAccess.rename_absolute(ProjectSettings.globalize_path(temporary),ProjectSettings.globalize_path(destination))==OK

func load_game() -> bool:
	var s=read_json(save_path)
	if not SaveValidation.campaign_valid(self,s,SAVE_FIELDS):return false
	var previous_schema=int(s.schema)
	if int(s.schema)<3:
		Casualties.migrate(s)
		if not SaveValidation.campaign_valid(self,s,SAVE_FIELDS):return false
	HeroProfessions.upgrade_checkpoint(s)
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
			if str(unit.id)=="M11_boss":unit.name_zh="追击队长";unit.objective_boss=true
	hub_record=str(s.get("hub_record","H01"));battle_data=stages[stage_id].duplicate(true)
	# In-progress battles retain their geometry until a normal retry/re-entry.
	# New walls and cargo must never appear underneath an old saved formation.
	var saved_revision=str(s.get("map_revision","0.2.0"))
	if saved_revision!=str(battle_data.get("tactical_review_version","0.2.0")) and mode in ["battle","victory","defeat"]:
		battle_data=SaveValidation.campaign_stage(self,stage_id,saved_revision).duplicate(true)
	# Current chapter-one prose is independent of saved terrain geometry.
	if chapter==1:
		for field in ["before","during","after","after_no_survivors","absent_branch","dialogue_require_speaker_alive"]:
			if stages[stage_id].has(field):battle_data[field]=stages[stage_id][field].duplicate(true) if stages[stage_id][field] is Array else stages[stage_id][field]
	for o in battle_data.objects:
		if flags.get("quest",{}).get("objects",{}).get(str(o.id),false):
			if stage_id>=200:ChapterTwo.open_object(self,o)
			elif o.kind in ["door","rescue"]:battle_data.map.tiles[int(o.position[1])*int(battle_data.map.width)+int(o.position[0])]=int(o.get("open_tile",208))
	if stage_id==302:
		for o in battle_data.objects:
			if o.has("follows_unit"):
				var followed=find_unit(str(o.follows_unit))
				if not followed.is_empty():o.position=followed.position.duplicate()
	if stage_id==408 and flags.get("quest",{}).get("transfer_cut_snapshot",false):battle_data.reinforcements=[];battle_data.reinforcement_turn=0
	if stage_id==404 and flags.get("quest",{}).get("mid_done",false) and find_unit(str(battle_data.boss_id)).get("surrendered",false):battle_data.reinforcements=[]
	if mode not in ["battle","victory","defeat"]:Equipment.reconcile(self)
	# Older peaceful checkpoints retained the last battle's wounds until the
	# next deployment. Active fights and unprocessed results keep their HP.
	if mode in ["hub","world","chapter_end","ending"] or (mode=="victory" and battle_settled):_restore_preparation_hp()
	var clinic_changed=Medicine.prepare(self,units)
	Medicine.prepare(self,battle_start_snapshot.get("units",[]))
	var beck_changed=MineEscort.applies(self,find_unit("beck")) and str(find_unit("beck").get("quest_kind",""))=="witness"
	for actors in [units,battle_start_snapshot.get("units",[])]:
		EnemyBalance.prepare(stage_id,actors);MineEscort.prepare(self,actors)
	_prepare_prison_rescue(units,bool(flags.get("quest",{}).get("objects",{}).get("M13_door_0",false)))
	_prepare_prison_rescue(battle_start_snapshot.get("units",[]))
	if beck_changed and mode=="battle":queue_lines("战场提示：贝克会随矿工自动推进，并在安全时提供弓援；战后存活可邀请同行。他不替代两组矿工的撤离目标。","S11-BECK-DUTY")
	if clinic_changed and mode=="battle":
		queue_lines("战场提示：赫维在北岸诊所核对药单、照护伤者。药车由运药员护送，清路后会在友军行动时前进。","S12-CLINIC-DUTY")
	_repair_overlapped_escorts()
	Battlefield.restore(self)
	Cover.refresh(self)
	_casualty_legacy_path=save_path if previous_schema<3 else ""
	var journal=s.get("journal",{})
	var seconds=journal.get("play_seconds",0.0) if journal is Dictionary else 0.0
	play_seconds=maxf(0.0,float(seconds)) if seconds is float or seconds is int else 0.0
	return true

func slot_records() -> Array:
	var result=[]
	for slot in range(1,Journals.COUNT+1):result.append(Journals.info(self,slot))
	return result

func save_to_slot(slot: int) -> bool:
	var target=Journals.path_for(slot_directory,slot)
	if target.is_empty():return false
	var previous=save_path
	save_path=target
	if not save_game():save_path=previous;return false
	active_slot=slot
	return true

func load_slot(slot: int) -> bool:
	if slot<1 or slot>Journals.COUNT:return false
	var record=Journals.info(self,slot)
	if not record.valid:return false
	var previous=save_path
	save_path=record.path
	if not load_game():save_path=previous;return false
	active_slot=slot
	# Subsequent auto-saves go to the chosen journal, leaving old saves intact.
	save_path=Journals.path_for(slot_directory,slot)
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
	Equipment.reconcile(self)
	return true

func finish_chapter_two() -> bool:
	if chapter!=2 or route!="celica" or not stage_cleared(206) or flags.get("chapter2_complete",false):return false
	parties.celica=party.duplicate();previous_world_node=world_node;world_node=6;route_positions.celica=6;flags.world_previous=previous_world_node
	flags.chapter2_complete=true;flags.chapter3_pending=true
	mode="chapter_end";selected_id="";return true

func event_boats() -> Array:return ChapterTwo.event_boats(self)

func recruit(id: String) -> void:
	if id=="hervi" and not party.has(id) and not can_invite_hervi():return
	if id=="celine" and not flags.get("celine_ready",false):return
	if id in ["german","noya"] and not flags.get("chapter3_recruits",{}).get(id,false):return
	if id in ["lord","roan","shia"] and not flags.get("east_recruit_ready",{}).get(id,false):return
	var already_joined=parties.get("alm",[]).has(id) or parties.get("celica",[]).has(id)
	super.recruit(id)
	if roster.has(id):roster[id].route=route
	Equipment.reconcile(self)
	if not already_joined and party.has(id):character_recruited.emit(id)

func can_invite_hervi() -> bool:
	var member=roster.get("hervi",{})
	var npc=find_unit("hervi") if stage_id==112 else {}
	return stage_cleared(112) and bool(flags.get("clinic_staffed",false)) and not bool(flags.get("clinic_hervi_unavailable",false)) and (npc.is_empty() or int(npc.hp)>0) and not bool(member.get("dead",false)) and not is_dying(member)

func objective_status() -> Array[String]:
	if Training.active(self):return Training.status(self)
	var tactical=Battlefield.status(self)
	if stage_id>=500:return ChapterFive.status(self)+tactical
	if stage_id>=400:return ChapterFour.status(self)+tactical
	if stage_id>=300:return ChapterThree.status(self)+tactical
	if stage_id>=200:return ChapterTwo.status(self)+tactical
	var result: Array[String]=[str(battle_data.get("goal","完成战场目标"))]
	var q: Dictionary=flags.get("quest",{})
	if not q.get("failed_reason","").is_empty():result.append(str(q.failed_reason))
	return result

func receive_equipment(item_id: int) -> Dictionary:
	var definition=Items.item(item_id)
	if item_id<=0 or definition.get("kind","") not in ["weapon","accessory"]:return {"valid":false,"reason":"unsupported_item"}
	for id in party:
		var recipient: Dictionary=roster.get(id,{})
		if not can_deploy(recipient):continue
		if int(recipient.get("item_id",0))==0 and Items.can_use(recipient,item_id):
			recipient.item_id=item_id
			return {"valid":true,"destination":"unit","recipient":id,"item_id":item_id,"route":route}
	if convoy[route].size()>=40:return {"valid":false,"reason":"convoy_full"}
	convoy[route].append(item_id)
	return {"valid":true,"destination":"convoy","item_id":item_id,"route":route}

func give_item(item_id: int) -> bool:
	return bool(receive_equipment(item_id).valid)
