extends SceneTree
## Actual GameState integration, not a scenario fixture. Isolated save only.
const GameState = preload("res://core/game_state.gd")
const SaveValidation = preload("res://core/campaign_save_validation.gd")
const Scenario = preload("res://core/scenario_rules.gd")
const WorldArmies = preload("res://core/world_armies.gd")
const SAVE := "res://reports/test-campaign-continuity-save.json"
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)
		push_error(message)

func fresh():
	var game = GameState.new()
	game.save_path = SAVE
	game.new_game()
	return game

func at_battle(stage: int, route: String = "alm", groups: Array = []):
	var game = fresh()
	game.chapter = 4
	game.route = route
	game.party = [route]
	game.parties[route] = [route]
	game.roster[route] = game._initial_character(route)
	game.world_node = stage
	game.route_positions[route] = stage if stage < 49 else 78
	game.world_armies.clear()
	game.start_battle(stage, groups, stage > 48)
	return game

func source_unit(game, id: int) -> Dictionary:
	for unit in game.units:
		if int(unit.get("source_enemy_character_id", unit.get("character_id", 0))) == id:
			return unit
	return {}

func kill(game, unit: Dictionary) -> void:
	game.commit_strike({"attacker": game.leader_id(), "defender": unit.id, "hp_after": 0})

func clear(game) -> void:
	# This test covers settlement/transitions; battle arithmetic has its own suite.
	for unit in game.living("enemy"):
		unit.hp = 0
	game.check_outcome()
	game.complete_battle()

func equivalent(a: Variant, b: Variant) -> bool:
	if typeof(a) in [TYPE_INT, TYPE_FLOAT] and typeof(b) in [TYPE_INT, TYPE_FLOAT]:
		return float(a) == float(b)
	if a is Array and b is Array:
		if a.size() != b.size(): return false
		for i in range(a.size()):
			if not equivalent(a[i], b[i]): return false
		return true
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size(): return false
		for key in a:
			if not b.has(key) or not equivalent(a[key], b[key]): return false
		return true
	return a == b

func _run() -> void:
	_test_world_progress()
	_test_chapters_and_routes()
	_test_quest_callbacks()
	_test_dynamic_deployment()
	_test_army_initiative()
	_test_retry_and_round_trip()
	_test_final_battle()
	_test_save_validation()
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	var file := FileAccess.open("res://reports/campaign-continuity-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures,
		"scope": "native GameState campaign hooks, dynamic deployment, chapter/route transitions, rescue/death persistence, final battle, v3 validation and retry transactions"}, "\t") + "\n")
	print("CAMPAIGN CONTINUITY: %d checks, %d failures" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

func _test_world_progress() -> void:
	var game = fresh()
	for id in ["lukas", "gray", "tobin", "kliff"]: game.recruit(id)
	check(game.travel_to(1) and game.world_node == 1, "Village exit enters first source node")
	check(not game.travel_to(2) and game.world_node == 1, "Unbeaten enemy node blocks forward travel")
	check(game.start_battle(1), "First battle starts from real travel state")
	clear(game)
	check(not game.world_has_battle(1) and game.travel_to(2), "Victory removes current army and permits next road")
	check(game.start_battle(2), "Second battle begins through source road")
	clear(game)
	check(game.travel_to(3) and game.start_battle(3), "Former two-map endpoint continues into Ram valley")
	check(game.stage_id == 3 and not game.living("enemy").is_empty(), "Third battle has source enemies")
	check(game.stage_cleared(1) and game.stage_cleared(2), "Earlier clears survive expanded campaign transition")

func _test_chapters_and_routes() -> void:
	var game = fresh()
	game.recruit("lukas")
	game.roster.alm.exp = 47
	check(game.next_chapter(1) and game.chapter == 2 and game.route == "celica" and game.hub_id == 5, "First source transition starts Celica at monastery")
	check(game.parties.alm == ["alm", "lukas"] and int(game.roster.alm.exp) == 47, "Route switch preserves Alm roster and growth")
	check(bool(game.flags.scenario_alm_frozen) and not game.switch_route(), "Chapter two retains source Alm freeze")
	game.recruit("mae")
	game.world_node = 57
	game.world_armies.clear()
	check(game.travel_to(7) and game.travel_to(52), "Celica reaches castle through source harbor57-gate7-castle52 road")
	game.apply_hub_flag(48)
	check(bool(game.flags.mila_visited), "Hub flags invoke scenario milestone hook")
	check(game.next_chapter(2) and game.chapter == 3 and game.route == "alm" and game.hub_id == 44, "Second source transition restores Alm route")
	check(int(game.route_positions.celica) == 18 and not bool(game.flags.scenario_alm_frozen), "Chapter three preserves Celica on western road and unfreezes both")
	check(game.hub_used.get("9:0", true) == false and game.hub_used.get("9:1", false) == true, "Chapter three updates original harbor road-block feature bits")
	check(not game.flags.get("source_flag_42", false), "Chapter three cannot disable unrelated Jesse recruitment with guessed flag42")
	check(game.switch_route() and game.party == ["celica", "mae"] and game.world_node == 18, "World route switch restores separate Celica roster")
	check(game.switch_route() and game.party == ["alm", "lukas"], "Returning to Alm retains independent party")
	check(game.next_chapter(3) and game.chapter == 4 and int(game.flags.world_gate_bits) == 4, "Sluice transition installs source chapter-four gate state")
	check(game.hub_used.get("15:0", false), "Chapter four applies source Mila sluice opening pattern")
	var armies: Dictionary = game.world_armies.duplicate(true)
	game.route_positions.celica = 48
	check(game.next_chapter(4) and game.chapter == 5 and game.hub_id == 30, "Final underground chapter enters source Rigel room")
	check(equivalent(game.world_armies, armies) and int(game.route_positions.celica) == 48, "Finale cannot regenerate cleared world armies or reset Celica progress")
	check(int(game.flags.scenario_source_chapter_counter) == 4, "Displayed chapter five retains source world chapter four")
	game.route = "celica"
	game.party = game.parties.celica.duplicate()
	game.world_node = 77
	game.route_positions.alm = 36
	game.hub_id = 27
	game.hub_position = Vector2i(7,3)
	check(game.enter_dungeon_battle(22) and game.mode == "world" and game.route == "alm" and game.world_node == 36, "Celica altar capture returns control to Alm's existing valley position")
	check(game.battle_return.get("mode", "") == "world" and game.units.is_empty(), "Capture redirects battle return instead of reopening Celica's altar as Alm")

func _test_quest_callbacks() -> void:
	var game = at_battle(29)
	var npc: Dictionary = game.find_unit("mathilda")
	check(not npc.is_empty() and bool(npc.neutral) and not bool(npc.controllable), "Mathilda rescue NPC is installed by battle-start hook")
	kill(game, npc)
	check(bool(game.roster.mathilda.dead) and bool(game.flags.unrecruitable_mathilda), "NPC death callback blocks later recruitment persistently")
	game.recruit("mathilda")
	check(not game.party.has("mathilda"), "Recruit API cannot revive a lost rescue NPC")
	check(game.retry_battle() and not game.roster.has("mathilda") and int(game.find_unit("mathilda").hp) > 0, "Retry rolls back failed rescue fate and restores NPC")
	game = at_battle(32)
	var captive: Dictionary = source_unit(game, 145)
	kill(game, source_unit(game, 143))
	check(bool(captive.get("rescued", false)) and not bool(captive.get("dead", false)) and int(captive.hp) == 0, "Tatara death frees Delthea without a character death")
	check(not game.flags.get("unrecruitable_delthea", false) and bool(game.flags.delthea_rescued), "Freed Delthea remains recruitable")
	check(game.story_events.any(func(event): return event.get("group", "") == "events" and event.get("key", "") == "12"), "Rescue queues exact translated source dialogue")
	game = at_battle(32)
	kill(game, source_unit(game, 145))
	kill(game, source_unit(game, 143))
	game.recruit("delthea")
	check(bool(game.roster.delthea.dead) and not game.party.has("delthea"), "Killing captive cannot be undone by later controller death")
	game = at_battle(22, "celica")
	kill(game, source_unit(game, 136))
	check(game.flags.get("desert_survivor", "") == "sonya" and game.flags.get("unrecruitable_deen", false), "Deen defeat selects only Sonya's recruitment branch")
	game = fresh()
	game.chapter = 4
	game.world_node = 34
	game.recruit("tatiana")
	game.apply_hub_flag(31)
	game.start_battle(34, [34,35])
	check(game.units.any(func(unit): return bool(unit.get("zeke_npc", false)) and unit.side == "player"), "Tatiana source flag converts Zeke in actual battle")
	check(game.living("enemy").any(func(unit): return int(unit.get("character_id", 0)) == 138), "Jerome remains hostile after Zeke conversion")
	kill(game, source_unit(game, 139))
	check(bool(game.roster.zeke.dead), "Green Zeke death persists as playable identity")
	game = at_battle(42)
	kill(game, source_unit(game, 133))
	check(game.battle_outcome == "victory" and game.living("enemy").is_empty(), "Rudolf death immediately settles surrender condition")
	check(game.units.any(func(unit): return bool(unit.get("retreated", false)) and bool(unit.get("no_experience", false))), "Surrendering units are not awarded as extra kills")

func _test_dynamic_deployment() -> void:
	for fixture in [[76,13], [77,16], [78,20]]:
		var game = at_battle(36, "alm", [fixture[0]])
		check(game.living("enemy").size() == fixture[1], "Dynamic dragon wave %d keeps all %d source units" % fixture)
		var occupied: Dictionary = {}
		for unit in game.living("enemy"): occupied[GameState.pos(unit)] = true
		check(occupied.size() == game.living("enemy").size(), "Dynamic wave %d deployment has no overlapping enemies" % fixture[0])

func _test_army_initiative() -> void:
	var game = fresh()
	game.chapter = 4
	game.flags.world_gate_bits = 4
	game.world_node = 31
	game.world_armies = {"33":[73]}
	game.flags.world_mobile_armies = [{"node":33,"group_id":73,"previous_node":34}]
	check(game.travel_to(32), "Player can enter unoccupied watergate road in chapter four")
	check(game.flags.get("inventory_enemy_initiated", false) and int(game.flags.get("inventory_attacking_group_id", -1)) == 73 and int(game.flags.get("inventory_attacker_previous_node", -1)) == 33, "Arriving enemy preserves original initiator and retreat origin")
	check(int(game.flags.world_mobile_armies[0].previous_node) == 33 and int(game.flags.world_mobile_armies[0].node) == 32, "Mobile army movement records previous node for source retreat")
	game.flags.inventory_defeated_enemy_records = {"78:0":true, "78:1":true, "73:0":true}
	check(Scenario._add_army(game, 36, 78, 79), "Fresh dragon generation enters source origin")
	var survivor_id: String = str(WorldArmies.instances_at(game, 32)[0])
	check(not game.flags.inventory_defeated_enemy_records.has("78:0") and game.flags.inventory_defeated_enemy_records.has(survivor_id + ":0"), "Fresh generation resets orphan historical losses and preserves the living army's migrated losses")
	check(int(game.flags.world_mobile_armies[-1].previous_node) == 79, "Fresh wave retains source shrine origin rather than guessing a neighbor")

func _test_retry_and_round_trip() -> void:
	var game = at_battle(29)
	game.convoy = {"alm": [17,2,51], "celica": [6,58]}
	game.hub_used["spring_18_4"] = 2
	game.hub_changes["1"] = {"0": 48}
	game.battle_start_snapshot = game._capture_battle_start()
	var expected: Dictionary = game.battle_start_snapshot.duplicate(true)
	kill(game, game.find_unit("mathilda"))
	game.convoy.alm.append(3)
	game.hub_used["spring_18_4"] = 3
	game.hub_changes["1"]["0"] = 49
	check(game.save_game(), "Expanded rescue suspend writes isolated atomic save")
	var loaded = GameState.new()
	loaded.save_path = SAVE
	check(loaded.load_game(), "Expanded rescue suspend reloads")
	for key in ["parties", "route_positions", "hub_flags", "convoy", "hub_changes", "hub_used", "story_events", "world_armies"]:
		check(equivalent(loaded.get(key), game.get(key)), "v3 restores " + key)
	check(loaded.retry_battle(), "Loaded retry snapshot remains executable")
	for key in ["parties", "route_positions", "hub_flags", "convoy", "hub_changes", "hub_used", "story_events", "world_armies", "flags"]:
		check(equivalent(loaded.get(key), expected[key]), "Retry restores transaction field " + key)
	game = fresh()
	var promotion: Dictionary = game.promote_unit("alm", 23, true)
	check(bool(promotion.valid) and int(game.roster.alm.class_id) == 21 and bool(game.roster.alm.promoted), "Source story promotion keeps runtime class21 and promotion flag")
	game.start_battle(1)
	game.save_game()
	loaded = GameState.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and int(loaded.roster.alm.class_id) == 21 and bool(loaded.roster.alm.promoted), "Promoted Alm save and retry snapshot preserve source representation")

func _final_fixture():
	var game = fresh()
	game.chapter = 5
	game.parties = {"alm": ["alm", "mycen"], "celica": ["celica", "mae"]}
	game.party = game.parties.alm.duplicate()
	for id in ["mycen", "celica", "mae"]: game.roster[id] = game._initial_character(id)
	game.roster.celica.hp = 7
	game.roster.mae.hp = 11
	game.apply_hub_flag(76)
	game.apply_hub_flag(82)
	game.battle_return = {"mode": "hub", "hub_id": 40, "position": [7,3], "world_node": 78}
	game.start_battle(62, [86], true)
	return game

func _test_final_battle() -> void:
	var game = _final_fixture()
	check(game.living("player").size() == 4 and game.living("enemy").size() == 20, "Final battle merges both parties and all twenty enemies")
	check(int(game.find_unit("celica").hp) == 7 and int(game.find_unit("mae").hp) == 11, "Final deployment restores captive Celica-route HP snapshot")
	check(GameState.pos(game.find_unit("celica")) == Vector2i(game.stages[62].player_positions_by_party[0][0][0], game.stages[62].player_positions_by_party[0][0][1]), "Celica occupies source final party-zero formation")
	check(GameState.pos(game.find_unit("alm")) == Vector2i(game.stages[62].player_positions_by_party[1][0][0], game.stages[62].player_positions_by_party[1][0][1]), "Alm occupies source final party-one formation")
	kill(game, source_unit(game, 167))
	check(game.battle_outcome == "victory" and game.flags.get("campaign_complete", false), "Duma death triggers victory through GameState death hook")
	check(game.complete_battle() and not game.complete_battle(), "Final reward settlement is idempotent")
	check(game.story_events.filter(func(event): return event.kind == "ending").size() == 1, "Final settlement queues ending once")
	check(game.parties.alm == ["alm", "mycen"] and game.parties.celica == ["celica", "mae"], "Final settlement does not merge persistent route lists")
	check(game.roster.has("mae") and int(game.roster.mae.hp) == 11, "Final settlement persists both routes' deployed units")
	game.save_game()
	var loaded = GameState.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.battle_settled and not loaded.complete_battle(), "Final victory save cannot duplicate ending or rewards")
	check(loaded.retry_battle() and not loaded.flags.get("campaign_complete", false) and int(source_unit(loaded,167).hp) == 182, "Final retry restores original Duma and both parties")
	kill(loaded, loaded.find_unit("celica"))
	check(loaded.battle_outcome == "defeat", "Alm-led final deployment still loses if Celica dies")

func _test_save_validation() -> void:
	var game = at_battle(29)
	game.save_game()
	var valid: Dictionary = GameState.read_json(SAVE)
	check(SaveValidation.valid(game, valid), "Complete v3 state satisfies campaign validation")
	var accessories: Dictionary = valid.duplicate(true)
	accessories.convoy = {"alm":[48,49,50,51,52], "celica":[53,54,55,56,57,58]}
	check(SaveValidation.valid(game, accessories), "All original shields and rings survive convoy validation")
	for key in SaveValidation.EXTENDED_FIELDS:
		var missing: Dictionary = valid.duplicate(true)
		missing.erase(key)
		check(not SaveValidation.valid(game, missing), "v3 rejects absent campaign field " + key)
	var invalid := {"chapter": 6, "route": "unknown", "parties": [], "route_positions": {"alm":0,"celica":53},
		"previous_world_node": -1, "world_armies": {"36":[66]}, "convoy": {"alm":[-1],"celica":[]},
		"hub_id":999, "hub_position":[1], "hub_flags":{"1":{"actors":256,"talk":0,"triggers":0}},
		"hub_changes":{"1":{"999999":1}}, "hub_used":[], "battle_return":{"mode":"hub","world_node":78,"hub_id":40},
		"battle_settled":"false", "story_events":[{}], "encounter_groups":[1,1,1]}
	for key in invalid:
		var broken: Dictionary = valid.duplicate(true)
		broken[key] = invalid[key]
		check(not SaveValidation.valid(game, broken), "v3 rejects malformed " + key)
		if valid.battle_start_snapshot.has(key):
			broken = valid.duplicate(true)
			broken.battle_start_snapshot[key] = invalid[key]
			check(not SaveValidation.valid(game, broken), "Retry rejects malformed " + key)
	var legacy: Dictionary = valid.duplicate(true)
	legacy.version = 2
	for key in SaveValidation.EXTENDED_FIELDS: legacy.erase(key)
	for key in SaveValidation.EXTENDED_FIELDS: legacy.battle_start_snapshot.erase(key)
	_legacy_armies(legacy)
	_legacy_armies(legacy.battle_start_snapshot)
	check(SaveValidation.valid(game, legacy), "Authentic v2 and its legacy snapshot require no v3 fields")
	legacy = valid.duplicate(true)
	for key in SaveValidation.EXTENDED_FIELDS: legacy.battle_start_snapshot.erase(key)
	_legacy_armies(legacy.battle_start_snapshot)
	check(SaveValidation.valid(game, legacy), "A v2 retry snapshot remains valid after top-level upgrade to v3")
	for used in [{"leader_facing":[0]}, {"leader_facing":[1,1]}, {"event_vm":[]}, {"event_vm":{"script_id":999,"pc":0,"hub_id":1,"actors":{}}}]:
		var broken: Dictionary = valid.duplicate(true)
		broken.hub_used = used
		check(not SaveValidation.valid(game, broken), "Malformed resumable hub state is rejected before entering UI")

func _legacy_armies(state: Dictionary) -> void:
	# Real v2 saves predate all independent-army metadata, including unit tags.
	for key in ["world_army_instances", "world_army_next_id", "world_random_army_instance", "battle_army_instances", "dungeon_army_instances", "inventory_attacking_instance_id"]:
		state.flags.erase(key)
	for unit in state.get("units", []): unit.erase("army_instance")
	for army in state.flags.get("world_mobile_armies", []): army.erase("instance_id")
