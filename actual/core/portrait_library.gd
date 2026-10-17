extends RefCounted
## Campaign identities and regional uniforms, separate from inherited FE2 IDs.
static var cache: Dictionary={}
static func data() -> Dictionary:
	if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/portraits.json"))
	return cache
static func entry(key: String) -> Dictionary:
	if not data().assets.has(key):return {}
	if not ResourceLoader.exists(str(data().assets[key].path)):return {}
	return {"path":data().assets[key].path,"size":[48,48],"key":key}
static func phase_key(game, id: String) -> String:
	if id=="hunapu":
		if game.hub_record=="P00":return "hunapu_present"
		return "hunapu_victory" if game.flags.get("korlan_defeated",false) else "hunapu_memory"
	if id=="eileen":
		if game.hub_record=="P00":return "eileen_present"
		return "eileen_chart" if game.flags.get("sea_chart_collected",false) else "eileen_departure"
	return id
static func unit(game, actor: Dictionary) -> Dictionary:
	var id=str(actor.get("id",""))
	if game.characters.has(id):return entry(phase_key(game,id))
	var region="west" if game.stage_id<200 else "east"
	if actor.get("neutral",false) or actor.side in ["neutral","evacuated"]:
		if actor.get("quest_kind","") in ["sailor","ship"]:return entry("old_sailor" if id=="old_sailor" else "sailor")
		return entry("civilian_"+region)
	if actor.get("class","")=="gargoyle":return entry("gargoyle")
	if actor.get("class","")=="revenant":return entry("revenant")
	var cid=int(actor.get("class_id",6));var role="infantry"
	if cid in [12,13,20]:role="archer"
	elif cid in [1,3,4,5,7]:role="cavalry"
	elif cid in [2,22]:role="armored"
	elif cid in [8,9,10,14]:role="mercenary"
	elif cid in [11,15,16,17,18,19]:role="mage"
	var named={"M15_boss":"korlan","F25_boss":"pesa"}
	if named.has(id):return entry(named[id])
	return entry(region+"_"+role)
static func speaker(game, name: String) -> Dictionary:
	for id in game.characters:
		if str(game.characters[id].name_zh)==name:return entry(phase_key(game,id))
	var direct={"赫兰":"herlan","科兰":"korlan","裴萨":"pesa","乌库布·卡基":"vucub","旧船员":"old_sailor","渔村长者":"island_elder","学舍导师":"scholar","船长":"sailor","舵手":"sailor","固定舵手":"sailor","船员":"sailor","求救船员":"sailor","守灯人":"sailor","矿工":"miner","洞民":"miner"}
	if direct.has(name):return entry(direct[name])
	var region="east" if game.chapter==2 else "west"
	if name in ["医者","岛上医者","地方医者","医师","船医"]:return entry("medic_"+region)
	if name in ["管理员","仓吏","记录员","文书","账房"]:return entry("administrator_"+region)
	if name in ["教团守卫","教团兵","教团守军","指挥官","士兵","守军","焚毁兵","投降兵","斥候","甲板护卫","留守骑士"]:return entry(region+"_infantry")
	return entry("civilian_"+region)
static func source(game, source_id: int) -> Dictionary:
	for id in game.characters:
		if int(game.characters[id].character_id)==source_id:return entry(phase_key(game,id))
	return {}
