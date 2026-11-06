extends SceneTree
## Targeted visual check; deliberately does not replay the full campaign.
const OUT="res://reports/lightning-refine-20261026/"
const Effects=preload("res://core/campaign_effects.gd")
var ui
var viewport
var shots=[]
var errors=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func check(ok:bool,message:String):
	if not ok:errors.append(message)
func shot(name:String,tick:int):
	for i in range(8):ui.queue_redraw();await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	for issue in ui.layout_errors:errors.append(name+": "+str(issue))
	shots.append({"file":name+".png","tick":tick,"variant":ui.battle_animation.active_variant,"layout_errors":ui.layout_errors.duplicate()})
func setup(enemy:bool=false,far:bool=false)->Dictionary:
	var a=ui.game.characters.hunapu.duplicate(true);a.id="fixture_actor";a.class_id=8 if enemy else 21;a.side="enemy" if enemy else "player";a.hp=28;a.max_hp=28;a.position=[4,4];a.name_zh="剑豪" if enemy else "胡纳普"
	var b=a.duplicate(true);b.id="fixture_target";b.class_id=6;b.side="player" if enemy else "enemy";b.name_zh="士兵";b.position=[5,4]
	ui.game.units=[a,b];ui.view="combat";ui.combat={"attacker":a.id,"defender":b.id,"distance":2 if far else 1,"initiative_side":a.side};ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.combat_message="";ui.combat_hit_id="";ui.battle_animation.reset()
	return {"attacker":a.id,"defender":b.id,"weapon_index":15,"critical":false,"hit":true,"hp_before":28,"hp_after":26}
func impact_tick(selected:Dictionary)->int:
	for n in range(selected.variant.frames.size()):
		for effect in selected.variant.frames[n].get("effects",[]):
			var art=Effects.graphic(str(effect.sprite),str(selected.key))
			if str(art.get("path","")).ends_with("lightning-4.png"):return n
	return int(selected.variant.contact_tick)
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(1280,960);viewport.size_2d_override=Vector2i(320,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/lightning-refine-slots";ui.game.save_path="/private/tmp/lightning-refine-save.json";viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4;ui.game.new_game()
	var bindings=0;var variants=0
	for key in Effects.data().variants:
		var used=false
		for art in Effects.data().variants[key].values():
			if str(art.path).begins_with("res://assets/lightning-refine-20261026/"):
				bindings+=1;used=true;check(ResourceLoader.exists(art.path),"missing "+str(art.path))
		if used:variants+=1
	check(bindings==504 and variants==72,"all 72 lightning variants use the new textures")
	var event=setup();var selected=ui.battle_animation.selection(event)
	check(selected.kind=="source","normal lightning selection")
	var tick=impact_tick(selected)
	# Render the previous material at the identical body/timeline frame for comparison.
	for row in Effects.data().variants.values():
		for art in row.values():art.path=str(art.path).replace("/lightning-refine-20261026/","/fallback-effects-20261026/")
	check(ui.battle_animation.show_frame(event,tick),"before frame");await shot("01-before-contact",tick)
	for row in Effects.data().variants.values():
		for art in row.values():art.path=str(art.path).replace("/fallback-effects-20261026/lightning-","/lightning-refine-20261026/lightning-")
	check(ui.battle_animation.show_frame(event,tick),"after frame");await shot("02-after-contact",tick)
	var seen={}
	for n in range(selected.variant.frames.size()):
		for effect in selected.variant.frames[n].get("effects",[]):
			var art=Effects.graphic(str(effect.sprite),str(selected.key));var path=str(art.get("path",""))
			if not path.begins_with("res://assets/lightning-refine-20261026/") or seen.has(path):continue
			seen[path]=true
			if path.ends_with("lightning-3.png") or path.ends_with("lightning-5.png"):
				ui.battle_animation.show_frame(event,n);await shot("03-phase-"+path.get_file().get_basename(),n)
	event=setup(true,true);selected=ui.battle_animation.selection(event);check(selected.kind=="source","opposite side ranged lightning selection")
	tick=impact_tick(selected);ui.battle_animation.show_frame(event,tick);await shot("04-enemy-ranged-contact",tick)
	var f=FileAccess.open(OUT+"visual-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"shots":shots,"texture_bindings":bindings,"variants":variants,"guarded_background":true,"device_updated":false},"  "))
	print("LIGHTNING_REFINE ",shots.size()," shots; errors: ",errors)
	ui.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
