extends SceneTree

# Offscreen-only regression probe for mirrored combat sprites and both attack sides.
var viewport: SubViewport
var ui
var errors: Array = []
var samples: Array = []
var attack_done := false
var attack_contact := false

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("Use tools/background_capture/run.sh; no unguarded graphics launch")
		quit(1)
		return
	call_deferred("run")

func fresh_combat(player_id: String = "alm") -> void:
	ui.game.new_game()
	ui.game.party = ["alm", "lukas", "kliff", "tobin", "gray"]
	ui.game.start_battle()
	ui.game.find_unit(player_id).position = [6, 9]
	ui.combat = ui.game.plan_combat(player_id, "brigand_4")
	ui.combat_poses.clear()
	ui.combat_offsets.clear()
	ui.combat_hp.clear()
	ui.combat_fades.clear()
	for id in [player_id, "brigand_4"]:
		var unit = ui.game.find_unit(id)
		ui.combat_poses[id] = int(ui._battle_sprite(unit).sequences.idle[0])
		ui.combat_offsets[id] = Vector2.ZERO
		ui.combat_hp[id] = int(unit.hp)
		ui.combat_fades[id] = 1.0
	ui.combat_hit_id = ""
	ui.combat_hit_time = 0.0
	ui.combat_shake = 0.0
	ui.view = "combat"

func capture(id: String) -> Image:
	ui.queue_redraw()
	for i in range(3):
		await process_frame
	RenderingServer.force_draw(false)
	var image: Image = viewport.get_texture().get_image()
	image.save_png("res://reports/screenshots/combat-position-" + id + ".png")
	return image

func compare_stage(image: Image, player_id: String) -> int:
	var expected = Image.create(256, 128, false, Image.FORMAT_RGBA8)
	expected.fill(Color.BLACK)
	for id in ["brigand_4", player_id]:
		var unit = ui.game.find_unit(id)
		var sprite = ui._battle_sprite(unit)
		var atlas: Image = ui._tex(sprite.path).get_image()
		var size = Vector2i(sprite.frame_size[0], sprite.frame_size[1])
		var frame: Image = atlas.get_region(Rect2i(int(ui.combat_poses[id]) * size.x, 0, size.x, size.y))
		if unit.side == "enemy":
			frame.flip_x()
		var x = 64 if unit.side == "enemy" else 176
		var at = Vector2i(x - int(sprite.anchor[0]), 128 - int(sprite.anchor[1]))
		expected.blend_rect(frame, Rect2i(Vector2i.ZERO, size), at)
	var mismatches := 0
	for y in range(128):
		for x in range(256):
			if image.get_pixel(x, y) != expected.get_pixel(x, y):
				mismatches += 1
	return mismatches

func strike(event: Dictionary) -> void:
	await ui._animate_strike(event)
	attack_done = true

func check_attack(attacker_id: String, defender_id: String, player_id: String) -> void:
	fresh_combat(player_id)
	attack_done = false
	attack_contact = false
	var target = ui.game.find_unit(defender_id)
	var event = {"attacker": attacker_id, "defender": defender_id, "hit": true,
		"critical": false, "damage": 1, "hp_before": int(target.hp), "hp_after": int(target.hp) - 1}
	strike(event)
	var max_x := 0.0
	var min_x := 0.0
	var max_y := 0.0
	var min_y := 0.0
	var contact_offset := Vector2.ZERO
	var contact_pose := -1
	var deadline = Time.get_ticks_msec() + 10000
	while not attack_done and Time.get_ticks_msec() < deadline:
		await create_timer(1.0 / 120.0).timeout
		var offset: Vector2 = ui.combat_offsets[attacker_id]
		max_x = maxf(max_x, offset.x)
		min_x = minf(min_x, offset.x)
		max_y = maxf(max_y, offset.y)
		min_y = minf(min_y, offset.y)
		if not attack_contact and not str(ui.combat_hit_id).is_empty():
			attack_contact = true
			contact_offset = offset
			contact_pose = int(ui.combat_poses[attacker_id])
			await capture(attacker_id + "-contact")
	var returned: bool = ui.combat_offsets[attacker_id] == Vector2.ZERO
	if not attack_done or not attack_contact or not returned:
		errors.append(attacker_id + " failed contact/return")
	if attacker_id == "brigand_4" and max_x <= 0.0:
		errors.append("Enemy must advance right toward player")
	if attacker_id != "brigand_4" and min_x >= 0.0:
		errors.append("Player must advance left toward enemy")
	samples.append({"attacker": attacker_id, "contact_pose": contact_pose,
		"contact_offset": [contact_offset.x, contact_offset.y],
		"x_range": [min_x, max_x], "y_range": [min_y, max_y], "returned": returned,
		"contact_seen": attack_contact, "completed": attack_done})

func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256, 240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	viewport.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.game.save_path = "res://reports/combat-position-test-save.json"
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.animation_speed = 3.0
	for id in ["alm", "lukas", "kliff"]:
		fresh_combat(id)
		var image: Image = await capture(id + "-standing")
		var mismatch = compare_stage(image, id)
		samples.append({"standing_player": id, "expected_enemy_anchor": [64, 128],
			"expected_player_anchor": [176, 128], "stage_pixel_mismatches": mismatch})
		if mismatch != 0:
			errors.append(id + " standing pixels differ from anchored mirrored frames: " + str(mismatch))
	for id in ["alm", "lukas", "kliff"]:
		await check_attack(id, "brigand_4", id)
	await check_attack("brigand_4", "alm", "alm")
	var report = {"guarded_offscreen": true, "samples": samples, "errors": errors,
		"source": "https://github.com/godotengine/godot/blob/4.6/servers/rendering/renderer_canvas_cull.cpp#L1492-L1511",
		"negative_destination_width_behavior": "Horizontal UV flip; destination position remains unchanged"}
	var file = FileAccess.open("res://reports/combat-position-review.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print(JSON.stringify(report))
	ui.queue_free()
	viewport.queue_free()
	await process_frame
	quit(0 if errors.is_empty() else 1)
