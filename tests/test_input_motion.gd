extends SceneTree
## Exercise native key events and controller stepping with OS-style echoes.
## Only the village map fixture changes; movement/input use the real controller.
const STEP := 16.0 / 60.0988
const DELTA := 1.0 / 120.0
var scene
var checks := 0
var failures := 0

func _initialize() -> void:
	call_deferred("_run")

func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _key(code: Key, pressed: bool, echo: bool = false) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = pressed
	event.echo = echo
	scene._input(event)

func _reset(cell: Vector2i = Vector2i(12, 7)) -> void:
	scene.view = "village"
	scene.ui_mode = "inspect"
	scene.busy = false
	scene.batch_running = false
	scene.instant_mode = false
	scene.held_direction = Vector2i.ZERO
	scene.repeat_timer = 0.0
	scene.menu_items.clear()
	scene.menu_actions.clear()
	scene.game.village_position = cell
	scene.game.village_facing = Vector2i.DOWN
	scene._sync_village_position()

func _advance(duration: float) -> void:
	var time := 0.0
	while time < duration - 0.00001:
		var delta := minf(DELTA, duration - time)
		scene._process(delta)
		time += delta

func _run() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	scene.game.save_path = "res://reports/test-input-save.json"
	root.add_child(scene)
	await process_frame
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.audio.stop_all()
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	# Plain passable interior avoids NPC/house collisions obscuring timing tests.
	var tiles: Array = []
	tiles.resize(24 * 15)
	tiles.fill(0)
	scene.game.opening.village.tiles = tiles
	scene.game.opening.village.objects = []
	scene.game.opening.village.npcs = []
	for pair in [[KEY_UP, Vector2i.UP], [KEY_DOWN, Vector2i.DOWN],
		[KEY_LEFT, Vector2i.LEFT], [KEY_RIGHT, Vector2i.RIGHT]]:
		_test_held_with_echo(pair[0], pair[1])
	_test_echo_does_not_restart_input()
	_test_turn_after_current_cell()
	_test_release_finishes_cell()
	_test_blocked_and_restart()
	_test_battle_cursor_echo()
	_check(not scene._village_side_flip(Vector2i.RIGHT),
		"The source right-facing village sprite remains unmirrored while walking right")
	_check(scene._village_side_flip(Vector2i.LEFT),
		"The source right-facing village sprite mirrors while walking left")
	_check(not scene._village_side_flip(Vector2i.UP)
		and not scene._village_side_flip(Vector2i.DOWN),
		"Front/back village poses retain their source orientation")
	scene.audio.stop_all()
	scene.queue_free()
	await create_timer(0.30).timeout
	print("FE2 native input/motion: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)

func _test_held_with_echo(code: Key, direction: Vector2i) -> void:
	_reset()
	var start: Vector2 = scene.village_render_position
	_key(code, true)
	var time := 0.0
	var next_echo := 0.4
	var longest_pause := 0.0
	var pause := 0.0
	var previous: Vector2 = start
	while time < 1.2 - 0.00001:
		if time >= next_echo:
			_key(code, true, true)
			next_echo += 0.04
		scene._process(DELTA)
		time += DELTA
		var current: Vector2 = scene.village_render_position
		if current.distance_to(previous) < 0.001:
			pause += DELTA
		else:
			pause = 0.0
		longest_pause = maxf(longest_pause, pause)
		previous = current
	var travel: float = (scene.village_render_position - start).dot(Vector2(direction))
	_check(absf(travel - 1.2 * 60.0988) < 2.0,
		"Held %s with 25 Hz system echoes keeps original walking speed" % direction)
	_check(longest_pause <= DELTA * 2.01,
		"Held %s has no multi-frame stalls between cells" % direction)
	_check(scene.game.village_facing == direction,
		"Held %s keeps its movement direction" % direction)
	_key(code, false)
	_advance(STEP + DELTA)
	_check(scene.held_direction == Vector2i.ZERO and scene.village_motion_time == 0.0,
		"Releasing %s stops after finishing the active cell" % direction)
	_check(scene.village_render_position == Vector2(scene.game.village_position) * 16,
		"Releasing %s leaves an exact tile-aligned position" % direction)

func _test_echo_does_not_restart_input() -> void:
	_reset()
	_key(KEY_RIGHT, true)
	_advance(0.10)
	var timer: float = scene.repeat_timer
	var position: Vector2i = scene.game.village_position
	_key(KEY_RIGHT, true, true)
	_check(scene.repeat_timer == timer and scene.game.village_position == position,
		"OS echo does not reset repeat delay or enqueue another cell")
	_key(KEY_DOWN, true)
	_key(KEY_RIGHT, true, true)
	_check(scene.held_direction == Vector2i.DOWN,
		"A delayed echo from the previous key cannot undo a direction change")
	_key(KEY_RIGHT, false)
	_check(scene.held_direction == Vector2i.DOWN,
		"Releasing the previous key cannot release the current direction")
	_key(KEY_DOWN, false)

func _test_turn_after_current_cell() -> void:
	_reset()
	_key(KEY_RIGHT, true)
	_advance(0.10)
	_key(KEY_DOWN, true)
	_check(scene.game.village_facing == Vector2i.RIGHT,
		"Direction changes preserve facing until the active cell finishes")
	_advance(STEP - 0.10 + DELTA)
	_check(scene.game.village_position == Vector2i(13, 8)
		and scene.game.village_facing == Vector2i.DOWN,
		"Held new direction starts immediately at the next cell")
	_check(absf(scene.village_render_position.x - 13 * 16) < 0.001,
		"A corner never cuts diagonally across the previous cell")
	_key(KEY_DOWN, false)
	_advance(STEP + DELTA)
	_check(scene.village_render_position == Vector2(13, 8) * 16,
		"Direction-change release finishes exactly at the new tile")

func _test_release_finishes_cell() -> void:
	_reset()
	_key(KEY_UP, true)
	_advance(0.06)
	var released_at: Vector2 = scene.village_render_position
	_key(KEY_UP, false)
	_advance(STEP)
	_check(scene.village_render_position == Vector2(12, 6) * 16
		and scene.village_render_position != released_at,
		"A quick tap completes its step after release rather than freezing midway")
	_advance(0.5)
	_check(scene.game.village_position == Vector2i(12, 6),
		"Released input does not start a second step")

func _test_blocked_and_restart() -> void:
	_reset()
	scene.game.opening.village.tiles[6 * 24 + 12] = 110
	_key(KEY_UP, true)
	_advance(0.5)
	_check(scene.game.village_position == Vector2i(12, 7)
		and scene.village_motion_time == 0.0,
		"A held key respects collision and never starts a blocked step")
	_key(KEY_RIGHT, true)
	_advance(0.08)
	_check(scene.game.village_position == Vector2i(13, 7)
		and scene.village_render_position.x > 12 * 16,
		"Changing direction after a wall starts walking without an extra delay")
	_key(KEY_RIGHT, false)
	scene.game.opening.village.tiles[6 * 24 + 12] = 0

func _test_battle_cursor_echo() -> void:
	_reset()
	scene.view = "battle"
	scene.game.cursor = Vector2i(7, 7)
	_key(KEY_UP, true)
	var time := 0.0
	var next_echo := 0.4
	while time < 0.8:
		if time >= next_echo:
			_key(KEY_UP, true, true)
			next_echo += 0.04
		scene._process(DELTA)
		time += DELTA
	_check(scene.game.cursor.y <= 2,
		"Battle cursor repeat continues despite system echo events")
	_key(KEY_UP, false)
	var cell: Vector2i = scene.game.cursor
	_advance(0.3)
	_check(scene.game.cursor == cell,
		"Battle cursor stops repeating on release")
