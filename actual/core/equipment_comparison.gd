extends RefCounted
## Preparation forecasts use the same item profiles and combat formulas as play.
const Items=preload("res://core/item_rules.gd")
const Rules=preload("res://core/combat_rules.gd")

static func profession_name(unit: Dictionary,classes: Dictionary) -> String:
	var hero_name := Items.HeroProfessions.name(unit)
	if not hero_name.is_empty():return hero_name
	return str(classes.get(str(int(unit.get("class_id",0))),{}).get("name_zh","未知职业"))

static func automatic(unit: Dictionary) -> Dictionary:
	var actor=unit.duplicate(true);actor.erase("weapon_index");actor.erase("triangle_attack");return actor

static func attack_name(unit: Dictionary) -> String:
	var actor=automatic(unit);var index=Rules.weapon_index(actor)
	if index==0:return "普通枪" if int(actor.class_id) in [1,2,3,4,5,6,7,22] else "普通剑"
	return str(Items.item(index).get("name_zh","无法攻击"))

static func held_name(unit: Dictionary) -> String:
	var id=int(unit.get("item_id",0))
	if id<=0:return attack_name(unit)+"（默认）"
	var item=Items.item(id);var label=str(item.get("name_zh","未知装备"))
	if item.get("kind","")=="accessory" or item.get("family","")=="focus":label+=" / "+attack_name(unit)
	return label

static func stats(unit: Dictionary) -> Dictionary:
	var actor=automatic(unit);var index=Rules.weapon_index(actor);var profile=Items.weapon_profile(actor,index)
	var target={"side":"enemy","class_id":6,"character_id":128,"hp":52,"max_hp":52,"strength":0,"skill":0,"speed":0,"luck":0,"defence":0,"resistance":0,"item_id":0}
	var forecast=Rules.attack_stats(actor,target,0);var reach=Rules.attack_range(actor)
	var power=15 if index==15 else int(actor.strength)+int(profile.get("might",0))
	if not forecast.can_attack:power=0
	return {"power":power,"hit":int(forecast.hit) if forecast.can_attack else 0,"critical":int(forecast.critical) if forecast.can_attack else 0,
		"speed":Rules.attack_speed(actor),"defence":int(actor.defence)+Items.physical_defence_bonus(actor),"resistance":Items.magic_defence(actor),
		"luck":Items.effective_luck(actor),"move":Items.movement(actor),"range":reach.y,"reach":reach,"hp_cost":Rules.magic_cost(actor)}

static func compare(unit: Dictionary,target_id: int,classes: Dictionary) -> Dictionary:
	var after=automatic(unit);after.item_id=target_id
	var before_stats=stats(unit);var after_stats=stats(after);var rows=[]
	for spec in [["攻击力","power"],["命中基础","hit"],["必杀","critical"],["攻速","speed"],["物防","defence"],["魔防","resistance"],["幸运","luck"],["移动","move"],["射程","range"]]:
		var key=str(spec[1]);var old_value=int(before_stats[key]);var new_value=int(after_stats[key]);var delta=new_value-old_value
		var suffix="%" if key in ["hit","critical"] else ""
		var old_text=str(old_value)+suffix;var new_text=str(new_value)+suffix
		if key=="range":
			old_text=range_name(before_stats.reach);new_text=range_name(after_stats.reach)
		rows.append({"key":key,"label":spec[0],"before":old_value,"after":new_value,"delta":delta,
			"before_text":old_text,"after_text":new_text,"delta_text":("+" if delta>0 else "")+str(delta)+suffix if delta!=0 else "不变"})
	var compatible=Items.can_use(after,target_id);var reason="适配 · 可装备"
	if not compatible:
		reason="不适配 · 当前职业无法使用"
		if target_id in [17,18]:reason="不适配 · 仅胡纳普可使用"
		elif int(unit.class_id)==6 and target_id in [4,7]:reason="不适配 · 士兵无法使用该枪"
	return {"compatible":compatible,"can_equip":compatible,"reason":reason,"target_id":target_id,"held_id":int(unit.get("item_id",0)),
		"name":str(unit.name_zh),"class_name":profession_name(unit,classes),"current_name":held_name(unit),"target_name":str(Items.item(target_id).get("name_zh","未知装备")),
		"before":before_stats,"after":after_stats,"rows":rows,"current_description":description(unit),"target_description":description(after)}

static func range_name(reach: Vector2i) -> String:
	return "无" if reach.y==0 else str(reach.x) if reach.x==reach.y else "%d-%d"%[reach.x,reach.y]

static func description(unit: Dictionary) -> String:
	var actor=automatic(unit);var id=int(actor.get("item_id",0));var item=Items.item(id);var notes: Array[String]=[]
	if id<=0:return "使用职业默认武器。"
	if not Items.can_use(actor,id):return "当前角色无法使用，此武器不提供加成。"
	match id:
		14:notes.append("近身攻击可能反噬自身。")
		15:notes.append("魔法攻击力固定15，按目标魔防结算。")
		51:notes.append("仅对魔物的物理攻击增加13物防。")
		52:notes.append("敌方法术命中率为10%。")
		53:notes.append("增加13物防与13魔防。")
		55:notes.append("幸运固定40，升级属性增长量加倍。")
		56:notes.append("速度固定40，移动增加5。")
		57:notes.append("使用攻击法术时，射程可达5格。")
		58:notes.append("当前生命不高于一半时，必杀为100%。")
	if item.get("family","")=="focus":notes.append("仅强化已学攻击法术，不增加法术或治疗量。")
	var effective=int(item.get("effective",0))
	if effective>0:notes.append({1:"对魔物特效。",2:"对指定兵种特效。",3:"对飞行单位特效。",4:"对骑兵特效。"}.get(effective,"对指定目标特效。"))
	if int(item.get("effect_kind",0))==10:notes.append("每回合恢复5生命。")
	if Rules.magic_cost(actor)>0:notes.append("当前攻击法术消耗%d生命。"%Rules.magic_cost(actor))
	if notes.is_empty():notes.append("属性按当前职业与实际武器计算。")
	return "".join(notes)
