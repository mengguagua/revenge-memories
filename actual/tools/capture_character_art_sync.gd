extends SceneTree
const OUT="res://reports/character-art-sync-20261024/screenshots/"
const Reviewed=preload("res://core/reviewed_animations.gd")
var ui
var viewport
var shots:Array=[]
var errors:Array=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func actor(cid:int,side:String,id:String,position:Array)->Dictionary:
	var a:Dictionary=ui.game.characters.hunapu.duplicate(true)
	a.merge({"id":id,"class_id":cid,"side":side,"position":position,"hp":30,"max_hp":30,"acted":false,"promoted":cid in [23,24],"alm_promoted":false,"name_zh":"敌军" if side=="enemy" else "盟军"},true)
	if cid==21 and side=="enemy":a.campaign_final_boss=true
	return a
func shot(name:String):
	ui.queue_redraw()
	for n in range(2):await process_frame
	await RenderingServer.frame_post_draw
	var im=viewport.get_texture().get_image()
	im.save_png(OUT+name+".png")
	shots.append({"name":name,"size":[im.get_width(),im.get_height()],"layout_errors":ui.layout_errors.duplicate()})
	if not ui.layout_errors.is_empty():errors.append({"shot":name,"errors":ui.layout_errors.duplicate()})
func battle(cid:int,side:String,id:String,weapon:int,label:String,critical:bool=false):
	var a=actor(cid,side,id,[4,4]);var b=actor(6,"player" if side=="enemy" else "enemy","capture_target",[5,4])
	ui.game.units=[a,b];ui.view="combat";ui.combat={"attacker":a.id,"defender":b.id,"distance":1,"initiative_side":side}
	ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.battle_animation.reset()
	var event={"attacker":a.id,"defender":b.id,"weapon_index":weapon,"critical":critical,"hit":true,"hp_before":30,"hp_after":29,"visual_only":true}
	ui.battle_animation.active_event=event.duplicate(true)
	var chosen:Dictionary=ui.battle_animation.selection(event)
	if chosen.get("kind","")!="source":errors.append("no reviewed action "+label);return
	var contact=int(chosen.variant.contact_tick)
	for tick in [maxi(0,contact-10),contact,mini(chosen.variant.frames.size()-1,contact+9)]:
		if not ui.battle_animation.show_frame(event,tick):errors.append("no frame "+label);return
		await shot(label+"-"+str(tick))
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.new_game();ui.game.save_path="/private/tmp/character-art-capture-unused.json"
	ui.game.start_battle(101);ui.game.story_events.clear();ui.view="battle";ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false
	var units=[]
	for pair in [[23,"player","hunapu"],[24,"player","eileen"],[11,"enemy","revenant"],[14,"enemy","brigand"],[16,"enemy","rift"],[17,"enemy","bone"],[18,"enemy","eye"],[19,"enemy","summoner"],[3,"enemy","stone"],[5,"enemy","dragon"],[21,"enemy","divine"]]:
		var n=units.size();units.append(actor(pair[0],pair[1],pair[2],[3+n%4*3,3+n/4*3]))
	ui.game.units=units;ui._focus_battle(Vector2i(7,6),true);ui.elapsed=0
	await shot("01-new-map-idle")
	ui.elapsed=22.1/60.0988;await shot("02-new-map-idle-phase")
	for n in [0,1,3,8]:
		ui.moving_id=units[n].id;ui.moving_position=Vector2(ui.game.pos(units[n]))*16
		for direction in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
			ui.moving_direction=direction
			for tick in [0,16]:
				ui.elapsed=(tick+0.1)/60.0988;await shot("03-walk-"+str(n)+"-"+str(direction.x)+"-"+str(direction.y)+"-"+str(tick))
	ui.moving_id=""
	await battle(23,"player","hunapu",0,"04-dawn-normal")
	await battle(23,"player","hunapu",0,"05-dawn-critical",true)
	await battle(24,"player","eileen",0,"06-eileen-promoted")
	await battle(11,"enemy","revenant",0,"07-revenant")
	await battle(14,"enemy","brigand",0,"08-brigand")
	await battle(16,"enemy","rift",24,"09-rift-lightning")
	await battle(17,"enemy","bone",0,"10-bone-guard")
	await battle(18,"enemy","eye",0,"11-cleft-eye")
	await battle(19,"enemy","summoner",24,"12-summoner-lightning")
	await battle(3,"enemy","stone",1001,"13-legacy-stone")
	await battle(5,"enemy","dragon",1004,"14-bone-breath")
	await battle(21,"enemy","divine",1006,"15-divine-crown")
	var file=FileAccess.open(OUT+"checks.json",FileAccess.WRITE);file.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"actual_runtime":true,"background_guard":true,"device_updated":false},"  "));file.close()
	print("CHARACTER_ART_VISUAL ",shots.size()," screenshots; errors ",errors)
	ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
