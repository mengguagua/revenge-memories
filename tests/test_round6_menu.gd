extends SceneTree
## New long-menu pointer branch and battle-menu frame click; no campaign rerun.
const SAVE := "res://reports/test-round6-menu-save.json"
const State = preload("res://core/game_state.gd")
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

func click(point: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.position = point
	ui._input(event)

func choose(action: String) -> void:
	check(ui.menu_actions.has(action), "Actual menu offers " + action)
	if not ui.menu_actions.has(action): return
	ui.menu_selected = ui.menu_actions.find(action)
	key(KEY_Z)

func setup_world(count: int) -> void:
	ui.game.new_game()
	ui.game.recruit("lukas")
	ui.game.mode = "world"
	ui.view = "world"
	ui.busy = false
	ui.batch_running = false
	ui._clear_menu()
	for i in range(count): ui.game.convoy.alm.append(2)
	if count > 10: ui.game.convoy.alm[10] = 57
	if count > 20: ui.game.convoy.alm[20] = 17
	key(KEY_S)
	choose("camp:convoy")
	choose("camp:withdraw")

func down_arrow() -> Vector2:
	var rect: Rect2 = ui._menu_rect()
	return rect.position + Vector2(rect.size.x - 16, rect.size.y - 20)

func up_arrow() -> Vector2:
	var rect: Rect2 = ui._menu_rect()
	return rect.position + Vector2(16, rect.size.y - 20)

func test_inventory_pointer() -> void:
	setup_world(40)
	var before := JSON.stringify(ui.game.convoy)
	# Legacy down-arrow coordinates are inside the new footer hit zone.
	var rect: Rect2 = ui._menu_rect()
	click(rect.position + Vector2(rect.size.x - 12, rect.size.y - 12))
	check(ui.menu_context == "stored_items" and ui.menu_scroll == 10, "Down arrow scrolls instead of confirming hidden item11")
	check(JSON.stringify(ui.game.convoy) == before and ui.camp_first.is_empty(), "Page navigation neither commits nor stages an item choice")
	if ui.menu_context != "stored_items":
		scenarios.append("Legacy down-arrow hit incorrectly selects unseen item")
		return
	click(down_arrow())
	check(ui.menu_scroll == 20 and ui.menu_selected == 20, "Second page step exposes actual Falchion item21")
	click(up_arrow())
	check(ui.menu_scroll == 10, "Up arrow scrolls back through same list")
	click(down_arrow())
	click(down_arrow())
	check(ui.menu_scroll == 30, "Forty-item convoy reaches final ten entries")
	click(down_arrow())
	check(ui.menu_context == "stored_items" and ui.menu_scroll == 30, "Inactive down-arrow region cannot confirm an unseen entry")
	click(up_arrow())
	rect = ui._menu_rect()
	click(rect.position + Vector2(40, 24))
	check(ui.menu_context == "camp_members" and ui.camp_first == "20", "Visible first row binds exact stored index20")
	choose("camp:withdraw_member:alm")
	check(ui.game.roster.alm.item_id == 17 and ui.game.convoy.alm.size() == 39, "Actual recipient receives clicked Falchion with one inventory removal")
	check(ui.game.convoy.alm[10] == 57, "Unseen Steel lance is not taken by a scroll action")
	check(ui.game.save_game(), "Committed inventory action saves to isolated checkpoint")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.roster.alm.item_id == 17 and loaded.convoy.alm.size() == 39, "Receipt persists through production save/load")
	scenarios.append("Real S/convoy/withdraw → pointer page controls → visible item21 → Alm receipt → save/load")

func test_list_boundaries() -> void:
	for count in [1, 10, 11, 17, 40]:
		setup_world(count)
		var rect: Rect2 = ui._menu_rect()
		var original: Array = ui.menu_actions.duplicate()
		click(rect.position + Vector2(12, 10))
		check(ui.menu_actions == original and ui.menu_context == "stored_items", "Top frame padding cannot confirm a row at count%d" % count)
		click(rect.position + Vector2(40, rect.size.y - 11))
		check(ui.menu_actions == original and ui.menu_context == "stored_items", "Bottom/footer padding cannot select hidden content at count%d" % count)
		if count > 10:
			click(down_arrow())
			check(ui.menu_scroll > 0 and ui.menu_selected >= ui.menu_scroll and ui.menu_selected < mini(ui.menu_scroll + 10, count), "Partial/final page keeps selected row visible at count%d" % count)
		key(KEY_X)
		check(ui.menu_items.is_empty() and ui.view == "world", "Page cancellation returns to world at count%d" % count)
	setup_world(40)
	key(KEY_UP)
	check(ui.menu_selected == 39 and ui.menu_scroll == 30, "Keyboard wrap reaches final item and reveals matching last page")
	key(KEY_DOWN)
	check(ui.menu_selected == 0 and ui.menu_scroll == 0, "Keyboard wrap returns to first item/page")
	scenarios.append("1/10/11/17/40-row pointer safe zones, partial pages, keyboard wrap and cancel")

func test_battle_frame() -> void:
	ui.game.new_game()
	ui.game.recruit("lukas")
	ui.game.world_node = 1
	ui.game.previous_world_node = 49
	ui._enter_battle(1)
	ui.game.story_events.clear()
	ui.busy = false
	ui.batch_running = false
	key(KEY_S)
	var before := JSON.stringify(ui.game.units)
	var rect: Rect2 = ui._menu_rect()
	click(rect.position + Vector2(16, 10))
	check(ui.menu_context == "system" and ui.game.turn == 1 and ui.game.phase == "player", "Clicking battle-menu frame cannot silently end turn")
	check(JSON.stringify(ui.game.units) == before, "Decorative frame click causes no enemy actions or HP changes")
	key(KEY_X)
	check(ui.view == "battle" and ui.ui_mode == "inspect" and not ui.busy and not ui.batch_running, "Dismissed frame probe leaves selectable source battle")
	scenarios.append("Source battle S-menu frame click → no hidden end-turn commitment")

func test_loot_pointer() -> void:
	ui.game.new_game()
	ui.game.recruit("lukas")
	ui.game.world_node = 1
	ui._enter_battle(1)
	ui.game.story_events.clear()
	ui.busy = false
	ui.batch_running = false
	var alm: Dictionary = ui.game.find_unit("alm")
	alm.item_id = 57
	for i in range(40): ui.game.convoy.alm.append(2)
	var enemy: Dictionary = ui.game.find_unit("brigand_1")
	enemy.item_id = 17
	enemy.hp = 0
	var record: Dictionary = ui.Inventory.on_death(ui.game, enemy, alm)
	check(record.get("destination") == "pending", "Occupied recipient with full convoy requires actual loot choice")
	ui._show_loot_menu()
	var rect: Rect2 = ui._menu_rect()
	click(rect.position + Vector2(40, 10))
	check(ui.view == "loot" and ui.game.flags.pending_loot.size() == 1 and alm.item_id == 57, "Loot top frame cannot stage discard")
	click(rect.position + Vector2(40, 40))
	check(ui.view == "loot_confirm" and ui.loot_choice == "discard_old", "Visible second loot row stages the displayed replacement")
	rect = ui._menu_rect()
	click(rect.position + Vector2(40, rect.size.y - 11))
	check(ui.view == "loot_confirm" and ui.game.flags.pending_loot.size() == 1 and alm.item_id == 57, "Confirmation bottom frame cannot discard either item")
	key(KEY_X)
	check(ui.view == "loot" and ui.game.flags.pending_loot.size() == 1 and alm.item_id == 57, "Cancelling pointer confirmation retains both items")
	rect = ui._menu_rect()
	click(rect.position + Vector2(40, 40))
	rect = ui._menu_rect()
	click(rect.position + Vector2(40, 40))
	check(ui.view == "battle" and ui.game.flags.pending_loot.is_empty() and alm.item_id == 17, "Visible confirm row commits one explicit discard/replacement")
	check(ui.game.convoy.alm.size() == 40, "Pointer replacement preserves full convoy")
	scenarios.append("New shared mouse hit detector: full-convoy loot → frame ignored → visible replace → cancel → explicit confirm")

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	ui.instant_mode = true
	root.add_child(ui)
	await process_frame
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	var loot_only := OS.get_cmdline_user_args().has("--loot-only")
	if loot_only:
		test_loot_pointer()
	else:
		test_inventory_pointer()
		test_list_boundaries()
		test_battle_frame()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var before_run := OS.get_cmdline_user_args().has("--before")
	var report_path := "res://reports/round6-loot-verification.json" if loot_only else "res://reports/round6-menu-" + ("before" if before_run else "after") + "-verification.json"
	var file := FileAccess.open(report_path, FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures, "scenarios": scenarios,
		"user_save_accessed": false, "scope": "New long-menu pointer hit regions and source battle-menu frame; isolated40-item fixture.",
		"limits": "Instant timing and checkpoint inventory; no broad campaign replay."}, "  ") + "\n")
	file.close()
	print("ROUND6 MENU: ", checks, " checks, ", failures.size(), " failures")
	quit(0 if failures.is_empty() else 1)
