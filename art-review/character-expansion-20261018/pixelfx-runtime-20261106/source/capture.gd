extends SceneTree
## Preview-only harness. Calls the shipped controller; does not patch its scripts.
const State=preload("res://core/game_state.gd")
const M=preload("res://core/mechanical_puppets.gd")
const OUT="/Users/gcc/gaocc/project/revenge-memories/art-review/character-expansion-20261018/pixelfx-runtime-20261106/source/captures/"
var vp;var phone;var ui
var playing=false
var errors=[]
var records=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":push_error("Background guard is required");quit(1);return
	call_deferred("run")
func fixture(key:String)->Dictionary:
	ui.battle_animation.reset();ui.audio.stop_all()
	ui.game=State.new()
	var stage=205 if key=="core-break" else 201
	ui.game.save_path="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F%d-deployment.json"%(25 if stage==205 else 21)
	if not ui.game.load_game():errors.append("Fixture load failed: "+key);return {}
	ui.game.save_path="/private/tmp/pixelfx-preview-only/never-written.json"
	ui.game.slot_directory="/private/tmp/pixelfx-preview-only/slots"
	if not ui.game.start_battle(stage):errors.append("Stage start failed: "+key);return {}
	ui.game.story_events.clear();ui.game.flags.erase("active_plot")
	ui.view="combat";ui.ui_mode="inspect";ui.busy=true;ui.batch_running=false;ui.instant_mode=false;ui.animation_speed=1.
	ui.phase_time=0;ui.notice_time=0;ui.held_direction=Vector2i.ZERO;ui._clear_menu()
	ui.mechanical_target_confirmed=false;ui.mechanical_target_part=""
	ui.combat_hit_time=0;ui.combat_hit_id="";ui.combat_message="";ui.combat_shake=0;ui.combat_wait_accumulated=0
	var enemy=ui.game.find_unit("F25_pseudo_titan_1" if stage==205 else "F21_water_monkey_1")
	var hero=ui.game.find_unit("eileen")
	hero.hp=hero.max_hp;enemy.hp=enemy.max_hp
	var distance=3 if key=="water" else 1
	enemy.position=[18,9];hero.position=[18-distance,9]
	var actor=enemy if key=="water" else hero
	var target=hero if key=="water" else enemy
	if key!="water":hero.weapon_index=0;hero.item_id=0
	var part=""
	if key=="cannon-break" or key=="core-break":
		part=M.part_key(enemy);enemy.parts[part].hp=1
	var plan={}
	for seed in range(100):
		ui.game.rng_state=seed
		plan=ui.game.plan_combat(actor.id,target.id,part)
		if not plan.is_empty() and not plan.events.is_empty() and bool(plan.events[0].hit) and not bool(plan.events[0].critical):break
	if plan.is_empty() or plan.events.is_empty():errors.append("No plan: "+key);return {}
	var event=plan.events[0]
	if not event.hit or event.critical:errors.append("Expected a normal hit: "+key)
	ui.combat=plan;ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_hp.clear();ui.combat_fades.clear()
	for id in [str(plan.attacker),str(plan.defender)]:
		var u=ui.game.find_unit(id)
		ui.combat_poses[id]=int(ui.battle_animation.sprite(u).sequences.idle[0]);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_hp[id]=int(u.hp);ui.combat_fades[id]=1.
	var selected=ui.battle_animation.selection(event)
	if selected.get("kind","")!="source":errors.append("No source timeline: "+key);return {}
	return {"event":event,"variant":str(selected.key),"source_frames":selected.variant.frames.size(),"contact_tick":int(selected.variant.contact_tick),"native_fps":float(selected.variant.get("native_fps",60.0988)),"actor":actor.duplicate(true),"target":target.duplicate(true)}
func do_play(event:Dictionary):
	playing=true
	await ui.battle_animation.play(event)
	playing=false
func capture(key:String):
	var job=fixture(key)
	if job.is_empty():return
	phone._sync_controls();phone.set_process(false);ui.set_process(false);ui.set_physics_process(false)
	ui.queue_redraw();phone.queue_redraw()
	await process_frame;await RenderingServer.frame_post_draw
	var images=[];var frames=[]
	var first=vp.get_texture().get_image();first.resize(592,240,Image.INTERPOLATE_NEAREST)
	images.append(first);frames.append({"t":0.,"contact":false,"tick":-1})
	var start=Time.get_ticks_usec();var contact_time=-1.;var last=start
	do_play(job.event)
	while playing:
		await process_frame
		var now=Time.get_ticks_usec();var dt=float(now-last)/1000000.;last=now
		ui.elapsed+=dt;ui.combat_hit_time=maxf(0.,ui.combat_hit_time-dt);ui.queue_redraw();phone.queue_redraw()
		await RenderingServer.frame_post_draw
		var t=float(Time.get_ticks_usec()-start)/1000000.+.4
		var contacted=ui.battle_animation.contact_calls>0
		if contacted and contact_time<0:contact_time=t
		var img=vp.get_texture().get_image();img.resize(592,240,Image.INTERPOLATE_NEAREST);images.append(img)
		frames.append({"t":t,"contact":contacted,"tick":ui.battle_animation.active_tick,"message":ui.combat_message})
		if t>18:errors.append("Capture timeout: "+key);break
	var duration=float(frames[-1].t)+.65
	if ui.battle_animation.contact_calls!=1:errors.append("Expected one contact: "+key)
	for e in ui.layout_errors+phone.layout_errors:
		if not errors.has(str(e)):errors.append(str(e))
	var dir=OUT+key+"/";DirAccess.make_dir_recursive_absolute(dir)
	for i in range(images.size()):images[i].save_png(dir+"%04d.png"%i)
	var a=ui.battle_animation.origin(ui.game.find_unit(str(job.event.attacker)),ui.combat)
	var b=ui.battle_animation.origin(ui.game.find_unit(str(job.event.defender)),ui.combat)
	var off=ui._canvas_offset()
	var phone_offset=phone.game_rect.position/2.
	var report={"key":key,"duration":duration,"frames":frames,"contact_time":contact_time,"contact_calls":ui.battle_animation.contact_calls,"source":job,"phone_size":[592,240],"game_rect":[phone_offset.x,phone_offset.y,phone.game_rect.size.x/2.,phone.game_rect.size.y/2.],"canvas_offset":[off.x,off.y],"actor_origin":[a.x+off.x+phone_offset.x,a.y+off.y+phone_offset.y],"target_origin":[b.x+off.x+phone_offset.x,b.y+off.y+phone_offset.y],"layout_errors":ui.layout_errors.duplicate(),"final_target":ui.game.find_unit(str(job.event.defender)).duplicate(true)}
	var f=FileAccess.open(dir+"capture.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	records.append({"key":key,"frames":frames.size(),"duration":duration,"contact_time":contact_time,"contact_calls":ui.battle_animation.contact_calls,"variant":job.variant})
	print("PIXELFX_CAPTURE ",JSON.stringify(records[-1]))
func run():
	DirAccess.make_dir_recursive_absolute(OUT)
	vp=SubViewport.new();vp.size=Vector2i(1184,480);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(0,0,1184,480);phone.journal_directory_override="/private/tmp/pixelfx-preview-only/slots";vp.add_child(phone)
	await process_frame;ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);phone.set_process(false);ui.audio.stop_all()
	for key in ["hit","cannon-break","core-break","water"]:await capture(key)
	var f=FileAccess.open(OUT+"summary.json",FileAccess.WRITE);f.store_string(JSON.stringify({"guard":true,"passed":errors.is_empty(),"errors":errors,"records":records,"scope":"Current Godot production phone renderer, actual battle_animation.play and contact/reaction controller, controlled saved-state fixtures; no device recording and no runtime source changes."},"  "));f.close()
	ui.audio.stop_all();phone.queue_free();await process_frame;vp.queue_free();await process_frame
	print("PIXELFX_ERRORS ",errors);quit(0 if errors.is_empty() else 1)
