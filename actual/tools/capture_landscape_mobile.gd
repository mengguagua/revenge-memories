extends "res://tools/capture_display_fixes.gd"
func run() -> void:
	viewport=SubViewport.new();viewport.size=Vector2i(562,260);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	load_checkpoint("prologue");walk_to(Vector2i(7,3));key(KEY_UP);key(KEY_Z);await process_frame
	for i in range(50):
		if ui.view=="plot" and str(ui.plot_pages[ui.plot_index].speaker)=="旁白":break
		key(KEY_Z);await process_frame
	key(KEY_Z);await shot("04-narration-mobile-landscape","Actual prologue input and narration, landscape phone canvas")
	var path="res://reports/display-fixes/captures.json";var report=State.read_json(path)
	for i in range(report.shots.size()):
		if str(report.shots[i].path).contains("04-narration-phone"):report.shots[i]=shots[0]
	var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	await settle()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit(0 if not abort else 1)
