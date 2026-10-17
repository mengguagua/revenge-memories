extends RefCounted
## Hunapu's personal art; source class animations and combat programs are retained.
static var cache: Dictionary={}
static func data() -> Dictionary:
	if cache.is_empty() and FileAccess.file_exists("res://data/hunapu_visuals.json"):
		cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/hunapu_visuals.json"))
	return cache
static func applies(actor: Dictionary) -> bool:
	return str(actor.get("id",""))=="hunapu" and str(actor.get("side","player"))=="player" and int(actor.get("class_id",21))==21 and not bool(actor.get("promoted",actor.get("alm_promoted",false)))
static func sprite(kind: String) -> Dictionary:
	var value: Dictionary=data().get(kind,{})
	return value.duplicate(true) if not value.is_empty() and ResourceLoader.exists(str(value.path)) else {}
static func battle(actor: Dictionary,original: Dictionary) -> Dictionary:
	if not applies(actor):return original
	var art=sprite("battle")
	if art.is_empty():return original
	var result=original.duplicate(false)
	result.path=art.path;result.personal_art="hunapu-"+str(data().get("version",""))
	if data().has("executed_melee"):result.personal_source_programs=data().executed_melee
	return result
