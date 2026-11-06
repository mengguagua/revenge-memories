extends SceneTree
## Background-only phone presentation and actual imported-texture lifetime probe.
const OUT = "res://reports/full-assessment-20261025/performance/"
const TEMP = "/private/tmp/revenge-performance-20261025/"
var phone
var ui
var screen
var checks: Array = []
var errors: Array = []
var measurements: Dictionary = {}
var visual := false

func _initialize():call_deferred("run")
func check(ok: bool, label: String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func frames(count: int):
	for i in range(count):await process_frame
	if visual:await RenderingServer.frame_post_draw
func snap():return screen.get_texture().get_image().get_data().hex_encode().sha256_text()
func sample_draws(force: bool):
	phone.draw_microseconds.clear()
	for i in range(90):
		if force:phone.queue_redraw()
		await process_frame
	if visual:await RenderingServer.frame_post_draw
	var samples = phone.draw_microseconds.duplicate()
	var total = 0
	for value in samples:total += int(value)
	return {"frames":90,"rail_draw_calls":samples.size(),"rail_draw_cpu_usec":total,"mean_draw_usec":float(total)/maxi(1,samples.size())}
func memory():
	return {"render_texture_bytes":int(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)),
		"static_memory_bytes":int(Performance.get_monitor(Performance.MEMORY_STATIC)),"cache_count":ui.textures.size()}
func gather_paths(value, paths: Dictionary):
	if value is String:
		if value.begins_with("res://assets/") and value.ends_with(".png"):paths[value] = true
	elif value is Array:
		for child in value:gather_paths(child,paths)
	elif value is Dictionary:
		for child in value.values():gather_paths(child,paths)
func texture_probe():
	var manifest = ui.PartySprites.Reviewed.metadata()
	var rows: Array = []
	var paths: Dictionary = {}
	gather_paths(manifest,paths);gather_paths(ui.GameState.read_json("res://data/party_visuals.json"),paths)
	for path in paths:
		# File dimensions are read from the imported resource, not guessed from frame metadata.
		if path.ends_with("-battle.png"):rows.append(path)
	rows.sort()
	var chosen: Array = []
	for wanted in ["professions-class-7-ally-battle.png","professions-class-7-enemy-battle.png","hunapu-battle.png","professions-class-5-enemy-battle.png","professions-class-3-ally-battle.png","professions-class-5-ally-battle.png","professions-class-22-enemy-battle.png"]:
		for path in rows:
			if path.ends_with(wanted):chosen.append(path);break
	check(chosen.size() >= 5,"probe uses at least five current runtime battle atlases")
	if chosen.is_empty():return
	var refs: Dictionary = {};var sizes: Dictionary = {};var original_hash = ""
	measurements.memory_before = memory()
	for path in chosen:
		var texture = ui._tex(path)
		check(texture != null,"current atlas loads: " + path)
		refs[path] = weakref(texture);sizes[path] = [texture.get_width(),texture.get_height()]
		if path == chosen[0]:original_hash = texture.get_image().get_data().hex_encode().sha256_text()
		texture = null
	await frames(3)
	measurements.memory_unbounded = memory()
	# Simulate leaving these scenes, then render the currently visible map once.
	ui.texture_cache_clock += 4.0
	ui.queue_redraw();await frames(3)
	var hot = chosen.slice(chosen.size()-2)
	var hot_ids: Array = []
	for path in hot:hot_ids.append(ui._tex(path).get_instance_id())
	ui._trim_texture_cache();await frames(3)
	var released: Array = []
	for path in chosen:
		if refs[path].get_ref() == null:
			released.append(path)
			check(not ResourceLoader.has_cached(path),"released atlas also leaves ResourceLoader cache: " + path)
	check(not released.is_empty(),"budget trimming releases actual Texture2D resources, not only dictionary entries")
	for i in range(hot.size()):
		var same = true
		for j in range(100):same = same and ui._tex(hot[i]).get_instance_id() == hot_ids[i]
		check(same,"100 hot atlas lookups retain the same resource: " + hot[i])
	measurements.memory_trimmed = memory()
	measurements.textures = {"paths":chosen,"sizes":sizes,"released":released,"hot":hot,"budget":ui.TEXTURE_CACHE_BUDGET}
	var restored = ui._tex(chosen[0])
	check(restored.get_image().get_data().hex_encode().sha256_text() == original_hash,"evicted atlas reload preserves exact imported pixels")
	restored = null
	measurements.memory_reloaded = memory()

func run():
	visual = DisplayServer.get_name() != "headless"
	if visual and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("Visible-window test refused without startup guard");quit(2);return
	Engine.max_fps = 60
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT));DirAccess.make_dir_recursive_absolute(TEMP+"slots")
	screen = SubViewport.new();screen.size = Vector2i(2556,1179);screen.render_target_update_mode = SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone = load("res://scenes/phone.tscn").instantiate();phone.set_script(load("res://tests/performance_phone_instrument.gd"))
	phone.safe_area_override = Rect2(177,0,2202,1116);phone.journal_directory_override = TEMP+"slots";screen.add_child(phone)
	await frames(4);ui = phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.audio.stop_all();ui.audio.set_process(false)
	ui.game.new_game();ui.game.save_path = TEMP+"working.json";ui.game.world_node = int(ui.game.stages[101].node);ui.game.start_battle(101)
	ui.game.story_events.clear();ui.view = "battle";ui.ui_mode = "inspect";ui.busy = false;ui.notice_time = 0;ui.phase_time = 0;ui.elapsed = 2
	ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true);ui.queue_redraw();await frames(5)
	check(phone.game_view.size_2d_override == Vector2i(364,240) and phone.pixel_scale == 4,"phone logical and physical resolution preserved")
	if visual:
		measurements.forced_legacy_rails = await sample_draws(true)
		measurements.cached_rails = await sample_draws(false)
		check(int(measurements.forced_legacy_rails.rail_draw_calls) >= 85,"legacy control rerender comparison exercised each frame")
		check(int(measurements.cached_rails.rail_draw_calls) <= 1,"unchanged rails no longer rebuild every frame")
		var stable = snap();phone.queue_redraw();await frames(3)
		check(snap() == stable,"cached controls match forced redraw pixel-for-pixel")
		var previous = snap();ui.elapsed += 0.33;ui.game.cursor.x += 1;ui.queue_redraw();await frames(3)
		check(snap() != previous,"game viewport keeps updating when control rails are cached")
		var advanced = snap();phone.queue_redraw();await frames(3)
		check(snap() == advanced,"updated game viewport matches a full shell redraw pixel-for-pixel")
		phone.draw_microseconds.clear();ui.game.turn += 1;await frames(3)
		check(phone.draw_microseconds.size() >= 1,"turn counter change redraws rail text")
		phone.draw_microseconds.clear();ui.busy = true;await frames(3)
		check(phone.draw_microseconds.size() >= 1,"cycle-unit enabled state redraws rail material")
		ui.busy = false;await frames(3)
		var p = Vector2.ZERO
		for button in phone.buttons:
			if int(button.key) == KEY_RIGHT:p = phone.safe_area.position + button.rect.get_center()*phone.pixel_scale
		phone.draw_microseconds.clear();phone._finger(81,p,true);await frames(3)
		check(phone.draw_microseconds.size() >= 1 and int(phone.fingers.get(81,0)) == KEY_RIGHT,"pressed control redraws and dispatches direction")
		phone._notification(Control.NOTIFICATION_APPLICATION_FOCUS_OUT);await frames(3)
		check(phone.fingers.is_empty() and ui.held_direction == Vector2i.ZERO,"focus loss clears held direction and pressed material")
		check(phone.layout_errors.is_empty() and ui.layout_errors.is_empty(),"current phone text, borders and controls remain in safe areas")
		await texture_probe()
	else:
		# Null render backends cannot establish GPU lifetime or pixel equality.
		check(phone._button_enabled(KEY_E),"headless: normal battle cycle control remains available")
	var result = {"passed":errors.is_empty(),"checks":checks,"errors":errors,"measurements":measurements,"background_render":visual,"iphone_device_measured":false,"player_saves_touched":false}
	var file = FileAccess.open(OUT+("render-performance.json" if visual else "logic-performance.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	print("PERFORMANCE_PHONE ",checks.size()," checks; errors: ",errors," measurements: ",JSON.stringify(measurements))
	phone.queue_free();await process_frame;screen.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
