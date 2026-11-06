extends SceneTree
const Art=preload("res://core/campaign_art.gd")
const Reviewed=preload("res://core/reviewed_animations.gd")
const FX=preload("res://core/campaign_effects.gd")
const OUT="res://reports/new-art-fallback-20261026/"
var checks=0
var errors=[]
var paths={}
var ui
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks+=1
	if not ok:errors.append(label);push_error(label)
func resources(value,label:String):
	if value is Dictionary:
		for key in value:
			var entry=value[key]
			if key=="path" and entry is String and entry.begins_with("res://"):
				check(not entry.begins_with("res://assets/original/"),label+" source path")
				check(not FX.excluded(entry),label+" renamed original pixels")
				paths[entry]=true
			else:resources(entry,label)
	elif value is Array:
		for child in value:resources(child,label)
func actors_in(value)->Array:
	var result=[]
	if value is Dictionary:
		if value.has("class_id") and value.has("id") and value.has("hp"):result.append(value)
		else:
			for child in value.values():result.append_array(actors_in(child))
	elif value is Array:
		for child in value:result.append_array(actors_in(child))
	return result
func run():
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/new-art-fallback-slots";ui.game.save_path="/private/tmp/new-art-fallback.json";root.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
	resources(ui.graphics,"campaign graphics");resources(ui.cursors,"campaign cursors");resources(ui.health_ui,"campaign health");resources(ui.map_effects.source(),"map effects")
	resources(FX.sprites(),"new effect bindings");resources(FX.data().variants,"per-action effects");resources(ui.battle_animation._source_metadata(),"merged effects")
	for path in paths:check(ResourceLoader.exists(path),"resource exists "+path)
	ui.game.new_game();var roster=ui.game.roster.duplicate(true);var stage_count=0;var actor_count=0
	for stage in ui.game.stages:
		if int(stage)<100:continue
		stage_count+=1
		ui.game.stage_id=int(stage);ui.game.chapter=int(ui.game.stages[stage].get("chapter",1));ui.game.route=str(ui.game.stages[stage].get("route","alm"))
		var stage_actors=actors_in(ui.game.stages[stage])+ui.game.characters.values()
		for original in stage_actors:
			var actor:Dictionary=original.duplicate(true)
			if not actor.has("side"):actor.side="player"
			if not actor.has("position"):actor.position=[4,4]
			if actor.get("event_object",false):continue
			actor_count+=1
			var before=actor.duplicate(true)
			var map=ui._map_unit_sprite(actor);var body=ui.battle_animation.sprite(actor);var face=ui._unit_portrait(actor)
			check(Art.valid(map),"map material "+str(stage)+"/"+str(actor.id))
			check(Art.valid(body),"battle material "+str(stage)+"/"+str(actor.id))
			check(Art.valid(face),"portrait material "+str(stage)+"/"+str(actor.id))
			check(actor==before,"visual lookup does not change actor state")
	ui.game.new_game();ui.game.world_node=2;ui.game.start_battle(101);ui.view="combat"
	var hero=ui.game.find_unit("hunapu");var other=ui.game.find_unit("M11_e1")
	var event={"attacker":hero.id,"defender":other.id,"weapon_index":0,"critical":false,"hit":true,"hp_before":other.hp,"hp_after":maxi(1,int(other.hp)-2)}
	ui.combat={"attacker":hero.id,"defender":other.id,"distance":1,"initiative_side":"player"}
	var metadata=Reviewed.metadata();var key=Reviewed.key(hero);var saved_path=metadata.battle[key].path
	var class_key=ui.PartySprites.class_key(hero);var old_party_path=ui.PartySprites.data().classes[class_key].battle.path
	metadata.battle[key].path="res://missing-approved-art.png";ui.PartySprites.data().classes[class_key].battle.path="res://missing-class-art.png"
	var fallback=ui.battle_animation.sprite(hero)
	check(Art.valid(fallback) and fallback.get("campaign_safe_idle",false),"broken primary body selects a new safe idle")
	check(int(fallback.sequences.idle[0])<int(fallback.frames),"safe idle belongs to its own atlas")
	ui.battle_animation.reset();await ui.battle_animation.play(event)
	check(ui.battle_animation.contact_calls==1 and int(other.hp)==int(event.hp_after),"missing animation commits actual damage exactly once")
	metadata.battle[key].path=saved_path;ui.PartySprites.data().classes[class_key].battle.path=old_party_path
	var maps=metadata.maps[key];var old_map_path=maps["tactical-idle"].path;maps["tactical-idle"].path="res://missing-map-art.png"
	check(Art.valid(ui._map_unit_sprite(hero)),"missing tactical art uses campaign material")
	maps["tactical-idle"].path=old_map_path
	var unknown=hero.duplicate(true);unknown.id="future_class";unknown.class_id=999
	check(Art.valid(ui._map_unit_sprite(unknown)) and Art.valid(ui.battle_animation.sprite(unknown)),"unknown class remains visible using new fallback")
	for id in ["noya","celine"]:check(not ui.Portraits.entry(id).path.begins_with("res://assets/original/"),"new portrait fallback "+id)
	var result={"passed":errors.is_empty(),"checks":checks,"errors":errors,"stages":stage_count,"actors":actor_count,"distinct_resources":paths.size(),"forced_missing_art":true,"audio_unchanged":true,"device_updated":false}
	var f=FileAccess.open(OUT+"fallback-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
	print("CAMPAIGN_ART_FALLBACK ",JSON.stringify(result))
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
