class_name FeScenarioRules
extends RefCounted
const WorldArmies = preload("res://core/world_armies.gd")
## Source-backed campaign hooks. Gameplay callers own scene transitions/saving.
## NPC allies use player side for targeting, but remain uncontrollable/neutral.
## Full per-frame world AI tie-breaking is intentionally not claimed here.

static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty():
		_data = JSON.parse_string(FileAccess.get_file_as_string("res://data/campaign_events.json"))
	return _data

static func _once(game, key: String) -> bool:
	key = "scenario_" + key
	if bool(game.flags.get(key, false)):
		return false
	game.flags[key] = true
	return true

static func _source_id(unit: Dictionary) -> int:
	return int(unit.get("source_enemy_character_id", unit.get("character_id", unit.get("name_id", 0))))

static func _key(game, character_id: int) -> String:
	for key in game.characters:
		if int(game.characters[key].get("character_id", game.characters[key].get("id", 0))) == character_id:
			return str(key)
	return ""

static func _dialogue(game, group: String, index: int, once_key: String = "") -> void:
	if not once_key.is_empty() and not _once(game, "text_" + once_key):
		return
	game.story_events.append({"kind": "dialogue", "group": group, "key": str(index)})

static func _flag(game, flag_id: int) -> void:
	game.apply_hub_flag(flag_id)

static func _has_source_flag(game, flag_id: int) -> bool:
	return bool(game.flags.get("source_flag_" + str(flag_id), false))

static func _fresh_unit(game, key: String) -> Dictionary:
	var unit: Dictionary = game.characters.get(key, {}).duplicate(true)
	unit.id = key
	unit.side = "player"
	unit.dead = false
	unit.acted = false
	unit.controllable = true
	unit.magic_level = int(unit.get("magic_level", 0))
	return unit

static func _find_source(game, source_id: int) -> Dictionary:
	for unit in game.units:
		if _source_id(unit) == source_id and int(unit.get("hp", 0)) > 0:
			return unit
	return {}

static func _retire(unit: Dictionary, rescued: bool = false) -> void:
	unit.hp = 0
	unit.dead = false
	unit.retreated = not rescued
	unit.rescued = rescued
	unit.no_experience = true
	unit.no_drop = true
	unit.acted = true

static func _dead_roster(game, key: String, unit: Dictionary, block_recruit: bool) -> void:
	if key.is_empty():
		return
	var persistent: Dictionary = game.roster.get(key, _fresh_unit(game, key)).duplicate(true)
	# Keep playable Zeke's source template; his enemy/NPC form has other stats.
	if str(unit.get("id", "")) == key:
		persistent = unit.duplicate(true)
	persistent.id = key
	persistent.hp = 0
	persistent.dead = true
	game.roster[key] = persistent
	if block_recruit:
		game.flags["unrecruitable_" + key] = true

static func on_battle_start(game) -> void:
	game.flags.scenario_battle_serial = int(game.flags.get("scenario_battle_serial", 0)) + 1
	game.flags.scenario_processed_deaths = {}
	game.flags.erase("scenario_forced_victory")
	var stage := int(game.stage_id)
	if stage == 62:
		if bool(game.flags.get("scenario_final_merge_ready", false)):
			_merge_final_parties(game)
		elif str(game.route) == "celica":
			# L0D9633 -> L068DFB: first altar entry is Celica's capture and
			# a route switch; it is not the final playable confrontation.
			game.flags.celica_captive = true
			game.flags.scenario_celica_story_phase = 3
			game.flags.dragon_valley_released = true
			game.flags.world_gate_bits = int(game.flags.get("world_gate_bits", 22)) & ~33
			game.parties.celica = game.party.duplicate()
			game.route = "alm"
			game.party = game.parties.alm.duplicate()
			game.world_node = int(game.route_positions.get("alm", 36))
			game.mode = "world"
			game.units.clear()
			_dialogue(game, "events", 13, "celica_first_altar")
			return
		else:
			# The original final merge is a separate hub trigger. Preserve
			# the caller's hub return instead of admitting Alm alone.
			game.mode = "hub"
			game.units.clear()
			return
	for npc in data().battle_allied_npcs:
		if int(npc.map_id) != stage:
			continue
		var key := _key(game, int(npc.character_id))
		if key.is_empty() or game.party.has(key) or bool(game.flags.get("unrecruitable_" + key, false)):
			continue
		if bool(game.roster.get(key, {}).get("dead", false)):
			continue
		if game.units.any(func(unit): return str(unit.get("id", "")) == key):
			continue
		var unit := _fresh_unit(game, key)
		unit.position = npc.position.duplicate()
		unit.controllable = false
		unit.neutral = true
		unit.no_experience = true
		unit.ai_flags = int(npc.ai_flags)
		unit.rescue_npc = true
		game.units.append(unit)
	if stage == 34 and _has_source_flag(game, 31):
		var groups: Array[int] = []
		for value in game.encounter_groups:
			groups.append(int(value))
		if groups.has(34) and groups.has(35):
			for unit in game.units:
				if int(unit.get("group_id", -1)) != 34:
					continue
				var source_id := _source_id(unit)
				unit.source_enemy_character_id = source_id
				unit.character_id = int(data().events.tatiana_zeke.npc_name_id_map.get(str(source_id), source_id))
				unit.side = "player"
				unit.controllable = false
				unit.neutral = true
				unit.no_experience = true
				unit.ai_flags = int(unit.get("raw_ai_flags", 0)) | 4
				unit.zeke_npc = source_id == 139
			game.flags.zeke_allied = true
	for opening in data().battle_opening_events:
		if int(opening.map_id) != stage:
			continue
		if stage == 34 and not bool(game.flags.get("zeke_allied", false)):
			continue
		if stage == 62:
			_dialogue(game, "events", 14, "final_reunion")
		else:
			_dialogue(game, "events", int(opening.script_index), "opening_" + str(stage))

static func _merge_final_parties(game) -> void:
	var enemies: Array = game.units.filter(func(unit): return str(unit.side) == "enemy")
	var combined: Array = []
	var positions: Array = game.stages[62].player_positions_by_party
	var snapshot: Dictionary = game.flags.get("celica_captive_hp", {})
	for index in range(2):
		var route_name: String = ["celica", "alm"][index]
		var slot := 0
		for value in game.parties.get(route_name, []):
			var key := str(value)
			var unit: Dictionary = game.roster.get(key, _fresh_unit(game, key)).duplicate(true)
			if int(unit.get("hp", 0)) <= 0 or bool(unit.get("dead", false)) or slot >= 10:
				continue
			unit.id = key
			unit.side = "player"
			unit.route = route_name
			unit.controllable = true
			unit.neutral = false
			unit.no_experience = false
			unit.acted = false
			unit.position = positions[index][slot].duplicate()
			unit.hp = clampi(int(snapshot.get(key, unit.max_hp)) if route_name == "celica" else int(unit.max_hp), 1, int(unit.max_hp))
			unit.erase("weapon_index")
			combined.append(unit)
			slot += 1
	combined.append_array(enemies)
	game.units = combined
	game.flags.scenario_celica_story_phase = 4
	game.flags.final_parties_merged = true

static func on_unit_death(game, unit: Dictionary) -> void:
	if int(unit.get("hp", 1)) > 0 or bool(unit.get("temporary", false)) or bool(unit.get("rescued", false)) or bool(unit.get("retreated", false)):
		return
	var seen: Dictionary = game.flags.get("scenario_processed_deaths", {})
	var identity := str(unit.get("id", ""))
	if seen.has(identity):
		return
	seen[identity] = true
	game.flags.scenario_processed_deaths = seen
	var cid := _source_id(unit)
	var key := _key(game, cid)
	if cid in [1, 2] and str(unit.get("side", "")) == "player":
		game.battle_outcome = "defeat"
	if bool(unit.get("zeke_npc", false)) or (cid == 139 and int(game.stage_id) == 34):
		_dead_roster(game, "zeke", unit, true)
	elif str(unit.get("side", "")) == "player":
		_dead_roster(game, key, unit, bool(unit.get("rescue_npc", false)))
	if cid == 145:
		_dead_roster(game, "delthea", {}, true)
	if cid in [136, 157]:
		_desert_branch(game, cid)
	if cid == 143:
		var captive := _find_source(game, 145)
		if not captive.is_empty():
			_retire(captive, true)
			game.flags.delthea_rescued = true
			_dialogue(game, "events", 12)
	var boss_ids: Array = [129, 130, 131, 132, 133, 134, 137, 138, 139, 140, 141, 142, 143, 144, 145]
	if cid >= 1 and cid <= 34:
		_dialogue(game, "death_quotes", cid + 13)
	elif boss_ids.has(cid):
		_dialogue(game, "death_quotes", 49 + boss_ids.find(cid))
	for source in data().character_death_events:
		if int(source.character_id) != cid:
			continue
		match str(source.action):
			"set_event_flag":
				_flag(game, int(source.flag_index))
			"set_world_branch_bits":
				game.flags.world_branch_bits = int(game.flags.get("world_branch_bits", 0)) | int(source.bitmask)
			"set_reinforcement_state":
				if not bool(game.flags.get("generator_disabled_" + str(int(source.generator_index)), false)):
					game.flags["reinforcement_state_" + str(int(source.generator_index))] = int(source.generator_state)
			"queue_world_army":
				game.flags["queued_army_" + str(int(source.parameter) & 127)] = true
			"dispatch_surviving_unit_battle_event":
				# Delthea rescue was handled above with its own nondeath fate.
				if int(source.target_character_id) == 145:
					continue
				var found := false
				for survivor in game.units:
					if _source_id(survivor) == int(source.target_character_id) and int(survivor.hp) > 0:
						_retire(survivor)
						found = true
				if found:
					_dialogue(game, "events", int(source.battle_event_id))
			"dispatch_battle_event":
				_dialogue(game, "events", int(source.battle_event_id))
	if cid == 133 and int(game.stage_id) == 42:
		_force_victory(game, "rudolf_surrender")
		game.flags.rudolf_defeated = true
	if cid == 167 and int(game.stage_id) == 62:
		_force_victory(game, "duma_defeated")
		if game.battle_outcome == "victory":
			game.flags.campaign_complete = true
			game.flags.duma_defeated = true

static func _force_victory(game, reason: String) -> void:
	for unit in game.units:
		if str(unit.side) == "player" and str(unit.get("id", "")) in ["alm", "celica"] and int(unit.hp) <= 0:
			game.battle_outcome = "defeat"
			return
	for unit in game.units:
		if str(unit.side) == "enemy" and int(unit.hp) > 0:
			_retire(unit)
	game.flags.scenario_forced_victory = reason
	game.battle_outcome = "victory"

static func _desert_branch(game, defeated: int) -> void:
	for branch in data().events.desert_choice.branches:
		if int(branch.defeat_character_id) != defeated:
			continue
		if not _once(game, "desert_choice"):
			return
		game.flags.desert_survivor = str(branch.recruit_key)
		game.flags["unrecruitable_" + ("deen" if defeated == 136 else "sonya")] = true
		var surviving_group := int(branch.surviving_group_id)
		WorldArmies.ensure(game)
		for node in game.world_armies.keys():
			var groups: Array = game.world_armies[node].duplicate()
			var identities: Array = WorldArmies.instances_at(game,int(node))
			for i in range(groups.size()):
				if int(groups[i]) == surviving_group: WorldArmies.remove(game,str(identities[i]))
		_flag(game, int(branch.set_event_flag))
		return

static func on_victory(game) -> void:
	var serial := int(game.flags.get("scenario_battle_serial", 0))
	if not _once(game, "settled_" + str(serial)):
		return
	for unit in game.units:
		if int(unit.get("hp", 0)) <= 0:
			continue
		if bool(unit.get("rescue_npc", false)):
			game.flags["rescued_" + str(unit.id)] = true
		if bool(unit.get("zeke_npc", false)):
			game.flags.zeke_survived = true
	# L06B715 deliberately excludes dragon-valley36; other captured source
	# fortresses set their generator state255, so later deaths cannot restart it.
	for generator in data().reinforcement_generators:
		var index := int(generator.generator_index)
		if int(generator.origin_battle_map_id) == int(game.stage_id) and int(game.stage_id) != 36:
			game.flags["generator_disabled_" + str(index)] = true
			game.flags["reinforcement_state_" + str(index)] = 255
	WorldArmies.remove_battle(game)
	if bool(game.flags.get("duma_defeated", false)):
		if _once(game, "ending_queued"):
			game.story_events.append({"kind": "ending"})
	# Victory XP is already applied by GameState.complete_battle using the
	# exact source base20 formula and EXP99 cap; never award it a second time.

static func can_travel(game, from: int, to: int) -> bool:
	if str(game.route) == "alm" and bool(game.flags.get("scenario_alm_frozen", false)):
		return false
	if str(game.route) == "celica" and bool(game.flags.get("celica_captive", false)):
		return false
	var bits := int(game.flags.get("world_gate_bits", 22))
	for gate in data().world_blocked_edge_bits:
		var a := int(gate.edge[0])
		var b := int(gate.edge[1])
		if (from == a and to == b) or (from == b and to == a):
			if bits & int(gate.mask):
				return false
	return true

static func on_travel(game) -> void:
	var tick := int(game.flags.get("scenario_world_tick", 0)) + 1
	game.flags.scenario_world_tick = tick
	_advance_mobile_armies(game)
	if int(game.world_node) == 36 and str(game.route) == "alm" and not bool(game.flags.get("dragon_valley_released", false)):
		game.flags.world_gate_bits = int(game.flags.get("world_gate_bits", 22)) | 33
		if int(game.flags.get("reinforcement_state_6", 0)) == 0:
			game.flags.reinforcement_state_6 = 1
	# Source queued army0 leaves water-gate hub67 along its sole exit32.
	# Coalesce the noninteractive hub-to-road step into this travel tick.
	for queued in data().queued_world_armies:
		var flag := "queued_army_" + str(int(queued.queue_bit))
		if not bool(game.flags.get(flag, false)):
			continue
		var origin := int(queued.origin_world_node)
		var target := origin
		for generator in data().reinforcement_generators:
			if int(generator.origin_hub_world_node) == origin:
				target = int(generator.origin_battle_map_id)
				break
		if _add_army(game, target, int(queued.group_id), origin):
			game.flags.erase(flag)
	# Probabilistic reinforcement selection uses one active generator per
	# world action, matching the source structure (not source frame timing).
	var active: Array = []
	for generator in data().reinforcement_generators:
		var index := int(generator.generator_index)
		var state := int(game.flags.get("reinforcement_state_" + str(index), 0))
		if state > 0 and state <= generator.waves.size() and not bool(game.flags.get("generator_disabled_" + str(index), false)):
			active.append(generator)
	if active.is_empty():
		return
	var forced_dragon := (int(game.flags.get("world_gate_bits", 0)) & 32) != 0
	var generator: Dictionary = active[game.random_bounded(active.size())]
	if forced_dragon:
		generator = data().reinforcement_generators[6]
	var index := int(generator.generator_index)
	var state := clampi(int(game.flags.get("reinforcement_state_" + str(index), 1)), 1, generator.waves.size())
	var wave: Dictionary = generator.waves[state - 1]
	if game.random_bounded(100) < int(wave.probability_percent):
		_add_army(game, int(generator.origin_battle_map_id), int(wave.group_id), int(generator.origin_hub_world_node))

static func _add_army(game, node: int, group_id: int, previous_node: int = -1) -> bool:
	return not WorldArmies.add(game,node,group_id,previous_node).is_empty()

static func _advance_mobile_armies(game) -> void:
	WorldArmies.ensure(game)
	var mobile: Array = game.flags.get("world_mobile_armies", []).duplicate(true)
	for record in mobile:
		var node := int(record.node)
		var group_id := int(record.group_id)
		var identity := str(record.instance_id)
		if WorldArmies.locate(game,identity).is_empty():
			continue
		if node == int(game.world_node):
			continue
		var neighbors: Array = game.catalog.world_nodes.get(str(node), {}).get("neighbors", [])
		var destination := node
		# L07A4F3 prioritizes an adjacent player party. Native scheduling is
		# one source-route step per travel; frame-level random ties remain TODO.
		if neighbors.any(func(value): return int(value) == int(game.world_node)) and int(game.world_node) < 49:
			destination = int(game.world_node)
		else:
			for path in data().get("army_movement_paths", []):
				for i in range(path.size() - 1):
					if int(path[i]) == node and neighbors.any(func(value): return int(value) == int(path[i + 1])):
						destination = int(path[i + 1])
						break
				if destination != node:
					break
		if destination == node or game.world_armies.get(str(destination), []).size() >= 2:
			continue
		if not WorldArmies.move(game,identity,destination): continue
		if destination == int(game.world_node):
			# Source $7477 records which side initiated the battle. A source
			# turn-limit retreat sends that initiator back to its prior node.
			game.flags.inventory_enemy_initiated = true
			game.flags.inventory_attacking_group_id = group_id
			game.flags.inventory_attacking_instance_id = identity
			game.flags.inventory_attacker_previous_node = node
			# L07A52F returns as soon as one army attacks a player. Do not
			# replace that initiator with another move in the same action.
			break

static func on_chapter(game, _old_chapter: int, new_chapter: int) -> void:
	var bits := int(game.flags.get("world_gate_bits", 22))
	match new_chapter:
		1:
			game.flags.world_gate_bits = 22
			# New-game entry, L0D853B-L0D857C: $6E08|=1 closes the
			# harbor's northern road before the chapter-three transition.
			game.hub_used["9:0"] = true
		2:
			game.flags.scenario_alm_frozen = true
			game.flags.world_gate_bits = bits & 251
		3:
			game.flags.scenario_alm_frozen = false
			game.flags.world_gate_bits = (bits & 239) | 4
			game.route_positions.alm = 52
			game.route_positions.celica = 18
			game.previous_world_node = 16
			# L0CAC05: $6E08=($6E08&254)|2. Hub9's feature byte
			# changes the source road-block patterns, not NPC event flags.
			game.hub_used["9:0"] = false
			game.hub_used["9:1"] = true
		4:
			game.flags.world_gate_bits = bits & 4
			# L0CAC4B: $6E0E|=1 applies hub15 feature0's sluice pattern.
			game.hub_used["15:0"] = true
		5:
			game.flags.scenario_source_chapter_counter = 4
			game.flags.underground_finale = true

static func after_hub_flag(game, flag_id: int) -> void:
	match flag_id:
		31:
			# The same source flag is also set when hostile Zeke dies. Only
			# call the native quest "Tatiana rescued" when she was recruited.
			game.flags.tatiana_rescued = game.parties.get("alm", []).has("tatiana")
		48:
			game.flags.mila_visited = true
		73:
			game.flags.celica_captive = true
			game.flags.scenario_celica_story_phase = 3
		74:
			game.flags.celica_captive = true
			game.flags.scenario_celica_story_phase = 2
		76:
			game.flags.falchion_scene_seen = true
			var snapshot: Dictionary = {}
			for key in game.parties.get("celica", []):
				if game.roster.has(key):
					snapshot[str(key)] = int(game.roster[key].get("hp", 0))
			game.flags.celica_captive_hp = snapshot
		82:
			game.flags.scenario_final_merge_ready = true
			game.flags.celica_captive = false
			game.flags.scenario_celica_story_phase = 4
