extends SceneTree
## Source-valid world-army checkpoints, actual movement and save operations.
const State = preload("res://core/game_state.gd")
const Scenario = preload("res://core/scenario_rules.gd")
const WorldArmies = preload("res://core/world_armies.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const SAVE := "res://reports/test-spot-world-save.json"
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func fresh():
	var game = State.new()
	game.save_path = SAVE
	game.new_game()
	game.chapter = 3
	game.route = "celica"
	game.roster.celica = game._initial_character("celica")
	game.parties.celica = ["celica"]
	game.party = ["celica"]
	game.world_node = 18
	game.route_positions.celica = 18
	game.mode = "world"
	game.world_armies.clear()
	WorldArmies.reset_for_chapter(game)
	game.flags.inventory_enemy_record_chapter = 3
	return game

func _run() -> void:
	_test_converging_instances()
	_test_partial_casualty_generations()
	_test_world_attack_and_capacity()
	_test_source_slot_limit()
	_test_precise_cleanup_and_legacy()
	_test_instance_save_round_trip()
	_test_legacy_hub_save_migration()
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	var report := FileAccess.open("res://reports/spot-world-verification.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"failures":failures,
		"source_contract":"bank008 L089FCA ordinary13 slots; L089D38 reserved cemetery slot13; L08A095 independent per-army survival mask; L089D93 fresh dungeon slots14/15; bank007 L07A52F first attacking army",
		"scope":"same-template generations/convergence, distinct casualties, capacity, attacker origin, settlement cleanup, old-v3 world/dungeon migration, retry and isolated save/load",
		"limits":"Deterministic source-valid world checkpoints and movement hooks, not original per-frame random scheduling or an entire natural campaign."},"\t") + "\n")
	print("SPOT WORLD: %d checks, %d failures" % [checks,failures.size()])
	quit(0 if failures.is_empty() else 1)

func _test_converging_instances() -> void:
	var game = fresh()
	var first := WorldArmies.add(game,22,62,24)
	var second := WorldArmies.add(game,21,62,22,false)
	check(not first.is_empty() and not second.is_empty() and first != second,"Same-template source reinforcements have distinct army IDs")
	Scenario._advance_mobile_armies(game)
	check(not game.world_armies.has("22") and game.world_armies["21"] == [62,62],"Same-template meeting preserves both armies rather than swallowing one")
	var identities := WorldArmies.instances_at(game,21)
	check(identities == [second,first],"Meeting preserves target and arriving identities in slot order")
	check(game.flags.world_mobile_armies[0].instance_id == first and int(game.flags.world_mobile_armies[0].previous_node) == 22,"Arriving army keeps its own prior world node")
	game.world_node = 21
	game.route_positions.celica = 21
	check(game.start_battle(21),"Same-template stacked encounter starts through native GameState")
	var counts: Dictionary = {}
	for enemy in game.living("enemy"):
		var identity := str(enemy.get("army_instance",""))
		counts[identity] = int(counts.get(identity,0)) + 1
	var expected := int(game.catalog.enemy_groups["62"].enemies.size())
	check(counts.get(first,0) == expected and counts.get(second,0) == expected,"Deployment binds each template copy to its own full source roster")
	check(game.flags.battle_army_instances == [second,first],"Encounter identity input order remains stable across deployment priority reversal")

func _test_partial_casualty_generations() -> void:
	var game = fresh()
	var damaged := WorldArmies.add(game,21,62,22,false)
	game.flags.inventory_defeated_enemy_records = {damaged+":0":true}
	check(Scenario._add_army(game,22,62,24),"A later generation of a still-living template is allowed")
	var newborn := str(WorldArmies.instances_at(game,22)[0])
	check(newborn != damaged and game.flags.inventory_defeated_enemy_records.has(damaged+":0"),"New generation never restores the older army's slain soldier")
	Scenario._advance_mobile_armies(game)
	game.world_node = 21
	game.route_positions.celica = 21
	check(game.start_battle(21),"Damaged and fresh same-template armies can share an encounter")
	var count_old := 0
	var count_new := 0
	for enemy in game.living("enemy"):
		if str(enemy.get("army_instance","")) == damaged: count_old += 1
		if str(enemy.get("army_instance","")) == newborn: count_new += 1
	var expected := int(game.catalog.enemy_groups["62"].enemies.size())
	check(count_old == expected-1 and count_new == expected,"Only the previously damaged instance loses its casualty on re-entry")
	check(game.save_game(),"Stacked damaged encounter saves")
	var restored = State.new()
	restored.save_path = SAVE
	check(restored.load_game(),"Stacked damaged encounter reloads")
	check(restored.flags.battle_army_instances == game.flags.battle_army_instances,"Suspend preserves both encounter identities")
	check(restored.living("enemy").size() == count_old+count_new,"Suspend preserves independent casualty-filtered enemy count")

func _test_world_attack_and_capacity() -> void:
	var game = fresh()
	# Two source paths can approach the same player node. The original
	# dispatcher returns immediately once one of them initiates battle.
	game.world_node = 21
	var first := WorldArmies.add(game,22,62,24)
	var second := WorldArmies.add(game,23,61,24)
	Scenario._advance_mobile_armies(game)
	check(str(game.flags.get("inventory_attacking_instance_id","")) == first,"The first moving attacker is retained as the battle initiator")
	check(int(game.flags.get("inventory_attacker_previous_node",0)) == 22,"Enemy initiative records the attacking instance's original location")
	check(int(WorldArmies.locate(game,second).get("node",0)) == 23,"Second army cannot overwrite the initiator within the same movement action")
	var at21 := str(WorldArmies.add(game,21,65,29,false))
	check(not at21.is_empty(),"Second defender fits the two-army source encounter capacity")
	check(not WorldArmies.move(game,second,21),"Third army cannot overfill the battlefield")
	check(int(WorldArmies.locate(game,second).get("node",0)) == 23 and game.world_armies["21"].size() == 2,"Rejected capacity move changes neither source nor target army")

func _test_source_slot_limit() -> void:
	var game = fresh()
	game._setup_chapter_armies()
	WorldArmies.reset_for_chapter(game)
	check(WorldArmies._ordinary_count(game) == 13,"Chapter3 has thirteen ordinary source slots")
	check(not str(game.flags.get("world_random_army_instance","")).is_empty(),"Cemetery occupies a separate reserved source slot")
	check(WorldArmies.add(game,24,62,61).is_empty(),"Reinforcement cannot allocate beyond thirteen ordinary armies")
	var deleted := str(WorldArmies.instances_at(game,17)[0])
	WorldArmies.remove(game,deleted)
	var created := WorldArmies.add(game,24,62,61)
	check(not created.is_empty() and WorldArmies._ordinary_count(game) == 13,"Freeing one ordinary slot permits exactly one new reinforcement")
	check(WorldArmies.add(game,26,63,63).is_empty(),"A full ordinary table remains full with its reserved cemetery army")

func _test_precise_cleanup_and_legacy() -> void:
	var game = fresh()
	var fought := WorldArmies.add(game,22,62,24)
	var unrelated := WorldArmies.add(game,23,62,24)
	game.flags.battle_army_instances = [fought]
	game.battle_return = {"mode":"world","world_node":22}
	game.flags.inventory_defeated_enemy_records = {fought+":0":true,unrelated+":0":true}
	Inventory.on_victory(game)
	WorldArmies.remove_battle(game)
	check(WorldArmies.locate(game,fought).is_empty() and not WorldArmies.locate(game,unrelated).is_empty(),"Victory removes the fought instance and retains remote same-template army")
	check(not game.flags.inventory_defeated_enemy_records.has(fought+":0") and game.flags.inventory_defeated_enemy_records.has(unrelated+":0"),"Victory releases only the fought instance's casualty mask")
	check(game.flags.world_mobile_armies.size() == 1 and game.flags.world_mobile_armies[0].instance_id == unrelated,"Victory removes only the fought mobile record")
	game = fresh()
	game.world_armies = {"22":[62],"24":[62]}
	game.stage_id = 22
	game.flags.erase("world_army_instances")
	game.flags.inventory_defeated_enemy_records = {"62:0":true}
	game.flags.world_mobile_armies = [{"node":24,"group_id":62,"previous_node":61}]
	WorldArmies.ensure(game)
	var old := str(WorldArmies.instances_at(game,22)[0])
	var other := str(WorldArmies.instances_at(game,24)[0])
	check(game.flags.inventory_defeated_enemy_records.has(old+":0") and not game.flags.inventory_defeated_enemy_records.has(other+":0"),"Legacy group casualties attach to the previous battlefield, never both copies")
	check(game.flags.world_mobile_armies[0].instance_id == other,"Legacy mobile record receives its matching node instance")
	var ids: Dictionary = game.flags.world_army_instances.duplicate(true)
	WorldArmies.ensure(game)
	check(game.flags.world_army_instances == ids,"Repeated ensure preserves allocated IDs")

func _test_instance_save_round_trip() -> void:
	var game = fresh()
	var first := WorldArmies.add(game,22,62,24,false)
	var second := WorldArmies.add(game,22,62,24)
	game.flags.inventory_defeated_enemy_records = {first+":0":true}
	check(game.save_game(),"Same-template overworld stack saves without schema migration")
	var restored = State.new()
	restored.save_path = SAVE
	check(restored.load_game(),"Same-template overworld stack reloads as v3")
	check(WorldArmies.instances_at(restored,22) == [first,second],"World suspend preserves ordered independent army identities")
	check(restored.flags.world_mobile_armies[0].instance_id == second,"World suspend keeps the moving copy distinct from stationary one")
	var created := WorldArmies.add(restored,24,62,61)
	check(not created in [first,second] and not created.is_empty(),"Generation after load cannot reuse a live army identity")

func _test_legacy_hub_save_migration() -> void:
	# Source dungeon trigger6/map56 uses group15, also used by the chapter2
	# overworld. A legacy hub suspend must never damage that remote army.
	for missing_groups in [false,true]:
		var game = State.new()
		game.save_path = SAVE
		game.new_game()
		game.chapter = 2
		game._setup_chapter_armies()
		game.world_node = 56
		check(game.enter_hub(56,Vector2i(8,12)) and game.enter_dungeon_battle(6),"Source dungeon checkpoint starts for legacy migration")
		check(game.save_game(),"Dungeon checkpoint writes isolated migration input")
		var state: Dictionary = State.read_json(SAVE)
		for checkpoint in [state,state.battle_start_snapshot]:
			for key in ["world_army_instances","world_random_army_instance","battle_army_instances","dungeon_army_instances"]:
				checkpoint.flags.erase(key)
			checkpoint.flags.inventory_defeated_enemy_records = {"15:0":true}
			for unit in checkpoint.units: unit.erase("army_instance")
			if missing_groups: checkpoint.encounter_groups = []
		var file := FileAccess.open(SAVE,FileAccess.WRITE)
		file.store_string(JSON.stringify(state)); file.close()
		var restored = State.new()
		restored.save_path = SAVE
		check(restored.load_game(),"Legacy dungeon suspend loads with source-derived encounter groups")
		var world_id := str(WorldArmies.instances_at(restored,15)[0])
		var hub_id := str(restored.flags.battle_army_instances[0])
		check(restored.flags.inventory_defeated_enemy_records.has(hub_id+":0") and not restored.flags.inventory_defeated_enemy_records.has(world_id+":0"),"Legacy dungeon loss belongs to its battle instance, never the remote same-template army")
		check(restored.units.filter(func(unit):return str(unit.get("side","")) == "enemy" and int(unit.get("group_id",-1)) == 15).all(func(unit):return str(unit.get("army_instance","")) == hub_id),"Legacy dungeon soldiers bind to the migrated dungeon identity")
		check(restored.retry_battle(),"Legacy dungeon retry snapshot restores")
		world_id = str(WorldArmies.instances_at(restored,15)[0])
		hub_id = str(restored.flags.battle_army_instances[0])
		check(restored.flags.inventory_defeated_enemy_records.has(hub_id+":0") and not restored.flags.inventory_defeated_enemy_records.has(world_id+":0"),"Legacy retry migrates its own dungeon mask without damaging the overworld")
		check(restored.save_game(),"Migrated dungeon retry writes current instance metadata")
		var resumed = State.new()
		resumed.save_path = SAVE
		check(resumed.load_game() and resumed.flags.battle_army_instances[0] == hub_id and resumed.flags.inventory_defeated_enemy_records.has(hub_id+":0"),"Current dungeon suspend retains its identity and casualty mask across load")
		restored = resumed
		var unrelated_id := str(WorldArmies.instances_at(restored,14)[0])
		restored.flags.inventory_defeated_enemy_records[unrelated_id+":0"] = true
		check(restored.enter_dungeon_battle(6),"Migrated dungeon can be entered again")
		check(restored.flags.battle_army_instances[0] != hub_id and not restored.flags.inventory_defeated_enemy_records.has(hub_id+":0"),"New source dungeon encounter replaces its old slot identity and casualty mask")
		check(restored.flags.inventory_defeated_enemy_records.has(unrelated_id+":0"),"New dungeon allocation preserves all independent world-army casualty masks")
		var expected := int(restored.catalog.enemy_groups["15"].enemies.size())
		var dungeon_count := restored.living("enemy").filter(func(unit):return int(unit.get("group_id",-1)) == 15).size()
		check(dungeon_count == expected,"New dungeon encounter resets its source slots to full rosters")
		restored.world_node = 15
		check(restored.start_battle(15),"Remote source army enters native overworld battle")
		check(restored.living("enemy").size() == expected,"Same-template remote army retains its full roster after dungeon migration")
