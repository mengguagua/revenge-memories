extends SceneTree
## Headless smoke flow through actual controller methods, not a parallel game.
## Every save is redirected before entering the first dialogue.
const GameState = preload("res://core/game_state.gd")
const SAVE := "res://reports/test-save.json"
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

func _run() -> void:
	DirAccess.make_dir_recursive_absolute("res://reports")
	var packed = load("res://scenes/main.tscn") as PackedScene
	if packed == null:
		_check(false, "Main scene loads")
		_finish()
		return
	scene = packed.instantiate()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	_check(scene.view == "title" and not scene.title_menu, "Original title is the first state")
	scene._accept()
	_check(scene.title_menu and scene.view == "title", "First confirm exposes title options")
	scene._accept()
	_check(scene.view == "chapter" and scene.game.party == ["alm"], "New game enters chapter card")
	scene._accept()
	_check(scene.view == "dialogue" and scene.dialogue_key == "training", "Chapter enters original training dialogue")
	_finish_dialogue()
	_check(scene.view == "village" and scene.game.mode == "village", "Training ends in explorable Ram village")
	scene._open_system_menu()
	_check(scene.game.party == ["alm"] and scene._npc_present("lukas"), "Before recruitment Lukas remains in the village and party contains only Alm")
	scene._cancel()
	for visit in [["lukas", "lukas_report"], ["mycen", "mycen_refusal"], ["lukas", "alm_volunteers"],
		["gray", "gray_joins"], ["tobin", "tobin_joins"], ["kliff", "kliff_joins"]]:
		if not _visit_npc(str(visit[0]), str(visit[1])):
			await _cleanup()
			return
	_check(scene.game.party == ["alm", "lukas", "gray", "tobin", "kliff"], "Actual village dialogue recruits the five-member party")
	_check(scene.game.flags.get("joined_deliverance", false), "Actual conversation sets departure flag")
	scene._open_system_menu()
	var depart_index: int = scene.menu_actions.find("depart")
	_check(depart_index >= 0, "Departure becomes available after joining")
	if depart_index < 0:
		await _cleanup()
		return
	scene.menu_selected = depart_index
	scene._accept()
	_check(scene.view == "world", "Departure reaches original world-map bridge")
	scene._direction(Vector2i.RIGHT)
	scene._accept()
	_check(scene.view == "battle" and scene.game.units.size() == 10, "World confirmation loads complete first battle")
	if scene.view != "battle":
		await _cleanup()
		return
	_check(scene.game.phase == "player" and scene.game.turn == 1, "First battle opens on player turn1")
	_test_busy_lock()
	_test_move_cancel()
	# Exercise the real M-key path, including public audio properties.
	var key := InputEventKey.new()
	key.physical_keycode = KEY_M
	key.pressed = true
	scene._input(key)
	await create_timer(0.05).timeout
	_check(scene.audio.music_enabled, "M key enables music through the public audio contract")
	scene._input(key)
	_check(not scene.audio.music_enabled, "M key toggles music off again")
	var cycles := 0
	while scene.game.battle_outcome.is_empty() and cycles < 40:
		_check(not scene.busy and not scene.batch_running, "Controller unlocks before next automatic batch")
		await scene._auto_player(false)
		cycles += 1
		_check(not scene.busy and not scene.batch_running, "Automatic player/enemy batch returns without a dangling lock")
		if scene.game.battle_outcome.is_empty():
			_check(scene.game.phase == "player" and scene.view == "battle", "Enemy batch returns exactly once to player phase")
	_check(scene.game.battle_outcome in ["victory", "defeat"], "Original first battle reaches a terminal result within40 turns")
	_check(scene.view == scene.game.battle_outcome and scene.game.mode == scene.view, "Result screen and saved mode agree")
	if scene.game.battle_outcome == "victory":
		_check(scene.game.living("enemy").is_empty() and scene.game.find_unit("alm").hp > 0, "Victory requires all enemies gone and Alm alive")
		_check(scene.game.flags.get("first_battle_complete", false), "Victory records first-battle completion")
	elif scene.game.battle_outcome == "defeat":
		_check(scene.game.find_unit("alm").hp == 0, "Failure requires defeated Alm")
	var terminal = JSON.stringify({"units": scene.game.units, "phase": scene.game.phase, "turn": scene.game.turn,
		"rng": scene.game.rng_state, "view": scene.view})
	await scene._enemy_phase()
	await scene._auto_player(false)
	_check(terminal == JSON.stringify({"units": scene.game.units, "phase": scene.game.phase, "turn": scene.game.turn,
		"rng": scene.game.rng_state, "view": scene.view}), "Terminal result cannot run another phase or unit action")
	print("FE2 flow outcome: %s; %d batches; turn%d; player survivors%d" % [scene.game.battle_outcome, cycles,
		scene.game.turn, scene.game.living("player").size()])
	# A separate controlled exchange exercises the reward screen and losing path,
	# which need not occur during the successful all-recruited autoplay above.
	scene._accept()
	_check(scene.menu_context == "result", "Terminal confirm exposes retry/title options")
	scene.menu_selected = scene.menu_actions.find("retry")
	scene._accept()
	_check(scene.view == "battle" and scene.game.turn == 1 and scene.game.living("enemy").size() == 5,
		"Retry starts a fresh first battle without carrying dead enemy state")
	var alm = scene.game.find_unit("alm")
	var enemy = scene.game.find_unit("brigand_1")
	alm.exp = 90
	alm.skill = 255
	enemy.position = [int(alm.position[0]) + 1, int(alm.position[1])]
	enemy.hp = 1
	await scene._play_combat("alm", "brigand_1")
	_check(scene.view == "reward" and not scene.busy and alm.level == 2 and alm.exp == 5,
		"A level-up exchange displays an unlocked reward screen")
	scene._accept()
	_check(scene.view == "battle" and scene.game.phase == "player", "Reward confirmation returns to the same unfinished player phase")
	enemy = scene.game.find_unit("brigand_2")
	enemy.position = [int(alm.position[0]) + 1, int(alm.position[1])]
	enemy.skill = 255
	enemy.strength = 60
	alm.hp = 1
	scene.game.phase = "enemy"
	await scene._play_combat("brigand_2", "alm")
	_check(scene.view == "defeat" and scene.game.mode == "defeat" and not scene.busy,
		"Lethal enemy exchange reaches the actual defeat screen")
	await _cleanup()

func _finish_dialogue() -> void:
	var clicks := 0
	while scene.view == "dialogue" and clicks < 300:
		scene._accept()
		clicks += 1
	_check(scene.view == "village" and clicks < 300, "Dialogue fully reveals and advances without a dead end")

func _visit_npc(id: String, expected: String) -> bool:
	var position := Vector2i.ZERO
	var found := false
	for npc in scene.game.opening.village.npcs:
		if str(npc.id) == id:
			position = Vector2i(npc.position[0], npc.position[1])
			found = true
			break
	_check(found, "Original NPC is present: " + id)
	if not found:
		return false
	var path: Array = _path_to_neighbor(position)
	_check(not path.is_empty(), "NPC can be reached using village movement: " + id)
	if path.is_empty():
		return false
	for i in range(1, path.size()):
		scene._direction(path[i] - path[i-1])
		_check(scene.game.village_position == path[i], "Village path step is accepted for " + id)
	scene.game.village_facing = position - scene.game.village_position
	scene._accept()
	_check(scene.view == "dialogue" and scene.dialogue_key == expected, "NPC interaction follows story stage: " + expected)
	if scene.view != "dialogue":
		return false
	_finish_dialogue()
	return true

func _path_to_neighbor(target: Vector2i) -> Array:
	var start: Vector2i = scene.game.village_position
	var queue: Array[Vector2i] = [start]
	var previous: Dictionary = {start: start}
	while not queue.is_empty():
		var cell: Vector2i = queue.pop_front()
		if absi(cell.x - target.x) + absi(cell.y - target.y) == 1:
			var path: Array[Vector2i] = [cell]
			while cell != start:
				cell = previous[cell]
				path.push_front(cell)
			return path
		for direction in [Vector2i.UP, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.DOWN]:
			var next: Vector2i = cell + direction
			if not previous.has(next) and scene._village_passable(next):
				previous[next] = cell
				queue.append(next)
	return []

func _test_busy_lock() -> void:
	var cursor: Vector2i = scene.game.cursor
	var selected: String = scene.game.selected_id
	scene.busy = true
	scene._accept()
	scene._cancel()
	scene._direction(Vector2i.RIGHT)
	scene._mouse_accept(Vector2(100, 100))
	scene._open_system_menu()
	_check(scene.game.cursor == cursor and scene.game.selected_id == selected and scene.menu_items.is_empty(), "Busy lock blocks all mutation-capable input paths")
	scene.busy = false

func _test_move_cancel() -> void:
	var origin = GameState.pos(scene.game.find_unit("alm"))
	var enemy = scene.game.find_unit("brigand_1")
	var enemy_origin: Array = enemy.position.duplicate()
	enemy.position = [7, 6]
	scene.game.cursor = origin
	scene._accept()
	_check(scene.ui_mode == "move", "Confirming a fresh ally opens movement selection")
	scene.game.cursor = Vector2i(7, 5)
	scene._accept()
	_check(scene.ui_mode == "action" and scene.menu_context == "unit_action", "Completed movement opens action menu")
	scene._show_status()
	_check(scene.ui_mode == "action" and GameState.pos(scene.game.find_unit("alm")) == Vector2i(7, 5),
		"Status hotkey cannot escape a pending move's action menu")
	scene.menu_selected = scene.menu_actions.find("attack")
	scene._accept()
	_check(scene.ui_mode == "target", "Attack action enters target selection")
	scene._show_status()
	_check(scene.ui_mode == "target" and GameState.pos(scene.game.find_unit("alm")) == Vector2i(7, 5),
		"Status hotkey cannot bypass target selection and commit a free move")
	scene._cancel()
	scene._cancel()
	enemy.position = enemy_origin
	_check(GameState.pos(scene.game.find_unit("alm")) == origin and scene.game.selected_id.is_empty() and not scene.game.find_unit("alm").acted,
		"Canceling the action menu returns to the pre-move square without spending an action")
	var loaded = GameState.new()
	loaded.save_path = SAVE
	_check(loaded.load_game() and GameState.pos(loaded.find_unit("alm")) == origin, "Autosave remains at last confirmed deployment after canceled preview")

func _cleanup() -> void:
	if is_instance_valid(scene):
		scene.audio.stop_all()
		scene.queue_free()
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	# Allow the Dummy audio driver to release queued playback references.
	await create_timer(0.15).timeout
	_finish()

func _finish() -> void:
	print("FE2 flow: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
