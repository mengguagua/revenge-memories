class_name FeUnitProgression
extends RefCounted
const Items = preload("res://core/item_rules.gd")

static func promotion_options(unit: Dictionary) -> Array[Dictionary]:
	# bank008 L08A804. Villager's five possible choices are shown by the
	# native UI; the original shrine cycles a random choice on each visit.
	var cid := int(unit.get("class_id", 0))
	var level := int(unit.get("level", 1))
	var result: Array[Dictionary] = []
	if cid == 14 and level >= 3:
		for target in Items.data().villager_options:
			result.append({"class_id": int(target), "level_required": 3})
	else:
		for entry in Items.data().promotions:
			if int(entry.from_class) == cid and level >= int(entry.level):
				result.append({"class_id": int(entry.to_class), "level_required": int(entry.level)})
	return result

static func promote(unit: Dictionary, target_class: int, story_promotion: bool = false) -> Dictionary:
	# L08A96C-L08AA27: level1/EXP0; raise six stats to destination minima.
	# A promotion with no stat increase guarantees maxHP +1 (cap52).
	if int(unit.get("hp", 1)) <= 0 or bool(unit.get("dead", false)):
		return {"valid": false, "unit": unit.duplicate(true), "growths": {}}
	var allowed := false
	for option in promotion_options(unit):
		if int(option.class_id) == target_class:
			allowed = true
	var alm_story := story_promotion and int(unit.get("character_id", 0)) == 1 and target_class == 23
	if not allowed and not alm_story:
		return {"valid": false, "unit": unit.duplicate(true), "growths": {}}
	var result := unit.duplicate(true)
	var old_class := int(result.get("class_id", 0))
	var bases: Dictionary = Items.data().promotion_bases.get(str(target_class), {})
	if bases.is_empty():
		return {"valid": false, "unit": result, "growths": {}}
	result.class_id = old_class if alm_story else target_class
	result.promoted = true
	result.level = 1
	result.exp = 0
	var growths: Dictionary = {}
	var changed := false
	for key in ["strength", "skill", "speed", "luck", "defence", "max_hp"]:
		var before := int(result.get(key, result.get("defense", 0) if key == "defence" else 0))
		var after := maxi(before, int(bases.get(key, 0)))
		result[key] = after
		growths["hp" if key == "max_hp" else key] = after - before
		changed = changed or after > before
	if not changed and int(result.max_hp) < 52:
		result.max_hp += 1
		growths.hp = 1
	result.move = int(Items.data().class_move[int(result.class_id) - 1])
	# Dread Fighter has an additional15 resistance, removed on returning
	# to Villager. Keep personal resistance separate from the class bonus.
	var personal_res := int(result.get("personal_resistance", int(result.get("resistance", 0)) - (15 if old_class == 10 else 0)))
	result.personal_resistance = personal_res
	result.resistance = personal_res + (15 if int(result.class_id) == 10 else 0)
	var bits := int(result.get("magic_flags", result.get("raw_magic_flags", 0)))
	if target_class == 15:
		bits = 1
		result.magic_level = 0
	elif target_class in [11, 17, 19]:
		bits |= 128
	result.magic_flags = bits
	# The original overworld rebuild fills current HP when battle begins.
	# Return a healthy camp unit; dead units cannot be selected for promotion.
	result.hp = int(result.max_hp)
	result.erase("weapon_index")
	return {"valid": true, "unit": result, "growths": growths, "class_before": old_class,
		"class_after": int(result.class_id), "story_promotion": alm_story}

static func learn_spells(unit: Dictionary, levels_gained: int = 1) -> Dictionary:
	# L0988F8 increments the personal training counter except Villager.
	# L01ADDE checks learned spell level against counter+1, not displayed
	# promoted level. Store magic_level alongside a unit in campaign saves.
	var copy := unit.duplicate(true)
	var character_id := int(copy.get("character_id", 0))
	var entries: Array = Items.data().spell_learning.get(str(character_id), [])
	var learned: Array[int] = []
	if entries.is_empty() or int(copy.get("class_id", 0)) == 14:
		return {"unit": copy, "learned": learned}
	var training := int(copy.get("magic_level", 0))
	var bits := int(copy.get("magic_flags", copy.get("raw_magic_flags", 0)))
	var table: Array = Items.data().player_spell_tables.get(str(int(copy.get("class_id", 0))), [])
	for _i in range(maxi(0, levels_gained)):
		training += 1
		for entry in entries:
			if int(entry.level) == training + 1:
				var slot := table.find(int(entry.spell_id))
				if slot >= 0 and (bits & (1 << slot)) == 0:
					bits |= 1 << slot
					learned.append(int(entry.spell_id))
	copy.magic_level = training
	copy.magic_flags = bits
	return {"unit": copy, "learned": learned}

static func spell_learning_list(unit: Dictionary) -> Array:
	return Items.data().spell_learning.get(str(int(unit.get("character_id", 0))), []).duplicate(true)
