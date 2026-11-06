extends SceneTree
const State=preload("res://core/game_state.gd")
const Map=preload("res://core/map_skills.gd")
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")
const OUT="res://reports/map-skills-20261029/"
var checks=[]
var errors=[]
var ui
var timings=[]
var audio_errors=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh():
	var g=State.new();g.new_game();g.save_path="/private/tmp/revenge-map-skills-20261029/fixture.json";g.world_node=3;g.start_battle(102);g.story_events.clear();return g
func fixture(id:String="hunapu",advanced:bool=false,bow:bool=false):
	var g=fresh();var actor=g._initial_character(id)
	actor.side="player";actor.acted=false;actor.no_experience=true;actor.position=[8,10] if id=="hunapu" else [6,10]
	Map.clear(actor)
	if advanced:g.HeroProfessions.apply(actor)
	actor.hp=int(actor.max_hp);actor.item_id=22 if bow else 0
	var enemy=g.find_unit("M12_boss").duplicate(true);enemy.class_id=6;enemy.item_id=0;enemy.hp=100;enemy.max_hp=100;enemy.defence=5;enemy.resistance=3;enemy.speed=0;enemy.erase("story_invulnerable")
	var positions=[[9,10],[9,9],[10,11],[12,10]] if id=="hunapu" else [[9,10],[9,9],[10,10],[11,10]]
	g.units=[actor]
	for i in range(positions.size()):
		var e=enemy.duplicate(true);e.id="map_enemy_"+str(i);e.position=positions[i];g.units.append(e)
	var ally=g.roster.daan.duplicate(true);ally.side="player";ally.acted=false;ally.position=[10,10] if id=="hunapu" else [9,11];ally.hp=int(ally.max_hp);g.units.append(ally)
	g.selected_id=id;g.cursor=Vector2i(9,10);g.move_origin=g.pos(actor);return g
func domain():
	for case in [["hunapu",false,false],["hunapu",true,false],["eileen",false,false],["eileen",true,false],["hunapu",true,true]]:
		var g=fixture(case[0],case[1],case[2]);var actor=g.find_unit(case[0]);var center=Vector2i(9,10);var spec=Map.profile(actor)
		check(spec.bow==case[2],"equipped bow chooses only the promoted bow MAP "+str(case))
		var original=g.units.duplicate(true);var rng=g.rng_state
		var before=Map.preview(g,actor.id,center)
		check(g.units==original and g.rng_state==rng,"forecast is side effect free "+str(case))
		check(before.valid and before.cells.size()==(12 if case[1] else 6) if case[0]=="hunapu" else before.valid and before.cells.size()==(13 if case[1] else 5),"confirmed shape "+str(case))
		for tier in range(3):
			actor.acted=false;g.selected_id=actor.id;var hp=int(actor.hp);var count=Map.used(actor)
			var plan=Map.preview(g,actor.id,center);var ally_hp=int(g.find_unit("daan").hp)
			var result=Map.apply(g,actor.id,center)
			check(result.valid and Map.used(actor)==count+1 and actor.acted,"one action and one use "+str(case)+"/"+str(tier))
			check(int(actor.hp)==hp-int(plan.cost) and int(actor.hp)>=1,"exact ceil HP cost "+str(case)+"/"+str(tier))
			check(int(result.power)==([0,3,6] if case[1] else [0,2,4])[tier],"stair-step bonus "+str(case)+"/"+str(tier))
			check(int(g.find_unit("daan").hp)==ally_hp,"friendly safe "+str(case)+"/"+str(tier))
			for hit in plan.targets:
				check(int(g.find_unit(hit.id).hp)==int(hit.hp_after),"one settlement per target "+str(case)+"/"+str(tier)+"/"+str(hit.id))
				if case[0]=="eileen" and case[1] and hit.position==[9,10]:check(int(hit.center_bonus)==4,"promoted Eileen center +4 at every tier "+str(tier))
			var after=g.units.duplicate(true)
			check(not Map.apply(g,actor.id,center).valid and after==g.units,"duplicate confirm cannot charge or damage twice "+str(case)+"/"+str(tier))
			g.turn+=1
		check(int(actor.map_fatigue_until_turn)>0,"third use applies fatigue after MAP resolution "+str(case))
		actor.acted=false;var after=g.units.duplicate(true)
		check(not Map.apply(g,actor.id,center).valid and after==g.units,"no fourth use "+str(case))
	var g=fixture();var actor=g.find_unit("hunapu");actor.map_uses=1;actor.hp=ceili(actor.max_hp*.25)
	var initial=g.units.duplicate(true)
	check(not Map.apply(g,"hunapu",Vector2i(9,10)).valid and g.units==initial,"insufficient HP rejects without charge or action")
	actor.hp=actor.max_hp;var used_before=Map.used(actor)
	check(not Map.apply(g,"hunapu",Vector2i(9,10),Vector2i.LEFT).valid and Map.used(actor)==used_before,"empty area cannot consume an action")
	for direction in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:check(Map.cells(g,actor,Vector2i(9,10),direction).size()==6,"four directional physical areas "+str(direction))
	var e=fixture("eileen",true);check(not Map.preview(e,"eileen",Vector2i(12,10)).valid,"Eileen cannot select beyond promoted reach four")
	var mixed=fixture("hunapu",true);var archer=mixed.find_unit("hunapu")
	Map.apply(mixed,"hunapu",Vector2i(9,10));archer.acted=false;archer.item_id=22
	check(Map.profile(archer).bow and Map.used(archer)==1 and Map.profile(archer).cost>0,"sword and bow share the same hero allowance")
	check(Map.used(e.find_unit("eileen"))==0,"the two protagonists keep independent allowances")
	var protected=g.units[1];protected.story_invulnerable=true
	check(Map.preview(g,"hunapu",Vector2i(9,10)).targets[0].damage==0,"story invulnerability remains intact")
	var plain=actor.duplicate(true);Map.clear(plain);plain.item_id=0;var foe=g.units[2]
	actor.map_fatigue_until_turn=g.turn+1
	check(Items.movement(actor)==maxi(1,Items.movement(plain)-2),"fatigue reduces effective movement by two")
	check(Rules.attack_stats(actor,foe,0).damage==maxi(1,floori(Rules.attack_stats(plain,foe,0).damage*.75)),"fatigue reduces ordinary attack forecast once")
	check(Rules.strike_effect(actor,foe,true,true).damage==mini(int(foe.hp),maxi(1,floori(mini(120,int(Rules.attack_stats(plain,foe,0).damage)*3)*.75))),"fatigue scales final critical damage once")
	check(Items.phase_effect(actor,218,15,false).heal==Items.phase_effect(plain,218,15,false).heal,"fatigue leaves healing unchanged")
	Map.expire_after_player_phase(g);check(actor.has("map_fatigue_until_turn"),"fatigue survives the current player phase")
	g.turn+=1;g.phase="player";Map.expire_after_player_phase(g)
	check(not actor.has("map_fatigue_until_turn"),"fatigue ends at next player phase end")
func checkpoints():
	var g=fresh();var hero=g.find_unit("hunapu");hero.map_uses=2
	check(g.save_game(),"checkpoint accepts optional MAP fields")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game() and Map.used(loaded.find_unit("hunapu"))==2,"reload retains battle use count")
	hero.map_uses=3;hero.map_fatigue_until_turn=2;check(g.save_game() and loaded.load_game(),"third-use fatigue checkpoint reloads")
	check(int(loaded.find_unit("hunapu").get("map_fatigue_until_turn",0))==2,"reload retains fatigue expiry")
	check(loaded.retry_battle() and Map.used(loaded.find_unit("hunapu"))==0,"retry starts a fresh battle allowance")
	Map.clear(g.find_unit("hunapu"));check(g.save_game(),"old-style checkpoint without MAP fields remains valid")
	check(loaded.load_game() and Map.used(loaded.find_unit("hunapu"))==0,"old checkpoints default to unused MAP")
	hero.map_uses=3;hero.map_fatigue_until_turn=2
	g.Inventory._persist_participants(g)
	check(not g.roster.hunapu.has("map_uses") and not g.roster.hunapu.has("map_fatigue_until_turn"),"retreat persistence excludes battle-only MAP state")
func interface():
	var scene=load("res://scenes/main.tscn")
	if scene==null:check(false,"main scene loads");return
	ui=scene.instantiate();root.add_child(ui);await process_frame;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
	ui.audio.playback_failed.connect(func(key,reason):audio_errors.append([key,reason]))
	for key in ["map_hunapu_base","map_hunapu_advanced","map_eileen_base","map_eileen_advanced","map_hunapu_bow","map_bow_draw"]:
		var stream=ui.audio._get_stream("sfx",key)
		check(stream!=null and stream.get_length()>0 and stream.get_length()<1.0,"dedicated MAP cue loads in production audio controller "+key)
	for case in [["hunapu",false,false],["hunapu",true,false],["eileen",false,false],["eileen",true,false],["hunapu",true,true]]:
		ui.game=fixture(case[0],case[1],case[2]);ui.view="battle";ui.busy=false;ui.notice_time=0;ui.phase_time=0
		ui._unit_action_menu();check(ui.menu_actions.has("map:choose"),"MAP entry in hero action menu "+str(case))
		ui._menu_action("map:choose","unit_action")
		check(ui.ui_mode=="map_target","MAP targeting opens "+str(case))
		var before=ui.game.units.duplicate(true);ui._cancel()
		check(before==ui.game.units and ui.ui_mode=="action","cancel targeting preserves HP and uses "+str(case))
		ui._menu_action("map:choose","unit_action");ui._open_system_menu()
		check(before==ui.game.units and ui.ui_mode=="inspect" and ui.menu_context=="system" and ui.hero_map_animation.forecast.is_empty(),"system menu cancels targeting without cost or stale range "+str(case))
		ui._clear_menu();ui.game.selected_id=case[0];ui._unit_action_menu()
		ui._menu_action("map:choose","unit_action");ui.game.cursor=Vector2i(9,10);ui.map_facing=Vector2i.RIGHT;ui._refresh_map_forecast()
		await ui._play_map_skill()
		var a=ui.hero_map_animation.audit
		check(a.duration<=1.5 and a.contacts.size()==ui.game.units.filter(func(u):return u.get("side","")=="enemy" and int(u.hp)<100).size(),"short timeline with one visual contact per damaged target "+str(case))
		check(a.sounds.any(func(s):return str(s.key)=="map_"+str(a.case)),"distinct attack audio cue "+str(case))
		check(ui.view=="battle" and not ui.busy and not ui.hero_map_animation.active and ui.map_actor_alpha.is_empty(),"no trailing result wait; actor masks restored "+str(case))
	ui.instant_mode=false;ui.animation_speed=1.0
	for case in [["hunapu",false,false],["hunapu",true,false],["eileen",false,false],["eileen",true,false],["hunapu",true,true]]:
		ui.game=fixture(case[0],case[1],case[2]);ui.view="battle";ui.busy=false;ui.game.cursor=Vector2i(9,10);ui.map_facing=Vector2i.RIGHT
		var start=Time.get_ticks_usec();await ui._play_map_skill();var wall=float(Time.get_ticks_usec()-start)/1000000.0
		var expected=float(ui.hero_map_animation.audit.duration)
		timings.append({"case":str(ui.hero_map_animation.audit.case),"planned_seconds":expected,"wall_seconds":wall})
		check(wall>=expected-.03 and wall<=expected+.15,"real playback has no leading/trailing wait "+str(case))
	check(audio_errors.is_empty(),"all five real-time MAP sound timelines play without audio errors")
	ui.hero_map_animation.reset();ui.audio.stop_all();ui.queue_free();ui=null;await process_frame;await process_frame
func run():
	DirAccess.make_dir_recursive_absolute('/private/tmp/revenge-map-skills-20261029');DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	domain();checkpoints();await interface()
	var f=FileAccess.open(OUT+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"count":checks.size(),"checks":checks,"errors":errors,"normal_speed_timings":timings},"\t"));f.close()
	print("MAP_CHECKS=",checks.size()," ERRORS=",errors.size());quit(0 if errors.is_empty() else 1)
