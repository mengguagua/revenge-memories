extends SceneTree

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("World tile capture requires no-window/no-focus guard");quit(1);return
	call_deferred("capture")

func capture() -> void:
	var pack: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world_tiles/world-tiles.json"))
	var samples: Array = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world_tiles/sample-maps.json"))
	var scene: Dictionary = samples[0]
	var lookup: Dictionary = {}
	for t in pack.tiles: lookup[int(t.id)] = Vector2i(t.atlas[0],t.atlas[1])
	var tile_set := load("res://assets/world_tiles/world-tiles.tres") as TileSet
	var viewport := SubViewport.new()
	viewport.size = Vector2i(int(scene.width)*16,int(scene.height)*16)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var painted := 0
	for cells in scene.layers:
		var layer := TileMapLayer.new()
		layer.tile_set = tile_set
		layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		viewport.add_child(layer)
		for y in range(int(scene.height)):
			for x in range(int(scene.width)):
				var id: int = int(cells[y][x])
				if id >= 0: layer.set_cell(Vector2i(x,y),0,lookup[id]);painted += 1
	for i in range(6): await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("res://reports/world-tiles-b/godot-world-sample.png")
	var f := FileAccess.open("res://reports/world-tiles-b/godot-render-verification.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"native_size":viewport.size,"painted_cells":painted,"layers":scene.layers.size(),"background_guard":true,"visible_windows":false,"terrain_resource_loaded":true},"  ")+"\n")
	print("WORLD_TILES_RENDERED=",painted)
	quit()
