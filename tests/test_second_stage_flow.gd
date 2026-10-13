extends SceneTree
## Exercise the actual campaign controller, including the enlarged map's input.
## The isolated save fixture represents the shipped 0.4 schema. No user save or
## visible Godot window is opened by this headless test.
const GameState = preload("res://core/game_state.gd")
const SAVE := "res://reports/test-second-stage-flow-save.json"
var checks := 0
var failures := 0
var scene
var outcomes: Array = []

func _initialize() -> void:
	call_deferred("_run")

func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _run() -> void:
	DirAccess.make_dir_recursive_absolute("res://reports")
	scene = load("res://scenes/main.tscn").instantiate()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	var node: Dictionary = scene.world.nodes["2"]
	_check(Vector2i(int(node.position[0]), int(node.position[1])) == Vector2i(8, 41)
		and node.neighbors.size() == 3 and int(node.neighbors[0]) == 80
		and int(node.neighbors[1]) == 1 and int(node.neighbors[2]) == 3,
		"Second world node keeps the original coordinate and adjacency source data")
	await _test_natural_campaign()
	await _test_scrolled_input_and_suspend()
	await _test_ranged_preview_and_exchange()
	await _test_v1_title_continue()
	if is_instance_valid(scene):
		scene.audio.stop_all()
		scene.queue_free()
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	await create_timer(0.15).timeout
	var file = FileAccess.open("res://reports/second-stage-flow-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures,
		"natural_battles": outcomes, "save_scope": "isolated v1 and v2 fixtures",
		"rendering": "headless controller/layout checks; actual pixel capture is separate"}, "\t"))
	file.close()
	print("FE2 second-stage flow: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)

func _fresh_party() -> void:
	scene.game.new_game()
	scene.game.party = ["alm", "lukas", "gray", "tobin", "kliff"]
	scene.game.flags.joined_deliverance = true
	scene.game.save_path = SAVE
	scene._clear_menu()
	scene.busy = false
	scene.batch_running = false
	scene.held_direction = Vector2i.ZERO

func _test_natural_campaign() -> void:
	_fresh_party()
	scene._depart()
	scene._direction(Vector2i.RIGHT)
	scene._direction(Vector2i.RIGHT)
	_check(scene.world_selected == 1, "Uncleared first battle gates the second world node")
	scene._accept()
	_check(scene.view == "battle" and scene.game.stage_id == 1,
		"First world confirmation starts stage one through the actual controller")
	await _autoplay_to_result(1)
	if scene.view != "victory":
		return
	var previous: Dictionary = {}
	for unit in scene.game.living("player"):
		previous[str(unit.id)] = unit.duplicate(true)
	_check(scene.game.stage_cleared(1), "First result records the completed stage")
	var saved_exp: int = int(scene.game.find_unit("alm").exp)
	scene._show_result()
	_check(int(scene.game.find_unit("alm").exp) == saved_exp,
		"Re-entering the result does not grant a second completion reward")
	scene._accept()
	_check(scene.menu_actions.has("continue_world"), "Victory menu offers continued world travel")
	_choose_menu("continue_world")
	_check(scene.view == "world" and scene.world_selected == 1
		and scene.game.world_node == 1, "Victory resumes at the cleared forest's original world node")
	scene._show_title()
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	_check(scene.view == "world" and scene.world_selected == 1,
		"Continue restores a world-map suspend after victory without reopening the result")
	if scene.view != "world":
		return
	scene._direction(Vector2i.RIGHT)
	_check(scene.world_selected == 2 and scene.game.world_node == 2,
		"Moving right from Ram Woods reaches the second node")
	scene._accept()
	_check(scene.view == "battle" and scene.game.stage_id == 2
		and int(scene.game.battle_data.map.width) == 24
		and int(scene.game.battle_data.map.height) == 22,
		"World confirmation starts the complete 24 by 22 second battlefield")
	if scene.view != "battle" or scene.game.stage_id != 2:
		return
	_check(scene.game.living("enemy").size() == 7, "The next battle deploys all seven original enemies")
	var archers := 0
	for enemy in scene.game.living("enemy"):
		if str(enemy["class"]) == "archer":
			archers += 1
	_check(archers == 1, "The original enemy archer is present in the second battle")
	for id in previous:
		var unit: Dictionary = scene.game.find_unit(id)
		_check(not unit.is_empty() and int(unit.hp) == int(unit.max_hp),
			"Surviving next-stage deployment restores full HP: " + id)
		for stat in ["level", "exp", "max_hp", "strength", "skill", "speed", "luck", "defence", "item_id"]:
			_check(unit.get(stat) == previous[id].get(stat), "Next stage preserves " + stat + " for " + id)
	_check(scene.game.phase == "player" and scene.game.turn == 1,
		"Second battle opens at player turn one without retaining the old phase")
	await _autoplay_to_result(2)
	if scene.view == "victory":
		_check(scene.game.stage_cleared(2), "Second result records a completed second battle")
		scene._accept()
		_choose_menu("continue_world")
		_check(scene.view == "world" and scene.world_selected == 2,
			"Second victory returns to its own world node")
		scene._direction(Vector2i.RIGHT)
		_check(scene.game.world_node != 2 and scene.game.world_node in scene.game.allowed_world_nodes(), "Full campaign exposes the next original connected location")
		scene._accept()
		_check(scene.view in ["battle", "hub", "hub_dialogue", "hub_choice"] and scene.game.stage_id != 2 or scene.view.begins_with("hub"), "Next location opens its own battle or hub rather than replaying the cleared second battle")

func _autoplay_to_result(stage: int) -> void:
	var cycles := 0
	while scene.game.battle_outcome.is_empty() and cycles < 60:
		await scene._auto_player(false)
		cycles += 1
		_check(not scene.busy and not scene.batch_running, "Stage %d automatic batch releases its input lock" % stage)
		if scene.game.battle_outcome.is_empty():
			_check(scene.view == "battle" and scene.game.phase == "player",
				"Stage %d enemy phase returns once to the player" % stage)
	_check(scene.game.stage_id == stage and scene.view == "victory" and scene.game.battle_outcome == "victory",
		"Unmodified stage %d enemies can be defeated by the actual gameplay loop" % stage)
	outcomes.append({"stage": stage, "result": scene.view, "batches": cycles,
		"turn": scene.game.turn, "survivors": scene.game.living("player").size()})
	print("FE2 stage %d natural flow: %s, %d batches, turn %d" % [stage, scene.view, cycles, scene.game.turn])

func _test_scrolled_input_and_suspend() -> void:
	# A separate healthy party avoids changing the natural campaign above.
	_fresh_party()
	scene.game.start_battle(1)
	for enemy in scene.game.living("enemy"):
		enemy.hp = 0
	scene.game.check_outcome()
	scene.game.complete_battle()
	scene._enter_battle(2)
	_check(scene.view == "battle" and scene.game.stage_id == 2, "Second-stage input fixture deploys")
	scene.phase_time = 0.0
	scene.game.cursor = Vector2i.ZERO
	scene._focus_battle(scene.game.cursor, true)
	_check(scene.battle_camera == Vector2.ZERO, "Camera cannot scroll outside the northwest map boundary")
	for i in range(30):
		scene._direction(Vector2i.RIGHT)
	for i in range(30):
		scene._direction(Vector2i.DOWN)
	_check(scene.game.cursor == Vector2i(23, 21), "Cursor reaches enlarged map edges beyond the old 16 by 15 limits")
	_check(scene.battle_camera == Vector2(128, 112), "Camera reaches the exact southeast map clamp")
	_check(scene._battle_screen_cell(scene._battle_cell_screen(Vector2i(20, 18)) + Vector2(8, 8)) == Vector2i(20, 18),
		"Scrolled tile screen coordinates round-trip without selecting a neighboring unit")
	var before = scene.game.cursor
	scene._mouse_accept(Vector2(-8, -8))
	_check(scene.game.cursor == before and scene.game.selected_id.is_empty(),
		"A click outside the native viewport cannot select an offscreen scrolled cell")
	var alm: Dictionary = scene.game.find_unit("alm")
	alm.position = [20, 18]
	alm.acted = false
	scene._mouse_accept(scene._battle_cell_screen(Vector2i(20, 18)) + Vector2(8, 8))
	_check(scene.game.cursor == Vector2i(20, 18) and scene.game.selected_id == "alm"
		and scene.ui_mode == "move", "Mouse selects the visible ally using the scrolled map coordinate")
	scene._cancel()
	_check(scene.ui_mode == "inspect" and scene.game.selected_id.is_empty(),
		"Canceling the scrolled selection leaves no pending move")
	scene.game.cursor = Vector2i(10, 0)
	scene._focus_battle(scene.game.cursor, true)
	var key := InputEventKey.new()
	key.physical_keycode = KEY_DOWN
	key.pressed = true
	scene._input(key)
	for i in range(40):
		scene._process(0.15)
	key.pressed = false
	scene._input(key)
	_check(scene.game.cursor.y == 21 and scene.held_direction == Vector2i.ZERO,
		"Holding down crosses the old screen edge and key release stops repeating")
	scene.game.cursor = Vector2i(20, 18)
	scene._focus_battle(scene.game.cursor, true)
	scene.game.mode = "battle"
	_check(scene.game.save_game(), "Second battle suspend writes the isolated save")
	scene._show_title()
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	_check(scene.view == "battle" and scene.game.stage_id == 2,
		"Title Continue loads the second-stage map rather than the old first stage")
	var at: Vector2 = scene._battle_cell_screen(GameState.pos(scene.game.find_unit("alm")))
	_check(Rect2(Vector2.ZERO, Vector2(256, 240)).has_point(at),
		"Continue restores a camera that shows the saved player's deployment")
	scene.queue_redraw()
	await process_frame
	await process_frame
	_check(scene.layout_errors.is_empty(), "Scrolled unit information remains within bitmap content-safe areas")

func _test_ranged_preview_and_exchange() -> void:
	var archer: Dictionary = {}
	for enemy in scene.game.living("enemy"):
		if str(enemy["class"]) == "archer":
			archer = enemy
	_check(not archer.is_empty(), "Ranged UI fixture finds the original enemy archer")
	if archer.is_empty():
		return
	var alm: Dictionary = scene.game.find_unit("alm")
	archer.position = [18, 18]
	alm.position = [21, 18]
	scene.game.selected_id = str(archer.id)
	scene.game.cursor = GameState.pos(alm)
	scene.target_ids = ["alm"]
	scene.target_index = 0
	scene.ui_mode = "target"
	scene._focus_battle(scene.game.cursor, true)
	scene.queue_redraw()
	await process_frame
	await process_frame
	var labels: Array = []
	for label in scene.text_checks:
		labels.append(str(label.text))
	_check(labels.has("无法反击") and labels.has("超出攻击范围"),
		"Three-tile bow preview visibly states that the melee defender cannot counter")
	_check(scene.layout_errors.is_empty(),
		"Chinese ranged preview labels and dynamic numbers remain within the bitmap safe area")
	scene.game.selected_id = ""
	scene.ui_mode = "inspect"
	archer.skill = 255
	alm.hp = alm.max_hp
	var hp_before: int = int(alm.hp)
	var exp_before: int = int(alm.exp)
	var archer_hp_before: int = int(archer.hp)
	scene.game.phase = "enemy"
	await scene._play_combat(str(archer.id), "alm")
	_check(int(alm.hp) < hp_before and int(alm.hp) > 0,
		"The actual ranged animation controller settles a nonlethal arrow hit")
	# L0980CC/L0980E4 grants a surviving player one EXP when total dealt
	# damage is zero, including an exchange where the bow prevents a counter.
	_check(int(alm.exp) == exp_before + 1 and int(archer.hp) == archer_hp_before
		and scene.view == "reward" and int(scene.reward.gain) == 1,
		"An out-of-range melee defender deals no counter damage but earns the source one survival EXP")
	scene._accept()
	_check(scene.view == "battle" and not scene.busy and scene.combat_projectile.is_empty(),
		"Arrow exchange returns to the battlefield with no lingering projectile or input lock")

func _test_v1_title_continue() -> void:
	var legacy = GameState.new()
	legacy.new_game()
	legacy.party = ["alm", "lukas", "gray", "tobin", "kliff"]
	legacy.start_battle()
	var alm: Dictionary = legacy.find_unit("alm")
	alm.level = 3
	alm.exp = 27
	alm.max_hp = 31
	alm.hp = 13
	alm.strength = 14
	for enemy in legacy.living("enemy"):
		enemy.hp = 0
	legacy.battle_outcome = "victory"
	legacy.flags.first_battle_complete = true
	# Shipped v1 saves contain neither per-army metadata nor enemy identity tags.
	for key in ["world_army_instances", "world_army_next_id", "world_random_army_instance", "battle_army_instances", "dungeon_army_instances", "inventory_attacking_instance_id"]:
		legacy.flags.erase(key)
	for unit in legacy.units: unit.erase("army_instance")
	for army in legacy.flags.get("world_mobile_armies", []): army.erase("instance_id")
	var v1 := {"version": 1, "source_revision": legacy.battle_data.source_commit,
		"mode": "victory", "flags": legacy.flags, "party": legacy.party,
		"village_position": [22, 8], "units": legacy.units, "phase": "player", "turn": 4,
		"rng_state": 17, "frame_counter": 32, "kills": 5, "battle_outcome": "victory"}
	var file = FileAccess.open(SAVE, FileAccess.WRITE)
	file.store_string(JSON.stringify(v1))
	file.close()
	scene._show_title()
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	_check(scene.view == "victory" and scene.game.stage_id == 1,
		"The shipped version-one first-victory save continues through the title UI")
	_check(scene.game.find_unit("alm").level == 3 and scene.game.find_unit("alm").strength == 14,
		"Legacy Continue retains grown character stats")
	var resumed_exp: int = int(scene.game.find_unit("alm").exp)
	scene._accept()
	_choose_menu("continue_world")
	scene._direction(Vector2i.RIGHT)
	scene._accept()
	_check(scene.view == "battle" and scene.game.stage_id == 2,
		"Legacy first victory can proceed to the second battle without restarting the story")
	alm = scene.game.find_unit("alm")
	_check(alm.level == 3 and alm.strength == 14 and alm.max_hp == 31
		and alm.hp == 31 and alm.exp == resumed_exp,
		"Legacy campaign deployment preserves level/EXP/growth and restores current HP")

func _choose_menu(action: String) -> void:
	var index: int = scene.menu_actions.find(action)
	_check(index >= 0, "Controller menu contains " + action)
	if index >= 0:
		scene.menu_selected = index
		scene._accept()
