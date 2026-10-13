extends SceneTree
## Original maps/deployments and recruitment stats, real controller actions.
## This samples mechanics and phase completion, not tactical win difficulty.
const SAVE := "res://reports/test-spot-combat-save.json"
const ALM := ["alm", "lukas", "gray", "silque", "clair", "clive", "python", "luthier", "delthea", "tatiana"]
const CELICA := ["celica", "mae", "boey", "genny", "saber", "valbar", "leo", "kamui", "palla", "catria"]
class RecordingScene extends "res://core/main.gd":
	var observed_actions: Array = []
	func _play_combat(attacker: String, defender: String) -> void:
		observed_actions.append({"kind": "combat", "attacker": attacker, "defender": defender, "weapon": Rules.weapon_index(game.find_unit(attacker))})
		await super._play_combat(attacker, defender)
	func _play_support(caster: String, spell: int, target: String = "", destination: Vector2i = Vector2i(-1, -1)) -> void:
		observed_actions.append({"kind": "support", "caster": caster, "spell": spell})
		await super._play_support(caster, spell, target, destination)
	func _map_spell_feedback(caster: Dictionary, result: Dictionary) -> void:
		observed_actions.append({"kind": str(result.get("action", "")), "caster": str(caster.id), "spawned": result.get("spawned", []).size()})
		await super._map_spell_feedback(caster, result)
var scene
var checks := 0
var errors: Array[String] = []
var samples: Array = []
var boss_probes: Array = []

func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		errors.append(label)
		push_error(label)

func run() -> void:
	scene = RecordingScene.new()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	for spec in [[12, "celica", 2, 8], [15, "celica", 2, 6], [32, "alm", 3, 6], [40, "alm", 4, 5], [42, "alm", 4, 4], [48, "celica", 4, 6], [62, "alm", 5, 4]]:
		await sample(int(spec[0]), str(spec[1]), int(spec[2]), int(spec[3]))
	await boss_counter_checks()
	scene.audio.stop_all()
	scene.queue_free()
	await process_frame
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	var report := {"checks": checks, "errors": errors, "samples": samples, "boss_probes": boss_probes,
		"scope": "Seven original maps, initial source recruitment stats, original enemy groups and deployment, real AI/movement/combat/animation/phase controllers, instant timing, isolated save.",
		"limits": "Sampling starts directly at these battles and does not model earlier level-ups or prove a full campaign playthrough. Instant timing does not validate visible real-time animation."}
	var file := FileAccess.open("res://reports/spot-combat-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	file.close()
	print(JSON.stringify(report))
	quit(0 if errors.is_empty() else 1)

func sample(id: int, route: String, chapter: int, rounds: int) -> void:
	var game = scene.game
	game.new_game()
	game.save_path = SAVE
	game.chapter = chapter
	game.world_armies.clear()
	for side in ["alm", "celica"]:
		game.route = side
		game.party = []
		var members: Array = ALM.duplicate() if side == "alm" else CELICA.duplicate()
		if side == "alm" and id in [32, 40]:
			members[members.find("tatiana")] = "mathilda"
			if id == 32: members[members.find("delthea")] = "tobin"
		for member in members:
			if chapter == 2 and side == "celica" and member in ["palla", "catria"]: continue
			game.recruit(member)
	game.route = route
	game.party = game.parties[route].duplicate()
	game.world_node = id if id < 49 else 77
	# Seed100 exercises the boat Cantor's real >=128 conjure branch on
	# its first enemy turn, without changing units, flags or decisions.
	game.rng_state = 100 if id == 12 else (id * 17) & 255
	game.frame_counter = 0
	if id == 62: game.flags.scenario_final_merge_ready = true
	check(game.start_battle(id, [], true), "map %d starts" % id)
	check(game.mode == "battle", "map %d is battle" % id)
	game.story_events.clear()
	scene.view = "battle"
	scene.busy = false
	scene.batch_running = false
	scene.ui_mode = "inspect"
	scene._clear_menu()
	scene.battle_animation.reset()
	scene.battle_animation.missing_animations.clear()
	scene.map_effects.reset()
	scene.map_effects.missing_programs.clear()
	scene.observed_actions.clear()
	var record := {"map": id, "name": game.battle_data.name_zh, "route": route,
		"initial_player": game.living("player").size(), "initial_enemy": game.living("enemy").size(),
		"rounds": []}
	for round_index in range(rounds):
		if game.battle_outcome != "": break
		var before := int(game.turn)
		# This is the same auto command exposed in the player turn menu.
		await scene._auto_player(false)
		var label := "map %d round %d" % [id, round_index + 1]
		check(not scene.busy and not scene.batch_running, label + " releases phase locks")
		check(game.turn == before + 1 or game.battle_outcome != "", label + " advances a full turn or settles")
		check(scene.view in ["battle", "victory", "defeat", "ending"], label + " returns to gameplay/result")
		check(scene.battle_animation.missing_animations.is_empty(), label + " uses available original combat programs")
		check(scene.map_effects.missing_programs.is_empty(), label + " uses available original map programs")
		check(scene.map_actor_alpha.is_empty() and scene.map_offset == Vector2.ZERO, label + " restores map feedback")
		var cells: Dictionary = {}
		var slots: Dictionary = {}
		for unit in game.units:
			check(int(unit.hp) >= 0 and int(unit.hp) <= int(unit.max_hp), label + " bounded HP " + str(unit.id))
			if int(unit.hp) <= 0: continue
			check(game.in_bounds(game.pos(unit)), label + " in-bounds " + str(unit.id))
			check(not cells.has(game.pos(unit)), label + " distinct position " + str(unit.id))
			cells[game.pos(unit)] = unit.id
			var key = str(unit.side) + ":" + str(unit.get("player_slot" if unit.side == "player" else "enemy_slot", -1))
			check(not slots.has(key), label + " distinct living slot " + str(unit.id))
			slots[key] = unit.id
		check(game.living("player").size() <= 20 and game.living("enemy").size() <= 20, label + " source capacity")
		check(game.save_path == SAVE, label + " save stays isolated")
		record.rounds.append({"turn": game.turn, "living_player": game.living("player").size(), "living_enemy": game.living("enemy").size(), "outcome": game.battle_outcome,
			"total_summoned": game.units.filter(func(u): return bool(u.get("temporary", false))).size(), "kills": game.kills})
		print("SPOT_COMBAT_PROGRESS ", id, " ", round_index + 1, " ", game.battle_outcome)
		await process_frame
	record.outcome = game.battle_outcome
	record.missing_animations = scene.battle_animation.missing_animations.duplicate()
	record.missing_map_programs = scene.map_effects.missing_programs.duplicate()
	record.actions = scene.observed_actions.duplicate(true)
	samples.append(record)

func boss_counter_checks() -> void:
	for spec in [[48, "celica", 134], [62, "alm", 167]]:
		var game = scene.game
		game.new_game()
		game.chapter = 5
		game.world_armies.clear()
		game.route = str(spec[1])
		game.party = []
		game.recruit(str(spec[1]))
		game.world_node = 77 if int(spec[0]) == 62 else 48
		if int(spec[0]) == 62: game.flags.scenario_final_merge_ready = true
		game.start_battle(int(spec[0]), [], true)
		game.story_events.clear()
		var boss: Dictionary = game.units.filter(func(u): return int(u.character_id) == int(spec[2]))[0]
		var hero: Dictionary = game.find_unit(str(spec[1]))
		# Place the player on a legal adjacent cell, without altering either
		# unit's source stats. The HP51 branch is Duma's normal final form.
		for direction in [Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP]:
			var cell = game.pos(boss) + direction
			if game.in_bounds(cell) and game.can_stop(hero, cell) and game.movement_cost(hero, cell) < 255:
				hero.position = [cell.x, cell.y]
				break
		if int(spec[2]) == 167: boss.hp = 51
		game.turn = 1
		var exchange: Dictionary = game.plan_combat(str(hero.id), str(boss.id))
		check(not exchange.is_empty(), "protected boss can enter actual exchange")
		check(exchange.events.any(func(e): return str(e.attacker) == str(boss.id)), "boss %d retaliates while protected" % int(spec[2]))
		check(exchange.events.all(func(e): return str(e.attacker) != str(hero.id)), "boss %d cancels only the protected incoming attack" % int(spec[2]))
		if int(spec[2]) == 134:
			game.turn = 4
			var vulnerable: Dictionary = game.plan_combat(str(hero.id), str(boss.id))
			check(vulnerable.events.any(func(e): return str(e.attacker) == str(hero.id)), "Jedah can receive attacks on turn4")
			game.turn = 1
		scene.view = "battle"
		scene.busy = false
		scene.batch_running = true
		scene._clear_menu()
		await scene._play_combat(str(hero.id), str(boss.id))
		check(scene.combat.events.any(func(e): return str(e.attacker) == str(boss.id)), "actual boss controller executes protected counter")
		check(scene.battle_animation.contact_calls == scene.combat.events.size(), "protected boss counter commits once per real contact")
		check(scene.battle_animation.missing_animations.is_empty(), "protected boss counter has original animation")
		boss_probes.append({"map": int(spec[0]), "boss_id": int(spec[2]), "turn": game.turn,
			"events": scene.combat.events.duplicate(true), "contacts": scene.battle_animation.contact_calls,
			"scope": "Original actors and map; player relocated to a legal adjacent cell; Duma HP51 selects his final form. Validates protected counter and animation settlement."})
		scene.batch_running = false
