extends SceneTree
## Round-three inventory/summon boundaries. Saves stay inside reports/.
const State = preload("res://core/game_state.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const Summons = preload("res://core/summon_rules.gd")
const Scenario = preload("res://core/scenario_rules.gd")
const SAVE := "res://reports/test-round3-inventory-save.json"
class Board:
	extends RefCounted
	var units: Array = []
var checks := 0
var failures: Array[String] = []
var samples: Array = []
func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label); push_error(label)
func fresh(stage := 4, chapter := 1):
	var game = State.new()
	game.save_path = SAVE
	game.new_game(); game.recruit("lukas")
	game.chapter = chapter; game.world_node = stage; game.previous_world_node = 3
	game.start_battle(stage, [], true); game.story_events.clear()
	return game
func count_item(game, item: int) -> int:
	var count := 0
	for route in ["alm", "celica"]:
		for value in game.convoy[route]:
			if int(value) == item: count += 1
	for unit in game.units:
		if int(unit.get("item_id", 0)) == item: count += 1
	for record in game.flags.get("pending_loot", []):
		if int(record.item_id) == item: count += 1
	return count
func drop(game, enemy: Dictionary, killer: Dictionary, item: int) -> Dictionary:
	enemy.hp = 0; enemy.item_id = item
	return Inventory.on_death(game, enemy, killer)
func run() -> void:
	_test_slot_order_and_restore()
	_test_native_summon_reuse()
	_test_pending_full_storage_roundtrip()
	_test_automatic_overflow_roundtrip()
	_test_neutral_and_recruited()
	_test_cleanup_and_expel()
	_test_rare_rng_gates()
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var report := {"checks": checks, "failures": failures, "samples": samples,
		"reproduced_before_fix": {"failed_checks": 5, "native_map4_live_enemies_after_commander_removed": 6, "reported_free_before": 14, "source_free_expected": 13, "log": "/private/tmp/fe2-round3-inventory-before.log"},
		"source": ["bank003.asm:L0392BF-L0392E2", "bank003.asm:L03941B-L039444", "bank003.asm:L039496-L039544", "bank003.asm:L03956A-L0395E9", "bank006.asm:L069D28-L069DD1", "bank006.asm:L06AA62", "bank006.asm:L06B0E8-L06B13C", "bank008.asm:L08A3EE"],
		"scope": "New native-State probes: FIFO loot across full convoy suspend/resume, automatic death/neutral overflow conservation, neutral-to-formal recruitment, Cantor vanish versus combat drops, original enemy deployment slot reservation after casualties/reorder, ineligible rare drops do not advance RNG.",
		"limits": "Deterministic boundary probes and source inspection, not a full natural campaign playthrough or GUI/animation inspection."}
	var file := FileAccess.open("res://reports/round3-inventory-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n"); file.close()
	print(JSON.stringify(report)); quit(0 if failures.is_empty() else 1)
func _test_slot_order_and_restore() -> void:
	var board := Board.new()
	check(Summons.available_slots(board, "enemy") == 19, "empty enemy bank still reserves native slot0")
	for slot in range(1, 20): board.units.append({"side": "enemy", "enemy_slot": slot, "hp": 20})
	check(Summons.available_slots(board, "enemy") == 0, "19 live enemies after commander casualty fill all summon slots")
	board.units.append({"side": "enemy", "enemy_slot": 0, "hp": 0})
	check(Summons.available_slots(board, "enemy") == 0, "dead commander reservation follows slot0 rather than array ordering")
	board.units[4].hp = 0
	check(Summons.available_slots(board, "enemy") == 1, "only the dead noncommander slot becomes reusable")
	board.units.reverse()
	check(Summons.available_slots(board, "enemy") == 1, "reordering deployment records does not change enemy capacity")
	var game = fresh()
	var enemies: Array = game.units.filter(func(unit): return unit.side == "enemy")
	var removed: Dictionary = enemies[0]
	game.flags.inventory_defeated_enemy_records = {Inventory._enemy_key(removed): true}
	Inventory.restore_enemy_survivors(game)
	var live_slots := game.living("enemy").size()
	check(Summons.available_slots(game, "enemy") == 19 - live_slots, "native survivor restoration preserves the empty commander slot reservation")
	samples.append({"probe": "commander_removed", "live_enemies": live_slots, "available": Summons.available_slots(game, "enemy"), "expected": 19 - live_slots})
func _test_native_summon_reuse() -> void:
	var game = fresh()
	game.units = game.units.filter(func(unit): return unit.side == "player")
	var source := {"id": "cantor", "side": "enemy", "class_id": 19, "magic_flags": 32, "position": [4, 4]}
	for slot in range(1, 20):
		var monster := Summons.spawn_unit(source, 11)
		monster.id = "slot_probe_" + str(slot); monster.position = [4, 4] if slot == 1 else [8, 8]; monster.enemy_slot = slot
		game.units.append(monster)
	check(game._summon(source, 11, 2).is_empty(), "native allocator cannot create a20th noncommander enemy")
	game.find_unit("slot_probe_19").hp = 0
	var spawned: Array = game._summon(source, 11, 2)
	check(spawned.size() == 1 and int(game.find_unit(str(spawned[0])).enemy_slot) == 19, "native summon fills exactly the one reusable dead slot")
	check(Summons.available_slots(game, "enemy") == 0, "dead corpse plus live replacement count as one occupied summon slot")
	game.find_unit(str(spawned[0])).hp = 0
	spawned = game._summon(source, 11, 3)
	check(spawned.size() == 1 and int(game.find_unit(str(spawned[0])).enemy_slot) == 19 and Summons.available_slots(game, "enemy") == 0, "repeated corpse-slot reuse remains capped without stale-record drift")
func _test_pending_full_storage_roundtrip() -> void:
	var game = fresh()
	var alm: Dictionary = game.find_unit("alm"); alm.item_id = 7; game.roster.alm.item_id = 7
	var enemies: Array = game.living("enemy")
	check(drop(game, enemies[0], alm, 53).destination == "pending", "first carried loot waits behind equipped item")
	check(drop(game, enemies[1], alm, 55).destination == "pending", "second drop queues independently")
	for i in range(40): game.convoy.alm.append(2)
	var queue_before := JSON.stringify(game.flags.pending_loot)
	check(not Inventory.resolve_loot(game, "store") and not Inventory.resolve_loot(game, "new"), "manual choices cannot overflow a full convoy")
	check(JSON.stringify(game.flags.pending_loot) == queue_before and alm.item_id == 7, "blocked choices leave FIFO and equipment unchanged")
	check(game.save_game(), "full convoy with two pending drops suspends")
	var loaded = State.new(); loaded.save_path = SAVE
	check(loaded.load_game(), "full convoy pending queue resumes through native loader")
	check(loaded.flags.pending_loot.size() == 2 and count_item(loaded, 53) == 1 and count_item(loaded, 55) == 1, "resume conserves each incoming item once")
	check(Inventory.resolve_loot(loaded, "discard_new"), "explicit first-item discard resolves at full storage")
	check(loaded.flags.pending_loot.size() == 1 and loaded.flags.pending_loot[0].item_id == 55 and loaded.find_unit("alm").item_id == 7, "discarding first loot keeps the second queue entry and old equipment")
	loaded.convoy.alm.pop_back()
	check(Inventory.resolve_loot(loaded, "new"), "one freed convoy slot permits incoming replacement")
	check(loaded.find_unit("alm").item_id == 55 and count_item(loaded, 7) == 1 and loaded.convoy.alm.size() == 40 and loaded.flags.pending_loot.is_empty(), "replacement conserves old item and consumes only one free slot")
	check(loaded.save_game() and game.load_game() and game.flags.pending_loot.is_empty() and count_item(game, 55) == 1, "resolved queue cannot replay after another suspend/resume")
	check(Inventory.on_death(game, game.find_unit(str(enemies[1].id)), game.find_unit("alm")).is_empty(), "resumed corpse remains processed after queue resolution")
	samples.append({"probe": "full_convoy_fifo_suspend", "queue_before": 2, "queue_after": game.flags.pending_loot.size(), "convoy_after": game.convoy.alm.size()})
func _test_automatic_overflow_roundtrip() -> void:
	var game = fresh()
	for i in range(40): game.convoy.alm.append(2)
	var lukas: Dictionary = game.find_unit("lukas"); lukas.item_id = 53; lukas.hp = 0
	check(Inventory.on_death(game, lukas).kind == "death_storage", "formal death automatically recovers held item even at40")
	check(game.convoy.alm.size() == 41 and lukas.item_id == 0 and game.roster.lukas.item_id == 0, "automatic overflow avoids native SRAM overwrite and item duplication")
	check(game.save_game(), "automatic overflow death suspends")
	var loaded = State.new(); loaded.save_path = SAVE
	check(loaded.load_game() and loaded.convoy.alm.size() == 41 and count_item(loaded, 53) == 1, "native loader preserves intentional automatic overflow")
	var alm: Dictionary = loaded.find_unit("alm"); alm.item_id = 0
	var enemy: Dictionary = loaded.living("enemy")[0]
	check(drop(loaded, enemy, alm, 55).destination == "unit" and count_item(loaded, 55) == 1, "empty killer can directly equip loot while convoy exceeds40")
	check(loaded.convoy.alm.size() == 41 and loaded.flags.pending_loot.is_empty(), "direct equip does not consume an extra storage slot")
func _test_neutral_and_recruited() -> void:
	var game = fresh(34, 4)
	# Reload this stage with the actual Tatiana rescued flag used by Scenario.
	Scenario._flag(game, 31)
	game.start_battle(34, [34, 35], true)
	var allies: Array = game.units.filter(func(unit): return bool(unit.get("neutral", false)))
	check(not allies.is_empty(), "Tatiana source flag converts the real Zeke army into temporary allies")
	if allies.is_empty(): return
	var ally: Dictionary = allies[0]
	var enemy: Dictionary = game.living("enemy")[0]
	check(drop(game, enemy, ally, 53).destination == "convoy" and ally.item_id != 53, "neutral army killer sends held enemy loot directly to owning convoy")
	# Keep Zeke alive so this probe cannot bypass his permanent-death gate.
	var casualty: Dictionary = allies.filter(func(unit): return not bool(unit.get("zeke_npc", false)))[0]
	casualty.item_id = 55
	var attacker: Dictionary = game.living("enemy")[0]
	game.commit_strike({"attacker": attacker.id, "defender": casualty.id, "hp_after": 0})
	check(casualty.hp == 0 and not game.convoy.alm.has(55), "real combat death of neutral ally does not recover its own held equipment")
	check(not game.roster.has(str(casualty.id)), "neutral battle record never becomes a persistent party item owner")
	game.recruit("zeke")
	check(not bool(game.roster.zeke.get("neutral", false)) and not bool(game.roster.zeke.get("no_experience", false)), "subsequent real Zeke recruitment enables formal inventory status")
	var zeke: Dictionary = game.roster.zeke.duplicate(true); zeke.position = [2, 3]; zeke.side = "player"; zeke.hp = zeke.max_hp; zeke.item_id = 53
	var alm: Dictionary = game.find_unit("alm"); alm.position = [2, 2]; alm.item_id = 0; alm.acted = false
	game.units.append(zeke)
	check(Inventory.exchange(game, "alm", "zeke") and alm.item_id == 53 and game.roster.zeke.item_id == 0, "formal recruited Zeke can trade and sync inventory independently of his NPC record")
func _test_cleanup_and_expel() -> void:
	var game = fresh()
	var caster := {"id": "cantor_probe", "side": "enemy", "class_id": 19, "character_id": 191, "magic_flags": 32, "hp": 0}
	var monster: Dictionary = game.living("enemy")[1]; monster.class_id = 11; monster.item_id = 53
	check(Summons.cleanup(game, caster).has(str(monster.id)), "Cantor death vanishes matching original monster records")
	check(monster.no_drop and monster.no_experience and monster.vanished, "vanished records suppress both held loot and experience")
	check(Inventory.on_death(game, monster, game.find_unit("alm")).is_empty() and not game.convoy.alm.has(53), "Cantor cleanup never turns its erased monster into held-item loot")
	var expelled: Dictionary = game.living("enemy")[0]; expelled.hp = 0; expelled.item_id = 55
	check(Inventory.on_death(game, expelled).is_empty(), "map removal without combat actor does not award guaranteed held loot")
	check(Inventory.rare_drop(monster, 1, 0, 0, 0) == 0, "vanished monster cannot produce rare loot")
	game = fresh()
	var alm: Dictionary = game.find_unit("alm"); alm.class_id = 18; alm.magic_flags = 64; alm.strength = 16; alm.max_hp = 52; alm.hp = 52
	var enemies: Array = game.living("enemy")
	for unit in enemies: unit.class_id = 11; unit.item_id = 53
	var exp_before: int = alm.exp
	var result: Dictionary = game.use_support("alm", 46)
	check(not result.is_empty() and result.action == "expel", "native Expel support action executes against the original enemy bank")
	check(int(enemies[0].hp) > 0 and result.changed.size() == enemies.size() - 1, "native Expel preserves commander0 and removes all other eligible classes with strength16")
	check(alm.exp == exp_before and game.flags.pending_loot.is_empty() and game.convoy.alm.is_empty(), "Expel removes held-item monsters without experience or loot")
func _test_rare_rng_gates() -> void:
	for spec in [[5, 0, 181], [1, 2, 181], [1, 0, 180]]:
		var game = fresh()
		game.flags.scenario_source_chapter_counter = int(spec[0]); game.flags.inventory_rare_drop_count = int(spec[1])
		var monster: Dictionary = game.living("enemy")[0]; monster.character_id = int(spec[2]); monster.hp = 0; monster.item_id = 0
		var before: int = game.rng_state
		check(Inventory.on_death(game, monster, game.find_unit("alm")).is_empty(), "ineligible rare probe has no drop: %s" % str(spec))
		check(game.rng_state == before and game.flags.inventory_rare_drop_count == int(spec[1]), "ineligible rare probe does not advance RNG/count: %s" % str(spec))
