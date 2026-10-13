extends SceneTree
## Capture changed controller states in a guarded offscreen viewport.
const State = preload("res://core/game_state.gd")
const SAVE := "res://reports/spot-capture-save.json"

class RecordingScene extends "res://core/main.gd":
	var capture_contact: Callable
	var in_recoil := false
	var captured_recoil := false
	func _contact(event: Dictionary) -> void:
		in_recoil = int(event.get("self_damage", 0)) > 0
		await super._contact(event)
		in_recoil = false
	func _wait(seconds: float) -> void:
		if in_recoil and not captured_recoil:
			captured_recoil = true
			await capture_contact.call("05-dark-sword-recoil")
		await super._wait(seconds)

var viewport: SubViewport
var ui
var captures: Array = []
var errors: Array[String] = []

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		quit(1)
		return
	call_deferred("run")

func snap(label: String) -> void:
	ui.phase_time = 0
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var path := "res://reports/screenshots/spot-" + label + ".png"
	viewport.get_texture().get_image().save_png(path)
	for error in ui.layout_errors: errors.append(label + ": " + str(error))
	captures.append({"id": label, "path": path, "safe_area_errors": ui.layout_errors.duplicate()})

func setup_menus() -> void:
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
	var mage: Dictionary = ui.game.find_unit("mae")
	var origin := State.pos(mage)
	ui.game.cursor = origin
	ui._accept()
	for cell in ui.game.reachable(mage).costs:
		if cell == origin or not ui.game.can_stop(mage, cell): continue
		if not ui.game.living("player").any(func(other): return other.id != mage.id and absi(State.pos(other).x - cell.x) + absi(State.pos(other).y - cell.y) == 1): continue
		ui.game.cursor = cell
		ui._accept()
		return
	errors.append("No legal moved mage with adjacent ally")

func choose(action: String) -> void:
	var index: int = ui.menu_actions.find(action)
	if index < 0:
		errors.append("Missing action " + action)
		return
	ui.menu_selected = index
	ui._accept()

func capture_recoil() -> void:
	var game = ui.game
	game.new_game()
	game.chapter = 3
	game.route = "celica"
	game.party = []
	game.recruit("celica")
	game.recruit("deen")
	var grown: Dictionary = game.roster.deen
	var growth: Dictionary = game.Rules.growth_result(grown, [99, 99, 99, 99, 1, 99])
	grown.skill = int(grown.skill) + int(growth.skill)
	grown.level = int(grown.level) + 1
	grown.item_id = 14
	game.world_armies.clear()
	game.world_node = 25
	game.start_battle(25, [], true)
	game.story_events.clear()
	var hero: Dictionary = game.find_unit("deen")
	var target: Dictionary = game.find_unit("g25_01")
	for direction in [Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP]:
		var cell: Vector2i = State.pos(target) + direction
		if game.in_bounds(cell) and game.can_stop(hero, cell) and game.movement_cost(hero, cell) < 255:
			hero.position = [cell.x, cell.y]
			break
	var seed := -1
	for value in range(256):
		game.rng_state = value
		var exchange: Dictionary = game.plan_combat("deen", "g25_01")
		if exchange.events.any(func(event): return event.attacker == "deen" and int(event.self_damage) > 0 and bool(event.hit)):
			seed = value
			break
	if seed < 0:
		errors.append("No source RNG recoil")
		return
	game.rng_state = seed
	ui.view = "battle"
	ui.busy = false
	ui.batch_running = true
	ui.ui_mode = "inspect"
	ui._clear_menu()
	await ui._play_combat("deen", "g25_01")
	if not ui.captured_recoil: errors.append("Recoil contact was not captured")

func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256, 240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = RecordingScene.new()
	ui.instant_mode = true
	ui.game.save_path = SAVE
	ui.capture_contact = snap
	viewport.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	setup_menus()
	choose("magic")
	await snap("01-magic-menu")
	ui._cancel()
	await snap("02-magic-cancel-action-menu")
	choose("exchange")
	await snap("03-exchange-menu")
	ui._cancel()
	await snap("04-exchange-cancel-action-menu")
	await capture_recoil()
	var report := {"captures": captures, "safe_area_errors": errors,
		"background_guard": true, "user_save_accessed": false,
		"scope": "Actual keyboard submenu cancellation and native Dark Sword recoil contact; original assets, guarded SubViewport pixels."}
	var file := FileAccess.open("res://reports/spot-visual-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	file.close()
	ui.audio.stop_all()
	ui.queue_free()
	await create_timer(0.2).timeout
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	print("SPOT CAPTURE: ", captures.size(), " screens, errors=", errors)
	quit(0 if errors.is_empty() else 1)
