extends SceneTree
## Preview-only native replay. Reads the frozen capture's time and production draw functions.
const W=592
const H=240
const FRAMES=16
const COLS=4
const HUD=Rect2i(191,128,256,112)
var views:Array=[]
var phones:Array=[]
var uis:Array=[]
var records:Array=[]
var errors:Array=[]

func _initialize()->void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":
		push_error("Background guard required");quit(1);return
	call_deferred("run")

func setup(item:Dictionary, path:String)->bool:
	var j:Dictionary=item.job
	for ui in uis:
		ui.battle_animation.reset()
		ui.audio.stop_all()
		ui.game.units=[j.actor.duplicate(true),j.target.duplicate(true)]
		ui.game.story_events.clear()
		ui.game.flags.erase("active_plot")
		ui.view="combat";ui.ui_mode="inspect";ui.busy=true
		ui.instant_mode=false;ui.animation_speed=1.;ui.touch_fast_forward=false
		ui.phase_time=0.;ui.notice_time=0.;ui.held_direction=Vector2i.ZERO;ui._clear_menu()
		ui.combat=j.exchange.duplicate(true)
		ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear()
		ui.combat_hit_id="";ui.combat_message="";ui.combat_hit_time=0.;ui.combat_shake=0.;ui.elapsed=0.
		ui.battle_animation.active_event=j.event.duplicate(true)
		for u in ui.game.units:
			var id:String=str(u.id)
			ui.combat_hp[id]=int(u.hp);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_fades[id]=1.
			ui.combat_poses[id]=int(ui.battle_animation.sprite(u).sequences.idle[0])
		ui.layout_errors.clear()
	for ui in uis.slice(0,2):
		if not ui.battle_animation.cinema.prepare(j.event):
			errors.append("Cannot prepare "+str(item.key));return false
		if str(ui.battle_animation.cinema.spec.key)!=str(j.program):
			errors.append("Program changed "+str(item.key));return false
	return true

func filtered(p:Dictionary, data:Dictionary, remove_fx:bool, remove_hud:bool, sword:bool)->Dictionary:
	var out:Dictionary=p.duplicate(false)
	var frames:Array=[]
	for n in range(p.frames.size()):
		var src:Array=p.frames[n]
		var keep:Array=[]
		for i in range(src.size()):
			var op:Array=src[i]
			var kind:int=int(op[0])
			if remove_hud and kind in [3,4]:continue
			if remove_fx and kind==1:
				var art:String=str(data.images[int(op[1])].get("source",""))
				var actor:bool=art.begins_with("assets/") and ("hunapu-" in art or "eileen-" in art)
				if "spell-" in art or "fire-flight-" in art or "/impact-" in art or (sword and actor):continue
			if remove_fx and kind==0 and i>0:
				var wide:bool=float(op[3])>=628. and float(op[4])>=345.
				if sword and float(n)/float(p.fps)>=2.65:
					var top:float=float(op[2])
					if wide or (top>=39. and top<316.):continue
				elif not sword and float(n)/float(p.fps)>=2. and float(op[3])==640. and float(op[4])==360.:
					continue
			keep.append(op)
		frames.append(keep)
	out.frames=frames
	return out

func write_tiles(images:Array,rect:Rect2i,dir:String,stem:String)->Array:
	var paths:Array=[]
	for start in range(0,images.size(),FRAMES):
		var count:int=mini(FRAMES,images.size()-start)
		var atlas:Image=Image.create(rect.size.x*COLS,rect.size.y*ceili(float(count)/COLS),false,Image.FORMAT_RGBA8)
		for i in range(count):
			var tile:Image=images[start+i]
			atlas.blit_rect(tile,Rect2i(Vector2i.ZERO,rect.size),Vector2i(i%COLS*rect.size.x,i/COLS*rect.size.y))
		var name:String="%s-%03d.png"%[stem,paths.size()]
		if atlas.save_png(dir+name)!=OK:errors.append("Cannot write "+dir+name)
		paths.append(name)
	return paths

func sample(view:SubViewport,rect:Rect2i)->Image:
	var im:Image=view.get_texture().get_image()
	im.resize(W,H,Image.INTERPOLATE_NEAREST);im.convert(Image.FORMAT_RGBA8)
	return im.get_region(rect)

func draw_case(item:Dictionary,out:String)->void:
	var dir:String=out+str(item.key)+"/"
	var hud_only:bool=OS.get_environment("PIXELFX_HUD_ONLY")=="1"
	var prior:Dictionary={}
	if FileAccess.file_exists(dir+"native.json"):
		if not hud_only:return
		prior=JSON.parse_string(FileAccess.get_file_as_string(dir+"native.json"))
	DirAccess.make_dir_recursive_absolute(dir)
	if not setup(item,dir):return
	var rect:=Rect2i(int(item.rect[0]),int(item.rect[1]),int(item.rect[2]),int(item.rect[3]))
	var cinema=uis[0].battle_animation.cinema
	var specdata:Dictionary=cinema.data()
	var program:Dictionary=cinema.program
	var plain:Array=[program,filtered(program,specdata,false,true,bool(item.sword))]
	var clean:Array=[filtered(program,specdata,true,false,bool(item.sword)),filtered(program,specdata,true,true,bool(item.sword))]
	var with_labels:Array=[];var without:Array=[]
	views[2].render_target_update_mode=SubViewport.UPDATE_DISABLED
	if prior.is_empty():
		for req in item.requests:
			for i in range(2):
				var ui=uis[i];var c=ui.battle_animation.cinema
				c.elapsed=float(req.elapsed);ui.elapsed=float(req.elapsed)
				c.program=(clean if req.strip else plain)[i]
				ui.combat_hp=req.hp.duplicate(true)
				ui.queue_redraw()
			await RenderingServer.frame_post_draw
			with_labels.append(sample(views[0],rect));without.append(sample(views[1],rect))
	views[0].render_target_update_mode=SubViewport.UPDATE_DISABLED
	views[1].render_target_update_mode=SubViewport.UPDATE_DISABLED
	views[2].render_target_update_mode=SubViewport.UPDATE_ALWAYS
	var hud_ui=uis[2]
	var event:Dictionary=item.job.event
	var j:Dictionary=item.job
	# Cinematic capture puts both test units on one map cell. For the ordinary
	# HUD only, restore the declared attack distance so its forecast is native.
	for u in hud_ui.game.units:
		if str(u.id)==str(event.defender):u.position=[5-int(event.distance),5]
	var reaction=11.0/60.0988
	var g:Dictionary=hud_ui.battle_animation.sprite(hud_ui.game.find_unit(str(event.defender)))
	var hit_key:String=str(g.get("reviewed_reactions",{}).get("hit",""))
	if not hit_key.is_empty():
		var variant:Dictionary=hud_ui.battle_animation.Reviewed.variant(hit_key)
		if not variant.is_empty():reaction=float(variant.frames.size())/float(variant.native_fps)
	var hud_frames:Array=[]
	for hp in item.casterHp:
		for target_hp in range(int(event.hp_after),int(event.hp_before)+1):
			hud_ui.combat_hp[str(event.attacker)]=int(hp)
			hud_ui.combat_hp[str(event.defender)]=target_hp
			hud_ui.queue_redraw()
			await RenderingServer.frame_post_draw
			hud_frames.append(sample(views[2],HUD))
	views[0].render_target_update_mode=SubViewport.UPDATE_ALWAYS
	views[1].render_target_update_mode=SubViewport.UPDATE_ALWAYS
	for i in range(uis.size()):
		if not uis[i].layout_errors.is_empty() or not phones[i].layout_errors.is_empty():
			errors.append(str(item.key)+" layout: "+str(uis[i].layout_errors)+str(phones[i].layout_errors))
	var r:Dictionary={"rect":item.rect,"with":prior["with"] if not prior.is_empty() else write_tiles(with_labels,rect,dir,"with"),
		"without":prior["without"] if not prior.is_empty() else write_tiles(without,rect,dir,"without"),
		"hud":write_tiles(hud_frames,HUD,dir,"hud-native"),
		"frames":int(prior.frames) if not prior.is_empty() else with_labels.size(),"hud_count":hud_frames.size(),"hud_size":[256,112],
		"atlas_frames":FRAMES,"atlas_cols":COLS,"reaction":reaction,
		"rate":60.0988,"target_min":int(event.hp_after),"target_max":int(event.hp_before)}
	var file:FileAccess=FileAccess.open(dir+"native.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(r));file.close();records.append(item.key)
	print("CINEMA ",item.key," ",r.frames," HUD ",hud_frames.size()," reaction ",reaction)

func run()->void:
	Engine.max_fps=120
	var input:String=OS.get_environment("PIXELFX_INVENTORY")
	var out:String=OS.get_environment("PIXELFX_CAPTURE_OUT")
	var jobs=JSON.parse_string(FileAccess.get_file_as_string(input))
	if jobs==null or out.is_empty():quit(1);return
	for i in range(3):
		var view:=SubViewport.new();view.size=Vector2i(1184,480)
		view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
		root.add_child(view)
		var phone=load("res://scenes/phone.tscn").instantiate()
		phone.safe_area_override=Rect2(0,0,1184,480)
		phone.journal_directory_override="/private/tmp/pixelfx-r5-"+str(OS.get_process_id())+"/slots-"+str(i)
		view.add_child(phone);views.append(view);phones.append(phone)
	await process_frame
	for phone in phones:
		var ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);phone.set_process(false)
		ui.audio.stop_all();ui._clear_menu();ui.game.new_game()
		ui.game.save_path="/private/tmp/pixelfx-r5-preview-never-save.json"
		ui.game.slot_directory="/private/tmp/pixelfx-r5-preview-slots"
		uis.append(ui)
	for item in jobs:await draw_case(item,out)
	for view in views:view.queue_free()
	await process_frame
	print("BATCH ",JSON.stringify({"captured":records,"errors":errors}))
	quit(0 if errors.is_empty() else 1)
