extends RefCounted
## Beck supports the actual miners; he is never a substitute rescue objective.
static func applies(g,unit:Dictionary)->bool:
	return g.stage_id==111 and str(unit.get("id",""))=="beck" and bool(unit.get("neutral",false)) and not bool(unit.get("controllable",true))
static func prepare(g,actors:Array)->void:
	for unit in actors:
		if applies(g,unit):unit.quest_kind="mine_guard"
static func action(g,unit:Dictionary,gather:bool)->Dictionary:
	var exit=Vector2i(g.battle_data.exit[0],g.battle_data.exit[1])
	var miners=g.units.filter(func(u):return str(u.id).begins_with("S11_miners") and int(u.hp)>0 and u.side!="evacuated" and not u.get("hidden",false))
	miners.sort_custom(func(a,b):return distance(g.pos(a),exit)>distance(g.pos(b),exit))
	var target=exit if miners.is_empty() else g.pos(miners[0])
	if not gather and not miners.is_empty():
		var shot=g.RefugeeTactics.safe_attack(g,unit)
		if not shot.is_empty() and distance(g.pos(g.find_unit(str(shot.target))),target)<=4:return shot
	if not miners.is_empty() and distance(g.pos(unit),target)<=2:
		var retreat=g.RefugeeTactics.disengage(g,unit)
		return retreat if not retreat.is_empty() else {"destination":g.pos(unit),"target":""}
	return g._safe_escort_move(unit,target)
static func distance(a:Vector2i,b:Vector2i)->int:return absi(a.x-b.x)+absi(a.y-b.y)
