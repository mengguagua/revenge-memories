extends RefCounted
## Adapted campaign supply. Deterministic grants never depend on enemy loot.
const Items = preload("res://core/item_rules.gd")
const Armaments = preload("res://core/story_armaments.gd")
static var _data: Dictionary = {}

static func data() -> Dictionary:
	if _data.is_empty(): _data = JSON.parse_string(FileAccess.get_file_as_string("res://data/equipment_progression.json"))
	return _data

static func award_clear(game, stage: int, announce: bool = true) -> void:
	Armaments.award_clear(game,stage,announce)
	var rewards: Array = data().clear_rewards.get(str(stage), [])
	var taken: Dictionary = game.flags.get("equipment_clear_rewards", {})
	if rewards.is_empty() or taken.get(str(stage), false): return
	var route: String = str(game.stages[stage].get("route", "alm" if stage < 200 else "celica"))
	var names: Array[String] = []
	for item in rewards:
		# Automatic rewards preserve equipment even when manual storage is full.
		game.convoy[route].append(int(item))
		names.append(str(Items.item(int(item)).name_zh))
	taken[str(stage)] = true
	game.flags.equipment_clear_rewards = taken
	if announce: game.queue_lines("旁白：战后整理出" + "、".join(names) + "，已收入本队行囊，可在部队整备中分配。", "EQUIPMENT-" + str(stage))

static func _match(member: String, roster: Dictionary, available: Array, owners: Dictionary, visited: Dictionary) -> bool:
	for i in range(available.size()):
		if visited.has(i) or not Items.can_use(roster[member], int(available[i])): continue
		visited[i] = true
		if not owners.has(i) or _match(str(owners[i]), roster, available, owners, visited):
			owners[i] = member
			return true
	return false

static func reconcile(game) -> void:
	# Called only at a safe hub/world/preparation boundary, never mid-exchange.
	for stage in game.cleared_stages: award_clear(game, int(stage), false)
	var checked: Dictionary = game.flags.get("equipment_starter_checked", {})
	for route in ["alm", "celica"]:
		var members: Array = []
		var available: Array = []
		var army: Array = game.party if route == game.route else game.parties.get(route, [])
		for id in army:
			var u: Dictionary = game.roster.get(id, {})
			if u.is_empty() or u.get("dead", false) or int(u.get("hp", 0)) <= 0: continue
			members.append(str(id))
			var held := int(u.get("item_id", 0))
			if held > 0 and str(Items.item(held).get("kind", "")) == "weapon": available.append(held)
		for held in game.convoy[route]:
			if str(Items.item(int(held)).get("kind", "")) == "weapon": available.append(int(held))
		var owners: Dictionary = {}
		for id in members: _match(id, game.roster, available, owners, {})
		var covered: Array = owners.values()
		for id in members:
			if not checked.get(id, false) and not covered.has(id):
				var starter := int(data().starter_items[id])
				if int(game.roster[id].get("item_id", 0)) == 0 and Items.can_use(game.roster[id], starter): game.roster[id].item_id = starter
				else: game.convoy[route].append(starter)
			checked[id] = true
	game.flags.equipment_starter_checked = checked
