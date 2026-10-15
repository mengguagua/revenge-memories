extends SceneTree
## Rendering geometry and module-preservation checks; no combat simulation.
const Border=preload("res://core/environment_border.gd")
const State=preload("res://core/game_state.gd")
var count:=0
var errors: Array=[]
var ui
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	count+=1
	if not ok:errors.append(label);push_error(label)
func geometry(label: String,cells: Vector2i,module_cells: Vector2i,origin: Vector2,size: Vector2i) -> void:
	var visible=Rect2(-((Vector2(size)-Vector2(256,240))/2).floor(),Vector2(size))
	var protected=Rect2(origin,Vector2(cells)*16)
	for rect in Border.module_rects(origin,cells,module_cells,visible):
		check(visible.encloses(rect),label+" complete object inside viewport")
		check(not protected.intersects(rect),label+" whole object outside map boundary")
		check(rect.size==Vector2(module_cells)*16,label+" original module dimensions")
func run() -> void:
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.game.save_path="res://reports/campaign/border-fixtures-save.json";ui.game.new_game();ui.instant_mode=true
	var pack=State.read_json("res://assets/battle_tiles/battle-tiles.json");var modules={}
	for m in pack.modules:modules[str(m.name)]=m
	var sizes=[Vector2i(256,240),Vector2i(384,240),Vector2i(426,240),Vector2i(426,266),Vector2i(562,260)]
	var rooms=["P00","H01","H02","H03","H04","H05","H06","H07","H08","H09"]
	for room in rooms:
		ui.hub_controller.enter_room(room)
		for item in ui.hub_controller.scenery:
			var image=load("res://assets/battle_tiles/"+str(modules[item.name].path))
			check(image.get_size()==Vector2(item.rect.size)*16,room+" scenery uses full source "+str(item.name))
			check(Rect2i(0,0,14,9).encloses(item.rect),room+" scenery does not cross room bounds "+str(item.name))
		for size in sizes:geometry(room,Vector2i(14,9),Vector2i(4,2) if room=="H08" else Vector2i(3,3),Vector2(16,8),size)
	var snow_visible=Rect2(-64,0,384,240)
	var snow=Border.module_rects(Vector2(16,8),Vector2i(14,9),Vector2i(3,3),snow_visible)
	check(snow.has(Rect2(240,8,48,48)),"regression: right snow grove starts at first column after 14-cell room")
	check(snow.has(Rect2(-32,8,48,48)),"regression: left snow grove ends at room boundary")
	var stages=[]
	for meta in ui.game.campaign.stages.values():
		var stage=State.read_json(str(meta.path));var cells=Vector2i(stage.map.width,stage.map.height)
		stages.append(stage.code)
		for m in stage.art_modules:
			var original=modules[m.name];var ox=int(m.origin[0]);var oy=int(m.origin[1])
			for dy in range(original.footprint[1]):
				for dx in range(original.footprint[0]):check(stage.art_layers[2][oy+dy][ox+dx]==original.tiles[dy][dx],stage.code+" complete placed module "+str(m.name))
		for size in sizes:
			for origin in [Vector2.ZERO,Vector2(256,240)/2-Vector2(cells)*8]:geometry(stage.code,cells,Vector2i(4,2),origin,size)
	var world=State.read_json("res://data/formal_world.json");var world_pack=State.read_json("res://assets/world_tiles/world-tiles.json");var wm={}
	for m in world_pack.modules:wm[str(m.name)]=m
	for m in world.modules:
		var original=wm[m.name];var ox=int(m.origin[0]);var oy=int(m.origin[1])
		for dy in range(original.footprint[1]):
			for dx in range(original.footprint[0]):check(world.layers[2][oy+dy][ox+dx]==original.tiles[dy][dx],"world module remains intact "+str(m.name))
	var report={"passed":errors.is_empty(),"checks":count,"errors":errors,"rooms":rooms,"stages":stages,"world_modules":world.modules.size(),"canvas_sizes":sizes,"scope":"All 10 hubs, 7 battle art layers, world modules, and five landscape widths; border sources drawn whole, never modulo-clipped"}
	var f=FileAccess.open("res://reports/campaign/border-integrity.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("BORDER_INTEGRITY ",JSON.stringify(report))
	ui.queue_free();await process_frame;ui=null;quit(0 if errors.is_empty() else 1)
