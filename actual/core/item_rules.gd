extends RefCounted
## Tables are extracted from the SHA-verified original FE2 source/ROM.
## All methods return new values and do not mutate the caller's unit.

static var _rules: Dictionary = {}
static var _armaments: Dictionary = {}
static var _accessories: Dictionary = {}
const Body = preload("res://core/innate_attacks.gd")
const StrongBody=preload("res://core/strong_body.gd")
const HeroProfessions = preload("res://core/hero_professions.gd")

static func armaments() -> Dictionary:
	if _armaments.is_empty():_armaments=JSON.parse_string(FileAccess.get_file_as_string("res://data/story_armaments.json"))
	return _armaments

static func is_story_armament(item_id: int) -> bool:
	return armaments().items.has(str(item_id))

static func accessories() -> Dictionary:
	if _accessories.is_empty():_accessories=JSON.parse_string(FileAccess.get_file_as_string("res://data/story_accessories.json"))
	return _accessories

static func is_story_accessory(item_id: int) -> bool:
	return accessories().items.has(str(item_id))

static func data() -> Dictionary:
	if _rules.is_empty():
		_rules = _integer_tables(JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/rules_full.json")))
		# Adapted balance stays separate from the extracted original tables.
		var promotion_tuning=_integer_tables(JSON.parse_string(FileAccess.get_file_as_string("res://data/campaign_promotions_20261030.json")))
		for cid in promotion_tuning.bases:
			_rules.promotion_bases[cid].merge(promotion_tuning.bases[cid],true)
		for change in promotion_tuning.levels:
			for entry in _rules.promotions:
				if entry.from_class==change.from_class and entry.to_class==change.to_class:entry.level=change.level
		# Confirmed display name; the original spell ID, cost and effect stay.
		_rules.items[31].name_zh = "鬼火"
		_rules.items[45].hp_cost = 10
		# Adapted display/ownership metadata overlays source IDs and numeric rules.
		var adapted:Dictionary=armaments().items.duplicate(true)
		adapted.merge(accessories().items)
		for key in adapted:
			var spec: Dictionary=adapted[key]
			for field in ["name_zh","personal_character_id","personal_name_zh","story_description"]:
				if spec.has(field):_rules.items[int(key)][field]=spec[field]
		# Campaign additions have separate provenance; never renumber source IDs.
		var additions = _integer_tables(JSON.parse_string(FileAccess.get_file_as_string("res://data/equipment_progression.json")))
		for id in additions.get("weapon_overrides",{}):
			_rules.items[int(id)].merge(additions.weapon_overrides[id],true)
		var tactics = _integer_tables(JSON.parse_string(FileAccess.get_file_as_string("res://data/knockback_equipment.json")))
		var campaign_items: Array = additions.items + tactics.items
		campaign_items.sort_custom(func(a,b):return int(a.id)<int(b.id))
		for entry in campaign_items:
			assert(int(entry.id) == _rules.items.size())
			_rules.items.append(entry)
	return _rules

static func item(item_id: int) -> Dictionary:
	if Body.PROFILES.has(item_id):return Body.profile(item_id)
	var entries: Array = data().items
	return entries[item_id].duplicate(true) if item_id >= 0 and item_id < entries.size() else {}

static func inventory_groups(stored:Array)->Array:
	# One row per item identity; actions still point at one actual copy.
	var groups=[];var indices={}
	for i in range(stored.size()):
		var id=int(stored[i])
		if indices.has(id):groups[indices[id]].count+=1
		else:indices[id]=groups.size();groups.append({"id":id,"index":i,"count":1,"name":str(item(id).get("name_zh","道具"))})
	for group in groups:group.label=group.name+("x%d"%group.count if group.count>1 else "")
	return groups

static func spell(spell_id: int) -> Dictionary:
	return item(spell_id) if spell_id >= 23 and spell_id <= 46 else {}

static func spells(unit: Dictionary) -> Array[int]:
	if Body.is_body(unit):return []
	var table_key := "enemy_spell_tables" if _enemy(unit) else "player_spell_tables"
	var table: Array = data()[table_key].get(str(int(unit.get("class_id", 0))), [])
	var bits := int(unit.get("magic_flags", unit.get("raw_magic_flags", 0)))
	var result: Array[int] = []
	for i in range(table.size()):
		if (bits & (1 << i)) != 0 and int(table[i]) != 255 and not int(table[i]) in result:
			result.append(int(table[i]))
	return result

static func can_use(unit: Dictionary, item_id: int) -> bool:
	# Body attacks and recovered nest loot never grant held weapon compatibility.
	if Body.is_body(unit):return item_id==0
	# bank015 L0FF460-L0FF507: class restrictions, personal blades, HP gate.
	if item_id < 0 or item_id >= data().items.size():
		return false
	if item_id >= 59:
		var cid := int(unit.get("class_id", 0))
		var entry := item(item_id)
		if entry.has("allowed_classes"):
			return entry.allowed_classes.has(cid)
		if entry.get("kind", "") == "accessory":return true
		match str(entry.get("family", "")):
			"sword": return cid in [8, 9, 10, 11, 21, 14]
			"lance": return cid in [1, 2, 3, 4, 5, 6, 7, 22]
			"bow": return cid in [12, 13, 20] or (cid == 21 and bool(unit.get("promoted", unit.get("alm_promoted", false))))
			"focus": return cid in [11, 15, 16, 17, 18, 19]
		return false
	if item_id >= 48:
		return true
	var cid := int(unit.get("class_id", 0))
	if cid == 6 and item_id in [4, 7]:
		return false
	if item_id in [17, 18]:
		return not _enemy(unit) and int(unit.get("character_id", 1 if str(unit.get("id", "")) == "alm" else 0)) == int(item(item_id).get("personal_character_id",1))
	if item_id >= 23 and int(unit.get("hp", 0)) <= cost_for(unit,item_id):
		return false
	if item_id <= 1:
		return true
	if item_id < 11:
		return cid in [1, 2, 3, 4, 5, 6, 7, 22]
	if item_id < 20:
		return cid in [8, 9, 10, 11, 21, 14]
	if item_id < 23:
		return cid in [12, 13, 20] or (cid == 21 and bool(unit.get("promoted", unit.get("alm_promoted", false))))
	return cid in [11, 15, 16, 17, 18, 19] and item_id in spells(unit)

static func weapon_profile(unit: Dictionary, weapon_id: int) -> Dictionary:
	var profile := item(weapon_id)
	if Body.is_body(unit):return profile
	var held_id := int(unit.get("item_id", 0))
	if held_id < 59 or not can_use(unit, held_id): return profile
	var held := item(held_id)
	if str(held.get("family", "")) == "focus":
		# A focus augments existing attack magic, never grants a spell or healing.
		if weapon_id >= 23 and weapon_id <= 46 and not is_support(weapon_id):
			profile.might = int(profile.get("might", 0)) + int(held.might)
			profile.hit = int(profile.get("hit", 0)) + int(held.hit)
			profile.weight = int(profile.get("weight", 0)) + int(held.weight)
	elif weapon_id == int(held.get("base_weapon", -1)):
		return held
	return profile

static func cost(spell_id: int) -> int:
	if Body.PROFILES.has(spell_id):return int(Body.profile(spell_id).hp_cost)
	return int(item(spell_id).get("hp_cost", 0)) if spell_id >= 23 and spell_id < 48 else 0

static func cost_for(unit: Dictionary, spell_id: int) -> int:
	var base := cost(spell_id)
	if base > 0 and spell_id >= 23 and spell_id <= 46 and not is_support(spell_id) and spell_id in spells(unit) and HeroProfessions.advanced(unit) and str(unit.id)=="eileen":
		return maxi(1,base-1)
	return base

static func is_support(spell_id: int) -> bool:
	return str(item(spell_id).get("kind", "")) == "support"

static func support_range(spell_id: int) -> Vector2i:
	return Vector2i(1, 1) if spell_id in [35, 40, 43] else Vector2i(1, 255)

static func support_effect(caster: Dictionary, target: Dictionary, spell_id: int, roll: int = 99) -> Dictionary:
	# Recover: L09896C; Physic: L098968; Fortify: L06B3A5;
	# Warp: L0697DE (caller validates destination); Invoke/Expel: bank003.
	var info := spell(spell_id)
	var result := {"valid": false, "spell_id": spell_id, "action": str(info.get("action", "none")),
		"hp_cost": 0, "heal": 0, "repeat_heal": 0, "repeat_cost": 0,
		"all_allies": false, "summon_class": 0, "summon_count": 0, "expel": false,
		"target": str(info.get("target", ""))}
	if not is_support(spell_id) or int(caster.get("hp", 0)) <= cost(spell_id):
		return result
	result.valid = true
	result.hp_cost = cost(spell_id)
	var missing := maxi(0, int(target.get("max_hp", 0)) - int(target.get("hp", 0)))
	var strength := int(caster.get("strength", 0))
	match str(info.action):
		"recover", "physic":
			if int(target.get("hp", 0)) <= 0 or bool(target.get("dead", false)) or missing == 0:
				result.valid = false
				return result
			result.heal = mini(missing, strength)
			# Recover alone can heal twice: random 0..99 < native luck+speed,
			# enough HP remains to pay a second cost, target remains injured.
			if str(info.action) == "recover" and roll < int(caster.get("luck", 0)) + int(caster.get("speed", 0)) and int(caster.get("hp", 0)) > cost(spell_id) * 2:
				result.repeat_heal = mini(maxi(0, missing - int(result.heal)), strength)
				if result.repeat_heal > 0:
					result.repeat_cost = cost(spell_id)
		"fortify":
			result.all_allies = true
			result.heal = mini(missing, strength)
		"invoke":
			var summon := summon_spec(caster, roll)
			result.summon_class = summon.class_id
			result.summon_count = summon.count
			result.valid = int(summon.class_id) > 0
		"conjure":
			var summon := enemy_summon_spec(caster, roll)
			result.summon_class = summon.class_id
			result.summon_count = summon.count
			result.hp_cost = summon.hp_cost
			result.valid = int(caster.get("hp", 0)) > int(summon.hp_cost)
		"expel":
			result.expel = _enemy(target) and int(target.get("class_id", 0)) in [3, 5, 11, 17] and (roll & 15) < strength
		"warp":
			result.valid = int(target.get("hp", 0)) > 0 and not bool(target.get("dead", false))
	return result

static func summon_spec(caster: Dictionary, bounded_roll: int) -> Dictionary:
	# L03930B: Silque14->Dread Fighter10; Genny15->Soldier6;
	# Tatiana30->Pegasus3. L039286/L0392E2 decrements with BPL.
	var cid := int(caster.get("character_id", 0))
	var classes := {14: 10, 15: 6, 30: 3}
	var roll := clampi(bounded_roll, 0, maxi(0, int(caster.get("strength", 1)) - 1))
	return {"class_id": int(classes.get(cid, 0)), "count": (roll >> 1) + 2,
		"character_id": 35, "level": 1, "no_experience": true, "temporary": true}

static func enemy_summon_spec(caster: Dictionary, bounded_roll: int) -> Dictionary:
	# L039358-L039444: Cantor inspects the first high magic bit.
	var bits := int(caster.get("magic_flags", caster.get("raw_magic_flags", 0)))
	var i := 11
	for n in range(4):
		if bits & (128 >> n):
			i = n
			break
	var classes := [5, 3, 11, 17, 0, 0, 1, 1, 1, 16, 18, 18]
	var costs := [6, 4, 1, 2, 0, 0, 1, 1, 1, 0, 0, 0]
	var roll := clampi(bounded_roll, 0, maxi(0, int(caster.get("strength", 1)) - 1))
	return {"class_id": classes[i], "count": (roll >> 1) + 1, "hp_cost": costs[i], "level": 1, "temporary": true}

static func summon_offsets() -> Array:
	return data().summon_offsets.duplicate(true)

static func effective_against(weapon_id: int, defender: Dictionary, profile: Dictionary = {}) -> bool:
	var group := int((item(weapon_id) if profile.is_empty() else profile).get("effective", 0))
	return group > 0 and int(defender.get("class_id", 0)) in data().effectiveness_classes.get(str(group), [])

static func physical_defence_bonus(unit: Dictionary, attacker: Dictionary = {}) -> int:
	var bonus=StrongBody.bonus(unit)
	if Body.is_body(unit):return Body.armour(unit)+bonus
	var id := int(unit.get("item_id", 0))
	if id == 51:
		return (13 if int(attacker.get("class_id", 0)) in [3, 5, 11, 17, 18] else 0)+bonus
	if is_story_accessory(id):return int(accessories().items[str(id)].get("physical_defence_bonus",0))+bonus
	if id>=59:return int(item(id).get("physical_defence_bonus",0))+bonus
	return int({48: 3, 49: 5, 50: 7}.get(id, 0))+bonus

static func magic_defence(unit: Dictionary) -> int:
	var bonus=int(accessories().items.get(str(int(unit.get("item_id",0))),{}).get("magic_defence_bonus",0))
	return int(unit.get("resistance", unit.get("magic_defence", 0))) + bonus + Body.Mechanical.armour_bonus(unit)

static func effective_luck(unit: Dictionary) -> int:
	return 40 if int(unit.get("item_id", 0)) == 55 else int(unit.get("luck", 0))

static func effective_speed(unit: Dictionary) -> int:
	var base=40 if int(unit.get("item_id", 0)) == 56 else int(unit.get("speed", 0))
	return maxi(0,base-(1 if unit.get("water_slow",false) else 0))

static func movement(unit: Dictionary) -> int:
	var amount=int(unit.get("move", 4)) + (5 if int(unit.get("item_id", 0)) == 56 else 0)
	return maxi(1,amount-2) if int(unit.get("map_fatigue_until_turn",0))>0 or int(unit.get("map_move_penalty_until_turn",0))>0 else amount

static func phase_effect(unit: Dictionary, tile_id: int, terrain_category: int = -1, adjacent_saint: bool = false) -> Dictionary:
	# L03910F-L0391DA: recovery tile wins before poison processing.
	var hp := int(unit.get("hp", 0))
	var max_hp := int(unit.get("max_hp", hp))
	if hp <= 0 or bool(unit.get("dead", false)):
		return {"damage": 0, "heal": 0, "hp_after": hp}
	var cid := int(unit.get("class_id", 0))
	var immune := cid in [3, 5] or (_enemy(unit) and cid in [11, 17, 18, 21])
	var damage := mini(5, maxi(0, hp - 1)) if tile_id != 218 and terrain_category == 16 and not immune else 0
	var amount := 0
	var enemy_duma := _enemy(unit) and int(unit.get("character_id", unit.get("source_id", 0))) == 167
	var held_id := int(unit.get("item_id", 0))
	# Carrying an unusable weapon through trade does not activate its passive.
	# Terrain, adjacent saints and innate class recovery remain independent.
	var item_recovery := can_use(unit, held_id) and int(item(held_id).get("effect_kind", 0)) == 10
	if tile_id == 218 or (adjacent_saint and not _enemy(unit)) or cid == 19 or item_recovery:
		amount = 5
	elif enemy_duma:
		amount = 5 if hp >= 20 else 40
	var healed := mini(amount, maxi(0, max_hp - hp + damage))
	return {"damage": damage, "heal": healed, "hp_after": hp - damage + healed}

static func _enemy(unit: Dictionary) -> bool:
	return str(unit.get("team", "")) == "enemy" or str(unit.get("side", "")) == "enemy" or int(unit.get("character_id", unit.get("source_id", 0))) >= 128

static func _integer_tables(value: Variant) -> Variant:
	# Godot JSON numbers are floats; Array.find/in are type-sensitive.
	# Every numeric field in these original byte tables is an integer.
	if value is float:
		return int(value)
	if value is Array:
		var result: Array = []
		for child in value:
			result.append(_integer_tables(child))
		return result
	if value is Dictionary:
		var result: Dictionary = {}
		for key in value:
			result[key] = _integer_tables(value[key])
		return result
	return value
