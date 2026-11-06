extends RefCounted
## Campaign clear experience can cross a level threshold, using normal growth rules.
const Rules=preload("res://core/combat_rules.gd")
const Progression=preload("res://core/unit_progression.gd")
static func award(game, unit: Dictionary, gain: int) -> Dictionary:
	var before=int(unit.get("exp",0));var level=int(unit.level)
	var result={"unit":str(unit.id),"gain":gain,"exp_before":before,"level_before":level,"leveled":false,"growths":{},"learned":[],"victory_training":true}
	unit.exp=before+gain
	if int(unit.exp)>=100 and int(unit.level)<20:
		unit.exp-=100;unit.level+=1;result.leveled=true
		var rolls=[]
		for i in range(6):rolls.append(game.random_bounded(99)+1)
		result.growths=Rules.growth_result(unit,rolls)
		for stat in result.growths:
			if stat=="hp":
				unit.max_hp=mini(52,int(unit.max_hp)+int(result.growths.hp));unit.hp=mini(int(unit.max_hp),int(unit.hp)+int(result.growths.hp))
			else:unit[stat]=mini(40,int(unit[stat])+int(result.growths[stat]))
		var learned=Progression.learn_spells(unit);unit.magic_flags=learned.unit.magic_flags;unit.magic_level=learned.unit.get("magic_level",0);result.learned=learned.learned
	unit.exp=mini(99,int(unit.exp))
	result.exp_after=int(unit.exp);result.level_after=int(unit.level);result.actual_gain=gain
	return result
