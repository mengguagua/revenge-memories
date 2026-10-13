extends SceneTree
const Rules = preload("res://core/combat_rules.gd")
const Items = preload("res://core/item_rules.gd")
const Progression = preload("res://core/unit_progression.gd")
var checks := 0
var failures := 0
func _initialize() -> void:
	var data := Items.data()
	_check(data.items.size() == 59, "All original item IDs0..58 extracted")
	_check(data.spell_learning.size() == 18, "18 personal training lists extracted")
	_check(data.promotions.size() == 13, "13 fixed promotion paths extracted")
	_check(data.items[25].might == 24 and data.items[25].hp_cost == 10, "Ragnarok original might24 HP10")
	_check(data.items[27].critical == 20 and data.items[27].weight == 1, "Excalibur crit and weight")
	var mage := {"class_id": 15, "character_id": 6, "hp": 20, "max_hp": 24, "strength": 10, "skill": 7, "speed": 8, "luck": 6, "defence": 4, "magic_flags": 3, "side": "player"}
	var target := {"class_id": 6, "hp": 30, "max_hp": 30, "strength": 10, "skill": 4, "speed": 5, "luck": 3, "defence": 20, "resistance": 2, "side": "enemy"}
	_check(Items.spells(mage) == [23, 24], "Mage flags map to Fire/Thunder")
	_check(Rules.weapon_index(mage) == 23, "Mage default counter Fire")
	var fire := Rules.attack_stats(mage, target, 40)
	_check(fire.damage == 11, "Fire strength10+3-resistance2, ignores DEF20")
	_check(fire.hit == 72, "Magic hit80 minus raw SPD5 LCK3, ignores forest40")
	_check(fire.attack_speed == 5, "Fire weight3 reduces speed8")
	_check(Rules.attack_range(mage) == Vector2i(1,2), "Fire adjacent/two squares")
	var thunder := mage.duplicate(true); thunder.weapon_index = 24
	_check(Rules.attack_range(thunder) == Vector2i(1,3), "Thunder range3")
	_check(Rules.magic_cost(thunder) == 2, "Thunder HP2")
	thunder.hp = 2
	_check(not Rules.can_attack(thunder,2), "Cannot pay all current HP")
	thunder.hp = 3
	_check(Rules.can_attack(thunder,2), "One HP must remain after spell")
	thunder.item_id = 57
	_check(Rules.attack_range(thunder) == Vector2i(1,5), "Mage ring range5")
	var shield := target.duplicate(true); shield.item_id = 52
	_check(Rules.attack_stats(mage,shield,0).hit == 10, "Dread/anti-magic shield fixes magic hit10")
	shield.item_id = 53
	_check(Rules.attack_stats(mage,shield,0).damage == 1, "Dragon shield adds13 RES")
	var fighter := {"class_id": 21, "character_id": 1, "hp": 28,"max_hp": 28,"strength": 20,"skill": 7,"speed": 6,"luck": 7,"defence": 6,"side":"player"}
	var base := target.duplicate(true); base.defence = 2
	shield = base.duplicate(true); shield.item_id = 49
	_check(Rules.attack_stats(fighter,shield,0).damage == 13, "Steel shield DEF+5")
	fighter.item_id = 15
	_check(Rules.attack_stats(fighter,base,0).damage == 13, "Levin sword fixed15 versus RES2")
	fighter.strength = 40
	_check(Rules.attack_stats(fighter,base,0).damage == 13, "Levin ignores wielder STR")
	fighter.item_id = 10; fighter.class_id = 1
	_check(Rules.attack_stats(fighter,base,90).hit == 100, "Luna always100 hit")
	fighter.item_id = 55
	_check(Rules.attack_stats(fighter,base,0).critical == 11, "Angel Ring treats luck as40")
	fighter.item_id = 56
	_check(Rules.attack_speed(fighter) == 40, "Speed ring treats SPD40")
	fighter.move = 5
	_check(Items.movement(fighter) == 10, "Speed ring MOV+5")
	fighter.item_id = 58; fighter.hp = 14
	_check(Rules.attack_stats(fighter,base,0).critical == 100, "Prayer ring at halfHP guaranteed crit")
	fighter.hp = 15
	_check(Rules.attack_stats(fighter,base,0).critical < 100, "Prayer inactive abovehalfHP")
	fighter.item_id = 6; fighter.strength = 10
	var cavalry := base.duplicate(true); cavalry.class_id = 1
	_check(Rules.attack_stats(fighter,cavalry,0).damage == 17, "Ridersbane triple weapon might3 against cavalry")
	cavalry.class_id = 6
	_check(Rules.attack_stats(fighter,cavalry,0).damage == 11, "Ridersbane no infantry effectiveness")
	var falcon := fighter.duplicate(true); falcon.class_id = 5; falcon.item_id = 3
	var terror := base.duplicate(true); terror.class_id = 11
	_check(Rules.attack_stats(falcon,terror,0).damage == 28, "Falcon against terror tripledSTR10, no weapon add")
	var light := mage.duplicate(true); light.weapon_index = 26
	_check(Rules.attack_stats(light,terror,0).damage == 32, "Seraphim triples spell might8 versus terror RES2")
	var siphon := mage.duplicate(true); siphon.class_id = 18; siphon.magic_flags = 5; siphon.hp = 5; siphon.weapon_index = 42
	var wounded := base.duplicate(true); wounded.hp = 3
	var drained := Rules.strike_effect(siphon,wounded,true,true)
	_check(drained.damage == 3 and drained.heal == 3, "Nosferatu heals actual HP removed, no overkill")
	_check(drained.hp_cost == 0, "Original Nosferatu no HPcost")
	var miss := Rules.strike_effect(mage,base,false,false)
	_check(miss.hp_cost == 1 and miss.damage == 0, "Missed Fire still costs HP")
	fighter.item_id = 14; fighter.class_id = 21; fighter.luck = 0; fighter.defence = 6
	var recoil := Rules.strike_effect(fighter,base,true,false,0,1)
	_check(recoil.self_damage == 17 and recoil.damage == 0, "DarkSword recoil harms wielder only")
	_check(Rules.strike_effect(fighter,base,true,false,99,1).damage > 0, "DarkSword no recoil abovethreshold")
	fighter.class_id = 10
	_check(Rules.strike_effect(fighter,base,true,false,0,1).self_damage == 0, "Dread Fighter immune to DarkSword recoil")
	var duma := base.duplicate(true); duma.character_id = 167; duma.hp = 40; duma.max_hp = 182
	fighter.class_id = 21; fighter.item_id = 18
	_check(Rules.attack_blocked(fighter,duma), "Final Duma rejects ordinary blade")
	fighter.item_id = 17
	_check(not Rules.attack_blocked(fighter,duma), "Falchion can finish Duma")
	_check(not Rules.attack_blocked(siphon,duma), "Original Nosferatu loophole retained")
	var rudolf := base.duplicate(true); rudolf.character_id = 133
	_check(Rules.attack_blocked(rudolf,fighter), "Rudolf does not attack Alm")
	var cleric := mage.duplicate(true); cleric.class_id = 18; cleric.character_id = 14; cleric.magic_flags = 13
	_check(Items.spells(cleric) == [40,42,43], "Cleric Recover Nosferatu Warp bits")
	_check(Items.can_use(cleric,43), "Learned Warp usable with sufficientHP")
	_check(not Items.can_use(cleric,44), "Unlearned spell unavailable")
	var friend := {"hp": 2,"max_hp": 24,"side":"player"}
	var heal := Items.support_effect(cleric,friend,40,0)
	_check(heal.heal == 10 and heal.repeat_heal == 10 and heal.repeat_cost == 1, "Recover may heal twice via SPD+LCK")
	_check(Items.support_effect(cleric,friend,41,0).repeat_heal == 0, "Physic does not repeat")
	_check(Items.support_range(43) == Vector2i(1,1), "Warp selects adjacent ally")
	_check(Items.support_range(41).y == 255, "Physic selection spans battlefield")
	_check(Items.support_effect(cleric,friend,44).all_allies, "Fortify is team heal")
	_check(Items.support_effect(cleric,{"hp":0,"max_hp":24},40).valid == false, "Healing cannot revive")
	_check(Items.summon_spec(cleric,0).class_id == 10 and Items.summon_spec(cleric,0).count == 2, "Silque invokes minimum2 dreadfighters")
	cleric.character_id = 15
	_check(Items.summon_spec(cleric,9).class_id == 6 and Items.summon_spec(cleric,9).count == 6, "Genny's strength-bounded soldiers")
	cleric.character_id = 30
	_check(Items.summon_spec(cleric,0).class_id == 3, "Tatiana invokes Pegasus")
	_check(Items.support_effect(cleric,terror,46,9).expel, "Expel roll9 below strength10 removes terror")
	_check(not Items.support_effect(cleric,terror,46,10).expel, "Expel equality fails")
	_check(not Items.support_effect(cleric,base,46,0).expel, "Expel cannot remove human soldier")
	var injured := fighter.duplicate(true); injured.hp = 10; injured.max_hp = 28; injured.item_id = 5
	_check(Items.phase_effect(injured,0).heal == 5, "Holy weapon regeneration5")
	injured.item_id = 0
	_check(Items.phase_effect(injured,0,16).hp_after == 5, "Poison terrain damage5")
	injured.hp = 3
	_check(Items.phase_effect(injured,0,16).hp_after == 1, "Poison never kills")
	_check(Items.phase_effect(injured,218,16).hp_after == 8, "Recovery tile bypasses poison")
	injured.class_id = 3
	_check(Items.phase_effect(injured,0,16).damage == 0, "Flying avoids swampdamage")
	injured.class_id = 6
	_check(Items.phase_effect(injured,0,0,true).heal == 5, "Adjacent saint heals5")
	var villager := {"character_id":6,"class_id":14,"level":3,"exp":91,"hp":20,"max_hp":20,"strength":7,"skill":1,"speed":2,"luck":10,"defence":3,"resistance":8,"magic_flags":0,"side":"player"}
	_check(Progression.promotion_options(villager).size() == 5, "Level3 villager five paths")
	var promoted := Progression.promote(villager,15)
	_check(promoted.valid and promoted.unit.level == 1 and promoted.unit.exp == 0, "Promotion resets level1EXP0")
	_check(promoted.unit.max_hp == 28 and promoted.unit.strength == 8 and promoted.unit.luck == 10, "Promotion raises to minima without reducing highstats")
	_check(promoted.unit.magic_flags == 1 and promoted.unit.magic_level == 0, "Villager->Mage startsFire/trainingzero")
	_check(villager.class_id == 14 and villager.exp == 91, "Pure promotion leaves original untouched")
	villager.level = 2
	_check(not Progression.promote(villager,15).valid, "Early promotion rejected")
	var soldier := villager.duplicate(true); soldier.class_id = 6; soldier.level = 7
	_check(Progression.promotion_options(soldier)[0].class_id == 2, "SoldierLv7 toKnight")
	var high := soldier.duplicate(true)
	for key in ["strength","skill","speed","luck","defence"]: high[key] = 40
	high.max_hp = 50
	_check(Progression.promote(high,2).growths.hp == 1, "Promotion no otherstatgain grantsHP1")
	high.max_hp = 52
	_check(Progression.promote(high,2).growths.hp == 0, "Promotion consolationHP caps52")
	var swordsman := soldier.duplicate(true); swordsman.class_id = 9; swordsman.level = 10; swordsman.resistance = 2
	var dread := Progression.promote(swordsman,10)
	_check(dread.unit.resistance == 17, "Dread adds15 resistance")
	dread.unit.level = 10
	_check(Progression.promote(dread.unit,14).unit.resistance == 2, "Dread->Villager removesclass resistancebonus")
	var training: Dictionary = promoted.unit.duplicate(true); training.level = 4; training.magic_level = 2
	var learned := Progression.learn_spells(training)
	_check(learned.learned == [24] and learned.unit.magic_flags == 3, "Kliff learnsThunder at magic traininglevel4")
	training.class_id = 19; training.magic_level = 5; training.level = 2
	_check(Progression.learn_spells(training).learned == [27], "PromotedMage training continues toExcalibur7")
	var hero := fighter.duplicate(true); hero.character_id = 1; hero.class_id = 21; hero.level = 12
	_check(Progression.promote(hero,23,true).unit.class_id == 21, "Alm hero remains runtimeclass21 withflag")
	_check(Progression.promote(hero,23,true).unit.promoted, "Alm storypromotion flagsbow access")
	_check(Items.can_use(Progression.promote(hero,23,true).unit,20), "PromotedAlm can useSteelBow")

	var jedah := {"character_id":134,"side":"enemy","hp":52}
	_check(Rules.boss_guard(jedah,1) and Rules.boss_guard(jedah,3), "Jedah protected onturn1/3")
	_check(not Rules.boss_guard(jedah,4) and not Rules.boss_guard(jedah,8), "Jedah vulnerable each fourthturn")
	duma.hp = 182
	_check(Rules.boss_weapon(duma,177) == 19 and Rules.boss_weapon(duma,178) == 38, "Duma originalframe boundary177/178")
	duma.hp = 51
	_check(Rules.boss_weapon(duma,0) == 39, "Duma finalform EyeBall")
	duma.hp = 52; duma.defence = 0; duma.speed = 0
	var powerhouse := hero.duplicate(true); powerhouse.strength = 40; powerhouse.item_id = 9; powerhouse.class_id = 1; powerhouse.speed = 40
	var safe := Rules.duma_safe_rolls(powerhouse,duma,[true,true],[true,true])
	_check(safe.hits == [false,false], "Duma suppresses lethal fullform strike sequence")
	powerhouse.strength = 34; powerhouse.item_id = 17; powerhouse.class_id = 21
	safe = Rules.duma_safe_rolls(powerhouse,duma,[true,true],[true,true])
	_check(safe.hits == [true,false] and not safe.criticals[0], "Duma keeps nonlethal first normalhit")
	var forbidden := mage.duplicate(true); forbidden.item_id = 12
	_check(Rules.weapon_index(forbidden) == 23, "Carried incompatible sword does not equip Mage")
	_check(Items.can_use({"class_id":6,"hp":20},4) == false, "Original Soldier cannot equipJavelin")
	var dead_unit := villager.duplicate(true); dead_unit.hp = 0; dead_unit.level = 3
	_check(not Progression.promote(dead_unit,15).valid, "Shrine cannot promote fallenunit")

	var bonded := {"character_id":1,"side":"player","pos":[3,3],"hp":20}
	var beloved := {"character_id":2,"side":"player","pos":[4,3],"hp":20}
	_check(Rules.combat_support(bonded,base,[beloved]), "Alm adjacent to Celica receives combat support")
	_check(not Rules.combat_support(beloved,base,[bonded]), "Original love support applies to Alm only")
	var sisters := [{"character_id":31,"pos":[2,3],"hp":20},{"character_id":32,"pos":[3,2],"hp":20},{"character_id":33,"pos":[4,3],"hp":20}]
	_check(Rules.combat_support(sisters[0],{"pos":[3,3]},sisters,1), "Three sisters around target enable triangle")
	_check(not Rules.combat_support(sisters[0],{"pos":[3,3]},sisters,2), "Triangle cannot trigger at distance2")
	sisters[1].hp = 0
	_check(not Rules.combat_support(sisters[0],{"pos":[3,3]},sisters,1), "Fallen sister does not enable triangle")
	var report := FileAccess.open("res://reports/full-rules-verification.json", FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"source-derived magic/items/promotion/training/terrain/support pure rules"},"  "))
	print("FE2 full rules: %d checks, %d failures" % [checks,failures])
	quit(1 if failures else 0)
func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)
