extends RefCounted
## Adapted loot policy, separate from original FE2 monster-rare tables.
const Supply = preload("res://core/equipment_supply.gd")

static func config() -> Dictionary:
	return Supply.data().random_loot

static func tier(enemy: Dictionary) -> int:
	var level := int(enemy.get("level", 1))
	var result := 0
	var levels: Array = config().tier_level_minimums
	for i in range(levels.size()):
		if level >= int(levels[i]): result = i
	var advanced := false
	for cid in config().advanced_classes:
		if int(cid) == int(enemy.get("class_id", 0)): advanced = true
	var advanced_boss := bool(enemy.get("objective_boss", false)) and level >= int(config().boss_advanced_min_level)
	if (level >= 3 and advanced) or advanced_boss: result = maxi(result, 2)
	return result

static func role(enemy: Dictionary) -> String:
	var source := int(enemy.get("source_enemy_character_id", enemy.get("character_id", enemy.get("name_id", 0))))
	for monster_id in config().monster_source_ids:
		if int(monster_id) == source: return "monster"
	var cid := int(enemy.get("class_id", 0))
	if cid in [12, 13, 20]: return "bow"
	if cid in [15, 16, 17, 18, 19]: return "focus"
	if cid in [8, 9, 10, 11, 14, 21]: return "sword"
	return "lance"

static func pool(enemy: Dictionary) -> Array:
	return config().pools[role(enemy)][tier(enemy)]

static func chance(enemy: Dictionary) -> int:
	if bool(enemy.get("no_drop", false)): return 0
	return 100 if int(enemy.get("item_id", 0)) > 0 else int(config().chance_percent)

static func ordinary_drop(enemy: Dictionary, chance_roll: int, item_roll: int) -> int:
	if bool(enemy.get("no_drop", false)) or int(enemy.get("item_id", 0)) > 0: return 0
	if chance_roll >= int(config().chance_percent): return 0
	var entries := pool(enemy)
	var total := 0
	for entry in entries: total += int(entry.weight)
	var selection := posmod(item_roll, total)
	for entry in entries:
		selection -= int(entry.weight)
		if selection < 0: return int(entry.item_id)
	return 0
