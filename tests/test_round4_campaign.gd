extends SceneTree
## Round4: progression exits after source milestones, using real State and VM.
## Earlier wins are source-table checkpoints, never modified battle damage.
const State = preload("res://core/game_state.gd")
const Armies = preload("res://core/world_armies.gd")
const Scenario = preload("res://core/scenario_rules.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const SAVE := "res://reports/test-round4-campaign-save.json"
var scene
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func _run() -> void:
	_test_route_reload()
	_test_route_encounter_identity()
	scene = load("res://scenes/main.tscn").instantiate()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	_test_sluice_vm()
	_test_dragon_capture_vm()
	scene.audio.stop_all()
	scene.queue_free()
	await process_frame
	for path in [SAVE, SAVE + ".tmp", SAVE + ".bak"]:
		DirAccess.remove_absolute(path)
	var file := FileAccess.open("res://reports/round4-campaign-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,
		"scope":"Chapter2 freeze and chapter3 independent routes/entry roads after reload; probability and timeout retreats after route switching; actual allocated mobile attacker context across route switch and reload; actual Mila sluice VM, watergate chapter4 VM and north exit; actual dragon-valley trap, first Celica altar VM, saved capture checkpoint and legal resolved-wave escape road.",
		"source_contract":"bank006 L069164/L06B7C6 uses route-indexed previous-node table $6D16,X; bank007 L07A52F records first incoming attacker; bank012 L0CABD3/L0CAC05/L0CAC4B; bank013 L0DB808/L0DB83C/L0DB8DB and L0D9633; bank006 L068DFB clears dragon gate bits33 only after Celica altar capture; bank006 L06B715 excludes valley36 from permanent generator shutdown.",
		"limits":"Headless actual State/controller with source-valid milestone checkpoints for earlier resolved armies. No combat stat changes, no claim of natural full-campaign victory, no graphical rendering or frame-exact world RNG scheduling."}, "\t") + "\n")
	print("ROUND4 CAMPAIGN: %d checks, %d failures" % [checks,failures.size()])
	quit(0 if failures.is_empty() else 1)

func fresh():
	var game = State.new()
	game.save_path = SAVE
	game.new_game()
	game.recruit("lukas")
	return game

func _test_route_reload() -> void:
	var game = fresh()
	check(game.next_chapter(1), "Source first transition initializes Celica chapter2")
	game.recruit("mae")
	check(game.flags.get("scenario_alm_frozen",false) and not game.can_switch_route(), "Chapter2 intentionally keeps Alm unavailable")
	check(game.next_chapter(2), "Source reunion transition initializes both chapter3 routes")
	game.mode = "world"
	check(not game.flags.get("scenario_alm_frozen",true) and game.world_neighbors().has(16), "Chapter3 castle exit can reach north road16")
	check(game.travel_to(16) and game.travel_to(17), "Actual Alm travel reaches occupied northern road17")
	check(game.world_has_battle(17) and game.world_neighbors() == [16], "Unresolved road17 army permits its legal retreat road")
	check(game.switch_route() and game.world_node == 18 and game.party == ["celica","mae"], "Switch from occupied Alm checkpoint returns independent Celica party")
	check(game.travel_to(19) and game.world_has_battle(19), "Actual Celica travel reaches occupied eastern road19")
	check(game.save_game(), "Two occupied route checkpoints save to isolated report path")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game(), "Both occupied route checkpoints reload")
	check(loaded.world_neighbors().has(18), "Reloaded Celica still has its legal retreat road")
	check(loaded.switch_route() and loaded.world_node == 17 and loaded.party == ["alm","lukas"], "Reloaded route switch restores occupied Alm position and party")
	check(loaded.previous_world_node == 16 and loaded.world_neighbors().has(16), "Reloaded occupied Alm route restores its original entry road16")
	# on_battle_start rolls exactly once; seed201 makes that production
	# roll0. refresh_retreat must observe the same result, never reroll it.
	loaded.rng_state = 201
	check(loaded.start_battle(17), "Reloaded occupied Alm checkpoint starts native battle17")
	check(Inventory.retreat_destination(loaded) == 16, "Switched-back player battle retains its source retreat destination16")
	check(Inventory.refresh_retreat(loaded,0), "Source probability roll0 offers retreat after route switch")
	check(Inventory.retreat(loaded) and loaded.world_node == 16, "Actual probability retreat exits to original road16")
	check(loaded.load_game() and loaded.switch_route() and loaded.start_battle(17), "Original dual-route checkpoint can reload into another native battle17")
	loaded.phase = "enemy"
	loaded.turn = Inventory.forced_retreat_turn(17)
	var result: Dictionary = Inventory.forced_retreat(loaded)
	check(result.get("triggered",false) and result.get("destination",-1) == 16 and loaded.world_node == 16, "Source turn-limit retreat also preserves route entry road16")
	check(loaded.switch_route() and loaded.world_node == 19 and loaded.previous_world_node == 18, "Returning to saved Celica restores its independent road18 entry")

func _test_route_encounter_identity() -> void:
	var game = fresh()
	game.next_chapter(1)
	game.recruit("mae")
	game.next_chapter(2)
	game.mode = "world"
	check(game.switch_route() and game.travel_to(19), "Celica player-initiated checkpoint records its road18 entry")
	check(game.switch_route() and game.travel_to(16) and game.travel_to(17), "Alm approaches northern campaign road through real travel calls")
	# Separate source-table checkpoints for the resolved northern road17
	# and plain27. The incoming group64 is a legal mobile wave from29.
	for identity in Armies.instances_at(game,17):
		Armies.remove(game,str(identity))
	check(game.travel_to(27), "Resolved northern road checkpoint admits source plain27")
	for identity in Armies.instances_at(game,27):
		Armies.remove(game,str(identity))
	var attacker := Armies.add(game,29,64,65,true)
	check(not attacker.is_empty() and game.travel_to(28), "Source mobile reinforcement can approach actual forest28 travel")
	check(game.flags.get("inventory_enemy_initiated",false) and game.flags.get("inventory_attacking_instance_id","") == attacker, "Actual army movement records enemy initiative under its allocated instance")
	check(game.flags.get("inventory_attacker_previous_node",-1) == 29 and int(Armies.locate(game,attacker).get("node",-1)) == 28, "Actual arriving army identity and previous road stay consistent")
	check(game.switch_route() and game.world_node == 19 and not game.flags.get("inventory_enemy_initiated",false), "Alm's incoming-army initiative cannot leak into Celica's pending battle")
	check(game.save_game(), "Independent encounter context saves in a real dual-route world checkpoint")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.start_battle(19), "Celica checkpoint reloads and begins its own native battle19")
	check(not loaded.flags.get("inventory_enemy_initiated",false) and Inventory.retreat_destination(loaded) == 18, "Reloaded Celica battle retains player initiative and its own source retreat road")
	check(game.switch_route() and game.world_node == 28 and game.flags.get("inventory_attacking_instance_id","") == attacker, "Switch back restores the actual Alm attacker instead of another route's context")
	check(game.start_battle(28), "Restored Alm incoming army starts a stacked native battle28")
	game.phase = "enemy"
	game.turn = Inventory.forced_retreat_turn(28)
	var result: Dictionary = Inventory.forced_retreat(game)
	check(result.get("triggered",false) and result.get("instance_id","") == attacker, "Source timeout retreats exactly the restored incoming army")
	check(int(Armies.locate(game,attacker).get("node",-1)) == 29 and game.world_has_battle(28), "Enemy timeout sends its own army back while retaining the stationary forest defenders")

func reset_four() -> void:
	scene.game.new_game()
	scene.game.recruit("lukas")
	scene.game.next_chapter(1)
	scene.game.recruit("mae")
	scene.game.next_chapter(2)
	scene.game.mode = "world"
	scene.view = "world"
	scene.busy = false
	scene.batch_running = false
	scene.held_direction = Vector2i.ZERO
	scene._clear_menu()

func room(id: int, at: Vector2i) -> void:
	scene.game.enter_hub(id, at)
	scene.hub_controller._setup(false)

func drain() -> void:
	var pages := 0
	while scene.view in ["hub_dialogue","hub_choice","battle_story"] and pages < 300:
		pages += 1
		if scene.view == "battle_story":
			scene.dialogue_reveal = 10000
		else:
			scene.hub_controller.reveal = 10000
			if scene.view == "hub_choice":
				if not scene.hub_controller.choice_title.contains("记录进度"):
					break
				scene.hub_controller.choice_index = 1
		scene._accept()
	check(pages < 300, "Source milestone dialogue VM reaches a bounded continuation")

func _test_sluice_vm() -> void:
	reset_four()
	scene.game.switch_route()
	scene.game.world_node = 63
	scene.game.route_positions.celica = 63
	room(15,Vector2i(6,3))
	scene.hub_controller._start_script(36)
	drain()
	check(scene.game.flags.get("mila_visited",false) and scene.game.flags.get("source_flag_48",false), "Actual Mila sluice VM enables watergate keeper event")
	scene.hub_controller._cross_edge(Vector2i.UP)
	check(scene.view == "hub_dialogue", "Before chapter4 Mila north exit gives its source water-level refusal")
	drain()
	scene.game.switch_route()
	scene.game.world_node = 67
	scene.game.route_positions.alm = 67
	room(19,Vector2i(8,10))
	scene.hub_controller._start_script(38)
	drain()
	check(scene.view == "chapter" and scene.game.chapter == 4 and int(scene.game.flags.world_gate_bits) == 4, "Actual keeper VM removes Rigel border gate and reaches chapter4")
	scene._accept()
	drain()
	check(scene.view == "hub" and not scene.busy, "Chapter4 entry VM returns exploration control")
	scene.hub_controller._cross_edge(Vector2i.UP)
	check(scene.view == "hub_choice", "Watergate north exit offers the actual leave choice")
	scene.hub_controller.choice_index = 0
	scene._accept()
	check(scene.view == "world" and scene.game.world_node == 32, "Watergate north exit returns to source road32")
	check(scene.game.travel_to(33) and scene.game.world_has_battle(33), "Opened chapter4 border permits the next native battle checkpoint")
	check(scene.game.save_game(), "Opened border saves through actual State")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and Scenario.can_travel(loaded,33,32), "Reloaded chapter4 border stays open in both directions")
	check(loaded.switch_route() and loaded.world_node == 63, "Reloaded chapter4 can continue Celica at Mila")
	check(Scenario.can_travel(loaded,63,43), "Mila north route remains available after chapter4 reload")

func _test_dragon_capture_vm() -> void:
	reset_four()
	scene.game.next_chapter(3)
	# Source-valid checkpoint: Alm has resolved the Rigel road armies33/34
	# and is standing at35, while Celica has reached Duma's tower77.
	for node in [33,34]:
		for identity in Armies.instances_at(scene.game,node):
			Armies.remove(scene.game,str(identity))
	scene.game.world_node = 35
	scene.game.route_positions = {"alm":35,"celica":77}
	scene.game.mode = "world"
	scene.view = "world"
	scene.game.rng_state = 0
	check(scene.game.travel_to(36), "Source road35 reaches dragon valley36")
	check(scene.game.world_has_battle(36) and int(scene.game.world_armies["36"][0]) == 73, "Dragon entry allocates first source wave73")
	check(scene.game.world_neighbors().is_empty(), "Dragon trap intentionally closes both roads until Celica progresses")
	check(scene.game.switch_route() and scene.game.world_node == 77, "Trapped Alm can switch to Celica tower milestone")
	room(37,Vector2i(7,3))
	scene.hub_controller._start_script(49)
	drain()
	check(scene.view == "world" and scene.game.route == "alm" and scene.game.world_node == 36, "Actual Celica altar VM returns control to trapped Alm")
	check(not scene.busy and scene.game.story_events.is_empty(), "Capture dialogue finishes with world controls unlocked")
	check(scene.game.flags.get("dragon_valley_released",false) and (int(scene.game.flags.world_gate_bits) & 33) == 0, "Actual capture clears both valley gates and forced-dragon bit")
	check(scene.game.previous_world_node == 35 and Inventory.retreat_destination(scene.game) == 35, "Automatic capture handoff restores Alm's own valley entry35")
	check(not scene.game.can_switch_route(), "Captured Celica is intentionally unavailable before final reunion")
	check(scene.game.save_game(), "Capture checkpoint saves after actual VM return")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.world_node == 36 and loaded.route == "alm", "Captured-route checkpoint reloads at correct Alm valley position")
	check(Scenario.can_travel(loaded,36,35) and Scenario.can_travel(loaded,36,37), "Reloaded capture keeps both source roads open")
	check(loaded.world_has_battle(36) and not loaded.flags.get("generator_disabled_6",false), "Capture preserves surviving dragon wave instead of claiming a win")
	loaded.rng_state = 201
	check(loaded.start_battle(36) and Inventory.retreat_destination(loaded) == 35, "Captured-route reload preserves Alm's original road in the unresolved dragon encounter")
	check(not Inventory.refresh_retreat(loaded,0) and not Inventory.retreat(loaded) and Inventory.retreat_chance(36) == 0 and Inventory.forced_retreat_turn(36) == 255, "Source dragon battle intentionally offers neither probability nor timeout retreat")
	check(loaded.load_game(), "Original captured-route checkpoint remains available after the isolated retreat check")
	# Separate legal post-wave checkpoint: the unresolved army has now been
	# defeated. Removing the source-table instance tests only road admission;
	# it neither changes damage nor claims that this test fought the battle.
	for identity in Armies.instances_at(loaded,36):
		Armies.remove(loaded,str(identity))
	check(loaded.world_neighbors().has(37) and loaded.travel_to(37), "Legal resolved-wave checkpoint can leave valley toward Rigel falls")
	check(loaded.world_has_battle(37), "Escape reaches the real next army rather than bypassing its battle")
