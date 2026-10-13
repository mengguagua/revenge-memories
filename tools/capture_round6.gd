extends SceneTree
## Only the previously unreviewed world long-menu branch; no old UI recaptures.
const SAVE := "res://reports/test-round6-capture-save.json"
var ui
var viewport: SubViewport
var captures: Array = []
var errors: Array = []
var before := false

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		quit(1)
		return
	before = OS.get_cmdline_user_args().has("--before")
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
		errors.append("Missing actual menu action " + action)
		return
	ui.menu_selected = ui.menu_actions.find(action)
	key(KEY_Z)

func click(point: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.position = point
	ui._input(event)

func snap(id: String, operation: String) -> void:
	ui.phase_time = 0
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var pixels: Image = viewport.get_texture().get_image()
	var path := "res://reports/screenshots/round6-" + id + ".png"
	if pixels.save_png(path) != OK: errors.append("Screenshot failed " + id)
	for error in ui.layout_errors: errors.append(id + ": " + str(error))
	captures.append({"id": id, "path": path, "operation": operation, "menu_context": ui.menu_context,
		"scroll": ui.menu_scroll, "selected": ui.menu_selected, "items": ui.menu_items.duplicate(),
		"safe_area_errors": ui.layout_errors.duplicate(), "pixels": [256, 240],
		"bytes": FileAccess.get_file_as_bytes(path).size()})

func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256, 240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	ui.instant_mode = true
	viewport.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.game.new_game()
	ui.game.recruit("lukas")
	ui.game.mode = "world"
	ui.view = "world"
	for i in range(40): ui.game.convoy.alm.append(2)
	ui.game.convoy.alm[10] = 57
	ui.game.convoy.alm[20] = 17
	key(KEY_S)
	choose("camp:convoy")
	choose("camp:withdraw")
	if before:
		await snap("01-before-long-list", "S → 仓库 → 领取道具；旧下箭头点击会确认未显示的第11项")
		var rect: Rect2 = ui._menu_rect()
		click(rect.position + Vector2(rect.size.x - 12, rect.size.y - 12))
		captures[0].arrow_result_context = ui.menu_context
		captures[0].arrow_result_item_index = ui.camp_first
	else:
		for _i in range(2):
			var rect: Rect2 = ui._menu_rect()
			click(rect.position + Vector2(rect.size.x - 16, rect.size.y - 20))
		await snap("02-after-visible-page", "两次点击下箭头 → 第21-30项；没有进入领取确认或改变库存")
		if OS.get_cmdline_user_args().has("--page-only"):
			# Re-render only the range label whose missing source glyph was fixed.
			var previous = ui.game.read_json("res://reports/round6-after-visual-verification.json")
			for record in previous.get("captures", []):
				if record.id == "03-after-received-item": captures.append(record)
		else:
			var rect: Rect2 = ui._menu_rect()
			click(rect.position + Vector2(40, 24))
			choose("camp:withdraw_member:alm")
			ui.game.save_game()
			key(KEY_S)
			choose("camp:roster")
			choose("camp:status:alm")
			ui.notice_time = 0
			await snap("03-after-received-item", "点击可见第21项法尔西昂 → 阿尔姆领取 → 部队状态核对实际装备")
	var path := "res://reports/round6-" + ("before" if before else "after") + "-visual-verification.json"
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify({"captures": captures, "errors": errors, "background_guard": true,
		"user_save_accessed": false, "previous_round_screens_recaptured": false,
		"limits": "Isolated40-item world inventory checkpoint; no natural acquisition or full accessibility claim."}, "  ") + "\n")
	file.close()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	print("ROUND6 CAPTURE: ", captures.size(), " screens, errors=", errors)
	quit(0 if errors.is_empty() else 1)
