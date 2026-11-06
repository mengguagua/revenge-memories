extends RefCounted
const Reviewed=preload("res://core/reviewed_animations.gd")
static var cache={}
static func data()->Dictionary:
	if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/tactical_idle_20261031.json"))
	return cache
static func sprite(original:Dictionary,actor:Dictionary,clock:float)->Dictionary:
	var spec:Dictionary=data().get(Reviewed.key(actor),{})
	if spec.is_empty():return original
	var art=original.duplicate(true)
	if spec.override.is_empty() and str(art.path)!=str(spec.path):return art
	art.merge(spec.override,true)
	var period=0
	for ticks in art.cycle_ticks:period+=int(ticks)
	var tick=int(clock*60.0988)%maxi(1,period);var frame=int(art.native_cycle[0])
	for i in range(art.native_cycle.size()):
		if tick<int(art.cycle_ticks[i]):frame=int(art.native_cycle[i]);break
		tick-=int(art.cycle_ticks[i])
	var density=float(art.get("native_density",1));var pose=spec.poses[frame]
	var target="left" if actor.get("side","")=="enemy" else "right"
	art.idle_flip=spec.source_facing!=target
	var foot_x=(float(art.frame_size[0])-float(spec.foot_x)) if art.idle_flip else float(spec.foot_x)
	art.tile_origin=[foot_x/density-8,float(pose.bottom)/density-16]
	art.anchor=[foot_x/density,float(pose.bottom)/density]
	if art.has("ground_shadow"):art.ground_shadow.offset=[0,-float(art.ground_shadow.size[1])/2]
	art.idle_alignment={"frame":frame,"facing":target,"foot":[8,16],"source_bounds":pose.bounds}
	return art
