extends RefCounted
## Template IDs select ROM stats; instance IDs identify independent armies.
## bank008 L089FCA allocates slots0..12, L089D38 reserves slot13 for the
## random cemetery army, and L08A095 writes a separate survival mask per slot.

static func new_instance(game) -> String:
	var serial := maxi(1,int(game.flags.get("world_army_next_id",1)))
	game.flags.world_army_next_id = serial + 1
	return "army_" + str(serial)

static func _observe_id(game, identity: String) -> void:
	if identity.begins_with("army_") and identity.substr(5).is_valid_int():
		game.flags.world_army_next_id = maxi(int(game.flags.get("world_army_next_id",1)),int(identity.substr(5))+1)

static func reset_for_chapter(game) -> void:
	game.flags.world_army_instances = {}
	game.flags.world_mobile_armies = []
	game.flags.erase("world_random_army_instance")
	game.flags.erase("battle_army_instances")
	game.flags.erase("dungeon_army_instances")
	game.flags.erase("inventory_attacking_instance_id")
	ensure(game)

static func ensure(game) -> void:
	var existing: Dictionary = game.flags.get("world_army_instances",{})
	# Advance the serial before allocating missing metadata from a v3 save.
	for values in existing.values():
		for identity in values: _observe_id(game,str(identity))
	for identity in game.flags.get("battle_army_instances",[]): _observe_id(game,str(identity))
	for identity in game.flags.get("dungeon_army_instances",{}).values(): _observe_id(game,str(identity))
	var meta: Dictionary = {}
	var used: Dictionary = {}
	for node in game.world_armies:
		var groups: Array = game.world_armies[node]
		var old: Array = existing.get(str(node),[])
		var identities: Array = []
		for i in range(groups.size()):
			var identity := str(old[i]) if i < old.size() else ""
			if identity.is_empty() or used.has(identity): identity = new_instance(game)
			identities.append(identity)
			used[identity] = true
		meta[str(node)] = identities
	game.flags.world_army_instances = meta
	# Before instance metadata existed there was exactly one special random
	# node in the source chapter table. Its identity stays stable as saved.
	if not game.flags.has("world_random_army_instance"):
		for variant in game.catalog.get("chapter_random_armies",[]):
			var record: Dictionary = variant.get("by_chapter",{}).get(str(game.chapter),{})
			var node := str(int(record.get("world_node",0)))
			var groups: Array = game.world_armies.get(node,[])
			for i in range(groups.size()):
				if int(groups[i]) == int(record.get("group_id",-1)):
					game.flags.world_random_army_instance = meta[node][i]
					break
			if game.flags.has("world_random_army_instance"): break
	var mobile: Array = []
	var assigned: Dictionary = {}
	for value in game.flags.get("world_mobile_armies",[]):
		var record: Dictionary = value.duplicate(true)
		var node := str(int(record.get("node",0)))
		var groups: Array = game.world_armies.get(node,[])
		var identities: Array = meta.get(node,[])
		var identity := str(record.get("instance_id",""))
		if not identities.has(identity) or assigned.has(identity):
			identity = ""
			for i in range(groups.size()):
				if int(groups[i]) == int(record.get("group_id",-1)) and not assigned.has(identities[i]):
					identity = str(identities[i])
					break
		if identity.is_empty(): continue
		record.instance_id = identity
		assigned[identity] = true
		mobile.append(record)
	game.flags.world_mobile_armies = mobile
	_migrate_legacy_casualties(game)
	if not game.flags.has("inventory_attacking_instance_id") and game.flags.get("inventory_enemy_initiated",false):
		for record in mobile:
			if int(record.node) == int(game.world_node) and int(record.group_id) == int(game.flags.get("inventory_attacking_group_id",-1)):
				game.flags.inventory_attacking_instance_id = str(record.instance_id)
				break

static func instances_at(game, node: int) -> Array:
	ensure(game)
	return game.flags.world_army_instances.get(str(node),[]).duplicate()

static func instance_ids_at(game, node: int) -> Array:
	return instances_at(game,node)

static func locate(game, identity: String) -> Dictionary:
	var meta: Dictionary = game.flags.get("world_army_instances",{})
	for node in meta:
		var index: int = meta[node].find(identity)
		if index >= 0 and index < game.world_armies.get(str(node),[]).size():
			return {"node":int(node),"index":index,"group_id":int(game.world_armies[str(node)][index])}
	return {}

static func current_battle_instances(game, groups: Array, from_hub: bool, resume_dungeon: bool = false) -> Array:
	ensure(game)
	var result: Array = []
	if from_hub:
		var dungeon: Dictionary = game.flags.get("dungeon_army_instances",{})
		if not resume_dungeon:
			# L089D93 initializes slots14/15 with L08A095 for every newly
			# triggered dungeon encounter. Suspend/retry binding retains the
			# current slots; entering again creates full rosters in new slots.
			var retired: Array = dungeon.values()
			var defeated: Dictionary = game.flags.get("inventory_defeated_enemy_records",{})
			for key in defeated.keys():
				if retired.has(str(key).get_slice(":",0)): defeated.erase(key)
			game.flags.inventory_defeated_enemy_records = defeated
			dungeon = {}
		for i in range(groups.size()):
			var key := "%d:%d:%d:%d" % [int(game.hub_id),int(game.stage_id),int(groups[i]),i]
			if not dungeon.has(key): dungeon[key] = new_instance(game)
			result.append(str(dungeon[key]))
		game.flags.dungeon_army_instances = dungeon
	else:
		var available: Array = game.world_armies.get(str(game.world_node),[])
		var identities: Array = game.flags.world_army_instances.get(str(game.world_node),[])
		var chosen: Dictionary = {}
		for group in groups:
			var identity := ""
			for i in range(available.size()):
				if int(available[i]) == int(group) and not chosen.has(i):
					identity = str(identities[i])
					chosen[i] = true
					break
			# Explicit battle fixtures/nonworld scenarios still need isolated
			# identities; they do not create an invented overworld army.
			result.append(new_instance(game) if identity.is_empty() else identity)
	game.flags.battle_army_instances = result
	_migrate_legacy_casualties(game)
	return result

static func bind_legacy_battle_units(game) -> void:
	# Old saves could not contain two same-template armies at one node, so
	# their group ID uniquely selects the newly allocated battle instance.
	# Newly deployed duplicate groups already carry an explicit identity.
	if game.encounter_groups.is_empty():
		game.encounter_groups = game.battle_data.get("enemy_group_ids",[]).duplicate()
	if game.encounter_groups.is_empty(): return
	var identities: Array = game.flags.get("battle_army_instances",[])
	if identities.size() != game.encounter_groups.size():
		identities = current_battle_instances(game,game.encounter_groups,str(game.battle_return.get("mode","world")) == "hub",true)
	for unit in game.units:
		if str(unit.get("side","")) != "enemy" or unit.has("army_instance") or not unit.has("group_id"): continue
		for i in range(game.encounter_groups.size()):
			if int(game.encounter_groups[i]) == int(unit.group_id):
				unit.army_instance = str(identities[i])
				break

static func _ordinary_count(game) -> int:
	var count := 0
	var reserved := str(game.flags.get("world_random_army_instance",""))
	for values in game.flags.world_army_instances.values():
		for identity in values:
			if str(identity) != reserved: count += 1
	return count

static func add(game, node: int, group_id: int, previous_node: int = -1, mobile: bool = true) -> String:
	ensure(game)
	if not bool(game.catalog.enemy_groups.get(str(group_id),{}).get("valid",false)): return ""
	var groups: Array = game.world_armies.get(str(node),[]).duplicate()
	if groups.size() >= 2 or _ordinary_count(game) >= 13: return ""
	# An orphan legacy template mask has no surviving army to attach to.
	# A new source allocation starts with a full roster, never that stale mask.
	var defeated: Dictionary = game.flags.get("inventory_defeated_enemy_records",{})
	var already_alive := false
	for current in game.world_armies.values():
		if current.any(func(value):return int(value) == group_id): already_alive = true
	if not already_alive:
		for key in defeated.keys():
			if str(key).begins_with(str(group_id)+":"): defeated.erase(key)
	var identity := new_instance(game)
	var identities: Array = game.flags.world_army_instances.get(str(node),[]).duplicate()
	groups.append(group_id)
	identities.append(identity)
	game.world_armies[str(node)] = groups
	game.flags.world_army_instances[str(node)] = identities
	if mobile:
		var records: Array = game.flags.get("world_mobile_armies",[])
		records.append({"node":node,"group_id":group_id,"previous_node":previous_node,"instance_id":identity})
		game.flags.world_mobile_armies = records
	return identity

static func move(game, identity: String, destination: int) -> bool:
	ensure(game)
	var source := locate(game,identity)
	if source.is_empty() or destination <= 0 or not game.catalog.world_nodes.has(str(destination)): return false
	if int(source.node) == destination: return true
	var target: Array = game.world_armies.get(str(destination),[]).duplicate()
	if target.size() >= 2: return false
	var target_ids: Array = game.flags.world_army_instances.get(str(destination),[]).duplicate()
	_remove_position(game,identity)
	target.append(int(source.group_id))
	target_ids.append(identity)
	game.world_armies[str(destination)] = target
	game.flags.world_army_instances[str(destination)] = target_ids
	for record in game.flags.get("world_mobile_armies",[]):
		if str(record.get("instance_id","")) == identity:
			record.previous_node = int(source.node)
			record.node = destination
	return true

static func _remove_position(game, identity: String) -> void:
	var at := locate(game,identity)
	if at.is_empty(): return
	var node := str(int(at.node))
	game.world_armies[node].remove_at(int(at.index))
	game.flags.world_army_instances[node].remove_at(int(at.index))
	if game.world_armies[node].is_empty():
		game.world_armies.erase(node)
		game.flags.world_army_instances.erase(node)

static func remove(game, identity: String) -> void:
	_remove_position(game,identity)
	var mobile: Array = game.flags.get("world_mobile_armies",[])
	game.flags.world_mobile_armies = mobile.filter(func(record):return str(record.get("instance_id","")) != identity)

static func remove_battle(game) -> void:
	if str(game.battle_return.get("mode","world")) == "hub": return
	for identity in game.flags.get("battle_army_instances",[]): remove(game,str(identity))

static func _migrate_legacy_casualties(game) -> void:
	var defeated: Dictionary = game.flags.get("inventory_defeated_enemy_records",{})
	for key in defeated.keys():
		var pieces: PackedStringArray = str(key).split(":")
		if pieces.size() != 2 or not pieces[0].is_valid_int(): continue
		var group := int(pieces[0])
		var candidates: Array = []
		var preferred := ""
		if int(game.stage_id) > 48 and str(game.battle_return.get("mode","world")) == "hub":
			var battle_ids: Array = game.flags.get("battle_army_instances",[])
			var battle_groups: Array = game.encounter_groups
			if battle_groups.is_empty(): battle_groups = game.battle_data.get("enemy_group_ids",[])
			var in_dungeon := false
			for i in range(battle_groups.size()):
				if int(battle_groups[i]) != group: continue
				in_dungeon = true
				if i < battle_ids.size(): preferred = str(battle_ids[i])
			# load/retry ensures world metadata before binding old dungeon
			# units. Wait for that binding instead of consuming a dungeon
			# mask into an unrelated overworld copy of the same ROM template.
			if in_dungeon and preferred.is_empty(): continue
			if not preferred.is_empty():
				defeated[preferred + ":" + pieces[1]] = bool(defeated[key])
				defeated.erase(key)
				continue
		for node in game.world_armies:
			for i in range(game.world_armies[node].size()):
				if int(game.world_armies[node][i]) != group: continue
				var identity := str(game.flags.world_army_instances[node][i])
				candidates.append(identity)
				if int(node) == int(game.stage_id) and preferred.is_empty(): preferred = identity
		if candidates.is_empty(): continue
		if preferred.is_empty(): preferred = str(candidates[0])
		if candidates.size() > 1: game.flags.world_army_legacy_casualty_migration = true
		defeated[preferred + ":" + pieces[1]] = bool(defeated[key])
		defeated.erase(key)
	game.flags.inventory_defeated_enemy_records = defeated
