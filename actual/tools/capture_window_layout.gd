extends "res://tools/capture_real.gd"
func run() -> void:
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
	load_checkpoint("prologue");var records=[];var passed=true
	for dimensions in [Vector2i(1280,720),Vector2i(1280,800),Vector2i(1688,780)]:
		root.size=dimensions
		for i in range(5):await process_frame
		await RenderingServer.frame_post_draw
		var name="window-%dx%d.png"%[dimensions.x,dimensions.y]
		root.get_texture().get_image().save_png("res://reports/display-fixes/"+name)
		var scale=root.get_screen_transform().get_scale();var logical=root.get_visible_rect().size
		var unused=Vector2(root.size)-logical*scale
		var fills=unused.x<scale.x+0.01 and unused.y<scale.y+0.01 and is_equal_approx(scale.x,scale.y)
		passed=passed and fills and ui.layout_errors.is_empty()
		records.append({"window":root.size,"logical_viewport":logical,"content_scale_size":root.content_scale_size,"aspect":root.content_scale_aspect,"scale_mode":root.content_scale_stretch,"screen_transform":root.get_screen_transform(),"stretch_transform":root.get_stretch_transform(),"unused_physical_pixels":unused,"fills_at_integer_scale":fills,"layout_errors":ui.layout_errors.duplicate()})
		print("WINDOW_LAYOUT ",records[-1])
	var f=FileAccess.open("res://reports/display-fixes/window-layout.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":passed,"records":records,"background_guard":true,"visible_windows":false},"  "));f.close()
	ui.queue_free();await process_frame;ui=null;quit(0 if passed else 1)
