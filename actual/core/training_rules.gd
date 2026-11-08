extends RefCounted
## Optional, finite field exercises. They use their own stage IDs and never
## clear a story battle, generate loot, consume treatment or grant combat XP.
const Experience = preload("res://core/campaign_experience.gd")
const VERSION := "training-1"
const UNLOCK_KEY := "TRAINING-UNLOCK-20261101"
static var _config: Dictionary = {}

static func config() -> Dictionary:
	if _config.is_empty():
		_config = JSON.parse_string(FileAccess.get_file_as_string("res://data/training_encounters.json"))
	return _config

static func _pool(chapter: int, route: String) -> String:
	return "%d:%s" % [chapter, route]

static func is_stage(g, id: int) -> bool:
	return bool(g.stages.get(id, {}).get("training", false))

static func active(g) -> bool:
	return is_stage(g, int(g.stage_id)) and g.flags.get("training_active") is Dictionary

static func register(g) -> void:
	for region in config().regions:
		for variant in range(2):
			var stage = _stage(g, region, variant)
			g.stages[int(stage.id)] = stage

static func _walkable(stage: Dictionary, p: Vector2i) -> bool:
	var width = int(stage.map.width)
	var height = int(stage.map.height)
	if p.x <= 0 or p.y <= 0 or p.x >= width - 1 or p.y >= height - 1:return false
	var tile = int(stage.map.tiles[p.y * width + p.x])
	var category = int(stage.terrain.tile_categories.get(str(tile), 0))
	# All drill positions are legal for ordinary infantry, including riders.
	for class_id in [1, 6, 9, 12, 15, 17]:
		var costs: Array = stage.terrain.movement_by_class_and_category.get(str(class_id), [])
		if category < 0 or category >= costs.size() or int(costs[category]) >= 255:return false
	return true

static func _distance_field(stage: Dictionary, origin: Vector2i) -> Dictionary:
	var found = {origin: 0}
	var queue: Array[Vector2i] = [origin]
	while not queue.is_empty():
		var here: Vector2i = queue.pop_front()
		for d in [Vector2i.UP, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.DOWN]:
			var next: Vector2i = here + d
			if found.has(next) or not _walkable(stage, next):continue
			found[next] = int(found[here]) + 1
			queue.append(next)
	return found

static func _stage(g, region: Dictionary, variant: int) -> Dictionary:
	var base: Dictionary = g.stages[int(region.base)]
	var stage = base.duplicate(true)
	stage.id = int(region.ids[variant])
	stage.code = "T%d%s%d" % [int(region.chapter), "W" if region.route == "alm" else "E", variant + 1]
	stage.name_zh = str(region.name) + ("·突破" if variant == 0 else "·护阵")
	stage.chapter = int(region.chapter)
	stage.route = str(region.route)
	stage.training = true
	stage.training_variant = "capture" if variant == 0 else "hold"
	stage.training_unlock = int(region.unlock)
	stage.training_pool = _pool(int(region.chapter), str(region.route))
	stage.training_base = int(region.base)
	stage.tactical_review_version = VERSION
	stage.npc_units = []
	stage.reinforcements = []
	stage.reinforcement_turn = 0
	stage.event_boats = []
	stage.enemy_group_ids = []
	stage.boss_id = ""
	stage.clear_training_exp = 0
	stage.objects = []
	stage.optional = true
	for key in ["enemy_role_hint", "summon_template", "final_phase", "recovery_sites", "training_target", "battlefield_tactics", "breakable_obstacles", "special_ai", "tactical_notes", "tactical_routes", "ai_and_timing", "contract", "cause", "absent_branch", "burner_departure_turn", "transport_path"]:
		stage.erase(key)
	stage.tactical_notes=["营地演习不推进主线；失败、退出均不发放经验，也不消耗次数。"]
	var at: Array = base.player_positions[0]
	var anchor = Vector2i(int(at[0]), int(at[1]))
	var field = _distance_field(stage, anchor)
	var occupied = {}
	stage.player_positions = []
	for p in base.player_positions:
		var cell = Vector2i(int(p[0]), int(p[1]))
		if _walkable(stage, cell) and field.has(cell) and not occupied.has(cell):
			stage.player_positions.append(p.duplicate())
			occupied[cell] = true
	# Keep all nine possible members deployable on each route.
	var near: Array = field.keys()
	near.sort_custom(func(a, b):return int(field[a]) < int(field[b]) if int(field[a]) != int(field[b]) else a.y * 100 + a.x < b.y * 100 + b.x)
	for cell in near:
		if stage.player_positions.size() >= 10:break
		if not occupied.has(cell):
			stage.player_positions.append([cell.x, cell.y]);occupied[cell] = true
	var target = anchor
	if variant == 0:
		var best_score = 100000
		for cell in near:
			if occupied.has(cell):continue
			var score = absi(int(field[cell]) - 7) * 100 + cell.y * 2 + cell.x
			if score < best_score:best_score = score;target = cell
	stage.training_target = [target.x, target.y]
	stage.exit = stage.training_target.duplicate()
	stage.targets = [stage.training_target.duplicate()]
	stage.objects = [{"id":"training_goal", "kind":"occupy", "label":"演习据点", "sprite":"white_flag", "position":stage.training_target.duplicate(), "adjacent":false, "optional":true}]
	var candidates = []
	for cell in near:
		if occupied.has(cell):continue
		var score: int
		if variant == 0:score = (absi(cell.x - target.x) + absi(cell.y - target.y)) * 100 + absi(int(field[cell]) - 7)
		else:score = absi(int(field[cell]) - 6) * 100 + cell.y * 2 + cell.x
		candidates.append({"cell":cell, "score":score})
	candidates.sort_custom(func(a, b):return int(a.score) < int(b.score))
	var templates: Array = base.enemies.filter(func(u):return not u.get("objective_boss", false) and not g.Mechanical.is_puppet(u) and int(u.class_id) not in [3, 5, 11, 16, 17, 18, 19, 21])
	if templates.is_empty():templates = base.enemies.filter(func(u):return not g.Mechanical.is_puppet(u))
	# Interleave distinct human professions. A second drill changes both its
	# objective and opening formation; it is not the old boss fight replayed.
	var ordered=[];var classes=[]
	for raw in templates:
		if not classes.has(int(raw.class_id)):ordered.append(raw);classes.append(int(raw.class_id))
	for raw in templates:
		if not ordered.has(raw):ordered.append(raw)
	templates=ordered
	stage.enemies = []
	for i in range(mini(int(region.enemy_count), candidates.size())):
		var raw: Dictionary = templates[(i + variant) % templates.size()]
		var u = raw.duplicate(true)
		for key in ["quest_kind", "objective_role", "burner", "enemy_role", "campaign_role", "summon_role", "battle_guard", "innate_knockback", "knockback", "knockback_elite"]:u.erase(key)
		u.id = str(stage.code) + "_drill" + str(i)
		u.name_zh = "对练" + str(g.catalog.classes.get(str(int(u.class_id)), {}).get("name_zh", "队员"))
		u.position = [candidates[i].cell.x, candidates[i].cell.y]
		u.side = "enemy";u.acted = false;u.objective_boss = false;u.behavior = "aggressive"
		u.no_experience = true;u.no_drop = true;u.training_opponent = true
		u.exp_value = 0;u.drop_chance = 0;u.move = maxi(4, int(u.move))
		u.hp = int(u.max_hp)
		stage.enemies.append(u)
	stage.goal = "抵达演习据点并结束行动，或击败全部对练者。" if variant == 0 else "守住演习据点，连续坚持%d个敌方阶段；也可击败全部对练者。" % int(config().hold_phases)
	stage.before = "教习：这是营地对练，倒地会退出本场，不会留下新的伤势。" 
	stage.during = ""
	stage.after = "教习：演习结束，回营整备。"
	return stage

static func remaining(g) -> int:
	return maxi(0, int(config().success_limit_per_chapter_route) - int(g.flags.get("training_counts", {}).get(_pool(int(g.chapter), str(g.route)), 0)))

static func rules_pages() -> Array:
	return [
		{"speaker":"提示","text":"成功后，每位未满级参训者获得%d经验，包括本场倒地者。演习中没有战斗经验，也没有掉落。" % int(config().completion_experience)},
		{"speaker":"提示","text":"每章每队最多成功%d次，两种演习共用次数。失败、退出或重试不获经验、不扣次数；未用次数不结转。最终合军后不再开放。" % int(config().success_limit_per_chapter_route)}
	]

static func queue_unlock(g, post_battle: bool=false) -> bool:
	if not g.stage_cleared(103) or g.flags.get("seen_"+UNLOCK_KEY,false) or active(g):return false
	if not post_battle and g.mode not in ["hub","world"]:return false
	var available=config().regions.any(func(r):return int(r.chapter)==int(g.chapter) and str(r.route)==str(g.route) and g.stage_cleared(int(r.unlock))) and not g.flags.get("chapter5_merged",false) and not g.flags.get("campaign_complete",false)
	var text="战术补练已开放。世界地图或据点中，打开菜单，选择部队整备，再选择战术补练。" if available else "战术补练在各章达到开放条件后可用，最终合军后关闭。入口在世界地图或据点的菜单、部队整备中。"
	g.queue_pages([
		{"speaker":"提示","text":text},
		{"speaker":"提示","text":"成功后每位未满级参训者获得%d经验，每章每队最多成功%d次。补练菜单可随时查看“收益与次数”。" % [int(config().completion_experience),int(config().success_limit_per_chapter_route)]}
	],UNLOCK_KEY)
	return true

static func choices(g) -> Array:
	var result = []
	if g.mode not in ["hub", "world"] or active(g) or g.flags.get("chapter5_merged", false) or g.flags.get("campaign_complete", false):return result
	for region in config().regions:
		if int(region.chapter) != int(g.chapter) or str(region.route) != str(g.route) or not g.stage_cleared(int(region.unlock)):continue
		for id in region.ids:
			var stage: Dictionary = g.stages[int(id)]
			result.append({"id":int(id), "label":str(stage.name_zh), "enabled":remaining(g)>0,
				"detail":"%s\n本章本队剩余%d次；成功后每位参训者获得%d经验。对练无永久伤亡；失败或退出不获经验、不消耗次数。" % [stage.goal, remaining(g), int(config().completion_experience)]})
	return result

static func _origin(g) -> Dictionary:
	var result = {"schema":3, "campaign_id":g.CAMPAIGN_ID, "hub_record":g.hub_record, "map_revision":str(g.battle_data.get("tactical_review_version", "0.2.0"))}
	for field in g.SAVE_FIELDS:
		var value = g.get(field)
		result[field] = [value.x, value.y] if value is Vector2i else value.duplicate(true) if value is Dictionary or value is Array else value
	# Peaceful return never needs a former encounter's retry chain or actors.
	result.battle_start_snapshot = {};result.units = [];result.selected_id = ""
	result.story_events = [];result.battle_outcome = "";result.battle_settled = false
	return result

static func _quest() -> Dictionary:
	return {"objects":{}, "evacuated":[], "freed":[], "burn_streak":0, "reinforced":true, "mid_done":false,
		"boats":[], "beacon_since":-1, "beacon_contested":false,
		"transport_index":0, "transport_stopped":false, "german_decision":"",
		"record_lost":false, "summon_wave":false, "old_comrades_talked":false, "transfer_cut_snapshot":false,
		"burn_count":0, "repair_since":{"repair_1":-1,"repair_2":-1}, "wells":{"well_n":false,"well_s":false}, "well_since":{"well_n":-1,"well_s":-1},
		"final_phase":false, "training_held":0, "failed_reason":""}

static func start(g, id: int) -> bool:
	if not choices(g).any(func(c):return int(c.id)==id and bool(c.enabled)) or not g.story_events.is_empty() or g.flags.has("active_plot"):return false
	var leader: Dictionary = g.roster.get(g.leader_id(), {})
	if not g.can_deploy(leader):return false
	var origin = _origin(g)
	g.stage_id = id;g.battle_data = g.stages[id].duplicate(true)
	g.units.clear();var participants = []
	for member in g.party:
		if not g.can_deploy(g.roster.get(str(member), {})):continue
		if participants.size() >= g.battle_data.player_positions.size():break
		var u: Dictionary = g.roster[str(member)].duplicate(true)
		g.Cover.clear(u)
		u.position = g.battle_data.player_positions[participants.size()].duplicate()
		u.player_slot = participants.size();u.hp = int(u.max_hp);u.acted = false;u.side = "player";u.route = g.route
		u.no_experience = true;u.no_drop = true;u.erase("weapon_index")
		participants.append(str(member));g.units.append(u)
	for raw in g.battle_data.enemies:
		var u: Dictionary = raw.duplicate(true);u.enemy_slot = g.units.size()-participants.size();g.units.append(u)
	g.flags.training_active = {"stage_id":id, "pool":str(g.battle_data.training_pool), "participants":participants, "origin":origin, "settled":false}
	g.flags.quest = _quest()
	g.MapSkills.reset_battle(g.units)
	if int(g.chapter)==4:g.flags.quest.repair_since=-1
	g.flags.inventory_processed_deaths = {}
	g.flags.pending_loot = [];g.flags.erase("active_plot")
	g.turn=1;g.phase="player";g.kills=0;g.selected_id="";g.battle_outcome="";g.battle_settled=false;g.mode="battle"
	g.encounter_groups=[];g.story_events=[];g.victory_rewards=[];g.log_lines.clear()
	g.battle_return={"mode":str(origin.mode), "world_node":int(origin.world_node)}
	g.cursor=g.pos(g.find_unit(g.leader_id()))
	g.queue_lines(str(g.battle_data.before)+"／教习："+str(g.battle_data.goal)+" 本场最多%d回合；成功后每位参训者获得%d经验，包括本场倒地者。" % [int(config().turn_limit), int(config().completion_experience)])
	g.battle_start_snapshot=g._capture_battle_start()
	g.Rewind.reset(g)
	return true

static func before_phase(g) -> void:
	if not active(g) or g.phase!="enemy" or not str(g.battle_outcome).is_empty():return
	if g.battle_data.training_variant != "hold":return
	var target=Vector2i(int(g.battle_data.training_target[0]),int(g.battle_data.training_target[1]))
	var u=g.unit_at(target)
	var held=not u.is_empty() and u.side=="player" and g.flags.training_active.participants.has(str(u.id))
	g.flags.quest.training_held=int(g.flags.quest.get("training_held",0))+1 if held else 0

static func check_outcome(g) -> String:
	if not active(g):return str(g.battle_outcome)
	if not str(g.battle_outcome).is_empty():return str(g.battle_outcome)
	var leader=g.find_unit(g.leader_id())
	if leader.is_empty() or int(leader.hp)<=0:
		g.flags.quest.failed_reason="领队退出演习；本次无收益，可重试或回营。";g.battle_outcome="defeat"
	elif g.living("enemy").is_empty():g.battle_outcome="victory"
	elif g.battle_data.training_variant=="capture":
		var target=Vector2i(int(g.battle_data.training_target[0]),int(g.battle_data.training_target[1]))
		var u=g.unit_at(target)
		if not u.is_empty() and u.side=="player" and u.get("acted",false) and g.flags.training_active.participants.has(str(u.id)):g.battle_outcome="victory"
	elif int(g.flags.quest.get("training_held",0))>=int(config().hold_phases):g.battle_outcome="victory"
	if str(g.battle_outcome).is_empty() and int(g.turn)>int(config().turn_limit):
		g.flags.quest.failed_reason="演习时限已到；本次无收益，可重试或回营。";g.battle_outcome="defeat"
	return str(g.battle_outcome)

static func interact(g, id: String) -> bool:
	if not active(g) or id!="training_goal" or str(g.battle_outcome)!="":return false
	var actor=g.find_unit(g.selected_id)
	var target=Vector2i(int(g.battle_data.training_target[0]),int(g.battle_data.training_target[1]))
	if actor.is_empty() or actor.side!="player" or actor.get("acted",false) or g.pos(actor)!=target:return false
	actor.acted=true;g.selected_id="";check_outcome(g);return true

static func complete(g) -> bool:
	if not active(g) or g.battle_outcome!="victory" or g.battle_settled:return false
	var info: Dictionary=g.flags.training_active
	var origin: Dictionary=info.origin
	g.victory_rewards.clear()
	for id in info.participants:
		var current=g.find_unit(str(id))
		var persistent: Dictionary=origin.roster[str(id)].duplicate(true)
		# Equipment exchanges are legitimate preparation; drills cannot loot.
		if not current.is_empty():persistent.item_id=int(current.get("item_id",persistent.get("item_id",0)))
		persistent.acted=false;persistent.hp=int(persistent.max_hp)
		if int(persistent.level)<20 and not persistent.get("no_experience",false):
			g.victory_rewards.append(Experience.award(g,persistent,int(config().completion_experience)))
		g.roster[str(id)]=persistent
		if not current.is_empty():
			var position=current.position.duplicate();var slot=int(current.get("player_slot",0))
			current.clear();current.merge(persistent,true);current.position=position;current.player_slot=slot
	var counts: Dictionary=g.flags.get("training_counts",{}).duplicate(true)
	counts[str(info.pool)]=int(counts.get(str(info.pool),0))+1
	g.flags.training_counts=counts;info.settled=true;g.battle_settled=true
	return true

static func _restore(g, origin: Dictionary) -> void:
	for field in g.SAVE_FIELDS:
		var value=origin[field]
		if field in ["hub_position","cursor","move_origin"]:g.set(field,Vector2i(int(value[0]),int(value[1])))
		elif field=="cleared_stages":g.cleared_stages=value.map(func(v):return int(v))
		else:g.set(field,value.duplicate(true) if value is Dictionary or value is Array else value)
	g.stage_id=int(g.stage_id);g.chapter=int(g.chapter);g.world_node=int(g.world_node);g.previous_world_node=int(g.previous_world_node)
	g.hub_record=str(origin.hub_record);g.battle_data=g.stages[int(g.stage_id)].duplicate(true)
	g.encounter_groups=[];g.log_lines.clear()

static func leave(g) -> bool:
	if not active(g):return false
	var info: Dictionary=g.flags.training_active.duplicate(true)
	var kept_roster=g.roster.duplicate(true);var kept_convoy=g.convoy.duplicate(true)
	var kept_counts=g.flags.get("training_counts",{}).duplicate(true)
	var kept_rng=int(g.rng_state);var kept_frame=int(g.frame_counter)
	_restore(g,info.origin)
	g.battle_rewind={}
	if bool(info.settled):
		g.roster=kept_roster;g.convoy=kept_convoy;g.flags.training_counts=kept_counts
		g.rng_state=kept_rng;g.frame_counter=kept_frame
	return true

static func retry(g) -> bool:
	if not active(g) or g.battle_settled or g.battle_start_snapshot.is_empty():return false
	var snapshot: Dictionary=g.battle_start_snapshot.duplicate(true)
	for field in snapshot:
		if field in g.SAVE_FIELDS:g.set(field,snapshot[field].duplicate(true) if snapshot[field] is Dictionary or snapshot[field] is Array else snapshot[field])
	g.stage_id=int(g.stage_id);g.battle_data=g.stages[int(g.stage_id)].duplicate(true)
	g.cleared_stages=g.cleared_stages.map(func(v):return int(v))
	g.flags.erase("active_plot");g.story_events.clear();g.turn=1;g.phase="player";g.kills=0
	g.battle_outcome="";g.battle_settled=false;g.mode="battle";g.selected_id="";g.victory_rewards.clear()
	g.cursor=g.pos(g.find_unit(g.leader_id()));g.Rewind.reset(g);return true

static func status(g) -> Array[String]:
	var lines: Array[String]=[str(g.battle_data.goal)]
	if not active(g):return lines
	if g.battle_data.training_variant=="hold":lines.append("据点已连续守住%d/%d个敌方阶段。" % [int(g.flags.quest.get("training_held",0)),int(config().hold_phases)])
	lines.append("演习第%d/%d回合；成功每人%d经验，本章本队剩余%d次。" % [int(g.turn),int(config().turn_limit),int(config().completion_experience),remaining(g)])
	lines.append("无战斗经验、无掉落；倒地不留新伤。失败或退出还原本次进度。")
	return lines

static func _integer(value: Variant, minimum: int, maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value)==float(int(value)) and int(value)>=minimum and int(value)<=maximum

static func validate(g, state: Dictionary) -> bool:
	var flags=state.get("flags",{})
	if not flags is Dictionary:return false
	var pools=[]
	for region in config().regions:pools.append(_pool(int(region.chapter),str(region.route)))
	var counts=flags.get("training_counts",{})
	if not counts is Dictionary:return false
	for pool in counts:
		if pool not in pools or not _integer(counts[pool],0,int(config().success_limit_per_chapter_route)):return false
	var training=is_stage(g,int(state.get("stage_id",0)))
	if not training:return not flags.has("training_active")
	if state.has("mode") and state.mode not in ["battle","victory","defeat"]:return false
	var info=flags.get("training_active")
	if not info is Dictionary:return false
	var stage: Dictionary=g.stages[int(state.stage_id)]
	if not _integer(info.get("stage_id"),int(state.stage_id),int(state.stage_id)):return false
	if not info.get("pool") is String or info.pool!=stage.training_pool or not info.get("settled") is bool:return false
	var origin=info.get("origin")
	if not origin is Dictionary or not origin.get("flags") is Dictionary:return false
	if not _integer(origin.get("stage_id"),101,534):return false
	if origin.flags.has("training_active") or is_stage(g,int(origin.stage_id)):return false
	if not origin.get("mode") is String or origin.mode not in ["hub","world"]:return false
	if not origin.get("battle_start_snapshot") is Dictionary or not origin.battle_start_snapshot.is_empty():return false
	if not g.SaveValidation.campaign_valid(g,origin,g.SAVE_FIELDS):return false
	if int(origin.chapter)!=int(state.chapter) or origin.route!=state.route or origin.world_node!=state.world_node:return false
	if not origin.cleared_stages.has(float(stage.training_unlock)) and not origin.cleared_stages.has(int(stage.training_unlock)):return false
	if origin.flags.get("chapter5_merged",false) or origin.flags.get("campaign_complete",false):return false
	var initial_count=int(origin.flags.get("training_counts",{}).get(str(info.pool),0))
	if initial_count>=int(config().success_limit_per_chapter_route):return false
	if int(counts.get(str(info.pool),0))!=initial_count+(1 if info.settled else 0):return false
	var participants=info.get("participants")
	if not participants is Array or participants.is_empty() or participants.size()>stage.player_positions.size():return false
	var seen=[]
	for id in participants:
		if not id is String or id in seen or not origin.party.has(id) or not origin.roster.has(id) or not g.can_deploy(origin.roster[id]):return false
		seen.append(id)
	if not info.settled:
		for unit in state.get("units",[]):
			if unit.get("id") in participants and (unit.get("no_experience")!=true or unit.get("no_drop")!=true):return false
	else:
		for id in participants:
			if not state.get("roster",{}).has(id) or state.roster[id].get("no_experience",false)!=origin.roster[id].get("no_experience",false):return false
	if not participants.has("hunapu" if state.route=="alm" else "eileen"):return false
	if not _integer(flags.get("quest",{}).get("training_held"),0,int(config().hold_phases)):return false
	if state.has("battle_settled") and bool(state.battle_settled)!=bool(info.settled):return false
	return true
