extends SceneTree
## Source-valid late milestone states; no claim of natural late-battle wins.
const State = preload("res://core/game_state.gd")
const Rules = preload("res://core/combat_rules.gd")
const Items = preload("res://core/item_rules.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const SAVE := "res://reports/test-round5-progress-save.json"
var checks := 0
var failures: Array[String] = []
var evidence: Dictionary = {}
var scene

func _initialize() -> void:
	call_deferred("_run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func same_json(first: Variant, second: Variant) -> bool:
	# Save/load normalizes integer Variants and StringName keys to JSON types.
	return JSON.parse_string(JSON.stringify(first)) == JSON.parse_string(JSON.stringify(second))

func fresh():
	var game = State.new()
	game.save_path = SAVE
	game.new_game()
	for transition in [1,2,3,4]:
		check(game.next_chapter(transition), "Source chapter transition %d loads its milestone" % transition)
	game.world_node = 78
	game.route_positions.alm = 78
	game.previous_world_node = 42
	game.mode = "hub"
	game.hub_id = 37
	game.hub_position = Vector2i(11,23)
	return game

func duma(game) -> Dictionary:
	for unit in game.units:
		if int(unit.get("character_id",0)) == 167:
			return unit
	return {}

func _run() -> void:
	_test_final_missing_finisher()
	_test_readiness_matrix()
	scene = load("res://scenes/main.tscn").instantiate()
	scene.instant_mode = true
	scene.game.save_path = SAVE
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	_test_old_checkpoint_recovery_and_prepare()
	_test_captured_courier_storage()
	_test_captured_reserve_caster()
	scene.audio.stop_all()
	scene.queue_free()
	await process_frame
	for path in [SAVE,SAVE+".tmp",SAVE+".bak"]:
		DirAccess.remove_absolute(path)
	var file := FileAccess.open("res://reports/round5-progress-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"evidence":evidence,
		"scope":"Source chapter transitions and legitimate final milestone with only mandatory leaders; production final merge, attack guard, first10 per-route preparation matrix, complete start-transaction rollback for old unprepared final checkpoint, actual Falchion pickup/save/return and prepared source final entry.",
		"limits":"Final low form is a source-rule boundary witness, not an artificial victory. Earlier late-campaign wins and room traversal checkpoints are fixtures. No combat stats or boss immunity/retreat rules changed."},"\t")+"\n")
	print("ROUND5 PROGRESS: %d checks, %d failures" % [checks,failures.size()])
	quit(0 if failures.is_empty() else 1)

func _test_final_missing_finisher() -> void:
	var game = fresh()
	check(game.party == ["alm"] and game.parties.celica == ["celica"], "Optional healer recruitments can legitimately remain skipped")
	check(not game.final_battle_readiness().ready and game.final_battle_readiness().reason == "missing_finisher", "Preparation check identifies an actual missing finishing tool")
	game.apply_hub_flag(82)
	check(game.enter_dungeon_battle(22) and game.mode == "battle" and game.stage_id == 62, "Legacy unprepared source final checkpoint can be reconstructed")
	check(game.flags.get("final_parties_merged",false) and game.living("player").size() == 2, "Production final merge deploys both real leaders")
	check(game.select_unit("alm") and not game.reachable(game.find_unit("alm")).is_empty(), "Unprepared final battle remains controllable and movable")
	var boss := duma(game)
	check(not boss.is_empty() and int(boss.hp) >= 52, "Source Duma initial form exists")
	boss.hp = 51
	var blocked: Array = []
	for unit in game.living("player"):
		check(Rules.attack_blocked(unit,boss), "%s ordinary attack cannot finish source Duma low form" % str(unit.id))
		for id in Items.spells(unit):
			if str(Items.spell(id).get("kind","")) != "spell": continue
			var caster: Dictionary = unit.duplicate(true)
			caster.weapon_index = id
			check(Rules.attack_blocked(caster,boss), "%s learned attack %d is also blocked" % [str(unit.id),id])
		blocked.append(str(unit.id))
	check(Inventory.retreat_chance(62) == 0 and Inventory.forced_retreat_turn(62) == 255, "Source final battle keeps neither manual nor timeout retreat")
	check(game.save_game(), "Unable-to-finish final battle writes an otherwise valid checkpoint")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.retry_battle(), "Continue/retry restores the same unprepared final battle")
	check(loaded.can_return_to_final_preparation(), "Old unprepared checkpoint explicitly offers preparation recovery")
	evidence = {"kind":"P1 unprepared final battle previously overwrote the usable exploration checkpoint", "stage":62,
		"players_without_finisher":blocked,"final_low_form_hp_fixture":51,"retreat_probability":Inventory.retreat_chance(62),"timeout":Inventory.forced_retreat_turn(62),
		"source":"bank009 L098A63/L098CC8; bank013 L0DB91E final trigger and L0D8ED4 door; room40 feature0 offers source Falchion17"}

func _test_readiness_matrix() -> void:
	var game = fresh()
	game.roster.alm.item_id = 17
	check(game.final_battle_readiness().ready and game.final_battle_readiness().reason == "falchion", "Alm carrying actual Falchion is ready")
	game.roster.alm.item_id = 0
	game.convoy.alm = [17]
	check(not game.final_battle_readiness().ready and game.final_battle_readiness().reason == "stored_falchion", "Stored sword requires explicit withdrawal before battle")
	game.convoy.alm.clear()
	game.recruit("lukas")
	game.roster.lukas.item_id = 17
	check(game.final_battle_readiness().ready, "Actually deployed companion may carry sword for legal battle exchange with Alm")
	game.roster.lukas.dead = true
	game.roster.lukas.hp = 0
	check(not game.final_battle_readiness().ready, "Dead sword holder cannot count as an available finisher")
	game.roster.lukas.item_id = 0
	game.recruit("silque")
	check(game.final_battle_readiness().ready and game.final_battle_readiness().reason == "nosferatu" and Items.spell(42).hp_cost == 0, "Source learned Nosferatu42 is an available zero-cost final-form alternative")
	game.roster.silque.dead = true
	game.roster.silque.hp = 0
	check(not game.final_battle_readiness().ready, "Dead Nosferatu caster cannot pass preparation")
	# A source legal party has more than ten recruitable members; only living
	# front10 deploy. Exactly10 ordinary members precede reserve Tatiana.
	game = fresh()
	for id in ["lukas","gray","tobin","kliff","clair","clive","forsyth","python","luthier","tatiana"]:
		game.recruit(id)
	game.roster.tatiana.item_id = 17
	check(not game.final_battle_readiness().ready and game.final_battle_readiness().reason == "reserve_falchion", "Sword on eleventh living member cannot make the real final army ready")
	check(game.final_battle_readiness().deployed.size() == 11 and not game.final_battle_readiness().deployed.has("tatiana"), "Readiness uses source10 Alm plus actual1 Celica deployment")
	game.roster.tatiana.item_id = 0
	check(not game.final_battle_readiness().ready and game.final_battle_readiness().reason == "reserve_nosferatu", "Undeployed reserve caster gives an actionable formation hint")
	game.roster.lukas.dead = true
	game.roster.lukas.hp = 0
	check(game.final_battle_readiness().ready and game.final_battle_readiness().deployed.has("tatiana"), "Dead member does not consume a deployment slot, matching final merge")
	game.apply_hub_flag(82)
	check(game.enter_dungeon_battle(22) and not game.can_return_to_final_preparation(), "Prepared source final battle keeps original commitment and normal retry")
	var caster = game.find_unit("tatiana")
	game.commit_strike({"attacker":game.living("enemy")[0].id,"defender":caster.id,"hp_after":0})
	check(not game.can_return_to_final_preparation(), "Losing a finishing caster during combat does not retroactively enable preparation rollback")
	check(game.retry_battle() and int(game.find_unit("tatiana").hp)>0, "Normal retry remains the remedy for a caster lost during a prepared battle")

func drain() -> void:
	var pages := 0
	while scene.view in ["hub_dialogue","hub_choice","battle_story"] and pages < 200:
		pages += 1
		if scene.view == "battle_story": scene.dialogue_reveal = 10000
		else: scene.hub_controller.reveal = 10000
		scene._accept()
	check(pages < 200, "Source preparation dialogue drains without an input loop")

func _test_old_checkpoint_recovery_and_prepare() -> void:
	var game = fresh()
	game.recruit("lukas")
	game.roster.lukas.dead = true
	game.roster.lukas.hp = 0
	game.apply_hub_flag(82)
	check(game.enter_dungeon_battle(22), "Unprepared legacy final starts with already fallen Lukas excluded")
	var before: Dictionary = game.battle_start_snapshot.duplicate(true)
	game.rng_state = (game.rng_state+43)%256
	game.roster.alm.exp = 88
	game.convoy.alm.append(17)
	game.flags.test_midbattle_only = true
	game.commit_strike({"attacker":game.living("enemy")[0].id,"defender":"alm","hp_after":0})
	game.mode = "defeat"
	check(game.save_game(), "Unprepared leader-death checkpoint saves with changed battle transaction")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.can_return_to_final_preparation(), "Actual saved unprepared defeat exposes preparation recovery")
	check(loaded.return_to_final_preparation() and loaded.mode=="hub" and loaded.hub_id==37 and loaded.hub_position==Vector2i(11,25), "Recovery returns to source altar south door preparation side")
	check(same_json(loaded.roster,before.roster) and same_json(loaded.convoy,before.convoy) and loaded.rng_state==int(before.rng_state), "Complete initial roster/items/RNG rollback prevents keeping battle gains or fabricated sword")
	check(same_json(loaded.world_armies,before.world_armies) and not loaded.flags.has("test_midbattle_only"), "World armies and changed gameplay flags roll back with the same transaction")
	check(loaded.roster.lukas.dead and int(loaded.roster.lukas.hp)==0 and not loaded.roster.alm.dead, "Recovery restores current-battle leader only, never revives a prior fallen member")
	check(loaded.units.is_empty() and loaded.battle_start_snapshot.is_empty() and not loaded.flags.get("final_parties_merged",false), "Recovered exploration has no stale tactical units or reusable rollback snapshot")
	check(loaded.hub_script(0,Vector2i(11,23))==55 and loaded.hub_script(0,loaded.hub_position)==-1, "Final source trigger reopens while the recovery landing cannot immediately retrigger it")
	check(loaded.save_game(), "Recovered preparation is itself a valid persisted checkpoint")
	scene.game = loaded
	scene.hub_controller.game = loaded
	scene.hub_controller.resume()
	check(scene.view=="hub" and scene.hub_controller._ground(loaded.hub_position), "Actual hub resume shows valid source ground and walking control")
	scene._direction(Vector2i.LEFT)
	check(loaded.hub_position==Vector2i(10,25) and scene.view=="hub", "First real movement leaves the recovery landing without a final-battle loop")
	# Solved-maze room checkpoint, reached earlier through the source portals.
	# Item interaction uses production facing+confirm, not give_item directly.
	check(scene.hub_controller.enter(40,Vector2i(7,3)), "Original Falchion room opens at its legal item approach checkpoint")
	scene.hub_controller.facing = Vector2i.UP
	scene._accept()
	drain()
	check(int(loaded.roster.alm.item_id)==17 and loaded.hub_used.get("40:0",false), "Real facing+confirm picks up source Falchion17 into Alm's empty slot")
	check(loaded.final_battle_readiness().ready and loaded.save_game(), "Acquired sword makes preparation both playable and persistable")
	check(scene.hub_controller.enter(37,Vector2i(11,25)), "Player can return to altar preparation door after taking sword")
	scene._direction(Vector2i.UP)
	scene._direction(Vector2i.UP)
	scene._direction(Vector2i.UP)
	drain()
	check(scene.view=="battle" and loaded.mode=="battle" and loaded.stage_id==62, "Actual source final-floor trigger now admits prepared army")
	check(not loaded.can_return_to_final_preparation() and int(loaded.find_unit("alm").item_id)==17, "Prepared final checkpoint commits source battle with the equipped actual sword")
	var boss := duma(loaded)
	boss.hp = 51
	var blade: Dictionary = loaded.find_unit("alm").duplicate(true)
	check(not Rules.attack_blocked(blade,boss) and Rules.strike_effect(blade,boss,true,false).valid, "Source low-form Duma now accepts the genuine Falchion strike")

func bind_game(game) -> void:
	scene.game = game
	scene.hub_controller.game = game
	scene.busy = false
	scene.batch_running = false
	scene.held_direction = Vector2i.ZERO
	scene._clear_menu()
	scene.ui_mode = "inspect"

func choose_hub(value: Variant) -> void:
	check(scene.view=="hub_choice", "Expected a native preparation/courier choice")
	var desired := -1
	for index in range(scene.hub_controller.choices.size()):
		if str(scene.hub_controller.choices[index].get("value"))==str(value):
			desired = index
			break
	check(desired>=0, "Native menu exposes selected value %s" % str(value))
	if desired < 0: return
	var safety := 0
	while scene.hub_controller.choice_index != desired and safety < 100:
		scene._direction(Vector2i.DOWN)
		safety += 1
	check(safety < 100, "Keyboard choice reaches actual listed option without cycling")
	scene._accept()

func storage_index(game, army: String, item_id: int) -> int:
	for index in range(game.convoy[army].size()):
		if int(game.convoy[army][index])==item_id: return index
	return -1

func count_owned(game, item_id: int) -> int:
	var count := 0
	for army in ["alm","celica"]:
		for value in game.convoy[army]:
			if int(value)==item_id: count += 1
	for unit in game.roster.values():
		if int(unit.get("item_id",0))==item_id: count += 1
	return count

func _test_captured_courier_storage() -> void:
	var game = fresh()
	game.flags.celica_captive = true
	game.flags.scenario_celica_story_phase = 3
	bind_game(game)
	check(scene.hub_controller.enter(40,Vector2i(7,3)), "Source Falchion room is available before the captured-route inventory witness")
	scene.hub_controller.facing = Vector2i.UP
	scene._accept()
	drain()
	check(int(game.roster.alm.item_id)==17 and game.hub_used.get("40:0",false), "Unique source Falchion is genuinely collected, not assigned to a fixture")
	# Earlier solved loot fixture: destination has39 slots before real courier,
	# current route has40. The real source send must place the one sword in40.
	for index in range(40): game.convoy.alm.append(11)
	for index in range(39): game.convoy.celica.append(12)
	game.world_node = 64
	game.route_positions.alm = 64
	check(scene.hub_controller.enter(16,Vector2i(15,9)) and game.hub_script(7)==41, "Alm's source courier actor exposes real script41 at its legal room16 approach")
	scene.hub_controller.facing = Vector2i.UP
	scene._accept()
	check(scene.view=="hub_choice" and scene.hub_controller.script_id==41, "Actual facing+confirm starts the source courier, without allowing a route switch")
	choose_hub("alm")
	drain()
	check(int(game.roster.alm.item_id)==0 and game.convoy.celica.size()==40 and game.convoy.celica.has(17), "Source courier actually sends Falchion17 into the captured Celica convoy")
	check(count_owned(game,17)==1 and not game.can_switch_route(), "Sending retains the unique sword and original captured-party lock")
	# The receiving party is now fully equipped with its already owned blade;
	# both bags remainfull, so ordinary withdrawal cannot solve the situation.
	game.roster.alm.item_id = 18
	game.world_node = 78
	game.route_positions.alm = 78
	check(scene.hub_controller.enter(37,Vector2i(11,25)), "Captured courier checkpoint reaches source final preparation side")
	var readiness: Dictionary = game.final_battle_readiness()
	check(not readiness.ready and readiness.reason=="stored_falchion" and readiness.storage_route=="celica" and str(readiness.message).contains("双方整备"), "Readiness names captured Celica storage and the locally accessible joint preparation path")
	game.apply_hub_flag(82)
	check(game.enter_dungeon_battle(22) and game.save_game(), "Legacy courier-trapped final checkpoint persists with the genuine remote sword")
	var loaded = State.new()
	loaded.save_path = SAVE
	check(loaded.load_game() and loaded.return_to_final_preparation(), "Old final courier storage checkpoint recovers to preparation without inventing a sword")
	bind_game(loaded)
	scene.hub_controller.resume()
	check(count_owned(loaded,17)==1 and loaded.convoy.alm.size()==40 and loaded.convoy.celica.size()==40 and int(loaded.roster.alm.item_id)==18, "Rollback keeps both full inventories, occupied hands and the one real Falchion")
	var saved_readiness: Dictionary = loaded.final_battle_readiness()
	check(saved_readiness.reason=="stored_falchion" and saved_readiness.storage_route=="celica" and str(saved_readiness.message).contains("队伍菜单"), "Reloaded JSON item17.0 retains the correct remote-storage preparation instruction")
	scene._cancel()
	choose_hub("joint_prepare")
	choose_hub("convoy")
	choose_hub("celica")
	choose_hub(storage_index(loaded,"celica",17))
	choose_hub("alm")
	check(scene.view=="hub_choice" and scene.hub_controller.choices.any(func(option):return str(option.get("value"))=="swap"), "Occupied Alm receives an explicit item-swap decision")
	choose_hub("cancel")
	check(count_owned(loaded,17)==1 and int(loaded.roster.alm.item_id)==18 and storage_index(loaded,"celica",17)>=0, "Cancelling a full-inventory exchange leaves every owned item in place")
	scene._cancel()
	choose_hub("joint_prepare")
	choose_hub("convoy")
	choose_hub("celica")
	choose_hub(storage_index(loaded,"celica",17))
	choose_hub("alm")
	choose_hub("swap")
	drain()
	check(int(loaded.roster.alm.item_id)==17 and storage_index(loaded,"celica",18)>=0 and storage_index(loaded,"celica",17)<0, "Real explicit exchange moves the remote sword to Alm and his old blade into exactly its former storage slot")
	check(count_owned(loaded,17)==1 and count_owned(loaded,18)==1 and loaded.convoy.alm.size()==40 and loaded.convoy.celica.size()==40, "Both full bags and both individual item counts stay conserved")
	check(loaded.flags.get("celica_captive",false) and loaded.route=="alm" and not loaded.can_switch_route() and loaded.final_battle_readiness().ready, "Joint inventory preparation makes battle ready without unfreezing Celica or moving either world route")
	check(loaded.save_game() and loaded.load_game() and int(loaded.roster.alm.item_id)==17 and count_owned(loaded,17)==1, "Actual preparation autosave/reload retains the unique exchanged sword")
	scene.hub_controller.resume()
	for step in range(3): scene._direction(Vector2i.UP)
	drain()
	check(scene.view=="battle" and loaded.stage_id==62 and int(loaded.find_unit("alm").item_id)==17, "Same source final gate now starts the equipped merged battle from the formerly blocked courier checkpoint")

func _test_captured_reserve_caster() -> void:
	var game = fresh()
	game.route = "celica"
	game.party = game.parties.celica.duplicate()
	for id in ["mae","boey","saber","kamui","valbar","leo","atlas","jesse","palla","genny"]:
		game.recruit(id)
	game.route = "alm"
	game.party = game.parties.alm.duplicate()
	game.flags.celica_captive = true
	game.flags.scenario_celica_story_phase = 3
	bind_game(game)
	check(scene.hub_controller.enter(37,Vector2i(11,25)), "Captured reserve spell checkpoint opens the final preparation side")
	var readiness: Dictionary = game.final_battle_readiness()
	check(not readiness.ready and readiness.reason=="reserve_nosferatu" and readiness.reserve_route=="celica" and str(readiness.message).contains("赛莉卡队") and str(readiness.message).contains("双方整备"), "Captured eleventh Nosferatu caster receives its own actionable final-preparation direction")
	var old_alm: Array = game.party.duplicate()
	var old_positions: Dictionary = game.route_positions.duplicate(true)
	scene._cancel()
	choose_hub("joint_prepare")
	choose_hub("formation")
	choose_hub("celica")
	check(not scene.hub_controller.choices.any(func(option):return str(option.get("value"))=="celica"), "Joint formation keeps Celica leader fixed instead of offering a swap")
	choose_hub("mae")
	choose_hub("genny")
	drain()
	check(game.parties.celica[0]=="celica" and game.parties.celica[1]=="genny" and game.parties.celica[10]=="mae", "Actual two selections move the reserve source caster into the real ten-member deployment")
	check(game.party==old_alm and game.route=="alm" and game.route_positions==old_positions and game.flags.get("celica_captive",false) and not game.can_switch_route(), "Captured-route formation changes only its source ordering, preserving active party and both world positions")
	check(game.final_battle_readiness().ready and game.save_game() and game.load_game(), "Adjusted captured reserve formation is now battle ready and persists")
	scene.hub_controller.resume()
	for step in range(3): scene._direction(Vector2i.UP)
	drain()
	check(scene.view=="battle" and game.living("player").size()==11 and not game.find_unit("genny").is_empty() and game.find_unit("mae").is_empty(), "Real final merge deploys the moved caster, not the now reserved ordinary mage")
	var caster: Dictionary = game.find_unit("genny").duplicate(true)
	caster.weapon_index = 42
	var boss := duma(game)
	boss.hp = 51
	var strike: Dictionary = Rules.strike_effect(caster,boss,true,false)
	check(not Rules.attack_blocked(caster,boss) and strike.valid and int(strike.damage)>0 and int(strike.hp_cost)==0, "Genuine moved Nosferatu42 deals positive zero-cost damage through the source low-form guard without changing combat rules")
