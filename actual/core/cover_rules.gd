extends RefCounted
## One committed action protects a spent adjacent ally against one damaging hit.
## Damage is shared, never deleted; an exhausted guard cannot absorb overflow.
const MELEE_CLASSES := [1,2,3,4,5,6,7,8,9,10,11,14,21,22]

static func eligible(unit:Dictionary)->bool:
	return (str(unit.get("side",""))=="player" and int(unit.get("hp",0))>0
		and int(unit.get("class_id",0)) in MELEE_CLASSES
		and not unit.get("locked",false) and not unit.get("event_object",false))

static func targets(g,actor:Dictionary)->Array:
	if not eligible(actor) or actor.get("acted",false) or g.phase!="player":return []
	return g.living("player").filter(func(u):return (str(u.id)!=str(actor.id)
		and bool(u.get("acted",false))
		and not u.get("event_object",false) and not u.get("locked",false)
		and not u.get("hidden",false) and distance(g.pos(u),g.pos(actor))==1))

static func start(g,actor:Dictionary,target_id:String)->bool:
	refresh(g)
	if not targets(g,actor).any(func(u):return str(u.id)==target_id):return false
	actor.cover_target=target_id;actor.cover_turn=g.turn
	g.mark_wait(str(actor.id))
	return true

static func distance(a:Vector2i,b:Vector2i)->int:
	return absi(a.x-b.x)+absi(a.y-b.y)

static func clear(unit:Dictionary)->void:
	unit.erase("cover_target");unit.erase("cover_turn")

static func refresh(g,new_player_phase:bool=false)->void:
	for unit in g.units:
		if not unit.has("cover_target"):continue
		var target=g.find_unit(str(unit.cover_target))
		if (new_player_phase or not eligible(unit) or target.is_empty()
			or int(target.get("hp",0))<=0 or target.get("hidden",false)
			or not target.get("acted",false)
			or str(target.get("side",""))!="player"
			or distance(g.pos(unit),g.pos(target))!=1):clear(unit)

static func guard_for(g,target:Dictionary,shadow:Dictionary={})->Dictionary:
	if str(target.get("side",""))!="player" or not target.get("acted",false):return {}
	# Stable deployment order resolves multiple guards; one hit consumes one guard.
	for original in g.units:
		var unit:Dictionary=shadow.get(str(original.id),original)
		if (eligible(unit) and str(unit.get("cover_target",""))==str(target.id)
			and int(unit.get("cover_turn",-1))==g.turn
			and distance(g.pos(unit),g.pos(target))==1):return unit
	return {}

static func split(g,target:Dictionary,damage:int,shadow:Dictionary)->Dictionary:
	if damage<=0:return {}
	var guard=guard_for(g,target,shadow)
	if guard.is_empty():return {}
	if not shadow.has(str(guard.id)):
		shadow[str(guard.id)]=guard.duplicate(true);guard=shadow[str(guard.id)]
	var before=int(guard.hp)
	var shared=mini(before,ceili(float(damage)/2.0))
	guard.hp=before-shared;clear(guard)
	return {"unit":str(guard.id),"target":str(target.id),"damage":shared,
		"hp_before":before,"hp_after":int(guard.hp),"remaining_damage":damage-shared}

static func description(g,unit:Dictionary)->String:
	if unit.has("cover_target"):
		var target=g.find_unit(str(unit.cover_target))
		if not target.is_empty() and guard_for(g,target).get("id","")==unit.id:
			return "掩护"+str(target.name_zh)+" · 待分担一次"
	var guard=guard_for(g,unit)
	if not guard.is_empty():return str(guard.name_zh)+"掩护 · 首击分担"
	return ""
