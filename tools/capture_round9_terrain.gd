extends SceneTree
## One new recovery confirmation only; all graphics are guarded before launch.
var ui
var viewport: SubViewport
func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		quit(1)
		return
	call_deferred("run")
func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)
	event = InputEventKey.new()
	event.physical_keycode = code
	ui._input(event)
func choose(action: String) -> void:
	for _i in range(12):
		if str(ui.menu_actions[ui.menu_selected]) == action:
			key(KEY_Z)
			return
		key(KEY_DOWN)
func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256,240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = "res://reports/round9-visual-isolated-save.json"
	viewport.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.game.new_game()
	ui.game.chapter = 2
	ui.game.route = "celica"
	ui.game.party = []
	ui.game.parties.celica = []
	for id in ["celica","genny","boey","mae","saber"]: ui.game.recruit(id)
	ui.game.world_node = 10
	ui.game.route_positions.celica = 10
	ui.game.start_battle(10)
	ui.view = "battle"
	ui.game.find_unit("celica").position = [28,19]
	ui.game.cursor = Vector2i(20,13)
	ui._focus_battle(ui.game.cursor,true)
	key(KEY_S); choose("terrain_retry")
	ui.phase_time = 0
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var pixels: Image = viewport.get_texture().get_image()
	var path := "res://reports/screenshots/round9-terrain-recovery-confirm.png"
	var error := pixels.save_png(path)
	var report := FileAccess.open("res://reports/round9-terrain-visual.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"path":path,"bytes":FileAccess.get_file_as_bytes(path).size(),"pixels":[256,240],"captures":1,"old_screens_recaptured":0,"menu_context":ui.menu_context,"menu_items":ui.menu_items,"notice":ui.notice,"safe_area_errors":ui.layout_errors,"guarded_before_launch":true,"save_error":error},"  ")+"\n")
	print("ROUND9_VISUAL ",error," safe_area_errors=",ui.layout_errors.size())
	var passed: bool = error == OK and ui.layout_errors.is_empty()
	ui.audio.stop_all(); ui.queue_free()
	await process_frame
	quit(0 if passed else 1)
