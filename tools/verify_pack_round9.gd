extends SceneTree
## Loaded by exported app outside the project; only new terrain/recovery code.
var ui
var checks := 0
var failures: Array = []
func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label)
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
		failures.append("missing action: "+action)
		return
	for _i in range(20):
		if str(ui.menu_actions[ui.menu_selected]) == action:
			key(KEY_Z)
			return
		key(KEY_DOWN)
func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = "/private/tmp/fe2-round9-pack-isolated-save.json"
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.instant_mode = true
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.game.new_game()
	ui.game.chapter = 2
	ui.game.route = "celica"
	ui.game.party = []
	ui.game.parties.celica = []
	for id in ["celica","genny","boey","mae","saber"]: ui.game.recruit(id)
	ui.game.cleared_stages = [8,9]
	ui.game.world_node = 10
	ui.game.route_positions.celica = 10
	ui.game.start_battle(10)
	ui.view = "battle"
	check(ui.game.category(Vector2i(28,19)) == 7,"exported source sea terrain resolves to water")
	check(ui.game.movement_cost(ui.game.find_unit("celica"),Vector2i(28,19)) == 255,"exported foot movement blocks water")
	check(not ui.game.needs_terrain_recovery(),"exported normal source deployment has no recovery option")
	ui.game.find_unit("celica").position = [28,19]
	ui.game.battle_start_snapshot = JSON.parse_string(JSON.stringify(ui.game.battle_start_snapshot))
	key(KEY_S); choose("terrain_retry")
	check(ui.menu_context == "terrain_retry_confirm" and ui.notice == "重试将重置本战进度","exported recovery action opens the actual loss-of-progress prompt")
	choose("terrain_retry_cancel")
	check(ui.game.find_unit("celica").position == [28,19],"exported cancel leaves off-ship suspend unchanged")
	choose("terrain_retry"); choose("retry")
	for _i in range(20):
		if ui.view == "battle_story": key(KEY_Z)
		await process_frame
	check(ui.view == "battle" and ui.game.turn == 1 and ui.game.stage_cleared(8) and ui.game.stage_cleared(9) and ui.game.pos(ui.game.find_unit("celica")) == Vector2i(20,13) and not ui.game.needs_terrain_recovery(),"exported confirmed retry restores legal original deployment")
	ui.audio.stop_all(); ui.queue_free()
	await process_frame
	await create_timer(0.15).timeout
	DirAccess.remove_absolute("/private/tmp/fe2-round9-pack-isolated-save.json")
	var file := FileAccess.open("/private/tmp/fe2-round9-package-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"battle_replays":0,"screenshots":0,"user_save_accessed":false},"  ")+"\n")
	print("ROUND9_PACKAGE checks=",checks," failures=",failures.size())
	quit(0 if failures.is_empty() else 1)
