class_name FeCombatRules
extends RefCounted
## Native original FE2 combat, with source-derived physical/magic/item rules.
## Tables/provenance: data/rules_full.json. No runtime ROM or emulator.
const Items = preload("res://core/item_rules.gd")

const WEAPON_MIGHT: Array[int] = [0, 0, 4, 8, 3, 3, 3, 15, 10, 20, 10, 4, 8, 5, 13, 15, 3, 10, 7, 12, 3, 5, 7]
const WEAPON_WEIGHT: Array[int] = [0, 0, 1, 1, 2, 0, 1, 0, 0, 2, 1, 1, 1, 0, 5, 3, 0, 0, 0, 0, 1, 0, 2]
const WEAPON_HIT: Array[int] = [90, 70, 80, 90, 70, 90, 85, 100, 100, 80, 100, 80, 90, 100, 70, 80, 100, 100, 100, 80, 70, 100, 80]
const WEAPON_CRITICAL: Array[int] = [0, 0, 0, 0, 0, 10, 0, 0, 50, 0, 0, 0, 0, 30, 0, 0, 15, 0, 20, 0, 0, 10, 0]

# L098F21, indexed by player class - 1, and L098EF9, level - 1.
const EXPERIENCE_CLASS: Array[int] = [6, 5, 6, 3, 1, 8, 1, 7, 4, 2, 5, 7, 4, 10, 5, 6, 7, 10, 2, 1, 5, 1]
const EXPERIENCE_LEVEL: Array[int] = [10, 10, 9, 8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
const GROWTH_ORDER: Array[String] = ["hp", "defence", "luck", "speed", "skill", "strength"]


static func default_weapon_index(unit: Dictionary) -> int:
	var cid := _class_id(unit)
	if _source_id(unit) == 167:
		return 39 if int(unit.get("hp", 0)) < 52 else (38 if int(unit.get("frame_counter", 0)) >= 178 else 19)
	if cid in [12, 13, 20]:
		return 1
	if _enemy(unit) and cid in [15, 16, 19]:
		for spell_id in Items.spells(unit):
			if spell_id < 35 or spell_id == 38:
				return spell_id
		return 31
	if not _enemy(unit):
		if cid in [15, 16, 19]:
			return 23
		if cid in [17, 18]:
			var bits := int(unit.get("magic_flags", unit.get("raw_magic_flags", 0)))
			if bits & 4:
				return 42
			if bits & 128:
				return 23
			return 47
	return 0


static func weapon_index(unit: Dictionary) -> int:
	if unit.has("weapon_index"):
		return clampi(int(unit.weapon_index), 0, 47)
	var id := int(unit.get("item_id", 0))
	if id > 0 and id < 23:
		if not unit.has("class_id") or Items.can_use(unit, id):
			return id
	return default_weapon_index(unit)


static func magic_cost(unit: Dictionary) -> int:
	return Items.cost(weapon_index(unit))


static func attack_speed(unit: Dictionary) -> int:
	return maxi(0, Items.effective_speed(unit) - int(Items.item(weapon_index(unit)).get("weight", 0)))


static func attack_range(unit: Dictionary) -> Vector2i:
	# L09844A: distance is Manhattan distance minus1. All ranges start at1.
	var index := weapon_index(unit)
	var maximum := 1
	if index == 47 or Items.is_support(index):
		return Vector2i.ZERO
	if _class_id(unit) == 20 or (_class_id(unit) in [11, 15, 16, 17, 18, 19] and index >= 23 and int(unit.get("item_id", 0)) == 57):
		maximum = 5
	elif index in [20, 21, 22]:
		maximum = 5
	elif index in [1, 24]:
		maximum = 3
	elif int(Items.item(index).get("target_flags", 0)) & 4:
		maximum = 2
	return Vector2i(1, maximum)


static func in_attack_range(unit: Dictionary, distance: int) -> bool:
	var reach := attack_range(unit)
	return reach.y > 0 and distance >= reach.x and distance <= reach.y


static func can_attack(unit: Dictionary, distance: int = 1) -> bool:
	return in_attack_range(unit, distance) and (magic_cost(unit) == 0 or int(unit.get("hp", 0)) > magic_cost(unit))


static func attack_stats(attacker: Dictionary, defender: Dictionary, defender_avoid: int) -> Dictionary:
	var index := weapon_index(attacker)
	var weapon := Items.item(index)
	var magical := index >= 23 or index == 15
	var speed := attack_speed(attacker)
	var defender_speed := attack_speed(defender)
	var might := int(weapon.get("might", 0))
	var strength := int(attacker.get("strength", 0))
	var effective := Items.effective_against(index, defender)
	if effective:
		might *= 3
	var falcon_bonus := not _enemy(attacker) and _class_id(attacker) == 5 and _enemy(defender) and _class_id(defender) in [3, 5, 11, 17, 18]
	if falcon_bonus:
		strength *= 3
		might = 0 # L09832F: original falcon formula uses tripled STR only.
	var power := 15 if index == 15 else strength + might
	var defence := Items.magic_defence(defender) if magical else _defence(defender) + Items.physical_defence_bonus(defender, attacker)
	var damage := clampi(power - defence + (5 if bool(attacker.get("triangle_attack", false)) else 0), 1, 60)
	var hit: int
	if index >= 23:
		hit = 10 if int(defender.get("item_id", 0)) == 52 else clampi(int(weapon.get("hit", 0)) - Items.effective_luck(defender) - Items.effective_speed(defender), 0, 100)
	else:
		hit = clampi(int(attacker.get("skill", 0)) + int(weapon.get("hit", 0)) - defender_avoid - defender_speed, 0, 100)
	if int(attacker.get("item_id", 0)) == 10:
		hit = 100
	var critical := (int(attacker.get("skill", 0)) + Items.effective_luck(attacker)) >> 1
	critical = (critical + int(weapon.get("critical", 0))) >> 1
	if _enemy(attacker) and not _class_id(attacker) in [10, 8, 9, 3]:
		critical = 0
	if not _enemy(attacker) and int(attacker.get("item_id", 0)) == 58 and int(attacker.get("hp", 0)) <= (int(attacker.get("max_hp", 0)) >> 1):
		critical = 100
	if bool(attacker.get("triangle_attack", false)):
		critical = 100
	if index == 34:
		damage = maxi(1, int(defender.get("hp", 1)) - 1)
		critical = 0
	return {"damage": damage, "hit": hit, "critical": critical, "attack_speed": speed,
		"weapon_index": index, "defender_attack_speed": defender_speed, "magic": magical,
		"hp_cost": magic_cost(attacker), "effective": effective or falcon_bonus,
		"defender_defence": defence, "can_attack": index != 47 and not Items.is_support(index)}


static func strike_sequence(attacker: Dictionary, defender: Dictionary, distance: int = 1) -> Array[String]:
	if not can_attack(attacker, distance):
		return []
	# L098D25 sets one actor's $0357 suppression flag. L098606/60A
	# skips that actor only; Jedah and final-form Duma still retaliate.
	var first := not attack_blocked(attacker, defender)
	var counter := can_attack(defender, distance) and not attack_blocked(defender, attacker)
	var result: Array[String] = []
	if first:
		result.append("attacker")
	if counter:
		result.append("defender")
	var first_speed := attack_speed(attacker)
	var second_speed := attack_speed(defender)
	if first_speed > second_speed and first:
		result.append("attacker")
	elif second_speed > first_speed and counter:
		result.append("defender")
	return result


static func attack_blocked(attacker: Dictionary, defender: Dictionary) -> bool:
	# L098D25: Rudolf does not attack Alm. Story shields are set by the
	# scenario controller from the original chapter/turn event state.
	if _source_id(attacker) == 133 and _source_id(defender) == 1:
		return true
	if bool(defender.get("story_invulnerable", false)):
		return true
	# L098A63 + L098CC8: Duma's final form blocks non-Falchion attacks;
	# the original >=40 loophole intentionally lets Nosferatu through.
	if _source_id(defender) == 167 and int(defender.get("hp", 0)) < 52:
		return weapon_index(attacker) != 17 and weapon_index(attacker) < 40
	return false


static func strike_effect(attacker: Dictionary, defender: Dictionary, hit: bool, critical: bool, roll: int = 99, distance: int = 1, defender_avoid: int = 0) -> Dictionary:
	# Resolve one strike; callers apply HP cost before damage and stop if a
	# preceding strike left the caster unable to pay. Nosferatu heals actual
	# damage dealt; Dark Sword may recoil instead of harming the opponent.
	var result := {"valid": false, "damage": 0, "self_damage": 0, "heal": 0, "hp_cost": 0,
		"hit": hit, "critical": critical, "blocked": false}
	if not can_attack(attacker, distance):
		return result
	result.blocked = attack_blocked(attacker, defender)
	if result.blocked:
		return result
	result.valid = true
	result.hp_cost = magic_cost(attacker)
	if not hit:
		return result
	var index := weapon_index(attacker)
	var stats := attack_stats(attacker, defender, defender_avoid)
	var damage := int(stats.damage)
	if critical and index != 34:
		damage = mini(120, damage * 3)
	if index == 14 and not _enemy(attacker) and _class_id(attacker) != 10 and distance == 1 and roll <= 20 - Items.effective_luck(attacker):
		# L0985B5 clears the recoil flag when the wielder's own defence
		# absorbs all recoil. That strike still damages the enemy and may crit.
		var recoil_damage := int(attacker.get("strength", 0)) + 13 - _defence(attacker)
		if recoil_damage > 0:
			result.self_damage = recoil_damage
			result.critical = false
			return result
	result.damage = mini(int(defender.get("hp", damage)), damage)
	if index == 42:
		result.heal = mini(int(result.damage), maxi(0, int(attacker.get("max_hp", 0)) - int(attacker.get("hp", 0)) + int(result.hp_cost)))
	return result


static func default_counter(unit: Dictionary, distance: int = 1) -> Dictionary:
	# L098AF5 and L069BD9: mage counters use Fire; priestess uses a sword
	# at melee and Fire at distance. Clerics use Nosferatu when learned.
	var copy := unit.duplicate(true)
	copy.erase("weapon_index")
	if not _enemy(copy) and _class_id(copy) == 11 and distance > 1:
		copy.weapon_index = 23
	return copy


static func _source_id(unit: Dictionary) -> int:
	return int(unit.get("character_id", unit.get("source_id", 1 if str(unit.get("id", "")) == "alm" else 0)))


static func _enemy(unit: Dictionary) -> bool:
	return str(unit.get("side", unit.get("team", ""))) == "enemy" or _source_id(unit) >= 128


static func victory_experience_gain(unit: Dictionary) -> int:
	# bank006 L06B74B calls the same class/level multiplier with enemy value
	# 20 for every surviving controllable player. It caps stored EXP at 99
	# and cannot trigger a level-up from this map-clear reward.
	var level := int(unit.get("level", 1))
	if level >= 20 or bool(unit.get("no_experience", false)) or int(unit.get("hp", 0)) <= 0:
		return 0
	var gain := _ceil_ratio(EXPERIENCE_CLASS[_class_id(unit) - 1] * EXPERIENCE_LEVEL[level - 1] * 20, 100)
	if bool(unit.get("easy_mode", false)):
		gain *= 2
	return mini(100, gain)


static func experience_gain(attacker: Dictionary, defender: Dictionary, hp_before: int, hp_after: int, killed: bool) -> int:
	# The original grants experience to the player unit after an entire exchange,
	# including enemy-phase counters, not after each individual strike.
	var level: int = int(attacker.get("level", 1))
	if level >= 20 or bool(attacker.get("no_experience", false)):
		return 0
	var class_id: int = _class_id(attacker)
	assert(class_id >= 1 and class_id <= EXPERIENCE_CLASS.size())
	assert(level >= 1 and level <= EXPERIENCE_LEVEL.size())
	# Enemy record field 4 comes from the final column of L0FED04 class data.
	# Its meaning is exp value; it is not an enemy unit's level-up progress.
	var enemy_value: int = int(defender.get("exp_value", defender.get("exp", 30)))
	var full_gain: int = _ceil_ratio(EXPERIENCE_CLASS[class_id - 1] * EXPERIENCE_LEVEL[level - 1] * enemy_value, 100)
	if bool(attacker.get("easy_mode", false)):
		full_gain = mini(255, full_gain * 2)
	full_gain = mini(100, full_gain)
	if killed:
		return full_gain
	var actual_damage: int = maxi(0, hp_before - hp_after)
	if actual_damage == 0:
		return 1
	var enemy_maximum: int = int(defender.get("max_hp", defender.get("hp", hp_before)))
	assert(enemy_maximum > 0)
	return _ceil_ratio(full_gain * actual_damage, enemy_maximum * 2)


static func growth_result(unit: Dictionary, rolls: Array) -> Dictionary:
	# The six rolls are already 1..99, in the engine's reverse iteration order:
	# HP, DEF, LCK, SPD, SKL, STR. Its CMP/BCS means equality FAILS.
	assert(rolls.size() == 6, "Growth needs exactly six original-order rolls")
	var growths: Dictionary = unit.get("growths", {})
	var delta: Dictionary = {"hp": 0, "defence": 0, "luck": 0, "speed": 0, "skill": 0, "strength": 0}
	var increment: int = 2 if int(unit.get("item_id", 0)) == 55 else 1
	var successful_rolls: int = 0
	for i in range(GROWTH_ORDER.size()):
		var stat: String = GROWTH_ORDER[i]
		var roll: int = int(rolls[i])
		assert(roll >= 1 and roll <= 99)
		var rate: int = int(growths.get(stat, growths.get("defense", 0) if stat == "defence" else 0))
		if roll < rate:
			successful_rolls += 1
			var before: int = _growth_stat(unit, stat)
			var maximum: int = 52 if stat == "hp" else 40
			delta[stat] = maxi(0, mini(before + increment, maximum) - before)
	# Success at a cap still increments the original $10 success counter.
	# Thus only six FAILED rolls activate the guaranteed HP growth.
	if successful_rolls == 0:
		var before_hp: int = _growth_stat(unit, "hp")
		delta["hp"] = maxi(0, mini(before_hp + increment, 52) - before_hp)
	return delta


static func phase_recovery(unit: Dictionary, tile_id: int) -> int:
	return int(Items.phase_effect(unit, tile_id).heal)


static func _class_id(unit: Dictionary) -> int:
	if unit.has("class_id"):
		return int(unit["class_id"])
	return int({"fighter": 21, "soldier": 6, "villager": 14, "brigand": 14,
		"archer": 12, "sniper": 13, "bow_knight": 20}.get(str(unit.get("class", "fighter")), 21))


static func _defence(unit: Dictionary) -> int:
	return int(unit.get("defence", unit.get("defense", 0)))


static func _growth_stat(unit: Dictionary, stat: String) -> int:
	if stat == "hp":
		return int(unit.get("max_hp", unit.get("hp", 0)))
	if stat == "defence":
		return _defence(unit)
	return int(unit.get(stat, 0))


static func _ceil_ratio(numerator: int, denominator: int) -> int:
	return int(ceil(float(numerator) / float(denominator)))


static func boss_weapon(unit: Dictionary, frame_counter: int = 0) -> int:
	# L098CC8. Duma changes from Tentacle/Eye Beam at HP>=52 to Eye
	# Ball below52; animation-frame byte chooses his intact-form attack.
	if _source_id(unit) != 167:
		return weapon_index(unit)
	if int(unit.get("hp", 0)) < 52:
		return 39
	return 38 if (frame_counter & 255) >= 178 else 19


static func boss_guard(unit: Dictionary, battle_turn: int) -> bool:
	# L098D25: Jedah can be harmed only when turn's low two bits are0.
	# L068C81 initializes turn1; L06A3F6 adds1 after enemy phase.
	return _source_id(unit) == 134 and (battle_turn & 3) != 0


static func duma_safe_rolls(player: Dictionary, duma: Dictionary, hits: Array, criticals: Array) -> Dictionary:
	# L098D58-L098DDC suppresses selected original hit/critical flags so
	# Duma cannot die during an exchange begun with >=52HP. This is NOT
	# a minimum-52HP clamp: a legal exchange may leave him with1HP.
	var hit_values := [bool(hits[0]) if hits.size() > 0 else false, bool(hits[1]) if hits.size() > 1 else false]
	var crit_values := [bool(criticals[0]) if criticals.size() > 0 else false, bool(criticals[1]) if criticals.size() > 1 else false]
	if _source_id(duma) != 167 or int(duma.get("hp", 0)) < 52:
		return {"hits": hit_values, "criticals": crit_values}
	var base_damage := int(attack_stats(player, duma, 0).damage)
	var follow_up := attack_speed(player) > attack_speed(duma)
	for step in range(4):
		var total := (base_damage * (3 if crit_values[0] else 1)) if hit_values[0] else 0
		if follow_up and hit_values[1]:
			total += base_damage * (3 if crit_values[1] else 1)
		if total < int(duma.hp):
			break
		match step:
			0: crit_values[1] = false
			1: hit_values[1] = false
			2: crit_values[0] = false
			3: hit_values[0] = false
	return {"hits": hit_values, "criticals": crit_values}


static func combat_support(attacker: Dictionary, defender: Dictionary, allies: Array, distance: int = 1) -> bool:
	# L06AAF6: Alm beside Celica receives the same guaranteed-critical
	# +5 damage flag. L069C20: the three Pegasus sisters surround target.
	if _enemy(attacker):
		return false
	var aid := _source_id(attacker)
	var here := _position(attacker)
	if aid == 1:
		for ally in allies:
			if int(ally.get("hp", 0)) > 0 and _source_id(ally) == 2 and _distance(here, _position(ally)) == 1:
				return true
	if distance != 1 or not aid in [31, 32, 33]:
		return false
	var sisters: Array[int] = [aid]
	for ally in allies:
		var id := _source_id(ally)
		if int(ally.get("hp", 0)) > 0 and id in [31, 32, 33] and not id in sisters and _distance(_position(defender), _position(ally)) == 1:
			sisters.append(id)
	return sisters.size() == 3


static func _position(unit: Dictionary) -> Vector2i:
	var p = unit.get("pos", unit.get("position", [0, 0]))
	if p is Vector2i or p is Vector2:
		return Vector2i(p)
	return Vector2i(int(p[0]), int(p[1]))


static func _distance(a: Vector2i, b: Vector2i) -> int:
	return absi(a.x - b.x) + absi(a.y - b.y)
