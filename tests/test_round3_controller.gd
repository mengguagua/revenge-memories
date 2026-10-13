extends SceneTree
## Actual shortcut dispatch while native hub dialogue/choice/motion owns input.
const SAVE := "res://reports/test-round3-controller-save.json"
var ui
var checks := 0
var failures: Array[String] = []
var scenarios: Array[String] = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)

func reset() -> void:
	ui.game.new_game()
	ui.view = "hub"
	ui.busy = false
	ui.batch_running = false
	ui.held_direction = Vector2i.ZERO
	ui.instant_mode = true
	ui.game.enter_hub(44, Vector2i(6, 6))
	ui.hub_controller._setup(false)

func drain() -> void:
	var steps := 0
	while ui.view in ["hub_dialogue", "hub_choice"] and steps < 1000:
		steps += 1
		if ui.view == "hub_dialogue":
			ui.hub_controller.reveal = 10000
		else:
			if ui.hub_controller.choice_title.contains("记录进度"):
				ui.hub_controller.choice_index = 1
		ui._accept()
	check(steps < 1000, "Hub pages terminate within bounded input")

func test_vm_dialogue() -> void:
	reset()
	ui.game.recruit("lukas")
	ui.hub_controller._start_script(16)
	var hub = ui.hub_controller
	check(ui.view == "hub_dialogue" and hub.script_id == 16, "Original chapter transition waits on its actual dialogue")
	var before_pages := JSON.stringify(hub.pages)
	var before_callback: Callable = hub.after_dialogue
	var before_pc: int = hub.pc
	for code in [KEY_TAB, KEY_A, KEY_S]:
		key(code)
		check(ui.view == "hub_dialogue" and JSON.stringify(hub.pages) == before_pages, "Dialogue owns input when shortcut %d is pressed" % code)
		check(hub.after_dialogue == before_callback and hub.pc == before_pc and hub.script_id == 16, "Shortcut %d preserves pending VM continuation" % code)
	drain()
	check(ui.view == "chapter" and ui.game.chapter == 2 and hub.script_id < 0, "Dialogue still completes original transition into chapter two")
	check(ui.game.hub_used.get("event_vm", {}).is_empty(), "Completed transition releases its VM checkpoint")
	scenarios.append("source script16 dialogue + TAB/A/S -> original chapter transition")

func test_vm_choice() -> void:
	reset()
	ui.hub_controller.enter(1, Vector2i(5, 10))
	var hub = ui.hub_controller
	check(ui.view == "hub_choice" and hub.script_id >= 0 and hub.choice_title.contains("记录进度"), "Training VM opens original progress choice")
	var before_options := JSON.stringify(hub.choices)
	var before_title: String = hub.choice_title
	var before_callback: Callable = hub.after_choice
	var before_pc: int = hub.pc
	for code in [KEY_TAB, KEY_A, KEY_S]:
		key(code)
		check(ui.view == "hub_choice" and hub.choice_title == before_title and JSON.stringify(hub.choices) == before_options, "VM choice owns input when shortcut %d is pressed" % code)
		check(hub.after_choice == before_callback and hub.pc == before_pc, "Shortcut %d preserves original progress choice callback" % code)
	drain()
	check(ui.view == "hub" and hub.script_id < 0, "Training resumes and releases keyboard ownership")
	check(ui.game.flags.get("source_flag_17", false), "Training's original final flag is applied")
	scenarios.append("source training progress choice + TAB/A/S -> original continuation")

func test_free_choice() -> void:
	reset()
	ui.hub_controller.open_system_menu()
	var hub = ui.hub_controller
	check(ui.view == "hub_choice" and hub.choice_title == "队伍", "Idle hub still exposes its actual system menu")
	var before := JSON.stringify(hub.choices)
	var callback: Callable = hub.after_choice
	for code in [KEY_TAB, KEY_A, KEY_S]:
		key(code)
		check(JSON.stringify(hub.choices) == before and hub.after_choice == callback and hub.choice_title == "队伍", "Shortcut %d cannot replace a pending free hub choice" % code)
	ui._cancel()
	check(ui.view == "hub", "Cancelled system menu returns to exploration")
	key(KEY_TAB)
	check(ui.view == "hub_choice" and hub.choice_title == "查看人物", "TAB still opens status from idle exploration")
	ui._accept()
	check(ui.view == "hub_dialogue", "Status choice displays actual source character data")
	var pages := JSON.stringify(hub.pages)
	key(KEY_S)
	check(ui.view == "hub_dialogue" and JSON.stringify(hub.pages) == pages, "System shortcut cannot replace the pending status page")
	drain()
	check(ui.view == "hub", "Status pages return to normal hub input")
	scenarios.append("idle system/status access; pending choices and pages protected")

func test_motion() -> void:
	reset()
	var hub = ui.hub_controller
	ui.instant_mode = false
	var at: Vector2i = ui.game.hub_position
	var destination := at
	for direction in [Vector2i.DOWN, Vector2i.UP, Vector2i.LEFT, Vector2i.RIGHT]:
		var candidate: Vector2i = at + direction
		if hub._ground(candidate) and hub._actor_at(candidate) == 0:
			destination = candidate
			break
	check(destination != at, "Original room has a legal source movement cell")
	hub._start_motion(1, destination, 0.2)
	for code in [KEY_TAB, KEY_A, KEY_S]:
		key(code)
		check(ui.view == "hub" and hub.motion_left > 0, "Shortcut %d cannot replace an in-progress native step" % code)
	hub.process(0.2)
	check(ui.view == "hub" and hub.motion_left == 0 and ui.game.hub_position == destination, "Real movement reaches its target and leaves input unlocked")
	ui.instant_mode = true
	scenarios.append("real timed source movement + TAB/A/S -> complete target position")

func test_save_feedback() -> void:
	reset()
	var hub = ui.hub_controller
	var missing := "res://reports/__round3_missing_save_directory__/save.json"
	check(not DirAccess.dir_exists_absolute(missing.get_base_dir()), "Save-failure probe uses a nonexistent isolated directory")
	ui.game.save_path = missing
	key(KEY_S)
	for i in range(hub.choices.size()):
		if hub.choices[i].value == "save": hub.choice_index = i
	ui._accept()
	check(ui.view == "hub_dialogue" and str(hub.pages[0].text).contains("保存失败"), "Hub save menu reports failed write instead of claiming success")
	check(not FileAccess.file_exists(missing) and not FileAccess.file_exists(missing + ".tmp"), "Failed write creates neither save nor temporary file")
	drain()
	ui.game.save_path = SAVE
	key(KEY_S)
	for i in range(hub.choices.size()):
		if hub.choices[i].value == "save": hub.choice_index = i
	ui._accept()
	check(ui.view == "hub_dialogue" and str(hub.pages[0].text).contains("已经记录"), "Successful hub save keeps the existing success feedback")
	check(FileAccess.file_exists(SAVE), "Successful manual save writes only the isolated test checkpoint")
	drain()
	scenarios.append("actual hub manual-save menu -> failed/successful write feedback")

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	root.add_child(ui)
	await process_frame
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	test_vm_dialogue()
	test_vm_choice()
	test_free_choice()
	test_motion()
	test_save_feedback()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var report := {"checks": checks, "failures": failures, "scenarios": scenarios,
		"scope": "Actual main keyboard input and original hub VM/dialogue/choice; one real timed step; isolated save, headless.", "user_save_accessed": false}
	var file := FileAccess.open("res://reports/round3-controller-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	file.close()
	print("ROUND3 CONTROLLER: ", checks, " checks, ", failures.size(), " failures")
	quit(0 if failures.is_empty() else 1)
