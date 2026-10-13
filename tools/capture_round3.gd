extends SceneTree
## Guarded pixels of actual round3 hub input ownership and failed-save notice.
const SAVE := "res://reports/round3-capture-save.json"
var viewport: SubViewport
var ui
var captures: Array = []
var errors: Array[String] = []

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

func snap(label: String) -> void:
	ui.hub_controller.reveal = 10000
	ui.notice_time = 0
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var path := "res://reports/screenshots/round3-" + label + ".png"
	viewport.get_texture().get_image().save_png(path)
	for error in ui.layout_errors: errors.append(label + ": " + str(error))
	captures.append({"id": label, "path": path, "safe_area_errors": ui.layout_errors.duplicate()})

func reset() -> void:
	ui.game.new_game()
	ui.game.save_path = SAVE
	ui.game.enter_hub(44, Vector2i(6, 6))
	ui.hub_controller._setup(false)

func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256, 240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	ui.instant_mode = true
	viewport.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	reset()
	ui.hub_controller.enter(1, Vector2i(5, 10))
	key(KEY_TAB)
	if not ui.hub_controller.choice_title.contains("记录进度"): errors.append("TAB replaced source VM choice")
	await snap("01-source-choice-after-tab")
	reset()
	ui.game.recruit("lukas")
	ui.hub_controller._start_script(16)
	key(KEY_A)
	if ui.view != "hub_dialogue": errors.append("A replaced source VM dialogue")
	await snap("02-source-dialogue-after-a")
	reset()
	ui.game.save_path = "res://reports/__round3_missing_save_directory__/save.json"
	ui.hub_controller.open_system_menu()
	for i in range(ui.hub_controller.choices.size()):
		if ui.hub_controller.choices[i].value == "save": ui.hub_controller.choice_index = i
	ui._accept()
	if not str(ui.hub_controller.pages[0].text).contains("保存失败"): errors.append("Save failure was not displayed")
	await snap("03-save-failure")
	var report := {"captures": captures, "safe_area_errors": errors, "background_guard": true,
		"user_save_accessed": false, "scope": "Actual source hub VM after shortcuts and failed manual-save notice, guarded SubViewport pixels."}
	var file := FileAccess.open("res://reports/round3-visual-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	file.close()
	ui.audio.stop_all()
	ui.queue_free()
	await create_timer(0.2).timeout
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	print("ROUND3 CAPTURE: ", captures.size(), " screens, errors=", errors)
	quit(0 if errors.is_empty() else 1)
