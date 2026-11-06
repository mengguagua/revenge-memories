extends SceneTree
const Items = preload("res://core/item_rules.gd")
const Rules = preload("res://core/combat_rules.gd")
const Body = preload("res://core/innate_attacks.gd")
const Heroes = preload("res://core/hero_professions.gd")
const Summons = preload("res://core/summon_rules.gd")

func describe(unit: Dictionary) -> Dictionary:
	var u = unit.duplicate(true)
	u.side = "enemy"
	var defender = {"id":"reference","side":"player","class_id":6,"character_id":5,"hp":52,"max_hp":52,"strength":10,"skill":0,"speed":0,"luck":0,"defence":10,"resistance":10,"item_id":0}
	var options = []
	var seen = {}
	for distance in [1,2,3,5]:
		var contexts = [Rules.attack_context(u,distance),Rules.attack_context(u,distance,true)]
		if not Body.is_body(u):
			for spell_id in Items.spells(u):
				if Items.is_support(spell_id):continue
				var copy=u.duplicate(true);copy.weapon_index=spell_id;contexts.append(copy)
		for context in contexts:
			var index=Rules.weapon_index(context)
			if seen.has(index) or not Rules.can_attack(context,distance):continue
			seen[index]=true
			var stats=Rules.attack_stats(context,defender,0)
			var profile=Items.weapon_profile(context,index)
			var reach=Rules.attack_range(context)
			options.append({"id":index,"name":profile.get("name_zh",""),"might":profile.get("might",0),"weight":profile.get("weight",0),"hit":profile.get("hit",0),"range_min":reach.x,"range_max":reach.y,"damage_def10":stats.damage,"attack_speed":stats.attack_speed,"magic":stats.magic,"hp_cost":stats.hp_cost})
	var item_id=int(u.get("item_id",0))
	return {"options":options,"item_name":Items.item(item_id).get("name_zh",""),"physical_defence":int(u.get("defence",0))+Items.physical_defence_bonus(u),"magic_defence":Items.magic_defence(u),"movement":Items.movement(u)}

func _initialize():
	var result={"enemies":{},"heroes":Heroes.DEFINITIONS,"items":Items.data().items,"minions":{}}
	var campaign=JSON.parse_string(FileAccess.get_file_as_string("res://data/campaign.json"))
	for entry in campaign.stages.values():
		var stage=JSON.parse_string(FileAccess.get_file_as_string(entry.path))
		for unit in stage.enemies+stage.get("reinforcements",[]):result.enemies[str(stage.code)+":"+str(unit.id)]=describe(unit)
		if stage.has("summon_template"):result.enemies[str(stage.code)+":summon_template"]=describe(stage.summon_template)
	for cid in [17,18]:
		var caster={"id":"F43_reference","side":"enemy","class_id":19,"route":"celica"}
		var unit=Summons.spawn_unit(caster,cid,{"campaign_minion":true,"source_template_index":3 if cid==17 else 10})
		result.minions[str(cid)]={"unit":unit,"combat":describe(unit)}
	var file=FileAccess.open("res://reports/full-playtest-20261023/difficulty/_support/runtime.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(result,"  "))
	print("Difficulty runtime profiles exported for ",result.enemies.size()," deployed or event templates.")
	quit()
