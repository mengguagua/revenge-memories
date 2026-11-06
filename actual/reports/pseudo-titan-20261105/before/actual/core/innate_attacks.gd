extends RefCounted
const Mechanical=preload("res://core/mechanical_puppets.gd")
## Body attacks are combat profiles, never equipable inventory entries.
const STONE_CLAW = 1001
const STONE_SPIT = 1002
const BONE_BITE = 1003
const ERODING_BREATH = 1004
const WING_BEAK = 1005
const SUN_CROWN = 1006
const PROFILES = {
	1001: {"id":1001,"name_zh":"裂石爪","kind":"innate_attack","might":0,"weight":0,"hit":90,"critical":0,"hp_cost":0,"magic":false,"range":1},
	1002: {"id":1002,"name_zh":"碎岩喷吐","kind":"innate_attack","might":3,"weight":2,"hit":70,"critical":0,"hp_cost":0,"magic":false,"range":2},
	1003: {"id":1003,"name_zh":"骸颚撕咬","kind":"innate_attack","might":3,"weight":3,"hit":85,"critical":0,"hp_cost":0,"magic":false,"range":1},
	1004: {"id":1004,"name_zh":"蚀息","kind":"innate_attack","might":3,"weight":3,"hit":75,"critical":0,"hp_cost":1,"magic":true,"range":2},
	1005: {"id":1005,"name_zh":"翼喙重击","kind":"innate_attack","might":3,"weight":3,"hit":80,"critical":0,"hp_cost":0,"magic":false,"range":1},
	1006: {"id":1006,"name_zh":"日冠聚光","kind":"innate_attack","might":3,"weight":3,"hit":80,"critical":0,"hp_cost":1,"magic":true,"range":2},
	1007: {"id":1007,"name_zh":"机械掌击","kind":"innate_attack","might":0,"weight":0,"hit":85,"critical":0,"hp_cost":0,"magic":false,"range":1},
	1008: {"id":1008,"name_zh":"水炮","kind":"innate_attack","might":3,"weight":5,"hit":75,"critical":0,"hp_cost":0,"magic":false,"range":3},
}

static func profile(id: int) -> Dictionary:
	return PROFILES.get(id,{}).duplicate(true)

static func is_body(unit: Dictionary) -> bool:
	if str(unit.get("side",unit.get("team","")))!="enemy":return false
	if Mechanical.is_puppet(unit):return true
	return int(unit.get("class_id",0)) in [3,5] or (int(unit.get("class_id",0))==21 and bool(unit.get("campaign_final_boss",false)))

static func selected(unit: Dictionary, distance: int = 0, counter: bool = false) -> int:
	if not is_body(unit):return 0
	if Mechanical.is_puppet(unit):
		if distance==0 and int(unit.get("innate_attack_index",0)) in [Mechanical.PALM,Mechanical.WATER,47]:
			var chosen=int(unit.innate_attack_index)
			return 47 if chosen==Mechanical.WATER and (Mechanical.cannon_hp(unit)<=0 or unit.get("mechanical_retreating",false)) else chosen
		if distance>1:return Mechanical.WATER if Mechanical.cannon_hp(unit)>0 and not unit.get("mechanical_retreating",false) else 47
		return Mechanical.PALM
	if distance==0 and PROFILES.has(int(unit.get("innate_attack_index",0))):return int(unit.innate_attack_index)
	match int(unit.class_id):
		3:return STONE_SPIT if unit.get("body_attack","")=="stone_spit" or (counter and distance>1 and str(unit.get("behavior","")) in ["guard","guard_exit"]) else STONE_CLAW
		5:return BONE_BITE if distance==1 else ERODING_BREATH
		21:return WING_BEAK if counter and distance==1 else SUN_CROWN
	return 0

static func armour(unit: Dictionary) -> int:
	return 5 if is_body(unit) and unit.get("body_armour","")=="thick_stone" else 0

static func description(unit: Dictionary) -> String:
	if Mechanical.is_puppet(unit):return "机械傀儡，经验×1.5。掌击1格；背炮1–3格，命中速度－1，不叠加。同阵营仅剩机械傀儡时移动＋3并撤离。"
	match int(unit.get("class_id",0)):
		3:return "身体固有攻击：碎岩喷吐，物理1–2格。" if selected(unit)==STONE_SPIT else "身体固有攻击：裂石爪，物理1格。"+("厚石甲增加5物防。" if armour(unit)>0 else "")
		5:return "贴身骸颚撕咬；距离2使用蚀息，按魔防结算并消耗1生命。每次交锋只使用其中一种。"
		21:return "主动日冠聚光，魔法1–2格、消耗1生命；贴身反击改用翼喙重击。"
	return ""
