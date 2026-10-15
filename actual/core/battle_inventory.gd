extends RefCounted
## Native item/death/retreat rules. All pending decisions are JSON-saveable flags.
const Items = preload("res://core/item_rules.gd")
const Worlds = preload("res://core/world_armies.gd")
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/battle_inventory.json"))
	return _data

static func _formal(unit: Dictionary) -> bool:
	return str(unit.get("side", "player")) == "player" and not bool(unit.get("temporary", false)) and not bool(unit.get("neutral", false)) and int(unit.get("character_id", 0)) != 35

static func _sync(game, unit: Dictionary) -> void:
	var id := str(unit.get("id", ""))
	if _formal(unit) and game.roster.has(id):
		game.roster[id].item_id = int(unit.get("item_id", 0))
	unit.erase("weapon_index")

static func _store(game, item_id: int, route: String) -> void:
	if item_id <= 0: return
	if not game.convoy.has(route): game.convoy[route] = []
	game.convoy[route].append(item_id)

static func on_battle_start(game) -> void:
	game.flags.inventory_processed_deaths = {}
	if not game.flags.has("pending_loot"): game.flags.pending_loot = []
	game.flags.erase("inventory_retreat_roll_turn")
	if int(game.flags.get("inventory_enemy_record_chapter", 0)) != int(game.chapter):
		game.flags.inventory_defeated_enemy_records = {}
		game.flags.inventory_enemy_record_chapter = int(game.chapter)
	restore_enemy_survivors(game)
	refresh_retreat(game)

static func rare_drop(enemy: Dictionary, chapter: int, cumulative_count: int, first_roll: int, second_roll: int) -> int:
	if chapter < 1 or chapter >= int(data().rare_drops_disabled_from_chapter): return 0
	if cumulative_count >= int(data().rare_drop_cumulative_caps_by_chapter[chapter - 1]): return 0
	if int(enemy.get("item_id", 0)) > 0 or bool(enemy.get("no_drop", false)): return 0
	var source_id := int(enemy.get("source_enemy_character_id", enemy.get("character_id", enemy.get("name_id", 0))))
	for entry in data().rare_drops:
		if source_id == int(entry.character_id) and first_roll < int(entry.roll_threshold) and second_roll < int(entry.roll_threshold):
			return int(entry.item_id)
	return 0

static func on_death(game, unit: Dictionary, killer: Dictionary = {}) -> Dictionary:
	if int(unit.get("hp", 0)) > 0 or bool(unit.get("no_drop", false)): return {}
	var processed: Dictionary = game.flags.get("inventory_processed_deaths", {})
	var key := str(unit.get("id", ""))
	if processed.has(key): return {}
	processed[key] = true
	game.flags.inventory_processed_deaths = processed
	var held := int(unit.get("item_id", 0))
	if _formal(unit):
		var owner_route := str(unit.get("route", game.route))
		_store(game, held, owner_route)
		unit.item_id = 0
		_sync(game, unit)
		return {"kind":"death_storage", "item_id":held, "unit_id":key, "route":owner_route} if held > 0 else {}
	if str(unit.get("side", "")) != "enemy": return {}
	# The original drop flow follows combat against a player, not mere removal
	# from the map (escape, rescue, event cleanup or Expel).
	if killer.is_empty() or str(killer.get("side", "")) != "player" or int(killer.get("hp", 0)) <= 0: return {}
	if held == 0:
		var count := int(game.flags.get("inventory_rare_drop_count", 0))
		var source_chapter := int(game.flags.get("scenario_source_chapter_counter", game.chapter))
		# Avoid advancing RNG for ineligible enemies/chapters. The source
		# reseeds $37 from frame counter $36 before the second successful gate.
		if rare_drop(unit, source_chapter, count, 0, 0) > 0:
			var first: int = game.random_bounded(100)
			if rare_drop(unit, source_chapter, count, first, 0) > 0:
				game.rng_state = int(game.frame_counter)
				held = rare_drop(unit, source_chapter, count, first, game.random_bounded(100))
		if held > 0: game.flags.inventory_rare_drop_count = count + 1
	if held <= 0: return {}
	unit.item_id = 0
	var loot_route := str(killer.get("route", game.route))
	var record := {"kind":"loot", "item_id":held, "unit_id":str(killer.get("id", "")), "enemy_id":key, "route":loot_route}
	if not _formal(killer):
		_store(game, held, loot_route)
		record.destination = "convoy"
	elif int(killer.get("item_id", 0)) == 0:
		killer.item_id = held
		_sync(game, killer)
		record.destination = "unit"
	else:
		var queue: Array = game.flags.get("pending_loot", [])
		queue.append(record.duplicate(true))
		game.flags.pending_loot = queue
		record.destination = "pending"
	return record

static func resolve_loot(game, choice: String) -> bool:
	# keep/store: retain current item and send new item to convoy.
	# new: equip new item, put displaced item into convoy. No silent deletion.
	var queue: Array = game.flags.get("pending_loot", [])
	if queue.is_empty() or not choice in ["keep", "store", "new", "discard_new", "discard_old"]: return false
	var record: Dictionary = queue[0]
	var route := str(record.route)
	var recipient: Dictionary = game.find_unit(str(record.unit_id))
	if recipient.is_empty(): recipient = game.roster.get(str(record.unit_id), {})
	var replace := choice in ["new", "discard_old"]
	var displaced := int(recipient.get("item_id", 0)) if replace else int(record.item_id)
	if choice in ["discard_new", "discard_old"]: displaced = 0
	if replace and (recipient.is_empty() or int(recipient.get("hp", 0)) <= 0): return false
	if displaced > 0 and game.convoy.get(route, []).size() >= int(data().convoy_capacity): return false
	if replace:
		recipient.item_id = int(record.item_id)
		_sync(game, recipient)
	_store(game, displaced, route)
	queue.pop_front()
	game.flags.pending_loot = queue
	return true

static func can_exchange(first: Dictionary, second: Dictionary) -> bool:
	if not _formal(first) or not _formal(second) or str(first.get("id", "")) == str(second.get("id", "")): return false
	if int(first.get("hp", 0)) <= 0 or int(second.get("hp", 0)) <= 0 or bool(first.get("acted", false)): return false
	if int(first.get("item_id", 0)) == 0 and int(second.get("item_id", 0)) == 0: return false
	var a: Array = first.get("position", [-100, -100])
	var b: Array = second.get("position", [100, 100])
	return absi(int(a[0]) - int(b[0])) + absi(int(a[1]) - int(b[1])) == 1

static func exchange(game, first_id: String, second_id: String) -> bool:
	if game.mode != "battle" or game.phase != "player": return false
	var first: Dictionary = game.find_unit(first_id)
	var second: Dictionary = game.find_unit(second_id)
	if not can_exchange(first, second): return false
	var held := int(first.get("item_id", 0))
	first.item_id = int(second.get("item_id", 0))
	second.item_id = held
	first.acted = true
	_sync(game, first)
	_sync(game, second)
	game.selected_id = ""
	return true

static func retreat_destination(game) -> int:
	if not bool(game.flags.get("inventory_enemy_initiated", false)):
		return int(game.previous_world_node)
	if int(game.chapter) == 2: return -1
	var paths: Array = data().enemy_initiated_retreat_paths
	for i in range(paths.size() - 1, -1, -1):
		var path: Array = paths[i]
		for j in range(path.size()):
			if int(path[j]) == int(game.stage_id):
				return int(path[j+1]) if j+1 < path.size() else -1
	return -1

static func retreat_chance(stage_id: int) -> int:
	var table: Array = data().retreat_chance_by_map
	return int(table[stage_id-1]) if stage_id >= 1 and stage_id <= table.size() else 0

static func refresh_retreat(game, roll: int = -1) -> bool:
	if str(game.phase) != "player": return false
	var stamp := "%d:%d" % [int(game.stage_id), int(game.turn)]
	if str(game.flags.get("inventory_retreat_roll_turn", "")) == stamp: return can_retreat(game)
	game.flags.inventory_retreat_roll_turn = stamp
	var target := retreat_destination(game)
	var available: bool = target > 0 and target != int(game.world_node) and not game.world_has_battle(target)
	if available:
		if roll < 0: roll = game.random_bounded(100)
		available = roll < retreat_chance(int(game.stage_id))
	game.flags.inventory_retreat_available = available
	return can_retreat(game)

static func can_retreat(game) -> bool:
	if str(game.mode) != "battle" or str(game.phase) != "player" or not str(game.battle_outcome).is_empty(): return false
	if not game.flags.get("pending_loot", []).is_empty(): return false
	var target := retreat_destination(game)
	return bool(game.flags.get("inventory_retreat_available", false)) and target > 0 and target != int(game.world_node) and not game.world_has_battle(target)

static func _enemy_key(unit: Dictionary) -> String:
	var instance := str(unit.get("army_instance", ""))
	if not instance.is_empty():
		return "%s:%d" % [instance, int(unit.get("record_index", -1))]
	return "%d:%d" % [int(unit.get("group_id", -1)), int(unit.get("record_index", -1))] if unit.has("group_id") else str(unit.get("id", ""))

static func restore_enemy_survivors(game) -> void:
	var defeated: Dictionary = game.flags.get("inventory_defeated_enemy_records", {})
	game.units = game.units.filter(func(unit): return str(unit.get("side", "")) != "enemy" or not defeated.has(_enemy_key(unit)))

static func on_victory(game) -> void:
	# L08A095 stores casualties per deployed world-army slot. Two armies
	# may share one ROM template while keeping independent survival masks.
	var defeated: Dictionary = game.flags.get("inventory_defeated_enemy_records", {})
	var instances: Array = game.flags.get("battle_army_instances", []).duplicate()
	if instances.is_empty():
		for unit in game.units:
			var identity := str(unit.get("army_instance", ""))
			if str(unit.get("side", "")) == "enemy" and not identity.is_empty() and not instances.has(identity):
				instances.append(identity)
	if not instances.is_empty():
		for key in defeated.keys():
			for identity in instances:
				if str(key).begins_with(str(identity) + ":"):
					defeated.erase(key)
		game.flags.inventory_defeated_enemy_records = defeated
		return
	# Compatibility for isolated legacy fixtures without instance metadata.
	# Real old saves migrate these keys once through Worlds.ensure().
	var groups: Array = game.encounter_groups.duplicate()
	for unit in game.units:
		if str(unit.get("side", "")) == "enemy" and unit.has("group_id") and not groups.has(int(unit.group_id)):
			groups.append(int(unit.group_id))
	for key in defeated.keys():
		for group in groups:
			if str(key).begins_with(str(int(group)) + ":"):
				defeated.erase(key)
	game.flags.inventory_defeated_enemy_records = defeated

static func retreat(game) -> bool:
	if not can_retreat(game): return false
	_finish_player_retreat(game, retreat_destination(game))
	return true

static func _persist_participants(game) -> void:
	var defeated: Dictionary = game.flags.get("inventory_defeated_enemy_records", {})
	for unit in game.units:
		if _formal(unit):
			var persistent: Dictionary = unit.duplicate(true)
			persistent.dead = int(unit.hp) <= 0
			persistent.acted = false
			game.roster[str(unit.id)] = persistent
		elif str(unit.get("side", "")) == "enemy" and int(unit.get("hp", 0)) <= 0 and not bool(unit.get("temporary", false)):
			defeated[_enemy_key(unit)] = true
	game.flags.inventory_defeated_enemy_records = defeated

static func _finish_player_retreat(game, destination: int) -> void:
	_persist_participants(game)
	var return_hub: Dictionary = game.battle_return.duplicate(true)
	if str(return_hub.get("mode", "world")) == "hub":
		# L06B863 restores the building map after the exceptional map49
		# timeout. Other underground maps use255 and never time out.
		game.world_node = int(return_hub.get("world_node", game.world_node))
		var at: Array = return_hub.get("position", [0, 0])
		game.enter_hub(int(return_hub.hub_id), Vector2i(int(at[0]), int(at[1])))
		game.battle_outcome = "retreat"
		game.battle_settled = true
		game.selected_id = ""
		game.units.clear()
		return
	game.world_node = destination
	game.route_positions[game.route] = game.world_node
	game.previous_world_node = game.world_node
	game.battle_return = {"mode":"world", "world_node":game.world_node}
	game.battle_outcome = "retreat"
	game.battle_settled = true
	game.selected_id = ""
	game.parties[game.route] = game.party.duplicate()
	game.mode = "world"
	game.units.clear()

static func forced_retreat_turn(stage_id: int) -> int:
	var table: Array = data().enemy_retreat_turn_by_map
	return int(table[stage_id-1]) if stage_id >= 1 and stage_id <= table.size() else 255

static func forced_retreat(game) -> Dictionary:
	# L06A50A checks this at enemy phase start, but L06B7A6 retreats the
	# attacking world army ($7477), not unconditionally the enemy side.
	var threshold := forced_retreat_turn(int(game.stage_id))
	if str(game.mode) != "battle" or str(game.phase) != "enemy" or threshold == 255 or int(game.turn) < threshold:
		return {"triggered":false, "reason":"not_due"}
	if not str(game.battle_outcome).is_empty() or not game.flags.get("pending_loot", []).is_empty():
		return {"triggered":false, "reason":"unsettled_battle"}
	if not bool(game.flags.get("inventory_enemy_initiated", false)):
		var destination := int(game.previous_world_node)
		var hub_return := str(game.battle_return.get("mode", "world")) == "hub"
		if not hub_return and (destination <= 0 or destination == int(game.world_node)):
			return {"triggered":false, "reason":"missing_player_origin"}
		_finish_player_retreat(game, destination)
		return {"triggered":true, "side":"player", "destination":destination}
	var group_id := int(game.flags.get("inventory_attacking_group_id", -1))
	var destination := int(game.flags.get("inventory_attacker_previous_node", -1))
	var instance := str(game.flags.get("inventory_attacking_instance_id", ""))
	if (group_id < 0 and instance.is_empty()) or destination <= 0 or destination == int(game.world_node):
		return {"triggered":false, "reason":"missing_attacking_army_origin"}
	var current: Array = game.world_armies.get(str(game.world_node), [])
	if not instance.is_empty() or game.flags.has("world_army_instances"):
		var identities: Array = Worlds.instances_at(game, int(game.world_node))
		if instance.is_empty():
			for i in range(current.size()):
				if int(current[i]) == group_id:
					instance = str(identities[i])
					break
		if not identities.has(instance): return {"triggered":false, "reason":"attacking_army_missing"}
		group_id = int(current[identities.find(instance)])
		if not Worlds.move(game, instance, destination): return {"triggered":false, "reason":"attacking_army_retreat_blocked"}
	else:
		# Older unit-test fixtures have no world catalog/metadata. Move one
		# matching occurrence; do not erase/deduplicate every shared template.
		var index := -1
		for i in range(current.size()):
			if int(current[i]) == group_id:
				index = i
				break
		if index < 0: return {"triggered":false, "reason":"attacking_army_missing"}
		var destination_groups: Array = game.world_armies.get(str(destination), []).duplicate()
		if destination_groups.size() >= 2: return {"triggered":false, "reason":"attacking_army_retreat_blocked"}
		var remaining := current.duplicate()
		remaining.remove_at(index)
		if remaining.is_empty(): game.world_armies.erase(str(game.world_node))
		else: game.world_armies[str(game.world_node)] = remaining
		destination_groups.append(group_id)
		game.world_armies[str(destination)] = destination_groups
		var mobile: Array = game.flags.get("world_mobile_armies", [])
		for record in mobile:
			if int(record.get("group_id", -1)) == group_id and int(record.get("node", -1)) == int(game.world_node):
				record.previous_node = game.world_node
				record.node = destination
				break
		game.flags.world_mobile_armies = mobile
	_persist_participants(game)
	game.battle_return = {"mode":"world", "world_node":game.world_node}
	game.battle_outcome = "enemy_retreat"
	game.battle_settled = true
	game.selected_id = ""
	game.parties[game.route] = game.party.duplicate()
	game.mode = "world"
	game.units.clear()
	game.flags.inventory_enemy_initiated = false
	return {"triggered":true, "side":"enemy", "group_id":group_id, "instance_id":instance, "destination":destination}
