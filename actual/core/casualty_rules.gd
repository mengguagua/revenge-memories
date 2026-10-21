extends RefCounted
## Persistent injuries; chapter three combines unused sources at the meeting camp.
const SOURCES := {"church":"alm", "lighthouse":"celica", "meeting":"shared", "final_delivery":"shared"}

static func owner(state: Dictionary, id: String) -> String:
	for route in ["alm", "celica"]:
		if state.get("parties", {}).get(route, []).has(id): return route
	return ""

static func initialize_unit(unit: Dictionary) -> void:
	if not unit.has("dying"): unit.dying = false
	if not unit.has("ever_dying"): unit.ever_dying = false
	# Campaign stats originate in JSON; keep integer-valued JSON numbers stable
	# across reloads, including exact actor/roster comparisons.
	if not unit.has("treatment_count"): unit.treatment_count = 0.0

static func ensure_sources(state: Dictionary) -> void:
	var flags: Dictionary = state.flags
	if not flags.has("treatment_sources"): flags.treatment_sources = {}
	if not flags.has("treatment_used"): flags.treatment_used = {"alm":0, "celica":0}
	var clears: Array = state.cleared_stages
	if flags.get("cooperation_done", false) and clears.any(func(id): return int(id) == 103):
		flags.treatment_sources.church = true
	if flags.get("islanders_settled", false) and clears.any(func(id): return int(id) == 204):
		flags.treatment_sources.lighthouse = true
	if flags.get("D33_done",false) and clears.any(func(id):return int(id)==303) and clears.any(func(id):return int(id)==306):
		flags.treatment_sources.meeting = true

	if flags.get("west_tower_safe",false) and flags.get("island_loop_safe",false) and flags.get("D42_done",false):
		flags.treatment_sources.final_delivery=true

static func available(flags: Dictionary, route: String) -> int:
	if flags.get("D33_done",false):
		return flags.get("treatment_sources",{}).size()-int(flags.get("treatment_used",{}).get("alm",0))-int(flags.get("treatment_used",{}).get("celica",0))
	var granted := 0
	for source in SOURCES:
		if SOURCES[source] == route and flags.get("treatment_sources", {}).get(source, false): granted += 1
	return granted - int(flags.get("treatment_used", {}).get(route, 0))

static func _injure(unit: Dictionary) -> void:
	initialize_unit(unit)
	unit.dead = false
	unit.dying = true
	unit.ever_dying = true
	unit.hp = 0.0
	unit.acted = true
	if unit.has("death_place"):
		unit.injury_place = unit.death_place
		unit.erase("death_place")

static func migrate(state: Dictionary) -> void:
	# Validate the original checkpoint first. Migrate live and retry states
	# independently so a new injury can still be rolled back normally.
	var active: bool = state.get("mode", "") in ["battle", "victory", "defeat"]
	if active:
		for unit in state.units:
			if unit.get("neutral",false) or unit.get("temporary",false) or unit.side!="player":continue
			var route := owner(state, str(unit.id))
			if route.is_empty() or int(unit.hp) > 0: continue
			# Tactical growth is newer than the pre-battle roster. The unit's
			# item is authoritative after the original inventory transfer.
			state.roster[unit.id] = unit.duplicate(true)
	for id in state.roster:
		var unit: Dictionary = state.roster[id]
		initialize_unit(unit)
		var route := owner(state, str(id))
		if route.is_empty() or (not unit.get("dead", false) and int(unit.hp) > 0): continue
		_injure(unit)
		var held := int(unit.get("item_id", 0))
		if held > 0:
			state.convoy[route].append(held)
			unit.item_id = 0
	for unit in state.units:
		if owner(state, str(unit.id)).is_empty(): continue
		if unit.get("neutral",false) or unit.get("temporary",false) or unit.side!="player":continue
		initialize_unit(unit)
		if int(unit.hp) > 0: continue
		_injure(unit)
		unit.item_id = 0
	ensure_sources(state)
	if not state.get("battle_start_snapshot", {}).is_empty():
		migrate(state.battle_start_snapshot)
	state.schema = 3

static func valid(state: Dictionary) -> bool:
	var flags: Dictionary = state.flags
	if not flags.get("treatment_sources") is Dictionary or not flags.get("treatment_used") is Dictionary: return false
	for source in flags.treatment_sources:
		if not SOURCES.has(source) or not flags.treatment_sources[source] is bool or flags.treatment_sources[source] != true: return false
	if flags.treatment_used.size() != 2: return false
	var spent := {"alm":0, "celica":0}
	for id in state.roster:
		var route := owner(state, str(id))
		var unit: Dictionary = state.roster[id]
		if route.is_empty():
			if unit.get("dying", false) or int(unit.get("treatment_count", 0)) != 0: return false
			continue
		if not unit.get("dying") is bool or not unit.get("ever_dying") is bool: return false
		var count = unit.get("treatment_count")
		if not (count is int or count is float) or count != int(count) or int(count) not in [0,1]: return false
		if unit.get("dead", false) or bool(unit.dying) != (int(unit.hp) <= 0): return false
		if (unit.dying or int(count) == 1) and not unit.ever_dying: return false
		if str(id) in ["hunapu", "eileen"] and int(count) != 0: return false
		spent[route] += int(count)
	for unit in state.units:
		if owner(state, str(unit.id)).is_empty(): continue
		if unit.get("neutral",false) or unit.get("temporary",false) or unit.side!="player":continue
		if not unit.get("dying") is bool or unit.get("dead", false): return false
		if bool(unit.dying) != (int(unit.hp) <= 0): return false
		if bool(unit.dying)!=bool(state.roster[unit.id].dying):return false
		if int(unit.get("treatment_count",0))!=int(state.roster[unit.id].treatment_count):return false
	for route in ["alm", "celica"]:
		var used = flags.treatment_used.get(route)
		if not (used is int or used is float) or used != int(used) or int(used) != spent[route]: return false
		if available(flags, route) < 0: return false
	var expected := state.duplicate(true)
	expected.flags.treatment_sources = {}
	ensure_sources(expected)
	return expected.flags.treatment_sources == flags.treatment_sources

static func enter_dying(game, unit: Dictionary) -> void:
	var route := owner({"parties":game.parties}, str(unit.get("id", "")))
	if route.is_empty() or int(unit.get("hp", 1)) > 0: return
	var first := not bool(unit.get("dying", false))
	_injure(unit)
	var persistent := unit.duplicate(true)
	persistent.acted = false
	game.roster[unit.id] = persistent
	if first:
		game.queue_pages([{"speaker":"战场提示", "text":str(unit.name_zh)+"濒死，已撤至照护处，暂时不能出阵。"}])

static func treat(game, id: String) -> Dictionary:
	if game.mode!="hub" or (not (game.chapter==5 and game.hub_record in ["H51","H55"]) and not (game.hub_record=="H10" and game.flags.get("D33_done",false)) and ((game.route=="alm" and game.hub_record!="H04") or (game.route=="celica" and game.hub_record!="H25"))):
		return {"valid":false, "reason":"请到本队救治泉接受救治"}
	game.ensure_treatment_sources()
	if not game.party.has(id) or id in ["hunapu", "eileen"]: return {"valid":false, "reason":"只能救治本队正式同伴"}
	var unit: Dictionary = game.roster.get(id, {})
	if unit.is_empty() or not game.is_dying(unit): return {"valid":false, "reason":"该成员无需濒死救治"}
	if int(unit.get("treatment_count", 0)) >= 1: return {"valid":false, "reason":"已接受过一次救治，无法再次救治"}
	if available(game.flags, game.route) <= 0: return {"valid":false, "reason":"本队救治份额已用尽"}
	var before := unit.duplicate(true)
	var old_flags: Dictionary = game.flags.duplicate(true)
	unit.dying = false
	unit.dead = false
	unit.hp = int(unit.max_hp)
	unit.acted = false
	unit.treatment_count = 1.0
	game.flags.treatment_used[game.route] = int(game.flags.treatment_used[game.route]) + 1
	# Stale, settled tactical actors must agree with the restored roster.
	var old_units: Array = game.units.duplicate(true)
	for actor in game.units:
		if str(actor.id) == id:
			actor.dying = false; actor.dead = false; actor.hp = int(unit.max_hp); actor.treatment_count = 1.0
	if not game.save_game():
		game.roster[id] = before; game.flags = old_flags; game.units = old_units
		return {"valid":false, "reason":"保存失败，未消耗救治份额"}
	return {"valid":true, "remaining":available(game.flags, game.route)}
