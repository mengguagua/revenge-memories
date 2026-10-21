extends SceneTree
const OUT="res://reports/recent-art-20261021/screenshots/"
var ui
var viewport
var shots:Array=[]
var errors:Array=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name:String):
	ui.queue_redraw()
	for n in range(2):await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	shots.append({"name":name,"layout_errors":ui.layout_errors.duplicate()})
	if not ui.layout_errors.is_empty():errors.append({"name":name,"errors":ui.layout_errors.duplicate()})
func actor(cid:int,side:String,id:String,position:Array)->Dictionary:
	var a=ui.game.characters.hunapu.duplicate(true)
	a.merge({"id":id,"class_id":cid,"side":side,"position":position,"hp":30,"max_hp":30,"acted":false,"name_zh":"敌军" if side=="enemy" else "盟军"},true)
	return a
func battle(cid:int,side:String,weapon:int,tick:int,name:String,target_class:int=6):
	var a=actor(cid,side,"art_actor",[4,4]);var b=actor(target_class,"player" if side=="enemy" else "enemy","art_target",[5,4])
	ui.game.units=[a,b];ui.view="combat";ui.combat={"attacker":a.id,"defender":b.id,"distance":1,"initiative_side":side}
	ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.battle_animation.reset()
	var event={"attacker":a.id,"defender":b.id,"weapon_index":weapon,"critical":false,"visual_only":true}
	if not ui.battle_animation.show_frame(event,tick):errors.append("no frame "+name);return
	await shot(name)
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.new_game();ui.game.save_path="/private/tmp/recent-art-capture-unused.json"
	ui.game.start_battle(101);ui.game.story_events.clear();ui.view="battle";ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false
	var units=[]
	for pair in [[1,"player"],[1,"enemy"],[4,"player"],[4,"enemy"],[7,"player"],[14,"player"],[15,"player"],[15,"enemy"]]:
		var n=units.size();units.append(actor(pair[0],pair[1],"map_"+str(n),[4+n%4*2,4+n/4*2]))
	ui.game.units=units;ui._focus_battle(Vector2i(7,5),true);ui.elapsed=0
	await shot("01-map-all-idle")
	ui.elapsed=22.1/60.0988;await shot("02-map-idle-phase")
	for n in [2,3]:
		ui.moving_id=units[n].id;ui.moving_position=Vector2(ui.game.pos(units[n]))*16;ui.moving_direction=Vector2i.LEFT
		for tick in [0,8,16,24]:
			ui.elapsed=(tick+0.1)/60.0988;await shot("03-knight-"+str(n)+"-left-"+str(tick))
	ui.moving_id=units[5].id;ui.moving_position=Vector2(ui.game.pos(units[5]))*16
	for direction in [Vector2i.LEFT,Vector2i.RIGHT]:
		ui.moving_direction=direction;ui.elapsed=16.1/60.0988;await shot("04-militia-bent-arm-"+str(direction.x))
	ui.moving_id=""
	for side in ["player","enemy"]:
		await battle(1,side,4,35,"05-cavalry-lance-"+side)
		await battle(4,side,0,32,"06-knight-battle-"+side)
		await battle(15,side,23,50,"07-fire-charge-"+side)
		await battle(15,side,24,38,"08-staff-"+side)
		await battle(15,side,31,89,"09-ghost-fire-"+side)
		await battle(15,side,32,325,"10-slime-real-cavalry-"+side,1)
		await battle(15,side,32,325,"11-slime-real-soldier-"+side,6)
	var f=FileAccess.open(OUT+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"fixture":true,"background_guard":true,"actual_runtime":true},"  "));f.close()
	print("RECENT_ART_VISUAL ",shots.size()," screenshots; errors ",errors)
	ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
