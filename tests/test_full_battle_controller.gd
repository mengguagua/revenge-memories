extends SceneTree
## Real main/controller integration, without replacing its state or audio class.
## Flat-map fixtures isolate source decisions; all action/phase methods are real.
const Items = preload("res://core/item_rules.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const SAVE = "res://reports/test-full-battle-controller-save.json"
var scene
var checks = 0
var failures: Array[String] = []
var scenarios: Array = []

func _initialize() -> void: call_deferred("run")
func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func actor(id: String, cid: int, at: Vector2i, side: String = "enemy") -> Dictionary:
	var unit = Items.data().promotion_bases[str(cid)].duplicate(true)
	unit.merge({"id": id, "class_id": cid, "class": str(scene.game.catalog.classes[str(cid)].key),
		"name_zh": id, "character_id": 176 + cid if side == "enemy" else 1,
		"name_id": 176 + cid if side == "enemy" else 1, "side": side, "position": [at.x, at.y],
		"level": 1, "exp": 0, "exp_value": 30, "hp": 40, "max_hp": 40,
		"item_id": 0, "magic_flags": 0, "ai_flags": 0, "raw_ai_flags": 0,
		"resistance": 10, "move": 0, "luck": 0, "skill": 0, "speed": 0,
		"strength": 5, "defence": 10, "acted": false, "controllable": side == "player",
		"no_experience": false, "route": "alm", "dead": false}, true)
	return unit

func setup(actors: Array, seed: int = 0) -> void:
	scene.game.new_game()
	scene.game.save_path = SAVE
	scene.game.units = actors
	scene.game.mode = "battle"
	scene.game.phase = "player"
	scene.game.stage_id = 1
	scene.game.world_node = 1
	scene.game.chapter = 1
	scene.game.turn = 1
	scene.game.rng_state = seed
	scene.game.frame_counter = 0
	scene.game.battle_outcome = ""
	scene.game.story_events.clear()
	scene.game.flags.pending_loot = []
	scene.game.flags.inventory_processed_deaths = {}
	scene.game.convoy = {"alm": [], "celica": []}
	scene.game.battle_data = scene.game.stages[1].duplicate(true)
	var data = scene.game.battle_data
	data.map.width = 16; data.map.height = 16
	data.map.tiles = []; data.map.tiles.resize(256); data.map.tiles.fill(0)
	data.terrain.tile_categories["0"] = 0
	for cid in range(1, 23):
		var costs = []; costs.resize(32); costs.fill(1)
		data.terrain.movement_by_class_and_category[str(cid)] = costs
	var slots = {"player": 0, "enemy": 0}
	for unit in actors:
		var key = "player_slot" if unit.side == "player" else "enemy_slot"
		unit[key] = slots[unit.side]
		slots[unit.side] += 1
		if unit.side == "player" and not bool(unit.get("temporary", false)):
			scene.game.roster[str(unit.id)] = unit.duplicate(true)
	scene.game.cursor = Vector2i(3, 3)
	scene.game.selected_id = ""
	scene.view = "battle"
	scene.ui_mode = "inspect"
	scene.busy = false
	scene.batch_running = true # Direct-action cases do not auto-end player phase.
	scene._clear_menu()
	scene.battle_animation.reset()
	scene.map_effects.reset()
	scene.map_actor_alpha.clear()
	scene.map_offset = Vector2.ZERO
	scene.self_modulate = Color.WHITE

func clean_effects(label: String) -> void:
	check(scene.map_actor_alpha.is_empty(), label + " leaves no hidden actors")
	check(scene.map_offset == Vector2.ZERO and scene.self_modulate == Color.WHITE, label + " restores screen transform/color")
	check(not scene.map_effects._active and scene.map_effects._hidden_ids.is_empty(), label + " clears effect playback")
	check(scene.map_effects.missing_programs.is_empty() and scene.battle_animation.missing_animations.is_empty(), label + " has no substituted or missing original animation")

func run() -> void:
	scene = load("res://scenes/main.tscn").instantiate()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	await test_combat_and_loot()
	await test_support()
	await test_invoke_and_real_phase()
	await test_witch_and_quake()
	test_loot_choice()
	check(FileAccess.file_exists(SAVE), "controller saved only to its isolated fixture")
	check(scene.game.save_path == SAVE, "controller did not switch to the user's save path")
	scene.audio.stop_all()
	scene.queue_free()
	await process_frame
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	var report = {"checks": checks, "failure_count": failures.size(), "failures": failures,
		"scenarios": scenarios, "scope": "headless real main/state/renderer/audio controllers; instant timing; isolated save; seeded actions and one complete player-auto/enemy/player phase",
		"limits": "Flat-map fixtures verify the new controller integration, not full campaign tactics, visible graphics, or real-time timing."}
	var file = FileAccess.open("res://reports/full-battle-controller-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n"); file.close()
	print(JSON.stringify(report)); quit(0 if failures.is_empty() else 1)

func test_combat_and_loot() -> void:
	var alm = actor("alm", 21, Vector2i(3, 3), "player")
	alm.item_id = 10; alm.skill = 40; alm.strength = 20; alm.no_experience = true
	var victim = actor("loot_enemy", 6, Vector2i(4, 3))
	victim.hp = 1; victim.item_id = 20
	var reserve = actor("reserve", 6, Vector2i(13, 13))
	setup([alm, victim, reserve])
	await scene._run_ai_unit(alm)
	check(victim.hp == 0 and alm.acted, "real AI action enters combat and commits its contact")
	check(scene.game.kills == 1, "real combat records one enemy death")
	check(scene.game.convoy.alm == [20] and alm.item_id == 10, "instant combat loot preserves held item and stores new item")
	check(scene.game.flags.pending_loot.is_empty(), "real combat resumes after resolving loot")
	check(scene.view == "battle" and scene.game.battle_outcome == "", "combat returns to continuing map")
	check(scene.battle_animation.contact_calls >= 1, "actual battle animation commits source contact")
	clean_effects("combat")
	scenarios.append("_run_ai_unit physical combat -> source animation -> death/drop -> instant loot storage")

func test_support() -> void:
	var alm = actor("alm", 21, Vector2i(4, 3), "player"); alm.hp = 5
	var healer = actor("silque", 18, Vector2i(3, 3), "player")
	healer.character_id = 14; healer.name_id = 14; healer.magic_flags = 1; healer.strength = 10
	var reserve = actor("reserve", 6, Vector2i(13, 13))
	setup([alm, healer, reserve])
	var before = int(healer.hp)
	await scene._play_support("silque", 40, "alm")
	check(alm.hp == 15 and healer.hp == before - Items.cost(40), "close-up support heals and charges source HP exactly once")
	check(healer.acted and scene.battle_animation.contact_calls == 1, "support visual contact does not repeat settlement")
	check(scene.view == "battle" and not scene.busy, "close-up support restores map interaction")
	clean_effects("player recovery")
	var enemy_healer = actor("enemy_healer", 15, Vector2i(5, 5)); enemy_healer.magic_flags = 16; enemy_healer.strength = 10
	var injured = actor("injured", 2, Vector2i(5, 6)); injured.hp = 2
	alm = actor("alm", 21, Vector2i(13, 13), "player")
	setup([alm, enemy_healer, injured]); scene.game.phase = "enemy"
	var ticks = scene.map_effects.ticks_played
	await scene._run_ai_unit(enemy_healer)
	check(injured.hp == 12 and enemy_healer.hp == 40 - Items.cost(35), "enemy AI Recover35 heals and spends correct HP")
	check(scene.map_effects.ticks_played - ticks == 20, "enemy recovery uses original map program10, not close-up Fire")
	check(enemy_healer.acted, "enemy recovery consumes its action")
	clean_effects("enemy recovery")
	scenarios.append("_play_support40 close-up and _run_ai_unit Recover35 map feedback")

func test_invoke_and_real_phase() -> void:
	var alm = actor("alm", 21, Vector2i(2, 2), "player"); alm.acted = true
	var genny = actor("genny", 18, Vector2i(4, 4), "player")
	genny.character_id = 15; genny.name_id = 15; genny.magic_flags = 32; genny.strength = 6
	var cantor = actor("cantor", 19, Vector2i(12, 12)); cantor.magic_flags = 32
	setup([alm, genny, cantor])
	await scene._play_support("genny", 45)
	var phantoms: Array = scene.game.living("player").filter(func(u): return bool(u.get("temporary", false)))
	check(phantoms.size() >= 2, "real Invoke creates native player phantoms")
	check(phantoms.all(func(u): return u.character_id == 35 and u.class_id == 6 and u.no_experience and not u.controllable and not u.acted), "Invoke constructor preserves original identity, action state and no EXP")
	var player_slots: Array = phantoms.map(func(u): return int(u.player_slot))
	check(player_slots[0] == 2 and player_slots.all(func(s): return player_slots.count(s) == 1), "player summons receive unique earliest free source slots")
	var positions: Dictionary = {}
	for unit in phantoms: positions[str(unit.id)] = unit.position.duplicate()
	clean_effects("Invoke")
	# This is the actual main phase controller. Summoned allies act first;
	# the Cantor's new later slots must be visited in the same enemy phase.
	scene.game.rng_state = 73
	scene.busy = false; scene.batch_running = false
	await scene._enemy_phase()
	var enemy_summons: Array = scene.game.living("enemy").filter(func(u): return bool(u.get("temporary", false)))
	check(scene.game.phase == "player" and scene.game.turn == 2, "real phase runs player auto-allies -> enemy -> next player turn")
	check(phantoms.any(func(u): return u.position != positions[str(u.id)]), "new player phantoms act automatically before enemy phase")
	check(enemy_summons.size() > 0, "Cantor conjures through the real enemy phase loop")
	check(enemy_summons.all(func(u): return u.acted and (int(u.ai_flags) & 8) == 0), "new later enemy slots consume skip-one flag in their creation phase")
	check(enemy_summons.all(func(u): return not u.no_experience and int(u.exp_value) > 0), "enemy summons preserve original experience rewards")
	var enemy_slots: Array = enemy_summons.map(func(u): return int(u.enemy_slot))
	check(enemy_slots[0] == 1 and enemy_slots.all(func(s): return enemy_slots.count(s) == 1), "enemy summons use unique source slots and reserve slot0")
	check(not scene.busy and not scene.batch_running and scene.view == "battle", "phase controller releases all busy guards")
	clean_effects("complete phase")
	scenarios.append("Invoke45 -> player source slots -> actual autonomous-ally/enemy phase -> dynamic Cantor slots")

func test_witch_and_quake() -> void:
	var alm = actor("alm", 21, Vector2i(8, 8), "player")
	var witch = actor("witch", 16, Vector2i(2, 2)); witch.magic_flags = 1
	setup([alm, witch], 201); scene.game.phase = "enemy"
	var ticks = scene.map_effects.ticks_played
	await scene._run_ai_unit(witch)
	check(witch.position == [7, 12] and witch.acted, "real witch AI moves through source teleport landing and consumes action")
	check(witch.hp == 40 and scene.map_effects.ticks_played - ticks == 120, "map teleport has two original60-tick programs without HP mutation")
	clean_effects("witch teleport")
	var duma = actor("duma", 21, Vector2i(4, 4)); duma.character_id = 167; duma.name_id = 167; duma.max_hp = 182
	alm = actor("alm", 21, Vector2i(13, 13), "player")
	setup([alm, duma], 201); scene.game.phase = "enemy"
	ticks = scene.map_effects.ticks_played
	await scene._run_ai_unit(duma)
	check(duma.acted and alm.hp == 26 and duma.hp == 38, "real Duma Gaia uses shared side damage rolls and actual HP settlement")
	check(scene.map_effects.ticks_played - ticks == 440, "Gaia uses original400-tick shake and map feedback on both sides")
	check(scene.game.battle_outcome == "" and alm.hp >= 1 and duma.hp >= 1, "Gaia preserves nonlethal source floor")
	clean_effects("Gaia")
	scenarios.append("_run_ai_unit ordinary witch teleport and Duma Gaia with original map feedback")

func test_loot_choice() -> void:
	var alm = actor("alm", 21, Vector2i(3, 3), "player"); alm.item_id = 10
	var enemy = actor("loot_enemy", 6, Vector2i(4, 3)); enemy.hp = 0; enemy.item_id = 20
	setup([alm, enemy, actor("reserve", 6, Vector2i(13, 13))])
	var record = Inventory.on_death(scene.game, enemy, alm)
	check(record.get("destination") == "pending", "occupied slot enters real inventory choice queue")
	scene._show_loot_menu()
	check(scene.view == "loot" and scene.menu_actions == ["store", "new"], "controller exposes storage/equip loot choices")
	scene.menu_selected = 1; scene._accept()
	check(alm.item_id == 20 and scene.game.convoy.alm == [10], "actual accept swaps loot and stores displaced item")
	check(scene.game.flags.pending_loot.is_empty() and scene.view == "battle", "loot accept returns to battle without pending choice")
	alm.item_id = 10; scene.game.roster.alm.item_id = 10
	scene.game.convoy.alm.resize(40); scene.game.convoy.alm.fill(2)
	scene.game.flags.pending_loot = [{"kind": "loot", "item_id": 20, "unit_id": "alm", "enemy_id": "second_loot", "route": "alm"}]
	scene._show_loot_menu(); scene.menu_selected = 0; scene._accept()
	check(scene.view == "loot_confirm" and alm.item_id == 10 and scene.game.flags.pending_loot.size() == 1, "full inventory discard requires explicit confirmation")
	scene.menu_selected = 0; scene._accept()
	check(scene.view == "loot" and scene.game.flags.pending_loot.size() == 1, "cancel confirmation preserves both items and pending queue")
	scene.menu_selected = 1; scene._accept(); scene.menu_selected = 1; scene._accept()
	check(alm.item_id == 20 and scene.game.convoy.alm.size() == 40 and scene.game.flags.pending_loot.is_empty(), "confirmed replacement preserves full convoy and resolves the choice")
	scenarios.append("real loot accept, full40-item convoy confirmation and cancellation")
