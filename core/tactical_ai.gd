class_name FeTacticalAI
extends RefCounted
## Native decisions transcribed from bank003 L038343-L039444.
## Source RNG probabilities, HP gates, goal modes and summons are retained.
## Equal-cost path ordering uses the game's weighted graph, not the original
## raster scan's randomized predecessor ordering. See reports/tactical-ai-source.json.
const Items = preload("res://core/item_rules.gd")
const Rules = preload("res://core/combat_rules.gd")
const DEFENSIVE_TERRAIN = [8, 15, 20, 1]
const ADJACENT = [Vector2i.DOWN, Vector2i.UP, Vector2i.RIGHT, Vector2i.LEFT]

static func action(game, unit: Dictionary, gather: bool = false) -> Dictionary:
	var result = _base(unit)
	if int(unit.get("hp", 0)) <= 0 or bool(unit.get("dead", false)) or bool(unit.get("acted", false)):
		return result
	var enemy = str(unit.get("side", "")) == "enemy"
	var flags = int(unit.get("ai_flags", unit.get("raw_ai_flags", 0)))
	if enemy and flags & 8:
		unit.ai_flags = flags & 247
		result.reason = "source_skip_once"
		return result
	var actor = unit.duplicate(true)
	actor.erase("weapon_index")
	var teleport = {}
	if enemy and int(actor.class_id) == 16:
		var name_id = _name(actor)
		if name_id in [142, 170]:
			if game.random_bounded(256) >= 160:
				var summon = _summon(game, actor, 16, 0, false)
				if not summon.is_empty(): return summon
		else:
			teleport = _witch_landing(game, actor)
			if not teleport.is_empty(): actor.position = [teleport.position.x, teleport.position.y]
	var mode = _update_mode(game, unit) if enemy else 0
	actor.ai_flags = unit.get("ai_flags", flags)
	var graph = game.reachable(actor)
	var opponents = game.living("player" if enemy else "enemy")
	var spell_id = _attack_spell(actor)
	if spell_id >= 0: actor.weapon_index = spell_id
	var can_initiate = not gather and mode != 1 and Rules.can_attack(actor)
	if enemy and (int(actor.class_id) == 19 or (int(actor.class_id) == 21 and int(actor.hp) < 52)):
		can_initiate = false
	if not enemy and (int(actor.class_id) == 18 or (int(actor.class_id) in [15, 16, 19] and int(actor.hp) * 2 < int(actor.max_hp))):
		can_initiate = false
	if enemy and int(actor.class_id) in [15, 16] and spell_id < 0:
		can_initiate = false
	result = _attack_choice(game, actor, graph, opponents) if can_initiate else _base(actor)
	if str(result.target).is_empty():
		if enemy and mode == 1 and str(unit.get("class", "")) == "brigand":
			result.merge(game._recovery_action(unit, graph), true)
		else:
			var goal_mode = 3 if enemy and int(actor.class_id) == 19 and mode == 0 else mode
			result.destination = _goal_destination(game, actor, graph, goal_mode, opponents, gather)
		if enemy and mode == 1 and result.destination == _pos(actor) and game.category(_pos(actor)) != 15:
			# Original failed recovery search clears bit7 and restores the saved mode.
			var full = game.reachable(actor, true)
			if not _has_recovery_goal(game, actor, full):
				unit.ai_flags = (int(unit.ai_flags) & 124) | ((int(unit.ai_flags) & 48) >> 4)
	else:
		result.spell_id = spell_id
	if enemy:
		_source_support(game, actor, result)
		var cid = int(actor.class_id)
		if cid == 19 and game.living("enemy").size() < 20 and game.random_bounded(256) >= 128:
			var spec = Items.enemy_summon_spec(actor, 0)
			var summon = _summon(game, actor, int(spec.class_id), int(spec.hp_cost), false)
			if not summon.is_empty(): result = summon
		elif cid in [18, 21] and str(result.target).is_empty() and not bool(result.support):
			var summon = _summon(game, actor, 18, 0, true)
			if not summon.is_empty(): result = summon
	if not teleport.is_empty():
		result.teleport = true
		result.teleport_position = teleport.position
		result.teleport_source = "L03841D-L038588"
	return result

static func _base(unit: Dictionary) -> Dictionary:
	return {"destination": _pos(unit), "target": "", "spell_id": -1,
		"support": false, "teleport": false}

static func _pos(unit: Dictionary) -> Vector2i:
	var p = unit.get("position", [0, 0])
	return Vector2i(int(p[0]), int(p[1]))

static func _name(unit: Dictionary) -> int:
	return int(unit.get("name_id", unit.get("character_id", unit.get("source_id", 0))))

static func _distance(a: Vector2i, b: Vector2i) -> int:
	return absi(a.x - b.x) + absi(a.y - b.y)

static func _update_mode(game, unit: Dictionary) -> int:
	if str(unit.get("class", "")) == "brigand":
		game._brigand_seeks_recovery(unit)
		return int(unit.get("ai_flags", 0)) & 3
	var flags = int(unit.get("ai_flags", unit.get("raw_ai_flags", 0)))
	var mode = flags & 3
	var hp = int(unit.hp)
	var maximum = int(unit.max_hp)
	if mode in [0, 3] and flags & 128:
		var health = (hp * 2) & 255
		if flags & 64 and int(unit.get("defence", 0)) >= 6: health = (health * 2) & 255
		if health < maximum: mode = 1
	elif mode == 1:
		if hp == maximum or ((int(game.frame_counter) & 1) and ((hp * 2) & 255) >= maximum): mode = (flags & 48) >> 4
	elif mode == 2:
		var commander = _commander(game, unit)
		if commander.is_empty() or int(commander.hp) <= 0: mode = 0
	unit.ai_flags = (flags & 252) | mode
	return mode

static func _commander(game, unit: Dictionary) -> Dictionary:
	var slot_key = "enemy_slot" if str(unit.side) == "enemy" else "player_slot"
	var first = {}
	for other in game.units:
		if str(other.side) != str(unit.side): continue
		if first.is_empty(): first = other
		if int(other.get(slot_key, -1)) == 0: return other
	return first

static func _attack_spell(unit: Dictionary) -> int:
	if str(unit.side) == "enemy" and int(unit.class_id) in [15, 16]:
		var bits = int(unit.get("magic_flags", unit.get("raw_magic_flags", 0)))
		var table = Items.data().enemy_spell_tables.get(str(int(unit.class_id)), [])
		for i in range(mini(4, table.size())):
			if bits & (1 << i): return int(table[i])
		return -1
	var weapon = Rules.weapon_index(unit)
	return weapon if weapon >= 23 and weapon < 47 and not Items.is_support(weapon) else -1

static func _attack_choice(game, actor: Dictionary, graph: Dictionary, opponents: Array) -> Dictionary:
	var result = _base(actor)
	var cells = graph.costs.keys()
	cells.sort_custom(func(a, b):
		if graph.costs[a] != graph.costs[b]: return int(graph.costs[a]) < int(graph.costs[b])
		return a.y < b.y if a.y != b.y else a.x < b.x)
	var best_score = 0
	var opposing_commander = _commander(game, {"side": "player" if str(actor.side) == "enemy" else "enemy"})
	var first_opponent = str(opposing_commander.get("id", ""))
	for cell in cells:
		if not game.can_stop(actor, cell): continue
		for i in range(opponents.size()):
			var target = opponents[i]
			var distance = _distance(cell, _pos(target))
			if not Rules.can_attack(actor, distance) or Rules.attack_blocked(actor, target): continue
			if str(actor.side) == "enemy" and distance > _source_range(actor): continue
			var score = _score(game, actor, target, cell, distance, str(target.id) == first_opponent)
			if score > best_score:
				best_score = score
				result.destination = cell
				result.target = str(target.id)
	return result

static func _score(game, actor: Dictionary, target: Dictionary, cell: Vector2i, distance: int, first_slot: bool) -> int:
	# L038843-L038A85: source uses damage, counter availability, terrain,
	# low HP and priest priority, rather than hit chance or a new kill bonus.
	var weapon = Rules.weapon_index(actor)
	var held = int(actor.get("item_id", 0))
	var might = int(Items.item(held).get("might", 0))
	if Items.effective_against(held, target): might *= 3
	var magic = int(actor.class_id) in [15, 16, 19] or weapon == 15
	var defence = int(target.get("resistance", 0)) if magic else int(target.get("defence", 0)) + _shield(target)
	var power = int(actor.get("strength", 0)) + might
	if not Items.effective_against(held, target): power = mini(60, power)
	var attack = (power & 255) - defence
	if attack < 0: attack = 1
	var bonus = 5 if first_slot else 0
	if not first_slot and not int(actor.class_id) in [15, 16]:
		if int(target.class_id) in [11, 18]: bonus += 20
		elif int(target.class_id) == 17: bonus += 10
	if not int(actor.class_id) in [3, 5]: bonus += int(game.terrain_avoid(cell))
	if int(target.hp) <= 10: bonus += 2 * (17 - int(target.hp))
	var counter = Rules.default_counter(target, distance)
	var risk = 0
	if distance <= _source_range(target):
		var target_magic = int(target.class_id) in [15, 16, 19] or Rules.weapon_index(counter) == 15
		var own_defence = int(actor.get("resistance", 0)) if target_magic else int(actor.get("defence", 0)) + _shield(actor)
		risk = maxi(0, int(target.get("strength", 0)) - own_defence)
	else: bonus += 40
	return mini(255, ((attack * 2 - risk + 60) & 255) + bonus)

static func _source_range(unit: Dictionary) -> int:
	var cid = int(unit.class_id)
	var reach = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 3, 1, 2, 2, 1, 1, 2, 5, 1, 1][clampi(cid - 1, 0, 21)]
	var item = int(unit.get("item_id", 0))
	if item in [4, 7] and cid in [1, 2, 3, 4, 5, 6, 7, 22]: reach = 2
	if item in [20, 21, 22] and cid in [12, 13, 20]: reach = 5
	if item == 57 and cid in [15, 16, 19]: reach = 5
	return reach

static func _shield(unit: Dictionary) -> int:
	return int({48: 3, 49: 5, 50: 7}.get(int(unit.get("item_id", 0)), 0))

static func _goal_destination(game, actor: Dictionary, turn_graph: Dictionary, mode: int, opponents: Array, gather: bool) -> Vector2i:
	var start = _pos(actor)
	var full = game.reachable(actor, true)
	var commander = game.find_unit(game.leader_id()) if gather else _commander(game, actor)
	var goal = start
	var best = 61
	for cell in full.costs:
		var cost = int(full.costs[cell])
		if cost >= best or not game.can_stop(actor, cell): continue
		var valid = false
		if gather or mode == 2:
			valid = not commander.is_empty() and _distance(cell, _pos(commander)) <= 1
		elif mode == 1:
			valid = _recovery_goal(game, actor, cell)
		elif mode == 3:
			valid = int(game.category(cell)) in DEFENSIVE_TERRAIN
		else:
			for target in opponents:
				if _distance(cell, _pos(target)) == 1:
					valid = true
					break
		if valid:
			goal = cell
			best = cost
	if goal == start: return start
	var path = [goal]
	while path[0] != start:
		if not full.previous.has(path[0]): return start
		path.push_front(full.previous[path[0]])
	var destination = start
	for cell in path:
		if turn_graph.costs.has(cell) and game.can_stop(actor, cell): destination = cell
	return destination

static func _recovery_goal(game, actor: Dictionary, cell: Vector2i) -> bool:
	if int(game.category(cell)) == 15: return true
	for direction in ADJACENT:
		var other = game.unit_at(cell + direction)
		if not other.is_empty() and str(other.side) == str(actor.side) and str(other.id) != str(actor.id) and int(other.class_id) in [15, 19]: return true
	return false

static func _has_recovery_goal(game, actor: Dictionary, graph: Dictionary) -> bool:
	for cell in graph.costs:
		if int(graph.costs[cell]) < 61 and game.can_stop(actor, cell) and _recovery_goal(game, actor, cell): return true
	return false

static func _witch_landing(game, actor: Dictionary) -> Dictionary:
	# L038430-L03856D: one random byte jointly determines player slot and
	# both coordinate offsets; the final LSR carry affects the x offset.
	var flags = int(actor.get("ai_flags", actor.get("raw_ai_flags", 0)))
	if (flags & 3) != 0 or ((int(actor.hp) * 2) & 255) < int(actor.max_hp): return {}
	if game.random_bounded(256) >= 64: return {}
	var players = game.units.filter(func(u): return str(u.side) == "player")
	var slots: Dictionary = {}
	for i in range(players.size()): slots[int(players[i].get("player_slot", i))] = players[i]
	for attempt in range(15):
		var raw = int(game.random_bounded(256))
		var slot = (raw & 60) >> 2
		if slot >= 10: slot = 0
		if not slots.has(slot) or int(slots[slot].hp) <= 0: continue
		var low = raw & 7
		var high = (raw >> 4) & 7
		var carry = (raw >> 3) & 1
		var dy = low - 4 + (1 if low >= 4 else 0)
		var dx = high - 4 + carry + (1 if high >= 4 - carry else 0)
		var cell = _pos(slots[slot]) + Vector2i(dx, dy)
		if not game.in_bounds(cell) or cell.x <= 0 or cell.y <= 0 or cell.x >= int(game.battle_data.map.width) - 1 or cell.y >= int(game.battle_data.map.height) - 1: continue
		if not game.unit_at(cell).is_empty() or game.movement_cost(actor, cell) >= 255: continue
		return {"position": cell}
	return {}

static func _source_support(game, actor: Dictionary, result: Dictionary) -> void:
	if _name(actor) in [167, 144] and game.random_bounded(256) < 32:
		result.target = ""
		result.spell_id = 30
		result.support = true
		result.special = "quake"
		result.source = "L038DD0; L06A156-L06A20F"
		result.quake = {"player_random_upper": 20, "player_base": 10, "enemy_random_upper": 4, "enemy_base": 1, "subtract_half_luck": true, "hp_floor": 1}
		return
	if not str(result.target).is_empty() or int(actor.class_id) != 15: return
	var bits = int(actor.get("magic_flags", actor.get("raw_magic_flags", 0)))
	if bits & 32:
		if game.random_bounded(256) >= 64 or int(actor.hp) <= Items.cost(36): return
		for other in game.living(str(actor.side)):
			if int(other.hp) < int(other.max_hp):
				result.target = str(actor.id)
				result.spell_id = 36
				result.support = true
				return
	elif bits & 16 and int(actor.hp) > Items.cost(35):
		for direction in ADJACENT:
			var other = game.unit_at(result.destination + direction)
			if not other.is_empty() and str(other.side) == str(actor.side) and str(other.id) != str(actor.id) and int(other.hp) < int(other.max_hp):
				result.target = str(other.id)
				result.spell_id = 35
				result.support = true
				return

static func _summon(game, actor: Dictionary, cid: int, cost: int, divide: bool) -> Dictionary:
	if game.living("enemy").size() >= 20 or int(actor.hp) <= cost: return {}
	var count = (int(game.random_bounded(256)) & 3) + 1 if divide else (int(game.random_bounded(maxi(1, int(actor.get("strength", 1))))) >> 1) + 1
	var template_id = 11 if (divide and int(actor.class_id) == 21) or (int(actor.class_id) == 19 and not (int(actor.get("magic_flags", actor.get("raw_magic_flags", 0))) & 240)) else 10 if divide else int({5: 0, 3: 1, 11: 2, 17: 3, 16: 9}.get(cid, 11))
	var result = _base(actor)
	result.target = str(actor.id)
	result.spell_id = 37
	result.support = true
	result.special = "summon"
	result.source_summon = {"class_id": cid, "count": count, "hp_cost": cost, "capacity": 20,
		"level": 5 if template_id == 11 else 1, "source_template_index": template_id,
		"character_id": 176 + cid, "ai_flags": 8 if template_id == 11 else 200 if cid == 16 else 72,
		"magic_flags": 1 if cid == 16 else 0, "no_experience": false,
		"source": "L039358-L039444; L0899FA-L089A54", "divide": divide}
	return result
