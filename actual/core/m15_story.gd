extends RefCounted
## M15 prose and presentation triggers. Combat damage, exits and rewards stay
## owned by the existing battle rules; a cinematic never changes a unit's HP.

static func decorate(game,key:String,scene:String) -> void:
	if game.story_events.is_empty():return
	var event:Dictionary=game.story_events[-1]
	if str(event.get("key",""))!=key:return
	event.m15_scene=scene

static func opening(game) -> void:
	game.queue_lines(str(game.battle_data.before),"M15-BEGIN")
	decorate(game,"M15-BEGIN","opening")

static func escaping(game,unit:Dictionary) -> bool:
	return game.stage_id==105 and str(unit.get("id",""))=="M15_boss" and int(unit.get("hp",0))>0 and ((game.turn>=6 and int(unit.hp)*2<int(unit.max_hp)) or game.turn>=8)

static func announce_escape(game) -> void:
	if game.flags.quest.get("escape_announced",false):return
	game.flags.quest.escape_announced=true
	game.queue_pages(game.campaign.scenes.M15_ESCAPE,"M15-ESCAPE")
	decorate(game,"M15-ESCAPE","escape")

static func first_exchange(game,exchange:Dictionary) -> void:
	if game.stage_id!=105 or game.flags.quest.get("escape_announced",false):return
	if str(exchange.get("attacker",""))!="M15_boss" and str(exchange.get("defender",""))!="M15_boss":return
	var boss=game.find_unit("M15_boss")
	# A fatal first exchange goes straight to the last words, never challenges
	# the player to fight an opponent who is already dying.
	if boss.is_empty() or int(boss.hp)<=0:return
	game.queue_lines(str(game.battle_data.during),"M15-MID")

static func last_words(game) -> void:
	if game.flags.get("seen_D13",false):return
	game.queue_pages(game.campaign.scenes.D13,"D13")
	decorate(game,"D13","death")
	game.flags.korlan_defeated=true

static func restore(game) -> void:
	if game.stage_id!=105:return
	var boss=game.find_unit("M15_boss")
	if game.flags.get("quest",{}).get("escape_announced",false) or (not boss.is_empty() and int(boss.hp)<=0):
		game.story_events=game.story_events.filter(func(event):return str(event.get("key",""))!="M15-MID")
	# Pending queues from the old build get current text without changing map,
	# RNG, formation, wounds, rescue records, turn history or claimed rewards.
	for event in game.story_events:
		match str(event.get("key","")):
			"M15-BEGIN":
				event.m15_scene="opening";event.pages=game.dialogue_pages(str(game.stages[105].before))
			"M15-ESCAPE":
				event.m15_scene="escape";event.pages=game.campaign.scenes.M15_ESCAPE.duplicate(true)
			"D13":
				event.m15_scene="death";event.pages=game.campaign.scenes.D13.duplicate(true)
			"M15-MID":event.pages=game.dialogue_pages(str(game.stages[105].during))
			"M15-END":event.pages=game.dialogue_pages(str(game.stages[105].after))
	if game.flags.has("m15_scene") or not game.flags.has("active_plot"):return
	var plot:Dictionary=game.flags.active_plot
	if not str(plot.get("callback","")).is_empty():return
	var old="".join(plot.get("pages",[]).map(func(p):return str(p.text).replace("\n","")))
	var scene="";var pages=[]
	if old.contains("凯尔被押回营那天"):
		scene="opening";pages=game.dialogue_pages(str(game.stages[105].before))
	elif old.contains("撤离点就在旧塔后面"):
		scene="escape";pages=game.campaign.scenes.M15_ESCAPE.duplicate(true)
	elif old.contains("他已经把人放走了") or old.contains("你若让他活着"):
		scene="death";pages=game.campaign.scenes.D13.duplicate(true)
	if scene.is_empty():return
	game.flags.m15_scene={"version":1,"scene":scene,"pages":pages,"return":str(plot["return"]),"step":0,"time":0.0,"clock":0.0}
	game.flags.erase("active_plot")
