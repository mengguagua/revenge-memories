extends SceneTree
## Round3: native queued-army priority, source mobility and ID lifecycle.
const State = preload("res://core/game_state.gd")
const Scenario = preload("res://core/scenario_rules.gd")
const Armies = preload("res://core/world_armies.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const SAVE := "res://reports/test-round3-world-save.json"
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func fresh(chapter: int = 3):
	var game = State.new()
	game.save_path = SAVE
	game.new_game()
	game.chapter = chapter
	game.world_node = 31
	game.route_positions.alm = 31
	game.route_positions.celica = 18
	game.roster.celica = game._initial_character("celica")
	game.parties.celica = ["celica"]
	game.mode = "world"
	game.world_armies.clear()
	Armies.reset_for_chapter(game)
	game.flags.inventory_enemy_record_chapter = chapter
	return game

func _run() -> void:
	_test_queue_priority()
	_test_blocked_queue()
	_test_queued_boss_mobility()
	_test_forced_dragon_rng()
	_test_reencounter_and_routes()
	_test_reserved_slot_variants()
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	var report := FileAccess.open("res://reports/round3-world-verification.json", FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"failures":failures,
		"scope":"Native queued army allocation and failed allocation priority; fixed boss mobility; forced dragon-gate generator RNG; partial casualties after enemy retreat and route switching; all five cemetery variants in chapters3/4; chapter ID lifecycle and source slot capacity.",
		"source_contract":"bank008 L089F15-L089F44/L089FBC selects one queued army before probability generators; L08A130 sets group<60 mobility0; bank007 L07A4F3 skips mobility0; bank008 L089F4A jumps past generator selection for the dragon gate; L089D38 cemetery slot13, L089FCA ordinary13 slots; L08A095 per-army masks.",
		"limits":"Deterministic checkpoints and source-table travel steps, not frame-exact RNG scheduling, all natural battles or graphics."}, "\t") + "\n")
	print("ROUND3 WORLD: %d checks, %d failures" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

func _test_queue_priority() -> void:
	var game = fresh()
	game.flags.queued_army_0 = true
	game.flags.reinforcement_state_3 = 1
	# Without queue priority this seed makes generator3's second roll0,
	# spawning an extra wave alongside the scripted Tatara army.
	game.rng_state = 146
	Scenario.on_travel(game)
	check(game.world_armies.get("32", []) == [32], "Scripted water-gate queue takes the sole allocation before a successful random wave")
	check(not game.flags.get("queued_army_0", false), "Successful scripted queue clears exactly its source bit")
	check(game.rng_state == 146, "A queued allocation does not consume probabilistic generator RNG")
	game = fresh()
	game.flags.queued_army_0 = true
	game.flags.queued_army_1 = true
	Scenario.on_travel(game)
	check(game.world_armies.get("32", []) == [32] and not game.world_armies.has("40"), "Two queued source bits allocate only the lower bit per world action")
	check(not game.flags.get("queued_army_0", false) and game.flags.get("queued_army_1", false), "Higher queued bit waits until the next world action")
	Scenario.on_travel(game)
	check(game.world_armies.get("40", []) == [50] and not game.flags.get("queued_army_1", false), "The next action allocates and consumes the waiting second queue")

func _test_blocked_queue() -> void:
	var game = fresh()
	var occupied := Armies.add(game, 32, 64, 67, false)
	Armies.add(game, 32, 65, 67, false)
	game.flags.queued_army_0 = true
	game.flags.reinforcement_state_0 = 1
	game.rng_state = 146
	Scenario.on_travel(game)
	check(game.flags.get("queued_army_0", false), "A blocked queued army keeps its source queue bit")
	check(not game.world_armies.has("24") and Armies._ordinary_count(game) == 2, "Failed queued allocation does not fall through to another generator")
	check(game.rng_state == 146, "Failed queued allocation does not advance unrelated wave RNG")
	Armies.remove(game, occupied)
	Scenario.on_travel(game)
	check(game.world_armies.get("32", []) == [65, 32] and not game.flags.get("queued_army_0", false), "Queued army retries once its target has a free source encounter slot")

func _test_queued_boss_mobility() -> void:
	var game = fresh()
	game.flags.queued_army_0 = true
	Scenario.on_travel(game)
	var tatara := str(Armies.instances_at(game, 32)[0])
	check(game.flags.world_mobile_armies.is_empty(), "Queued Tatara group32 has source mobility0")
	# The active party is adjacent to the water gate; the source boss must
	# remain there rather than launching a reinforcement attack on node31.
	Scenario.on_travel(game)
	check(int(Armies.locate(game, tatara).get("node", -1)) == 32 and not game.world_armies.has("31"), "Stationary scripted boss remains at the water gate across travel ticks")
	check(not game.flags.get("inventory_enemy_initiated", false), "Stationary scripted boss cannot create a false enemy-initiated encounter")
	game.flags.queued_army_1 = true
	Scenario.on_travel(game)
	var second := str(Armies.instances_at(game, 40)[0])
	game.world_node = 39
	Scenario.on_travel(game)
	check(int(Armies.locate(game, second).get("node", -1)) == 40, "Queued group50 also keeps source mobility0 beside a player party")
	check(not Scenario._add_army(game, 24, 66, 61), "Malformed source group66 remains uninstantiable")
	check(Scenario._add_army(game, 22, 62, 24) and game.flags.world_mobile_armies.size() == 1, "True source reinforcement group62 retains movement metadata")
	game = fresh()
	var legacy_boss := Armies.add(game, 32, 32, 67)
	check(game.save_game(), "Legacy moving-boss metadata writes an isolated compatibility checkpoint")
	var restored = State.new()
	restored.save_path = SAVE
	check(restored.load_game(), "Legacy moving-boss metadata reloads without discarding the army")
	Scenario._advance_mobile_armies(restored)
	check(int(Armies.locate(restored, legacy_boss).get("node", -1)) == 32 and not restored.flags.get("inventory_enemy_initiated", false), "Old save movement metadata cannot reactivate a source stationary boss")

func _test_forced_dragon_rng() -> void:
	var game = fresh(4)
	game.world_node = 36
	game.flags.world_gate_bits = 33
	game.flags.reinforcement_state_6 = 4
	game.rng_state = 146
	Scenario.on_travel(game)
	check(not game.world_armies.has("36"), "Forced dragon gate uses the first source probability roll and rejects roll78 for the50-percent fourth wave")
	check(game.rng_state == 201, "Forced dragon generator bypasses the ordinary generator selection RNG")
	game = fresh(4)
	game.world_node = 36
	game.flags.world_gate_bits = 33
	game.flags.reinforcement_state_6 = 4
	game.rng_state = 0
	Scenario.on_travel(game)
	check(game.world_armies.get("36", []) == [76] and game.rng_state == 55, "Forced dragon wave accepts its first roll21 and consumes exactly one RNG step")
	game = fresh()
	game.flags.reinforcement_state_0 = 1
	game.rng_state = 146
	Scenario.on_travel(game)
	check(game.world_armies.get("24", []) == [62], "Ordinary source generation still chooses a generator then rolls its wave probability")
	check(game.rng_state == 0, "Ordinary source generator retains both RNG steps")

func _test_reencounter_and_routes() -> void:
	var game = fresh(4)
	game.world_node = 32
	game.route_positions.alm = 32
	var first := Armies.add(game, 33, 64, 67)
	var second := Armies.add(game, 32, 64, 67, false)
	Scenario._advance_mobile_armies(game)
	check(game.flags.get("inventory_attacking_instance_id", "") == first, "A damaged reencounter starts with the arriving army's own identity")
	check(game.start_battle(32), "Native source map starts a converged two-army encounter")
	var dead := 0
	for enemy in game.living("enemy"):
		if str(enemy.get("army_instance", "")) == first and dead == 0:
			enemy.hp = 0
			dead += 1
	game.phase = "enemy"
	game.turn = Inventory.forced_retreat_turn(32)
	var retreat := Inventory.forced_retreat(game)
	check(retreat.get("triggered", false) and retreat.get("instance_id", "") == first, "Source turn limit retreats exactly the arriving army")
	check(int(Armies.locate(game, first).get("node", -1)) == 33 and int(Armies.locate(game, second).get("node", -1)) == 32, "Retreat preserves the stationary same-template army at the battlefield")
	check(game.flags.inventory_defeated_enemy_records.has(first + ":0"), "Retreat persists the defeated soldier under the attacking army identity")
	check(game.switch_route() and game.world_node == 18, "Switching to Celica preserves Alm's world position after retreat")
	check(game.save_game(), "Two-route retreat checkpoint saves to an isolated report path")
	var restored = State.new()
	restored.save_path = SAVE
	check(restored.load_game(), "Two-route retreat checkpoint reloads")
	check(restored.switch_route() and restored.world_node == 32, "Route switch back restores Alm's original battlefield")
	Scenario._advance_mobile_armies(restored)
	check(restored.flags.get("inventory_attacking_instance_id", "") == first and int(Armies.locate(restored, first).get("node", -1)) == 32, "Returning attacker reuses its army identity after route switch and reload")
	check(restored.start_battle(32), "Returned attacker can begin a second native battle")
	var expected := int(restored.catalog.enemy_groups["64"].enemies.size())
	check(restored.living("enemy").filter(func(unit): return str(unit.get("army_instance", "")) == first).size() == expected - 1, "Returned attacker keeps exactly its prior casualty")
	check(restored.living("enemy").filter(func(unit): return str(unit.get("army_instance", "")) == second).size() == expected, "Stationary same-template army retains its complete roster on reencounter")

func _seed_for_choice(choice: int) -> int:
	for seed in range(256):
		if ((((seed + 55) & 255) * 5) >> 8) == choice: return seed
	return 0

func _test_reserved_slot_variants() -> void:
	for chapter in [3, 4]:
		for variant in range(5):
			var game = fresh(chapter)
			game.rng_state = _seed_for_choice(variant)
			game._setup_chapter_armies()
			var selected: Dictionary = game.catalog.chapter_random_armies[variant].by_chapter[str(chapter)]
			var cemetery := str(game.flags.get("world_random_army_instance", ""))
			check(int(Armies.locate(game, cemetery).get("group_id", -1)) == int(selected.group_id), "Chapter%d cemetery choice%d receives the reserved identity" % [chapter, variant])
			check(Armies._ordinary_count(game) == 13 and Armies.add(game, 16, 62, 24).is_empty(), "Chapter%d choice%d preserves all13 ordinary source slots" % [chapter, variant])
			Armies.remove(game, cemetery)
			check(Armies._ordinary_count(game) == 13 and Armies.add(game, 16, 62, 24).is_empty(), "Removing cemetery choice%d never frees an ordinary army slot" % variant)
			var ordinary := str(Armies.instances_at(game, 17 if chapter == 3 else 33)[0])
			Armies.remove(game, ordinary)
			var allocated := Armies.add(game, 16, 62, 24)
			check(not allocated.is_empty() and allocated != cemetery and allocated != ordinary and Armies._ordinary_count(game) == 13, "Replacing an ordinary slot never reuses the retired cemetery or ordinary identity")
			var before: Array = []
			for ids in game.flags.world_army_instances.values(): before.append_array(ids)
			game.chapter = 4 if chapter == 3 else 3
			game._setup_chapter_armies()
			var after: Array = []
			for ids in game.flags.world_army_instances.values(): after.append_array(ids)
			check(after.all(func(identity): return not before.has(identity)) and game.flags.world_mobile_armies.is_empty(), "Chapter rebuild retires prior armies and their movement metadata")
