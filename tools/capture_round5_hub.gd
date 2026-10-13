extends SceneTree
## Native hub pixels, guarded before launch; before/after use the same fixtures.
const SAVE := "res://reports/test-round5-hub-capture-save.json"
var viewport: SubViewport
var ui
var captures: Array = []
var errors: Array[String] = []
var phase := "before"

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("Round5 hub capture requires the preloaded background guard")
		quit(1)
		return
	for arg in OS.get_cmdline_user_args():
		if arg in ["after", "formation-before", "formation-after", "joint-before", "joint-after", "joint-celica-after"]: phase = arg
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	if not ok: errors.append(label)

func require(ok: bool, label: String) -> bool:
	if ok: return true
	errors.append(label)
	push_error(label)
	quit(1)
	return false

func choose_value(value) -> bool:
	if not require(ui.view == "hub_choice", "Choice input must stay in actual hub_choice: " + str(value)): return false
	var hub = ui.hub_controller
	var wanted := -1
	for i in range(hub.choices.size()):
		if hub.choices[i].value == value:
			wanted = i
			break
	if not require(wanted >= 0, "Actual visible choice value exists: " + str(value)): return false
	var steps := 0
	while hub.choice_index != wanted and steps < hub.choices.size():
		key(KEY_DOWN)
		steps += 1
	if not require(hub.choice_index == wanted and hub.choices[hub.choice_index].value == value, "Actual input selected expected value: " + str(value)): return false
	key(KEY_ENTER)
	return true

func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)
	event = InputEventKey.new()
	event.physical_keycode = code
	event.pressed = false
	ui._input(event)

func reset(chapter: int) -> void:
	ui.game.new_game()
	for transition in range(1, chapter):
		check(ui.game.next_chapter(transition), "Original chapter landmark%d" % transition)
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
	if ui.view == "hub_dialogue": ui.hub_controller.reveal = 10000
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var pixels: Image = viewport.get_texture().get_image()
	var path := "res://reports/screenshots/round5-hub-" + phase + "-" + label + ".png"
	check(pixels.get_width() == 256 and pixels.get_height() == 240, label + ": viewport dimensions")
	check(pixels.save_png(path) == OK, label + ": PNG write")
	for error in ui.layout_errors: errors.append(label + ": " + str(error))
	captures.append({"id": label, "path": path, "pixels": [pixels.get_width(), pixels.get_height()],
		"bytes": FileAccess.get_file_as_bytes(path).size(), "safe_area_errors": ui.layout_errors.duplicate(), "state": state})

func capture_paging() -> void:
	reset(1)
	for id in ["lukas", "gray", "tobin", "kliff", "silque", "clair", "clive", "forsyth", "python"]: ui.game.recruit(id)
	ui.hub_controller.enter(3, Vector2i(7, 3))
	key(KEY_TAB)
	await snap("01-status-page1", {"view": ui.view, "choices": ui.hub_controller.choices.size(), "choice_index": ui.hub_controller.choice_index})
	ui._mouse_accept(Vector2(230, 214))
	await snap("02-next-page-arrow", {"view": ui.view, "choice_index": ui.hub_controller.choice_index,
		"page": int(ui.hub_controller.choice_index / 5) + 1, "input": "Main native mouse point230,214"})

func capture_final_gate() -> void:
	reset(5)
	ui.game.world_node = 48
	ui.game.route_positions.alm = 48
	ui.game.flags.scenario_celica_story_phase = 3
	ui.game.flags.celica_captive = true
	ui.game.apply_hub_flag(81)
	ui.hub_controller.enter(37, Vector2i(11, 25))
	await snap("03-final-gate", {"view": ui.view, "room": ui.game.hub_id, "leader": [11,25], "finisher": ui.game.final_battle_readiness()})
	key(KEY_UP)
	key(KEY_UP)
	key(KEY_UP)
	await snap("04-final-gate-result", {"view": ui.view, "room": ui.game.hub_id, "stage_id": ui.game.stage_id,
		"leader": [ui.game.hub_position.x, ui.game.hub_position.y], "script": ui.hub_controller.script_id,
		"source_flag82": ui.game.flags.get("source_flag_82", false), "input": "Actual Main UP opens source final door; two UP steps walk onto script55 trigger"})

func capture_formation() -> void:
	reset(5)
	ui.game.world_node = 48
	ui.game.route_positions.alm = 48
	ui.game.flags.scenario_celica_story_phase = 3
	ui.game.flags.celica_captive = true
	ui.game.apply_hub_flag(81)
	for id in ["lukas", "gray", "tobin", "kliff", "clair", "clive", "forsyth", "python", "luthier", "tatiana"]: ui.game.recruit(id)
	ui.hub_controller.enter(37, Vector2i(11,25))
	key(KEY_S)
	await snap("01-preparation-menu", {"view": ui.view, "choices": ui.hub_controller.choices, "readiness": ui.game.final_battle_readiness()})
	if phase == "formation-before": return
	key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_ENTER)
	key(KEY_RIGHT); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN)
	await snap("02-reserve-person", {"view": ui.view, "choice_index": ui.hub_controller.choice_index, "choices": ui.hub_controller.choices})
	key(KEY_ENTER)
	await snap("03-exchange-order-target", {"view": ui.view, "choices": ui.hub_controller.choices})
	key(KEY_ENTER)
	await snap("04-prepared-order-result", {"view": ui.view, "party": ui.game.party, "readiness": ui.game.final_battle_readiness()})

func capture_joint_preparation() -> void:
	reset(5)
	ui.game.world_node = 48
	ui.game.route_positions.alm = 48
	ui.game.flags.scenario_celica_story_phase = 3
	ui.game.flags.celica_captive = true
	ui.game.apply_hub_flag(81)
	ui.game.roster.alm.item_id = 1
	ui.game.convoy.alm = []
	ui.game.convoy.celica = []
	for _i in range(40):
		ui.game.convoy.alm.append(1)
		ui.game.convoy.celica.append(17 if _i == 39 else 1)
	ui.game.hub_used["40:0"] = true
	ui.hub_controller.enter(37, Vector2i(11,25))
	key(KEY_S); key(KEY_RIGHT)
	await snap("01-preparation-menu-page2", {"view": ui.view, "choices": ui.hub_controller.choices,
		"readiness": ui.game.final_battle_readiness(), "convoy_sizes": [40,40]})
	if phase == "joint-before": return
	key(KEY_ENTER)
	await snap("02-joint-operation", {"view": ui.view, "choices": ui.hub_controller.choices})
	key(KEY_ENTER); key(KEY_DOWN); key(KEY_ENTER)
	for _i in range(7): key(KEY_RIGHT)
	for _i in range(4): key(KEY_DOWN)
	await snap("03-other-convoy-sword", {"view": ui.view, "choices": ui.hub_controller.choices,
		"choice_index": ui.hub_controller.choice_index})
	key(KEY_ENTER); key(KEY_ENTER)
	await snap("04-explicit-equipment-swap", {"view": ui.view, "choices": ui.hub_controller.choices})
	key(KEY_ENTER)
	await snap("05-conserved-preparation-result", {"view": ui.view, "readiness": ui.game.final_battle_readiness(),
		"convoy_sizes": [ui.game.convoy.alm.size(),ui.game.convoy.celica.size()], "held": ui.game.roster.alm.item_id,
		"original_sword_slot": ui.game.convoy.celica[39], "route": ui.game.route, "captive": ui.game.flags.celica_captive})

func capture_celica_reserve() -> void:
	reset(5)
	ui.game.world_node = 48
	ui.game.route_positions.alm = 48
	ui.game.flags.scenario_celica_story_phase = 3
	ui.game.flags.celica_captive = true
	ui.game.apply_hub_flag(81)
	ui.game.parties.celica = ["celica", "mae", "boey", "saber", "kamui", "leo", "valbar", "palla", "catria", "atlas", "genny"]
	for id in ui.game.parties.celica:
		if not require(ui.game.characters.has(id), "Real source Celica reserve fixture member exists: " + str(id)): return
		if not ui.game.roster.has(id): ui.game.roster[id] = ui.game._initial_character(id)
	var readiness: Dictionary = ui.game.final_battle_readiness()
	if not require(not readiness.ready and readiness.reason == "reserve_nosferatu" and readiness.reserve_route == "celica", "Captured healer is truly beyond the first ten deployed Celica members"): return
	ui.hub_controller.enter(37, Vector2i(11,25))
	key(KEY_UP); key(KEY_UP); key(KEY_UP)
	if not require(ui.view == "hub_dialogue" and ui.game.hub_position == Vector2i(11,24) and not ui.game.flags.get("source_flag_82",false), "Celica reserve fixture reaches the actual final preparation instruction before entering battle"): return
	await snap("01-reserve-instruction", {"view": ui.view, "readiness": ui.game.final_battle_readiness(), "leader": [ui.game.hub_position.x,ui.game.hub_position.y]})
	while ui.view == "hub_dialogue":
		ui.hub_controller.reveal = 10000
		key(KEY_ENTER)
	if not require(ui.view == "hub", "Preparation explanation closes to active hub exploration"): return
	key(KEY_S)
	if not choose_value("joint_prepare"): return
	if not require(ui.hub_controller.choice_title == "双方整备", "Actual local joint preparation submenu is open"): return
	if not choose_value("formation"): return
	if not require(ui.view == "hub_choice" and ui.hub_controller.choice_title == "选择队伍", "Actual joint order branch asks for the army"): return
	await snap("02-choose-army-order", {"view": ui.view, "choices": ui.hub_controller.choices})
	if not choose_value("celica"): return
	if not require(ui.view == "hub_choice" and ui.hub_controller.choice_title.contains("赛莉卡") and ui.hub_controller.choices.size() == 10, "Actual complete captured Celica member choice is open"): return
	var target := -1
	for i in range(ui.hub_controller.choices.size()):
		if ui.hub_controller.choices[i].value == "genny": target = i
	if not require(target >= 0, "Actual reserve Genny is selectable"): return
	while ui.hub_controller.choice_index != target: key(KEY_DOWN)
	if not require(ui.view == "hub_choice" and ui.hub_controller.choices[ui.hub_controller.choice_index].value == "genny", "Actual input highlight is the reserve healer"): return
	await snap("03-captured-reserve-selected", {"view": ui.view, "choices": ui.hub_controller.choices, "choice_index": ui.hub_controller.choice_index})
	key(KEY_ENTER)
	if not require(ui.view == "hub_choice" and ui.hub_controller.choice_title == "选择交换顺序的队员", "Actual second order selection is open"): return
	if not choose_value("mae"): return
	if not require(ui.view == "hub_dialogue" and ui.game.final_battle_readiness().ready and ui.game.parties.celica[0] == "celica" and ui.game.parties.celica[1] == "genny" and ui.game.route == "alm" and ui.game.flags.celica_captive, "Actual joint order makes Genny deployable while route/captivity and leader stay intact"): return
	await snap("04-joint-order-result", {"view": ui.view, "celica_party": ui.game.parties.celica, "alm_party": ui.game.party,
		"readiness": ui.game.final_battle_readiness(), "route": ui.game.route, "captive": ui.game.flags.celica_captive})
	while ui.view == "hub_dialogue":
		ui.hub_controller.reveal = 10000
		key(KEY_ENTER)
	key(KEY_UP)
	if not require(ui.game.stage_id == 62 and ui.game.flags.get("final_parties_merged",false) and ui.view in ["battle","battle_story"] and not ui.game.find_unit("genny").is_empty(), "Prepared joint order enters actual final battle with the reserve healer"): return
	await snap("05-prepared-final-entry", {"view": ui.view, "stage_id": ui.game.stage_id,
		"deployed_genny": not ui.game.find_unit("genny").is_empty(), "final_parties_merged": ui.game.flags.get("final_parties_merged",false)})

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
	if phase == "joint-celica-after":
		await capture_celica_reserve()
	elif phase.begins_with("joint"):
		await capture_joint_preparation()
	elif phase.begins_with("formation"):
		await capture_formation()
	else:
		await capture_paging()
		await capture_final_gate()
	var file := FileAccess.open("res://reports/round5-hub-visual-"+phase+"-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"captures": captures, "safe_area_errors": errors,
		"background_guard": true, "guard_loaded_before_engine_main": true,
		"user_save_accessed": false, "visible_or_focused_game_window_started": false,
		"scope": "Original256x240 status page mouse arrow and final gate screenshots at source chapter/room landmarks.",
		"limits": "Chapter landmarks skip previous battles; screenshots do not establish a natural full campaign playthrough."}, "\t") + "\n")
	file.close()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	print("ROUND5 HUB CAPTURE: ", captures.size(), " screens, errors=", errors)
	quit(0 if errors.is_empty() else 1)
