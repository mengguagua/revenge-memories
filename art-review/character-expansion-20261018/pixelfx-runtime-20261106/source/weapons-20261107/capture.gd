extends "../capture.gd"
## Isolated production-renderer comparison. One controller drives all captured layers.
var clean_vp;var clean_phone;var clean_ui;var actor_vp;var actor_canvas
var active_key=""

class ActorCanvas extends Node2D:
	var ui
	func _draw():
		if ui==null or ui.combat.is_empty():return
		var anim=ui.battle_animation;var unit=ui.game.find_unit(str(ui.combat.attacker));var id=str(unit.id)
		var graphic=anim.sprite(unit);var frame=int(ui.combat_poses.get(id,graphic.sequences.idle[0]))
		var flip=anim._left(unit,ui.combat)!=bool(anim.flips.get(id,graphic.get("idle_flip",false)))
		var at=anim.origin(unit,ui.combat)+anim._vec(ui.combat_offsets.get(id,Vector2.ZERO))-anim._vec(graphic.anchor)
		if flip and frame<int(graphic.get("source_oam_frame_count",0)):at+=anim._vec(graphic.get("oam_flip_origin_offset",[0,0]))
		var region=anim.clipped_region(graphic,frame,at,flip)
		if region.is_empty():return
		var dest:Rect2=region.destination
		if flip:dest.size.x=-dest.size.x
		var shade=float(anim.pose_tint.get(id,1.));var color=Color(shade,shade,shade,float(ui.combat_fades.get(id,1.))*float(anim.pose_alpha.get(id,1.)))
		draw_set_transform(Vector2(191,0))
		draw_texture_rect_region(ui._tex(str(graphic.path)),dest,region.source,color)

func fixture(key:String)->Dictionary:
	if super.fixture("hit").is_empty():return {}
	ui.battle_animation.reset();ui.combat.clear()
	var actor=ui.game.find_unit("F21_e6" if key=="archery" else "carlo")
	var target=ui.game.find_unit("eileen" if key=="archery" else "F21_water_monkey_1")
	var distance=3 if key=="archery" else 1
	actor.position=[18,9];target.position=[18-distance,9];actor.hp=actor.max_hp;target.hp=target.max_hp
	var plan={}
	for seed in range(100):
		ui.game.rng_state=seed;plan=ui.game.plan_combat(actor.id,target.id)
		if not plan.is_empty() and bool(plan.events[0].hit) and not bool(plan.events[0].critical):break
	if plan.is_empty():errors.append("Missing weapon plan "+key);return {}
	var event=plan.events[0];ui.combat=plan
	ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_hp.clear();ui.combat_fades.clear()
	for id in [str(actor.id),str(target.id)]:
		var u=ui.game.find_unit(id);ui.combat_poses[id]=int(ui.battle_animation.sprite(u).sequences.idle[0]);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_hp[id]=int(u.hp);ui.combat_fades[id]=1.
	var chosen=ui.battle_animation.selection(event)
	if chosen.get("kind","")!="source":errors.append("Missing source animation "+key);return {}
	print("WEAPON_PLAN ",key," ",JSON.stringify(event)," variant=",chosen.key)
	return {"event":event,"variant":str(chosen.key),"source_frames":chosen.variant.frames.size(),"contact_tick":int(chosen.variant.contact_tick),"native_fps":float(chosen.variant.get("native_fps",60.0988)),"actor":actor.duplicate(true),"target":target.duplicate(true)}

func sync_layers():
	clean_ui.game=ui.game
	for field in ["view","ui_mode","busy","elapsed","phase_time","notice_time","combat","combat_poses","combat_offsets","combat_hp","combat_fades","combat_hit_id","combat_hit_time","combat_message","combat_shake"]:clean_ui.set(field,ui.get(field))
	var a=ui.battle_animation;var b=clean_ui.battle_animation
	for field in ["flips","target_alpha","pose_alpha","pose_tint","active_variant","active_tick","active_event"]:b.set(field,a.get(field))
	b.effects=[] if active_key=="archery" else a.effects
	clean_phone._sync_controls();clean_ui.queue_redraw();clean_phone.queue_redraw();actor_canvas.queue_redraw()

func frame_meta(t:float)->Dictionary:
	var anim=ui.battle_animation;var actor=ui.game.find_unit(str(ui.combat.attacker));var p=anim.origin(actor,ui.combat)+anim._vec(ui.combat_offsets.get(str(actor.id),Vector2.ZERO))+Vector2(191,0)
	var fx=[]
	for e in anim.effects:
		var g=anim.CampaignEffects.graphic(str(e.sprite),anim.active_variant)
		if g.is_empty():g=anim._source_metadata().sprites.get(str(e.sprite),{})
		var pt=anim.effect_position(e);var at=pt-anim._vec(g.anchor)
		if e.flip:at+=anim._vec(g.get("flip_origin_offset",[0,0]))
		var density=float(g.get("native_density",1));var size=anim._vec(g.logical_frame_size) if g.has("logical_frame_size") else anim._vec(g.frame_size)/density
		fx.append({"sprite":e.sprite,"point":[pt.x+191,pt.y],"rect":[roundf(at.x)+191,roundf(at.y),size.x,size.y],"flip":e.flip,"path":g.path})
	return {"t":t,"contact":anim.contact_calls>0,"tick":anim.active_tick,"message":ui.combat_message,"actor_position":[p.x,p.y],"effects":fx}

func capture(key:String):
	active_key=key;var job=fixture(key)
	if job.is_empty():return
	actor_canvas.ui=ui;phone._sync_controls();sync_layers();ui.queue_redraw();phone.queue_redraw()
	await process_frame;await RenderingServer.frame_post_draw
	var images=[];var clean_images=[];var actor_images=[];var frames=[]
	for pair in [[vp,images],[clean_vp,clean_images],[actor_vp,actor_images]]:
		var im=pair[0].get_texture().get_image();im.resize(592,240,Image.INTERPOLATE_NEAREST);pair[1].append(im)
	frames.append(frame_meta(0.))
	var start=Time.get_ticks_usec();var last=start;var contact_time=-1.
	do_play(job.event)
	while playing:
		await process_frame
		var now=Time.get_ticks_usec();var dt=float(now-last)/1000000.;last=now
		ui.elapsed+=dt;ui.combat_hit_time=maxf(0.,ui.combat_hit_time-dt);sync_layers();ui.queue_redraw();phone.queue_redraw()
		await RenderingServer.frame_post_draw
		var t=float(Time.get_ticks_usec()-start)/1000000.+.4
		if ui.battle_animation.contact_calls>0 and contact_time<0:contact_time=t
		for pair in [[vp,images],[clean_vp,clean_images],[actor_vp,actor_images]]:
			var im=pair[0].get_texture().get_image();im.resize(592,240,Image.INTERPOLATE_NEAREST);pair[1].append(im)
		frames.append(frame_meta(t))
		if t>16:errors.append("Weapon capture timeout "+key);break
	var dir=OUT+key+"/";DirAccess.make_dir_recursive_absolute(dir+"clean");DirAccess.make_dir_recursive_absolute(dir+"actor")
	for i in range(images.size()):
		images[i].save_png(dir+"%04d.png"%i);clean_images[i].save_png(dir+"clean/%04d.png"%i);actor_images[i].save_png(dir+"actor/%04d.png"%i)
	if ui.battle_animation.contact_calls!=1:errors.append("Weapon contact count "+key)
	for e in ui.layout_errors+clean_ui.layout_errors+phone.layout_errors:
		if not errors.has(str(e)):errors.append(str(e))
	var anim=ui.battle_animation;var a=anim.origin(ui.game.find_unit(str(job.event.attacker)),ui.combat)+Vector2(191,0);var b=anim.origin(ui.game.find_unit(str(job.event.defender)),ui.combat)+Vector2(191,0)
	var report={"key":key,"duration":float(frames[-1].t)+.65,"frames":frames,"contact_time":contact_time,"contact_calls":anim.contact_calls,"source":job,"phone_size":[592,240],"game_rect":[116,0,406,240],"canvas_offset":[75,0],"actor_origin":[a.x,a.y],"target_origin":[b.x,b.y],"layout_errors":ui.layout_errors.duplicate(),"final_target":ui.game.find_unit(str(job.event.defender)).duplicate(true),"layers":"Current production renderer plus synchronous clean effect layer and actual attacker-only layer."}
	var f=FileAccess.open(dir+"capture.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	records.append({"key":key,"frames":frames.size(),"duration":report.duration,"contact_time":contact_time,"contact_calls":anim.contact_calls,"variant":job.variant});print("WEAPON_CAPTURE ",JSON.stringify(records[-1]))

func run():
	vp=SubViewport.new();vp.size=Vector2i(1184,480);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(0,0,1184,480);phone.journal_directory_override="/private/tmp/pixelfx-weapons/slots";vp.add_child(phone)
	clean_vp=SubViewport.new();clean_vp.size=Vector2i(1184,480);clean_vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(clean_vp)
	clean_phone=load("res://scenes/phone.tscn").instantiate();clean_phone.safe_area_override=Rect2(0,0,1184,480);clean_phone.journal_directory_override="/private/tmp/pixelfx-weapons/clean-slots";clean_vp.add_child(clean_phone)
	actor_vp=SubViewport.new();actor_vp.size=Vector2i(1184,480);actor_vp.size_2d_override=Vector2i(592,240);actor_vp.size_2d_override_stretch=true;actor_vp.transparent_bg=true;actor_vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(actor_vp)
	actor_canvas=ActorCanvas.new();actor_canvas.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;actor_vp.add_child(actor_canvas)
	await process_frame;ui=phone.game_ui;clean_ui=clean_phone.game_ui
	for u in [ui,clean_ui]:u.set_process(false);u.set_physics_process(false);u.audio.stop_all();u._clear_menu()
	phone.set_process(false);clean_phone.set_process(false)
	for key in ["archery","dash-strike"]:await capture(key)
	var f=FileAccess.open(OUT+"weapons-summary.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"guard":true,"errors":errors,"records":records},"  "));f.close()
	ui.audio.stop_all();clean_ui.audio.stop_all();phone.queue_free();clean_phone.queue_free();actor_canvas.queue_free();await process_frame
	vp.queue_free();clean_vp.queue_free();actor_vp.queue_free();await process_frame
	print("WEAPON_ERRORS ",errors);quit(0 if errors.is_empty() else 1)
