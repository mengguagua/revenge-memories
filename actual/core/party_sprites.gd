extends RefCounted
## Campaign actors share class bodies; only Eileen has a personal body profile.
const Reviewed = preload("res://core/reviewed_animations.gd")
static var cache: Dictionary={}
static func data() -> Dictionary:
	if cache.is_empty() and FileAccess.file_exists("res://data/party_visuals.json"):
		cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/party_visuals.json"))
	return cache
static func applies(actor: Dictionary) -> bool:
	if str(actor.get("side","player"))!="player" or actor.get("event_object",false):return false
	if str(actor.get("id","")) in data().get("chapter1_npc_ids",[]):return true
	if str(actor.get("id","")) in data().get("neutral_ids",[]):return not actor.get("event_object",false)
	return str(actor.get("side","player"))=="player" and not actor.get("neutral",false) and not actor.get("event_object",false) and str(actor.get("id","")) in data().get("actor_ids",[])
static func class_key(actor: Dictionary) -> String:
	if str(actor.get("id","")) in data().get("chapter1_civilian_ids",[]):return "civilian"
	if str(actor.get("id","")) in data().get("neutral_ids",[]):return "civilian"
	var cid=int(actor.get("class_id",0))
	if str(actor.get("id",""))=="eileen":
		return "eileen_promoted" if cid==24 or bool(actor.get("promoted",false)) else "eileen"
	if cid==21 and bool(actor.get("promoted",actor.get("alm_promoted",false))):return "23"
	return str(cid)
static func sprite(kind: String,actor: Dictionary,chapter: int=0) -> Dictionary:
	var reviewed = Reviewed.map_sprite(kind, actor)
	if not reviewed.is_empty(): return reviewed
	if not applies(actor):return {}
	var profiles=data().get("classes",{})
	var actor_id=str(actor.get("id",""))
	if chapter==1 and (actor_id in data().get("chapter1_actor_ids",[]) or actor_id in data().get("chapter1_npc_ids",[])) and (not data().has("chapter1_review_actor_ids") or actor_id in data().chapter1_review_actor_ids):
		profiles=data().get("chapter1_classes",profiles)
	if data().has("pilot_actor_ids") and str(actor.get("id","")) not in data().get("pilot_actor_ids",[]) and str(actor.get("id","")) not in data().get("neutral_ids",[]):profiles=data().get("frozen_classes",profiles)
	if not profiles.has(class_key(actor)):profiles=data().get("frozen_classes",profiles)
	var value: Dictionary=profiles.get(class_key(actor),{}).get(kind,{})
	# Hair is an actor identity on maps; profession combat bodies remain shared.
	if kind in ["hub","map","map_move","world"]:
		var personal: Dictionary=data().get("actor_maps",{}).get(actor_id,{}).get(class_key(actor),{})
		value=personal.get("hub" if kind=="world" else kind,value)
		if kind=="world" and personal.is_empty():value=profiles.get(class_key(actor),{}).get("hub",value)
	return value.duplicate(false) if not value.is_empty() and ResourceLoader.exists(str(value.path)) else {}
static func battle(actor: Dictionary,original: Dictionary,chapter: int=0) -> Dictionary:
	var result=sprite("battle",actor,chapter)
	return original if result.is_empty() else result
