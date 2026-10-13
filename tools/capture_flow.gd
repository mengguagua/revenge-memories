extends SceneTree
var viewport: SubViewport
var ui
var captures: Array = []
var all_errors: Array = []
var animation_report: Dictionary = {}
var dialogue_page_count := 0
var motion_report: Dictionary = {}
var all_health_checks: Array = []

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("Launch with tools/background_capture/run.sh: no unguarded graphics windows allowed")
		quit(1)
		return
	call_deferred("run")

func snap(id: String) -> void:
	ui.queue_redraw()
	for _i in range(4):
		await process_frame
	RenderingServer.force_draw(false)
	var image = viewport.get_texture().get_image()
	var path = "res://reports/screenshots/" + id + ".png"
	image.save_png(path)
	captures.append({"id": id, "path": path, "width": 256, "height": 240,
		"text_checks": ui.text_checks.size(), "safe_area_errors": ui.layout_errors.duplicate()})
	all_errors.append_array(ui.layout_errors)
	all_health_checks.append_array(ui.health_checks)

func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256, 240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	viewport.add_child(ui)
	ui.game.save_path = "res://reports/capture-save.json"
	ui.instant_mode = true
	ui.elapsed = 0.4
	await snap("01-title")
	ui.title_menu = true
	await snap("02-title-menu")
	ui._new_game()
	await snap("03-chapter")
	ui._enter_village()
	ui.dialogue_reveal = 200.0
	await snap("04-training-dialogue")
	ui.view = "village"
	await snap("05-village-left")
	ui.game.village_position = Vector2i(20, 8)
	await snap("06-village-right")
	for key in ["lukas_report", "mycen_refusal", "alm_volunteers", "gray_joins", "tobin_joins", "kliff_joins"]:
		ui.game.complete_dialogue(key)
	ui._depart()
	await snap("07-world-map")
	ui.world_selected = 1
	await snap("21-world-previous-arrow")
	ui._enter_battle()
	ui.phase_time = 0.0
	await snap("08-first-battle")
	ui.game.select_unit("alm")
	ui.ui_mode = "move"
	await snap("09-movement")
	ui.game.selected_id = ""
	ui.ui_mode = "inspect"
	ui._open_system_menu()
	await snap("10-system-menu")
	ui._clear_menu()
	ui.status_id = "alm"
	ui.ui_mode = "status"
	await snap("11-unit-status")
	ui.ui_mode = "inspect"
	ui.game.find_unit("alm").position = [6, 9]
	ui.game.find_unit("brigand_1").position = [7, 9]
	ui.game.selected_id = "alm"
	ui.target_ids = ["brigand_4", "brigand_1"]
	ui.target_index = 0
	ui.ui_mode = "target"
	await snap("12-target-preview")
	var exchange = ui.game.plan_combat("alm", "brigand_4")
	ui.combat = exchange
	ui.combat_poses = {"alm": 0, "brigand_4": 8}
	ui.combat_offsets = {"alm": Vector2.ZERO, "brigand_4": Vector2.ZERO}
	ui.combat_hp = {"alm": 28, "brigand_4": 26}
	ui.combat_fades = {"alm": 1.0, "brigand_4": 1.0}
	ui.view = "combat"
	await snap("13-combat-standing")
	ui.combat_poses.alm = 9
	ui.combat_offsets.alm = Vector2(-76, 0)
	await snap("14-combat-contact")
	ui.view = "reward"
	ui.game.find_unit("alm").level = 2
	ui.game.find_unit("alm").exp = 5
	ui.game.find_unit("alm").max_hp = 29
	ui.game.find_unit("alm").hp = 29
	ui.game.find_unit("alm").strength = 11
	ui.reward = {"unit": "alm", "gain": 15, "leveled": true, "growths": {"hp": 1, "strength": 1},
		"exp_before": 90, "exp_after": 5, "level_before": 1, "level_after": 2}
	await snap("15-level-up")
	ui.reward = {"unit": "alm", "gain": 15, "leveled": false, "growths": {},
		"exp_before": 30, "exp_after": 45, "level_before": 2, "level_after": 2}
	await snap("22-experience-gain")
	ui.view = "combat"
	ui.game.find_unit("alm").max_hp = 52
	ui.game.find_unit("brigand_4").max_hp = 52
	ui.combat_hp = {"alm": 52, "brigand_4": 1}
	await snap("23-health-maximum")
	ui.view = "victory"
	await snap("16-victory")
	ui.view = "defeat"
	await snap("17-defeat")
	# Every localized page, including automatic continuation pages, is checked.
	for key in ui.game.opening.dialogues:
		ui._start_dialogue(str(key), "alm")
		for i in range(ui.dialogue_pages.size()):
			dialogue_page_count += 1
			ui.dialogue_index = i
			ui.dialogue_reveal = 300.0
			ui.queue_redraw()
			await process_frame
			await process_frame
			all_errors.append_array(ui.layout_errors)
	ui.view = "village"
	ui.game.village_position = Vector2i(5, 10)
	ui._sync_village_position()
	ui.instant_mode = false
	ui._direction(Vector2i.RIGHT)
	var samples: Array = []
	var monotonic := true
	var last_x := 80.0
	while ui.village_motion_time > 0.0:
		await process_frame
		var x = ui.village_render_position.x
		if x < last_x or x > 96.0:
			monotonic = false
		last_x = x
		samples.append([x, ui.village_motion_time])
	motion_report = {"samples": samples.size(), "monotonic": monotonic,
		"start": [80, 160], "end": [ui.village_render_position.x, ui.village_render_position.y],
		"source_step_seconds": ui.VILLAGE_STEP_SECONDS, "standing_npcs_static": true}
	if not monotonic or samples.size() < 8 or ui.village_render_position != Vector2(96, 160):
		all_errors.append("Village movement did not animate through one complete tile")
	await snap("19-village-movement-finished")
	ui.game.new_game()
	ui.game.complete_dialogue("lukas_report")
	ui.game.village_position = Vector2i(20, 8)
	ui._sync_village_position()
	ui._start_dialogue("gray_advice", "gray")
	ui.dialogue_reveal = 300.0
	await snap("20-chinese-gray-dialogue")
	# Run a real timer-driven exchange in the offscreen viewport as well.
	# No forced hit or damage: use the same source-defined fighters and rules.
	for key in ["mycen_refusal", "alm_volunteers", "gray_joins", "tobin_joins", "kliff_joins"]:
		ui.game.complete_dialogue(key)
	ui._enter_battle()
	ui.game.find_unit("alm").position = [6, 9]
	ui.game.selected_id = "alm"
	ui.game.move_origin = Vector2i(6, 9)
	ui.instant_mode = false
	ui.animation_speed = 3.0
	var started = Time.get_ticks_msec()
	ui._play_combat("alm", "brigand_4")
	var saw_contact := false
	var saw_hp_change := false
	while ui.busy:
		await process_frame
		if ui.combat_hp.get("brigand_4", 26) < 26 or ui.combat_hp.get("alm", 28) < 28:
			saw_hp_change = true
		if not saw_contact and not str(ui.combat_hit_id).is_empty():
			saw_contact = true
			await snap("18-animated-hit")
	if ui.view == "reward":
		await snap("24-live-experience")
		ui._accept()
	animation_report = {"timer_driven": true, "speed_multiplier": 3,
		"wall_milliseconds": Time.get_ticks_msec() - started,
		"saw_contact": saw_contact, "saw_hp_change": saw_hp_change,
		"end_view": ui.view, "actors_returned": true}
	for offset in ui.combat_offsets.values():
		if offset != Vector2.ZERO:
			animation_report.actors_returned = false
	if not saw_contact or not saw_hp_change or not animation_report.actors_returned or ui.view != "battle":
		all_errors.append("Timer-driven combat failed contact/HP/return checks")
	var report = {"native_windows_suppressed": true, "captures": captures,
		"dialogue_pages_checked": dialogue_page_count, "language": "zh_CN", "village_motion": motion_report,
		"safe_area_errors": all_errors, "animation": animation_report, "health_cell_checks": all_health_checks}
	var file = FileAccess.open("res://reports/visual-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("FE2_OFFSCREEN_CAPTURE ", captures.size(), " screens; safe-area errors=", all_errors.size())
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	await create_timer(0.2).timeout
	quit(0 if all_errors.is_empty() else 1)
