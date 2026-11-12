extends "res://tests/ch2_environment_play.gd"
const OUTPUT="/private/tmp/map-ambient-20261112/"
const SOURCES="/Users/gcc/gaocc/project/revenge-memories/art-review/map-ambient-20261112/source/sources.json"
const FOCUS={"M11":[11,9],"M12":[21,8],"M13":[12,15],"S11":[15,8],"S12":[15,11],"M14":[15,17],"M15":[16,15],"F21":[15,16],"F22":[14,21],"F23":[9,20],"F24":[17,10],"F25":[12,15],"F26":[21,14],"S21":[15,18],"S22":[20,11]}
const LATE_FOCUS={"M31":[15,13],"M32":[16,13],"M33":[16,15],"F31":[12,18],"F32":[15,14],"F33":[17,13],"S31":[15,13],"S32":[16,13],"M41":[15,12],"M42":[16,15],"M43":[16,14],"M44":[16,14],"F41":[15,14],"F42":[17,14],"F43":[17,14],"F44":[17,15],"S41":[13,12],"S42":[15,14],"M51":[16,17],"M52":[25,13],"F51":[17,13],"F52":[18,16],"S51":[15,10],"J53":[19,16],"J54":[17,15]}
var capture_view
var phone
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")

func state_hash()->String:
	var state={}
	for key in ui.game.SAVE_FIELDS:state[key]=ui.game.get(key)
	state["map_tiles"]=ui.game.battle_data.map.tiles
	return JSON.stringify(state).sha256_text()

func run():
	var sources=State.read_json(SOURCES)
	var frames=int(OS.get_environment("AMBIENT_FRAMES"))
	if frames<1:frames=96
	var codes=OS.get_environment("AMBIENT_CODES").split(",") if not OS.get_environment("AMBIENT_CODES").is_empty() else sources.keys()
	var mode=OS.get_environment("AMBIENT_VIEW")
	if mode.is_empty():mode="map"
	capture_view=SubViewport.new()
	capture_view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(capture_view)
	var report=[]
	for code in codes:
		abort=false
		var folder=OUTPUT+mode+"/"+code+"/"
		for version in ["before","after"]:DirAccess.make_dir_recursive_absolute(folder+version)
		var source=str(sources[code])
		var hash=FileAccess.get_sha256(source)
		if mode=="phone":
			capture_view.size=Vector2i(1334,750)
			phone=load("res://scenes/phone.tscn").instantiate()
			phone.journal_directory_override=OUTPUT+"journals"
			capture_view.add_child(phone)
			await process_frame
			ui=phone.game_ui
		else:
			ui=load("res://scenes/main.tscn").instantiate()
			ui.game.slot_directory=OUTPUT+"journals"
			ui.game.save_path=OUTPUT+"working.json"
			capture_view.add_child(ui)
			await process_frame
		ui.instant_mode=true
		ui.game.save_path=source
		var loaded=ui.game.load_game()
		ui.game.save_path=OUTPUT+"working.json"
		var reentered=loaded
		if loaded and code!="M15":reentered=ui.game.retry_battle()
		if not reentered:
			push_error("Cannot use battle checkpoint "+code);quit(1);return
		ui._resume_journey()
		await settle()
		if abort or ui.view!="battle":
			push_error("Battle presentation is not ready "+code+" "+ui.view);quit(1);return
		ui.set_process(false)
		ui.set_physics_process(false)
		ui.ui_mode="whole_capture"
		ui.phase_time=0;ui.notice_time=0
		if mode=="map":
			capture_view.size=Vector2i(ui.game.battle_data.map.width*16+64,ui.game.battle_data.map.height*16+64)
		await process_frame
		var focus=FOCUS.get(code,LATE_FOCUS.get(code,[15,13]))
		ui._focus_battle(Vector2i(focus[0],focus[1]),true)
		var invariant=state_hash()
		var initial={}
		for key in ui.game.SAVE_FIELDS:initial[key]=ui.game.get(key).duplicate(true) if ui.game.get(key) is Array or ui.game.get(key) is Dictionary else ui.game.get(key)
		var render_us=0
		for frame in range(frames):
			ui.elapsed=2.0+float(frame)/12
			for version in ["before","after"]:
				ui.map_ambient.enabled=version=="after"
				ui.queue_redraw()
				var start=Time.get_ticks_usec()
				await process_frame
				await RenderingServer.frame_post_draw
				render_us+=Time.get_ticks_usec()-start
				var file=folder+version+"/%04d.png"%frame
				var error=capture_view.get_texture().get_image().save_png(file)
				if error!=OK or not ui.layout_errors.is_empty():
					push_error("Capture/layout failure "+code+" "+str(ui.layout_errors));quit(1);return
			if frame%24==0:print("AMBIENT_FRAME ",mode," ",code," ",frame,"/",frames)
		var unchanged=invariant==state_hash()
		report.append({"code":code,"frames":frames,"fps":12,"size":[capture_view.size.x,capture_view.size.y],"source":source,"source_sha256":hash,"source_unchanged":hash==FileAccess.get_sha256(source),"game_state_unchanged":unchanged,"profile":ui.map_ambient.profile,"water_cells":ui.map_ambient.water.size(),"shore_segments":ui.map_ambient.shores.size(),"native_tile":16,"render_and_wait_ms_per_frame":float(render_us)/frames/2000.0})
		if mode=="phone":
			report[-1].pixel_scale=phone.pixel_scale
			report[-1].logical_size=[phone.game_view.size_2d_override.x,phone.game_view.size_2d_override.y]
			report[-1].game_rect=[phone.game_rect.position.x,phone.game_rect.position.y,phone.game_rect.size.x,phone.game_rect.size.y]
			report[-1].phone_layout_errors=phone.layout_errors.duplicate()
			if not phone.layout_errors.is_empty():push_error("Phone layout errors");quit(1);return
		if not unchanged:
			var changes={}
			for field in initial:
				var current=ui.game.get(field)
				if JSON.stringify(initial[field])!=JSON.stringify(current):changes[field]={"before":initial[field],"after":current}
			var diff=FileAccess.open(OUTPUT+"capture-state-diff.json",FileAccess.WRITE)
			diff.store_string(JSON.stringify(changes,"  "));diff.close()
			push_error("Rendering changed gameplay "+code);quit(1);return
		print("AMBIENT_CAPTURE ",mode," ",code," OK ",report[-1])
		if mode=="phone":phone.queue_free()
		else:ui.queue_free()
		await process_frame
		ui=null;phone=null
	var output=FileAccess.open(OUTPUT+mode+"-captures.json",FileAccess.WRITE)
	output.store_string(JSON.stringify({"passed":not abort,"mode":mode,"maps":report,"capture":"Godot guarded offscreen render, matched clock, genuine journal retry, frozen player decisions; not iPhone recording"},"  "));output.close()
	capture_view.queue_free();await process_frame
	quit(0 if not abort else 1)
