extends SceneTree
const OUT="/Users/gcc/gaocc/project/revenge-memories/officialWebsite/source/captures/"
const Effects=preload("res://core/campaign_effects.gd")
const Catalog=preload("res://tools/map_catalog_canvas.gd")
class WebsiteCatalog extends "res://tools/map_catalog_canvas.gd":
	func _tex(path:String)->Texture2D:
		assert(not path.begins_with("res://assets/original/"))
		if not textures.has(path):textures[path]=load(path)
		return textures[path]
var viewport
var ui
var shots=[]
var errors=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name:String,scope:String):
	for i in range(6):await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	shots.append({"name":name,"size":[viewport.size.x,viewport.size.y],"scope":scope,"layout_errors":ui.layout_errors.duplicate() if ui!=null else []})
	print("WEBSITE_EXPANSION ",name)
func run():
	viewport=SubViewport.new();viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	viewport.size=Vector2i(1280,960);viewport.size_2d_override=Vector2i(320,240);viewport.size_2d_override_stretch=true
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/website-expansion-unused-slots";viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.game.new_game();ui.game.save_path="/private/tmp/website-expansion-working.json";ui.elapsed=4
	var actor=ui.game._initial_character("hunapu");ui.game.HeroProfessions.apply(actor);actor.hp=actor.max_hp;actor.position=[4,4];actor.weapon_index=15;actor.held_item=15
	var target=ui.game.stages[533].enemies[1].duplicate(true);target.id="website-bastion";target.name_zh="壁垒卫士";target.class_id=22;target.side="enemy";target.position=[6,4];target.hp=40;target.max_hp=40
	ui.game.units=[actor,target];ui.view="combat";ui.combat={"attacker":actor.id,"defender":target.id,"distance":2,"initiative_side":"player"};ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.battle_animation.reset()
	var event={"attacker":actor.id,"defender":target.id,"weapon_index":15,"critical":false,"hit":true,"hp_before":40,"hp_after":30}
	var selected=ui.battle_animation.selection(event)
	if selected.get("kind","")!="source":errors.append("No promoted electrical sword animation")
	else:
		var impact=int(selected.variant.contact_tick)
		for n in range(selected.variant.frames.size()):
			for effect in selected.variant.frames[n].get("effects",[]):
				if str(Effects.graphic(str(effect.sprite),str(selected.key)).get("path","")).ends_with("bolt-ground.png"):impact=n;break
		ui.battle_animation.active_event=event;ui.battle_animation.show_frame(event,impact)
		await shot("dawn-thunder","Current PC battle renderer; isolated visual fixture: promoted Hunapu, electrical sword 15, enemy Bastion Guard 22; approved effect frame "+str(impact))
		shots[-1].animation={"character_id":"hunapu","profession":"dawn_warrior","weapon":15,"target_class":22,"tick":impact,"variant":selected.key}
	# Full world textures are rendered by the PC engine without a UI overlay.
	ui.hide();viewport.size_2d_override=Vector2i.ZERO;viewport.size_2d_override_stretch=false
	var rect=TextureRect.new();viewport.add_child(rect);rect.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	for chapter in [1,2,3,4,5]:
		ui.game.chapter=chapter;ui.game.flags={};
		var texture=ui._world_overview_texture();rect.texture=texture;rect.size=texture.get_size();viewport.size=Vector2i(texture.get_size())
		await shot("atlas-"+str(chapter),"Current PC full-world terrain texture rendered in Godot; chapter "+str(chapter)+" initial environment; no UI or invented landmarks")
	rect.queue_free();ui.queue_free();await process_frame;ui=null
	var canvas=WebsiteCatalog.new();viewport.add_child(canvas);await process_frame
	for id in [105,205,303,306,401,407,533,534]:
		canvas.prepare(id);viewport.size=Vector2i(int(canvas.game.battle_data.map.width)*16+64,int(canvas.game.battle_data.map.height)*16+64);canvas.size=Vector2(viewport.size)
		await shot("map-"+str(canvas.game.battle_data.code),"Current PC terrain and architecture renderer, full tactical map; scenery only, stage "+str(canvas.game.battle_data.code))
	canvas.queue_free();await process_frame
	var f=FileAccess.open(OUT+"expansion-report.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"shots":shots,"background_guard":true,"visible_windows":false,"user_saves_touched":false,"game_source_modified":false},"  "));f.close()
	quit(0 if errors.is_empty() else 1)
