extends SceneTree
## Directed fixtures for shared controls; distinct from real-input victory runs.
var ui
var checks := 0
var errors: Array = []
var sounds: Array = []
var stages_checked: Array = []
const OUT = "res://reports/playtest-0.3.7/"

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: errors.append(label); push_error(label)

func tap(code: int) -> void:
	var event = InputEventKey.new(); event.physical_keycode = code; event.pressed = true; ui._input(event)
	event = InputEventKey.new(); event.physical_keycode = code; ui._input(event)

func load_stage(code: String) -> void:
	var prefix = "res://reports/campaign/" if code.begins_with("M") or code in ["S11", "S12"] else "res://reports/chapter2/play/"
	ui.game.save_path = prefix + "natural-" + code + "-deployment-save.json"
	check(ui.game.load_game(), code + " genuine source loads")
	ui.game.save_path = "res://.cache/player-feedback-working.json"
	check(ui.game.retry_battle(), code + " ordinary retry enters current stage")
	ui.view = "battle"; ui.ui_mode = "inspect"; ui.busy = false; ui.batch_running = false; ui._clear_menu(); ui.phase_time = 0; ui.notice_time = 0

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	ui = load("res://scenes/main.tscn").instantiate(); root.add_child(ui); await process_frame
	ui.instant_mode = true; ui.set_process(false); ui.set_physics_process(false)
	ui.audio.sfx_played.connect(func(key): sounds.append(key))
	for code in ["M11", "M12", "M13", "M14", "M15", "S11", "S12", "F21", "F22", "F23", "F24", "F25", "F26", "S21", "S22"]:
		load_stage(code)
		var g = ui.game; var ready = g.party.filter(func(id): return not g.find_unit(str(id)).is_empty())
		var before = g.units.duplicate(true); var rng = g.rng_state
		g.cursor = g.pos(g.living("enemy")[0]); tap(KEY_E)
		check(str(g.unit_at(g.cursor).id) == str(ready[0]), code + " E locates first available ally from enemy")
		tap(KEY_E); check(str(g.unit_at(g.cursor).id) == str(ready[1]), code + " repeated E locates next ally")
		tap(KEY_Q); check(str(g.unit_at(g.cursor).id) == str(ready[0]), code + " Q locates previous ally")
		tap(KEY_Z); check(ui.ui_mode == "move", code + " locate then confirm opens movement")
		tap(KEY_E); check(ui.ui_mode == "inspect" and g.selected_id == "" and str(g.unit_at(g.cursor).id) == str(ready[1]), code + " cycle from movement cancels selection safely")
		check(g.units == before and g.rng_state == rng, code + " cycling does not move, act, heal or reroll")
		g.find_unit(str(ready[1])).acted = true
		g.cursor = g.pos(g.find_unit(str(ready[0]))); tap(KEY_E)
		check(str(g.unit_at(g.cursor).id) != str(ready[1]), code + " cycle skips acted members")
		g.find_unit(str(ready[1])).acted = false
		g.cursor = g.pos(g.find_unit(str(ready[0]))); tap(KEY_TAB); tap(KEY_RIGHT)
		check(ui.ui_mode == "status" and ui.status_id == str(ready[1]), code + " status right switches current army")
		tap(KEY_LEFT); check(ui.status_id == str(ready[0]), code + " status left returns")
		tap(KEY_LEFT); check(ui.status_id == str(ready[-1]), code + " status wraps at start")
		tap(KEY_X)
		var enemy = g.living("enemy")[0]; g.cursor = g.pos(enemy); tap(KEY_TAB); tap(KEY_RIGHT)
		check(ui.status_id == str(enemy.id), code + " enemy status cannot cycle into own army")
		tap(KEY_X)
		var cells = ui._enemy_movement_cells(enemy)
		check(not cells.is_empty(), code + " enemy movement preview available")
		var graph = g.reachable(enemy)
		for cell in cells:
			check(graph.costs.has(cell) and g.can_stop(enemy, cell) and g.movement_cost(enemy, cell) < 255, code + " red square is reachable and unoccupied " + str(cell))
		g.cursor = g.pos(enemy); ui._focus_player_leader()
		check(g.cursor == g.pos(g.find_unit(g.leader_id())), code + " player phase focuses living protagonist")
		# Isolate absence handling without producing a false campaign save or victory.
		var original = g.units.duplicate(true)
		g.units = g.units.filter(func(u): return str(u.id) != g.leader_id())
		ui._focus_player_leader()
		check(g.unit_at(g.cursor).get("side", "") == "player" and g.unit_at(g.cursor).get("controllable", true), code + " absent protagonist falls back to controllable ally")
		g.units = original
		stages_checked.append(code)
	load_stage("M11")
	var archer = ui.game.living("enemy").filter(func(u): return int(u.class_id) in [12, 13, 20])[0]
	check(ui.Rules.can_attack(ui.Rules.default_counter(archer, 1), 1), "source normal bow can counter at distance one")
	check(ui.Rules.attack_range(archer) == Vector2i(1, 3), "source normal bow range is 1..3")
	var equipped = archer.duplicate(true); equipped.item_id = 21
	check(ui.Rules.attack_range(equipped) == Vector2i(1, 5), "source holy bow range is 1..5")
	var normal = ui.graphics.map_units["class_6_enemy_acted"]; var sample = {"class_id": 6, "side": "enemy", "acted": true}
	var rest = ui._map_unit_sprite(sample)
	var a = ui._tex(normal.path).get_image(); var b = ui._tex(rest.path).get_image(); var preserved = true; var warm = 0
	for y in range(a.get_height()):
		for x in range(a.get_width()):
			var p = a.get_pixel(x, y); var q = b.get_pixel(x, y)
			if p.a != q.a or (p.r < .1 and p != q): preserved = false
			if q.a > 0 and q.r > q.g: warm += 1
	check(preserved and warm > 0, "enemy resting palette is red-grey with exact silhouette and black outlines")
	check(ui._map_unit_sprite({"class_id":6,"side":"player","acted":true}).path == "res://assets/original/graphics/map_units/class_6_ally_acted.png", "own resting palette remains neutral grey")
	ui.reward = {"unit":ui.game.leader_id(),"gain":20,"leveled":false}; ui.reward_elapsed=0; ui.view="reward"; sounds.clear()
	for tick in range(30): ui._process(1.0/60.0)
	check(sounds.has("hp_tick") and sounds.count("hp_tick") <= 6, "experience gain emits bounded original tick sounds during fill")
	ui.view="battle"; ui.ui_mode="inspect"; ui.game.selected_id=""; ui._clear_menu(); ui.game.cursor=ui.game.pos(ui.game.find_unit(ui.game.leader_id()))
	ui._open_camp_menu()
	check(ui.menu_items.has("交换装备") and ui.menu_items.has("装备行囊") and ui.menu_actions.has("new:equipment"), "camp exposes equipment, convoy and explanation")
	ui._clear_menu(); ui.hub_controller.enter_room("H01", true); tap(KEY_TAB)
	check(ui.menu_actions.has("camp:status:" + str(ui.game.party[0])), "hub status opens working member actions")
	ui.menu_selected=0; tap(KEY_Z)
	check(ui.view=="camp_status" and ui.camp_context=="hub", "hub member status retains its return context")
	tap(KEY_RIGHT); check(ui.status_id==str(ui.game.party[1]), "hub status right cycles own party")
	tap(KEY_X); check(ui.view=="hub", "hub status closes back to original room")
	var report = {"passed":errors.is_empty(), "checks":checks, "errors":errors, "stages":stages_checked, "scope":"Directed input/range/palette/audio/absence fixtures; not battle victory evidence", "experience_sound":"res://assets/original/audio/hp_tick.ogg"}
	var f=FileAccess.open(OUT+"control-checks.json",FileAccess.WRITE); f.store_string(JSON.stringify(report,"  ")); f.close()
	print("PLAYER_FEEDBACK ",JSON.stringify(report))
	ui.queue_free(); await process_frame; ui=null; quit(0 if errors.is_empty() else 1)
