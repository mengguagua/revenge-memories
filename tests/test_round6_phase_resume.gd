extends SceneTree
## Previously unchecked mouse-only resume at a real timed enemy-level reward.
const SAVE := "res://reports/test-round6-phase-save.json"
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
	event = InputEventKey.new()
	event.physical_keycode = code
	ui._input(event)

func click() -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.position = Vector2(128, 214)
	ui._input(event)

func tick() -> void:
	ui._process(1.0 / 60.0)
	await process_frame

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
	ui.game.recruit("lukas")
	ui.game.world_node = 1
	ui.game.previous_world_node = 49
	ui.instant_mode = true
	ui._enter_battle(1)
	ui.game.story_events.clear()
	ui.instant_mode = false
	ui.animation_speed = 100.0
	ui.game.phase = "enemy"
	# This is a legal source-map suspend checkpoint, isolating the last enemy.
	# Enemy attributes and original combat/AI/animation programs are unchanged.
	for enemy in ui.game.living("enemy"): enemy.acted = str(enemy.id) != "brigand_1"
	var alm: Dictionary = ui.game.find_unit("alm")
	alm.position = [11, 5]
	alm.exp = 99
	check(ui.game.in_bounds(Vector2i(11, 5)) and ui.game.category(Vector2i(11, 5)) >= 0, "Suspend position is on the actual source map")
	check(ui.game.can_attack(ui.game.find_unit("brigand_1"), alm), "Remaining source enemy can attack Alm")
	check(ui.game.save_game(), "Production suspend save contains one remaining enemy action")
	ui._show_title()
	ui.title_menu = true
	ui.title_selected = 1
	key(KEY_Z)
	var deadline := Time.get_ticks_msec() + 15000
	while ui.view != "reward" and Time.get_ticks_msec() < deadline:
		await tick()
	check(ui.view == "reward" and ui.batch_running and ui.game.phase == "enemy", "Title continue reaches a real timed reward in the resumed enemy phase")
	if ui.view != "reward":
		await finish()
		return
	check(bool(ui.reward.leveled) and ui.game.find_unit("alm").level == 2, "Original counterattack EXP creates an explicit level confirmation")
	var hp: int = ui.game.find_unit("alm").hp
	var exp: int = ui.game.find_unit("alm").exp
	var source_level: int = ui.game.find_unit("alm").level
	for code in [KEY_X, KEY_TAB, KEY_A, KEY_S, KEY_DOWN]: key(code)
	check(ui.view == "reward" and ui.menu_items.is_empty() and ui.batch_running, "Unrelated shortcuts cannot escape the owned timed reward")
	# Normal rewards auto-expire, but this leveled one must stay until confirm.
	ui._process(3.0)
	check(ui.view == "reward" and not ui.reward_dismissed, "Level-up does not silently auto-advance")
	click()
	check(ui.reward_dismissed and ui.view == "reward" and ui.batch_running, "Actual mouse confirm acknowledges reward without prematurely unlocking phase")
	var mouse_dismissed: bool = ui.reward_dismissed
	if not mouse_dismissed: key(KEY_Z) # Release the baseline failure to finish and clean up.
	deadline = Time.get_ticks_msec() + 15000
	while (ui.batch_running or ui.busy) and Time.get_ticks_msec() < deadline:
		await tick()
	check(ui.view == "battle" and ui.game.phase == "player" and ui.game.turn == 2 and not ui.busy and not ui.batch_running, "Reward continuation completes the remaining enemy phase and releases gameplay")
	check(ui.game.find_unit("alm").level == source_level and ui.game.find_unit("alm").exp == exp, "Continuation grants no repeated counterattack EXP or level")
	check(ui.game.find_unit("alm").hp == hp, "Continuation does not replay the already committed enemy attack")
	check(ui.game.find_unit("brigand_1").acted, "Remaining source enemy action commits once")
	check(ui.game.save_game(), "Completed resumed phase saves")
	ui._show_title()
	ui.title_menu = true
	ui.title_selected = 1
	key(KEY_Z)
	check(ui.view == "battle" and ui.game.turn == 2 and ui.game.phase == "player" and ui.game.find_unit("alm").hp == hp, "Title continue after reward restores the playable next turn")
	check(ui.game.find_unit("alm").exp == exp and ui.game.find_unit("alm").level == source_level, "Subsequent resume preserves one progression settlement")
	check(ui.battle_animation.missing_animations.is_empty() and ui.map_effects.missing_programs.is_empty(), "Real timed branch uses available original programs")
	scenarios.append("Source map1 enemy suspend → real title continue → timed counterattack level → mouse-only acknowledgement → remaining phase → save/title continue")
	scenarios.append("Level wait owns unrelated shortcuts and never double-grants attack/EXP")
	await finish()

func finish() -> void:
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var before_run := OS.get_cmdline_user_args().has("--before")
	var file := FileAccess.open("res://reports/round6-phase-" + ("before" if before_run else "after") + "-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures, "scenarios": scenarios,
		"user_save_accessed": false, "visible_window": false, "new_screenshots": 0,
		"scope": "One new timed resume branch with source AI/stats and real mouse input; isolated save and99EXP/map position checkpoint.",
		"limits": "Accelerated native timers; no natural campaign leveling or whole-campaign replay."}, "  ") + "\n")
	file.close()
	print("ROUND6 PHASE RESUME: ", checks, " checks, ", failures.size(), " failures")
	quit(0 if failures.is_empty() else 1)
