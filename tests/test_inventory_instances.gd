extends SceneTree
const State = preload("res://core/game_state.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const Worlds = preload("res://core/world_armies.gd")
var checks := 0
var errors: Array[String] = []
func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: errors.append(label); push_error(label)

func soldier(game, identity: String, record: int, hp: int = 20) -> Dictionary:
	var unit: Dictionary = game.catalog.enemy_groups["4"].enemies[record].duplicate(true)
	unit.id = identity + "_" + str(record)
	unit.army_instance = identity
	unit.group_id = 4
	unit.record_index = record
	unit.side = "enemy"
	unit.hp = hp
	return unit

func setup(game) -> void:
	game.new_game()
	game.chapter = 1
	game.world_node = 4
	game.stage_id = 4
	game.previous_world_node = 3
	game.mode = "battle"
	game.phase = "enemy"
	game.turn = 40
	game.world_armies = {"4": [4, 4], "5": [4]}
	game.flags.world_army_instances = {"4": ["army_101", "army_102"], "5": ["army_103"]}
	game.flags.world_mobile_armies = [
		{"node":4,"group_id":4,"previous_node":3,"instance_id":"army_101"},
		{"node":4,"group_id":4,"previous_node":5,"instance_id":"army_102"},
		{"node":5,"group_id":4,"previous_node":6,"instance_id":"army_103"}]
	game.flags.battle_army_instances = ["army_101", "army_102"]
	game.encounter_groups = [4,4]
	game.flags.inventory_enemy_initiated = true
	game.flags.inventory_attacking_group_id = 4
	game.flags.inventory_attacking_instance_id = "army_102"
	game.flags.inventory_attacker_previous_node = 5
	game.flags.inventory_defeated_enemy_records = {}
	game.units = [game.roster.alm.duplicate(true)]
	game.units[0].position = [2,2]
	game.units[0].side = "player"
	Worlds.ensure(game)

func run() -> void:
	var game = State.new()
	setup(game)
	game.units.append_array([soldier(game,"army_101",0,0), soldier(game,"army_102",0,20)])
	Inventory._persist_participants(game)
	check(game.flags.inventory_defeated_enemy_records.has("army_101:0"), "casualty recorded by army instance and source member")
	check(not game.flags.inventory_defeated_enemy_records.has("4:0") and not game.flags.inventory_defeated_enemy_records.has("army_102:0"), "same-template second army does not inherit first army casualty")
	game.units = [soldier(game,"army_101",0), soldier(game,"army_102",0)]
	Inventory.restore_enemy_survivors(game)
	check(game.units.size() == 1 and game.units[0].army_instance == "army_102", "re-entering battle restores the surviving duplicate independently")
	game.flags.inventory_defeated_enemy_records["army_102:1"] = true
	game.flags.inventory_defeated_enemy_records["army_103:0"] = true
	game.flags.battle_army_instances = ["army_101"]
	Inventory.on_victory(game)
	check(not game.flags.inventory_defeated_enemy_records.has("army_101:0"), "victory releases defeated instance casualty mask")
	check(game.flags.inventory_defeated_enemy_records.has("army_102:1") and game.flags.inventory_defeated_enemy_records.has("army_103:0"), "victory leaves all nonparticipant instance masks intact")

	setup(game)
	game.units.append_array([soldier(game,"army_101",0,20), soldier(game,"army_102",0,0)])
	var result: Dictionary = Inventory.forced_retreat(game)
	check(result.triggered and result.instance_id == "army_102", "timeout selects exact attacking instance")
	check(game.world_armies["4"] == [4] and game.flags.world_army_instances["4"] == ["army_101"], "same-template defending army remains in place")
	check(game.world_armies["5"] == [4,4] and game.flags.world_army_instances["5"] == ["army_103","army_102"], "retreat joins same-template army without merging or dropping either instance")
	check(game.flags.world_mobile_armies[0].node == 4 and game.flags.world_mobile_armies[1].node == 5 and game.flags.world_mobile_armies[2].node == 5, "only selected mobile instance moves")
	check(game.flags.inventory_defeated_enemy_records.has("army_102:0") and not game.flags.inventory_defeated_enemy_records.has("army_101:0"), "retreat carries its own losses without harming the retained army")
	check(game.mode == "world" and game.battle_outcome == "enemy_retreat" and game.units.is_empty(), "instance retreat completes normal battle exit")

	setup(game)
	game.world_armies["5"] = [4,4]
	game.flags.world_army_instances["5"] = ["army_103","army_104"]
	Worlds.ensure(game)
	var before_world: Dictionary = game.world_armies.duplicate(true)
	var before_ids: Dictionary = game.flags.world_army_instances.duplicate(true)
	result = Inventory.forced_retreat(game)
	check(not result.triggered and result.reason == "attacking_army_retreat_blocked", "full destination refuses a third army")
	check(game.mode == "battle" and game.world_armies == before_world and game.flags.world_army_instances == before_ids, "blocked retreat preserves battlefield and all army identities")

	setup(game)
	game.flags.inventory_attacking_instance_id = "army_999"
	result = Inventory.forced_retreat(game)
	check(not result.triggered and result.reason == "attacking_army_missing" and game.world_armies["4"] == [4,4], "missing specific attacker never falls back to deleting another copy")
	var report := {"checks":checks,"errors":errors,"scope":"Real native State and WorldArmies; two identical templates at a battlefield plus a third at the retreat origin; independently persisted casualties, exact victory cleanup, exact timeout retreat and capacity/error rollback. Legacy inventory suite remains separate."}
	var file := FileAccess.open("res://reports/inventory-instance-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")+"\n"); file.close()
	print(JSON.stringify(report)); quit(0 if errors.is_empty() else 1)
