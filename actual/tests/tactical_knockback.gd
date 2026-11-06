extends SceneTree
const Knockback=preload("res://core/knockback_rules.gd")
const Items=preload("res://core/item_rules.gd")
const Rules=preload("res://core/combat_rules.gd")
const State=preload("res://core/game_state.gd")
const Cover=preload("res://core/cover_rules.gd")
const OUT="res://reports/tactical-expansion-20261025/knockback-checks.json"
var checks:Array=[]
var errors:Array=[]

class Board extends RefCounted:
	var stage_id=303
	var turn=1
	var units:Array=[]
	var blocked:Array=[]
	var battle_data={"map":{"width":9,"height":9}}
	func pos(u):return Vector2i(int(u.position[0]),int(u.position[1]))
	func in_bounds(p):return p.x>=0 and p.y>=0 and p.x<9 and p.y<9
	func category(_p):return 0
	func movement_cost(_u,p):return 255 if blocked.has(p) else 1
	func can_stop(u,p):return not units.any(func(other):return other.id!=u.id and int(other.hp)>0 and pos(other)==p)
	func find_unit(id):
		for u in units:
			if u.id==id:return u
		return {}

func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func unit(id:String,side:String,at:Array,item_id:int=0,cid:int=6)->Dictionary:
	return {"id":id,"side":side,"position":at,"hp":30,"max_hp":30,"class_id":cid,"character_id":200 if side=="enemy" else 6,"item_id":item_id,"strength":10,"skill":0,"speed":5,"luck":0,"defence":3,"resistance":1,"acted":false}
func board():
	var b=Board.new();b.units=[unit("p","player",[3,3],67),unit("e","enemy",[4,3])];return b
func exchange(attacker:String="p",defender:String="e",hit:bool=true,damage:int=4)->Dictionary:
	return {"attacker":attacker,"defender":defender,"distance":1,"events":[{"attacker":attacker,"defender":defender,"hit":hit,"damage":damage,"distance":1,"weapon_index":0}]}

func authored_probe(stage:int,destination:Vector2i,defender_class:int=3):
	var g=State.new();g.new_game();g.stage_id=stage;g.battle_data=g.stages[stage].duplicate(true)
	var attacker=unit("p","player",[1,1],67);var defender=unit("e","enemy",[2,1],0,defender_class)
	for delta in [Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT,Vector2i.UP]:
		var from=destination-delta;var origin=destination-delta*2
		if not g.in_bounds(from) or not g.in_bounds(origin):continue
		if g.movement_cost(attacker,origin)>=255 or g.movement_cost(defender,from)>=255 or g.category(from)==12:continue
		attacker.position=[origin.x,origin.y];defender.position=[from.x,from.y];g.units=[attacker,defender]
		return g
	return null

func solid_terrain_checks():
	for spec in [[202,Vector2i(17,18),"ship cargo"],[402,Vector2i(16,11),"camp palisade"],[202,Vector2i(18,14),"closed prison gate"]]:
		var g=authored_probe(spec[0],spec[1])
		check(g!=null,"authored legal approach exists: "+str(spec[2]))
		if g==null:continue
		check(g.category(spec[1])==12 and g.movement_cost(g.units[1],spec[1])==1,"fixture exposes flight traversable solid: "+str(spec[2]))
		check(not Knockback.preview(g,g.units[0],g.units[1]).valid,"solid rejects flying knockback: "+str(spec[2]))
		if spec[2]=="closed prison gate":
			g.ChapterTwo.open_object(g,g.battle_data.objects.filter(func(o):return o.id=="prison_door")[0])
		else:
			var obstacle=g.battle_data.breakable_obstacles[0]
			g.Battlefield._open_obstacle(g,obstacle)
		check(Knockback.preview(g,g.units[0],g.units[1]).valid,"opened/demolished route permits flying knockback: "+str(spec[2]))
	var seed=State.new()
	for spec in [[402,1,"forest"],[202,7,"open water"]]:
		var stage:Dictionary=seed.stages[spec[0]];var probe=null
		for y in range(3,int(stage.map.height)-3):
			for x in range(3,int(stage.map.width)-3):
				var tile=int(stage.map.tiles[y*int(stage.map.width)+x])
				if int(stage.terrain.tile_categories.get(str(tile),0))!=spec[1]:continue
				probe=authored_probe(spec[0],Vector2i(x,y))
				if probe!=null:break
			if probe!=null:break
		check(probe!=null,"authored non-solid terrain found: "+str(spec[2]))
		if probe!=null:check(Knockback.preview(probe,probe.units[0],probe.units[1]).valid,"flyable terrain remains a valid knockback destination: "+str(spec[2]))

func run():
	var p=unit("p","player",[3,3],67)
	for cid in range(1,25):
		p.class_id=cid;check(Items.can_use(p,67)==(cid in [6,2,22]),"class permission "+str(cid))
	p.class_id=6
	var stats=Rules.attack_stats(p,unit("e","enemy",[4,3]),0)
	check(int(stats.damage)==10,"rejecting lance adds three might, normal defence remains")
	check(Rules.attack_speed(p)==2 and Rules.attack_range(p)==Vector2i(1,1),"heavy lance trades speed and range for displacement")
	var b=board();var rngless=Knockback.preview(b,b.units[0],b.units[1])
	check(rngless.valid and rngless.to==[5,3] and b.units[1].position==[4,3],"preview predicts displacement without mutation")
	var e=exchange();e.events.append(e.events[0].duplicate(true))
	check(Knockback.apply_exchange(b,e).valid and b.units[1].position==[5,3],"two successful initiating strikes move once")
	check(not bool(b.units[1].acted) and not bool(b.units[0].acted),"forced displacement changes no action state")
	check(Knockback.apply_exchange(b,e).is_empty() and b.units[1].position==[5,3],"repeated settlement cannot push again")
	b=board();b.blocked=[Vector2i(5,3)]
	check(not Knockback.apply_exchange(b,exchange()).valid and b.units[1].position==[4,3],"obstacle cancels push without extra collision damage")
	b=board();b.units.append(unit("blocker","player",[5,3]))
	check(not Knockback.preview(b,b.units[0],b.units[1]).valid,"living occupied destination blocks displacement")
	b.units[2].hp=0
	check(Knockback.preview(b,b.units[0],b.units[1]).valid,"vacated casualty cell does not act as invisible obstacle")
	b=board();b.units[0].position=[6,3];b.units[1].position=[7,3]
	check(not Knockback.preview(b,b.units[0],b.units[1]).valid,"battle boundary is not a legal push destination")
	for mode in ["miss","zero","defender_dead","attacker_dead","locked","object","range","magic","unusable"]:
		b=board();e=exchange()
		match mode:
			"miss":e.events[0].hit=false;e.events[0].damage=0
			"zero":e.events[0].damage=0
			"defender_dead":b.units[1].hp=0
			"attacker_dead":b.units[0].hp=0
			"locked":b.units[1].locked=true
			"object":b.units[1].event_object=true
			"range":b.units[0].position=[2,3];e.distance=2;e.events[0].distance=2
			"magic":b.units[0].weapon_index=23;e.events[0].weapon_index=23
			"unusable":b.units[0].class_id=1
		var original=b.units[1].position.duplicate();Knockback.apply_exchange(b,e)
		check(b.units[1].position==original,"no displacement for "+mode)
	b=board();e=exchange("e","p");e.events.append(exchange().events[0])
	Knockback.apply_exchange(b,e)
	check(b.units[0].position==[3,3] and b.units[1].position==[4,3],"counterattack with held lance does not knock back")
	for stage in Knockback.config().innate_elites:
		for id in Knockback.config().innate_elites[stage]:
			b=board();b.stage_id=int(stage);b.units[1].id=id
			e=exchange(id,"p");check(Knockback.apply_exchange(b,e).valid and b.units[0].position==[2,3],"listed elite moves target without a weapon: "+id)
	b=board();b.units[1].id="M33_e2"
	check(not Knockback.capable(b,b.units[1]),"ordinary enemy does not inherit elite skill")
	b=board();b.units[1].id="M33_e1"
	var guard=unit("guard","player",[3,4]);guard.cover_target="p";guard.cover_turn=1;b.units.append(guard)
	check(Cover.guard_for(b,b.units[0]).get("id","")=="guard","adjacent protection exists before elite displacement")
	Knockback.apply_exchange(b,exchange("M33_e1","p"));Cover.refresh(b)
	check(not guard.has("cover_target") and b.units[0].position==[2,3],"elite displacement breaks adjacency and cancels protection")

	var g=State.new();g.new_game();g.save_path="/private/tmp/revenge-knockback-fixture.json"
	Knockback.award_clear(g,103,false)
	check(g.convoy.alm.count(67)==0,"no reward before corresponding victory")
	g.cleared_stages.append(103);g.flags.equipment_clear_rewards={"103":true}
	g.Equipment.reconcile(g)
	check(g.convoy.alm.count(67)==1 and g.convoy.celica.count(67)==0,"old clear receives west lance despite existing supply receipt")
	var carried=int(g.roster.otto.item_id)
	g.Equipment.reconcile(g)
	check(g.convoy.alm.count(67)==1 and int(g.roster.otto.item_id)==carried,"repeat reconciliation neither duplicates nor auto equips")
	g.cleared_stages.append(105);g.flags.chapter1_complete=true
	check(g.begin_chapter_two(),"reward save fixture enters the east chapter through normal chapter transition")
	g.cleared_stages.append(204);Knockback.award_clear(g,204,false)
	check(g.convoy.celica.count(67)==1,"east clear receives independent single lance")
	check(g.save_game(),"new weapon and separate reward receipts save")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game(),"new weapon save reloads")
	loaded.Equipment.reconcile(loaded)
	check(loaded.convoy.alm.filter(func(id):return int(id)==67).size()==1 and loaded.convoy.celica.filter(func(id):return int(id)==67).size()==1,"JSON round trip retains exactly one lance in each army")
	var raw=State.read_json(g.save_path);raw.flags.knockback_clear_rewards["103"]="yes"
	check(not g.SaveValidation.campaign_valid(g,raw,g.SAVE_FIELDS),"malformed knockback reward receipt rejected")
	check(Items.can_use(g._initial_character("lord"),67) and Items.can_use(g._initial_character("otto"),67),"both routes have appropriate infantry recipients")
	solid_terrain_checks()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT.get_base_dir()))
	var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"scope":"controlled rules and supply fixtures; not a played campaign"},"  "));f.close()
	print("TACTICAL_KNOCKBACK ",checks.size()," checks; errors: ",errors)
	quit(0 if errors.is_empty() else 1)
