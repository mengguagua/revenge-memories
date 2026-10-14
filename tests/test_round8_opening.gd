extends SceneTree
## Newly covered opening exit and help shortcuts, no battle or old UI replay.
const SAVE := "res://reports/test-round8-opening-save.json"
var ui
var before := false
var failures: Array[String] = []
var observations: Array = []
var checks := 0
var inputs := 0

func _initialize() -> void: call_deferred("run")

func key(code: int) -> void:
	inputs += 1
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)
	event = InputEventKey.new()
	event.physical_keycode = code
	ui._input(event)

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func drain() -> void:
	var pages := 0
	while ui.view == "dialogue" and pages < 300:
		key(KEY_Z)
		pages += 1
		await process_frame
	check(ui.view == "village", "Opening conversation releases village input")

func path_to(target: Vector2i) -> Array:
	var start: Vector2i = ui.game.village_position
	var queue: Array = [start]
	var previous := {start: start}
	while not queue.is_empty():
		var cell: Vector2i = queue.pop_front()
		if cell == target:
			var path: Array = []
			while cell != start:
				path.push_front(cell)
				cell = previous[cell]
			return path
		for direction in [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]:
			var next: Vector2i = cell + direction
			if not previous.has(next) and ui._village_passable(next):
				previous[next] = cell
				queue.append(next)
	return []

func walk_to(target: Vector2i) -> void:
	for cell in path_to(target):
		var direction: Vector2i = cell - ui.game.village_position
		key(KEY_RIGHT if direction.x > 0 else KEY_LEFT if direction.x < 0 else KEY_DOWN if direction.y > 0 else KEY_UP)
		var frames := 0
		while ui.village_motion_time > 0 and frames < 60:
			await process_frame
			frames += 1
	check(ui.game.village_position == target, "Actual timed village keys reach intended cell")

func talk(id: String) -> void:
	var actor := Vector2i.ZERO
	for npc in ui.game.opening.village.npcs:
		if npc.id == id: actor = Vector2i(npc.position[0], npc.position[1])
	for direction in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
		var cell: Vector2i = actor + direction
		if ui._village_passable(cell) and (cell == ui.game.village_position or not path_to(cell).is_empty()):
			await walk_to(cell)
			var face: Vector2i = actor - cell
			key(KEY_RIGHT if face.x > 0 else KEY_LEFT if face.x < 0 else KEY_DOWN if face.y > 0 else KEY_UP)
			key(KEY_Z)
			await drain()
			return
	check(false, "Required opening actor remains reachable: " + id)

func opening_status() -> void:
	key(KEY_F1)
	var help: String = ui.notice
	key(KEY_TAB)
	observations.append({"kind":"village_help_shortcut", "help":help, "view":ui.view, "menu":ui.menu_context})
	if before:
		return
	check(ui.menu_context == "roster", "Village Tab implements the displayed status instruction")
	key(KEY_Z)
	check(ui.view == "village_status" and ui.status_id == "alm", "Village shortcut shows actual Alm status")
	key(KEY_X)
	key(KEY_A)
	check(ui.menu_context == "roster", "Village A shares status behavior")
	key(KEY_X)

func try_exit(label: String) -> void:
	if path_to(Vector2i(22,8)).is_empty():
		observations.append({"kind":"opening_boundary_candidate_ruled_out", "phase":label,
			"reason":"Lukas occupies the only corridor before his recruitment; no input path reaches the exit."})
		return
	await walk_to(Vector2i(22,8))
	key(KEY_RIGHT)
	observations.append({"kind":"opening_boundary", "phase":label,"view":ui.view,"menu":ui.menu_context,
		"actions":ui.menu_actions.duplicate(),"notice":ui.notice,"party":ui.game.party.duplicate()})
	if before:
		key(KEY_Z)
		observations.append({"kind":"premature_confirm","view":ui.view,"world":ui.game.world_node,"party":ui.game.party.duplicate()})
		return
	check(ui.view == "village" and not ui.menu_actions.has("depart"), "Village edge preserves the required conversation: " + label)
	check(ui.notice.contains("卢卡斯"), "Blocked exit explains the next real interaction: " + label)

func run() -> void:
	before = OS.get_cmdline_user_args().has("--before")
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	key(KEY_Z)
	key(KEY_Z)
	key(KEY_Z)
	await drain()
	await opening_status()
	await try_exit("before_report")
	await talk("lukas")
	await talk("mycen")
	await talk("lukas")
	await walk_to(Vector2i(22,8))
	key(KEY_RIGHT)
	check(ui.menu_context == "depart" and ui.menu_actions.has("depart"), "Completed participation makes boundary exit actionable")
	key(KEY_Z)
	check(ui.view == "world" and ui.game.party.has("lukas"), "Boundary confirm continues with the required recruit")
	key(KEY_F1)
	key(KEY_TAB)
	observations.append({"kind":"world_help_shortcut", "help":ui.notice,"view":ui.view,"menu":ui.menu_context})
	if not before:
		check(ui.menu_context == "camp_members", "World Tab implements status help without changing location")
		key(KEY_Z)
		check(ui.view == "camp_status" and ui.status_id == "alm", "World shortcut selects actual roster member")
		key(KEY_X)
		check(ui.view == "world" and ui.game.world_node == 49, "Closing status returns to the same world node")
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var file := FileAccess.open("res://reports/round8-opening-" + ("before" if before else "after") + ".json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"observations":observations,"key_events":inputs,
		"battle_replays":0,"screenshots":0,"user_save_accessed":false},"  ")+"\n")
	print("ROUND8 OPENING ", "before" if before else "after", ": ", checks, " checks, ", failures.size(), " failures")
	quit(0 if failures.is_empty() else 1)
