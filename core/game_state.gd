class_name FeGameState
extends RefCounted

# The game runs on native data and state, never on a ROM/6502 emulator.
# Canonical source coordinates are stored as [x,y] for JSON save compatibility.
const Rules = preload("res://core/combat_rules.gd")
const Items = preload("res://core/item_rules.gd")
const Progression = preload("res://core/unit_progression.gd")
const Scenario = preload("res://core/scenario_rules.gd")
const WorldArmies = preload("res://core/world_armies.gd")
const WORLD_ENCOUNTER_FLAGS = ["inventory_enemy_initiated", "inventory_attacking_group_id", "inventory_attacker_previous_node", "inventory_attacking_instance_id"]
const Summons = preload("res://core/summon_rules.gd")
const TacticalAI = preload("res://core/tactical_ai.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const SaveValidation = preload("res://core/campaign_save_validation.gd")
const DIRECTIONS = [Vector2i.UP, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.DOWN]
const SAVE_PATH = "user://opening_and_ram_woods.json"

var opening: Dictionary
var catalog: Dictionary = {}
var characters: Dictionary = {}
var hubs: Dictionary = {}
var chapter: int = 1
var route: String = "alm"
var parties: Dictionary = {"alm": ["alm"], "celica": []}
var route_positions: Dictionary = {"alm": 49, "celica": 53}
var previous_world_node: int = 49
var world_armies: Dictionary = {}
var convoy: Dictionary = {"alm": [], "celica": []}
var hub_id: int = 1
var hub_position := Vector2i(5, 10)
var hub_flags: Dictionary = {}
var hub_changes: Dictionary = {}
var hub_used: Dictionary = {}
var battle_return: Dictionary = {}
var battle_settled := false
var story_events: Array = []
var encounter_groups: Array = []
var battle_data: Dictionary
var stages: Dictionary = {}
var stage_id: int = 1
var world_node: int = 49
var cleared_stages: Array = []
var roster: Dictionary = {}
var battle_start_snapshot: Dictionary = {}
var victory_rewards: Array = []
var flags: Dictionary = {}
var party: Array = ["alm"]
var mode: String = "title"
var village_position := Vector2i(5, 10)
var village_facing := Vector2i.DOWN
var units: Array = []
var phase: String = "player"
var turn: int = 1
var rng_state: int = 0
var frame_counter: int = 0
var kills: int = 0
var selected_id: String = ""
var cursor := Vector2i(6, 5)
var move_origin := Vector2i.ZERO
var battle_outcome: String = ""
var log_lines: Array[String] = []
var save_path: String = SAVE_PATH

func _init() -> void:
	opening = read_json("res://data/opening.json")
	stages = {1: read_json("res://data/first_battle.json"), 2: read_json("res://data/second_battle.json")}
	catalog = read_json("res://data/campaign.json")
	characters = catalog.get("characters", stages[1].characters).duplicate(true)
	for key in catalog.get("stages", {}):
		if int(key) > 2:
			stages[int(key)] = read_json(str(catalog.stages[key].path))
	# Keep the old two-battle save IDs, but use the complete source tables.
	for id in [1, 2]:
		var full = read_json(str(catalog.stages[str(id)].path))
		for field in ["terrain", "deployment", "enemy_group_ids", "player_positions_by_party"]:
			stages[id][field] = full[field].duplicate(true)
		for index in range(stages[id].enemies.size()):
			stages[id].enemies[index].merge(full.enemies[index], false)
	hubs = read_json("res://data/hubs.json")
	opening.characters.merge(characters, false)
	battle_data = stages[1]

static func read_json(path: String) -> Dictionary:
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null: return {}
	var parser = JSON.new()
	if parser.parse(file.get_as_text()) != OK: return {}
	return parser.data if parser.data is Dictionary else {}

func new_game() -> void:
	flags.clear()
	chapter = 1
	route = "alm"
	parties = {"alm": ["alm"], "celica": []}
	route_positions = {"alm": 49, "celica": 53}
	previous_world_node = 49
	flags.world_route_previous_nodes = {"alm": 49, "celica": 53}
	flags.world_route_encounters = {}
	convoy = {"alm": [], "celica": []}
	hub_id = 1
	hub_position = Vector2i(5, 10)
	hub_flags.clear()
	hub_changes.clear()
	hub_used.clear()
	battle_return.clear()
	story_events.clear()
	for room in hubs.get("initial_trigger_masks", {}):
		hub_flags[room] = {"actors": 0, "talk": 0, "triggers": int(hubs.initial_trigger_masks[room])}
	_setup_chapter_armies()
	party = ["alm"]
	units.clear()
	roster.clear()
	roster.alm = _initial_character("alm")
	stage_id = 1
	battle_data = stages[1]
	world_node = 49
	cleared_stages.clear()
	battle_start_snapshot.clear()
	victory_rewards.clear()
	phase = "player"
	turn = 1
	kills = 0
	rng_state = 0
	frame_counter = 0
	battle_outcome = ""
	selected_id = ""
	village_position = Vector2i(opening.village.spawn[0], opening.village.spawn[1])
	village_facing = Vector2i.DOWN
	mode = "chapter"
	Scenario.on_chapter(self, 0, 1)

func tick() -> void:
	frame_counter = (frame_counter + 1) & 255
	# L0FC04E: eleven increments by five, once per main-loop synchronization.
	rng_state = (rng_state + 55) & 255

func random_bounded(upper: int) -> int:
	rng_state = (rng_state + 55) & 255
	# L0FC068/L0FC6C9 return the high byte of an unsigned 8-bit product.
	return (rng_state * upper) >> 8

func recruit(id: String) -> void:
	if not characters.has(id):
		return
	if bool(roster.get(id, {}).get("dead", false)) or bool(flags.get("unrecruitable_" + id, false)):
		return
	if not party.has(id):
		party.append(id)
		if not roster.has(id):
			roster[id] = _initial_character(id)
		roster[id].controllable = true
		roster[id].neutral = false
		roster[id].no_experience = false
		parties[route] = party.duplicate()

func dialogue_for_npc(id: String) -> String:
	if id == "mycen":
		return "mycen_refusal" if flags.get("heard_lukas", false) else "training"
	if id == "lukas":
		if flags.get("joined_deliverance", false):
			return "lukas_join_repeat"
		return "alm_volunteers" if flags.get("mycen_refused", false) else "lukas_report"
	if flags.get("joined_deliverance", false):
		return id + "_joins"
	if not flags.get("heard_lukas", false):
		return "friends_greeting"
	return {"gray": "gray_advice", "tobin": "tobin_encouragement", "kliff": "kliff_reaction"}.get(id, "friends_greeting")

func complete_dialogue(key: String) -> void:
	match key:
		"lukas_report": flags.heard_lukas = true
		"mycen_refusal": flags.mycen_refused = true
		"alm_volunteers":
			flags.joined_deliverance = true
			recruit("lukas")
		"gray_joins": recruit("gray")
		"tobin_joins": recruit("tobin")
		"kliff_joins": recruit("kliff")

func _initial_character(id: String) -> Dictionary:
	var unit: Dictionary = characters.get(id, stages[1].characters.get(id, {})).duplicate(true)
	unit.id = id
	unit.side = "player"
	unit.dead = false
	unit.acted = false
	unit.magic_level = 0
	return unit

func character_key(source_id: int) -> String:
	for key in characters:
		if int(characters[key].get("character_id", characters[key].get("id", 0))) == source_id:
			return str(key)
	return ""

func leader_id() -> String:
	return "celica" if route == "celica" else "alm"

func _setup_chapter_armies() -> void:
	world_armies.clear()
	for record in catalog.get("chapter_armies", {}).get(str(chapter), []):
		var key = str(int(record.world_node))
		if not world_armies.has(key):
			world_armies[key] = []
		world_armies[key].append(int(record.group_id))
	var variants: Array = catalog.get("chapter_random_armies", [])
	if not variants.is_empty():
		var record: Dictionary = variants[random_bounded(variants.size()) if chapter > 2 else 0].by_chapter.get(str(chapter), {})
		if int(record.get("world_node", 0)) > 0:
			world_armies[str(int(record.world_node))] = [int(record.group_id)]
	WorldArmies.reset_for_chapter(self)

func allowed_world_nodes() -> Array[int]:
	var result: Array[int] = []
	var regions: Dictionary = catalog.get("routes", {}).get(route, {}).get("chapter_nodes", {})
	for key in regions:
		if int(key) <= chapter:
			for node in regions[key]:
				if not result.has(int(node)):
					result.append(int(node))
	return result

func world_neighbors() -> Array[int]:
	var result: Array[int] = []
	var allowed = allowed_world_nodes()
	for node in catalog.get("world_nodes", {}).get(str(world_node), {}).get("neighbors", []):
		if int(node) in allowed and Scenario.can_travel(self, world_node, int(node)):
			if world_armies.get(str(world_node), []).is_empty() or int(node) == previous_world_node:
				result.append(int(node))
	return result

func travel_to(node: int) -> bool:
	if not world_neighbors().has(node):
		return false
	flags.erase("inventory_enemy_initiated")
	flags.erase("inventory_attacking_group_id")
	flags.erase("inventory_attacker_previous_node")
	flags.erase("inventory_attacking_instance_id")
	flags.erase("world_route_approach_recovered_" + route)
	previous_world_node = world_node
	world_node = node
	route_positions[route] = node
	Scenario.on_travel(self)
	remember_world_approach()
	return true

func world_has_battle(node: int) -> bool:
	return not world_armies.get(str(node), []).is_empty()

func can_switch_route() -> bool:
	if chapter < 3: return false
	var target = "celica" if route == "alm" else "alm"
	if parties.get(target, []).is_empty(): return false
	# L079432/L079468: world selection skips a frozen/captive party.
	if target == "celica" and bool(flags.get("celica_captive", false)): return false
	if target == "alm" and bool(flags.get("scenario_alm_frozen", false)): return false
	return not bool(flags.get("final_parties_merged", false)) and not bool(flags.get("campaign_complete", false))

func switch_route() -> bool:
	if not can_switch_route():
		return false
	remember_world_approach()
	parties[route] = party.duplicate()
	route_positions[route] = world_node
	route = "celica" if route == "alm" else "alm"
	party = parties[route].duplicate()
	world_node = int(route_positions[route])
	restore_world_approach()
	units.clear()
	selected_id = ""
	battle_outcome = ""
	battle_return = {"mode": "world", "world_node": world_node}
	mode = "world"
	return true

func remember_world_approach() -> void:
	# L06B7A6/L06B7C6 use $6D16,X: each route keeps its own previous node.
	var previous: Dictionary = flags.get("world_route_previous_nodes", {})
	previous[route] = previous_world_node
	flags.world_route_previous_nodes = previous
	var encounters: Dictionary = flags.get("world_route_encounters", {})
	var encounter: Dictionary = {}
	for key in WORLD_ENCOUNTER_FLAGS:
		if flags.has(key): encounter[key] = flags[key]
	encounters[route] = encounter
	flags.world_route_encounters = encounters

func restore_world_approach() -> void:
	_restore_world_previous_node()
	var encounters: Dictionary = flags.get("world_route_encounters", {})
	var encounter: Dictionary = encounters.get(route, {})
	for key in WORLD_ENCOUNTER_FLAGS:
		flags.erase(key)
		if encounter.has(key): flags[key] = encounter[key]

func _restore_world_previous_node(recover_legacy: bool = false) -> void:
	var previous: Dictionary = flags.get("world_route_previous_nodes", {})
	previous_world_node = int(previous.get(route, world_node))
	if previous_world_node != world_node: return
	# A known self-origin is legitimate just after a retreat. Only infer
	# history for legacy/unrecorded routes; never rewrite a new checkpoint.
	if previous.has(route) and not recover_legacy: return
	# Older switches discarded this history. Recover a source-legal clear
	# adjacent exit when possible, rather than retaining an impossible self
	# retreat. Ambiguous old histories cannot reveal the exact original path.
	var allowed := allowed_world_nodes()
	var neighbors: Array = catalog.world_nodes[str(world_node)].get("neighbors", [])
	var recovery: Array = []
	var entry: Dictionary = hubs.world_entries.get(str(world_node), {})
	var fallback: Dictionary = entry.get("fallback_approach_by_chapter", {})
	if fallback.has(str(chapter)) and neighbors.has(int(fallback[str(chapter)])):
		recovery.append(int(fallback[str(chapter)]))
	recovery.append_array(neighbors)
	for candidate in recovery:
		var node := int(candidate)
		if node in allowed and not world_has_battle(node) and Scenario.can_travel(self, world_node, node):
			previous_world_node = node
			flags["world_route_approach_recovered_" + route] = true
			break

func available_stage(id: int) -> bool:
	return stages.has(id) and not stages[id].is_empty()

func stage_cleared(id: int) -> bool:
	return cleared_stages.has(id)

func can_enter_stage(id: int) -> bool:
	return available_stage(id) and (id > 48 or world_has_battle(id)) and (id == world_node or id in world_neighbors())

func start_battle(id: int = 1, groups: Array = [], from_hub: bool = false) -> bool:
	if not available_stage(id) or (not from_hub and id != world_node and id not in world_neighbors()):
		return false
	stage_id = id
	if not from_hub:
		world_node = id
		battle_return = {"mode": "world", "world_node": world_node}
	battle_data = stages[id].duplicate(true)
	encounter_groups = groups.duplicate() if not groups.is_empty() else world_armies.get(str(world_node), battle_data.get("enemy_group_ids", [])).duplicate()
	var battle_instances = WorldArmies.current_battle_instances(self, encounter_groups, from_hub)
	if not encounter_groups.is_empty():
		battle_data.enemies = _build_enemy_groups(encounter_groups, battle_data, battle_instances)
	units.clear()
	var deployment_slot := 0
	for member in party:
		if not roster.has(member):
			roster[member] = _initial_character(str(member))
		var unit: Dictionary = roster[member].duplicate(true)
		if bool(unit.get("dead", false)) or int(unit.hp) <= 0:
			continue
		if deployment_slot >= battle_data.player_positions.size():
			break
		unit.id = str(member)
		unit.side = "player"
		unit.position = battle_data.player_positions[deployment_slot].duplicate()
		deployment_slot += 1
		# L068BD5/L068C0C: retain persistent stats/EXP/item and deploy alive
		# units with current HP filled from their persistent maximum HP.
		unit.hp = int(unit.max_hp)
		unit.acted = false
		unit.erase("weapon_index")
		units.append(unit)
	for source_index in range(battle_data.enemies.size()):
		var source: Dictionary = battle_data.enemies[source_index]
		var unit: Dictionary = source.duplicate(true)
		unit.enemy_slot = source_index
		unit.side = "enemy"
		unit.acted = false
		unit.exp = 0
		unit.exp_value = int(source.get("exp_value", 30))
		units.append(unit)
	turn = 1
	phase = "player"
	kills = 0
	selected_id = ""
	battle_outcome = ""
	battle_settled = false
	victory_rewards.clear()
	if units.is_empty():
		battle_outcome = "defeat"
		return false
	cursor = pos(units[0])
	mode = "battle"
	log_lines.clear()
	Scenario.on_battle_start(self)
	if mode != "battle" or units.is_empty():
		if mode == "world":
			battle_return = {"mode": "world", "world_node": world_node}
		return true
	var player_slot = 0
	for unit in units:
		if unit.side == "player":
			unit.player_slot = player_slot
			player_slot += 1
	Inventory.on_battle_start(self)
	cursor = pos(find_unit(leader_id()))
	battle_start_snapshot = _capture_battle_start()
	return true

func _build_enemy_groups(groups: Array, stage: Dictionary, instances: Array = []) -> Array:
	var expected: Array = stage.get("enemy_group_ids", [])
	if groups.size() == expected.size() and range(groups.size()).all(func(i): return int(groups[i]) == int(expected[i])):
		# Keep original/legacy unit IDs for fixed formations and suspend saves.
		var result: Array = stage.enemies.duplicate(true)
		for unit in result:
			for i in range(groups.size()):
				if int(unit.get("group_id", -1)) == int(groups[i]) and i < instances.size():
					unit.army_instance = str(instances[i])
					break
		return result
	var result: Array = []
	var ordered: Array = range(groups.size())
	if ordered.size() == 2:
		var first = int(catalog.enemy_groups[str(int(groups[0]))].get("deployment_priority", 0))
		var second = int(catalog.enemy_groups[str(int(groups[1]))].get("deployment_priority", 0))
		if first >= second: ordered.reverse()
	var layouts: Array = stage.get("deployment", {}).get("layouts", [])
	for group_index in range(ordered.size()):
		var source_index = int(ordered[group_index])
		var data: Dictionary = catalog.enemy_groups.get(str(int(groups[source_index])), {})
		if not data.get("valid", false): continue
		var positions: Array = layouts[mini(group_index + 2, layouts.size() - 1)].positions.duplicate() if not layouts.is_empty() else stage.enemy_positions.duplicate()
		if ordered.size() == 1 and layouts.size() >= 4: positions.append_array(layouts[3].positions)
		for i in range(mini(data.enemies.size(), positions.size())):
			var unit: Dictionary = data.enemies[i].duplicate(true)
			unit.id = str(unit.id) + "_army" + str(group_index)
			unit.position = positions[i].duplicate()
			if source_index < instances.size(): unit.army_instance = str(instances[source_index])
			result.append(unit)
	return result

func support_targets(caster: Dictionary, spell_id: int) -> Array:
	var reach = Items.support_range(spell_id)
	var candidates = living("enemy" if Items.spell(spell_id).get("action", "") == "expel" else str(caster.side))
	return candidates.filter(func(unit):
		var distance = absi(pos(unit).x - pos(caster).x) + absi(pos(unit).y - pos(caster).y)
		if str(unit.id) == str(caster.id):
			return false
		return distance >= reach.x and distance <= reach.y and Items.support_effect(caster, unit, spell_id).valid)

func use_support(caster_id: String, spell_id: int, target_id: String = "", destination: Vector2i = Vector2i(-1, -1)) -> Dictionary:
	var caster = find_unit(caster_id)
	if caster.is_empty() or int(caster.hp) <= 0 or bool(caster.acted) or not spell_id in Items.spells(caster):
		return {}
	var info = Items.spell(spell_id)
	var target = find_unit(target_id)
	var global = str(info.get("action", "")) in ["fortify", "invoke", "conjure", "expel"]
	if target.is_empty() and global:
		target = caster
	if target.is_empty() or (not global and not support_targets(caster, spell_id).has(target)):
		return {}
	if str(info.action) == "warp" and (not in_bounds(destination) or not can_stop(target, destination) or movement_cost(target, destination) >= 255):
		return {}
	var effect = Items.support_effect(caster, target, spell_id, random_bounded(int(caster.strength)) if str(info.action) in ["invoke", "conjure"] else random_bounded(100))
	if not effect.valid:
		return {}
	var result = {"caster": caster_id, "spell_id": spell_id, "action": info.action, "changed": [], "spawned": []}
	caster.hp = int(caster.hp) - int(effect.hp_cost) - int(effect.repeat_cost)
	match str(info.action):
		"recover", "physic":
			var before = int(target.hp)
			target.hp = mini(int(target.max_hp), before + int(effect.heal) + int(effect.repeat_heal))
			result.changed.append({"id": target_id, "before": before, "after": target.hp})
		"fortify":
			for unit in living(str(caster.side)):
				if str(unit.id) == caster_id:
					continue
				var before = int(unit.hp)
				unit.hp = mini(int(unit.max_hp), before + int(caster.strength))
				result.changed.append({"id": unit.id, "before": before, "after": unit.hp})
		"warp":
			target.position = [destination.x, destination.y]
			cursor = destination
			result.changed.append({"id": target_id, "position": target.position})
		"invoke", "conjure":
			result.spawned = _summon(caster, int(effect.summon_class), int(effect.summon_count))
		"expel":
			var enemy_slots = units.filter(func(unit): return unit.side == "enemy")
			for unit in living("enemy"):
				if int(unit.get("enemy_slot", enemy_slots.find(unit))) == 0: continue
				var outcome = Items.support_effect(caster, unit, spell_id, random_bounded(256))
				if bool(outcome.expel):
					result.changed.append({"id": unit.id, "before": unit.hp, "after": 0})
					unit.hp = 0
	# Original white magic bypasses combat experience entirely.
	caster.acted = true
	caster.erase("weapon_index")
	selected_id = ""
	check_outcome()
	return result

func _summon(caster: Dictionary, class_id: int, count: int, spec: Dictionary = {}) -> Array:
	var result: Array = []
	var template = Summons.spawn_unit(caster, class_id, spec, route)
	if template.is_empty(): return result
	for raw in Items.summon_offsets():
		if result.size() >= count or Summons.available_slots(self, str(caster.side)) <= 0: break
		var cell = pos(caster) + Vector2i(int(raw[1]), int(raw[0]))
		var unit = template.duplicate(true)
		if not in_bounds(cell) or cell.x <= 0 or cell.y <= 0 or cell.x >= int(battle_data.map.width)-1 or cell.y >= int(battle_data.map.height)-1 or not unit_at(cell).is_empty() or movement_cost(unit, cell) >= 255: continue
		unit.id = "summon_" + str(frame_counter) + "_" + str(units.size())
		unit.name_zh = "幻影" if caster.side == "player" else catalog.classes[str(class_id)].enemy_name_zh
		unit["class"] = catalog.classes[str(class_id)].get("enemy_key", catalog.classes[str(class_id)].key) if caster.side == "enemy" else catalog.classes[str(class_id)].key
		unit.position = [cell.x, cell.y]
		var slot_key = "enemy_slot" if unit.side == "enemy" else "player_slot"
		for slot in range(1 if unit.side == "enemy" else 0, 20):
			var occupied = units.any(func(other):
				return other.side == unit.side and int(other.get(slot_key, -1)) == slot and (int(other.hp) > 0 or (unit.side == "player" and int(other.get("character_id", 0)) != 35)))
			if not occupied:
				unit[slot_key] = slot
				break
		if not unit.has(slot_key): break
		units.append(unit)
		result.append(unit.id)
	return result

func camp_unit(id: String) -> Dictionary:
	return roster.get(id, {})

func exchange_items(first_id: String, second_id: String) -> bool:
	if not party.has(first_id) or not party.has(second_id) or first_id == second_id:
		return false
	var a = roster[first_id]
	var b = roster[second_id]
	if bool(a.get("dead", false)) or bool(b.get("dead", false)):
		return false
	var item = int(a.get("item_id", 0))
	a.item_id = int(b.get("item_id", 0))
	b.item_id = item
	return true

func give_item(item_id: int) -> bool:
	for id in party:
		if not bool(roster[id].get("dead", false)) and int(roster[id].get("item_id", 0)) == 0:
			roster[id].item_id = item_id
			return true
	if convoy[route].size() >= 40: return false
	convoy[route].append(item_id)
	return true

func promote_unit(id: String, class_id: int, story: bool = false) -> Dictionary:
	if not party.has(id):
		return {}
	var result = Progression.promote(roster[id], class_id, story)
	if result.valid:
		roster[id] = result.unit
		roster[id]["class"] = catalog.classes[str(int(roster[id].class_id))].key
	return result

func apply_hub_flag(flag_id: int) -> void:
	var updates: Array = hubs.get("flag_updates", [])
	if flag_id < 1 or flag_id > updates.size():
		return
	var data: Array = updates[flag_id - 1]
	var room = str(int(data[0]) + 1)
	var state = hub_flags.get(room, {"actors": 0, "talk": 0, "triggers": 0})
	state.actors = (int(state.actors) & int(data[1])) | int(data[4])
	state.talk = (int(state.talk) & int(data[2])) | int(data[5])
	state.triggers = (int(state.triggers) & int(data[3])) | int(data[6])
	hub_flags[room] = state
	flags["source_flag_" + str(flag_id)] = true
	Scenario.after_hub_flag(self, flag_id)

func hub_room() -> Dictionary:
	var room: Dictionary = hubs.rooms.get(str(hub_id), {}).duplicate(true)
	for key in hub_changes.get(str(hub_id), {}):
		room.tiles[int(key)] = int(hub_changes[str(hub_id)][key])
	return room

func hub_actors() -> Array:
	var state: Dictionary = hub_flags.get(str(hub_id), {"actors": 0, "talk": 0, "triggers": 0})
	var variants: Array = hubs.rooms.get(str(hub_id), {}).get("actors", [])
	if variants.is_empty():
		return []
	return variants[1 if int(state.actors) & 128 else 0].filter(func(actor): return not (int(state.actors) & (1 << (int(actor.actor_id) - 2)))).duplicate(true)

func hub_script(actor_id: int = 0, cell: Vector2i = Vector2i(-1, -1)) -> int:
	var state: Dictionary = hub_flags.get(str(hub_id), {"actors": 0, "talk": 0, "triggers": 0})
	var triggers: Array = hubs.rooms.get(str(hub_id), {}).get("triggers", [])
	for i in range(triggers.size()):
		if not (int(state.triggers) & (1 << i)):
			continue
		var trigger: Dictionary = triggers[i]
		if actor_id > 0 and int(trigger.actor_id) == actor_id:
			return int(trigger.script_id)
		if actor_id == 0 and int(trigger.actor_id) == 0 and Vector2i(trigger.position[0], trigger.position[1]) == cell:
			return int(trigger.script_id)
	return -1

func enter_hub(id: int, at: Vector2i) -> bool:
	if not hubs.rooms.has(str(id)):
		return false
	hub_id = id
	hub_position = at
	mode = "hub"
	battle_outcome = ""
	units.clear()
	return true

func world_hub_entry() -> Dictionary:
	var entry: Dictionary = hubs.world_entries.get(str(world_node), {})
	entry = entry.duplicate(true)
	var approaches: Dictionary = entry.get("approach_entries", {})
	if not approaches.is_empty():
		var approach := str(previous_world_node)
		if not approaches.has(approach):
			var fallback: Dictionary = entry.get("fallback_approach_by_chapter", {})
			approach = str(int(fallback.get(str(chapter), int(approaches.keys()[0]))))
		var arrival: Dictionary = approaches.get(approach, {})
		if not arrival.is_empty():
			entry.spawn = arrival.spawn.duplicate()
			entry.facing = int(arrival.facing)
	return entry

func enter_world_hub() -> bool:
	var entry := world_hub_entry()
	if entry.is_empty(): return false
	return enter_hub(int(entry.hub_id), Vector2i(entry.spawn[0], entry.spawn[1]))

func enter_dungeon_battle(trigger: int) -> bool:
	flags.erase("inventory_enemy_initiated")
	flags.erase("inventory_attacking_group_id")
	flags.erase("inventory_attacker_previous_node")
	flags.erase("inventory_attacking_instance_id")
	var encounters: Array = catalog.get("dungeon_encounters", [])
	if trigger < 0 or trigger >= encounters.size():
		return false
	var encounter: Dictionary = encounters[trigger]
	battle_return = {"mode": "hub", "hub_id": hub_id, "position": [hub_position.x, hub_position.y], "world_node": world_node}
	return start_battle(int(encounter.battle_map_id), encounter.enemy_group_ids, true)

func next_chapter(transition: int) -> bool:
	var entry: Dictionary = hubs.get("chapter_transitions", {}).get(str(transition), {})
	if entry.is_empty() or chapter >= 5:
		return false
	parties[route] = party.duplicate()
	chapter += 1
	route = "celica" if chapter == 2 else "alm"
	party = parties[route].duplicate()
	if party.is_empty():
		recruit(leader_id())
	if chapter == 3:
		route_positions.celica = 18
	if chapter < 5:
		_setup_chapter_armies()
	Scenario.on_chapter(self, chapter - 1, chapter)
	world_node = int(route_positions[route])
	enter_hub(int(entry.hub_id), Vector2i(entry.spawn[0], entry.spawn[1]))
	return true

func _capture_battle_start() -> Dictionary:
	return {"stage_id": stage_id, "units": units.duplicate(true), "roster": roster.duplicate(true),
		"party": party.duplicate(),
		"chapter": chapter, "route": route, "world_node": world_node, "world_armies": world_armies.duplicate(true),
		"previous_world_node": previous_world_node,
		"battle_return": battle_return.duplicate(true), "encounter_groups": encounter_groups.duplicate(),
		"parties": parties.duplicate(true), "route_positions": route_positions.duplicate(true),
		"hub_flags": hub_flags.duplicate(true), "story_events": story_events.duplicate(true),
		"convoy": convoy.duplicate(true), "hub_used": hub_used.duplicate(true), "hub_changes": hub_changes.duplicate(true),
		"cleared_stages": cleared_stages.duplicate(), "flags": flags.duplicate(true),
		"rng_state": rng_state, "frame_counter": frame_counter}

func retry_battle() -> bool:
	if battle_start_snapshot.is_empty():
		return false
	var snapshot := battle_start_snapshot.duplicate(true)
	stage_id = int(snapshot.stage_id)
	battle_data = stages[stage_id]
	chapter = int(snapshot.get("chapter", chapter))
	route = str(snapshot.get("route", route))
	world_node = int(snapshot.get("world_node", stage_id))
	world_armies = snapshot.get("world_armies", world_armies).duplicate(true)
	battle_return = snapshot.get("battle_return", {}).duplicate(true)
	encounter_groups = snapshot.get("encounter_groups", battle_data.get("enemy_group_ids", [])).duplicate()
	parties = snapshot.get("parties", parties).duplicate(true)
	route_positions = snapshot.get("route_positions", route_positions).duplicate(true)
	hub_flags = snapshot.get("hub_flags", hub_flags).duplicate(true)
	convoy = snapshot.get("convoy", convoy).duplicate(true)
	hub_used = snapshot.get("hub_used", hub_used).duplicate(true)
	hub_changes = snapshot.get("hub_changes", hub_changes).duplicate(true)
	story_events = snapshot.get("story_events", []).duplicate(true)
	units = snapshot.units.duplicate(true)
	party = snapshot.get("party", party).duplicate()
	roster = snapshot.roster.duplicate(true)
	cleared_stages = snapshot.cleared_stages.duplicate()
	flags = snapshot.flags.duplicate(true)
	previous_world_node = int(snapshot.get("previous_world_node", flags.get("world_route_previous_nodes", {}).get(route, previous_world_node)))
	rng_state = int(snapshot.rng_state)
	frame_counter = int(snapshot.frame_counter)
	turn = 1
	phase = "player"
	kills = 0
	selected_id = ""
	battle_outcome = ""
	battle_settled = false
	victory_rewards.clear()
	mode = "battle"
	WorldArmies.ensure(self)
	WorldArmies.bind_legacy_battle_units(self)
	cursor = pos(find_unit(leader_id()))
	log_lines.clear()
	return true

func complete_battle() -> bool:
	if battle_outcome != "victory" or battle_settled:
		return false
	victory_rewards.clear()
	for unit in units:
		if unit.side != "player" or bool(unit.get("temporary", false)) or bool(unit.get("neutral", false)):
			continue
		var before := int(unit.get("exp", 0))
		var gain := Rules.victory_experience_gain(unit)
		unit.exp = mini(99, before + gain)
		if gain > 0:
			victory_rewards.append({"unit": str(unit.id), "gain": gain,
				"exp_before": before, "exp_after": int(unit.exp), "actual_gain": int(unit.exp) - before})
		var persistent: Dictionary = unit.duplicate(true)
		persistent.dead = int(unit.hp) <= 0
		persistent.acted = false
		roster[str(unit.id)] = persistent
	if not stage_cleared(stage_id):
		cleared_stages.append(stage_id)
	battle_settled = true
	Scenario.on_victory(self)
	Inventory.on_victory(self)
	parties[route] = party.duplicate()
	if stage_id == 1:
		flags.first_battle_complete = true
	elif stage_id == 2:
		flags.second_battle_complete = true
	return true

static func pos(unit: Dictionary) -> Vector2i:
	return Vector2i(int(unit.position[0]), int(unit.position[1]))

func find_unit(id: String) -> Dictionary:
	for unit in units:
		if str(unit.id) == id:
			return unit
	return {}

func unit_at(cell: Vector2i, alive_only: bool = true) -> Dictionary:
	for unit in units:
		if pos(unit) == cell and (not alive_only or int(unit.hp) > 0):
			return unit
	return {}

func living(side: String) -> Array:
	return units.filter(func(unit): return unit.side == side and int(unit.hp) > 0)

func in_bounds(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < int(battle_data.map.width) and cell.y < int(battle_data.map.height)

func category(cell: Vector2i) -> int:
	if not in_bounds(cell):
		return -1
	var tile = battle_data.map.tiles[cell.y * int(battle_data.map.width) + cell.x]
	return int(battle_data.terrain.tile_categories.get(str(tile), 0))

func terrain_avoid(cell: Vector2i) -> int:
	var terrain_id = category(cell)
	var values: Array = battle_data.terrain.avoid_by_category
	return int(values[terrain_id]) if terrain_id >= 0 and terrain_id < values.size() else 0

func movement_cost(unit: Dictionary, cell: Vector2i) -> int:
	var terrain_id = category(cell)
	var values: Array = battle_data.terrain.movement_by_class_and_category.get(str(int(unit.class_id)), [])
	if terrain_id < 0 or terrain_id >= values.size(): return 255
	return int(values[terrain_id])

func reachable(unit: Dictionary, unrestricted: bool = false) -> Dictionary:
	var start = pos(unit)
	var costs: Dictionary = {start: 0}
	var previous: Dictionary = {}
	var queue: Array[Vector2i] = [start]
	var budget = 255 if unrestricted else Items.movement(unit)
	while not queue.is_empty():
		queue.sort_custom(func(a, b): return int(costs[a]) < int(costs[b]))
		var current: Vector2i = queue.pop_front()
		for direction in DIRECTIONS:
			var cell: Vector2i = current + direction
			if not in_bounds(cell):
				continue
			if cell.x <= 0 or cell.y <= 0 or cell.x >= int(battle_data.map.width) - 1 or cell.y >= int(battle_data.map.height) - 1:
				continue
			var occupant = unit_at(cell)
			if not occupant.is_empty() and occupant.side != unit.side:
				continue
			var step = movement_cost(unit, cell)
			var cost = int(costs[current]) + step
			if step >= 255 or cost > budget:
				continue
			if not costs.has(cell) or cost < int(costs[cell]):
				costs[cell] = cost
				previous[cell] = current
				if not queue.has(cell):
					queue.append(cell)
	return {"costs": costs, "previous": previous, "origin": start}

func path_to(unit: Dictionary, destination: Vector2i) -> Array[Vector2i]:
	var graph = reachable(unit)
	var path: Array[Vector2i] = []
	if not graph.costs.has(destination):
		return path
	var cell = destination
	path.push_front(cell)
	while cell != pos(unit):
		cell = graph.previous[cell]
		path.push_front(cell)
	return path

func can_stop(unit: Dictionary, cell: Vector2i) -> bool:
	var other = unit_at(cell)
	return other.is_empty() or str(other.id) == str(unit.id)

func select_unit(id: String) -> bool:
	var unit = find_unit(id)
	if unit.is_empty() or unit.side != phase or int(unit.hp) <= 0 or unit.acted or not bool(unit.get("controllable", true)):
		return false
	selected_id = id
	move_origin = pos(unit)
	cursor = move_origin
	return true

func move_selected(destination: Vector2i) -> bool:
	var unit = find_unit(selected_id)
	if unit.is_empty() or not can_stop(unit, destination):
		return false
	if not reachable(unit).costs.has(destination):
		return false
	unit.position = [destination.x, destination.y]
	cursor = destination
	return true

func cancel_move() -> void:
	var unit = find_unit(selected_id)
	if not unit.is_empty():
		unit.position = [move_origin.x, move_origin.y]
	cursor = move_origin
	selected_id = ""

func can_attack(unit: Dictionary, other: Dictionary) -> bool:
	# Range also drives previews/HUD after a unit's death, so HP is checked by
	# the target selector/planner rather than here.
	if unit.is_empty() or other.is_empty() or unit.side == other.side:
		return false
	var distance := absi(pos(unit).x - pos(other).x) + absi(pos(unit).y - pos(other).y)
	return Rules.in_attack_range(unit, distance) and (Rules.magic_cost(unit) == 0 or int(unit.hp) > Rules.magic_cost(unit))

func targets(unit: Dictionary) -> Array:
	return living("enemy" if unit.side == "player" else "player").filter(func(other):
		return can_attack(unit, other))

func plan_combat(attacker_id: String, defender_id: String) -> Dictionary:
	if battle_outcome != "":
		return {}
	var attacker = find_unit(attacker_id)
	var defender = find_unit(defender_id)
	if attacker.is_empty() or defender.is_empty() or int(attacker.hp) <= 0 or int(defender.hp) <= 0 or not targets(attacker).has(defender):
		return {}
	var distance := absi(pos(attacker).x - pos(defender).x) + absi(pos(attacker).y - pos(defender).y)
	var virtual_a = attacker.duplicate(true)
	var virtual_b = Rules.default_counter(defender, distance)
	for unit in [virtual_a, virtual_b]:
		if int(unit.get("character_id", 0)) == 167:
			unit.weapon_index = Rules.boss_weapon(unit, frame_counter)
		unit.story_invulnerable = Rules.boss_guard(unit, turn)
	virtual_a.triangle_attack = Rules.combat_support(virtual_a, virtual_b, living(str(virtual_a.side)), distance)
	virtual_b.triangle_attack = Rules.combat_support(virtual_b, virtual_a, living(str(virtual_b.side)), distance)
	var initial_a: Dictionary = virtual_a.duplicate(true)
	var initial_b: Dictionary = virtual_b.duplicate(true)
	var stats_a = Rules.attack_stats(initial_a, initial_b, terrain_avoid(pos(initial_b)))
	var stats_b = Rules.attack_stats(initial_b, initial_a, terrain_avoid(pos(initial_a)))
	stats_a.blocked = Rules.attack_blocked(initial_a, initial_b)
	stats_b.blocked = Rules.attack_blocked(initial_b, initial_a)
	stats_a.can_strike = Rules.can_attack(initial_a, distance)
	stats_b.can_strike = Rules.can_attack(initial_b, distance)
	var rolls: Array = []
	for role in Rules.strike_sequence(initial_a, initial_b, distance):
		var stats = stats_a if role == "attacker" else stats_b
		var hit_roll = random_bounded(100)
		var critical_roll = random_bounded(100) if int(stats.critical) > 0 else 100
		rolls.append({"role": role, "hit_roll": hit_roll, "critical_roll": critical_roll,
			"hit": hit_roll < int(stats.hit), "critical": hit_roll < int(stats.hit) and critical_roll <= int(stats.critical)})
	var duma = initial_b if int(initial_b.get("character_id", 0)) == 167 else initial_a
	if int(duma.get("character_id", 0)) == 167 and int(duma.hp) >= 52:
		var player = initial_a if initial_a.side == "player" else initial_b
		var player_role = "attacker" if initial_a.side == "player" else "defender"
		var player_rolls = rolls.filter(func(r): return r.role == player_role)
		var safe = Rules.duma_safe_rolls(player, duma, player_rolls.map(func(r): return r.hit), player_rolls.map(func(r): return r.critical))
		for i in range(player_rolls.size()):
			player_rolls[i].hit = safe.hits[i]
			player_rolls[i].critical = safe.criticals[i]
	var events: Array = []
	for roll in rolls:
		var role: String = roll.role
		var source = virtual_a if role == "attacker" else virtual_b
		var target = virtual_b if role == "attacker" else virtual_a
		if int(source.hp) <= 0 or int(target.hp) <= 0:
			break
		if not Rules.can_attack(source, distance):
			continue
		var stats = stats_a if role == "attacker" else stats_b
		var source_before := int(source.hp)
		var initial_target = initial_b if role == "attacker" else initial_a
		var target_for_effect = target.duplicate(true)
		# Form, prayer ring and support state are fixed at exchange start.
		if int(initial_target.get("character_id", 0)) == 167:
			target_for_effect.hp = int(initial_target.hp)
		var effect = Rules.strike_effect(source, target_for_effect, bool(roll.hit), bool(roll.critical), random_bounded(100) if Rules.weapon_index(source) == 14 else 99, distance, terrain_avoid(pos(target)))
		if not effect.valid:
			continue
		var damage = mini(int(target.hp), int(stats.damage) * (3 if bool(roll.critical) else 1)) if bool(roll.hit) else 0
		damage = mini(damage, 120)
		if int(effect.self_damage) > 0:
			damage = 0
		if Rules.weapon_index(source) == 34 and bool(roll.hit):
			damage = maxi(0, int(target.hp) - 1)
		var healing = mini(damage, int(source.max_hp) - int(source.hp) + int(effect.hp_cost)) if Rules.weapon_index(source) == 42 else 0
		var before: int = int(target.hp)
		target.hp = maxi(0, before - damage)
		source.hp = clampi(int(source.hp) - int(effect.hp_cost) - int(effect.self_damage) + healing, 0, int(source.max_hp))
		events.append({"attacker": str(source.id), "defender": str(target.id), "hit": bool(roll.hit),
			"critical": bool(effect.critical), "damage": damage, "hp_before": before,
			"hp_after": int(target.hp), "hit_roll": roll.hit_roll, "critical_roll": roll.critical_roll,
			"distance": distance, "weapon_index": Rules.weapon_index(source), "ranged": Rules.weapon_index(source) in [1, 20, 21, 22],
			"source_hp_before": source_before, "source_hp_after": int(source.hp), "hp_cost": int(effect.hp_cost),
			"self_damage": int(effect.self_damage), "heal": healing})
	return {"attacker": attacker_id, "defender": defender_id, "events": events,
		"distance": distance, "initiative_side": attacker.side, "stats": {attacker_id: stats_a, defender_id: stats_b},
		"initial_attacker_hp": int(attacker.hp), "initial_defender_hp": int(defender.hp)}

func commit_strike(event: Dictionary) -> void:
	var source = find_unit(str(event.attacker))
	if not source.is_empty() and event.has("source_hp_after"):
		source.hp = int(event.source_hp_after)
	var target = find_unit(str(event.defender))
	if not target.is_empty():
		var alive = int(target.hp) > 0
		target.hp = int(event.hp_after)
		if alive and int(target.hp) == 0 and target.side == "enemy":
			kills += 1
		if alive and int(target.hp) == 0:
			target.death_place = str(catalog.world_nodes.get(str(world_node), {}).get("name_zh", "战场"))
			Scenario.on_unit_death(self, target)
			_record_drop(Inventory.on_death(self, target, source))
			Summons.cleanup(self, target)
	if not source.is_empty() and event.has("source_hp_before") and int(event.source_hp_before) > 0 and int(source.hp) == 0:
		source.death_place = str(catalog.world_nodes.get(str(world_node), {}).get("name_zh", "战场"))
		Scenario.on_unit_death(self, source)
		_record_drop(Inventory.on_death(self, source, target))
		Summons.cleanup(self, source)

func finish_exchange(exchange: Dictionary) -> Dictionary:
	if exchange.is_empty():
		return {}
	var initiator = find_unit(str(exchange.attacker))
	var defender = find_unit(str(exchange.defender))
	if initiator.is_empty() or defender.is_empty():
		return {}
	initiator.acted = true
	initiator.erase("weapon_index")
	selected_id = ""
	var player = initiator if initiator.side == "player" else defender
	var enemy = defender if initiator.side == "player" else initiator
	var reward: Dictionary = {}
	if int(player.hp) > 0 and not bool(player.get("no_experience", false)) and not bool(enemy.get("no_experience", false)):
		var exp_before = int(player.get("exp", 0))
		var level_before = int(player.level)
		var before = int(exchange.initial_defender_hp) if initiator.side == "player" else int(exchange.initial_attacker_hp)
		var gain = Rules.experience_gain(player, enemy, before, int(enemy.hp), int(enemy.hp) <= 0)
		player.exp = int(player.get("exp", 0)) + gain
		reward = {"unit": str(player.id), "gain": gain, "leveled": false, "growths": {},
			"exp_before": exp_before, "level_before": level_before}
		if int(player.exp) >= 100 and int(player.level) < 20:
			player.exp -= 100
			player.level += 1
			var rolls: Array = []
			for _i in range(6):
				rolls.append(random_bounded(99) + 1)
			var delta = Rules.growth_result(player, rolls)
			for stat in delta:
				if stat == "hp":
					player.max_hp = mini(52, int(player.max_hp) + int(delta[stat]))
					player.hp = mini(int(player.max_hp), int(player.hp) + int(delta[stat]))
				else:
					player[stat] = mini(40, int(player[stat]) + int(delta[stat]))
			reward.leveled = true
			reward.growths = delta
			var learned = Progression.learn_spells(player)
			player.magic_flags = learned.unit.magic_flags
			player.magic_level = learned.unit.get("magic_level", 0)
			reward.learned = learned.learned
		reward.exp_after = int(player.exp)
		reward.level_after = int(player.level)
	check_outcome()
	return reward

func mark_wait(id: String) -> void:
	var unit = find_unit(id)
	if not unit.is_empty():
		unit.acted = true
	selected_id = ""

func phase_finished() -> bool:
	return living(phase).all(func(unit): return bool(unit.acted) or not bool(unit.get("controllable", true)))

func next_phase() -> void:
	if battle_outcome != "":
		return
	phase = "enemy" if phase == "player" else "player"
	if phase == "player":
		turn += 1
	for unit in living(phase):
		unit.acted = false
		var cell = pos(unit)
		var raw_tile = int(battle_data.map.tiles[cell.y * int(battle_data.map.width) + cell.x])
		var adjacent_saint = living(phase).any(func(other): return str(other.id) != str(unit.id) and int(other.class_id) == 17 and absi(pos(other).x - cell.x) + absi(pos(other).y - cell.y) == 1)
		unit.hp = Items.phase_effect(unit, raw_tile, category(cell), adjacent_saint).hp_after
	selected_id = ""
	if phase == "player": Inventory.refresh_retreat(self)

func check_outcome() -> String:
	var leader = find_unit(leader_id())
	if not leader.is_empty() and int(leader.hp) <= 0:
		battle_outcome = "defeat"
	elif battle_outcome != "defeat" and living("enemy").is_empty():
		battle_outcome = "victory"
	return battle_outcome

func ai_action(unit: Dictionary, gather: bool = false) -> Dictionary:
	return TacticalAI.action(self, unit, gather)

func apply_ai_special(caster: Dictionary, action: Dictionary) -> Dictionary:
	if int(caster.get("hp", 0)) <= 0 or bool(caster.acted): return {}
	var result: Dictionary = {"changed": [], "spawned": [], "action": str(action.get("special", ""))}
	match result.action:
		"summon":
			var spec: Dictionary = action.source_summon
			if int(caster.hp) <= int(spec.hp_cost): return {}
			caster.hp = int(caster.hp) - int(spec.hp_cost)
			result.divide = bool(spec.get("divide", false))
			result.spawned = _summon(caster, int(spec.class_id), int(spec.count), spec)
		"quake":
			var player_damage = random_bounded(20) + 10
			var enemy_damage = random_bounded(4) + 1
			for unit in units:
				if int(unit.hp) <= 0: continue
				var amount = player_damage if unit.side == "player" else enemy_damage
				var before = int(unit.hp)
				unit.hp = maxi(1, before - maxi(0, amount - (int(unit.luck) >> 1)))
				result.changed.append({"id": unit.id, "before": before, "after": unit.hp})
		_: return {}
	caster.acted = true
	selected_id = ""
	return result

func _brigand_seeks_recovery(unit: Dictionary) -> bool:
	if unit.side != "enemy" or str(unit.get("class", "")) != "brigand":
		return false
	# bank003 L038589/L03859A/L0385DB. Keep the original flag byte as
	# immutable source data and persist the current AI flags separately.
	var ai_flags = int(unit.get("ai_flags", unit.get("raw_ai_flags", 0)))
	var ai_mode = ai_flags & 3
	var current_hp = int(unit.hp)
	var maximum_hp = int(unit.max_hp)
	if ai_mode in [0, 3] and (ai_flags & 128) != 0:
		var health = current_hp * 2
		if (ai_flags & 64) != 0 and int(unit.defence) >= 6:
			health *= 2
		if health < maximum_hp:
			ai_mode = 1
	elif ai_mode == 1:
		# $36 is the original main-loop counter: full HP always resumes
		# offense; half HP resumes it only on an odd counter value.
		if current_hp >= maximum_hp or ((frame_counter & 1) != 0 and current_hp * 2 >= maximum_hp):
			ai_mode = (ai_flags & 48) >> 4
	unit.ai_flags = (ai_flags & 252) | ai_mode
	return ai_mode == 1

func _recovery_action(unit: Dictionary, turn_graph: Dictionary) -> Dictionary:
	# L038BC0 targets category15; use the same weighted movement graph as
	# ordinary movement, including enemy blockers and friendly traversal.
	var full_graph = reachable(unit, true)
	var goal = pos(unit)
	var goal_cost = 256
	for cell in full_graph.costs:
		if category(cell) == 15 and can_stop(unit, cell) and int(full_graph.costs[cell]) < goal_cost:
			goal = cell
			goal_cost = int(full_graph.costs[cell])
	if goal_cost == 256:
		# L038ACC/L038AF2: an unsuccessful recovery search waits this action,
		# restores the normal mode and clears the recovery-enabling bit.
		var ai_flags = int(unit.ai_flags)
		unit.ai_flags = (ai_flags & 124) | ((ai_flags & 48) >> 4)
		return {"destination": pos(unit), "target": ""}
	var path: Array[Vector2i] = [goal]
	while path[0] != pos(unit):
		path.push_front(full_graph.previous[path[0]])
	var destination = pos(unit)
	for cell in path:
		if turn_graph.costs.has(cell) and can_stop(unit, cell):
			destination = cell
	return {"destination": destination, "target": ""}

func save_game() -> bool:
	var snapshot_units = units.duplicate(true)
	# A cursor-confirmed move is still cancellable until attack/wait. Never
	# persist its temporary destination as a committed action in a suspend save.
	if selected_id != "":
		for unit in snapshot_units:
			if str(unit.id) == selected_id and not bool(unit.acted):
				unit.position = [move_origin.x, move_origin.y]
	var state = {"version": 3, "source_revision": stages[1].source_commit, "mode": mode,
		"flags": flags, "party": party, "village_position": [village_position.x, village_position.y],
		"units": snapshot_units, "phase": phase, "turn": turn, "rng_state": rng_state,
		"frame_counter": frame_counter, "kills": kills, "battle_outcome": battle_outcome,
		"stage_id": stage_id, "world_node": world_node, "cleared_stages": cleared_stages,
		"roster": roster, "battle_start_snapshot": battle_start_snapshot, "victory_rewards": victory_rewards,
		"chapter": chapter, "route": route, "parties": parties, "route_positions": route_positions,
		"previous_world_node": previous_world_node, "world_armies": world_armies, "convoy": convoy,
		"hub_id": hub_id, "hub_position": [hub_position.x, hub_position.y], "hub_flags": hub_flags,
		"hub_changes": hub_changes, "hub_used": hub_used, "battle_return": battle_return,
		"battle_settled": battle_settled, "story_events": story_events, "encounter_groups": encounter_groups}
	var file = FileAccess.open(save_path + ".tmp", FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(state))
	file.flush()
	var write_error = file.get_error()
	file.close()
	if write_error != OK: return false
	return DirAccess.rename_absolute(save_path + ".tmp", save_path) == OK

func load_game() -> bool:
	if not FileAccess.file_exists(save_path):
		return false
	var state = read_json(save_path)
	if not _valid_save(state) or state.get("source_revision", "") != stages[1].source_commit:
		return false
	var version := int(state.version)
	var saved_stage := int(state.get("stage_id", 1))
	if not available_stage(saved_stage):
		return false
	if version < 3 and not FileAccess.file_exists(save_path + ".v" + str(version) + ".bak"):
		DirAccess.copy_absolute(save_path, save_path + ".v" + str(version) + ".bak")
	stage_id = saved_stage
	battle_data = stages[stage_id]
	chapter = int(state.get("chapter", 1))
	route = str(state.get("route", "alm"))
	flags = state.flags
	party = state.party
	village_position = Vector2i(state.village_position[0], state.village_position[1])
	units = state.units
	# Localized names follow the current catalog even when resuming an older save.
	for unit in units:
		var id = str(unit.id)
		if opening.characters.has(id):
			unit.name_zh = opening.characters[id].name_zh
		elif str(unit.get("class", "")) in ["brigand", "archer"]:
			unit.name_zh = "弓箭手" if str(unit.get("class", "")) == "archer" else "山贼"
	phase = state.phase
	turn = int(state.turn)
	rng_state = int(state.rng_state)
	frame_counter = int(state.frame_counter)
	kills = int(state.kills)
	battle_outcome = state.battle_outcome
	selected_id = ""
	mode = str(state.mode)
	if mode not in ["village", "hub", "world", "battle", "victory", "defeat", "ending"]:
		mode = "village" if units.is_empty() else "battle"
	world_node = int(state.get("world_node", 49 if units.is_empty() else stage_id))
	if not catalog.get("world_nodes", {}).has(str(world_node)):
		world_node = stage_id
	roster = state.get("roster", {}).duplicate(true)
	cleared_stages = []
	for cleared in state.get("cleared_stages", []):
		if available_stage(int(cleared)) and not cleared_stages.has(int(cleared)):
			cleared_stages.append(int(cleared))
	victory_rewards = state.get("victory_rewards", []).duplicate(true)
	battle_start_snapshot = state.get("battle_start_snapshot", {}).duplicate(true)
	if version == 1:
		_migrate_v1_campaign()
	else:
		for id in party:
			if not roster.has(id):
				roster[id] = _initial_character(str(id))
	for id in roster:
		if opening.characters.has(id):
			roster[id].name_zh = opening.characters[id].name_zh
	parties = state.get("parties", {"alm": party.duplicate(), "celica": []}).duplicate(true)
	route_positions = state.get("route_positions", {"alm": world_node, "celica": 53}).duplicate(true)
	previous_world_node = int(state.get("previous_world_node", world_node))
	convoy = state.get("convoy", {"alm": [], "celica": []}).duplicate(true)
	hub_id = int(state.get("hub_id", 1))
	var at: Array = state.get("hub_position", [5, 10])
	hub_position = Vector2i(at[0], at[1])
	hub_flags = state.get("hub_flags", {}).duplicate(true)
	hub_changes = state.get("hub_changes", {}).duplicate(true)
	hub_used = state.get("hub_used", {}).duplicate(true)
	battle_return = state.get("battle_return", {"mode": "world", "world_node": world_node}).duplicate(true)
	battle_settled = bool(state.get("battle_settled", stage_cleared(stage_id) and battle_outcome == "victory"))
	story_events = state.get("story_events", []).duplicate(true)
	encounter_groups = state.get("encounter_groups", []).duplicate()
	if version < 3:
		_setup_chapter_armies()
		for cleared in cleared_stages:
			world_armies.erase(str(cleared))
		for room in hubs.get("initial_trigger_masks", {}):
			hub_flags[room] = {"actors": 0, "talk": 0, "triggers": int(hubs.initial_trigger_masks[room])}
		_bridge_opening_flags()
	else:
		world_armies = state.get("world_armies", {}).duplicate(true)
	var persistent_units: Array = units.duplicate()
	persistent_units.append_array(roster.values())
	for unit in persistent_units:
		var initial: Dictionary = characters.get(str(unit.id), {})
		if initial.is_empty():
			for template in battle_data.enemies:
				if str(template.id) == str(unit.id): initial = template; break
		for key in ["character_id", "resistance", "magic_level", "name_id", "group_id", "record_index"]:
			if not unit.has(key) and initial.has(key):
				unit[key] = initial[key]
	for side in ["player", "enemy"]:
		var side_units = units.filter(func(unit): return unit.side == side)
		for slot in range(side_units.size()):
			if not side_units[slot].has(side + "_slot"): side_units[slot][side + "_slot"] = slot
	WorldArmies.ensure(self)
	if not units.is_empty() and mode in ["battle", "victory", "defeat"]:
		WorldArmies.bind_legacy_battle_units(self)
	if mode == "world":
		# Repair0.6 world suspends that kept the previous route's unit cache.
		units.clear()
		var previous: Dictionary = flags.get("world_route_previous_nodes", {})
		var recover_legacy := not previous.has(route)
		if not previous.has(route): previous[route] = previous_world_node
		flags.world_route_previous_nodes = previous
		_restore_world_previous_node(recover_legacy)
		remember_world_approach()
	elif not units.is_empty():
		var leader = find_unit(leader_id())
		if not leader.is_empty(): cursor = pos(leader)
	return true

func _bridge_opening_flags() -> void:
	apply_hub_flag(17)
	if bool(flags.get("mycen_refused", false)):
		apply_hub_flag(19)
	if bool(flags.get("joined_deliverance", false)):
		apply_hub_flag(1)
	for key in {"kliff": 2, "tobin": 3, "gray": 4}:
		if party.has(key):
			apply_hub_flag({"kliff": 2, "tobin": 3, "gray": 4}[key])

func _valid_save(state: Dictionary) -> bool:
	if not SaveValidation.valid(self, state):
		return false
	# Validate the supported structure before touching the live campaign.
	if int(state.version) >= 2:
		for key in ["stage_id", "world_node", "roster", "cleared_stages", "battle_start_snapshot", "victory_rewards"]:
			if not state.has(key):
				return false
	for key in ["flags", "party", "village_position", "units", "phase", "turn", "rng_state", "frame_counter", "kills", "battle_outcome", "mode"]:
		if not state.has(key):
			return false
	if not state.flags is Dictionary or not state.party is Array or not state.units is Array:
		return false
	if not state.village_position is Array or state.village_position.size() != 2:
		return false
	if state.party.is_empty() or state.party[0] not in ["alm", "celica"] or state.phase not in ["player", "enemy"]:
		return false
	for member in state.party:
		if not characters.has(str(member)):
			return false
	for unit in state.units:
		if not _valid_unit(unit, true):
			return false
	if not state.units.is_empty():
		var has_alm := false
		for unit in state.units:
			has_alm = has_alm or str(unit.id) in ["alm", "celica"]
		if not has_alm:
			return false
	if not state.get("roster", {}) is Dictionary or not state.get("cleared_stages", []) is Array or not state.get("battle_start_snapshot", {}) is Dictionary or not state.get("victory_rewards", []) is Array:
		return false
	for member in state.get("roster", {}):
		if not characters.has(str(member)) or not _valid_unit(state.roster[member], false):
			return false
	var snapshot: Dictionary = state.get("battle_start_snapshot", {})
	if not snapshot.is_empty():
		for key in ["stage_id", "units", "roster", "cleared_stages", "flags", "rng_state", "frame_counter"]:
			if not snapshot.has(key):
				return false
		if not available_stage(int(snapshot.stage_id)) or not snapshot.units is Array or snapshot.units.is_empty() or not snapshot.roster is Dictionary or not snapshot.flags is Dictionary or not snapshot.cleared_stages is Array:
			return false
		if not snapshot.get("party", state.party) is Array or snapshot.get("party", state.party).is_empty() or snapshot.get("party", state.party)[0] not in ["alm", "celica"]:
			return false
		for member in snapshot.get("party", state.party):
			if not characters.has(str(member)):
				return false
		var has_snapshot_alm := false
		for unit in snapshot.units:
			if not _valid_unit(unit, true):
				return false
			has_snapshot_alm = has_snapshot_alm or str(unit.id) in ["alm", "celica"]
		if not has_snapshot_alm:
			return false
		for member in snapshot.roster:
			if not characters.has(str(member)) or not _valid_unit(snapshot.roster[member], false):
				return false
	return true

func _valid_unit(unit, tactical: bool) -> bool:
	if not unit is Dictionary:
		return false
	for key in ["id", "side", "hp", "max_hp", "class_id", "level", "strength", "skill", "speed", "luck", "defence", "move", "acted"]:
		if not unit.has(key):
			return false
	if unit.side not in ["player", "enemy"] or int(unit.class_id) < 1 or int(unit.class_id) > 22 or int(unit.level) < 1 or int(unit.level) > 20:
		return false
	if int(unit.max_hp) < 1 or int(unit.max_hp) > (255 if unit.side == "enemy" else 52) or int(unit.hp) < 0 or int(unit.hp) > int(unit.max_hp):
		return false
	if tactical and (not unit.get("position", null) is Array or unit.position.size() != 2):
		return false
	return true

func _migrate_v1_campaign() -> void:
	# v1 only contained the active first battle. Completed saves keep their
	# exact grown stats/EXP/deaths; do not add a new retroactive victory reward.
	roster.clear()
	for id in party:
		roster[id] = _initial_character(str(id))
	var current_units := units.duplicate(true)
	var current_rng := rng_state
	var current_frame := frame_counter
	var current_mode := mode
	var current_phase := phase
	var current_turn := turn
	var current_kills := kills
	var current_outcome := battle_outcome
	# The retry snapshot built by start_battle must include every saved v1
	# recruit, not the constructor's default one-member Alm party.
	parties = {"alm": party.duplicate(), "celica": []}
	start_battle(1)
	units = current_units
	rng_state = current_rng
	frame_counter = current_frame
	mode = current_mode
	phase = current_phase
	turn = current_turn
	kills = current_kills
	battle_outcome = current_outcome
	world_node = 49 if units.is_empty() else 1
	if battle_outcome == "victory" or bool(flags.get("first_battle_complete", false)):
		cleared_stages = [1]
		flags.first_battle_complete = true
		for unit in units:
			if unit.side == "player":
				roster[str(unit.id)] = unit.duplicate(true)
				roster[str(unit.id)].dead = int(unit.hp) <= 0

func _record_drop(record: Dictionary) -> void:
	if record.is_empty() or str(record.get("destination", "")) == "pending": return
	var notices: Array = flags.get("loot_notifications", [])
	notices.append(record)
	flags.loot_notifications = notices
