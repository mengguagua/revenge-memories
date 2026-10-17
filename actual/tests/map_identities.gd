extends SceneTree
const Party=preload("res://core/party_sprites.gd")
const State=preload("res://core/game_state.gd")
var errors=[]
var count=0
func check(ok: bool,label: String):
	count+=1
	if not ok:errors.append(label)
func _initialize():
	call_deferred("run")
func run():
	var game=State.new();game.new_game();var before=game.roster.duplicate(true)
	var data=Party.data()
	check(data.version=="0.7.2","Current map identity version")
	check(data.actor_maps.size()==16,"All16 named map identities")
	for id in data.actor_maps:
		for class_key in data.actor_maps[id]:
			var actor=game.characters[id].duplicate(true)
			actor.class_id=int(class_key) if class_key.is_valid_int() else 24 if class_key=="eileen_promoted" else 11
			if class_key=="23":actor.promoted=true
			var chapter=2 if id in ["german","eileen","mireille","lisa","carlo","lord","roan","shia"]else 1
			for kind in ["hub","map","map_move","world"]:
				var art=Party.sprite(kind,actor,chapter)
				check(not art.is_empty(),id+"/"+class_key+"/"+kind+" binding")
				check(ResourceLoader.exists(art.get("path","")),id+"/"+class_key+"/"+kind+" file")
				check(int(art.get("native_density",0))==4,id+"/"+class_key+"/"+kind+" native4")
				check(art.get("portrait_hair_palette",[])==data.map_hair_bindings[id].hair,id+"/"+class_key+"/"+kind+" portrait palette")
			check(Party.sprite("world",actor,chapter)==Party.sprite("hub",actor,chapter),id+"/"+class_key+" world uses hub")
			var original=data.chapter1_classes[class_key].battle if chapter==1 and id=="hunapu"else data.classes[class_key].battle
			check(Party.sprite("battle",actor,chapter)==original,id+"/"+class_key+" profession combat untouched")
	check(not Party.applies({"id":"daan","side":"enemy"}),"Actor colours cannot leak to enemy faction")
	check(data.story_npc_profiles.guard.hub.path!=Party.sprite("hub",game.characters.hunapu,1).path,"Guard cannot reuse protagonist")
	check(ResourceLoader.exists(data.story_npc_profiles.guard.hub.path),"Guard soldier art exists")
	check(game.roster==before,"No growth EXP equipment or save changes")
	var f=FileAccess.open("res://reports/current-art/logic-checks.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":count,"errors":errors},"  "));f.close()
	print("MAP_IDENTITY_LOGIC ",count," checks; errors ",errors)
	call_deferred("quit",0 if errors.is_empty()else 1)
