extends SceneTree
## Representative exploration routes through actual main input/controller.
## Initial chapter checkpoints are fixtures; walking, dialogue, VM, saves,
## promotions and final-battle entry use the same paths as player input.
const SAVE := "res://reports/test-spot-campaign-save.json"
var scene
var checks := 0
var failures: Array[String] = []
var routes: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

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
	_test_portal_round_trips()
	_test_source_reciprocal_portals()
	_test_celica_promotion_resume()
	_test_alm_promotion()
	_test_branches_and_ships()
	_test_timed_promotion()
	_test_chapter_entry_dialogues()
	_test_final_approach()
	var report := FileAccess.open("res://reports/spot-campaign-verification.json", FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"failures":failures,"routes":routes,
		"scope":"actual main direction/confirm, all27 reciprocal portal landings, saved story VM, two story promotions, both desert recruitment branches, boats, all four chapter transitions/entry scripts, final approach",
		"limits":"Initial chapter/quest checkpoints are fixtures; combat balance and complete natural playthrough are outside this exploration-focused suite."}, "\t") + "\n")
	scene.audio.stop_all()
	scene.queue_free()
	await process_frame
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	print("SPOT CAMPAIGN: %d checks, %d failures" % [checks,failures.size()])
	quit(0 if failures.is_empty() else 1)

func reset(route: String = "alm") -> void:
	scene.game.new_game()
	scene._clear_menu()
	scene.busy = false
	scene.batch_running = false
	scene.held_direction = Vector2i.ZERO
	scene.game.chapter = 4
	scene.game.route = route
	scene.game.roster.celica = scene.game._initial_character("celica")
	scene.game.parties.celica = ["celica"]
	scene.game.party = scene.game.parties[route].duplicate()
	scene.game.world_node = 77 if route == "celica" else 78
	scene.game.route_positions[route] = scene.game.world_node

func room(id: int, at: Vector2i) -> void:
	check(scene.hub_controller.enter(id,at),"Enter source room %d" % id)

func step(dir: Vector2i) -> void:
	scene._direction(dir)

func drain() -> void:
	var count := 0
	while scene.view in ["hub_dialogue","hub_choice"] and count < 500:
		count += 1
		if scene.view == "hub_choice":
			if scene.hub_controller.choice_title.contains("记录进度"):
				scene.hub_controller.choice_index = 1
			else: break
		scene.hub_controller.reveal = 10000
		scene._accept()
	check(count < 500,"Dialogue advances without a loop")

func _test_portal_round_trips() -> void:
	reset()
	room(25,Vector2i(7,8))
	step(Vector2i.UP)
	check(scene.game.hub_id == 26 and scene.game.hub_position == Vector2i(11,6),"Fear shrine portal reaches source reciprocal landing")
	step(Vector2i.DOWN)
	step(Vector2i.UP)
	check(scene.game.hub_id == 25 and scene.game.hub_position == Vector2i(7,7),"Leaving and returning to landing permits return portal")
	step(Vector2i.DOWN)
	step(Vector2i.UP)
	check(scene.game.hub_id == 26,"Reciprocal portal remains reusable in both directions")
	routes.append("25 → 26 → 25 → 26 reciprocal shrine portals")
	reset()
	# These rooms were cleared on this visit; test traversal without injecting
	# a victory. New visits/first encounter behavior has its own battle suite.
	scene.game.hub_used.dungeon_visited = 3
	room(31,Vector2i(11,3))
	step(Vector2i.UP)
	check(scene.game.hub_id == 97,"Duma maze upper staircase enters encounter room")
	step(Vector2i.UP)
	step(Vector2i.DOWN)
	check(scene.game.hub_id == 31,"Duma maze staircase permits backtracking after landing")
	routes.append("31 → 97 → 31 Duma maze staircase")

func _test_source_reciprocal_portals() -> void:
	var count := 0
	for original_id in scene.game.hubs.rooms:
		var original: Dictionary = scene.game.hubs.rooms[original_id]
		for portal in original.get("portals",[]):
			var destination_id := int(portal.destination)
			var destination: Dictionary = scene.game.hubs.rooms[str(destination_id)]
			var reverse: Dictionary = {}
			for candidate in destination.get("portals",[]):
				if candidate.position == portal.spawn and int(candidate.destination) == int(original_id):
					reverse = candidate
			if reverse.is_empty(): continue
			reset()
			scene.game.hub_used.dungeon_visited = 255
			var landing := Vector2i(portal.spawn[0],portal.spawn[1])
			scene.hub_controller.enter(destination_id,landing)
			check(scene.view == "hub" and scene.game.hub_position == landing,"Source portal %s→%d does not immediately bounce on landing" % [original_id,destination_id])
			var dir := Vector2i.ZERO
			for direction in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
				var at: Vector2i = landing + direction
				if not scene.hub_controller._ground(at) or scene.hub_controller._actor_at(at): continue
				if at.x <= 0 or at.y <= 0 or at.x >= int(destination.width)-1 or at.y >= int(destination.height)-1: continue
				if destination.get("portals",[]).any(func(p):return Vector2i(p.position[0],p.position[1]) == at): continue
				if scene.game.hub_script(0,at) >= 0: continue
				dir = direction
				break
			check(dir != Vector2i.ZERO,"Source portal %s→%d has a walkable departure tile" % [original_id,destination_id])
			if dir == Vector2i.ZERO: continue
			step(dir)
			step(-dir)
			check(scene.game.hub_id == int(original_id),"Source portal %s→%d permits actual input backtracking" % [original_id,destination_id])
			count += 1
	check(count == 27,"All 27 reciprocal source landing records are exercised")
	routes.append("All 27 reciprocal source portal landings: no immediate bounce, step away, return")

func _test_celica_promotion_resume() -> void:
	reset("celica")
	scene.game.roster.celica.level = 12
	scene.game.roster.celica.exp = 47
	room(13,Vector2i(11,9))
	step(Vector2i.UP) # Open the original two-tile door first.
	step(Vector2i.UP)
	check(scene.view == "hub_dialogue" and scene.game.hub_position == Vector2i(11,5),"Grieth fortress promotion trigger walks Celica to priestess")
	check(scene.game.hub_used.has("event_vm"),"Promotion dialogue records resumable VM checkpoint")
	scene._show_title()
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	check(scene.view == "hub_dialogue" and scene.game.hub_id == 13,"Title continue resumes actual promotion dialogue")
	drain()
	check(scene.game.roster.celica.get("promoted",false) and int(scene.game.roster.celica.level) == 1,"Resumed priestess event promotes Celica once")
	check(scene.game.flags.get("source_flag_45",false) and scene.game.flags.get("source_flag_46",false) and scene.game.flags.get("source_flag_58",false),"Promotion advances all original source flags")
	check(scene.game.hub_used.get("event_vm",{}).is_empty() and scene.hub_controller.script_id < 0,"Promotion finishes checkpoint and returns control")
	step(Vector2i.DOWN)
	step(Vector2i.DOWN)
	step(Vector2i.DOWN)
	check(scene.view == "hub" and scene.game.hub_position == Vector2i(11,8),"Completed promotion tile no longer restarts event")
	routes.append("Grieth fortress floor trigger → save/title continue → Celica promotion")

func _test_alm_promotion() -> void:
	reset("celica")
	scene.game.roster.alm.exp = 83
	scene.game.roster.alm.level = 12
	room(20,Vector2i(4,8))
	step(Vector2i.UP) # blocked by Halcyon: face him without entering his cell
	scene._accept()
	check(scene.view == "hub_dialogue","Facing Halcyon opens story promotion dialogue")
	drain()
	check(scene.game.roster.alm.get("promoted",false) and int(scene.game.roster.alm.level) == 1 and int(scene.game.roster.alm.exp) == 0,"Celica's Halcyon conversation promotes distant Alm through source VM")
	check(scene.game.route == "celica" and scene.game.party == ["celica"],"Remote promotion does not switch active route or party")
	check(scene.game.flags.get("source_flag_84",false),"Halcyon promotion consumes source trigger")
	scene._accept()
	drain()
	check(int(scene.game.roster.alm.level) == 1,"Repeating Halcyon conversation cannot duplicate promotion")
	routes.append("Sage village → face Halcyon → distant Alm promotion")

func _test_branches_and_ships() -> void:
	for branch in [[28,"sonya","deen",Vector2i(16,11)],[29,"deen","sonya",Vector2i(17,10)]]:
		reset("celica")
		# Source boss-death checkpoint; actual recruitment still requires
		# facing the surviving NPC and completing the native dialogue VM.
		scene.game.apply_hub_flag(int(branch[0]))
		room(13,branch[3])
		step(Vector2i.UP)
		scene._accept()
		check(scene.view == "hub_dialogue","Survivor %s has real NPC conversation" % branch[1])
		drain()
		check(scene.game.party.has(branch[1]) and not scene.game.party.has(branch[2]),"Desert branch recruits only %s" % branch[1])
		check(scene.game.save_game(),"Branch recruitment writes isolated suspend")
		scene._show_title()
		scene.title_menu = true
		scene.title_selected = 1
		scene._accept()
		check(scene.view == "hub" and scene.game.party.has(branch[1]),"Branch recruitment persists after title continue")
	reset("celica")
	room(6,Vector2i(16,3))
	step(Vector2i.UP)
	check(scene.view == "world" and scene.game.world_node == 9,"Novis boarding tile sails to original world node9")
	room(9,Vector2i(10,13))
	step(Vector2i.UP)
	check(scene.view == "world" and scene.game.world_node == 15,"Sofia boarding tile sails to original world node15")
	routes.append("Both desert survivor recruitment branches and two original boarding tiles")

func _test_timed_promotion() -> void:
	reset("celica")
	scene.instant_mode = false
	room(13,Vector2i(11,9))
	step(Vector2i.UP)
	step(Vector2i.UP)
	var frames := 0
	while frames < 1200:
		frames += 1
		if scene.view == "hub_dialogue":
			scene.hub_controller.reveal = 10000
			scene._accept()
		elif scene.view == "hub_choice":
			break
		scene.hub_controller.process(1.0/60.0988)
		if scene.hub_controller.script_id < 0 and scene.hub_controller.motion_left <= 0:
			break
	check(frames < 1200 and scene.game.roster.celica.get("promoted",false),"Original-timed walking/waiting promotion VM completes without instant mode")
	check(scene.view == "hub" and scene.game.hub_position == Vector2i(11,5),"Timed promotion returns control at original final position")
	scene.instant_mode = true
	routes.append("Grieth promotion VM at 60.0988-Hz motion/wait timing")

func _test_chapter_entry_dialogues() -> void:
	reset()
	scene.game.chapter = 1
	scene.game.recruit("lukas")
	room(44,Vector2i(7,7))
	step(Vector2i.UP)
	scene._accept()
	drain()
	check(scene.view == "chapter" and scene.game.chapter == 2,"Facing Mycen at Sofia advances chapter1 to2 through actual NPC")
	scene._show_title()
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	check(scene.view == "chapter" and scene.game.flags.get("chapter_intro_pending",false),"Continue restores pending chapter screen before entry dialogue")
	scene._accept()
	check(scene.view == "hub_choice" and scene.hub_controller.script_id == 18,"Confirming chapter2 executes monastery spawn event18")
	drain()
	check(scene.game.hub_id == 5 and scene.game.flags.get("source_flag_20",false),"Monastery opening dialogue unlocks source recruitment flags")
	# The later Sofia-arrival flag is this test's chapter-two milestone.
	scene.game.apply_hub_flag(21)
	room(44,Vector2i(6,7))
	step(Vector2i.UP)
	scene._accept()
	drain()
	check(scene.view == "chapter" and scene.game.chapter == 3,"Facing Alm at Sofia advances chapter2 to3")
	scene._accept()
	drain()
	check(scene.view == "hub" and scene.game.hub_id == 44 and scene.game.flags.get("source_flag_41",false),"Chapter3 entry completes its original save/flag VM")
	scene.game.apply_hub_flag(48)
	room(19,Vector2i(8,8))
	step(Vector2i.UP)
	scene._accept()
	drain()
	check(scene.view == "chapter" and scene.game.chapter == 4,"Sluice keeper conversation advances chapter3 to4")
	scene._accept()
	drain()
	check(scene.view == "hub" and scene.game.hub_id == 19 and scene.game.flags.get("source_flag_50",false),"Chapter4 entry completes source watergate spawn VM")
	room(30,Vector2i(11,15))
	step(Vector2i.UP)
	scene._accept()
	drain()
	check(scene.view == "chapter" and scene.game.chapter == 5 and scene.game.party.has("mycen"),"Rigel Mycen conversation recruits him and advances final chapter")
	scene._accept()
	drain()
	check(scene.view == "hub" and scene.game.hub_id == 30 and scene.game.flags.get("source_flag_83",false),"Chapter5 entry completes source Rigel spawn VM")
	routes.append("All four chapter advances via actual NPC conversations and chapter-entry floor VM")

func _test_final_approach() -> void:
	reset()
	scene.game.chapter = 5
	scene.game.recruit("mycen")
	scene.game.parties.celica = ["celica","mae"]
	scene.game.roster.mae = scene.game._initial_character("mae")
	scene.game.roster.celica.hp = 9
	scene.game.apply_hub_flag(73)
	scene.game.apply_hub_flag(80)
	room(41,Vector2i(4,8))
	step(Vector2i.LEFT)
	drain()
	check(scene.game.flags.get("falchion_scene_seen",false),"Actual Falchion approach triggers captive-party vision")
	check(int(scene.game.flags.get("celica_captive_hp",{}).get("celica",0)) == 9,"Vision preserves captured Celica HP")
	# The narrative later places the player at this altar checkpoint. Input
	# must trigger reunion before the final trigger, not start it manually.
	room(37,Vector2i(5,21))
	step(Vector2i.RIGHT)
	drain()
	check(scene.game.flags.get("source_flag_81",false),"Walking onto altar reunion tile activates original reunion VM")
	check(scene.view == "hub","Reunion returns walking control before final battle")
	# A separate maze entrance reaches the lower side of the final door.
	# These are intentionally separate checkpoints: the upper reunion
	# corridor does not connect directly through the original wall.
	room(37,Vector2i(11,25))
	step(Vector2i.UP) # Open the Alm-only final door.
	step(Vector2i.UP)
	step(Vector2i.UP)
	drain()
	check(scene.view == "battle" and scene.game.stage_id == 62,"Walking onto final source trigger enters playable Duma battle")
	check(scene.game.flags.get("final_parties_merged",false) and scene.game.living("player").size() == 4,"Actual final entry merges both two-person parties")
	check(int(scene.game.find_unit("celica").get("hp",0)) == 9,"Final scene keeps captive HP through actual route")
	routes.append("Falchion vision → altar reunion floor trigger → final battle floor trigger")
