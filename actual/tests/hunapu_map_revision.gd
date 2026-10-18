extends SceneTree
## Focused map integration check, runnable unchanged against the exported PCK.
const Party = preload("res://core/party_sprites.gd")
var checks := 0
var errors: Array = []
func _initialize(): call_deferred("run")
func check(ok: bool, label: String):
	checks += 1
	if not ok: errors.append(label);push_error(label)
func run():
	var ui = load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path = "/private/tmp/hunapu-map-test-unused-save.json";ui.game.new_game()
	var actor: Dictionary = ui.game.roster.hunapu
	var baseline = ui.game.roster.duplicate(true)
	var images: Dictionary = {}
	for kind in ["hub", "world", "map_move", "map"]:
		var art = Party.sprite(kind, actor, 1)
		check(art.get("art_revision", "") == "hero-map-v3-side-arms", kind + " latest art revision")
		check(int(art.get("native_density", 0)) == 4, kind + " exact four-times density")
		check(ResourceLoader.exists(art.path), kind + " atlas exists")
		var texture: Texture2D = load(art.path)
		var image = texture.get_image();image.convert(Image.FORMAT_RGBA8)
		check(image.get_size() == Vector2i(art.frame_size[0] * art.frames, art.frame_size[1]), kind + " atlas slots")
		var colors: Dictionary = {};var transparent := 0
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var color = image.get_pixel(x,y)
				if color.a == 0: transparent += 1
				else: colors[color.to_html(true)] = true
		check(transparent > 0 and colors.size() == 4, kind + " four opaque colors and true alpha")
		for color in colors: check(color in ["172638ff", "3976b5ff", "e4e1c8ff", "dda77dff"], kind + " approved color " + color)
		images[kind] = image
		check(art.has("ground_shadow") and ResourceLoader.exists(art.ground_shadow.path), kind + " independent ground shadow")
		var shadow_size = [11,3] if kind in ["hub", "world"] else [14,2]
		var shadow_alpha = 0.38 if kind in ["hub", "world"] else 0.58
		check(PackedInt32Array(art.ground_shadow.size) == PackedInt32Array(shadow_size) and is_equal_approx(float(art.ground_shadow.alpha),shadow_alpha), kind + " review shadow dimensions/opacity")
		check(Vector2(art.anchor[0],art.anchor[1])-Vector2(art.tile_origin[0],art.tile_origin[1]) == Vector2(8,16), kind + " shared foot anchor")
	check(images.hub.get_data() == images.world.get_data(), "world and story use identical frame pixels")
	check(Party.sprite("hub",actor,1).ground_shadow == Party.sprite("world",actor,1).ground_shadow, "world and story share the approved continuous shadow")
	var walk = Party.sprite("map_move", actor, 1)
	check(PackedInt32Array(walk.directions.left) == PackedInt32Array([6,7]) and PackedInt32Array(walk.directions.right) == PackedInt32Array([2,3]), "native side phase mapping")
	var idle = Party.sprite("map", actor, 1)
	check(PackedInt32Array(idle.native_cycle) == PackedInt32Array([0,1,2,1]) and PackedInt32Array(idle.cycle_ticks) == PackedInt32Array([14,8,14,8]), "idle native timing")
	for sample in [[0,0],[14,1],[22,2],[36,1]]:
		ui.elapsed = (float(sample[0])+0.01)/60.0988
		check(ui._native_map_pose(idle) == int(sample[1]), "idle runtime pose at tick " + str(sample[0]))
	check(ui.game.roster == baseline, "visual selection does not change roster")
	var result = {"passed":errors.is_empty(),"checks":checks,"errors":errors,"revision":"hero-map-v3-side-arms"}
	var output = OS.get_environment("HUNAPU_MAP_REPORT")
	if output.is_empty():output="res://reports/hunapu-map-test-20261018/runtime.json"
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	print("HUNAPU_MAP_TEST ",JSON.stringify(result))
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
