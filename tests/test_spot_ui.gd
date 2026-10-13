extends SceneTree
## Regression probes use the real keyboard controller and the source graveyard map.
const State = preload("res://core/game_state.gd")
const SAVE = "res://reports/test-spot-ui-save.json"
var ui
var checks := 0
var failures: Array[String] = []
func _initialize(): call_deferred("run")
func check(ok: bool, message: String):
	checks += 1
	if not ok: failures.append(message); push_error(message)
func setup():
	ui.game.new_game()
	ui.game.chapter = 2
	ui.game.route = "celica"
	ui.game.party = []
	for id in ["celica", "mae", "boey", "genny"]: ui.game.recruit(id)
	ui.game.give_item(57)
	ui.game.exchange_items("celica", "mae")
	ui.game.world_node = 8
	ui.game.start_battle(8, [8], true)
	ui.game.story_events.clear()
	ui.view = "battle"
	ui.ui_mode = "inspect"
	ui.busy = false
	ui.batch_running = false
	ui._clear_menu()
func choose(action: String):
	check(ui.menu_actions.has(action), "Actual menu exposes " + action)
	if not ui.menu_actions.has(action): return
	ui.menu_selected = ui.menu_actions.find(action)
	ui._accept()
func move_mae_to_neighbor() -> Vector2i:
	var unit = ui.game.find_unit("mae")
	var original = State.pos(unit)
	ui.game.cursor = original
	ui._accept()
	check(ui.ui_mode == "move" and ui.game.selected_id == "mae", "Select actual Mae deployment")
	for cell in ui.game.reachable(unit).costs:
		if cell != original and ui.game.can_stop(unit, cell):
			if ui.game.living("player").any(func(other): return other.id != unit.id and absi(State.pos(other).x-cell.x)+absi(State.pos(other).y-cell.y)==1):
				ui.game.cursor = cell
				ui._accept()
				check(State.pos(unit) == cell and ui.menu_context == "unit_action", "Native move reaches action menu")
				return original
	check(false, "Source map contains an adjacent legal exchange position")
	return original
func run():
	ui = load("res://scenes/main.tscn").instantiate()
	ui.instant_mode = true
	ui.game.save_path = SAVE
	root.add_child(ui)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.set_process(false)
	ui.set_physics_process(false)
	for submenu in ["magic", "exchange"]:
		setup()
		var origin = move_mae_to_neighbor()
		var moved = State.pos(ui.game.find_unit("mae"))
		choose(submenu)
		check(ui.menu_context == submenu and not ui.menu_items.is_empty(), "Submenu opens: " + submenu)
		ui._cancel()
		check(ui.menu_context == "unit_action" and not ui.menu_items.is_empty(), "Cancel " + submenu + " returns to action menu without softlock")
		check(ui.game.selected_id == "mae" and State.pos(ui.game.find_unit("mae")) == moved, "Cancel submenu preserves tentative movement")
		ui._cancel()
		check(ui.ui_mode == "inspect" and ui.game.selected_id.is_empty() and State.pos(ui.game.find_unit("mae")) == origin, "Second cancel returns Mae to her original tile")
		check(not ui.game.find_unit("mae").acted, "Cancelling spends no action")
	setup()
	ui.game.chapter = 3
	ui.game.mode = "world"
	ui.game.route_positions.celica = 8
	ui.view = "world"
	check(ui.game.switch_route(), "Free party switches from Celica to Alm after a battle")
	check(ui.game.units.is_empty(), "World party switch drops the previous route's tactical unit cache")
	check(ui.game.save_game(), "Switched world party saves")
	var resumed = State.new()
	resumed.save_path = SAVE
	check(resumed.load_game() and resumed.route == "alm" and resumed.party[0] == "alm", "World party switch can resume without looking up the other route's tactical leader")
	ui.game.flags.celica_captive = true
	var before = JSON.stringify({"route":ui.game.route,"party":ui.game.party,"world":ui.game.world_node})
	check(not ui.game.switch_route(), "Captured Celica cannot be selected as active world party")
	check(before == JSON.stringify({"route":ui.game.route,"party":ui.game.party,"world":ui.game.world_node}), "Rejected switch is non-mutating")
	ui._open_camp_menu()
	check(not ui.menu_actions.has("camp:switch"), "World menu does not offer captured party selection")
	ui._clear_menu()
	var report = {"checks":checks,"failures":failures,"scope":"actual map8 keyboard selection, movement, magic/exchange cancellation; isolated save"}
	var out = FileAccess.open("res://reports/spot-ui-verification.json", FileAccess.WRITE)
	out.store_string(JSON.stringify(report,"\t"));out.close()
	print("SPOT UI ",checks," checks, ",failures.size()," failures")
	ui.audio.stop_all()
	ui.queue_free()
	await create_timer(0.1).timeout
	DirAccess.remove_absolute(SAVE)
	quit(0 if failures.is_empty() else 1)
