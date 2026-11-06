extends RefCounted
## Missing class-6 throwing poses; existing professions keep their own programs.
const DATA="res://data/counter_animation_20261029.json"
static var cache:Dictionary={}
static func data()->Dictionary:
	if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string(DATA))
	return cache
static func sprite(actor:Dictionary,graphic:Dictionary,event:Dictionary)->Dictionary:
	if str(actor.get("side",""))!="enemy" or int(actor.get("class_id",0))!=6 or str(event.get("attacker",""))!=str(actor.get("id","")) or int(event.get("weapon_index",0)) not in [4,7]:return graphic
	var result=graphic.duplicate(false);result.merge(data().sprite,true);result.erase("campaign_safe_idle")
	return result
static func selection(graphic:Dictionary,far:String,heavy:bool)->Dictionary:
	if not graphic.get("counter_javelin",false):return {}
	var key="class_6_enemy_javelin"+("_far_"+far if not far.is_empty() else "")+("_vs_heavy" if heavy else "")
	var variant:Dictionary=data().variants.get(key,{})
	return {} if variant.is_empty() else {"kind":"source","key":"counter-20261029/"+key,"variant":variant,"sprite":graphic}
