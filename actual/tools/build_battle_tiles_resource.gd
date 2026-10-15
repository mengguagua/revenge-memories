extends SceneTree
const PEERS={12:1,0:2,4:4,8:8,15:16,3:32,7:64,11:128}
func _initialize() -> void:
	var p=JSON.parse_string(FileAccess.get_file_as_string("res://assets/battle_tiles/battle-tiles.json"))
	var set_=TileSet.new();set_.tile_size=Vector2i(16,16)
	for pair in [["category",TYPE_INT],["kind",TYPE_STRING],["name",TYPE_STRING]]:
		var index=set_.get_custom_data_layers_count();set_.add_custom_data_layer();set_.set_custom_data_layer_name(index,pair[0]);set_.set_custom_data_layer_type(index,pair[1])
	var atlas=TileSetAtlasSource.new();atlas.texture=load("res://assets/battle_tiles/battle-tiles.png");atlas.texture_region_size=Vector2i(16,16);set_.add_source(atlas,0)
	var sets={}
	for family in p.families:
		var si=set_.get_terrain_sets_count();set_.add_terrain_set();set_.set_terrain_set_mode(si,TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES)
		set_.add_terrain(si);set_.set_terrain_name(si,0,str(family));sets[family]=si
	for tile in p.tiles:
		var at=Vector2i(tile.atlas[0],tile.atlas[1]);atlas.create_tile(at);var data=atlas.get_tile_data(at,0)
		data.set_custom_data("category",int(tile.category));data.set_custom_data("kind",str(tile.kind));data.set_custom_data("name",str(tile.name))
		if tile.kind=="edge":
			var family=str(tile.name).substr(0,str(tile.name).rfind("_"));data.terrain_set=sets[family];data.terrain=0
			for peer in PEERS:data.set_terrain_peering_bit(peer,0 if int(tile.mask)&int(PEERS[peer]) else -1)
	var error=ResourceSaver.save(set_,"res://assets/battle_tiles/battle-tiles.tres")
	var loaded=load("res://assets/battle_tiles/battle-tiles.tres")
	var report={"saved":error==OK,"tiles":p.tiles.size(),"terrain_sets":sets.size(),"round_trip":loaded is TileSet,"tile_size":[16,16]}
	var f=FileAccess.open("res://reports/campaign/battle-resource.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("BATTLE_TILESET ",JSON.stringify(report));quit(0 if error==OK else 1)
