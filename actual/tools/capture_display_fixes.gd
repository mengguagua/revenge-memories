extends "res://tools/capture_real.gd"
var shots: Array=[]
func shot(name: String,source: String) -> void:
	ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var file="res://reports/display-fixes/"+name+".png"
	viewport.get_texture().get_image().save_png(file)
	shots.append({"path":file,"source":source,"canvas":viewport.size,"layout_errors":ui.layout_errors.duplicate(),"plot_layout":ui.plot_layout_audit.duplicate(true) if ui.view=="plot" else {},"fixture":false})
	print("DISPLAY_SHOT ",name," ",ui.layout_errors)
func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/display-fixes/walk-frames"))
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	load_checkpoint("prologue");walk_to(Vector2i(7,3));key(KEY_UP);key(KEY_Z);await process_frame;key(KEY_Z)
	await shot("01-dialogue-wide","Real prologue save, facing Helan and beginning D00 through input")
	for i in range(50):
		if ui.view=="plot" and str(ui.plot_pages[ui.plot_index].speaker)=="旁白":break
		key(KEY_Z);await process_frame
	key(KEY_Z);await shot("02-narration-wide","Actual first narration page following D00, no portrait allocation")
	viewport.size=Vector2i(256,240);await process_frame
	await shot("03-narration-native","Same live narration at original reference aspect ratio")
	viewport.size=Vector2i(562,260);await process_frame
	await shot("04-narration-mobile-landscape","Same live narration resized to landscape phone canvas")
	await settle()
	viewport.size=Vector2i(384,240);await process_frame
	await shot("05-village-mac","Real transition into snow village at 16:10 canvas")
	viewport.size=Vector2i(426,240);await process_frame
	load_checkpoint("M13-deployment");cursor_to(Vector2i(5,4))
	await shot("06-battle-wide","Actual M13 opening save with camera moved through cursor keys")
	viewport.size=Vector2i(560,240);await process_frame
	load_checkpoint("S12-deployment")
	await shot("07-battle-ultrawide","Actual S12 save, forest surroundings outside original playable map")
	viewport.size=Vector2i(426,240);await process_frame
	load_checkpoint("world-start");await shot("08-world-wide","Actual first departure, expanded geographic view")
	# A deterministic real-input/rendered walk strip, without OS key repeat.
	load_checkpoint("prologue");ui.instant_mode=false;ui.set_process(false);ui.set_physics_process(false)
	var frame=0
	for dir in [KEY_RIGHT,KEY_RIGHT,KEY_RIGHT,KEY_RIGHT,KEY_LEFT,KEY_LEFT,KEY_LEFT,KEY_LEFT]:
		key(dir)
		for tick_ in range(16):
			ui._process(ui.hub_controller.STEP/16.0);ui.queue_redraw()
			await process_frame;await RenderingServer.frame_post_draw
			viewport.get_texture().get_image().save_png("res://reports/display-fixes/walk-frames/%03d.png"%frame);frame+=1
	var bad=[]
	for item in shots:bad.append_array(item.layout_errors)
	var report={"passed":bad.is_empty() and not abort,"shots":shots,"walk_frames":frame,"failures":failures,"background_guard":true,"visible_windows":false,"scope":"Actual prologue/battle/world checkpoints and input, no fabricated map art; walk time sampled at original 60.0988Hz"}
	var f=FileAccess.open("res://reports/display-fixes/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit(0 if bad.is_empty() and not abort else 1)
