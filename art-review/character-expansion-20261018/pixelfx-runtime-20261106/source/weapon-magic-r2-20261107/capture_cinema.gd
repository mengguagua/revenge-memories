extends SceneTree
## Preview-only: calls the unchanged production controller in an isolated snapshot.
const ROOT="/Users/gcc/gaocc/project/revenge-memories/art-review/character-expansion-20261018/pixelfx-runtime-20261106/source/weapon-magic-r2-20261107/"
const W=592
const H=240
const CELLS=16
var vp;var phone;var ui;var clean_vp;var clean_phone;var clean_ui;var actor_vp;var actor_canvas
var playing=false;var errors=[];var records=[];var current={}
var cinema_clean_cache={}

class ActorCanvas extends Node2D:
	var ui;var actor_id=""
	func _draw():
		if ui==null or ui.combat.is_empty():return
		var a=ui.battle_animation;var u=ui.game.find_unit(actor_id)
		if u.is_empty():return
		var g=a.sprite(u);var frame=int(ui.combat_poses.get(actor_id,g.sequences.idle[0]));var left=a._left(u,ui.combat)
		var flip=a.Innate.horizontal_flip(g,left,bool(a.flips.get(actor_id,g.get("idle_flip",false)))) if a.Rules.Body.is_body(u) else left!=bool(a.flips.get(actor_id,g.get("idle_flip",false)))
		var at=a.origin(u,ui.combat)+a._vec(ui.combat_offsets.get(actor_id,Vector2.ZERO))-a._vec(g.anchor)
		if flip and frame<int(g.get("source_oam_frame_count",0)):at+=a._vec(g.get("oam_flip_origin_offset",[0,0]))
		var region=a.clipped_region(g,frame,at,flip)
		if region.is_empty():return
		var dest:Rect2=region.destination
		if flip:dest.size.x=-dest.size.x
		var shade=float(a.pose_tint.get(actor_id,1.));var color=Color(shade,shade,shade,float(ui.combat_fades.get(actor_id,1.))*float(a.pose_alpha.get(actor_id,1.))*float(a.target_alpha.get(actor_id,1.)))
		if str(ui.combat_hit_id)==actor_id and float(ui.combat_hit_time)>0 and int(float(ui.elapsed)*30.)%2==0:color=Color(.35,.35,.35,color.a)
		draw_set_transform(Vector2(191,0));draw_texture_rect_region(ui._tex(str(g.path)),dest,region.source,color)

func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":push_error("Background guard required");quit(1);return
	call_deferred("run")

func setup(job:Dictionary):
	current=job.duplicate(true);ui.battle_animation.reset();ui.audio.stop_all();cinema_clean_cache.clear()
	ui.game.units=[current.actor,current.target];ui.game.story_events.clear();ui.game.flags.erase("active_plot")
	ui.view="combat";ui.ui_mode="inspect";ui.busy=true;ui.batch_running=false;ui.instant_mode=false;ui.animation_speed=1.;ui.touch_fast_forward=false
	ui.phase_time=0.;ui.notice_time=0.;ui.held_direction=Vector2i.ZERO;ui._clear_menu()
	ui.combat=current.exchange.duplicate(true);ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_hp.clear();ui.combat_fades.clear()
	ui.combat_hit_time=0.;ui.combat_hit_id="";ui.combat_message="";ui.combat_shake=0.;ui.combat_wait_accumulated=0.;ui.elapsed=0.
	ui.battle_animation.active_event=current.event.duplicate(true)
	for u in ui.game.units:
		var id=str(u.id);var g=ui.battle_animation.sprite(u)
		ui.combat_poses[id]=int(g.sequences.idle[0]);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_hp[id]=int(u.hp);ui.combat_fades[id]=1.
	actor_canvas.ui=ui;actor_canvas.actor_id=str(current.event.attacker)
	var selected=ui.battle_animation.selection(current.event)
	if str(selected.get("key",""))!=str(current.program):errors.append("Selection changed: "+str(current.id))
	ui.layout_errors.clear();phone.layout_errors.clear();clean_ui.layout_errors.clear();clean_phone.layout_errors.clear()

func sync_layers():
	clean_ui.game=ui.game
	for field in ["view","ui_mode","busy","elapsed","phase_time","notice_time","combat","combat_poses","combat_offsets","combat_hp","combat_fades","combat_hit_id","combat_hit_time","combat_message","combat_shake"]:clean_ui.set(field,ui.get(field))
	var a=ui.battle_animation;var b=clean_ui.battle_animation
	for field in ["flips","target_alpha","pose_alpha","pose_tint","active_variant","active_tick","active_event"]:b.set(field,a.get(field))
	b.effects=[]
	var ca=a.cinema;var cb=b.cinema
	for field in ["active","elapsed","spec","event","program","audit","background_key","target_texture","_textures","_target_flip","_target_name","_target_max_hp"]:cb.set(field,ca.get(field))
	if ca.active:
		if cinema_clean_cache.is_empty():
			cinema_clean_cache=ca.program.duplicate(false);var cleaned=[];var original_images=ca.data().images
			for n in range(ca.program.frames.size()):
				var ops=ca.program.frames[n]
				var keep=[]
				for index in range(ops.size()):
					var op=ops[index]
					if int(op[0])==1:
						var src=str(original_images[int(op[1])].get("source",""))
						if "spell-" in src or "fire-flight-" in src or "/impact-" in src:continue
					if int(op[0])==0 and index>0 and float(op[3])==640. and float(op[4])==360. and float(n)/float(ca.program.fps)>=2.:continue
					keep.append(op)
				cleaned.append(keep)
			cinema_clean_cache.frames=cleaned
		cb.program=cinema_clean_cache
	phone._sync_controls();clean_phone._sync_controls();ui.queue_redraw();phone.queue_redraw();clean_ui.queue_redraw();clean_phone.queue_redraw();actor_canvas.queue_redraw()

func frame_meta(t:float)->Dictionary:
	var a=ui.battle_animation;var points=[]
	for id in [str(current.event.attacker),str(current.event.defender)]:
		var p=a.origin(ui.game.find_unit(id),ui.combat)+a._vec(ui.combat_offsets.get(id,Vector2.ZERO))+Vector2(191,0);points.append([p.x,p.y])
	var fx=[]
	for e in a.effects:
		var g=a.CampaignEffects.graphic(str(e.sprite),a.active_variant)
		if g.is_empty():g=a._source_metadata().sprites.get(str(e.sprite),{})
		if g.is_empty():continue
		var point=a.effect_position(e);var role=str(g.get("campaign_anchor_role",""))
		if not role.is_empty():
			var owner=ui.game.find_unit(str(current.event.defender if role=="defender" else current.event.attacker))
			point=a.origin(owner,ui.combat)+(Vector2(0,-52) if role=="attacker_charge" else Vector2.ZERO)
		var at=point-a._vec(g.anchor)
		if bool(e.flip):at+=a._vec(g.get("flip_origin_offset",[0,0]))
		var density=float(g.get("native_density",1));var size=a._vec(g.logical_frame_size) if g.has("logical_frame_size") else a._vec(g.frame_size)/density
		fx.append({"sprite":e.sprite,"point":[point.x+191,point.y],"rect":[roundf(at.x)+191,roundf(at.y),size.x,size.y],"flip":e.flip,"path":g.path,"role":role,"bound":e.get("bind_target",false)})
	var row={"t":t,"tick":a.active_tick,"contact":a.contact_calls>0,"message":ui.combat_message,"actor":points[0],"target":points[1],"effects":fx,"hp":ui.combat_hp.duplicate(true),"target_fade":float(ui.combat_fades.get(str(current.event.defender),1.))}
	if a.cinema.active:
		var c=a.cinema;var target_point=[];var actor_point=[];var cinema_fx=[];var frame=clampi(floori(c.elapsed*float(c.program.fps)),0,c.program.frames.size()-1)
		for op in c.program.frames[frame]:
			if int(op[0])==2:target_point=[op[1],op[2]]
			if int(op[0])==1:
				var src=str(c.data().images[int(op[1])].get("source",""))
				if "eileen-cast-" in src:actor_point=[float(op[2])+float(op[4])*.45,float(op[3])+float(op[5])]
				if "spell-" in src or "fire-flight-" in src:cinema_fx.append({"source":src,"rect":[op[2],op[3],op[4],op[5]]})
		var show=c._ease((c.elapsed-.08)/.29)*(1.-c._ease((c.elapsed-(c.duration()-.35))/.31));var size=ui.get_viewport_rect().size;var scale=minf((size.x-16)/640.,(size.y-16)/360.)*(.91+.09*show);var origin=(size-Vector2(640,360)*scale)/2.+Vector2(116,0)
		row.cinema={"elapsed":c.elapsed,"target":target_point,"actor":actor_point,"effects":cinema_fx,"scale":scale,"origin":[origin.x,origin.y],"show":show,"hit":c.spec.hit}
	return row

func do_play(event:Dictionary):
	playing=true;await ui.battle_animation.play(event);playing=false

func save_atlases(images:Array,dir:String,prefix:String)->Array:
	var paths=[]
	for start in range(0,images.size(),CELLS):
		var count=mini(CELLS,images.size()-start);var rows=ceili(float(count)/4.);var atlas=Image.create(W*4,H*rows,false,Image.FORMAT_RGBA8);atlas.fill(Color(0,0,0,0))
		for k in range(count):atlas.blit_rect(images[start+k],Rect2i(0,0,W,H),Vector2i((k%4)*W,(k/4)*H))
		var name=prefix+"-%03d.png"%(start/CELLS);var error=atlas.save_png(dir+name)
		if error!=OK:errors.append("PNG write failed "+dir+name)
		paths.append(name)
	return paths

func capture(job:Dictionary,out:String):
	var dir=out+str(job.id)+"/"
	if FileAccess.file_exists(dir+"capture.json"):print("SKIP ",job.id);return
	setup(job);sync_layers();await process_frame;await RenderingServer.frame_post_draw
	var images=[[],[],[]];var seen={};var frames=[];var last_data=[PackedByteArray(),PackedByteArray(),PackedByteArray()];var last_id=-1
	var start=Time.get_ticks_usec();var last=start;var contact=-1.;var first=true
	while first or playing:
		var t=0. if first else float(Time.get_ticks_usec()-start)/1000000.+.4
		var meta=frame_meta(t);var rendered=[];var data=[];var keys=[]
		for viewport in [vp,clean_vp,actor_vp]:
			var im=viewport.get_texture().get_image();im.resize(W,H,Image.INTERPOLATE_NEAREST);im.convert(Image.FORMAT_RGBA8);rendered.append(im);var bytes=im.get_data();data.append(bytes);keys.append(str(hash(bytes)))
		var identity="|".join(keys);var id=-1
		if data[0]==last_data[0] and data[1]==last_data[1] and data[2]==last_data[2]:id=last_id
		elif seen.has(identity):
			id=int(seen[identity])
			for k in range(3):
				if images[k][id].get_data()!=data[k]:errors.append("Hash collision "+str(job.id));id=-1;break
		if id<0:
			id=images[0].size();seen[identity]=id
			for k in range(3):images[k].append(rendered[k])
		last_data=data;last_id=id;meta.image=id;frames.append(meta)
		if bool(meta.contact) and contact<0:contact=t
		if first:first=false;start=Time.get_ticks_usec();last=start;do_play(current.event.duplicate(true))
		if t>32.:errors.append("Timeout "+str(job.id));break
		if not playing:break
		await process_frame
		var now=Time.get_ticks_usec();var dt=float(now-last)/1000000.;last=now;ui.elapsed+=dt;ui.combat_hit_time=maxf(0.,ui.combat_hit_time-dt)
		sync_layers();await RenderingServer.frame_post_draw
	# Preserve the final controller state even when the coroutine ended between frames.
	sync_layers();await process_frame;await RenderingServer.frame_post_draw
	var final_meta=frame_meta(float(Time.get_ticks_usec()-start)/1000000.+.4);var final_id=images[0].size()
	for k in range(3):
		var im=[vp,clean_vp,actor_vp][k].get_texture().get_image();im.resize(W,H,Image.INTERPOLATE_NEAREST);im.convert(Image.FORMAT_RGBA8);images[k].append(im)
	final_meta.image=final_id;frames.append(final_meta)
	if ui.battle_animation.contact_calls!=1:errors.append("Contact count "+str(job.id)+" "+str(ui.battle_animation.contact_calls))
	var layout=[]
	for e in ui.layout_errors+phone.layout_errors+clean_ui.layout_errors+clean_phone.layout_errors:
		if not layout.has(str(e)):layout.append(str(e))
	DirAccess.make_dir_recursive_absolute(dir)
	var atlases={}
	for k in range(3):atlases[["current","clean","actor"][k]]=save_atlases(images[k],dir,["current","clean","actor"][k])
	var report={"id":job.id,"duration":float(frames[-1].t)+.65,"frames":frames,"contact_time":contact,"contact_calls":ui.battle_animation.contact_calls,"job":job,"atlases":atlases,"unique_frames":images[0].size(),"atlas_frames":CELLS,"atlas_cols":4,"size":[W,H],"layout_errors":layout,"missing_animations":ui.battle_animation.missing_animations.duplicate(),"guard":true,"clean_cinema_version":2}
	var f=FileAccess.open(dir+"capture.json",FileAccess.WRITE);f.store_string(JSON.stringify(report));f.close()
	records.append({"id":job.id,"duration":report.duration,"frames":frames.size(),"unique":images[0].size(),"contact":contact,"layout_errors":layout.size()});print("CAPTURE ",JSON.stringify(records[-1]))

func run():
	Engine.max_fps=60
	var out=ROOT+"captures/";var inventory=ROOT+"inventory.json"
	if not OS.get_environment("PIXELFX_CAPTURE_OUT").is_empty():out=OS.get_environment("PIXELFX_CAPTURE_OUT")
	if not OS.get_environment("PIXELFX_INVENTORY").is_empty():inventory=OS.get_environment("PIXELFX_INVENTORY")
	DirAccess.make_dir_recursive_absolute(out)
	for k in range(2):
		var viewport=SubViewport.new();viewport.size=Vector2i(1184,480);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
		var p=load("res://scenes/phone.tscn").instantiate();p.safe_area_override=Rect2(0,0,1184,480);p.journal_directory_override="/private/tmp/pixelfx-full-"+str(OS.get_process_id())+"/slots-"+str(k);viewport.add_child(p)
		if k==0:vp=viewport;phone=p
		else:clean_vp=viewport;clean_phone=p
	actor_vp=SubViewport.new();actor_vp.size=Vector2i(1184,480);actor_vp.size_2d_override=Vector2i(W,H);actor_vp.size_2d_override_stretch=true;actor_vp.transparent_bg=true;actor_vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(actor_vp)
	actor_canvas=ActorCanvas.new();actor_canvas.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;actor_vp.add_child(actor_canvas)
	await process_frame;ui=phone.game_ui;clean_ui=clean_phone.game_ui
	for u in [ui,clean_ui]:u.set_process(false);u.set_physics_process(false);u.audio.stop_all();u._clear_menu()
	phone.set_process(false);clean_phone.set_process(false);ui.game.new_game();ui.game.save_path="/private/tmp/pixelfx-full-preview-never-save.json";ui.game.slot_directory="/private/tmp/pixelfx-full-preview-slots"
	var jobs=JSON.parse_string(FileAccess.get_file_as_string(inventory)).jobs
	var begin=int(OS.get_environment("PIXELFX_BATCH_FROM"));var count=jobs.size() if OS.get_environment("PIXELFX_BATCH_COUNT").is_empty() else int(OS.get_environment("PIXELFX_BATCH_COUNT"))
	for job in jobs.slice(begin,mini(jobs.size(),begin+count)):await capture(job,out)
	var f=FileAccess.open(out+"batch-"+str(begin)+"-"+str(count)+".json",FileAccess.WRITE);f.store_string(JSON.stringify({"guard":true,"errors":errors,"records":records,"passed":errors.is_empty()},"  "));f.close()
	ui.audio.stop_all();clean_ui.audio.stop_all();phone.queue_free();clean_phone.queue_free();actor_canvas.queue_free();await process_frame
	vp.queue_free();clean_vp.queue_free();actor_vp.queue_free();await process_frame
	print("BATCH_ERRORS ",errors);quit(0 if errors.is_empty() else 1)
