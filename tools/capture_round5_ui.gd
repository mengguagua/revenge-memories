extends SceneTree
## Source UI audit before/after, rendered under the preloaded no-window guard.
const Progression = preload("res://core/unit_progression.gd")
const State = preload("res://core/game_state.gd")
const SAVE := "res://reports/test-round5-ui-capture-save.json"
var viewport: SubViewport
var ui
var captures: Array = []
var errors: Array[String] = []
var phase := "before"

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		quit(1)
		return
	if OS.get_cmdline_user_args().has("--after"): phase = "after"
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
	if not ui.menu_actions.has(action):
		errors.append("Missing real menu action " + action)
		return
	ui.menu_selected = ui.menu_actions.find(action)
	key(KEY_Z)

func snap(id: String, state: Dictionary) -> void:
	ui.notice_time = 0
	ui.phase_time = 0
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var pixels: Image = viewport.get_texture().get_image()
	var path := "res://reports/screenshots/round5-ui-" + phase + "-" + id + ".png"
	if pixels.save_png(path) != OK: errors.append("PNG save failed " + id)
	for error in ui.layout_errors: errors.append(id + ": " + str(error))
	captures.append({"id": id, "path": path, "state": state, "pixels": [pixels.get_width(), pixels.get_height()],
		"bytes": FileAccess.get_file_as_bytes(path).size(), "safe_area_errors": ui.layout_errors.duplicate()})

func setup(stage: int = 1) -> void:
	ui.game.new_game()
	for id in ["lukas", "silque", "gray"]: ui.game.recruit(id)
	ui.game.roster.silque = Progression.learn_spells(ui.game.roster.silque, 7).unit
	ui.game.world_node = stage
	ui.game.previous_world_node = 49 if stage == 1 else 1
	ui.game.route_positions.alm = stage
	ui._enter_battle(stage)
	ui.game.story_events.clear()
	ui._clear_menu()
	ui.ui_mode = "inspect"
	ui.busy = false
	ui.batch_running = false
	ui.held_direction = Vector2i.ZERO

func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256, 240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	if phase == "before" and OS.get_cmdline_user_args().has("--baseline"):
		ui.set_script(load("/private/tmp/round5-main-baseline.gd"))
	ui.game.save_path = SAVE
	ui.instant_mode = true
	viewport.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	setup()
	ui.game.cursor = State.pos(ui.game.find_unit("lukas"))
	ui._focus_battle(ui.game.cursor, true)
	key(KEY_S)
	ui.menu_selected = ui.menu_actions.find("roster")
	await snap("01-status-command", {"focused": "lukas", "displayed_command": "人物状态"})
	choose("roster")
	await snap("02-status-result", {"focused": "lukas", "shown": ui.status_id, "view": ui.view, "ui_mode": ui.ui_mode})
	setup(2)
	var caster = ui.game.find_unit("silque")
	ui.game.cursor = State.pos(caster)
	key(KEY_Z)
	for at in ui.game.reachable(caster).costs:
		if ui.game.can_stop(caster, at) and ui.game.living("player").any(func(unit): return unit.id != caster.id and absi(State.pos(unit).x-at.x)+absi(State.pos(unit).y-at.y)==1):
			ui.game.cursor = at
			break
	key(KEY_Z)
	choose("magic")
	choose("spell:43")
	if ui.target_ids.is_empty():
		push_error("Native Warp capture did not reach an eligible recipient")
		quit(1)
		return
	await snap("03-warp-recipient", {"spell": 43, "selected": str(ui.target_ids[ui.target_index]), "mode": ui.ui_mode})
	key(KEY_Z)
	ui.game.cursor = Vector2i(20, 18)
	if not ui.game.in_bounds(ui.game.cursor) or not ui.game.can_stop(ui.game.find_unit(ui.support_target), ui.game.cursor):
		errors.append("Warp landing capture must use a legal source-map destination")
	ui._focus_battle(ui.game.cursor, true)
	await snap("04-warp-landing", {"spell": 43, "selected": ui.support_target, "mode": ui.ui_mode, "stage": 2, "cursor": [20, 18]})
	# Actual source boss-death settlement with remaining soldiers is a valid
	# result state. This checkpoint does not claim a natural combat victory.
	ui.game.new_game()
	for transition in [1, 2, 3]: ui.game.next_chapter(transition)
	ui.game.world_node = 42
	ui.game.start_battle(42)
	for enemy in ui.game.living("enemy"):
		if int(enemy.get("source_enemy_character_id", enemy.get("character_id", 0))) == 133:
			ui.game.commit_strike({"attacker": "alm", "defender": enemy.id, "hp_after": 0})
			break
	ui.game.check_outcome()
	ui.game.complete_battle()
	ui.view = "victory"
	ui._clear_menu()
	await snap("05-rudolf-result", {"outcome": ui.game.battle_outcome, "remaining_enemies": ui.game.living("enemy").size(), "source": "Rudolf death surrender settlement checkpoint"})
	if phase == "after":
		ui.game.new_game()
		for transition in [1, 2, 3, 4]: ui.game.next_chapter(transition)
		ui.game.apply_hub_flag(82)
		ui.game.enter_dungeon_battle(22)
		ui._begin_existing_battle()
		var pages := 0
		while ui.view == "battle_story" and pages < 100:
			ui.dialogue_reveal = 10000
			key(KEY_Z)
			pages += 1
		key(KEY_S)
		ui.menu_selected = ui.menu_actions.find("final_prepare")
		await snap("06-legacy-preparation-command", {"stage": 62, "prepared": ui.game.final_battle_readiness().ready, "action": "final_prepare"})
		choose("final_prepare")
		await snap("07-legacy-preparation-result", {"mode": ui.game.mode, "hub": ui.game.hub_id,
			"position": [ui.game.hub_position.x, ui.game.hub_position.y], "snapshot_cleared": ui.game.battle_start_snapshot.is_empty()})
	var file := FileAccess.open("res://reports/round5-ui-" + phase + "-visual-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"phase": phase, "captures": captures, "safe_area_errors": errors,
		"background_guard": true, "user_save_accessed": false, "visible_window": false,
		"scope": "Native system status command/result, learned Warp recipient/destination and source Rudolf surrender result.",
		"limits": "Source learned spell and resolved commander-death checkpoints; no natural late campaign victory claim."}, "\t") + "\n")
	file.close()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	print("ROUND5 UI CAPTURE ", phase, ": ", captures.size(), " screens, errors=", errors)
	quit(0 if errors.is_empty() else 1)
