extends SceneTree
## Real controller suspend/resume spot checks. Only this disposable save is used.
const State = preload("res://core/game_state.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const Worlds = preload("res://core/world_armies.gd")
const SAVE := "res://reports/test-spot-save.json"
var scene
var checks := 0
var failures: Array[String] = []
var scenarios: Array[String] = []

func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func fresh(stage: int = 1):
	var g = State.new()
	g.save_path = SAVE
	g.new_game()
	g.recruit("lukas")
	g.chapter = 4 if stage > 7 else 1
	g.world_node = stage
	g.start_battle(stage)
	g.story_events.clear()
	return g

func load_state():
	var g = State.new()
	g.save_path = SAVE
	check(g.load_game(), "isolated suspend load succeeds")
	return g

func source_unit(g, cid: int) -> Dictionary:
	for u in g.units:
		if int(u.get("source_enemy_character_id", u.get("character_id", 0))) == cid: return u
	return {}

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

func continue_title() -> void:
	scene._show_title()
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	await process_frame

func run() -> void:
	_test_pending_loot_and_retry()
	_test_summons_and_retreat()
	_test_special_victory()
	await _test_real_loot_resume()
	await _test_reward_resume()
	await _test_enemy_resume()
	await _test_story_resume()
	await _test_hub_resume()
	await _test_batched_final_kill()
	if is_instance_valid(scene):
		scene.audio.stop_all()
		scene.queue_free()
		await process_frame
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	var report := {"checks":checks,"failures":failures,"scenarios":scenarios,
		"scope":"headless real GameState and main title-continue; actual suspended UI decisions and phase continuation; isolated save only",
		"limits":"Bounded milestone fixtures, not complete natural playthroughs; no graphics or audio listening."}
	var file := FileAccess.open("res://reports/spot-save-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("SPOT SAVE: %d checks, %d failures" % [checks,failures.size()])
	quit(0 if failures.is_empty() else 1)

func _test_pending_loot_and_retry() -> void:
	var g = fresh()
	g.find_unit("alm").item_id = 10
	g.roster.alm.item_id = 10
	var target: Dictionary = g.living("enemy")[0]
	target.item_id = 20
	g.battle_start_snapshot = g._capture_battle_start()
	g.commit_strike({"attacker":"alm","defender":target.id,"hp_after":0})
	check(g.flags.pending_loot.size() == 1, "occupied killer slot creates one persistent pending item")
	check(g.save_game(), "pending item checkpoint writes atomically")
	var loaded = load_state()
	check(loaded.flags.pending_loot.size() == 1 and int(loaded.find_unit(str(target.id)).item_id) == 0, "pending item reload retains ownership exactly once")
	check(Inventory.resolve_loot(loaded,"new"), "loaded pending choice can replace current item")
	check(int(loaded.find_unit("alm").item_id) == 20 and int(loaded.roster.alm.item_id) == 20 and loaded.convoy.alm == [10], "equipped and roster item synchronized while displaced item stored")
	check(not Inventory.resolve_loot(loaded,"new"), "resolved choice cannot duplicate item")
	loaded.save_game()
	loaded = load_state()
	check(loaded.flags.pending_loot.is_empty() and loaded.convoy.alm.size() == 1 and int(loaded.convoy.alm[0]) == 10, "resolved item remains single after second load")
	check(loaded.retry_battle(), "loaded battle checkpoint retry succeeds")
	check(int(loaded.find_unit("alm").item_id) == 10 and loaded.convoy.alm.is_empty() and int(loaded.find_unit(str(target.id)).item_id) == 20, "retry atomically undoes equip/convoy/drop and restores source enemy")
	check(loaded.flags.pending_loot.is_empty(), "retry does not retain stale item decision")
	# A normal party death sends an item to the correct route and cannot repeat.
	var ally: Dictionary = loaded.find_unit("lukas")
	ally.item_id = 2
	loaded.commit_strike({"attacker":target.id,"defender":"lukas","hp_after":0})
	loaded.commit_strike({"attacker":target.id,"defender":"lukas","hp_after":0})
	loaded.save_game()
	loaded = load_state()
	check(loaded.convoy.alm.size() == 1 and int(loaded.convoy.alm[0]) == 2 and int(loaded.find_unit("lukas").item_id) == 0, "death storage remains single across repeated contact and suspend")
	scenarios.append("pending loot -> loaded choice -> resave -> retry; party death storage")

func _test_summons_and_retreat() -> void:
	var g = fresh()
	g.recruit("silque")
	g.start_battle(1)
	var caster: Dictionary = g.find_unit("silque")
	caster.position = [6,7]
	var spawn: Array = g._summon(caster,10,3)
	check(not spawn.is_empty(), "source Invoke produces summons in real stage")
	g.save_game()
	var loaded = load_state()
	for id in spawn:
		var u: Dictionary = loaded.find_unit(str(id))
		check(not u.is_empty() and bool(u.temporary) and not bool(u.controllable) and u.summoner_id == "silque", "summon identity/ownership/control survives reload")
	var enemy: Dictionary = loaded.living("enemy")[0]
	loaded.commit_strike({"attacker":enemy.id,"defender":"silque","hp_after":0})
	for id in spawn: check(int(loaded.find_unit(str(id)).hp) == 0 and bool(loaded.find_unit(str(id)).vanished), "loaded phantom cleanup follows caster death")
	loaded.save_game()
	loaded = load_state()
	check(loaded.retry_battle() and loaded.units.all(func(u): return not bool(u.get("temporary",false))), "retry removes all later summoned units")
	# Dead enemy records survive world return/re-entry without re-dropping loot.
	g = fresh(4)
	g.previous_world_node = 3
	g.world_armies.erase("3")
	g.world_armies["4"] = [4]
	Worlds.ensure(g)
	g.encounter_groups = [4]
	g.find_unit("alm").item_id = 0
	enemy = g.living("enemy")[0]
	enemy.item_id = 20
	var key := Inventory._enemy_key(enemy)
	g.commit_strike({"attacker":"alm","defender":enemy.id,"hp_after":0})
	g.turn += 1
	check(Inventory.refresh_retreat(g,0) and Inventory.retreat(g), "real combat casualty can retreat through original source chance")
	check(g.mode == "world" and g.world_node == 3 and g.flags.inventory_defeated_enemy_records.has(key), "retreat persists casualty and returns correct node")
	g.save_game()
	loaded = load_state()
	check(int(loaded.roster.alm.item_id) == 20 and loaded.world_armies.has("4"), "retreat suspend preserves loot and surviving army")
	check(loaded.start_battle(4), "re-entered battle starts after retreat suspend")
	check(not loaded.units.any(func(u): return u.side == "enemy" and Inventory._enemy_key(u) == key), "defeated record not respawned after loaded retreat")
	scenarios.append("Invoke suspend/caster death/retry; retreat suspend/re-entry casualty and loot")

func _test_special_victory() -> void:
	var g = fresh(42)
	var rudolf: Dictionary = source_unit(g,133)
	check(not rudolf.is_empty(), "Rudolf source deployment present")
	g.commit_strike({"attacker":"alm","defender":rudolf.id,"hp_after":0})
	check(g.battle_outcome == "victory" and not g.story_events.is_empty(), "Rudolf death queues surrender and source story")
	g.save_game()
	var loaded = load_state()
	check(loaded.complete_battle(), "unsettled boss victory suspend settles")
	var exp_after: int = int(loaded.roster.alm.exp)
	loaded.save_game()
	loaded = load_state()
	check(not loaded.complete_battle() and int(loaded.roster.alm.exp) == exp_after, "boss settlement remains idempotent after reload")
	check(loaded.retry_battle() and int(source_unit(loaded,133).hp) > 0 and loaded.battle_outcome.is_empty(), "boss retry restores surrender casualties and source flags")
	scenarios.append("Rudolf immediate surrender before settlement -> load -> settle once -> retry")

func _test_real_loot_resume() -> void:
	var g = fresh()
	g.find_unit("alm").item_id = 10
	g.roster.alm.item_id = 10
	g.convoy.alm.resize(40);g.convoy.alm.fill(2)
	var victim: Dictionary = g.living("enemy")[0]
	victim.item_id = 20
	g.commit_strike({"attacker":"alm","defender":victim.id,"hp_after":0})
	g.find_unit("alm").acted = true
	g.save_game()
	await new_scene()
	await continue_title()
	check(scene.view == "loot" and scene.menu_actions == ["discard_new","discard_old"], "title continue resumes full convoy decision instead of enabling battle")
	scene.menu_selected = 1
	scene._accept()
	check(scene.view == "loot_confirm", "discard-old option requires explicit in-game confirmation")
	# Simulate application exit while the destructive decision remains pending.
	await new_scene()
	await continue_title()
	check(scene.view == "loot" and int(scene.game.find_unit("alm").item_id) == 10 and scene.game.convoy.alm.size() == 40, "closing at confirmation neither deletes nor duplicates an item")
	scene.menu_selected = 1;scene._accept()
	scene.menu_selected = 1;scene._accept()
	await process_frame
	check(scene.view == "battle" and scene.game.flags.pending_loot.is_empty() and not scene.busy, "confirmed loaded loot returns to usable battle view")
	check(int(scene.game.find_unit("alm").item_id) == 20 and scene.game.convoy.alm.size() == 40, "explicit discard-old equips new item without exceeding full convoy")
	await new_scene()
	await continue_title()
	check(scene.view == "battle" and int(scene.game.find_unit("alm").item_id) == 20, "second title continue cannot repeat disposed loot decision")
	scenarios.append("actual title continue: full convoy loot -> cancel by closing -> confirm -> next load")

func _test_enemy_resume() -> void:
	var g = fresh()
	g.phase = "enemy";g.turn = 3
	for u in g.units: u.acted = true
	var e: Dictionary = g.living("enemy")[-1]
	e.acted = false;e.move = 0;e.position = [14,14]
	g.save_game()
	await new_scene()
	await continue_title()
	for i in range(10): await process_frame
	check(scene.game.phase == "player" and scene.game.turn == 4 and not scene.busy and not scene.batch_running, "mid-enemy-phase continue executes remaining slot then exactly one phase boundary")
	check(scene.game.living("enemy").all(func(u): return bool(u.acted)), "already acted enemies are not repeated and remaining enemy completes")
	check(scene.game.living("player").all(func(u): return not bool(u.acted)), "next player turn restores party actions")
	scenarios.append("actual title continue during enemy phase with completed and outstanding slots")

func _test_story_resume() -> void:
	var g = fresh(42)
	var rudolf: Dictionary = source_unit(g,133)
	g.commit_strike({"attacker":"alm","defender":rudolf.id,"hp_after":0})
	g.save_game()
	await new_scene()
	scene.instant_mode = false
	await continue_title()
	check(scene.view == "battle_story" and scene.game.battle_settled, "actual boss continue settles victory then pauses on Chinese story")
	var exp_after: int = int(scene.game.roster.alm.exp)
	await new_scene()
	scene.instant_mode = false
	await continue_title()
	check(scene.view == "battle_story" and int(scene.game.roster.alm.exp) == exp_after, "closing mid-story replays source story without duplicate reward")
	var count := 0
	while scene.view == "battle_story" and count < 100:
		scene.dialogue_reveal = 10000
		scene._accept()
		await process_frame
		count += 1
	check(count < 100 and scene.view == "victory" and not scene.busy, "continued boss story returns to actionable result")
	check(scene.game.story_events.is_empty(), "consumed boss dialogue queue stays empty in subsequent checkpoint")
	scenarios.append("actual title continue after Rudolf victory; close within source dialogue; resume without repeat reward")

func _test_hub_resume() -> void:
	await new_scene()
	scene.game.new_game()
	scene.game.recruit("lukas")
	scene.game.enter_hub(44,Vector2i(6,6))
	scene.hub_controller._setup(false)
	scene.hub_controller._start_script(16)
	check(scene.view == "hub_dialogue" and scene.game.hub_used.has("event_vm"), "chapter source VM saves a dialogue checkpoint")
	await new_scene()
	await continue_title()
	check(scene.view == "hub_dialogue" and scene.game.hub_id == 44, "title continue restores script dialogue in exact hub")
	var count := 0
	while scene.view in ["hub_dialogue","hub_choice"] and count < 100:
		scene.hub_controller.reveal = 10000
		if scene.view == "hub_choice": scene.hub_controller.choice_index = 1
		scene._accept()
		count += 1
	check(count < 100 and scene.view == "chapter" and scene.game.chapter == 2, "resumed source VM completes chapter transition once")
	check(scene.game.parties.alm.has("lukas") and scene.game.route == "celica", "resumed chapter retains first route roster")
	scenarios.append("actual title continue within chapter-event VM dialogue, then chapter-two route transition")

func _test_batched_final_kill() -> void:
	await new_scene()
	var g = scene.game
	g.new_game()
	g.chapter = 5
	g.world_node = 78
	g.parties = {"alm":["alm"],"celica":["celica"]}
	g.roster.celica = g._initial_character("celica")
	g.apply_hub_flag(76)
	g.apply_hub_flag(82)
	g.battle_return = {"mode":"hub","hub_id":40,"position":[7,3],"world_node":78}
	g.start_battle(62,[86],true)
	g.story_events.clear()
	var alm: Dictionary = g.find_unit("alm")
	var duma: Dictionary = source_unit(g,167)
	var boss_id := str(duma.id)
	g.units = g.units.filter(func(u): return u.side == "player" or str(u.id) == boss_id)
	alm.level = 20;alm.exp = 0;alm.item_id = 17;alm.skill = 40;alm.strength = 40
	duma.hp = 1;duma.defence = 0;duma.speed = 0;duma.luck = 0
	alm.position = [int(duma.position[0])-1,int(duma.position[1])]
	g.find_unit("celica").acted = true
	scene.view = "battle";scene.ui_mode = "inspect";scene.busy = false;scene.batch_running = false
	await scene._auto_player(false)
	check(g.flags.get("campaign_complete",false) and g.battle_settled, "real automated final hit commits Duma death and settlement")
	check(scene.view == "ending" and g.mode == "ending", "automated final hit preserves ending through nested result dispatch")
	check(not scene.busy and not scene.batch_running, "automated ending releases batch and interaction state")
	await new_scene()
	await continue_title()
	check(scene.view == "ending", "title continue after automated final hit restores ending")
	scenarios.append("level20 Alm automated final Falchion hit -> nested result controller -> ending persistence")

func _test_reward_resume() -> void:
	await new_scene()
	var g = scene.game
	g.new_game();g.recruit("lukas");g.world_node = 1;g.start_battle(1)
	g.story_events.clear()
	var alm: Dictionary = g.find_unit("alm")
	var enemy: Dictionary = g.living("enemy")[0]
	alm.exp = 99;alm.skill = 40;alm.strength = 40
	enemy.hp = 1;enemy.defence = 0;enemy.luck = 0;enemy.speed = 0
	enemy.position = [int(alm.position[0])+1,int(alm.position[1])]
	scene.view = "battle";scene.busy = false;scene.batch_running = true
	await scene._play_combat("alm",str(enemy.id))
	check(scene.view == "reward" and bool(scene.reward.get("leveled",false)), "actual combat pauses on level-up result")
	var after: Dictionary = g.find_unit("alm").duplicate(true)
	await new_scene()
	await continue_title()
	var loaded: Dictionary = scene.game.find_unit("alm")
	check(scene.view == "battle" and bool(loaded.acted), "closing level-up reward preserves consumed action and resumes battle")
	for stat in ["level","exp","hp","max_hp","strength","skill","speed","luck","defence","magic_level","magic_flags"]:
		check(int(loaded.get(stat,0)) == int(after.get(stat,0)), "level-up checkpoint preserves " + stat)
	check(scene.game.flags.pending_loot.is_empty(), "level-up reload cannot replay resolved loot")
	scenarios.append("actual combat -> level-up reward pause -> title continue; progression/action persist exactly once")
