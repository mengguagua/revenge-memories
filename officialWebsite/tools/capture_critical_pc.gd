extends SceneTree
## Website captures: production PC renderer, native critical program, isolated fixtures.
const OUT="/Users/gcc/gaocc/project/revenge-memories/officialWebsite/source/critical-captures/"
const FRAMES="/private/tmp/website-critical-pc-frames/"
const Cinema=preload("res://core/critical_cinema.gd")
var vp
var ui
var errors=[]
var records=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func picture(path:String):
	ui.queue_redraw()
	await process_frame;await RenderingServer.frame_post_draw
	for e in ui.layout_errors:
		if not errors.has(str(e)):errors.append(str(e))
	vp.get_texture().get_image().save_png(path)
func fixture(key:String,stage:int=101,enemy_class:int=4)->Dictionary:
	ui.battle_animation.reset();ui.game.new_game();ui.game.stage_id=stage;ui.game.battle_data=ui.game.stages[stage].duplicate(true);ui.game.mode="battle";ui.game.save_path="/private/tmp/website-critical-journal.json"
	var spec=Cinema.data().cases[key];var hero=ui.game.characters[str(spec.hero)].duplicate(true)
	hero.side="player";hero.position=[4,4];hero.hp=40;hero.max_hp=40;hero.no_experience=true;hero.item_id=22 if str(spec.weapon)=="弓" else 24 if str(spec.get("spell",""))=="thunder" else 0
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
	DirAccess.make_dir_recursive_absolute(OUT)
	DirAccess.make_dir_recursive_absolute(FRAMES)
	vp=SubViewport.new();vp.size=Vector2i(1278,720);vp.size_2d_override=Vector2i(426,240);vp.size_2d_override_stretch=true;vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	ui=load("res://scenes/main.tscn").instantiate();vp.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.audio.stop_all();ui.instant_mode=true;ui.game.slot_directory="/private/tmp/website-critical-pc-slots"
	for job in [["hunapu-sword",101],["hunapu-bow-advanced",301],["eileen-sword-advanced",201],["eileen-thunder-advanced",303]]:
		var key=str(job[0]);var event=fixture(key,int(job[1]));var cinema=ui.battle_animation.cinema
		if not cinema.prepare(event):errors.append("Cannot prepare "+key);continue
		var folder=FRAMES+key+"/";DirAccess.make_dir_recursive_absolute(folder)
		var frames=roundi(cinema.duration()*30);var contacted=false
		for frame in range(frames):
			cinema.elapsed=frame/30.
			if not contacted and cinema.elapsed>=float(cinema.spec.hit):
				contacted=true;await ui.battle_animation._contact(event)
			await picture(folder+"frame-%04d.png"%frame)
			if frame==42:vp.get_texture().get_image().save_png(OUT+key+"-portrait.png")
			if frame==ceili((float(cinema.spec.hit)+.25)*30):vp.get_texture().get_image().save_png(OUT+key+"-impact.png")
		records.append({"key":key,"frames":frames,"seconds":frames/30.,"hit":cinema.spec.hit,"contacts":cinema.audit.contacts.duplicate(true),"background":cinema.background_key,"final_hp":ui.game.find_unit(event.defender).hp,"movie_frames":folder})
		print("WEBSITE_CRITICAL ",key," ",frames)
	var report={"passed":errors.is_empty(),"errors":errors,"guard":true,"viewport":[1278,720],"records":records,"scope":"Current production Godot PC scene, native critical renderer, four staged legal weapon/form demonstrations, fixed 30fps capture, isolated journals; background guard kept all windows unactivated."}
	var f=FileAccess.open(OUT+"capture.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	ui.battle_animation.reset();ui.audio.stop_all();ui.queue_free();await process_frame;vp.queue_free();await process_frame
	print("WEBSITE_CRITICAL_ERRORS ",errors);quit(0 if errors.is_empty() else 1)
