extends RefCounted
## A transport worker and cart share one escort target and one occupied cell.
const STAGE := 112
const DUTY_REVISION := 1

static func is_staff(unit: Dictionary) -> bool:
	return str(unit.get("id",""))=="hervi" and bool(unit.get("neutral",false)) and not bool(unit.get("controllable",true))

static func delivered(game) -> bool:
	return game.flags.get("quest",{}).get("evacuated",[]).has("medicine_wagon")

static func prepare(game,actors: Array) -> bool:
	if int(game.stage_id)!=STAGE:return false
	var changed=false
	for unit in actors:
		if str(unit.id)=="medicine_wagon":unit.name_zh="运药员与药车"
		if not is_staff(unit) or int(unit.hp)<=0:continue
		if int(unit.get("clinic_duty_revision",0))==DUTY_REVISION:continue
		var position=_station(game,unit,actors)
		if position==Vector2i(-1,-1):continue
		unit.position=[position.x,position.y]
		unit.side="neutral";unit.quest_kind="clinic_staff";unit.no_counter=true
		unit.clinic_duty_revision=DUTY_REVISION
		changed=true
	return changed

static func _station(game,unit: Dictionary,actors: Array) -> Vector2i:
	var goal=Vector2i(game.battle_data.targets[0][0],game.battle_data.targets[0][1])
	var cfg=game.battle_data.get("clinic_duty",{})
	var at=cfg.get("position",[goal.x+2,goal.y-1])
	var candidates=[Vector2i(at[0],at[1])]
	for radius in range(1,5):
		for dy in range(-radius,radius+1):
			for dx in range(-radius,radius+1):
				if absi(dx)+absi(dy)==radius:candidates.append(goal+Vector2i(dx,dy))
	var reserved=[goal]
	for object in game.battle_data.objects:reserved.append_array(game.visit_fronts(object))
	for cell in candidates:
		if reserved.has(cell) or not game.in_bounds(cell) or game.movement_cost(unit,cell)>=255:continue
		if absi(cell.x-goal.x)+absi(cell.y-goal.y)>4:continue
		if actors.any(func(other):return str(other.id)!=str(unit.id) and int(other.hp)>0 and not other.get("hidden",false) and other.side!="evacuated" and game.pos(other)==cell):continue
		return cell
	return Vector2i(-1,-1)
