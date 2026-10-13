extends SceneTree
## Independent original-data fixtures and campaign/range regression checks.
const GameState = preload("res://core/game_state.gd")
const Rules = preload("res://core/combat_rules.gd")
const SAVE := "res://reports/test-second-state-save.json"
var checks := 0
var failures := 0

func _initialize() -> void:
	_test_original_second_map()
	_test_bow_boundaries_and_counters()
	_test_campaign_and_retry()
	_test_v1_migration()
	_test_saves()
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	print("FE2 second battle state: %d checks, %d failures" % [checks, failures])
	var report := FileAccess.open("res://reports/second-battle-state-verification.json", FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks": checks, "failures": failures,
		"scope": ["source map/deployment/enemy tables", "bow range/counters/AI", "victory experience",
			"campaign growth/permadeath/healing", "battle retry snapshot", "authentic v1 migration and current suspend"]}, "\t"))
	report.close()
	quit(1 if failures else 0)

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)

func fresh():
	var game = GameState.new()
	game.save_path = SAVE
	game.new_game()
	for id in ["lukas", "gray", "tobin", "kliff"]:
		game.recruit(id)
	game.start_battle()
	return game

func clear_battle(game) -> void:
	for enemy in game.living("enemy"):
		enemy.hp = 0
	game.check_outcome()
	game.complete_battle()

func second():
	var game = fresh()
	clear_battle(game)
	game.start_battle(2)
	return game

func _test_original_second_map() -> void:
	var game = fresh()
	check(not game.can_enter_stage(2) and not game.start_battle(2), "Next map is locked before first victory")
	check(game.available_stage(3) and not game.start_battle(3), "Full campaign map exists but cannot bypass preceding world nodes")
	clear_battle(game)
	check(game.can_enter_stage(2) and game.start_battle(2), "First clear opens the second battle")
	check(game.stage_id == 2 and game.world_node == 2 and game.battle_data.name_zh == "盗贼森林", "Second map identity and world node")
	check(int(game.battle_data.map.width) == 24 and int(game.battle_data.map.height) == 22, "Original 24x22 map size")
	check(game.living("enemy").size() == 7 and game.living("player").size() == 5, "Seven original enemies and recruited survivors deploy")
	var players := [[7,15],[14,14],[16,15],[15,17],[17,13]]
	for i in range(players.size()):
		check(GameState.pos(game.units[i]) == Vector2i(players[i][0],players[i][1]), "Source second-map player deployment slot %d" % i)
	var enemies := [[14,3],[12,3],[16,3],[16,5],[9,9],[17,10],[12,11]]
	for i in range(enemies.size()):
		var enemy: Dictionary = game.living("enemy")[i]
		check(GameState.pos(enemy) == Vector2i(enemies[i][0],enemies[i][1]), "Source enemy deployment slot %d" % i)
		check(int(enemy.raw_ai_flags) == (128 if i in [0,6] else 192), "Source enemy AI flag %d" % i)
	var archer: Dictionary = game.find_unit("archer_1")
	check([int(archer.class_id),int(archer.level),int(archer.hp),int(archer.strength),int(archer.skill),int(archer.speed),int(archer.defence),int(archer.move),int(archer.exp_value)] == [12,1,24,9,1,2,3,4,40], "Original Lv1 archer constructor stats")
	check(game.in_bounds(Vector2i(23,21)) and not game.in_bounds(Vector2i(24,21)), "Large-map bounds")
	check(game.movement_cost(archer, Vector2i(10,12)) < 255, "Archer class terrain movement table is present")
	check(Rules.default_weapon_index(archer) == 1 and Rules.attack_range(archer) == Vector2i(1,3), "Original unarmed archer receives the default bow")

func _test_bow_boundaries_and_counters() -> void:
	var game = second()
	var archer: Dictionary = game.find_unit("archer_1")
	var alm: Dictionary = game.find_unit("alm")
	game.units = [alm, archer]
	archer.position = [10,10]
	for distance in range(0,5):
		alm.position = [10+distance,10]
		check(game.can_attack(archer, alm) == (distance >= 1 and distance <= 3), "Bow boundary distance %d" % distance)
		check(game.can_attack(alm, archer) == (distance == 1), "Melee boundary distance %d" % distance)
	alm.position = [12,10]
	var rng_before: int = game.rng_state
	check(game.plan_combat("alm", "archer_1").is_empty() and game.rng_state == rng_before, "Illegal melee range consumes no RNG or exchange")
	check(game.finish_exchange({}).is_empty(), "Rejected exchange cannot award experience")
	var ranged: Dictionary = game.plan_combat("archer_1", "alm")
	check(ranged.events.size() == 1 and str(ranged.events[0].attacker) == "archer_1", "Faster melee defender cannot counter or follow up at two tiles")
	check(int(ranged.events[0].distance) == 2 and bool(ranged.events[0].ranged), "Ranged events retain original map distance and animation classification")
	for event in ranged.events:
		game.commit_strike(event)
	var exp_before: int = int(alm.exp)
	var reward: Dictionary = game.finish_exchange(ranged)
	check(int(reward.gain) == 1 and int(alm.exp) == exp_before + 1, "Original surviving target receives 1 passive EXP when unable to counter")
	game.battle_outcome = ""
	archer.hp = 24
	alm.hp = int(alm.max_hp)
	archer.speed = 9
	check(Rules.strike_sequence(archer, alm, 3) == ["attacker","attacker"], "Faster archer doubles at maximum normal bow range")
	check(Rules.strike_sequence(alm, archer, 1) == ["attacker","defender","defender"], "Adjacent archers can counter and follow up")
	alm.position = [10,11]
	var adjacent: Dictionary = game.plan_combat("alm", "archer_1")
	check(adjacent.events.any(func(event): return str(event.attacker) == "archer_1"), "Adjacent archer counter appears in planned events")
	archer.hp = 0
	check(game.can_attack(archer,alm) and game.plan_combat("archer_1","alm").is_empty(), "HUD range survives death while planner rejects dead actors")
	archer.hp = 24
	archer.speed = 2
	archer.move = 0
	archer.acted = false # Start a fresh action after the earlier committed exchange.
	alm.position = [12,10]
	var choice: Dictionary = game.ai_action(archer)
	check(choice.destination == Vector2i(10,10) and choice.target == "alm", "Stationary archer AI shoots a legal distant target")
	alm.position = [14,10]
	check(game.ai_action(archer).target == "", "Archer AI rejects a target beyond bow range")

func _test_campaign_and_retry() -> void:
	var game = fresh()
	var alm: Dictionary = game.find_unit("alm")
	var gray: Dictionary = game.find_unit("gray")
	alm.level = 3
	alm.exp = 44
	alm.strength = 12
	alm.max_hp = 30
	alm.hp = 7
	alm.item_id = 2
	gray.hp = 0
	clear_battle(game)
	check(int(alm.exp) == 53 and int(alm.level) == 3, "Map-clear EXP applies current class/level coefficient")
	check(game.stage_cleared(1) and game.flags.first_battle_complete, "Victory completion records first stage")
	check(game.roster.gray.dead and int(game.roster.gray.hp) == 0 and game.party.has("gray"), "Permanent death keeps recruit identity and marks roster")
	var after_clear: int = int(alm.exp)
	check(not game.complete_battle() and int(alm.exp) == after_clear, "Repeated completion cannot duplicate survival reward")
	game.start_battle(2)
	alm = game.find_unit("alm")
	check([int(alm.level),int(alm.exp),int(alm.strength),int(alm.max_hp),int(alm.hp),int(alm.item_id)] == [3,53,12,30,30,2], "Cross-stage levels/EXP/stats/equipment persist and HP fully heals")
	check(game.find_unit("gray").is_empty() and game.living("player").size() == 4, "Dead friend does not redeploy")
	check(GameState.pos(game.find_unit("tobin")) == Vector2i(16,15), "Survivor order fills source deployment slots without a hole")
	alm.exp = 97
	alm.level = 4
	alm.hp = 0
	alm.position = [2,2]
	game.phase = "enemy"
	game.turn = 8
	game.check_outcome()
	check(game.retry_battle(), "Retry restores a captured battle start")
	alm = game.find_unit("alm")
	check([int(alm.level),int(alm.exp),int(alm.hp)] == [3,53,30] and GameState.pos(alm) == Vector2i(7,15), "Retry discards failed battle growth, damage and movement")
	check(game.stage_id == 2 and game.stage_cleared(1) and not game.stage_cleared(2) and game.phase == "player" and game.turn == 1 and game.battle_outcome == "", "Retry restores campaign boundary and phase")
	check(game.roster.gray.dead, "Retry does not resurrect a friend lost in a prior battle")
	alm.exp = 97
	clear_battle(game)
	check(int(alm.exp) == 99 and int(alm.level) == 3, "Victory reward caps at EXP99 without leveling")
	check(game.victory_rewards.size() == 4 and game.stage_cleared(2) and game.flags.second_battle_complete, "Second-stage victory rewards each living party member once")
	check(game.retry_battle() and not game.stage_cleared(2) and int(game.find_unit("alm").exp) == 53, "Retry after victory rolls back that stage's reward and clear status")
	game.new_game()
	check(game.stage_id == 1 and game.world_node == 49 and game.cleared_stages.is_empty() and game.roster.size() == 1 and int(game.battle_data.map.width) == 16, "New game resets expanded campaign and map selection")
	for pair in [["alm",10],["lukas",16],["gray",14],["tobin",20],["kliff",20]]:
		var unit: Dictionary = game.stages[1].characters[pair[0]]
		check(Rules.victory_experience_gain(unit) == int(pair[1]), "Original survival EXP fixture " + str(pair[0]))

func _test_v1_migration() -> void:
	var old = fresh()
	old.find_unit("alm").level = 4
	old.find_unit("alm").exp = 61
	old.find_unit("alm").max_hp = 31
	old.find_unit("alm").hp = 9
	old.find_unit("gray").hp = 0
	for enemy in old.living("enemy"):
		enemy.hp = 0
	old.check_outcome()
	old.mode = "victory"
	old.flags.first_battle_complete = true
	old.save_game()
	var state: Dictionary = GameState.read_json(SAVE)
	state.version = 1
	for key in ["stage_id","world_node","roster","cleared_stages","battle_start_snapshot","victory_rewards",
		"chapter","route","parties","route_positions","previous_world_node","world_armies","convoy",
		"hub_id","hub_position","hub_flags","hub_changes","hub_used","battle_return",
		"battle_settled","story_events","encounter_groups"]:
		state.erase(key)
	var file := FileAccess.open(SAVE,FileAccess.WRITE)
	file.store_string(JSON.stringify(state))
	file.close()
	var loaded = GameState.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.stage_cleared(1) and loaded.world_node == 1, "Legacy completed first battle migrates to the open second node")
	check(int(loaded.find_unit("alm").exp) == 61 and int(loaded.roster.alm.level) == 4 and loaded.roster.gray.dead, "Legacy migration preserves grown stats, original EXP and prior deaths")
	check(not loaded.complete_battle() and int(loaded.find_unit("alm").exp) == 61, "Legacy completed save does not receive a retroactive duplicate reward")
	check(loaded.start_battle(2) and int(loaded.find_unit("alm").hp) == 31 and loaded.find_unit("gray").is_empty(), "Legacy party starts new stage fully healed without resurrecting casualties")
	old = fresh()
	old.find_unit("alm").level = 2
	old.find_unit("alm").exp = 42
	old.find_unit("alm").max_hp = 29
	old.find_unit("alm").hp = 12
	old.find_unit("alm").position = [8,9]
	old.phase = "enemy"
	old.turn = 4
	old.save_game()
	state = GameState.read_json(SAVE)
	state.version = 1
	for key in ["stage_id","world_node","roster","cleared_stages","battle_start_snapshot","victory_rewards",
		"chapter","route","parties","route_positions","previous_world_node","world_armies","convoy",
		"hub_id","hub_position","hub_flags","hub_changes","hub_used","battle_return",
		"battle_settled","story_events","encounter_groups"]:
		state.erase(key)
	file = FileAccess.open(SAVE,FileAccess.WRITE)
	file.store_string(JSON.stringify(state))
	file.close()
	loaded = GameState.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.stage_id == 1 and not loaded.stage_cleared(1) and loaded.phase == "enemy" and loaded.turn == 4, "Legacy mid-battle suspend restores active phase without clearing the map")
	check(int(loaded.find_unit("alm").level) == 2 and int(loaded.find_unit("alm").exp) == 42 and int(loaded.find_unit("alm").hp) == 12 and GameState.pos(loaded.find_unit("alm")) == Vector2i(8,9), "Legacy mid-battle growth and committed position are preserved")
	clear_battle(loaded)
	check(loaded.start_battle(2) and int(loaded.find_unit("alm").level) == 2 and int(loaded.find_unit("alm").exp) == 52 and int(loaded.find_unit("alm").hp) == 29, "Legacy in-progress growth carries into the next map after victory")

func _test_saves() -> void:
	var game = second()
	game.find_unit("alm").exp = 32
	game.find_unit("alm").hp = 23
	game.find_unit("alm").position = [18,9]
	game.phase = "enemy"
	game.turn = 3
	game.mode = "battle"
	check(game.save_game(), "Second-stage suspend save commits atomically")
	var loaded = GameState.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.stage_id == 2 and int(loaded.battle_data.map.width) == 24 and loaded.phase == "enemy" and loaded.turn == 3, "Second-stage suspend restores correct map, phase and turn")
	check(int(loaded.find_unit("alm").hp) == 23 and int(loaded.find_unit("alm").exp) == 32 and GameState.pos(loaded.find_unit("alm")) == Vector2i(18,9), "Suspend preserves committed HP, EXP and position")
	check(loaded.retry_battle() and int(loaded.find_unit("alm").exp) == 10 and GameState.pos(loaded.find_unit("alm")) == Vector2i(7,15), "Saved retry snapshot retains pre-stage reward and deployment")
	clear_battle(loaded)
	loaded.mode = "world"
	loaded.world_node = 2
	loaded.save_game()
	var resume = GameState.new()
	resume.save_path = SAVE
	check(resume.load_game() and resume.mode == "world" and resume.world_node == 2 and resume.stage_cleared(2), "Completed second-stage world position survives restart")
	var good_save: Dictionary = GameState.read_json(SAVE)
	good_save.battle_start_snapshot.units = [{}]
	var bad_snapshot := FileAccess.open(SAVE,FileAccess.WRITE)
	bad_snapshot.store_string(JSON.stringify(good_save))
	bad_snapshot.close()
	check(not resume.load_game() and resume.stage_id == 2 and resume.stage_cleared(2), "Broken retry snapshot is rejected before changing the active campaign")
	var malformed := FileAccess.open(SAVE,FileAccess.WRITE)
	malformed.store_string('{"version":2,"source_revision":"956365ef33c63751e7afd03f05e600d7728549da"}')
	malformed.close()
	var previous: Array = resume.party.duplicate()
	check(not resume.load_game() and resume.party == previous and resume.stage_id == 2, "Malformed supported-version save cannot partly replace live campaign")
