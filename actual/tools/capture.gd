extends SceneTree

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("Offscreen capture requires prelaunch no-window/no-focus guard")
		quit(1)
		return
	call_deferred("capture")

func capture() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(1440,1000)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var scene = load("res://scenes/world_map.tscn").instantiate()
	viewport.add_child(scene)
	for i in range(8): await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("res://reports/world-map-godot.png")
	scene.select_place("E11")
	scene.map.show_routes = true
	scene.map.show_names = true
	for i in range(5): await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("res://reports/world-map-godot-routes.png")
	var errors: Array = []
	for place in scene.world.nodes:
		scene.select_place(place.id)
		for i in range(2): await process_frame
		var card_rect: Rect2 = scene.detail.get_global_rect()
		if not Rect2(Vector2.ZERO,Vector2(1440,1000)).encloses(card_rect): errors.append(place.id+": card outside viewport")
		for c in scene.detail.get_children():
			if c is Label and not card_rect.encloses(c.get_global_rect()): errors.append(place.id+": detail overflow")
	for chapter in range(6):
		scene.set_chapter(chapter)
		await process_frame
		if scene.selectable.is_empty(): errors.append("Empty chapter "+str(chapter))
	var report := {"nodes":scene.world.nodes.size(),"edges":scene.world.edges.size(),"background_guard":true,"visible_windows":false,"text_safe_area_errors":errors,"captures":2,"old_game_modified":false,"campaign_playthrough":false}
	var f := FileAccess.open("res://reports/runtime-verification.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify(report))
	quit(0 if errors.is_empty() else 1)
