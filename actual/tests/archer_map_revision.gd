extends SceneTree
## Exercise the real selector and imported textures, also against the exported PCK.
const Party = preload("res://core/party_sprites.gd")
const Reviewed = preload("res://core/reviewed_animations.gd")
var checks := 0
var errors: Array = []
func _initialize(): call_deferred("run")
func check(ok: bool, label: String):
	checks += 1
	if not ok: errors.append(label);push_error(label)
func pixels(art: Dictionary) -> Image:
	var texture: Texture2D = load(art.path)
	var image = texture.get_image();image.convert(Image.FORMAT_RGBA8)
	return image
func run():
	var ui = load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/archer-map-test-unused-save.json";ui.game.new_game()
	var baseline = ui.game.roster.duplicate(true)
	for side in ["player", "enemy"]:
		var actor: Dictionary = ui.game.roster.daan.duplicate(true);actor.side=side
		var idle = Party.sprite("map", actor, 1)
		var walk = Party.sprite("map_move", actor, 1)
		for kind in ["map", "map_move"]:
			var art = Party.sprite(kind, actor, 1)
			var image = pixels(art)
			check(int(art.native_density)==4, side+kind+" four-times density")
			check(image.get_size()==Vector2i(art.frame_size[0]*art.frames,art.frame_size[1]),side+kind+" atlas dimensions")
			check(art.ground_shadow.path.ends_with("/archer-ground-shadow.png") and ResourceLoader.exists(art.ground_shadow.path),side+kind+" independent shadow")
			check(PackedInt32Array(art.ground_shadow.size)==PackedInt32Array([11,3]) and is_equal_approx(float(art.ground_shadow.alpha),0.38),side+kind+" reviewed shadow")
			check(Vector2(art.anchor[0],art.anchor[1])-Vector2(art.tile_origin[0],art.tile_origin[1])==Vector2(8,16),side+kind+" foot alignment")
			var colors: Dictionary = {}
			for y in range(image.get_height()):
				for x in range(image.get_width()):
					var color=image.get_pixel(x,y)
					if color.a>0:colors[color.to_html(true)]=true
			check(colors.size()==4,side+kind+" four opaque colors")
			check(colors.has("3976b5ff" if side=="player" else "ae5148ff"),side+kind+" faction palette")
		check(idle.art_revision=="body-volume-motion-20261018" and walk.art_revision=="body-volume-motion-20261018",side+" approved revisions")
		check(idle.static_facing and not walk.static_facing,side+" facing selection")
		check(PackedInt32Array(idle.native_cycle)==PackedInt32Array([0,1,2,1]) and PackedInt32Array(idle.cycle_ticks)==PackedInt32Array([14,8,14,8]),side+" native idle cycle")
		for sample in [[0,0],[14,1],[22,2],[36,1]]:
			ui.elapsed=(float(sample[0])+0.01)/60.0988
			check(ui._native_map_pose(idle)==int(sample[1]),side+" runtime idle tick "+str(sample[0]))
		var walking=pixels(walk)
		for direction in {"up":[0,1],"right":[2,3],"down":[4,5],"left":[6,7]}:
			var expected={"up":[0,1],"right":[2,3],"down":[4,5],"left":[6,7]}[direction]
			check(PackedInt32Array(walk.directions[direction])==PackedInt32Array(expected),side+" phase slots "+direction)
		for pair in [[2,6],[3,7]]:
			var right=walking.get_region(Rect2i(pair[0]*128,0,128,96));right.flip_x()
			check(right.get_data()==walking.get_region(Rect2i(pair[1]*128,0,128,96)).get_data(),side+" side mirror keeps phase "+str(pair))
		for slot in [4,5]:
			check(walking.get_pixel(slot*128+57,54).to_html(true)=="dda77dff",side+" drawing hand covers string "+str(slot))
	var story=Party.sprite("hub",ui.game.roster.daan,1)
	check(int(story.frames)==1 and story.static_facing and not story.has("native_cycle"),"friendly story static only")
	for direction in story.directions:check(PackedInt32Array(story.directions[direction])==PackedInt32Array([0,0]),"story holds pose "+direction)
	check(pixels(story).get_data()==pixels(Party.sprite("map",ui.game.roster.daan,1)).get_region(Rect2i(0,0,96,96)).get_data(),"story identical to idle first pose")
	for id in ["daan","beck","roan"]:
		var object={"action":id}
		check(ui._party_hub_sprite(object,{}).get("reviewed_profile","")==story.reviewed_profile,"real story NPC selector "+id)
	for variant in [{"side":"enemy"},{"neutral":true},{"event_object":true},{"class_id":7}]:
		var actor: Dictionary=ui.game.roster.daan.duplicate(true);actor.merge(variant,true)
		check(Reviewed.map_sprite("hub",actor).is_empty(),"story scope "+str(variant))
	check(Reviewed.map_sprite("world",ui.game.roster.daan).is_empty(),"archer world unchanged")
	check(ui.game.roster==baseline,"visual selection preserves roster")
	var result={"passed":errors.is_empty(),"checks":checks,"errors":errors,"revision":"body-volume-motion-20261018"}
	var output=OS.get_environment("ARCHER_MAP_REPORT")
	if output.is_empty():output="res://reports/body-volume-map-test-20261018/archer/runtime.json"
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	print("ARCHER_MAP_TEST ",JSON.stringify(result))
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
