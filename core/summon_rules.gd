class_name FeSummonRules
extends RefCounted
## L039267-L03965C, L0899FA-L089A54 and constructor L08A31B.
## Position, deployment-slot allocation and runtime ID belong to the caller.
const Items = preload("res://core/item_rules.gd")
const CAPACITY := 20
const TEMPLATES := [
	[181,5,1,0,72,0], [179,3,1,0,72,0],
	[187,11,1,0,72,0], [193,17,1,0,72,0],
	[80,7,20,0,4,0], [79,4,20,0,4,0],
	[35,6,1,0,68,0], [35,10,1,0,68,0], [35,3,1,0,68,0],
	[192,16,1,0,200,1], [194,18,1,0,72,0], [194,18,5,0,8,0]
]

static func template_index(caster: Dictionary, cid: int, spec: Dictionary = {}) -> int:
	if spec.has("source_template_index"):
		return clampi(int(spec.source_template_index), 0, TEMPLATES.size()-1)
	if str(caster.get("side", "player")) == "player":
		return int({6:6,10:7,3:8}.get(cid,-1))
	if int(caster.get("class_id",0)) == 19:
		var flags := int(caster.get("magic_flags",caster.get("raw_magic_flags",0)))
		for i in range(4):
			if flags & (128 >> i): return i
		return 11
	if int(caster.get("class_id",0)) == 21 and cid == 18: return 11
	return int({5:0,3:1,11:2,17:3,16:9,18:10}.get(cid,-1))

static func spawn_unit(caster: Dictionary, cid: int, spec: Dictionary = {}, route: String = "alm") -> Dictionary:
	var index := template_index(caster,cid,spec)
	if index < 0: return {}
	var raw: Array = TEMPLATES[index]
	if int(raw[1]) != cid: return {}
	var base: Dictionary = Items.data().promotion_bases.get(str(cid),{})
	if base.is_empty(): return {}
	var unit: Dictionary = base.duplicate(true)
	var level := int(raw[2])
	var bonus := (level-1) >> 1
	for key in ["strength","skill","speed","defence"]:
		unit[key] = int(base.get(key,0)) + bonus
	# L08A356 explicitly skips index3 (Luck); promotion minima are only
	# the baseline here, not a player-growth simulation.
	unit.luck = int(base.get("luck",0))
	unit.max_hp = int(base.max_hp) if cid == 21 else mini(52,int(base.max_hp)+bonus*3)
	unit.hp = int(unit.max_hp)
	unit.exp_value = mini(255,int(base.exp_value) + int(int(base.exp_value)*(level-1)/10))
	unit.level = level
	unit.exp = 0
	unit.class_id = cid
	unit.character_id = int(raw[0])
	unit.name_id = int(raw[0])
	unit.item_id = int(raw[3])
	unit.ai_flags = int(raw[4])
	unit.raw_ai_flags = int(raw[4])
	unit.magic_flags = int(raw[5])
	unit.raw_magic_flags = int(raw[5])
	unit.resistance = int(Items.data().class_resistance[cid-1])
	unit.move = int(Items.data().class_move[cid-1])
	unit.side = str(caster.get("side","player"))
	unit.route = str(caster.get("route",route))
	unit.no_experience = (int(raw[4]) & 4) != 0
	unit.temporary = true
	unit.controllable = false
	unit.acted = false
	unit.dead = false
	unit.source_template_index = index
	unit.summoner_id = str(caster.get("id",""))
	unit.summon_capacity = CAPACITY
	return unit

static func available_slots(game, side: String) -> int:
	# L0392BF keeps dead formal-player slots occupied, but reuses dead
	# phantoms. L03941B reserves enemy slot0 and reuses other dead slots.
	# Reserve the physical enemy slot0 even when its dead commander was
	# pruned during survivor restoration. Array order is not slot identity.
	var occupied := 1 if side == "enemy" else 0
	var first_enemy := true
	for unit in game.units:
		if str(unit.get("side","")) != side: continue
		if side == "player":
			if int(unit.get("character_id",0)) != 35 or int(unit.get("hp",0)) > 0: occupied += 1
		else:
			var commander := int(unit.enemy_slot) == 0 if unit.has("enemy_slot") else first_enemy
			if not commander and int(unit.get("hp",0)) > 0: occupied += 1
			first_enemy = false
	return maxi(0,CAPACITY-occupied)

static func cleanup(game, dead: Dictionary) -> Array[String]:
	# L039496-L039544: death of one Cantor removes every matching enemy
	# class; Mogall/Duma/witch death does not remove their offspring.
	var removed: Array[String] = []
	if int(dead.get("hp",1)) > 0 or bool(dead.get("retreated",false)) or bool(dead.get("rescued",false)) or bool(dead.get("vanished",false)):
		return removed
	var side := str(dead.get("side","player"))
	var target_class := 0
	if side == "player":
		target_class = int({15:6,14:10,30:3}.get(int(dead.get("character_id",0)),0))
	elif int(dead.get("class_id",0)) == 19:
		target_class = int(Items.enemy_summon_spec(dead,0).class_id)
	if target_class == 0: return removed
	for unit in game.units:
		if str(unit.get("side","")) != side or int(unit.get("hp",0)) <= 0 or int(unit.get("class_id",0)) != target_class:
			continue
		if side == "player" and int(unit.get("character_id",0)) != 35: continue
		unit.hp = 0
		unit.acted = true
		unit.no_drop = true
		unit.no_experience = true
		unit.vanished = true
		removed.append(str(unit.get("id","")))
	return removed
