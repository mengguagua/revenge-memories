extends SceneTree
## Every render runs with the existing prelaunch window/focus guard.
var viewport: SubViewport
var ui
var captures: Array = []
var errors: Array = []
var motion: Array = []
var strike_done := false

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("Use tools/background_capture/run.sh before any graphics launch")
		quit(1)
		return
	call_deferred("run")

func snap(id: String) -> void:
	ui.queue_redraw()
	for _i in range(3):
		await process_frame
	RenderingServer.force_draw(false)
	var image = viewport.get_texture().get_image()
	var path = "res://reports/screenshots/second-" + id + ".png"
	image.save_png(path)
	errors.append_array(ui.layout_errors)
	captures.append({"id": id, "path": path, "camera": [ui.battle_camera.x, ui.battle_camera.y], "safe_area_errors": ui.layout_errors.duplicate()})

func setup_stage() -> void:
	ui.game.new_game()
	ui.game.party = ["alm", "lukas", "gray", "tobin", "kliff"]
	ui.game.start_battle()
	for enemy in ui.game.living("enemy"):
		enemy.hp = 0
	ui.game.battle_outcome = "victory"
	ui.game.complete_battle()
	ui._enter_battle(2)
	ui.phase_time = 0.0
	ui._clear_menu()

func strike(event: Dictionary) -> void:
	await ui._animate_strike(event)
	strike_done = true

func probe_arrow(side: String, hit: bool) -> void:
	setup_stage()
	var archer = ui.game.find_unit("archer_1")
	var alm = ui.game.find_unit("alm")
	archer.side = side
	alm.side = "enemy" if side == "player" else "player"
	archer.position = [11, 12]
	alm.position = [13, 12]
	ui.combat = {"attacker": "archer_1", "defender": "alm"}
	ui.combat_poses = {"archer_1": 0, "alm": 0}
	ui.combat_offsets = {"archer_1": Vector2.ZERO, "alm": Vector2.ZERO}
	ui.combat_hp = {"archer_1": archer.hp, "alm": alm.hp}
	ui.combat_fades = {"archer_1": 1.0, "alm": 1.0}
	ui.combat_hit_id = ""
	ui.combat_hit_time = 0.0
	ui.view = "combat"
	ui.instant_mode = false
	ui.animation_speed = 1.0
	ui.busy = true
	strike_done = false
	var before = int(alm.hp)
	var event = {"attacker": "archer_1", "defender": "alm", "hit": hit, "critical": false,
		"damage": 1 if hit else 0, "hp_before": before, "hp_after": before - (1 if hit else 0)}
	strike(event)
	var samples: Array = []
	var arrow_seen := false
	var contact_seen := false
	var winding_seen := false
	var returned := true
	var deadline = Time.get_ticks_msec() + 10000
	while not strike_done and Time.get_ticks_msec() < deadline:
		await process_frame
		if ui.combat_offsets.archer_1 != Vector2.ZERO:
			returned = false
		if not winding_seen and ui.combat_poses.archer_1 == 1:
			winding_seen = true
			await snap(side + ("-hit" if hit else "-miss") + "-draw-bow")
		if not ui.combat_projectile.is_empty() and ui.combat_projectile.visible:
			var pos: Vector2 = ui.combat_projectile.position
			samples.append([pos.x, pos.y])
			if not arrow_seen:
				arrow_seen = true
				await snap(side + ("-hit" if hit else "-miss") + "-arrow")
		if not contact_seen and (ui.combat_hit_id == "alm" or ui.combat_message == "未命中"):
			contact_seen = true
			await snap(side + ("-hit" if hit else "-miss") + "-contact")
	var correct_direction := true
	for i in range(1, samples.size()):
		if (side == "enemy" and samples[i][0] < samples[i - 1][0]) or (side == "player" and samples[i][0] > samples[i - 1][0]):
			correct_direction = false
	var ok = strike_done and winding_seen and arrow_seen and contact_seen and returned and correct_direction and int(alm.hp) == int(event.hp_after) and ui.combat_projectile.is_empty()
	if not ok:
		errors.append("Ranged render/contact failed: " + side + " hit=" + str(hit))
	motion.append({"side": side, "hit": hit, "samples": samples, "stationary_shooter": returned,
		"correct_direction": correct_direction, "contact_seen": contact_seen, "completed": strike_done,
		"hp_before": before, "hp_after": alm.hp, "pass": ok})
	ui.busy = false
	ui.instant_mode = true

func run() -> void:
	DirAccess.make_dir_recursive_absolute("res://reports/screenshots")
	viewport = SubViewport.new()
	viewport.size = Vector2i(256, 240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	viewport.add_child(ui)
	ui.game.save_path = "res://reports/second-capture-save.json"
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.set_physics_process(false)
	ui.instant_mode = true
	setup_stage()
	await snap("01-deployment")
	ui._continue_world()
	ui.world_selected = 2
	await snap("02-world-next-node")
	ui.view = "battle"
	for cell in [Vector2i(3, 14), Vector2i(23, 21), Vector2i(0, 0), Vector2i(11, 12)]:
		ui.game.cursor = cell
		ui._focus_battle(cell, true)
		await snap("scroll-" + str(cell.x) + "-" + str(cell.y))
	ui.status_id = "archer_1"
	ui.ui_mode = "status"
	await snap("03-archer-status")
	ui.ui_mode = "move"
	ui.game.select_unit("alm")
	ui.game.cursor = ui.game.pos(ui.game.find_unit("alm"))
	ui._focus_battle(ui.game.cursor, true)
	await snap("04-movement")
	ui.game.selected_id = "archer_1"
	ui.game.find_unit("archer_1").side = "player"
	ui.game.find_unit("alm").side = "enemy"
	ui.game.find_unit("alm").position = [13, 12]
	ui.target_ids = ["alm"]
	ui.target_index = 0
	ui.game.cursor = Vector2i(13, 12)
	ui._focus_battle(ui.game.cursor)
	ui.ui_mode = "target"
	await snap("05-no-counter-preview")
	await probe_arrow("enemy", true)
	await probe_arrow("player", true)
	await probe_arrow("enemy", false)
	setup_stage()
	for unit in ui.game.living("enemy"):
		unit.hp = 0
	ui.game.battle_outcome = "victory"
	ui._show_result()
	await snap("06-victory")
	ui._accept()
	await snap("07-result-menu")
	ui._menu_action("continue_world", "result")
	await snap("08-world-cleared")
	var report = {"guarded_offscreen": true, "captures": captures, "ranged_animation": motion, "safe_area_errors": errors}
	var file = FileAccess.open("res://reports/second-stage-visual-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("FE2_SECOND_CAPTURE ", captures.size(), " screens; errors=", errors.size())
	ui.audio.stop_all()
	ui.queue_free()
	await create_timer(0.3).timeout
	DirAccess.remove_absolute("res://reports/second-capture-save.json")
	DirAccess.remove_absolute("res://reports/second-capture-save.json.tmp")
	quit(0 if errors.is_empty() else 1)
