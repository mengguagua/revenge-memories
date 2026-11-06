extends RefCounted
## Campaign-only safety net. Missing art never selects a source-game bitmap.
const Effects=preload("res://core/campaign_effects.gd")
const Reviewed=preload("res://core/reviewed_animations.gd")
const INDEX="res://data/campaign_graphics.json"
static var cache:Dictionary={}
static var fallbacks:Array=[]
static func graphics()->Dictionary:
	if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string(INDEX))
	return cache
static func valid(art:Dictionary)->bool:
	var path=str(art.get("path",""))
	return not path.is_empty() and not path.begins_with("res://assets/original/") and not Effects.excluded(path) and ResourceLoader.exists(path)
static func _note(actor:Dictionary,kind:String,art:Dictionary)->Dictionary:
	var result=art.duplicate(true)
	result.campaign_fallback=true
	var record={"id":str(actor.get("id","")),"class_id":int(actor.get("class_id",0)),"kind":kind,"path":str(result.get("path",""))}
	if record not in fallbacks:fallbacks.append(record)
	return result
static func map_sprite(kind:String,actor:Dictionary)->Dictionary:
	var side="enemy" if actor.get("side","")=="enemy" else "ally"
	var cid=int(actor.get("class_id",14))
	if kind=="hub" and actor.get("neutral",false):
		return _note(actor,kind,graphics().fallback_maps.civilian.hub)
	var context={"map":"tactical-idle","map_move":"tactical-walk","hub":"story","world":"world"}.get(kind,"tactical-idle")
	var choices=Reviewed.metadata().maps.get(Reviewed.key(actor),{})
	for name in [context,"tactical-idle"]:
		var art:Dictionary=choices.get(name,{})
		if valid(art):return _note(actor,kind,art)
	var entry:Dictionary=graphics().fallback_maps.get(str(cid),{}).get(kind,{})
	if valid(entry):return _note(actor,kind,entry)
	entry=graphics().map_units.get("class_%d_%s"%[cid,side],{})
	if valid(entry):return _note(actor,kind,entry)
	entry=graphics().map_units["class_6_"+side]
	return _note(actor,kind,entry)
static func map_or(art:Dictionary,kind:String,actor:Dictionary)->Dictionary:
	return art if valid(art) else map_sprite(kind,actor)
static func battle(actor:Dictionary)->Dictionary:
	var art:Dictionary=Reviewed.metadata().battle.get(Reviewed.key(actor),{})
	if valid(art):
		var side="enemy" if actor.get("side","")=="enemy" else "ally"
		var base:Dictionary=graphics().battle.get("class_%d_%s"%[int(actor.get("class_id",6)),side],{}).duplicate(false)
		base.merge(art,true);return _note(actor,"battle",base)
	var side="enemy" if actor.get("side","")=="enemy" else "ally"
	var cid=int(actor.get("class_id",6))
	art=graphics().fallback_battle.get(str(cid),{})
	if not valid(art):art=graphics().battle.get("class_%d_%s"%[cid,side],{})
	if not valid(art):art=graphics().battle["class_6_"+side]
	var result=_note(actor,"battle",art)
	# An alternate atlas has a different frame vocabulary. Its own idle is safe;
	# replaying another sheet's attack frame IDs would corrupt the new body.
	result.campaign_safe_idle=true
	result.erase("reviewed_variants");result.erase("innate_variants")
	return result
