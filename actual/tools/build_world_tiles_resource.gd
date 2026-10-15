extends SceneTree

const PEERS := {12:1,0:2,4:4,8:8,15:16,3:32,7:64,11:128}

func _initialize() -> void:
	var pack: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world_tiles/world-tiles.json"))
	var ts := TileSet.new()
	ts.tile_size = Vector2i(16,16)
	for field in [["terrain_id",TYPE_INT],["terrain_key",TYPE_STRING],["tile_kind",TYPE_STRING],["route_mask",TYPE_INT]]:
		ts.add_custom_data_layer()
		var index := ts.get_custom_data_layers_count()-1
		ts.set_custom_data_layer_name(index,field[0])
		ts.set_custom_data_layer_type(index,field[1])
	for family in pack.families:
		ts.add_terrain_set()
		var set_id: int = family.terrain_set
		ts.set_terrain_set_mode(set_id,TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES)
		for key in [family.background,family.foreground]:
			ts.add_terrain(set_id)
			var index := ts.get_terrains_count(set_id)-1
			ts.set_terrain_name(set_id,index,key)
			var rgb: Array = pack.materials[key]
			ts.set_terrain_color(set_id,index,Color(rgb[0]/255.0,rgb[1]/255.0,rgb[2]/255.0))
	var source := TileSetAtlasSource.new()
	source.texture = load("res://assets/world_tiles/world-tiles.png")
	source.texture_region_size = Vector2i(16,16)
	ts.add_source(source,0)
	var count := 0
	for tile in pack.tiles:
		if tile.kind == "unused": continue
		var cell := Vector2i(tile.atlas[0],tile.atlas[1])
		source.create_tile(cell)
		var data := source.get_tile_data(cell,0)
		data.set_custom_data("terrain_id",int(tile.terrain_id))
		data.set_custom_data("terrain_key",str(tile.terrain))
		data.set_custom_data("tile_kind",str(tile.kind))
		data.set_custom_data("route_mask",int(tile.get("route_mask",-1)))
		if tile.has("terrain_set"):
			data.terrain_set = int(tile.terrain_set)
			data.terrain = int(tile.terrain_index)
			for neighbor in PEERS:
				data.set_terrain_peering_bit(neighbor,1 if data.terrain==1 and int(tile.mask)&int(PEERS[neighbor]) else 0)
		count += 1
	var error := ResourceSaver.save(ts,"res://assets/world_tiles/world-tiles.tres")
	if error != OK:
		push_error("TileSet save failed: "+str(error)); quit(1); return
	var imported := load("res://assets/world_tiles/world-tiles.tres") as TileSet
	var atlas := imported.get_source(0) as TileSetAtlasSource
	assert(atlas.get_tiles_count() == count)
	for tile in pack.tiles:
		if tile.kind == "unused": continue
		var data := atlas.get_tile_data(Vector2i(tile.atlas[0],tile.atlas[1]),0)
		assert(int(data.get_custom_data("terrain_id")) == int(tile.terrain_id))
	var f := FileAccess.open("res://reports/world-tiles-b/godot-resource-verification.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"native_tile_size":16,"registered_tiles":count,"terrain_sets":imported.get_terrain_sets_count(),"custom_data_roundtrip":true,"headless":true},"  ")+"\n")
	print("WORLD_TILESET_REGISTERED=",count," TERRAIN_SETS=",imported.get_terrain_sets_count())
	quit()
