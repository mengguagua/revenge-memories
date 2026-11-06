extends "res://tools/capture_lightning_refine.gd"
const REUSE_OUT="res://reports/thunder-reuse-20261026/"
func shot(name:String,tick:int):
	for i in range(8):ui.queue_redraw();await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(REUSE_OUT+name+".png")
	for issue in ui.layout_errors:errors.append(name+": "+str(issue))
	shots.append({"file":name+".png","tick":tick,"variant":ui.battle_animation.active_variant,"layout_errors":ui.layout_errors.duplicate()})
func reuse_impact(selected:Dictionary)->int:
	for n in range(selected.variant.frames.size()):
		for effect in selected.variant.frames[n].get("effects",[]):
			if str(Effects.graphic(str(effect.sprite),str(selected.key)).get("path","")).ends_with("bolt-ground.png"):return n
	return int(selected.variant.contact_tick)
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(1280,960);viewport.size_2d_override=Vector2i(320,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/thunder-reuse-slots";ui.game.save_path="/private/tmp/thunder-reuse-save.json";viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4;ui.game.new_game()
	var bindings=0;var variants=0
	for row in Effects.data().variants.values():
		var found=false
		for art in row.values():
			if art.get("campaign_lightning_reuse","")!="":bindings+=1;found=true;check(ResourceLoader.exists(art.path),"missing reused art "+str(art.path))
			check(not str(art.path).contains("/lightning-refine-20261026/"),"newly generated lightning retired")
		if found:variants+=1
	check(bindings==504 and variants==72,"all electrical weapon variants reuse approved Thunder")
	var event=setup();var selected=ui.battle_animation.selection(event);check(selected.kind=="source","electrical sword selection")
	var tick=reuse_impact(selected);var current=Effects.data().variants
	Effects.data().variants=JSON.parse_string(FileAccess.get_file_as_string(REUSE_OUT+"before-campaign-effects.json")).variants
	ui.battle_animation.show_frame(event,tick);await shot("01-before-generated",tick)
	Effects.data().variants=current;ui.battle_animation.show_frame(event,tick);await shot("02-reused-existing",tick)
	event=setup(true,true);selected=ui.battle_animation.selection(event);check(selected.kind=="source","opposite ranged selection");tick=reuse_impact(selected)
	ui.battle_animation.show_frame(event,tick);await shot("03-enemy-ranged",tick)
	# The exact mage/spell shown by the user keeps its existing reviewed timeline.
	event=setup();ui.game.units[0].class_id=15;ui.game.units[0].name_zh=ui.game.catalog.classes["15"].name_zh;event.weapon_index=24
	selected=ui.battle_animation.selection(event);check(selected.kind=="source","existing mage Thunder selection");tick=int(selected.variant.contact_tick)
	ui.battle_animation.show_frame(event,tick);await shot("04-mage-thunder-impact",tick)
	ui.battle_animation.show_frame(event,tick+9);await shot("05-mage-thunder-branch",tick+9)
	var f=FileAccess.open(REUSE_OUT+"visual-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"shots":shots,"texture_bindings":bindings,"variants":variants,"guarded_background":true,"device_updated":false},"  "))
	print("THUNDER_REUSE ",shots.size()," shots; errors: ",errors)
	ui.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
