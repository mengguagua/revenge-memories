extends RefCounted
const Rules=preload("res://core/mechanical_puppets.gd")
static var cache:Dictionary={}
static func data(u:Dictionary={})->Dictionary:
	var path="res://data/pseudo_titan_art.json" if Rules.is_titan(u) else "res://data/mechanical_puppets_art.json"
	if not cache.has(path):cache[path]=JSON.parse_string(FileAccess.get_file_as_string(path))
	return cache[path]
static func portrait(u:Dictionary)->String:
	return str(data(u).get("portrait_broken" if Rules.part_hp(u)<=0 else "portrait","res://assets/mechanical-puppets-20261104/portrait.png"))
static func battle(u:Dictionary)->Dictionary:
	var d=data(u);var art:Dictionary=d.battle.duplicate(true)
	art.sequences={"idle":[int(d.idle_frames.broken if Rules.part_hp(u)<=0 else d.idle_frames.intact)]}
	art.mechanical=true
	return art
static func map_sprite(kind:String,u:Dictionary)->Dictionary:
	var art:Dictionary=data(u).maps["broken" if Rules.part_hp(u)<=0 else "intact"].duplicate(true)
	if kind=="map_move":art.erase("native_cycle");art.erase("cycle_ticks")
	return art
static func reaction(u:Dictionary,kind:String)->Dictionary:
	var prefix="broken-" if Rules.part_hp(u)<=0 else ""
	var key=prefix+{"hit":"hit","exit":"defeat"}.get(kind,"idle")
	if kind=="reflection":key="reflection"
	if kind=="part_break":key="core-break" if Rules.is_titan(u) else "part-break"
	return data(u).variants.get(key,{})
static func selection(u:Dictionary,event:Dictionary,actor_origin:Vector2,target_origin:Vector2,left:bool)->Dictionary:
	var key=("broken-" if Rules.part_hp(u)<=0 else "")+("cannon" if int(event.get("weapon_index",0))==Rules.WATER else "melee")
	var variant:Dictionary=data(u).variants[key].duplicate(true)
	var sign=-1.0 if left else 1.0
	var scale=maxf(0,absf(target_origin.x-actor_origin.x)-(28.0 if Rules.is_titan(u) else 24.0))/(84.0 if Rules.is_titan(u) else 88.0)
	for row in variant.frames:
		row.offset[0]*=sign*scale
		for effect in row.get("effects",[]):
			var progress=(176.0-float(effect.position[0]))/112.0
			effect.position[0]=lerpf(actor_origin.x,target_origin.x,progress)
			effect.position[1]+=actor_origin.y-128.0
			if left:effect.flip=not bool(effect.flip)
	return {"kind":"source","key":"mechanical_"+key,"sprite":battle(u),"variant":variant}
