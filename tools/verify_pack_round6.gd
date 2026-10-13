extends SceneTree
## External packaged-bytecode smoke, limited to this round's three changes.
var ui
var failures: Array[String] = []
var checks := 0

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label)

func click(point: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.position = point
	event.pressed = true
	event.button_index = MOUSE_BUTTON_LEFT
	ui._input(event)

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = "/private/tmp/test-round6-package-save.json"
	ui.instant_mode = true
	root.add_child(ui)
	ui.set_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.game.new_game()
	ui.game.mode = "world"
	ui.view = "world"
	for i in range(40): ui.game.convoy.alm.append(2)
	ui._camp_action("withdraw")
	var rect: Rect2 = ui._menu_rect()
	click(rect.position + Vector2(rect.size.x - 16, rect.size.y - 20))
	check(ui.menu_context == "stored_items" and ui.menu_scroll == 10, "Packaged pointer page scroll")
	check(ui.game.convoy.alm.size() == 40 and ui.camp_first.is_empty(), "Packaged page navigation keeps inventory")
	check(not ui._zh_glyph("至").is_empty(), "Packaged range label has its actual glyph")
	ui._clear_menu()
	ui.game.world_node = 1
	ui._enter_battle(1)
	ui.game.story_events.clear()
	ui._open_system_menu()
	rect = ui._menu_rect()
	click(rect.position + Vector2(16, 10))
	check(ui.menu_context == "system" and ui.game.turn == 1 and ui.game.phase == "player", "Packaged menu frame cannot end turn")
	ui._clear_menu()
	ui.view = "reward"
	ui.reward = {"unit": "alm", "gain": 5, "leveled": false, "growths": {}}
	ui.busy = true
	ui.batch_running = true
	ui.reward_dismissed = false
	click(Vector2(128, 214))
	check(ui.reward_dismissed and ui.batch_running and ui.view == "reward", "Packaged reward pointer acknowledgement retains phase owner")
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute("/private/tmp/test-round6-package-save.json" + suffix)
	var file := FileAccess.open("/private/tmp/round6-package-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures, "user_save_accessed": false,
		"scope": "External-directory delivered-bytecode smoke of the three changed paths; timed behavior verified separately."}, "  ") + "\n")
	file.close()
	print("ROUND6 PACK: ", checks, " checks, ", failures.size(), " failures")
	quit(0 if failures.is_empty() else 1)
