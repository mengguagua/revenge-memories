extends SceneTree
## Real map25 combat: reachable level6 Deen with a single SKL growth,
## Dark Sword, original Bray stats, and the real native RNG.
const Rules = preload("res://core/combat_rules.gd")
const SAVE := "res://reports/test-recoil-feedback-save.json"

class RecordingScene extends "res://core/main.gd":
	var recoil_observations: Array = []
	var recoil_event: Dictionary = {}
	var recording_recoil := false
	func _contact(event: Dictionary) -> void:
		if int(event.get("self_damage", 0)) > 0:
			recording_recoil = true
			recoil_event = event.duplicate(true)
		await super._contact(event)
		recording_recoil = false
	func _wait(seconds: float) -> void:
		if recording_recoil:
			recoil_observations.append({"hit_id": combat_hit_id, "message": combat_message,
				"source_hp": int(combat_hp.get(str(recoil_event.attacker), -1)),
				"target_hp": int(combat_hp.get(str(recoil_event.defender), -1))})
		await super._wait(seconds)

var checks := 0
var errors: Array[String] = []
func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		errors.append(label)
		push_error(label)

func run() -> void:
	var scene := RecordingScene.new()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	await process_frame
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	var game = scene.game
	game.new_game()
	game.chapter = 3
	game.route = "celica"
	game.party = []
	game.recruit("celica")
	game.recruit("deen")
	var grown: Dictionary = game.roster.deen
	var growth: Dictionary = Rules.growth_result(grown, [99, 99, 99, 99, 1, 99])
	check(growth.skill == 1 and growth.values().count(1) == 1, "source Deen growth table permits a single SKL gain")
	grown.skill = int(grown.skill) + int(growth.skill)
	grown.level = int(grown.level) + 1
	grown.item_id = 14
	game.world_armies.clear()
	game.world_node = 25
	check(game.start_battle(25, [], true), "original valley battle starts")
	game.story_events.clear()
	var hero: Dictionary = game.find_unit("deen")
	var target: Dictionary = game.find_unit("g25_01")
	check(not hero.is_empty() and not target.is_empty(), "source Deen and source Bray are present")
	for direction in [Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP]:
		var cell = game.pos(target) + direction
		if game.in_bounds(cell) and game.can_stop(hero, cell) and game.movement_cost(hero, cell) < 255:
			hero.position = [cell.x, cell.y]
			break
	check(game.can_attack(hero, target), "player is on a legal adjacent attack cell")
	check(hero.skill == 18 and hero.class_id == 9 and hero.luck == 6, "only legitimate SKL growth and equipped item differ from source stats")
	var found_seed := -1
	var planned: Dictionary = {}
	var recoil: Dictionary = {}
	for seed in range(256):
		game.rng_state = seed
		var exchange: Dictionary = game.plan_combat("deen", "g25_01")
		for event in exchange.events:
			if event.attacker == "deen" and int(event.self_damage) > 0 and bool(event.hit) and int(event.critical_roll) <= int(exchange.stats.deen.critical):
				found_seed = seed
				planned = exchange
				recoil = event
				break
		if found_seed >= 0: break
	check(found_seed >= 0, "real RNG produces successful critical pre-roll plus Dark Sword recoil")
	if found_seed < 0:
		print(JSON.stringify({"checks": checks, "errors": errors}))
		quit(1)
		return
	check(not bool(recoil.critical), "recoil cancels critical display despite a successful critical pre-roll")
	check(int(recoil.damage) == 0 and int(recoil.hp_after) == int(recoil.hp_before), "recoil leaves defender HP untouched")
	check(int(recoil.source_hp_before) - int(recoil.source_hp_after) == int(recoil.self_damage), "recoil charges only its source damage")
	game.rng_state = found_seed
	scene.view = "battle"
	scene.busy = false
	scene.batch_running = true
	scene.ui_mode = "inspect"
	scene._clear_menu()
	await scene._play_combat("deen", "g25_01")
	check(not scene.recoil_event.is_empty(), "real combat animation reaches recoil contact")
	check(not scene.recoil_observations.is_empty(), "real contact feedback exposes HP animation ticks")
	var source_hp: Array[int] = []
	check(scene.recoil_observations.all(func(o): return str(o.hit_id) == "deen"), "recoil hit feedback selects the wielder")
	check(scene.recoil_observations.all(func(o): return str(o.message) == "反噬"), "recoil explicitly labels its effect")
	check(scene.recoil_observations.all(func(o): return int(o.target_hp) == int(recoil.hp_before)), "defender HP cells do not decrease during recoil")
	for observed in scene.recoil_observations:
		if source_hp.is_empty() or source_hp[-1] != int(observed.source_hp): source_hp.append(int(observed.source_hp))
	var expected_hp: Array[int] = []
	for hp in range(int(recoil.source_hp_before), int(recoil.source_hp_after) - 1, -1): expected_hp.append(hp)
	check(source_hp == expected_hp, "source HP cells decrease exactly one HP at a time")
	check(scene.battle_animation.contact_calls == planned.events.size(), "every original strike contacts exactly once")
	check(scene.battle_animation.missing_animations.is_empty(), "Dark Sword and Bray use available source animations")
	check(game.save_path == SAVE, "regression never touches user save")
	var recoil_contacts: int = scene.battle_animation.contact_calls
	var absorbed_recoil: Dictionary = await cancelled_recoil_checks(scene)
	var report := {"checks": checks, "errors": errors, "seed": found_seed, "map": 25,
		"growth": growth, "event": recoil, "observed_source_hp": source_hp,
		"observations": scene.recoil_observations, "contacts": recoil_contacts,
		"absorbed_recoil": absorbed_recoil,
		"scope": "Real maps25/3, original enemies, Deen plus one legal SKL growth and Alm plus17 legal DEF/SKL growths; real RNG/plan/combat/animation/contact, including original zero-damage recoil cancellation; isolated save, headless instant timing."}
	var file := FileAccess.open("res://reports/recoil-feedback-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	file.close()
	scene.audio.stop_all()
	scene.queue_free()
	await process_frame
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	print(JSON.stringify({"checks": checks, "errors": errors, "seed": found_seed, "observed_source_hp": source_hp}))
	quit(0 if errors.is_empty() else 1)

func cancelled_recoil_checks(scene) -> Dictionary:
	var game = scene.game
	game.new_game()
	game.save_path = SAVE
	var grown: Dictionary = game.roster.alm
	for _level in range(17):
		var delta: Dictionary = Rules.growth_result(grown, [99, 1, 99, 99, 1, 99])
		grown.defence = int(grown.defence) + int(delta.defence)
		grown.skill = int(grown.skill) + int(delta.skill)
		grown.level = int(grown.level) + 1
	grown.item_id = 14
	game.world_armies.clear()
	game.world_node = 3
	check(game.start_battle(3, [], true), "original map3 accepts source-growth Dark Sword Alm")
	game.story_events.clear()
	var hero: Dictionary = game.find_unit("alm")
	var target: Dictionary = game.find_unit("g03_02")
	check(hero.level == 18 and hero.defence == 23 and hero.skill == 24 and hero.strength == 10, "17 legal DEF/SKL growths reach the source recoil cancellation boundary")
	for direction in [Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP]:
		var cell = game.pos(target) + direction
		if game.in_bounds(cell) and game.can_stop(hero, cell) and game.movement_cost(hero, cell) < 255:
			hero.position = [cell.x, cell.y]
			break
	for defence in [23, 24]:
		var boundary := hero.duplicate(true)
		boundary.defence = defence
		var effect := Rules.strike_effect(boundary, target, true, true, 0, 1)
		check(effect.self_damage == 0 and effect.damage > 0 and effect.critical, "L0985B5 cancels nonpositive recoil without canceling damage/critical at DEF%d" % defence)
	var found_seed := -1
	var recoil_roll := -1
	var planned: Dictionary = {}
	for seed in range(256):
		game.rng_state = seed
		var counter := Rules.default_counter(target, 1)
		# Advance the original hit/critical pre-rolls, then inspect the first
		# Dark Sword roll; reset before the actual unmodified planner runs.
		for role in Rules.strike_sequence(hero, counter, 1):
			var source: Dictionary = hero if role == "attacker" else counter
			var opponent: Dictionary = counter if role == "attacker" else hero
			var stats := Rules.attack_stats(source, opponent, game.terrain_avoid(game.pos(opponent)))
			game.random_bounded(100)
			if int(stats.critical) > 0: game.random_bounded(100)
		var candidate_roll: int = game.random_bounded(100)
		game.rng_state = seed
		var exchange: Dictionary = game.plan_combat("alm", "g03_02")
		if exchange.events.is_empty(): continue
		var event: Dictionary = exchange.events[0]
		if event.attacker == "alm" and event.hit and int(event.critical_roll) <= int(exchange.stats.alm.critical) and candidate_roll <= 20 - int(hero.luck):
			found_seed = seed
			recoil_roll = candidate_roll
			planned = exchange
			break
	check(found_seed >= 0, "real RNG naturally combines critical pre-roll and the canceled recoil branch")
	if found_seed < 0: return {}
	var first: Dictionary = planned.events[0]
	check(first.critical and first.self_damage == 0 and first.damage > 0 and first.source_hp_before == first.source_hp_after, "actual planner retains enemy damage/critical when source defence cancels recoil")
	game.rng_state = found_seed
	scene.view = "battle"
	scene.busy = false
	scene.batch_running = true
	scene.ui_mode = "inspect"
	scene._clear_menu()
	await scene._play_combat("alm", "g03_02")
	check(scene.combat.events[0].critical and target.hp == 0 and hero.hp == first.source_hp_before, "real canceled-recoil controller commits the critical to the enemy without self damage")
	check(scene.battle_animation.contact_calls == planned.events.size() and scene.battle_animation.missing_animations.is_empty(), "canceled recoil uses original animation and one contact per strike")
	return {"map": 3, "seed": found_seed, "recoil_roll": recoil_roll, "event": first,
		"source": "bank009 L098564-L0985BA; nonpositive own damage clears $035D recoil flag"}
