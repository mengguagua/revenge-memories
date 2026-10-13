extends SceneTree
## Bounded UI intent checks: empty two-person actions and surrender feedback.
const SAVE := "res://reports/test-round5-feedback-save.json"
var ui
var checks := 0
var failures: Array[String] = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func choose(action: String) -> void:
	check(ui.menu_actions.has(action), "Native menu exposes " + action)
	if not ui.menu_actions.has(action): return
	ui.menu_selected = ui.menu_actions.find(action)
	ui._accept()

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	ui.instant_mode = true
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.set_process(false)
	ui.set_physics_process(false)
	for action in ["trade", "formation"]:
		ui.game.new_game()
		ui.game.world_node = 1
		ui.game.mode = "world"
		ui.view = "world"
		ui._clear_menu()
		ui._open_camp_menu()
		choose("camp:" + action)
		choose("camp:" + action + "_first:alm")
		check(ui.notice == "没有其他队员" and ui.menu_context == "camp", "One-member " + action + " gives an actionable empty-state message")
		check(ui.view == "world" and ui.game.mode == "world" and not ui.menu_items.is_empty(), "Empty second-member selection retains the visible camp menu")
		ui._cancel()
		check(ui.menu_items.is_empty() and ui.view == "world", "Cancel exits the empty-state camp menu safely")
	ui.game.new_game()
	for transition in [1, 2, 3]: ui.game.next_chapter(transition)
	ui.game.world_node = 42
	check(ui.game.start_battle(42), "Source Rudolf battle deploys")
	for enemy in ui.game.living("enemy"):
		if int(enemy.get("source_enemy_character_id", enemy.get("character_id", 0))) == 133:
			ui.game.commit_strike({"attacker": "alm", "defender": enemy.id, "hp_after": 0})
			break
	ui.game.check_outcome()
	check(ui.game.flags.get("scenario_forced_victory", "") == "rudolf_surrender", "Actual commander death marks source surrender")
	ui.game.complete_battle()
	ui.view = "victory"
	ui._clear_menu()
	ui.queue_redraw()
	await process_frame
	check(ui.text_checks.any(func(row): return str(row.text).contains("敌军已投降")), "Surrender result describes the actual resolution")
	check(not ui.text_checks.any(func(row): return str(row.text).contains("已击败全部敌军")), "Surrender result does not claim every soldier was defeated in combat")
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var file := FileAccess.open("res://reports/round5-feedback-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures,
		"scope": "Actual camp menus for single-member exchange/formation cancellation; native Rudolf commander-death settlement and rendered result text.",
		"limits": "Resolved source commander-death checkpoint, no natural late-campaign victory claim."}, "\t") + "\n")
	print("ROUND5 FEEDBACK: %d checks, %d failures" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
