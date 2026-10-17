extends "res://tests/polish_play.gd"
## Real keyboard village walk/dialogue. Directed combat samples are explicitly
## marked fixtures and never counted as natural victories.
const MOTION_OUT="res://reports/clarity-0.5.2/motion/"
var movie=""
var frames=[]
var walk_states={}
var last_frame_ms=0
var alive=true
var film_failures=[]
var sample_results=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	review_out=MOTION_OUT;call_deferred("run")
func _observe():
	while alive:
		await process_frame
		if movie.is_empty() or not is_instance_valid(ui) or Time.get_ticks_msec()-last_frame_ms<20:continue
		await RenderingServer.frame_post_draw
		if not alive or movie.is_empty():continue
		last_frame_ms=Time.get_ticks_msec()
		var path=MOTION_OUT+movie+"-"+str(frames.size()).pad_zeros(5)+".png";viewport.get_texture().get_image().save_png(path)
		var record={"path":path,"movie":movie,"clock_ms":last_frame_ms,"fixture":movie!="walk","layout_errors":ui.layout_errors.duplicate(),"poses":ui.combat_poses.duplicate(),"offsets":str(ui.combat_offsets),"contact_calls":ui.battle_animation.contact_calls,"source_tick":ui.battle_animation.active_tick,"source_variant":ui.battle_animation.active_variant}
		if movie=="walk":
			var hub=ui.hub_controller;var direction="up" if hub.facing.y<0 else "down" if hub.facing.y>0 else "left" if hub.facing.x<0 else "right"
			var step=(int(hub.clock*60.0988)>>4)&1 if hub.motion_left>0 else 0
			record["direction"]=direction;record["step"]=step;record["position"]=str(hub.render_position)
			if hub.motion_left>0:walk_states[direction+":"+str(step)]=true
		frames.append(record)
		if not ui.layout_errors.is_empty():film_failures.append(record)
func shot(name: String):
	ui.queue_redraw();for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(MOTION_OUT+name+".png")
	if not ui.layout_errors.is_empty():film_failures.append({"name":name,"errors":ui.layout_errors.duplicate()})
func walk(target: Vector2i):
	var path=_hub_route(target)
	if path.is_empty():film_failures.append("Walk route blocked: "+str(target));return
	path.pop_front()
	for cell in path:
		while ui.hub_controller.motion_left>0:await process_frame
		var d=cell-ui.game.hub_position
		key(KEY_LEFT if d.x<0 else KEY_RIGHT if d.x>0 else KEY_UP if d.y<0 else KEY_DOWN)
		while ui.hub_controller.motion_left>0:await process_frame
		if ui.game.hub_position!=cell:film_failures.append("Actual key movement differs: "+str(cell));return
func sample(kind: String):
	# Isolated, declared fixtures exercise actual renderer/contact feedback, not
	# world progress. No saved playthrough is edited or claimed as a victory.
	ui.instant_mode=false;ui.game.new_game();ui.game.world_node=2;ui.game.start_battle(101)
	var hero=ui.game.find_unit("hunapu");var foe=ui.game.find_unit("M11_e1")
	if kind=="levin":hero.item_id=15
	if kind=="dying":hero.hp=1 # Declared HP boundary fixture, never a saved playthrough.
	ui.view="combat";ui.busy=true;ui._clear_menu();ui.phase_time=0;ui.notice_time=0
	var incoming=kind in ["hit","dying"]
	var actor=foe if incoming else hero;var target=hero if incoming else foe
	var damage=int(Rules.attack_stats(actor,target,ui.game.terrain_avoid(State.pos(target))).damage)*(3 if kind=="critical" else 1)
	var hit=kind!="miss";var hp_after=maxi(0,int(target.hp)-damage) if hit else int(target.hp)
	ui.combat={"attacker":actor.id,"defender":target.id,"distance":2 if kind=="levin" else 1,"initiative_side":actor.side}
	ui.combat.stats={}
	for who in [hero,foe]:
		var other=foe if who.id==hero.id else hero
		var stats=Rules.attack_stats(who,other,ui.game.terrain_avoid(State.pos(other)))
		stats.can_strike=Rules.can_attack(who,int(ui.combat.distance));ui.combat.stats[who.id]=stats
	ui.combat_poses={hero.id:60,foe.id:int(ui._battle_sprite(foe).sequences.idle[0])};ui.combat_offsets.clear();ui.combat_hp={hero.id:hero.hp,foe.id:foe.hp};ui.combat_fades.clear();ui.combat_shake=0;ui.combat_message=""
	ui.battle_animation.reset()
	var event={"attacker":actor.id,"defender":target.id,"weapon_index":Rules.weapon_index(actor),"distance":ui.combat.distance,"hit":hit,"critical":kind=="critical","damage":damage if hit else 0,"hp_before":target.hp,"hp_after":hp_after,"source_hp_before":actor.hp,"source_hp_after":actor.hp,"self_damage":0,"hp_cost":0}
	movie=kind;await ui._wait(.3);await ui.battle_animation.play(event);await ui._wait(.3);movie=""
	sample_results.append({"kind":kind,"fixture":true,"contacts":ui.battle_animation.contact_calls,"effects_clean":ui.battle_animation.effects.is_empty(),"hero_recovered_offset":str(ui.combat_offsets.get("hunapu",Vector2.ZERO)),"layout_errors":ui.layout_errors.duplicate()})
	if ui.battle_animation.contact_calls!=1:film_failures.append("Fixture contact count: "+kind)
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(MOTION_OUT));allow_capture=true
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.game.save_path="res://reports/campaign/natural-prologue-save.json";var loaded=ui.game.load_game();ui.game.save_path=MOTION_OUT+"working.json"
	if not loaded:film_failures.append("Prologue source save unavailable");quit(1);return
	ui.hub_controller.resume();ui.instant_mode=false;ui.notice_time=0;ui.phase_time=0
	_observe();await shot("01-caption-and-native-actor")
	movie="walk"
	for target in [Vector2i(3,7),Vector2i(3,5),Vector2i(6,5),Vector2i(6,7)]:await walk(target)
	await ui._wait(.3);movie=""
	await walk(Vector2i(7,3));key(KEY_UP);key(KEY_Z)
	for i in range(60):
		await process_frame
		if ui.view=="plot" and ui.plot_pages[ui.plot_index].speaker=="胡纳普":break
		if ui.view=="plot":key(KEY_Z)
	if ui.view=="plot" and ui.plot_pages[ui.plot_index].speaker=="胡纳普":
		key(KEY_Z);await shot("02-hunapu-mouth-actual-dialogue")
	else:film_failures.append("Actual protagonist dialogue was not reached")
	ui.instant_mode=true;await settle();ui.instant_mode=false
	for kind in ["normal","critical","miss","hit","dying","levin"]:await sample(kind)
	alive=false;await process_frame
	if walk_states.size()!=8:film_failures.append("Not all four directions/two native step frames observed: "+str(walk_states))
	var report={"passed":film_failures.is_empty(),"background_guard":true,"visible_windows":false,"walk_uses_actual_keys":true,"walk_fixture":false,"walk_states":walk_states,"frames":frames,"combat_samples":sample_results,"scope":"Real keyboard walking and dialogue from genuine prologue save. Combat demonstration events are isolated directed fixtures; real battle victories are recorded separately in the two play rounds.","failures":film_failures}
	var file=FileAccess.open(MOTION_OUT+"motion-checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("CLARITY_MOTION ",report.passed," frames ",frames.size()," failures ",film_failures)
	ui.set_process(false);viewport.remove_child(ui);ui.hub_controller.dispose();ui.hub_controller=null;ui.free();ui=null;viewport.queue_free();await process_frame
	quit(0 if report.passed else 1)
