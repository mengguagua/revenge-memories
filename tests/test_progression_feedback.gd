extends SceneTree
## Progression regression: real exchange settlement, reward controller, and save.
## All saves are isolated; no player save or visible window is touched.
const GameState = preload("res://core/game_state.gd")
const SAVE := "res://reports/test-progression-save.json"
var checks := 0
var failures := 0
var scene

func _initialize() -> void:
	call_deferred("_run")

func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _fresh():
	var game = GameState.new()
	game.save_path = SAVE
	game.new_game()
	game.party = ["alm", "lukas", "gray", "tobin", "kliff"]
	game.start_battle()
	return game

func _run() -> void:
	DirAccess.make_dir_recursive_absolute("res://reports")
	_test_damage_and_counter_experience()
	_test_growth_and_save()
	await _test_controller_feedback()
	if is_instance_valid(scene):
		scene.audio.stop_all()
		scene.queue_free()
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	await create_timer(0.15).timeout
	print("FE2 progression feedback: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)

func _test_damage_and_counter_experience() -> void:
	var game = _fresh()
	var alm = game.find_unit("alm")
	var enemy = game.find_unit("brigand_1")
	alm.exp = 12
	enemy.hp = 18
	var exchange = {"attacker": "alm", "defender": "brigand_1", "initial_attacker_hp": 28,
		"initial_defender_hp": 26, "events": [{"attacker": "alm", "defender": "brigand_1", "hit": true,
		"critical": false, "damage": 8, "hp_before": 26, "hp_after": 18}]}
	var result = game.finish_exchange(exchange)
	_check(result.gain == 3 and alm.exp == 15 and not result.leveled,
		"A nonlethal eight-HP hit awards three EXP without leveling")
	_check(int(result.get("exp_before", -1)) == 12 and int(result.get("exp_after", -1)) == 15,
		"Reward exposes the previous and final experience for visible feedback")
	_check(int(result.get("level_before", -1)) == 1 and int(result.get("level_after", -1)) == 1,
		"A normal reward exposes unchanged level rather than implying a level-up")
	game = _fresh()
	alm = game.find_unit("alm")
	enemy = game.find_unit("brigand_1")
	enemy.hp = 18
	exchange = {"attacker": "brigand_1", "defender": "alm", "initial_attacker_hp": 26,
		"initial_defender_hp": 28, "events": [{"attacker": "alm", "defender": "brigand_1", "hit": true,
		"critical": false, "damage": 8, "hp_before": 26, "hp_after": 18}]}
	result = game.finish_exchange(exchange)
	_check(result.unit == "alm" and result.gain == 3 and alm.exp == 3,
		"A damaging enemy-phase counter grants the surviving player EXP")
	game = _fresh()
	alm = game.find_unit("alm")
	alm.level = 20
	alm.exp = 75
	result = game.finish_exchange({"attacker": "alm", "defender": "brigand_1",
		"initial_attacker_hp": 28, "initial_defender_hp": 26, "events": [{"attacker": "alm",
		"defender": "brigand_1", "hit": false, "critical": false, "damage": 0, "hp_before": 26, "hp_after": 26}]})
	_check(result.gain == 0 and alm.level == 20 and alm.exp == 75 and not result.leveled,
		"The original level cap cannot add experience or trigger a false level-up")

func _test_growth_and_save() -> void:
	var game = _fresh()
	var alm = game.find_unit("alm")
	var enemy = game.find_unit("brigand_1")
	alm.exp = 90
	alm.hp = 18
	alm.growths = {"hp": 100, "defence": 100, "luck": 100, "speed": 100, "skill": 100, "strength": 100}
	var before = alm.duplicate(true)
	enemy.hp = 0
	var result = game.finish_exchange({"attacker": "alm", "defender": "brigand_1",
		"initial_attacker_hp": 18, "initial_defender_hp": 1, "events": [{"attacker": "alm", "defender": "brigand_1",
		"hit": true, "critical": false, "damage": 1, "hp_before": 1, "hp_after": 0}]})
	_check(result.gain == 15 and result.leveled and alm.level == 2 and alm.exp == 5,
		"Kill EXP crosses 100, increases level once and retains five EXP")
	_check(int(result.get("exp_before", -1)) == 90 and int(result.get("exp_after", -1)) == 5
		and int(result.get("level_before", -1)) == 1 and int(result.get("level_after", -1)) == 2,
		"Level-up reward preserves both ends of the experience wrap and level change")
	for stat in ["strength", "skill", "speed", "luck", "defence"]:
		_check(int(alm[stat]) == int(before[stat]) + 1 and int(result.growths[stat]) == 1,
			"Guaranteed source growth is applied and reported for " + stat)
	_check(alm.max_hp == 29 and alm.hp == 19 and result.growths.hp == 1,
		"HP growth adds one maximum and current HP without healing unrelated damage")
	_check(game.save_game(), "Progression can be written to the isolated native save")
	var loaded = GameState.new()
	loaded.save_path = SAVE
	_check(loaded.load_game(), "Progression save reload succeeds")
	var restored = loaded.find_unit("alm")
	for stat in ["level", "exp", "hp", "max_hp", "strength", "skill", "speed", "luck", "defence"]:
		_check(int(restored.get(stat, -1)) == int(alm[stat]),
			"Reload preserves progressed " + stat)

func _reset_controller() -> void:
	scene.game = _fresh()
	scene.view = "battle"
	scene.ui_mode = "inspect"
	scene.busy = false
	scene.batch_running = false
	scene._clear_menu()
	var alm = scene.game.find_unit("alm")
	var enemy = scene.game.find_unit("brigand_1")
	# Plain original terrain and guaranteed hit/zero critical provide a real,
	# deterministic nonlethal exchange without bypassing controller settlement.
	alm.position = [1, 3]
	alm.skill = 40
	alm.luck = -40
	alm.speed = 2
	enemy.position = [1, 4]
	enemy.speed = 0

func _test_controller_feedback() -> void:
	var packed = load("res://scenes/main.tscn") as PackedScene
	_check(packed != null, "The actual native controller scene loads")
	if packed == null:
		return
	scene = packed.instantiate()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	scene.audio.stop_all()
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	await process_frame
	_reset_controller()
	var alm = scene.game.find_unit("alm")
	alm.exp = 12
	await scene._play_combat("alm", "brigand_1")
	_check(scene.view == "reward" and not scene.busy and not scene.reward.leveled,
		"Ordinary damage EXP is shown as an unlocked experience reward")
	_check(scene.reward.gain == 5 and alm.exp == 17 and alm.level == 1,
		"Actual native two-strike exchange settles five EXP rather than a decorative counter")
	scene._accept()
	_check(scene.view == "battle" and scene.game.phase == "player" and scene.game.turn == 1,
		"Confirming ordinary EXP returns to the same unfinished player phase")
	var restored = GameState.new()
	restored.save_path = SAVE
	_check(restored.load_game() and int(restored.find_unit("alm").exp) == 17,
		"Confirming ordinary EXP saves that experience during the player phase")
	_reset_controller()
	alm = scene.game.find_unit("alm")
	alm.exp = 4
	scene.game.find_unit("brigand_1").hp = 1
	await scene._play_combat("alm", "brigand_1")
	_check(scene.view == "reward" and scene.reward.gain == 15 and not scene.reward.leveled and alm.exp == 19,
		"A non-leveling kill still displays its fifteen EXP reward")
	scene._accept()
	_check(scene.view == "battle" and scene.game.battle_outcome == "",
		"Normal kill feedback cannot incorrectly end a battle with surviving enemies")
	_reset_controller()
	scene.game.phase = "enemy"
	await scene._play_combat("brigand_1", "alm")
	_check(scene.view == "reward" and scene.reward.unit == "alm" and scene.reward.gain == 5,
		"A real enemy-initiated exchange displays the player's counterattack experience")
	scene._accept()
	_check(scene.view == "battle" and scene.game.phase == "enemy" and scene.game.turn == 1,
		"Counterattack reward confirmation preserves the current enemy phase")
	_reset_controller()
	alm = scene.game.find_unit("alm")
	alm.exp = 90
	alm.growths = {"hp": 100, "defence": 100, "luck": 100, "speed": 100, "skill": 100, "strength": 100}
	for unit in scene.game.living("enemy"):
		if str(unit.id) != "brigand_1":
			unit.hp = 0
	scene.game.find_unit("brigand_1").hp = 1
	await scene._play_combat("alm", "brigand_1")
	_check(scene.game.battle_outcome == "victory" and alm.level == 2 and alm.exp == 5,
		"Final kill still applies level and remainder before any result screen")
	_check(scene.view == "reward" and scene.reward.leveled and not scene.busy,
		"Final-kill level-up is visible before victory can replace it")
	var pending_save = FileAccess.get_file_as_string(SAVE)
	var pending = GameState.new()
	pending.save_path = SAVE
	_check(pending.load_game() and pending.battle_outcome == "victory"
		and int(pending.find_unit("alm").level) == 2 and int(pending.find_unit("alm").exp) == 5,
		"Final-kill progress is already saved while its reward is still onscreen")
	_check(pending.mode == "battle",
		"Pending reward fixture reproduces a settled result saved before the result screen")
	scene.batch_running = true
	scene.busy = true
	scene.reward_dismissed = false
	scene._accept()
	_check(scene.reward_dismissed and scene.view == "reward" and scene.busy and scene.batch_running,
		"Confirmation can dismiss a batch reward without escaping or unlocking the batch")
	scene.batch_running = false
	scene.busy = false
	scene._accept()
	_check(scene.view == "victory" and scene.game.mode == "victory" and scene.game.flags.get("first_battle_complete", false),
		"Confirming final-kill progression reaches and saves the actual victory")
	var loaded = GameState.new()
	loaded.save_path = SAVE
	_check(loaded.load_game() and loaded.mode == "victory" and int(loaded.find_unit("alm").level) == 2
		and int(loaded.find_unit("alm").exp) == 15,
		"Terminal autosave retains the final kill and the original ten-EXP survival reward")
	# Simulate closing the application during the final reward instead of after
	# its confirmation. Continue must reconcile the saved battle/result states.
	var file = FileAccess.open(SAVE, FileAccess.WRITE)
	file.store_string(pending_save)
	file.close()
	scene._show_title()
	scene.game = GameState.new()
	scene.game.save_path = SAVE
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	_check(scene.view == "victory" and scene.game.mode == "victory"
		and int(scene.game.find_unit("alm").level) == 2 and int(scene.game.find_unit("alm").exp) == 15,
		"Title continue settles the original survival reward once after the pending final kill")
	_check(scene.game.flags.get("first_battle_complete", false),
		"Continuing a pending final reward records first-battle completion")
	loaded = GameState.new()
	loaded.save_path = SAVE
	_check(loaded.load_game() and loaded.mode == "victory" and loaded.flags.get("first_battle_complete", false),
		"Continue reconciles and persists the result screen and completion flag")
