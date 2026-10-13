extends SceneTree
## Original runtime pixels; mandatory prelaunch native no-window/no-focus guard.
const SAVE := "res://reports/test-round4-capture-save.json"
var viewport: SubViewport
var ui
var captures: Array = []
var errors: Array[String] = []

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("Round4 capture requires the preloaded background guard")
		quit(1)
		return
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok: errors.append(label)

func reset(chapter: int) -> void:
	ui.game.new_game()
	for transition in range(1, chapter):
		check(ui.game.next_chapter(transition), "Missing original chapter transition%d" % transition)
	ui.game.save_path = SAVE
	ui.instant_mode = true
	ui.busy = false
	ui.batch_running = false
	ui.held_direction = Vector2i.ZERO
	ui._clear_menu()
	ui.view = "world"
	ui.game.mode = "world"

func snap(label: String, state: Dictionary) -> void:
	ui.notice_time = 0
	ui.hub_controller.notice_left = 0
	ui.phase_time = 0
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var pixels: Image = viewport.get_texture().get_image()
	var path := "res://reports/screenshots/round4-" + label + ".png"
	check(pixels.get_width() == 256 and pixels.get_height() == 240, label + ": viewport dimensions")
	check(pixels.save_png(path) == OK, label + ": PNG write")
	for error in ui.layout_errors: errors.append(label + ": " + str(error))
	captures.append({"id": label, "path": path, "pixels": [pixels.get_width(), pixels.get_height()],
		"bytes": FileAccess.get_file_as_bytes(path).size(), "safe_area_errors": ui.layout_errors.duplicate(), "state": state})

func capture_harbor() -> void:
	reset(2)
	ui.game.world_node = 7
	ui.game.previous_world_node = 57
	ui.game.route_positions.celica = 7
	check(ui.game.travel_to(57), "Actual gate7->harbor57 road")
	check(ui.hub_controller.enter_world(), "Actual harbor command")
	check(ui.game.hub_position == Vector2i(3,12), "Source harbor arrival at3,12")
	await snap("01-harbor-source-entry", {"chapter": ui.game.chapter, "route": ui.game.route,
		"world": ui.game.world_node, "previous_world": ui.game.previous_world_node,
		"room": ui.game.hub_id, "leader": [ui.game.hub_position.x, ui.game.hub_position.y],
		"northern_gate_tile": ui.hub_controller._tile(Vector2i(3,1))})

func capture_mila_resume() -> void:
	reset(3)
	check(ui.game.switch_route(), "Actual Celica route switch")
	ui.game.world_node = 63
	ui.game.previous_world_node = 26
	ui.game.route_positions.celica = 63
	# The old implementation consumed selector4 as a literal x-coordinate.
	ui.game.enter_hub(15, Vector2i(4,0))
	ui.hub_controller._setup(true)
	check(ui.game.hub_position == Vector2i(4,1), "Original legacy Mila normalization")
	check(ui.game.save_game() and ui.game.load_game(), "Legacy Mila production save/reload")
	ui.hub_controller.resume()
	check(ui.game.hub_position == Vector2i(11,19), "Mila legacy resume recovers inside the source gate")
	await snap("02-mila-legacy-resume", {"chapter": ui.game.chapter, "route": ui.game.route,
		"world": ui.game.world_node, "room": ui.game.hub_id,
		"legacy_saved_leader": [4,1], "resumed_leader": [ui.game.hub_position.x,ui.game.hub_position.y],
		"northern_gate_open": ui.hub_controller._ground(Vector2i(11,1))})

func capture_route_arrows() -> void:
	reset(3)
	check(ui.game.world_node == 52 and ui.game.route == "alm", "Original chapter3 Alm castle52 start")
	check(ui.game.travel_to(16) and ui.game.travel_to(17), "Actual Alm52->16->17 travel")
	check(ui.game.switch_route() and ui.game.world_node == 18 and ui.game.travel_to(19), "Actual independent Celica18->19 travel")
	check(ui.game.switch_route() and ui.game.world_node == 17 and ui.game.previous_world_node == 16, "Actual switch restores Alm17 approach16")
	check(ui.game.world_neighbors() == [16], "Occupied road17 displays its original available return arrow16")
	ui.view = "world"
	ui.game.mode = "world"
	await snap("03-world-route-return-arrows", {"chapter": ui.game.chapter, "route": ui.game.route,
		"world": ui.game.world_node, "previous_world": ui.game.previous_world_node,
		"available_roads": ui.game.world_neighbors(), "per_route_previous": ui.game.flags.world_route_previous_nodes.duplicate(),
		"journey": "Alm52->16->17; Celica18->19; return Alm17"})

func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256,240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	viewport.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	await capture_harbor()
	await capture_mila_resume()
	await capture_route_arrows()
	var file := FileAccess.open("res://reports/round4-visual-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"captures": captures, "safe_area_errors": errors,
		"background_guard": true, "guard_loaded_before_engine_main": true,
		"user_save_accessed": false, "visible_or_focused_game_window_started": false,
		"scope": "Three original256x240 runtime SubViewport captures: conditional harbor entrance, old closed Mila gate resume recovery, actual independent-world-route road arrows.",
		"limits": "Original source chapter/road landmarks for earlier battles; runtime screenshots are not a natural full-campaign playthrough."}, "\t") + "\n")
	file.close()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	print("ROUND4 CAPTURE: ", captures.size(), " screens, errors=", errors)
	quit(0 if errors.is_empty() else 1)
