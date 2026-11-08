extends RefCounted
const Rules=preload("res://core/mechanical_puppets.gd")
static var cache:Dictionary={}
static func trio(u:Dictionary)->bool:return int(u.get("class_id",0)) in [27,28,29]
static func trio_data()->Dictionary:
	if not cache.has("trio"):cache.trio=JSON.parse_string(FileAccess.get_file_as_string("res://data/story_puppets_art.json"))
	return cache.trio
static func state(u:Dictionary)->String:
	if Rules.is_prometheus(u):
		if Rules.part_hp(u,"fire")<=0 and Rules.part_hp(u,"life")<=0:return "both-broken"
		if Rules.part_hp(u,"fire")<=0:return "fire-broken"
		if Rules.part_hp(u,"life")<=0:return "life-broken"
		return "intact"
	return "broken" if Rules.part_hp(u)<=0 else "intact"
static func data(u:Dictionary={})->Dictionary:
	if trio(u):return trio_data().models[str(u.mechanical_model)]
	var path="res://data/pseudo_titan_art.json" if Rules.is_titan(u) else "res://data/mechanical_puppets_art.json"
	if not cache.has(path):cache[path]=JSON.parse_string(FileAccess.get_file_as_string(path))
	return cache[path]
static func portrait(u:Dictionary)->String:
	if trio(u):return str(data(u).portraits[state(u)])
	return str(data(u).get("portrait_broken" if Rules.part_hp(u)<=0 else "portrait","res://assets/mechanical-puppets-20261104/portrait.png"))
static func battle(u:Dictionary)->Dictionary:
	var d=data(u);var art:Dictionary=d.battle.duplicate(true)
	art.sequences={"idle":[int(d.idle_frames[state(u)] if trio(u) else (d.idle_frames.broken if Rules.part_hp(u)<=0 else d.idle_frames.intact))]}
	art.mechanical=true
	return art
static func map_sprite(kind:String,u:Dictionary)->Dictionary:
	var art:Dictionary=data(u).maps[state(u)].duplicate(true)
	if kind=="map_move":art.erase("native_cycle");art.erase("cycle_ticks")
	return art
static func reaction(u:Dictionary,kind:String,at:Vector2=Vector2(176,128),left:bool=false)->Dictionary:
	if trio(u):
		var status=state(u);var action={"hit":"hit","exit":"defeat","revive":"revive","miss":"idle"}.get(kind,"idle")
		if kind.begins_with("part_break:"):
			var part=kind.trim_prefix("part_break:");action="break-"+part
			status=("life-broken" if Rules.part_hp(u,"life")<=0 else "intact") if part=="fire" else ("fire-broken" if Rules.part_hp(u,"fire")<=0 else "intact") if part=="life" else "intact"
		if kind=="revive":status="fire-broken" if Rules.part_hp(u,"fire")<=0 else "intact"
		var variant:Dictionary=data(u).variants.get(status+":"+action,data(u).variants[status+":idle"]).duplicate(true)
		for row in variant.frames:
			for effect in row.get("effects",[]):
				effect.position[0]=at.x+(float(effect.position[0])-176.0)*(-1 if left else 1)
				effect.position[1]+=at.y-128.0
				if left:effect.flip=not bool(effect.get("flip",false))
		return variant
	var prefix="broken-" if Rules.part_hp(u)<=0 else ""
	var key=prefix+{"hit":"hit","exit":"defeat"}.get(kind,"idle")
	if kind=="reflection":key="reflection"
	if kind.begins_with("part_break"):key="core-break" if Rules.is_titan(u) else "part-break"
	return data(u).variants.get(key,{})
static func selection(u:Dictionary,event:Dictionary,actor_origin:Vector2,target_origin:Vector2,left:bool)->Dictionary:
	if trio(u):
		var action="fire" if int(event.get("weapon_index",0))==Rules.FIRE else "ranged" if Rules.is_prometheus(u) and int(event.get("distance",1))>1 else "attack"
		var key=state(u)+":"+action;var variant:Dictionary=data(u).variants[key].duplicate(true)
		var sign=-1.0 if left else 1.0;var scale=maxf(0,absf(target_origin.x-actor_origin.x)-28.0)/84.0
		for row in variant.frames:
			row.offset[0]*=sign*scale
			for effect in row.get("effects",[]):
				var progress=(176.0-float(effect.position[0]))/112.0
				effect.position[0]=lerpf(actor_origin.x,target_origin.x,progress);effect.position[1]+=actor_origin.y-128.0
				if left:effect.flip=not bool(effect.get("flip",false))
		return {"kind":"source","key":"mechanical_"+str(u.mechanical_model)+"_"+key,"sprite":battle(u),"variant":variant,
			"puppet_fx":str(u.mechanical_model)+":"+action}
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
