extends SceneTree
const OUT="res://reports/new-art-fallback-20261026/"
const Reviewed=preload("res://core/reviewed_animations.gd")
var ui
var viewport
var shots=[]
var errors=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name:String):
	ui.queue_redraw()
	for i in range(8):ui.queue_redraw();await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	var issues=ui.layout_errors.duplicate()
	for issue in issues:errors.append(name+": "+str(issue))
	shots.append({"file":name+".png","errors":issues,"view":ui.view,"texture_paths":ui.textures.keys()})
func actor(key:String,id:String)->Dictionary:
	var a=ui.game.characters.hunapu.duplicate(true)
	a.id="eileen" if key.begins_with("eileen") else id
	a.class_id=11 if key=="eileen" else 24 if key=="eileen_promoted" else int(key.split("_")[0])
	a.side="enemy" if key.ends_with("enemy") else "player";a.position=[4,4];a.hp=28;a.max_hp=28;a.acted=false;a.promoted=key in ["23_ally","eileen_promoted"]
	a.name_zh="胡纳普" if key=="21_ally" else "艾琳" if key.begins_with("eileen") else str(ui.game.catalog.classes[str(a.class_id)].name_zh)
	if key=="21_enemy":a.campaign_final_boss=true
	return a
func duel(key:String,weapon:int,name:String):
	var a=actor(key,"fixture_actor");var b=actor("6_ally","fixture_target");b.side="player" if a.side=="enemy" else "enemy"
	ui.game.units=[a,b];ui.view="combat";ui.combat={"attacker":a.id,"defender":b.id,"distance":1,"initiative_side":a.side};ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.combat_message="";ui.combat_hit_id="";ui.battle_animation.reset()
	var e={"attacker":a.id,"defender":b.id,"weapon_index":weapon,"critical":false,"hit":true,"hp_before":28,"hp_after":26}
	ui.battle_animation.active_event=e;var chosen=ui.battle_animation.selection(e)
	if chosen.kind!="source":errors.append(name+" animation unavailable");await shot(name);return
	var tick=int(chosen.variant.contact_tick)
	var used=chosen.variant.frames[tick].get("effects",[])
	if used.is_empty():
		for n in range(chosen.variant.frames.size()):
			if chosen.variant.frames[n].get("effects",[]).size()>0:tick=n
	ui.battle_animation.show_frame(e,tick)
	await shot(name)
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(1280,960);viewport.size_2d_override=Vector2i(320,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/new-art-capture-slots";ui.game.save_path="/private/tmp/new-art-capture.json";viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	ui.game.new_game();ui.hub_controller.enter_room("P00",false,false);await shot("01-hub-new-materials")
	ui.game.world_node=2;ui.game.start_battle(101);ui.game.story_events.clear();ui.view="battle";ui.ui_mode="inspect";ui.notice_time=0;ui.phase_time=0;ui.busy=false;ui.batch_running=false;ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true);ui._open_system_menu();await shot("02-battle-menu-new-panel");ui._clear_menu()
	await duel("21_ally",15,"03-new-electric-effect")
	await duel("12_enemy",1,"04-new-arrow-effect")
	await duel("1_enemy",4,"05-new-javelin-effect")
	await duel("15_enemy",23,"06-approved-fire-effect")
	await duel("19_ally",25,"07-approved-wind-effect")
	var a=ui.game.units[0];var key=Reviewed.key(a);var saved_path=Reviewed.metadata().battle[key].path;Reviewed.metadata().battle[key].path="res://missing-approved-body.png"
	ui.battle_animation.reset();ui.combat_poses.clear();await shot("08-forced-missing-body");Reviewed.metadata().battle[key].path=saved_path
	ui.game.new_game();ui.game.world_node=2;ui.game.start_battle(101);ui.view="battle";ui.ui_mode="status";ui.notice_time=0;ui.phase_time=0
	for id in ["noya","celine"]:
		var u=ui.game.characters[id].duplicate(true);u.side="player";u.position=[4,4];u.acted=false;ui.game.units=[u];ui.status_id=id;ui.game.party=[id];await shot("09-portrait-"+id)
	var target=ui.game.units[0];ui.map_effects._program=ui.map_effects.source().programs["9"];ui.map_effects._cell=Vector2i(4,4);ui.map_effects._frame=0;ui.map_effects._active=true;ui.ui_mode="inspect";ui._focus_battle(Vector2i(4,4),true);await shot("10-new-map-care");ui.map_effects.reset()
	var f=FileAccess.open(OUT+"visual-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"guarded_background":true,"device_updated":false},"  "));f.close()
	print("NEW_ART_VISUAL ",shots.size()," shots; errors: ",errors)
	ui.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
