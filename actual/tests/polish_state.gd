extends SceneTree
const State=preload("res://core/game_state.gd")
const Panels=preload("res://core/battle_panel_layout.gd")
const Rules=preload("res://core/combat_rules.gd")
var checks: Array=[]
var failures: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func fresh(chapter: int=1):
	var g=State.new();g.new_game();g.save_path="res://.cache/playtest-0.5.0/state.json"
	if chapter==2:g.cleared_stages.append(105);g.flags.chapter1_complete=true;g.begin_chapter_two()
	return g
func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://.cache/playtest-0.5.0"))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/playtest-0.5.0"))
	for width in [256,320,426,480]:
		var bounds=Rect2(-(width-256)/2.0,0,width,240)
		for x in range(12,width-12,16):
			for y in range(12,228,16):
				var anchor=bounds.position+Vector2(x,y)
				var result=Panels.place(anchor,Vector2(144,92),bounds)
				check(result.valid and bounds.grow(-8).encloses(result.panel) and not result.panel.intersects(result.focus),"Panel excludes cursor sprite and arrow: %s,%s,%s"%[width,x,y])
	var catalogue=fresh();var stage_records=[]
	for stage_id in catalogue.stages:
		var stage=catalogue.stages[stage_id];var g=fresh(int(stage.chapter));g.world_node=int(stage.node)
		check(g.start_battle(stage_id),"Normal stage entry: "+str(stage.code))
		var occupied={}
		for actor in g.units:
			var cell=g.pos(actor)
			check(not occupied.has(cell),"Unique deployment tile: "+str(stage.code)+":"+str(actor.id));occupied[cell]=true
			check(g.in_bounds(cell) and g.movement_cost(actor,cell)<255,"Deployment is on legal terrain: "+str(stage.code)+":"+str(actor.id))
		for object in stage.objects:
			var at=Vector2i(object.position[0],object.position[1])
			check(g.in_bounds(at),"Objective or visit inside map: "+str(stage.code)+":"+str(object.id))
			if object.get("kind","")=="visit":
				for front in g.visit_fronts(object):check(g.in_bounds(front) and g.movement_cost(g.find_unit(g.leader_id()),front)<255,"Legal visit approach: "+str(stage.code)+":"+str(front))
		if not g.exit_marker().is_empty():
			var exit_=Vector2i(stage.exit[0],stage.exit[1])
			check(g.in_bounds(exit_) and g.movement_cost(g.find_unit(g.leader_id()),exit_)<255,"Exit flag is on walkable terrain: "+str(stage.code))
		var nearest=9999
		for ally in g.living("player"):
			if ally.get("neutral",false):continue
			for enemy in g.living("enemy"):nearest=mini(nearest,absi(g.pos(ally).x-g.pos(enemy).x)+absi(g.pos(ally).y-g.pos(enemy).y))
		check(nearest<=10,"Opening contact is close: "+str(stage.code))
		stage_records.append({"stage":stage.code,"enemies":g.living("enemy").size(),"first_contact_distance":nearest})
	var g=fresh();g.world_node=2;g.start_battle(101)
	check(g.battle_data.map.width==22 and g.battle_data.map.height==18 and g.living("enemy").size()==10,"M11 compact valley and ten initial foes")
	var boss=g.find_unit("M11_boss")
	check(boss.name_zh=="追击队长" and int(boss.level)>1 and int(boss.max_hp)>22 and int(boss.strength)>7,"M11 visible captain matches objective and has stronger stats")
	var hero=g.find_unit("hunapu");g.units=[hero,boss]
	var goal=Vector2i(g.battle_data.exit[0],g.battle_data.exit[1])
	check(not g.reachable(hero,true).costs.has(goal),"Captain blocks the only exit entrance")
	boss.hp=0
	check(g.reachable(hero,true).costs.has(goal),"Defeated captain opens real exit path")
	g=fresh();g.world_node=2;g.start_battle(101)
	var archer=g.units.filter(func(u):return u.side=="enemy" and int(u.class_id)==12)[0]
	hero=g.find_unit("hunapu");g.units=[hero,archer]
	var action=g.ai_action(archer)
	check(action.destination!=g.pos(archer) or not str(action.target).is_empty(),"Archer advances or fires instead of being frozen by guard behavior")
	var fired=false
	for turn in range(4):
		action=g.ai_action(archer)
		if not str(action.target).is_empty():
			var distance=absi(action.destination.x-g.pos(hero).x)+absi(action.destination.y-g.pos(hero).y)
			fired=Rules.can_attack(archer,distance);break
		archer.position=[action.destination.x,action.destination.y]
	check(fired,"Ranged pursuit reaches an actual valid firing position")
	g=fresh();g.world_node=2;g.start_battle(101);hero=g.find_unit("hunapu");hero.exp=70
	g.battle_outcome="victory";check(g.complete_battle(),"Clear experience settles once")
	check(int(g.roster.hunapu.level)==2 and int(g.roster.hunapu.exp)<100,"Training reward crosses level threshold with normal growth")
	check(g.victory_rewards.any(func(r):return r.unit=="hunapu" and r.leveled and r.get("victory_training",false)),"Level-up presentation data includes clear training and growth")
	var roster=g.roster.duplicate(true);var bags=g.convoy.duplicate(true)
	check(not g.complete_battle() and roster==g.roster and bags==g.convoy,"Repeated result cannot duplicate EXP growth or items")
	var legacy=State.new();legacy.save_path="res://reports/campaign/natural-M11-deployment-save.json"
	check(legacy.load_game() and int(legacy.battle_data.map.width)==24,"Old schema-1 active checkpoint retains its genuine 0.2.1 geometry before explicit retry")
	legacy.save_path="res://.cache/playtest-0.5.0/old.json"
	check(legacy.retry_battle() and int(legacy.battle_data.map.width)==22,"Explicit retry adopts new geometry from genuine prebattle snapshot")
	check(legacy.save_game() and legacy.load_game(),"New geometry and injury schema roundtrip together")
	var report={"passed":failures.is_empty(),"checks":checks.size(),"labels":checks,"failures":failures,"stages":stage_records,"scope":"Directed layout grid, all 15 deployment geometries, ranged intent, captain choke, clear experience and real old-save retry fixtures; not natural play victories."}
	var f=FileAccess.open("res://reports/playtest-0.5.0/state-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("POLISH_STATE ",checks.size()," FAILURES ",failures);quit(0 if failures.is_empty() else 1)
