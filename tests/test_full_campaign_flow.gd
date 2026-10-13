extends SceneTree
## Headless main/controller integration. Milestone fixtures bypass walking and
## battle damage, while exercising real VM, result, save and route dispatch.
const State = preload("res://core/game_state.gd")
const SAVE := "res://reports/test-full-campaign-flow-save.json"
var scene
var checks := 0
var failures: Array[String] = []
var entered_maps: Array[int] = []

func _initialize() -> void:
	call_deferred("_run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)
		push_error(message)

func _run() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	_test_chapter_vm()
	_test_map_entry_pipeline()
	_test_capture_and_ending()
	scene.audio.stop_all()
	scene.queue_free()
	await process_frame
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	var file := FileAccess.open("res://reports/full-campaign-flow-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures, "entered_tactical_maps": entered_maps,
		"scope": "headless actual main, chapter event VM, all map entry/save pipelines, captured-route dispatch, final reunion and ending persistence",
		"limits": "Milestone fixtures do not simulate every map's combat, all world walking, graphical rendering or per-frame original timing."}, "\t") + "\n")
	print("FULL CAMPAIGN FLOW: %d checks, %d failures, %d maps" % [checks, failures.size(), entered_maps.size()])
	quit(0 if failures.is_empty() else 1)

func reset() -> void:
	scene.game.new_game()
	scene._clear_menu()
	scene.busy = false
	scene.batch_running = false
	scene.held_direction = Vector2i.ZERO
	scene.view = "world"

func setup_room(id: int, at: Vector2i) -> void:
	scene.game.enter_hub(id, at)
	scene.hub_controller._setup(false)

func drain() -> void:
	var count := 0
	while scene.view in ["hub_dialogue", "hub_choice"] and count < 1000:
		count += 1
		scene.hub_controller.reveal = 10000
		if scene.view == "hub_choice":
			if scene.hub_controller.choice_title.contains("记录进度"):
				scene.hub_controller.choice_index = 1
			else:
				break
		scene._accept()
	check(count < 1000, "Source milestone VM terminates within bounded dialogue pages")

func _test_chapter_vm() -> void:
	reset()
	scene.game.recruit("lukas")
	setup_room(44, Vector2i(6,6))
	scene.hub_controller._start_script(16)
	drain()
	check(scene.view == "chapter" and scene.campaign_chapter and scene.game.chapter == 2, "Source script16 reaches actual Celica chapter screen")
	scene._accept()
	drain()
	check(scene.game.hub_id == 5 and scene.view == "hub" and scene.game.route == "celica", "Chapter confirmation opens Celica monastery controller")
	scene.game.recruit("mae")
	scene.view = "world"
	scene.game.mode = "world"
	scene.game.world_node = 57
	scene.game.world_armies.clear()
	scene._direction(Vector2i.LEFT)
	check(scene.game.world_node == 7, "Actual world input allows Celica from harbor57 to shared castle gate7")
	scene._direction(Vector2i.UP)
	check(scene.game.world_node == 52, "Actual world input completes Celica harbor-to-castle path")
	setup_room(44, Vector2i(6,6))
	scene.hub_controller._start_script(19)
	drain()
	check(scene.view == "chapter" and scene.game.chapter == 3 and scene.game.route == "alm", "Source script19 completes reunion and restores Alm chapter")
	scene._accept()
	drain()
	check(scene.game.hub_id == 44 and scene.game.parties.celica.has("mae"), "Chapter-three hub retains both route parties")
	scene.game.apply_hub_flag(48)
	setup_room(19, Vector2i(8,10))
	scene.hub_controller._start_script(38)
	drain()
	check(scene.view == "chapter" and scene.game.chapter == 4 and scene.game.flags.get("source_flag_49", false), "Source sluice VM invokes main chapter-four interface")
	scene._accept()
	drain()
	check(scene.view == "hub" and scene.game.hub_id == 19, "Chapter-four confirmation returns to original watergate hub")
	scene.game.switch_route()
	scene.game.world_node = 63
	setup_room(15, Vector2i(4,1))
	scene.hub_controller._cross_edge(Vector2i.UP)
	scene._accept()
	check(scene.view == "world" and scene.game.world_node == 43 and scene.game.route == "celica", "Chapter-four Celica crosses Mila hub north exit into swamp world route")
	scene.game.switch_route()
	setup_room(29, Vector2i(11,15))
	scene.hub_controller._start_script(53)
	drain()
	check(scene.view == "chapter" and scene.game.chapter == 5 and scene.game.party.has("mycen"), "Source Mycen recruitment VM reaches underground finale chapter")
	scene._accept()
	drain()
	check(scene.game.hub_id == 30 and scene.game.parties.celica.has("mae"), "Finale chapter confirmation keeps separate Celica party")

func _test_map_entry_pipeline() -> void:
	for stage in range(1,81):
		if stage == 62:
			continue # The real altar VM and both parties are exercised below.
		reset()
		var route = str(scene.game.stages[stage].get("route", "alm"))
		if route not in ["alm", "celica"]: route = "alm"
		scene.game.chapter = 4
		scene.game.route = route
		scene.game.party = [route]
		scene.game.parties[route] = [route]
		scene.game.roster[route] = scene.game._initial_character(route)
		scene.game.world_armies.clear()
		scene.game.world_node = stage if stage < 49 else 78
		scene.game.route_positions[route] = scene.game.world_node
		if stage > 48:
			scene.game.battle_return = {"mode":"hub", "hub_id":30, "position":[11,15], "world_node":78}
		check(scene.game.start_battle(stage, [], stage > 48), "Source map %d native state entry" % stage)
		scene._begin_existing_battle()
		check(scene.view == "battle" and scene.game.mode == "battle", "Source map %d enters actual battle controller" % stage)
		entered_maps.append(stage)
		var saved: Dictionary = State.read_json(SAVE)
		check(scene.game._valid_save(saved), "Source map %d controller suspend passes full schema validation" % stage)
		check(scene.game.story_events.is_empty(), "Source map %d start dialogue queue is consumed" % stage)
		for enemy in scene.game.living("enemy"): enemy.hp = 0
		scene.game.check_outcome()
		scene._show_result()
		check(scene.view == "victory" and scene.game.battle_settled, "Source map %d result controller settles exactly once" % stage)
		scene._continue_world()
		check(scene.view == ("hub" if stage > 48 else "world"), "Source map %d returns to correct exploration surface" % stage)

func _test_capture_and_ending() -> void:
	reset()
	scene.game.chapter = 4
	scene.game.recruit("mycen")
	scene.game.route = "celica"
	scene.game.party = ["celica"]
	scene.game.parties.celica = ["celica"]
	scene.game.roster.celica = scene.game._initial_character("celica")
	scene.game.recruit("mae")
	scene.game.world_node = 77
	scene.game.route_positions = {"alm":36,"celica":77}
	setup_room(37, Vector2i(7,3))
	scene.hub_controller._start_script(49)
	drain()
	check(scene.view == "world" and scene.game.route == "alm" and scene.game.world_node == 36, "Actual altar VM returns to Alm valley, never Celica hub")
	check(scene.game.story_events.is_empty() and not scene.busy, "Capture dialogue queue is consumed and world input unlocked")
	check(bool(scene.game.flags.dragon_valley_released), "Captured Celica releases source dragon valley gate")
	scene.game.chapter = 5
	scene.game.roster.celica.hp = 9
	setup_room(40, Vector2i(7,3))
	scene.hub_controller._start_script(52)
	drain()
	check(int(scene.game.flags.celica_captive_hp.celica) == 9, "Actual Falchion vision snapshots Celica HP")
	setup_room(37, Vector2i(7,3))
	scene.hub_controller._start_script(55)
	drain()
	check(scene.view == "battle" and scene.game.stage_id == 62 and scene.game.flags.final_parties_merged, "Final source VM deploys merged armies through actual main battle entry")
	entered_maps.append(62)
	check(int(scene.game.find_unit("celica").hp) == 9 and scene.game.living("player").size() == 4, "Final controller retains both parties and captured HP")
	var duma: Dictionary = {}
	for unit in scene.game.units:
		if int(unit.get("character_id",0)) == 167: duma = unit
	scene.game.commit_strike({"attacker":"alm", "defender":duma.id, "hp_after":0})
	scene._show_result()
	check(scene.view == "ending" and scene.game.mode == "ending" and scene.game.battle_settled, "Duma true death enters actual ending screen through result queue")
	check(scene.ending_pages.size() > 5 and scene.game.flags.get("campaign_complete", false), "Ending contains source narrative and persistent character fates")
	var pages: int = scene.ending_pages.size()
	scene._show_title()
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	check(scene.view == "ending" and scene.ending_pages.size() == pages, "Title continue restores completed ending without reward duplication")
