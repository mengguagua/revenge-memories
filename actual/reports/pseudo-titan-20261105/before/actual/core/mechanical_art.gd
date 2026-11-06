extends RefCounted
const Rules=preload("res://core/mechanical_puppets.gd")
static var cache:Dictionary={}
static func data()->Dictionary:
	if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/mechanical_puppets_art.json"))
	return cache
static func battle(u:Dictionary)->Dictionary:
	var d=data();var art:Dictionary=d.battle.duplicate(true)
	art.sequences={"idle":[int(d.idle_frames.broken if Rules.cannon_hp(u)<=0 else d.idle_frames.intact)]}
	art.mechanical=true
	return art
static func map_sprite(kind:String,u:Dictionary)->Dictionary:
	var art:Dictionary=data().maps["broken" if Rules.cannon_hp(u)<=0 else "intact"].duplicate(true)
	if kind=="map_move":art.erase("native_cycle");art.erase("cycle_ticks")
	return art
static func reaction(u:Dictionary,kind:String)->Dictionary:
	var prefix="broken-" if Rules.cannon_hp(u)<=0 else ""
	var key=prefix+{"hit":"hit","exit":"defeat"}.get(kind,"idle")
	if kind=="part_break":key="part-break"
	return data().variants.get(key,{})
static func selection(u:Dictionary,event:Dictionary,actor_origin:Vector2,target_origin:Vector2,left:bool)->Dictionary:
	var key=("broken-" if Rules.cannon_hp(u)<=0 else "")+("cannon" if int(event.get("weapon_index",0))==Rules.WATER else "melee")
	var variant:Dictionary=data().variants[key].duplicate(true)
	var sign=-1.0 if left else 1.0
	var scale=maxf(0,absf(target_origin.x-actor_origin.x)-24.0)/88.0
	for row in variant.frames:
		row.offset[0]*=sign*scale
		for effect in row.get("effects",[]):
			var progress=(176.0-float(effect.position[0]))/112.0
			effect.position[0]=lerpf(actor_origin.x,target_origin.x,progress)
			effect.position[1]+=actor_origin.y-128.0
			if left:effect.flip=not bool(effect.flip)
	return {"kind":"source","key":"mechanical_"+key,"sprite":battle(u),"variant":variant}
