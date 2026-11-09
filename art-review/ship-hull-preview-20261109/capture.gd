extends SceneTree
## A read-only capture of the live stage data for this art review.

class MapLayers extends "res://tools/map_catalog_canvas.gd":
	var part := "full"
	var reserve_open := false

	func _ready() -> void:
		battle_animation = load("res://core/battle_animation.gd").new(self)
		super._ready()

	func _draw() -> void:
		if game.battle_data.is_empty() or not is_node_ready():
			return
		if part == "full" and not reserve_open:
			super._draw()
			return

		var stage = game.battle_data
		var origin := Vector2(PAD, PAD)
		var atlas := _tex(str(stage.art_atlas))
		var columns := int(stage.get("art_columns", 32))
		draw_set_transform(Vector2.ZERO)
		if part != "foreground":
			_draw_battle_surroundings(origin)
			_draw_layers(stage.art_layers.slice(0, 1), columns, atlas, origin)
		if part == "base":
			return

		_draw_layers(stage.art_layers.slice(1), columns, atlas, origin)
		_draw_nature_props(stage.get("natural_props", []), origin)
		var props = stage.get("art_props", [])
		if part == "foreground":
			props = props.filter(func(prop): return prop.get("tag", "") != "boarding_plank")
		_draw_art_props(props, origin)
		for obj in stage.objects:
			if obj.kind == "visit":
				continue
			if obj.id == "reserve_bridge" and reserve_open:
				if part == "full":
					for cell in obj.open_art_cells:
						var at := origin + Vector2(cell.position[0], cell.position[1]) * 16
						_draw_atlas_cell(atlas, int(cell.base_tile), at)
				continue
			var path := str(obj.get("sprite_path", "res://assets/battle_tiles/modules/" + str(obj.sprite) + ".png"))
			_draw_review_object(path, obj, origin, false)
		for unit in stage.npc_units:
			if unit.has("sprite_path"):
				_draw_review_object(str(unit.sprite_path), unit, origin, true)
			elif unit.id == "medicine_wagon":
				var at := origin + Vector2(unit.position[0], unit.position[1]) * 16
				draw_texture(_tex("res://assets/battle_tiles/modules/medicine_wagon.png"), at - Vector2(8, 0))

	func _draw_review_object(path: String, obj: Dictionary, origin: Vector2, centered: bool) -> void:
		var texture := _tex(path)
		var at := origin + Vector2(obj.position[0], obj.position[1]) * 16
		var offset := Vector2((texture.get_width() - 16) * 0.5 if centered else 0.0, texture.get_height() - 16)
		if obj.has("sprite_offset"):
			offset = -Vector2(obj.sprite_offset[0], obj.sprite_offset[1])
		draw_texture(texture, at - offset)

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		quit(1)
		return
	call_deferred("run")

func run() -> void:
	var out := OS.get_environment("SHIP_REVIEW_CAPTURE_DIR")
	if out.is_empty() or DirAccess.make_dir_recursive_absolute(out) != OK:
		quit(2)
		return
	var viewport := SubViewport.new()
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var canvas := MapLayers.new()
	canvas.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	viewport.add_child(canvas)
	await process_frame
	for id in [201, 202, 211, 304]:
		canvas.prepare(id)
		var stage = canvas.game.battle_data
		viewport.size = Vector2i(stage.map.width * 16 + 64, stage.map.height * 16 + 64)
		canvas.size = Vector2(viewport.size)
		var parts := ["full", "base", "foreground"]
		if id == 202:
			parts.append_array(["full-open", "foreground-open"])
		for part in parts:
			canvas.reserve_open = part.ends_with("-open")
			canvas.part = part.trim_suffix("-open")
			viewport.transparent_bg = canvas.part == "foreground"
			canvas.queue_redraw()
			for frame in range(2):
				await process_frame
			await RenderingServer.frame_post_draw
			var path := out.path_join("%s-%s.png" % [stage.code, part])
			var error := viewport.get_texture().get_image().save_png(path)
			if error != OK:
				push_error("Could not save " + path)
				quit(3)
				return
			print("SHIP_REVIEW_CAPTURE ", stage.code, " ", part, " ", viewport.size)
	viewport.queue_free()
	await process_frame
	quit()
