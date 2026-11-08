extends RefCounted
## Peaceful hub identities only. Battle bodies and escort movement are untouched.
static var cache:Dictionary={}
static func data()->Dictionary:
	if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/postbattle_npcs_20261025.json"))
	return cache
static func profile(game,name:String)->String:
	if game.mode!="hub":return ""
	if name in ["村中老妇","老妇","村中家属"]:return "village_elder_woman"
	if name in ["老矿工","矿工"]:return "miner_foreman"
	if name=="年轻矿工":return "miner_young_woman"
	if name in ["村民","村中居民"]:return "village_man"
	if game.hub_record=="H09":
		if name=="运药员":return "village_man"
		if name=="管理员":return "village_elder_woman"
	return ""
static func hub(game,object:Dictionary)->Dictionary:
	var name=str(object.get("name",""))
	var key="village_man" if name=="马丁" else profile(game,name)
	return data().profiles.get(key,{}).get("hub",{}).duplicate(true)
static func portrait(game,name:String)->Dictionary:
	var key=profile(game,name);var path=str(data().profiles.get(key,{}).get("portrait",""))
	if path.is_empty() or not ResourceLoader.exists(path):return {}
	return {"path":path,"size":[48,48],"key":"postbattle_"+key}

static func refresh_saved_dialogue(game,pages:Array)->Array:
	# A paused conversation stores rendered pages. Refresh only the retired hub line.
	if game.mode!="hub" or game.hub_record!="H08":return pages
	var result=pages.duplicate(true)
	for page in result:
		if str(page.get("text",""))=="工具不是开路的钥匙。你即使没有找到工具，也能继续追查科兰。":
			page.speaker="年轻矿工"
			page.text="谢谢你们救了大家。那些工具，我们自己收拾就行了。"
	return result
