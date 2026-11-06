extends SceneTree
## Production phone scene; deterministic frame capture, temporary journals only.
const OUT="res://reports/critical-cinema-20261104/"
const Cinema=preload("res://core/critical_cinema.gd")
var vp
var phone
var ui
var errors=[]
var records=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func picture(path:String):
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
	await process_frame;await RenderingServer.frame_post_draw
	for e in ui.layout_errors+phone.layout_errors:
		if not errors.has(str(e)):errors.append(str(e))
	vp.get_texture().get_image().save_png(OUT+path)
func fixture(key:String,stage:int=101,enemy_class:int=4)->Dictionary:
	ui.battle_animation.reset();ui.game.new_game();ui.game.stage_id=stage;ui.game.battle_data=ui.game.stages[stage].duplicate(true);ui.game.mode="battle"
	var spec=Cinema.data().cases[key];var hero=ui.game.characters[str(spec.hero)].duplicate(true)
	hero.side="player";hero.position=[4,4];hero.hp=40;hero.max_hp=40;hero.no_experience=true
	if bool(spec.advanced):ui.game.HeroProfessions.apply(hero)
	var target:Dictionary={}
	for stage_data in ui.game.stages.values():
		for enemy in stage_data.get("enemies",[]):
			if int(enemy.class_id)==enemy_class:target=enemy.duplicate(true);break
		if not target.is_empty():break
	target.id="capture_target";target.side="enemy";target.position=[5,4];target.hp=52;target.max_hp=52;target.item_id=0
	ui.game.units=[hero,target];ui.combat={"attacker":hero.id,"defender":target.id,"distance":1,"initiative_side":"player"};ui.view="combat";ui.busy=true
	ui.combat_hp={hero.id:40,target.id:52};ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.combat_message="";ui._clear_menu()
	var weapon=23 if spec.get("spell","")=="fire" else 24 if spec.get("spell","")=="thunder" else 26 if spec.get("spell","")=="holy" else 27 if spec.get("spell","")=="wind" else 1 if spec.weapon=="弓" else 0
	return {"attacker":hero.id,"defender":target.id,"weapon_index":weapon,"distance":1,"critical":true,"hit":true,"damage":28,"hp_before":52,"hp_after":24,"source_hp_before":40,"source_hp_after":38 if weapon>=23 else 40,"hp_cost":2 if weapon>=23 else 0}
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+"screens"))
	vp=SubViewport.new();vp.size=Vector2i(1280,592);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(89,0,1102,558);phone.journal_directory_override="/private/tmp/critical-capture-slots";vp.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.audio.stop_all();ui.instant_mode=true
	for key in Cinema.data().cases:
		var event=fixture(key);var cinema=ui.battle_animation.cinema;cinema.prepare(event)
		for row in [["portrait",1.4],["attack",float(cinema.spec.hit)-.3],["impact",float(cinema.spec.hit)+.1],["return",6.25]]:
			cinema.elapsed=float(row[1]);var file="screens/"+key+"-"+str(row[0])+".png";await picture(file)
			records.append({"case":key,"phase":row[0],"time":cinema.elapsed,"target_visible":cinema.audit.target_drawn,"background":cinema.background_key,"target":cinema.audit.target.duplicate(true),"file":file})
		print("CRITICAL_CAPTURE ",key)
	var themes={}
	for id in ui.game.stages:
		var stage=ui.game.stages[id];var key=Cinema.background_for(stage)
		if not themes.has(key):themes[key]=int(id)
	for theme in themes:
		var event=fixture("hunapu-sword",int(themes[theme]));await picture("screens/background-"+str(theme)+"-normal.png")
		ui.battle_animation.cinema.prepare(event);ui.battle_animation.cinema.elapsed=2.8;await picture("screens/background-"+str(theme)+".png")
	for cid in [3,12,17,18,19,21]:
		var event=fixture("eileen-holy-advanced",101,cid);ui.battle_animation.cinema.prepare(event);ui.battle_animation.cinema.elapsed=6.1
		await picture("screens/target-class-%d.png"%cid)
		if not ui.battle_animation.cinema.audit.target_drawn:errors.append("missing static real target "+str(cid))
	var movie=[]
	if OS.get_environment("CRITICAL_CAPTURE_MOVIE")=="1":
		DirAccess.make_dir_recursive_absolute("/private/tmp/critical-native-movie")
		var number=0
		for job in [["hunapu-sword",101],["eileen-sword-advanced",201]]:
			var event=fixture(str(job[0]),int(job[1]));var cinema=ui.battle_animation.cinema;cinema.prepare(event);var contacted=false;var start=number
			for frame in range(roundi(cinema.duration()*30)):
				cinema.elapsed=frame/30.
				if not contacted and cinema.elapsed>=float(cinema.spec.hit):
					contacted=true;await ui.battle_animation._contact(event)
				ui.queue_redraw();phone._sync_controls();await process_frame;await RenderingServer.frame_post_draw
				vp.get_texture().get_image().save_png("/private/tmp/critical-native-movie/frame-%05d.png"%number);number+=1
			movie.append({"key":job[0],"start":start,"frames":number-start,"contacted":contacted,"final_hp":ui.game.find_unit(event.defender).hp})
		print("CRITICAL_MOVIE ",number," frames")
	var report={"passed":errors.is_empty(),"errors":errors,"guard":true,"viewport":[1280,592],"records":records,"movie":movie,"scope":"Actual Godot production phone renderer, deterministic frame fixtures, no device installation; temporary journals only."}
	var f=FileAccess.open(OUT+"visual.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	ui.battle_animation.reset();ui.audio.stop_all();phone.queue_free();await process_frame;vp.queue_free();await process_frame
	print("CRITICAL_CAPTURE_ERRORS ",errors);quit(0 if errors.is_empty() else 1)
