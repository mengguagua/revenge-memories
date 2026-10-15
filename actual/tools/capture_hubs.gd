extends "res://tools/capture_real.gd"
func run() -> void:
	viewport=SubViewport.new();viewport.size=Vector2i(256,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	load_checkpoint("prologue");walk_to(Vector2i(7,3));key(KEY_UP);key(KEY_Z);await process_frame;key(KEY_Z)
	await real_shot("01-prologue-dialogue","Real prologue save, buildings and facing interaction")
	await settle();await real_shot("02-snow-village","Real prologue transition, intact snow cottages and grove")
	var source=State.read_json("res://reports/campaign/real-screenshots.json")
	for shot in real_shots:
		for i in range(source.shots.size()):
			if source.shots[i].path==shot.path:source.shots[i]=shot
	var f=FileAccess.open("res://reports/campaign/real-screenshots.json",FileAccess.WRITE);f.store_string(JSON.stringify(source,"  "));f.close()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit()
