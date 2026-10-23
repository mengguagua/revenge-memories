extends RefCounted
## Validate checkpoints before load_game converts or mutates any live fields.
## Old retry snapshots remain legal after a v1/v2 save is upgraded to v3.

const EXTENDED_FIELDS = ["chapter", "route", "parties", "route_positions", "previous_world_node",
	"world_armies", "convoy", "hub_id", "hub_position", "hub_flags", "hub_changes", "hub_used",
	"battle_return", "battle_settled", "story_events", "encounter_groups"]
const Items = preload("res://core/item_rules.gd")

static func valid(game, state: Dictionary) -> bool:
	if not _integer(state.get("version", 0), 1, 3):
		return false
	if not state.get("source_revision") is String: return false
	if not _base(game, state) or not _expanded(game, state, int(state.version) == 3):
		return false
	var snapshot = state.get("battle_start_snapshot", {})
	return snapshot is Dictionary and _base(game, snapshot) and _expanded(game, snapshot, false)

static func _base(game, state: Dictionary) -> bool:
	# Validate before callers convert or assign values. A malformed checkpoint
	# must not partially replace the current party, then fail on a later field.
	for key in ["stage_id", "world_node"]:
		if state.has(key) and not _integer(state[key], 1, 80): return false
	for key in ["rng_state", "frame_counter"]:
		if state.has(key) and not _integer(state[key], 0, 255): return false
	for key in ["turn", "kills"]:
		if state.has(key) and not _integer(state[key], 1 if key == "turn" else 0, 2147483647): return false
	if state.has("mode") and state.mode not in ["title", "chapter", "village", "hub", "world", "battle", "victory", "defeat", "ending"]: return false
	if state.has("phase") and state.phase not in ["player", "enemy"]: return false
	if state.has("battle_outcome") and state.battle_outcome not in ["", "victory", "defeat", "retreat", "enemy_retreat"]: return false
	if state.has("village_position") and not _point(state.village_position): return false
	if state.has("party"):
		if not state.party is Array or state.party.is_empty() or state.party[0] not in ["alm", "celica"]: return false
		var seen: Array = []
		for id in state.party:
			if not id is String or not game.characters.has(id) or seen.has(id): return false
			seen.append(id)
	if state.has("units"):
		if not state.units is Array: return false
		var seen: Array = []
		var stage: Dictionary = game.stages[int(state.get("stage_id", 1))]
		for unit in state.units:
			if not _unit(unit, true) or seen.has(unit.id): return false
			seen.append(unit.id)
			if int(unit.position[0]) < 0 or int(unit.position[1]) < 0 or int(unit.position[0]) >= int(stage.map.width) or int(unit.position[1]) >= int(stage.map.height): return false
	if state.has("roster"):
		if not state.roster is Dictionary: return false
		for id in state.roster:
			if not id is String or not game.characters.has(id) or not _unit(state.roster[id], false): return false
			if state.roster[id].id != id or state.roster[id].side != "player": return false
	if state.has("cleared_stages"):
		if not state.cleared_stages is Array: return false
		for stage in state.cleared_stages:
			if not _integer(stage, 1, 80): return false
	if state.has("victory_rewards"):
		if not state.victory_rewards is Array: return false
		for reward in state.victory_rewards:
			if not reward is Dictionary or not reward.get("unit") is String: return false
			for key in ["gain", "exp_before", "exp_after", "actual_gain"]:
				if reward.has(key) and not _integer(reward[key], 0, 65535): return false
	if state.has("flags") and not _flags(game, state.flags, state): return false
	return true

static func _unit(unit: Variant, tactical: bool) -> bool:
	if not unit is Dictionary or not unit.get("id") is String or unit.id.is_empty(): return false
	if unit.get("side") not in ["player", "enemy"] or not unit.get("acted") is bool: return false
	for key in ["hp", "strength", "skill", "speed", "luck", "defence", "move"]:
		if not _integer(unit.get(key), 0, 255): return false
	if not _integer(unit.get("max_hp"), 1, 255 if unit.side == "enemy" else 52) or int(unit.hp) > int(unit.max_hp): return false
	if not _integer(unit.get("class_id"), 1, 22) or not _integer(unit.get("level"), 1, 20): return false
	if tactical and not _point(unit.get("position")): return false
	for key in ["exp", "magic_level", "magic_flags", "raw_magic_flags", "character_id", "name_id", "resistance", "ai_flags", "raw_ai_flags", "record_index", "group_id", "exp_value", "weapon_index", "source_enemy_character_id"]:
		if unit.has(key) and not _integer(unit[key], 0, 65535 if key == "exp" else 255): return false
	# Personal resistance is consumed by promotion after resume. A source
	# Dread Fighter may have a negative personal baseline after bonus removal.
	if unit.has("personal_resistance") and not _integer(unit.personal_resistance, -15, 255): return false
	for key in ["player_slot", "enemy_slot"]:
		if unit.has(key) and not _integer(unit[key], 0, 19): return false
	if unit.has("item_id") and not (_integer(unit.item_id, 0, 0) or _carried_item(unit.item_id)): return false
	for key in ["dead", "temporary", "no_drop", "no_experience", "neutral", "controllable", "promoted", "retreated", "rescued", "vanished", "zeke_npc", "rescue_npc"]:
		if unit.has(key) and not unit[key] is bool: return false
	for key in ["name_zh", "class", "death_place", "summoner_id", "army_instance"]:
		if unit.has(key) and not unit[key] is String: return false
	if unit.has("army_instance") and not _instance_id(unit.army_instance): return false
	if unit.has("route") and unit.route not in ["alm", "celica"]: return false
	if unit.has("growths"):
		if not unit.growths is Dictionary: return false
		for key in unit.growths:
			if not _integer(unit.growths[key], 0, 255): return false
	return true

static func _loot_record(value: Variant) -> bool:
	return value is Dictionary and value.get("kind") in ["loot", "death_storage"] and _carried_item(value.get("item_id")) and value.get("unit_id") is String and not value.unit_id.is_empty() and value.get("route") in ["alm", "celica"]

static func _flags(game, flags: Variant, state: Dictionary) -> bool:
	if not flags is Dictionary: return false
	if flags.has("world_route_previous_nodes"):
		if not flags.world_route_previous_nodes is Dictionary: return false
		for route in flags.world_route_previous_nodes:
			if route not in ["alm", "celica"] or not _node(game, flags.world_route_previous_nodes[route]): return false
	if flags.has("world_route_encounters"):
		if not flags.world_route_encounters is Dictionary: return false
		for route in flags.world_route_encounters:
			var record = flags.world_route_encounters[route]
			if route not in ["alm", "celica"] or not record is Dictionary: return false
			for key in record:
				match key:
					"inventory_enemy_initiated":
						if not record[key] is bool: return false
					"inventory_attacking_group_id":
						if not _integer(record[key], 0, 255): return false
					"inventory_attacker_previous_node":
						if not (_integer(record[key], -1, -1) or _node(game, record[key])): return false
					"inventory_attacking_instance_id":
						if not _instance_id(record[key]): return false
					_: return false
	for key in ["pending_loot", "loot_notifications"]:
		if not flags.has(key): continue
		if not flags[key] is Array: return false
		for record in flags[key]:
			if not _loot_record(record): return false
	for key in ["inventory_processed_deaths", "inventory_defeated_enemy_records"]:
		if not flags.has(key): continue
		if not flags[key] is Dictionary: return false
		for id in flags[key]:
			if not id is String or not flags[key][id] is bool: return false
	if flags.has("celica_captive_hp"):
		if not flags.celica_captive_hp is Dictionary: return false
		for id in flags.celica_captive_hp:
			if not id is String or not game.characters.has(id) or not _integer(flags.celica_captive_hp[id], 0, 52): return false
	if flags.has("world_mobile_armies"):
		if not flags.world_mobile_armies is Array: return false
		for army in flags.world_mobile_armies:
			if not army is Dictionary or not _node(game, army.get("node")) or not _groups(game, [army.get("group_id")]): return false
			if army.has("previous_node") and not (_integer(army.previous_node, -1, -1) or _node(game, army.previous_node)): return false
			if army.has("instance_id") and not _instance_id(army.instance_id): return false
	if flags.has("world_army_next_id") and not _integer(flags.world_army_next_id, 1, 2147483647): return false
	if flags.has("world_random_army_instance"):
		if not flags.world_random_army_instance is String: return false
		if flags.world_random_army_instance != "" and not _instance_id(flags.world_random_army_instance): return false
	if flags.has("dungeon_army_instances"):
		if not flags.dungeon_army_instances is Dictionary: return false
		for key in flags.dungeon_army_instances:
			if not key is String or not _instance_id(flags.dungeon_army_instances[key]): return false
	if flags.has("world_army_instances"):
		if not flags.world_army_instances is Dictionary: return false
		var seen: Array = []
		var armies = state.get("world_armies", {})
		if not armies is Dictionary: return false
		for node in flags.world_army_instances:
			var ids = flags.world_army_instances[node]
			if not _numeric_key(node) or not _node(game, int(node)) or not ids is Array: return false
			if not armies.get(node, []) is Array or ids.size() != armies.get(node, []).size(): return false
			for id in ids:
				if not _instance_id(id) or seen.has(id): return false
				seen.append(id)
		for node in armies:
			if not flags.world_army_instances.has(node): return false
	if flags.has("battle_army_instances"):
		if not flags.battle_army_instances is Array: return false
		var groups = state.get("encounter_groups", [])
		if not groups is Array or flags.battle_army_instances.size() != groups.size(): return false
		var seen: Array = []
		for id in flags.battle_army_instances:
			if not _instance_id(id) or seen.has(id): return false
			seen.append(id)
	return true

static func _instance_id(value: Variant) -> bool:
	if not value is String or not value.begins_with("army_"): return false
	var serial: String = value.substr(5)
	return _numeric_key(serial) and _integer(int(serial), 1, 2147483647)

static func _battle_unit_instances(state: Dictionary) -> bool:
	var flags: Dictionary = state.get("flags", {})
	# Pre-instance v1/v2/v3 checkpoints are bound during migration. Once
	# explicit identities exist, a soldier cannot point at another army or
	# an orphan identity: its casualty would otherwise disappear on re-entry.
	if not flags.has("battle_army_instances"): return true
	var identities: Array = flags.battle_army_instances
	var groups: Array = state.get("encounter_groups", [])
	for unit in state.get("units", []):
		if unit.side != "enemy" or not unit.has("army_instance"): continue
		var index := identities.find(unit.army_instance)
		if index < 0 or (unit.has("group_id") and int(unit.group_id) != int(groups[index])): return false
	return true

static func _integer(value: Variant, minimum: int, maximum: int) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and float(value) == floor(float(value)) and float(value) >= minimum and float(value) <= maximum

static func _point(value: Variant) -> bool:
	return value is Array and value.size() == 2 and _integer(value[0], -256, 512) and _integer(value[1], -256, 512)

static func _node(game, value: Variant) -> bool:
	return _integer(value, 1, 80) and game.catalog.world_nodes.has(str(int(value)))

static func _room(game, value: Variant) -> bool:
	return _integer(value, 1, 255) and game.hubs.rooms.has(str(int(value)))

static func _carried_item(value: Variant) -> bool:
	return _integer(value, 1, Items.data().items.size()-1) and str(Items.item(int(value)).get("kind", "")) in ["weapon", "accessory"]

static func _hub_used(game, value: Variant) -> bool:
	if not value is Dictionary:
		return false
	if value.has("dungeon_visited") and not _integer(value.dungeon_visited, 0, 255): return false
	if value.has("leader_facing"):
		if not _point(value.leader_facing):
			return false
		if absi(int(value.leader_facing[0])) + absi(int(value.leader_facing[1])) != 1:
			return false
	if value.has("event_vm"):
		var vm = value.event_vm
		if not vm is Dictionary:
			return false
		if vm.is_empty():
			return true
		if not _integer(vm.get("script_id"), 0, 255) or not game.hubs.scripts.has(str(int(vm.script_id))) or not _room(game, vm.get("hub_id")):
			return false
		var program: Array = game.hubs.scripts[str(int(vm.script_id))].instructions
		if not _integer(vm.get("pc"), 0, program.size()) or not vm.get("actors") is Dictionary:
			return false
		# The controller persists the dialogue instruction itself, or the
		# instruction after a choice. Other PCs would skip/replay story effects.
		var pc := int(vm.pc)
		if not ((pc < program.size() and program[pc].kind == "dialogue") or (pc > 0 and program[pc - 1].kind == "choice")):
			return false
		for key in vm.actors:
			var actor = vm.actors[key]
			if not _numeric_key(key) or not _integer(int(key), 2, 255) or not actor is Dictionary or not _point(actor.get("position")) or not _integer(actor.get("sprite_id"), 0, 255):
				return false
			if actor.has("actor_id") and (not _integer(actor.actor_id, 2, 255) or int(actor.actor_id) != int(key)): return false
			if actor.has("facing") and not _integer(actor.facing, 1, 4): return false
			if actor.has("movement_flags") and not _integer(actor.movement_flags, 0, 255): return false
			if actor.has("interaction_flags") and not _integer(actor.interaction_flags, 0, 255): return false
			if actor.has("wander_bounds"):
				if not actor.wander_bounds is Array or actor.wander_bounds.size() != 4: return false
				for coordinate in actor.wander_bounds:
					if not _integer(coordinate, -256, 512): return false
			if actor.has("render_position"):
				if not actor.render_position is Array or actor.render_position.size() != 2: return false
				for coordinate in actor.render_position:
					if not typeof(coordinate) in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(coordinate)) or float(coordinate) < -4096 or float(coordinate) > 8192: return false
			for flag in ["hidden", "spawned"]:
				if actor.has(flag) and not actor[flag] is bool: return false
	return true

static func _numeric_key(value: Variant) -> bool:
	return value is String and value.is_valid_int() and str(int(value)) == value

static func _groups(game, value: Variant) -> bool:
	if not value is Array or value.size() > 2:
		return false
	for group in value:
		if not _integer(group, 0, 255) or not bool(game.catalog.enemy_groups.get(str(int(group)), {}).get("valid", false)):
			return false
	return true

static func _parties(game, value: Variant) -> bool:
	if not value is Dictionary or not value.has("alm") or not value.has("celica"):
		return false
	var seen: Array[String] = []
	for route in ["alm", "celica"]:
		var members = value[route]
		if not members is Array or (not members.is_empty() and (not members[0] is String or members[0] != route)):
			return false
		for member in members:
			if not member is String or not game.characters.has(member) or seen.has(member):
				return false
			seen.append(member)
	return true

static func _expanded(game, state: Dictionary, required: bool) -> bool:
	if required:
		for key in EXTENDED_FIELDS:
			if not state.has(key):
				return false
	if state.has("chapter") and not _integer(state.chapter, 1, 5):
		return false
	if state.has("route") and state.route not in ["alm", "celica"]:
		return false
	if state.has("parties") and not _parties(game, state.parties):
		return false
	if state.has("party") and state.has("route") and state.party[0] != state.route:
		return false
	if state.has("parties"):
		# Final battle deployment and revived companions may span routes;
		# membership must exist in the union, rather than only the active team.
		var members: Array = state.parties.alm + state.parties.celica
		for id in state.get("party", []):
			if not members.has(id): return false
		if state.has("roster"):
			for id in members:
				if not state.roster.has(id): return false
	if state.has("route_positions"):
		if not state.route_positions is Dictionary:
			return false
		for route in ["alm", "celica"]:
			if not _node(game, state.route_positions.get(route, null)):
				return false
	if state.has("previous_world_node") and not _node(game, state.previous_world_node):
		return false
	if state.has("world_armies"):
		if not state.world_armies is Dictionary:
			return false
		for key in state.world_armies:
			if not _numeric_key(key) or not _node(game, int(key)) or not _groups(game, state.world_armies[key]):
				return false
	if state.has("encounter_groups") and not _groups(game, state.encounter_groups):
		return false
	if state.has("convoy"):
		if not state.convoy is Dictionary:
			return false
		for route in ["alm", "celica"]:
			if not state.convoy.get(route) is Array:
				return false
			for item in state.convoy[route]:
				if not _carried_item(item):
					return false
	if state.has("hub_id") and not _room(game, state.hub_id):
		return false
	if state.has("hub_position") and not _point(state.hub_position):
		return false
	if state.has("hub_flags"):
		if not state.hub_flags is Dictionary:
			return false
		for key in state.hub_flags:
			if not _numeric_key(key) or not _room(game, int(key)) or not state.hub_flags[key] is Dictionary:
				return false
			for flag in ["actors", "talk", "triggers"]:
				if not _integer(state.hub_flags[key].get(flag), 0, 255):
					return false
	if state.has("hub_changes"):
		if not state.hub_changes is Dictionary:
			return false
		for key in state.hub_changes:
			if not _numeric_key(key) or not _room(game, int(key)) or not state.hub_changes[key] is Dictionary:
				return false
			for cell in state.hub_changes[key]:
				if not _numeric_key(cell) or not _integer(int(cell), 0, game.hubs.rooms[key].tiles.size() - 1) or not _integer(state.hub_changes[key][cell], 0, 255):
					return false
	if state.has("hub_used") and not _hub_used(game, state.hub_used):
		return false
	if state.has("hub_id") and not state.get("hub_used", {}).get("event_vm", {}).is_empty():
		if int(state.hub_used.event_vm.hub_id) != int(state.hub_id): return false
	if state.has("battle_settled") and not state.battle_settled is bool:
		return false
	if state.has("battle_return"):
		var back = state.battle_return
		if not back is Dictionary:
			return false
		if not back.is_empty():
			if back.get("mode", "") not in ["world", "hub"] or not _node(game, back.get("world_node")):
				return false
			if back.mode == "hub" and (not _room(game, back.get("hub_id")) or not _point(back.get("position"))):
				return false
	if state.has("story_events"):
		if not state.story_events is Array:
			return false
		for event in state.story_events:
			if not event is Dictionary or event.get("kind", "") not in ["dialogue", "ending"]:
				return false
			if event.kind == "dialogue" and (event.get("group", "") not in ["events", "death_quotes"] or not _numeric_key(event.get("key"))):
				return false
	return _battle_unit_instances(state)

## Reconstructed campaign checkpoints have their own schema and character IDs.
## Validate every live and retry field before assigning any state. Schema 1 is
## the shipped chapter-one format; schema 3 adds first-two-chapter injury care.
static func campaign_valid(game, state: Dictionary, fields: Array) -> bool:
	if state.get("campaign_id","")!=game.CAMPAIGN_ID or not _integer(state.get("schema"),1,3):return false
	for key in fields:
		if not state.has(key):return false
	var revision=str(state.get("map_revision","0.2.0"))
	if not _campaign_core(game,state,false,revision):return false
	if not state.get("hub_record") is String or state.hub_record not in (["P00","H01","H02","H03","H04","H05","H06","H07","H08","H09"] if int(state.chapter)==1 else ["H21","H22","H23","H24","H25","H26","H27"] if int(state.chapter)==2 else game.ChapterThree.ROOMS if int(state.chapter)==3 else game.ChapterFour.ROOMS if int(state.chapter)==4 else game.ChapterFive.ROOMS):return false
	for key in ["hub_position","cursor","move_origin"]:
		if not _point(state.get(key)):return false
	if not state.get("battle_settled") is bool or not state.get("selected_id") is String:return false
	if not _integer(state.get("hub_id"),0,255):return false
	if state.get("mode") not in ["title","hub","world","battle","victory","defeat","chapter_end","ending"] or state.get("phase") not in ["player","enemy"]:return false
	if state.get("battle_outcome") not in ["","victory","defeat"]:return false
	if not _integer(state.get("turn"),1,2147483647) or not _integer(state.get("kills"),0,2147483647):return false
	if not state.get("victory_rewards") is Array:return false
	for record in state.victory_rewards:
		if not record is Dictionary or not record.get("unit") is String or not game.characters.has(record.unit):return false
		for key in ["gain","exp_before","exp_after","actual_gain"]:
			if not _integer(record.get(key),0,65535):return false
	var snapshot=state.get("battle_start_snapshot")
	if not snapshot is Dictionary:return false
	if not snapshot.is_empty():
		if not _campaign_core(game,snapshot,true,revision):return false
		if int(snapshot.stage_id)!=int(state.stage_id) or int(snapshot.chapter)!=int(state.chapter) or snapshot.route!=state.route:return false
	if state.mode in ["battle","victory","defeat"] and snapshot.is_empty():return false
	if int(state.schema)==1 and (int(state.chapter)!=1 or state.route!="alm"):return false
	if int(state.schema)==3:
		if not game.Casualties.valid(state):return false
		if not snapshot.is_empty() and not game.Casualties.valid(snapshot):return false
	return true

static func campaign_stage(game, id: int, revision: String="") -> Dictionary:
	var stage: Dictionary=game.stages[id]
	if revision not in ["0.2.0","0.2.1","0.3.0","0.3.1","0.3.4","0.3.5","0.3.6","0.4.0","0.5.0"] or revision==str(stage.get("tactical_review_version","0.2.0")):return stage
	var path="res://data/compat/"+revision+"/"+str(stage.code)+".json"
	if not FileAccess.file_exists(path) and revision=="0.2.0":path="res://data/compat/0.2.1/"+str(stage.code)+".json"
	if not FileAccess.file_exists(path):return stage
	var compatible=game.read_json(path)
	return compatible if not compatible.is_empty() else stage

static func _campaign_core(game, state: Dictionary, snapshot: bool, revision: String="") -> bool:
	for key in ["chapter","route","parties","route_positions","previous_world_node","convoy","battle_return","story_events","stage_id","world_node","cleared_stages","roster","flags","party","units","rng_state","frame_counter"]:
		if not state.has(key):return false
	if not _integer(state.chapter,1,5) or state.route not in ["alm","celica"]:return false
	if int(state.chapter)<3 and ((int(state.chapter)==1)!=(state.route=="alm")):return false
	if not _integer(state.stage_id,101,534) or not game.stages.has(int(state.stage_id)):return false
	if int(game.stages[int(state.stage_id)].get("chapter",1))!=int(state.chapter):return false
	if int(state.chapter)>=3 and game.stages[int(state.stage_id)].route!=state.route and not (int(state.stage_id) in [533,534] and state.flags.get("chapter5_merged",false)):return false
	for key in ["world_node","previous_world_node"]:
		if not _integer(state[key],1,39) or not game.formal_world.nodes.has(str(int(state[key]))):return false
	for key in ["rng_state","frame_counter"]:
		if not _integer(state[key],0,255):return false
	if not state.flags is Dictionary or not state.roster is Dictionary:return false
	if not state.parties is Dictionary or not state.route_positions is Dictionary or not state.convoy is Dictionary:return false
	var ownership={}
	for route_name in ["alm","celica"]:
		if not state.parties.get(route_name) is Array or not state.convoy.get(route_name) is Array:return false
		if not _integer(state.route_positions.get(route_name),1,39):return false
		for id in state.parties[route_name]:
			if not id is String or not game.characters.has(id) or not state.roster.has(id) or ownership.has(id):return false
			if (id in ["eileen","mireille","lisa","carlo","lord","roan","shia","noya","celine"])!=(route_name=="celica"):return false
			ownership[id]=route_name
		for item in state.convoy[route_name]:
			if not _carried_item(item):return false
	if not state.party is Array or state.party.is_empty() or state.party!=state.parties[state.route]:return false
	if state.party[0]!=("hunapu" if state.route=="alm" else "eileen"):return false
	for id in state.roster:
		var u=state.roster[id]
		if not id is String or not game.characters.has(id) or not _campaign_unit(game,u,false):return false
		if u.id!=id or u.side!="player":return false
	if not state.units is Array or state.units.size()>40:return false
	var stage: Dictionary=campaign_stage(game,int(state.stage_id),revision);var seen={};var side_counts={"player":0,"enemy":0}
	for unit in state.units:
		if not _campaign_unit(game,unit,true) or seen.has(unit.id):return false
		seen[unit.id]=true
		if side_counts.has(unit.side):
			side_counts[unit.side]+=1
			if side_counts[unit.side]>20:return false
		if int(unit.position[0])<0 or int(unit.position[1])<0 or int(unit.position[0])>=int(stage.map.width) or int(unit.position[1])>=int(stage.map.height):return false
		if unit.side=="player" and not unit.get("neutral",false) and not unit.get("temporary",false) and not state.party.has(unit.id) and not (int(state.stage_id) in [533,534] and ownership.has(unit.id) and unit.get("route","")==ownership[unit.id]):return false
	if not state.cleared_stages is Array:return false
	seen={}
	for id in state.cleared_stages:
		if not _integer(id,101,534) or not game.stages.has(int(id)) or seen.has(int(id)):return false
		if int(game.stages[int(id)].get("chapter",1))>int(state.chapter):return false
		seen[int(id)]=true
	if not _campaign_story(state.story_events):return false
	if not state.battle_return is Dictionary:return false
	if not state.battle_return.is_empty():
		if state.battle_return.get("mode") not in ["hub","world"] or not _integer(state.battle_return.get("world_node"),1,39):return false
	if not _campaign_flags(game,state.flags,stage):return false
	if not state.units.is_empty() and state.flags.get("quest",{}).is_empty():return false
	if int(state.chapter)>=2 and (not state.flags.get("chapter1_complete",false) or not state.flags.get("chapter2_started",false) or not seen.has(105)):return false
	if int(state.chapter)==3:
		if not state.flags.get("chapter2_complete",false) or not state.flags.get("chapter3_started",false) or not seen.has(206):return false
		if not state.flags.get("chapter3_previous") is Dictionary or not state.flags.get("chapter3_recruits") is Dictionary:return false
		for side in ["alm","celica"]:
			var nodes=[6,7,8,35,9] if side=="alm" else [6,24,25,36,9]
			if not _integer(state.flags.chapter3_previous.get(side),1,39) or int(state.flags.chapter3_previous[side]) not in nodes:return false
			if int(state.route_positions[side]) not in nodes:return false
		if int(state.world_node) not in ([6,7,8,35,9] if state.route=="alm" else [6,24,25,36,9]):return false
		for id in state.flags.chapter3_recruits:
			if id not in ["german","noya"] or not state.flags.chapter3_recruits[id] is bool:return false
		if state.flags.get("D32_done",false) and (not seen.has(301) or not seen.has(304)):return false
		if state.flags.get("D33_done",false) and (not seen.has(303) or not seen.has(306)):return false
		if int(state.stage_id)==302 and not state.units.is_empty():
			var index=int(state.flags.quest.transport_index)
			for unit in state.units:
				if unit.id=="transport_cart" and unit.position!=stage.transport_path[index]:return false
	if int(state.chapter)==4:
		if not state.flags.get("chapter3_complete",false) or not state.flags.get("chapter4_started",false) or not state.flags.get("D33_done",false):return false
		if not seen.has(303) or not seen.has(306) or not state.flags.get("chapter4_previous") is Dictionary:return false
		for side in ["alm","celica"]:
			var nodes=[9,10,11,12,13,37] if side=="alm" else [9,26,27,28,29,38]
			if not _integer(state.flags.chapter4_previous.get(side),1,39) or int(state.flags.chapter4_previous[side]) not in nodes or int(state.route_positions[side]) not in nodes:return false
		if int(state.world_node) not in ([9,10,11,12,13,37] if state.route=="alm" else [9,26,27,28,29,38]):return false
		if state.flags.get("obs_steps_ready",false) and not seen.has(406):return false
		if state.flags.get("m43_seized",false) and not seen.has(403):return false
		if state.flags.get("west_tower_safe",false) and (not seen.has(403) or not state.flags.get("obs_steps_ready",false)):return false
		if state.flags.get("island_loop_safe",false) and not seen.has(408):return false
		if state.flags.get("D42_done",false) and (not state.flags.get("west_tower_safe",false) or not state.flags.get("island_loop_safe",false)):return false
		if state.flags.get("chapter4_closed",false) and (not seen.has(404) or not state.flags.get("D42_done",false)):return false
	if int(state.chapter)==5:
		if not state.flags.get("chapter4_closed",false) or not state.flags.get("D42_done",false) or not seen.has(404) or not seen.has(408):return false
		if not state.flags.get("chapter5_started",false) or not state.flags.get("chapter5_previous") is Dictionary or not state.flags.get("chapter5_deployment") is Dictionary or not state.flags.get("chapter5_ready") is Dictionary:return false
		for side in ["alm","celica"]:
			var nodes=[13,14,15,16] if side=="alm" else [29,30,39,15,16]
			if int(state.route_positions[side]) not in nodes or not _integer(state.flags.chapter5_previous.get(side),1,39) or int(state.flags.chapter5_previous[side]) not in nodes:return false
			if not state.flags.chapter5_ready.get(side) is bool:return false
			var chosen=state.flags.chapter5_deployment.get(side,[])
			if not chosen is Array or chosen.size()>10:return false
			var unique={}
			for id in chosen:
				if not state.parties[side].has(id) or unique.has(id):return false
				unique[id]=true
			if state.flags.get("chapter5_merged",false) and not chosen.has("hunapu" if side=="alm" else "eileen"):return false
		if state.flags.get("west_palace_gate",false) and not seen.has(502):return false
		if state.flags.get("east_palace_gate",false) and not seen.has(504):return false
		if state.flags.get("chapter5_merged",false) and (not seen.has(502) or not seen.has(504) or not state.flags.chapter5_ready.alm or not state.flags.chapter5_ready.celica):return false
		if state.flags.get("final_access",false) and not seen.has(533):return false
		if state.flags.get("campaign_complete",false) and not seen.has(534):return false
	if state.get("mode","")=="ending" and (int(state.chapter)!=5 or not seen.has(534) or not state.flags.get("campaign_complete",false)):return false
	if snapshot and state.flags.has("active_plot"):return false
	return true

static func _campaign_unit(game, unit: Variant, tactical: bool) -> bool:
	if not unit is Dictionary or not unit.get("id") is String or unit.id.is_empty():return false
	if unit.get("side") not in ["player","enemy","neutral","evacuated"]:return false
	for key in ["hp","strength","skill","speed","luck","defence","move"]:
		if not _integer(unit.get(key),0,255):return false
	if not _integer(unit.get("max_hp"),1,255) or int(unit.hp)>int(unit.max_hp):return false
	if not _integer(unit.get("class_id"),1,255) or not game.catalog.classes.has(str(int(unit.class_id))):return false
	if not Items.HeroProfessions.valid_marker(unit):return false
	if not _integer(unit.get("level"),1,20) or not unit.get("acted") is bool:return false
	if not unit.get("name_zh") is String:return false
	if tactical and not _point(unit.get("position")):return false
	if unit.has("item_id") and not (_integer(unit.item_id,0,0) or _carried_item(unit.item_id)):return false
	if unit.has("drop_chance") and not _integer(unit.drop_chance,0,100):return false
	for key in ["exp","magic_level","magic_flags","raw_magic_flags","character_id","name_id","resistance","ai_flags","raw_ai_flags","record_index","exp_value","weapon_index"]:
		if unit.has(key) and not _integer(unit[key],0,65535):return false
	if unit.has("treatment_count") and not _integer(unit.treatment_count,0,1):return false
	for key in ["dead","dying","ever_dying","acted","neutral","controllable","temporary","locked","hidden","event_object","no_counter","no_experience","no_drop","surrendered","battle_guard","promoted"]:
		if unit.has(key) and not unit[key] is bool:return false
	if unit.has("route") and unit.route not in ["alm","celica"]:return false
	if unit.has("growths"):
		if not unit.growths is Dictionary:return false
		for key in unit.growths:
			if not _integer(unit.growths[key],0,255):return false
	return true

static func _campaign_pages(value: Variant) -> bool:
	if not value is Array:return false
	for page in value:
		if not page is Dictionary or not page.get("speaker") is String or not page.get("text") is String:return false
	return true

static func _campaign_story(value: Variant) -> bool:
	if not value is Array:return false
	for event in value:
		if not event is Dictionary or event.get("kind")!="new_story" or not _campaign_pages(event.get("pages")) or not event.get("key") is String:return false
	return true

static func _campaign_flags(game, flags: Dictionary, stage: Dictionary) -> bool:
	if flags.has("ending_pages"):
		if not flags.ending_pages is Array or flags.ending_pages.is_empty() or flags.ending_pages.size()>200:return false
		for page in flags.ending_pages:
			if not page is Dictionary or not page.get("title") is String or not page.get("text") is String or not _integer(page.get("source_id"),0,255):return false
		if not _integer(flags.get("ending_index"),0,flags.ending_pages.size()-1):return false
	for key in ["chapter5_started","chapter5_merged","west_palace_gate","east_palace_gate","east_network_ready","S51_invited","S51_closed","S51_records_saved","M51_confirmed","chapter5_complete","campaign_complete","ending_done","final_access"]:
		if flags.has(key) and not flags[key] is bool:return false
	for key in ["equipment_clear_rewards","equipment_starter_checked"]:
		if not flags.has(key):continue
		if not flags[key] is Dictionary:return false
		for id in flags[key]:
			if not flags[key][id] is bool:return false
			if key=="equipment_starter_checked" and not game.characters.has(id):return false
			if key=="equipment_clear_rewards" and not game.stages.has(int(id)):return false
	for key in ["pending_loot","loot_notifications"]:
		if not flags.has(key):continue
		if not flags[key] is Array:return false
		for record in flags[key]:
			if not _loot_record(record) or (key=="pending_loot" and not game.characters.has(record.unit_id)):return false
	for key in ["chapter4_started","chapter4_complete","chapter4_closed","chapter5_pending","west_tower_safe","island_loop_safe","D42_done","obs_steps_ready","m43_seized","transfer_cut","M41_confirmed","F41_confirmed","F43_confirmed","S41_invited","S42_invited","celine_ready","S42_settled","S41_register_saved","chapter3_started","chapter3_complete","chapter4_pending","D31_done","D32_done","D33_done","M32_confirmed","M33_confirmed","F32_confirmed","F33_confirmed","S31_invited","S32_invited","chapter1_complete","chapter2_started","chapter2_complete","chapter3_pending","east_departure_ready","F21_confirmed","F22_confirmed","F23_confirmed","islanders_settled","sea_chart_collected","east_departure_confirmed","S21_invited","S22_invited"]:
		if flags.has(key) and not flags[key] is bool:return false
	if flags.has("active_plot"):
		var plot=flags.active_plot
		if not plot is Dictionary or not _campaign_pages(plot.get("pages")) or not _integer(plot.get("index"),0,plot.pages.size()-1):return false
	if flags.has("east_recruit_ready"):
		if not flags.east_recruit_ready is Dictionary:return false
		for id in flags.east_recruit_ready:
			if id not in ["lord","roan","shia"] or not flags.east_recruit_ready[id] is bool:return false
	if flags.has("quest"):
		var q=flags.quest
		if not q is Dictionary:return false
		if q.is_empty():return true
		for key in ["objects","evacuated","freed","burn_streak","reinforced","mid_done"]:
			if not q.has(key):return false
		if not q.objects is Dictionary or not q.evacuated is Array or not q.freed is Array:return false
		var object_ids=[]
		for o in stage.get("objects",[]):object_ids.append(str(o.id))
		for id in q.objects:
			if not id is String or not object_ids.has(id) or not q.objects[id] is bool:return false
		for id in q.evacuated:
			if not id is String:return false
		for index in q.freed:
			if not _integer(index,0,stage.get("objects",[]).size()-1):return false
		if not _integer(q.burn_streak,0,9999) or not q.reinforced is bool or not q.mid_done is bool:return false
		if int(stage.get("id",stage.get("stage_id",0)))>=200 and not q.has("boats"):return false
		if q.has("beacon_since") and not _integer(q.beacon_since,-1,2147483647):return false
		if q.has("beacon_contested") and not q.beacon_contested is bool:return false
		if int(stage.get("chapter",1))==3:
			if not _integer(q.get("transport_index"),0,maxi(0,stage.get("transport_path",[]).size()-1)) or not q.get("transport_stopped") is bool:return false
			if q.get("german_decision") not in ["","accepted","disarmed"]:return false
		if int(stage.get("chapter",1))==5:
			if not q.get("repair_since") is Dictionary or not q.get("final_phase") is bool or not q.get("summon_wave") is bool:return false
			for id in ["repair_1","repair_2"]:
				if not _integer(q.repair_since.get(id),-1,2147483647):return false
		if int(stage.get("chapter",1))==4:
			for name in ["record_lost","summon_wave","old_comrades_talked","transfer_cut_snapshot"]:
				if not q.get(name) is bool:return false
			if not _integer(q.get("burn_count"),0,9999) or not _integer(q.get("repair_since"),-1,2147483647):return false
			if not q.get("wells") is Dictionary or not q.get("well_since") is Dictionary:return false
			for name in ["well_n","well_s"]:
				if not q.wells.get(name) is bool or not _integer(q.well_since.get(name),-1,2147483647):return false
		if q.has("boats"):
			if not q.boats is Array or q.boats.size()!=stage.get("event_boats",[]).size():return false
			var boat_ids={}
			for source in stage.get("event_boats",[]):boat_ids[source.id]=source
			for boat in q.boats:
				if not boat is Dictionary or not boat_ids.has(boat.get("id")):return false
				var source: Dictionary=boat_ids[boat.id];boat_ids.erase(boat.id)
				if boat.get("speed",4)!=source.get("speed",4) or boat.get("delay",0)!=source.get("delay",0):return false
				if boat.get("path")!=source.path or not _integer(boat.get("path_index"),0,source.path.size()-1):return false
				if not _integer(boat.get("hp"),0,int(source.max_hp)) or boat.get("max_hp")!=source.max_hp:return false
				if boat.get("position")!=source.path[int(boat.path_index)] or not boat.get("arrived") is bool or not boat.get("stopped") is bool:return false
				if boat.arrived and int(boat.path_index)!=source.path.size()-1:return false
	return true
