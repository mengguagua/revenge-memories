extends RefCounted
const Experience=preload("res://core/enemy_experience.gd")
## Apply only known pre-tuning values. Never stack bonuses; preserve wounds and deaths.
static var cache:Dictionary={}
static func data()->Dictionary:
	if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/enemy_balance_20261025.json"))
	return cache
static func prepare(stage:int,actors:Array)->void:
	var balance=data();var base_revision=int(balance.get("base_revision",1))
	for unit in actors:
		if unit.side!="enemy":continue
		if str(unit.get("behavior","")) in ["guard","guard_exit"] and int(unit.get("guard_ai_revision",0))<2:
			# Old proximity alerts cannot prove an attack. A remaining wound can.
			unit.guard_alerted=int(unit.get("hp",0))<int(unit.get("max_hp",0))
			unit.guard_ai_revision=2
		var revision=int(unit.get("enemy_balance_revision",0))
		if revision>=int(balance.revision):continue
		if revision<base_revision:_apply(unit,balance.stages.get(str(stage),{}))
		for update in balance.get("updates",[]):
			if revision<int(update.revision):_apply(unit,update.stages.get(str(stage),{}))
		unit.enemy_balance_revision=int(balance.revision)
	# Run even when older stat patches were already applied. Current class and
	# level, rather than the historical cached value, determine every enemy V.
	Experience.prepare(stage,actors)

static func _apply(unit:Dictionary,changes:Dictionary)->void:
	if not changes.has(str(unit.id)):return
	var patch:Dictionary=changes[str(unit.id)]
	var old_class=int(unit.get("class_id",0))
	var old_item=int(unit.get("item_id",0))
	for key in patch.after:
		# Optional boolean flags are false when absent from an older journal.
		if unit.get(key,false if patch.before[key] is bool else null)!=patch.before[key]:continue
		if key=="max_hp":
			# Preserve missing HP when a known maximum changes; never revive a corpse.
			var old_hp=int(unit.get("hp",0));var delta=int(patch.after[key])-int(patch.before[key])
			unit.max_hp=int(patch.after[key])
			unit.hp=0 if old_hp<=0 else clampi(old_hp+delta,1,int(unit.max_hp))
		else:unit[key]=patch.after[key]
	if old_class!=int(unit.get("class_id",0)) or old_item!=int(unit.get("item_id",0)):unit.erase("weapon_index")
