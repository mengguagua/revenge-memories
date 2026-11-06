extends RefCounted
## Campaign-only enemy value: approved profession base plus enemy-level growth.
## The shared original FE2 tables and player experience coefficients stay intact.
static var _data:Dictionary={}

static func data()->Dictionary:
	if _data.is_empty():_data=JSON.parse_string(FileAccess.get_file_as_string("res://data/enemy_experience_20261104.json"))
	return _data

static func base_for(stage_id:int,unit:Dictionary)->int:
	var rules=data();var boss:Dictionary=rules.bosses.get(str(stage_id),{})
	if not boss.is_empty() and str(unit.get("id",""))==str(boss.unit_id):return int(boss.base)
	return int(rules.class_bases.get(str(int(unit.get("class_id",0))),{}).get("base",0))

static func value_for(stage_id:int,unit:Dictionary)->int:
	if unit.get("training_opponent",false):return 0
	var base=base_for(stage_id,unit)
	if base<=0:return int(unit.get("exp_value",0))
	var level=maxi(1,int(unit.get("level",1)))
	return mini(255,base+floori(float(base*(level-1))/10.0))

static func prepare(stage_id:int,actors:Array)->void:
	for unit in actors:
		if str(unit.get("side",""))!="enemy":continue
		unit.exp_value=value_for(stage_id,unit)

static func prepare_stage(stage:Dictionary)->void:
	if stage.get("training",false):return
	var stage_id=int(stage.id)
	prepare(stage_id,stage.get("enemies",[]))
	prepare(stage_id,stage.get("reinforcements",[]))
	if stage.get("summon_template") is Dictionary:prepare(stage_id,[stage.summon_template])
