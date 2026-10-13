extends SceneTree
## One bounded round: authentic saves, one-field corruption, and controller resume.
const State = preload("res://core/game_state.gd")
const Validator = preload("res://core/campaign_save_validation.gd")
const SAVE := "res://reports/test-round3-save.json"
var scene
var checks := 0
var failures: Array[String] = []
var rejected_cases: Array[String] = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func fresh():
	var g = State.new()
	g.save_path = SAVE
	g.new_game()
	g.recruit("lukas")
	g.world_node = 1
	check(g.start_battle(1), "authentic first battle starts")
	return g

func write(state: Dictionary) -> void:
	var file := FileAccess.open(SAVE, FileAccess.WRITE)
	file.store_string(JSON.stringify(state))
	file.close()

func fingerprint(g) -> String:
	# Capture every serialized campaign field through the production writer.
	check(g.save_game(), "live fingerprint checkpoint writes")
	return FileAccess.get_file_as_string(SAVE)

func reject(g, state: Dictionary, label: String) -> void:
	var before := fingerprint(g)
	write(state)
	check(not g.load_game(), label + " rejects before mutation")
	check(fingerprint(g) == before, label + " retains the complete live checkpoint")
	rejected_cases.append(label)

func new_scene() -> void:
	if is_instance_valid(scene):
		scene.audio.stop_all()
		scene.queue_free()
		await process_frame
	scene = load("res://scenes/main.tscn").instantiate()
	scene.game.save_path = SAVE
	scene.instant_mode = true
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	scene.set_process(false)
	scene.set_physics_process(false)

func run() -> void:
	var g = fresh()
	check(g.save_game(), "production writer creates round-three battle suspend")
	var base: Dictionary = State.read_json(SAVE)
	check(Validator.valid(g, base), "authentic battle checkpoint passes preflight")
	for retry in [false, true]:
		var label := "retry" if retry else "suspend"
		for field in ["route", "party", "roster_id", "roster_side", "active_parties"]:
			var bad: Dictionary = base.duplicate(true)
			var target: Dictionary = bad.battle_start_snapshot if retry else bad
			match field:
				"route": target.route = "celica"
				"party": target.party = ["celica"]
				"roster_id": target.roster.alm.id = "lukas"
				"roster_side": target.roster.alm.side = "enemy"
				"active_parties": target.parties.alm = ["alm"]
			reject(g, bad, label + " conflicting " + field)
	_test_unit_metadata()
	_test_move_and_retry()
	_test_final_parties()
	_test_v1_migration()
	await _test_vm(g)
	if is_instance_valid(scene):
		scene.audio.stop_all()
		scene.queue_free()
		await process_frame
	for suffix in ["", ".tmp", ".v1.bak", ".v2.bak"]:
		DirAccess.remove_absolute(SAVE + suffix)
	var report := {"checks": checks, "failures": failures, "rejected_cases": rejected_cases,
		"issues_observed_before_fix": ["conflicting suspend/retry route, party, and roster identities were accepted", "unsafe resumed unit and hub actor metadata were accepted", "source VM accepted another room and non-checkpoint continuation PCs", "v1 migration captured the default one-member party in its generated retry snapshot"],
		"scope": "production GameState.save_game; one-field suspend/retry corruption; authentic source hub dialogue VM and continued chapter transition",
		"limits": "bounded local fixtures and headless controllers, not every arbitrary dictionary or complete natural campaign; no real user save accessed"}
	var file := FileAccess.open("res://reports/round3-save-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	file.close()
	print("ROUND 3 SAVE: %d checks, %d failures" % [checks, failures.size()])
	# Give the audio mixer time to release stopped test-scene title streams.
	await create_timer(0.1).timeout
	quit(0 if failures.is_empty() else 1)

func _test_unit_metadata() -> void:
	for field in ["personal_resistance", "source_enemy_character_id", "rescue_npc"]:
		var g = fresh()
		match field:
			"personal_resistance":
				g.recruit("gray")
				check(g.promote_unit("gray", 1).get("valid", false), "actual villager promotion produces personal resistance")
				check(g.start_battle(1), "promoted unit is deployed by production battle constructor")
			"source_enemy_character_id":
				g.chapter = 4
				g.world_node = 34
				g.apply_hub_flag(31)
				check(g.start_battle(34, [34, 35]), "source Zeke alliance constructs NPC source identities")
			"rescue_npc":
				g.chapter = 4
				g.world_node = 29
				check(g.start_battle(29), "source allied NPC constructor marks rescue target")
		check(g.save_game(), field + " authentic checkpoint writes")
		var base: Dictionary = State.read_json(SAVE)
		check(Validator.valid(g, base), field + " authentic checkpoint is compatible")
		var index := -1
		for slot in range(base.units.size()):
			if base.units[slot].has(field):
				index = slot
				break
		check(index >= 0, field + " is present in the generated source record")
		if index < 0: continue
		for retry in [false, true]:
			var bad: Dictionary = base.duplicate(true)
			var target: Dictionary = bad.battle_start_snapshot if retry else bad
			target.units[index][field] = "false" if field == "rescue_npc" else {}
			reject(g, bad, "%s wrong existing %s type" % ["retry" if retry else "suspend", field])

func _test_move_and_retry() -> void:
	var g = fresh()
	var original: Array = g.find_unit("alm").position.duplicate()
	check(g.select_unit("alm"), "player selects real active unit")
	var moved := false
	for point in g.reachable(g.find_unit("alm")).costs:
		if point != State.pos(g.find_unit("alm")) and g.can_stop(g.find_unit("alm"), point):
			moved = g.move_selected(point)
			break
	check(moved, "player creates a cancellable movement through production API")
	check(g.save_game(), "tentative movement suspend writes")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game(), "tentative movement suspend resumes")
	check(loaded.find_unit("alm").position == original and not bool(loaded.find_unit("alm").acted), "suspend restores origin and preserves unspent action")
	check(loaded.retry_battle(), "legitimate suspended battle still retries")
	check(loaded.find_unit("alm").position == original and loaded.party == ["alm", "lukas"], "retry restores deployment and both recruited members")

func _test_final_parties() -> void:
	var g = fresh()
	for transition in [1, 2, 3, 4]:
		check(g.next_chapter(transition), "authentic chapter transition %d" % transition)
		if transition == 1: g.recruit("mae")
	g.flags.scenario_final_merge_ready = true
	g.world_node = 48
	check(g.enter_dungeon_battle(22), "final source trigger constructs combined deployment")
	check(g.units.any(func(unit): return unit.get("route", "") == "celica") and g.units.any(func(unit): return unit.get("route", "") == "alm"), "final deployment retains distinct route owners")
	check(g.save_game(), "merged-party checkpoint writes")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game(), "merged-party suspend passes cross-field validation")
	check(loaded.retry_battle() and loaded.find_unit("mae").route == "celica", "merged-party retry retains other-route companion")

func _test_v1_migration() -> void:
	var g = fresh()
	# A historical v1 milestone has tactical growth, but no campaign fields.
	var alm: Dictionary = g.find_unit("alm")
	alm.level = 3
	alm.exp = 61
	alm.max_hp = 30
	alm.hp = 13
	check(g.save_game(), "production writer captures legacy-compatible grown party")
	var old: Dictionary = State.read_json(SAVE)
	old.version = 1
	for field in Validator.EXTENDED_FIELDS: old.erase(field)
	for field in ["stage_id", "world_node", "roster", "cleared_stages", "battle_start_snapshot", "victory_rewards"]: old.erase(field)
	for field in ["world_army_instances", "world_army_next_id", "world_random_army_instance", "battle_army_instances", "dungeon_army_instances", "inventory_attacking_instance_id"]: old.flags.erase(field)
	for unit in old.units: unit.erase("army_instance")
	write(old)
	var original := FileAccess.get_file_as_string(SAVE)
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game(), "v1 recruited and grown party migrates")
	check(loaded.battle_start_snapshot.party == ["alm", "lukas"] and loaded.battle_start_snapshot.parties.alm == ["alm", "lukas"], "v1 generated retry snapshot records the actual recruited party")
	check(int(loaded.find_unit("alm").exp) == 61 and int(loaded.find_unit("alm").hp) == 13, "v1 migration retains earned growth and current HP")
	check(loaded.save_game() and Validator.valid(loaded, State.read_json(SAVE)), "v1 generated retry snapshot serializes as a valid v3 checkpoint")
	var again = State.new()
	again.save_path = SAVE
	check(again.load_game() and int(again.find_unit("alm").exp) == 61, "upgraded v1 recruited checkpoint reloads")
	check(again.retry_battle() and again.party == ["alm", "lukas"] and not again.find_unit("lukas").is_empty(), "upgraded v1 retry retains the full recruited deployment")
	check(again.parties.alm == again.party and again.save_game(), "v1 retried party remains consistent and saveable")
	var retried = State.new()
	retried.save_path = SAVE
	check(retried.load_game() and retried.party == ["alm", "lukas"], "v1 retried suspend resumes again")
	check(FileAccess.get_file_as_string(SAVE + ".v1.bak") == original, "v1 migration preserves the original checkpoint backup")

func _test_vm(g) -> void:
	await new_scene()
	scene.game.new_game()
	scene.game.recruit("lukas")
	check(scene.game.enter_hub(44, Vector2i(6, 6)), "authentic chapter hub enters")
	scene.hub_controller._setup(false)
	scene.hub_controller._start_script(16)
	check(scene.view == "hub_dialogue", "source VM suspends at actual dialogue")
	var base: Dictionary = State.read_json(SAVE)
	check(base.hub_used.event_vm.pc == 0 and Validator.valid(g, base), "production source checkpoint records legal VM boundary")
	for field in ["hub_id", "pc", "wander_bounds", "interaction_flags", "render_position", "dungeon_visited"]:
		var bad: Dictionary = base.duplicate(true)
		var vm: Dictionary = bad.hub_used.event_vm
		match field:
			"hub_id": vm.hub_id = 1
			"pc": vm.pc = 1
			"wander_bounds": vm.actors[vm.actors.keys()[0]].wander_bounds = [0]
			"interaction_flags": vm.actors[vm.actors.keys()[0]].interaction_flags = {}
			"render_position": vm.actors[vm.actors.keys()[0]].render_position = [0]
			"dungeon_visited": bad.hub_used.dungeon_visited = {}
		reject(g, bad, "corrupted source VM " + field)
	write(base)
	await new_scene()
	check(scene.game.load_game(), "authentic VM suspend restores")
	scene.hub_controller.resume()
	check(scene.view == "hub_dialogue" and scene.game.hub_id == 44, "authentic VM resumes the same source dialogue")
	var steps := 0
	while scene.view == "hub_dialogue" and steps < 100:
		scene.hub_controller.reveal = 10000
		scene.hub_controller.accept()
		steps += 1
	check(steps < 100 and scene.game.chapter == 2 and scene.game.route == "celica", "resumed dialogue commits chapter transition once")
	check(scene.game.parties.alm == ["alm", "lukas"] and not scene.game.hub_used.has("event_vm"), "completed VM retains first party and clears continuation")
	await new_scene()
	scene.game.new_game()
	scene.game.enter_hub(1, Vector2i(5, 10))
	scene.hub_controller._setup(false)
	scene.hub_controller._start_script(0)
	check(scene.view == "hub_choice" and State.read_json(SAVE).hub_used.event_vm.pc == 2, "source choice saves the instruction after the choice")
	await new_scene()
	check(scene.game.load_game(), "authentic choice continuation remains compatible")
	scene.hub_controller.resume()
	check(scene.view == "hub_dialogue", "source choice continuation reaches its next dialogue")
