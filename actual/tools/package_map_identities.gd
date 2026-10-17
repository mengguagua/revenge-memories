extends SceneTree
const Party=preload("res://core/party_sprites.gd")
var errors=[]
var checks=0
func check(ok: bool,label: String):
	checks+=1
	if not ok:errors.append(label)
func _initialize():
	var data=Party.data()
	check(ProjectSettings.get_setting("application/config/version")=="0.7.2","Package application version")
	check(data.version=="0.7.2" and data.actor_maps.size()==16,"Packaged map identities")
	for id in data.actor_maps:
		for role in data.actor_maps[id]:
			var profile=data.actor_maps[id][role]
			check(profile.world==profile.hub,id+" world is story hub")
			for kind in ["hub","map","map_move"]:
				var art=profile[kind]
				check(ResourceLoader.exists(art.path),id+"/"+role+"/"+kind+" packaged resource")
				check(int(art.native_density)==4,id+"/"+role+"/"+kind+" native density")
	check(ResourceLoader.exists(data.story_npc_profiles.guard.hub.path),"Packaged guard")
	var portraits=JSON.parse_string(FileAccess.get_file_as_string("res://data/portraits.json"))
	check(portraits.version=="0.7.2","Packaged portrait version")
	for key in portraits.assets:
		check(ResourceLoader.exists(portraits.assets[key].path),"Packaged portrait "+key)
	var motion=JSON.parse_string(FileAccess.get_file_as_string("res://data/m11_party_motion.json"))
	check(motion.variants.size()==508,"Original action programs retained")
	var result={"passed":errors.is_empty(),"version":data.version,"checks":checks,"actors":data.actor_maps.size(),"source_variants":motion.variants.size(),"errors":errors}
	var output=OS.get_environment("MAP_IDENTITY_PROBE_OUT")
	if not output.is_empty():
		var f=FileAccess.open(output,FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
	print("PACKAGED_MAP_IDENTITY ",JSON.stringify(result))
	quit(0 if errors.is_empty()else 1)
