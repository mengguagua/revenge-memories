extends RefCounted
## Apply only known pre-tuning values. Never stack bonuses or rewrite live HP.
static var cache:Dictionary={}
static func data()->Dictionary:
	if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/enemy_balance_20261025.json"))
	return cache
static func prepare(stage:int,actors:Array)->void:
	var balance=data();var base_revision=int(balance.get("base_revision",1))
	for unit in actors:
		if unit.side!="enemy":continue
		var revision=int(unit.get("enemy_balance_revision",0))
		if revision>=int(balance.revision):continue
		if revision<base_revision:_apply(unit,balance.stages.get(str(stage),{}))
		for update in balance.get("updates",[]):
			if revision<int(update.revision):_apply(unit,update.stages.get(str(stage),{}))
		unit.enemy_balance_revision=int(balance.revision)

static func _apply(unit:Dictionary,changes:Dictionary)->void:
	if not changes.has(str(unit.id)):return
	var patch:Dictionary=changes[str(unit.id)]
	for key in patch.after:
		if unit.get(key)==patch.before[key]:unit[key]=patch.after[key]
