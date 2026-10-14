extends SceneTree
## New shortcut bytecode only; no first-chapter battle/old UI replay.
const SAVE := "/private/tmp/fe2-round8-package-save.json"
var ui
var checks := 0
var failures: Array[String] = []

func _initialize() -> void: call_deferred("run")

func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)
	event = InputEventKey.new()
	event.physical_keycode = code
	ui._input(event)

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label)

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	root.add_child(ui)
	await process_frame
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.game.new_game()
	ui.view = "village"
	ui.game.mode = "village"
	key(KEY_TAB)
	check(ui.menu_context == "roster", "Pack village status shortcut opens actual roster")
	key(KEY_Z)
	check(ui.view == "village_status" and ui.status_id == "alm", "Pack roster confirms actual character")
	key(KEY_X)
	ui.view = "world"
	ui.game.mode = "world"
	key(KEY_A)
	check(ui.menu_context == "camp_members", "Pack world A shares status shortcut")
	key(KEY_Z)
	check(ui.view == "camp_status" and ui.status_id == "alm", "Pack world status shows actual member")
	key(KEY_X)
	check(ui.view == "world" and ui.game.world_node == 49, "Pack status closes to unchanged world location")
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var file := FileAccess.open("/private/tmp/fe2-round8-package-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"battle_replays":0,"screenshots":0,"user_save_accessed":false},"  ")+"\n")
	print("ROUND8 PACKAGE: ",checks," checks, ",failures.size()," failures")
	quit(0 if failures.is_empty() else 1)
