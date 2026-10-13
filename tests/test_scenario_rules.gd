extends SceneTree
const Scenario = preload("res://core/scenario_rules.gd")
var checks := 0
var failures: Array[String] = []

class FixtureGame extends RefCounted:
	var catalog: Dictionary = {}
	var characters: Dictionary = {}
	var stages: Dictionary = {}
	var units: Array = []
	var roster: Dictionary = {}
	var party: Array = ["alm"]
	var parties: Dictionary = {"alm": ["alm"], "celica": ["celica"]}
	var route := "alm"
	var chapter := 1
	var world_node := 1
	var world_armies: Dictionary = {}
	var encounter_groups: Array = []
	var flags: Dictionary = {}
	var hub_flags: Dictionary = {}
	var hub_used: Dictionary = {}
	var battle_return: Dictionary = {}
	var story_events: Array = []
	var route_positions: Dictionary = {"alm": 36, "celica": 77}
	var previous_world_node := 49
	var stage_id := 1
	var battle_outcome := ""
	var mode := "battle"
	func apply_hub_flag(flag_id: int) -> void:
		flags["source_flag_" + str(flag_id)] = true
		Scenario.after_hub_flag(self, flag_id)
	func random_bounded(_upper: int) -> int:
		return 0

func _initialize() -> void:
	call_deferred("_run")

func _check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures.append(label)
		push_error(label)

func _read(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))

func _unit(game, key: String) -> Dictionary:
	var value: Dictionary = game.characters[key].duplicate(true)
	value.id = key
	value.side = "player"
	value.acted = false
	value.dead = false
	value.position = [1, 1]
	return value

func _fixture(stage_id: int = 1, route: String = "alm"):
	var game = FixtureGame.new()
	game.catalog = _read("res://data/campaign.json")
	game.characters = game.catalog.characters
	for id in [stage_id, 62]:
		game.stages[id] = _read(game.catalog.stages[str(id)].path)
	game.stage_id = stage_id
	game.world_node = stage_id
	game.route = route
	game.party = [route]
	game.roster.alm = _unit(game, "alm")
	game.roster.celica = _unit(game, "celica")
	game.units = [_unit(game, route)]
	game.encounter_groups = game.stages[stage_id].enemy_group_ids.duplicate()
	for source in game.stages[stage_id].enemies:
		var enemy: Dictionary = source.duplicate(true)
		enemy.side = "enemy"
		enemy.acted = false
		game.units.append(enemy)
	return game

func _source(game, id: int) -> Dictionary:
	for unit in game.units:
		if int(unit.get("source_enemy_character_id", unit.get("character_id", 0))) == id:
			return unit
	return {}

func _kill(game, id: int) -> Dictionary:
	var unit := _source(game, id)
	assert(not unit.is_empty(), "Missing source fixture%s" % id)
	unit.hp = 0
	Scenario.on_unit_death(game, unit)
	return unit

func _has_story(game, group: String, key: int) -> bool:
	return game.story_events.any(func(event): return event.get("group", "") == group and event.get("key", "") == str(key))

func _run() -> void:
	_test_npc_survival()
	_test_zeke()
	_test_delthea()
	_test_desert_choice()
	_test_commanders()
	_test_gates_and_armies()
	_test_final_route()
	var file := FileAccess.open("res://reports/scenario-rules-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures, "fixtures": "original catalog; no user saves or graphics"}, "\t") + "\n")
	print("SCENARIO RULES: %d checks, %d failures" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

func _test_npc_survival() -> void:
	var game = _fixture(29)
	Scenario.on_battle_start(game)
	var mathilda := _source(game, 19)
	_check(not mathilda.is_empty(), "Mathilda spawns in rescue battle")
	_check(int(mathilda.position[0]) == 15 and int(mathilda.position[1]) == 1, "Mathilda original extra deployment position")
	_check(mathilda.neutral and not mathilda.controllable and mathilda.no_experience, "Rescue ally is neutral and grants no player XP")
	_check(not game.party.has("mathilda"), "Rescue does not instantly recruit")
	_kill(game, 19)
	_check(game.roster.mathilda.dead and game.flags.unrecruitable_mathilda, "NPC death permanently blocks fresh recruit")
	game.units = [_unit(game, "alm")]
	Scenario.on_battle_start(game)
	_check(_source(game, 19).is_empty(), "Returning to rescue map cannot resurrect killed NPC")
	var other = _fixture(11, "celica")
	Scenario.on_battle_start(other)
	_check(other.units.filter(func(unit): return bool(unit.get("rescue_npc", false))).size() == 3, "Valbar Kamui and Leo all spawn as NPCs")
	Scenario.on_victory(other)
	_check(other.flags.rescued_valbar and other.flags.rescued_kamui and other.flags.rescued_leo, "All three surviving rescuable fates preserved")

func _test_zeke() -> void:
	var hostile = _fixture(34)
	Scenario.on_battle_start(hostile)
	_check(_source(hostile, 139).side == "enemy", "Zeke stays enemy before Tatiana event")
	var allied = _fixture(34)
	allied.apply_hub_flag(31)
	Scenario.on_battle_start(allied)
	_check(_source(allied, 139).side == "player" and _source(allied, 139).neutral, "Tatiana flag changes Zeke to green ally")
	_check(_source(allied, 138).side == "enemy", "Jerome remains an enemy")
	_check(allied.units.filter(func(unit): return bool(unit.get("neutral", false))).size() == 10, "Entire source Zeke army changes allegiance")
	_check(not allied.party.has("zeke"), "Zeke not controllable until village recruitment")
	_check(allied.story_events.filter(func(event): return event.get("key", "") == "19").size() == 1, "Zeke alliance dialogue is queued exactly once")
	_kill(allied, 139)
	_check(allied.roster.zeke.dead and allied.flags.unrecruitable_zeke, "Allied Zeke death prevents village resurrection")

func _test_delthea() -> void:
	var game = _fixture(32)
	Scenario.on_battle_start(game)
	_kill(game, 143)
	var saved := _source(game, 145)
	_check(saved.rescued and not saved.dead and saved.no_drop, "Tatara death rescues Delthea without death or item drop")
	_check(game.flags.delthea_rescued and not game.flags.get("unrecruitable_delthea", false), "Living Delthea stays recruitable")
	_check(_has_story(game, "events", 12), "Rescue dialogue queued")
	Scenario.on_unit_death(game, saved)
	_check(not game.flags.get("unrecruitable_delthea", false), "Zero tactical HP rescue is not mistaken for death")
	var failure = _fixture(32)
	Scenario.on_battle_start(failure)
	_kill(failure, 145)
	_kill(failure, 143)
	_check(failure.roster.delthea.dead and failure.flags.unrecruitable_delthea, "Killing captive permanently blocks rescue")
	_check(not failure.flags.get("delthea_rescued", false), "Late Tatara kill cannot revive Delthea")

func _test_desert_choice() -> void:
	var game = _fixture(22, "celica")
	game.world_armies = {"22": [22], "23": [23], "24": [24]}
	Scenario.on_battle_start(game)
	_kill(game, 136)
	_check(game.flags.desert_survivor == "sonya", "Deen defeat selects Sonya")
	_check(not game.world_armies.has("23") and game.world_armies.has("24"), "Only opposing desert army withdraws")
	_check(game.flags.unrecruitable_deen and not game.flags.get("unrecruitable_sonya", false), "Desert recruitment stays exclusive")
	_check(not game.party.has("sonya"), "Desert survivor awaits stronghold dialogue")
	var other = _fixture(23, "celica")
	other.world_armies = {"22": [22], "23": [23]}
	Scenario.on_battle_start(other)
	_kill(other, 157)
	_check(other.flags.desert_survivor == "deen" and not other.world_armies.has("22"), "Reverse desert branch selects Deen")

func _test_commanders() -> void:
	var gate = _fixture(7)
	Scenario.on_battle_start(gate)
	_kill(gate, 147)
	_check(_source(gate, 155).retreated and _source(gate, 155).no_drop, "Slayde defeat makes Desaix double retreat without Dracoshield")
	_check(_has_story(gate, "events", 1), "Desaix double retreat dialogue queued")
	var rudolf = _fixture(42)
	Scenario.on_battle_start(rudolf)
	var corpse := _kill(rudolf, 133)
	var count: int = rudolf.story_events.size()
	Scenario.on_unit_death(rudolf, corpse)
	_check(rudolf.story_events.size() == count, "Repeated death callback cannot repeat story")
	_check(rudolf.battle_outcome == "victory", "Rudolf death forces commander victory")
	_check(rudolf.units.filter(func(unit): return unit.side == "enemy" and int(unit.hp) > 0).is_empty(), "Surviving imperial troops surrender")
	_check(_has_story(rudolf, "death_quotes", 53), "Rudolf revelation uses actual full source death quote")
	var finale = _fixture(62)
	finale.flags.scenario_final_merge_ready = true
	Scenario.on_battle_start(finale)
	_kill(finale, 167)
	_check(finale.flags.campaign_complete and finale.battle_outcome == "victory", "Duma death completes campaign with surviving enemies")
	Scenario.on_victory(finale)
	Scenario.on_victory(finale)
	_check(finale.story_events.filter(func(event): return event.kind == "ending").size() == 1, "Ending queued exactly once")
	var loss = _fixture(62)
	loss.flags.scenario_final_merge_ready = true
	Scenario.on_battle_start(loss)
	_kill(loss, 1)
	_kill(loss, 167)
	_check(loss.battle_outcome == "defeat" and not loss.flags.get("campaign_complete", false), "Dead protagonist cannot complete campaign")

func _test_gates_and_armies() -> void:
	var game = _fixture(1)
	_check(not Scenario.can_travel(game, 16, 17), "North gate closed before chapter3")
	Scenario.on_chapter(game, 1, 2)
	_check(not Scenario.can_travel(game, 49, 1), "Alm route freezes during Celica chapter2")
	game.route = "celica"
	_check(Scenario.can_travel(game, 57, 7), "Celica can enter Zofia during chapter2")
	Scenario.on_chapter(game, 2, 3)
	game.route = "alm"
	_check(Scenario.can_travel(game, 16, 17), "Chapter3 opens north gate")
	_check(not Scenario.can_travel(game, 32, 33), "Rigel border remains closed during chapter3")
	Scenario.on_chapter(game, 3, 4)
	_check(Scenario.can_travel(game, 32, 33), "Sluice progression opens chapter4 border")
	game.world_armies = {"42": [42]}
	Scenario.on_chapter(game, 4, 5)
	_check(game.world_armies.has("42") and game.flags.scenario_source_chapter_counter == 4, "Underground finale does not clear armies")
	var queue = _fixture(29)
	Scenario.on_battle_start(queue)
	_kill(queue, 129)
	_check(queue.flags.queued_army_0, "Real Desaix death queues water-gate army")
	Scenario.on_travel(queue)
	_check(queue.world_armies.has("32") and queue.world_armies["32"].has(32), "Queued Tatara army enters water gate battlefield")
	_check(not queue.flags.get("queued_army_0", false), "Successful queued spawn consumed once")
	var victory = _fixture(40)
	Scenario.on_battle_start(victory)
	Scenario.on_victory(victory)
	_check(victory.flags.generator_disabled_4 and victory.flags.reinforcement_state_4 == 255, "Capturing fortress disables matching generator")

func _test_final_route() -> void:
	var trap = _fixture(36)
	trap.world_node = 36
	trap.route_positions.alm = 36
	Scenario.on_travel(trap)
	_check(trap.world_armies["36"].has(73), "First dragon wave is group73, not same-index Magnum army")
	_check(not Scenario.can_travel(trap, 36, 35) and not Scenario.can_travel(trap, 36, 37), "Dragon trap blocks both exits")
	trap.stage_id = 62
	trap.route = "celica"
	trap.party = ["celica"]
	trap.apply_hub_flag(73)
	Scenario.on_battle_start(trap)
	_check(trap.route == "alm" and trap.mode == "world" and trap.units.is_empty(), "First Celica altar encounter switches to Alm")
	_check(trap.flags.dragon_valley_released and Scenario.can_travel(trap, 36, 37), "Celica altar progression releases valley trap")
	_check(not trap.flags.get("campaign_complete", false), "Celica capture does not complete the game")
	var merge = _fixture(62)
	merge.parties = {"alm": ["alm", "gray"], "celica": ["celica", "mae"]}
	merge.roster.gray = _unit(merge, "gray")
	merge.roster.mae = _unit(merge, "mae")
	merge.roster.alm.level = 17
	merge.roster.celica.hp = 11
	merge.apply_hub_flag(76)
	merge.apply_hub_flag(82)
	Scenario.on_battle_start(merge)
	_check(merge.units.filter(func(unit): return unit.side == "player").size() == 4, "Both full source parties deploy")
	_check(int(_source(merge, 1).level) == 17, "Final merge preserves growth")
	_check(int(_source(merge, 2).hp) == 11, "Celica captive HP snapshot restored")
	var celica_position: Array = merge.stages[62].player_positions_by_party[0][0]
	var alm_position: Array = merge.stages[62].player_positions_by_party[1][0]
	_check(_source(merge, 2).position == celica_position and _source(merge, 1).position == alm_position, "Final source deployment assigns Celica first, Alm second")
	_check(merge.parties.alm == ["alm", "gray"] and merge.parties.celica == ["celica", "mae"], "Final deployment never overwrites route rosters")
	_check(not merge.party.has("celica"), "Temporary battle merge does not corrupt active camp party")
