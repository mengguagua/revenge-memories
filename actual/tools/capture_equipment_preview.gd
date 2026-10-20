extends SceneTree
var ui
var viewport
var shots=[]
var errors=[]
const OUT="res://reports/equipment-preview-20261020/"
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name: String):
	ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	var snapshot={"name":name,"size":[viewport.size.x,viewport.size.y],"view":ui.view,"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.equipment_screen.audit.duplicate(true)}
	shots.append(snapshot);errors.append_array(ui.layout_errors)
func open_for(item_id: int,id: String):
	ui.view="world";ui._clear_menu();ui.game.convoy.alm=[item_id];ui._camp_action("withdraw_item:0")
	ui.equipment_screen.selected=ui.equipment_screen.members.find(id);ui.equipment_screen.accept()
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=3
	ui.game.new_game();ui.game.mode="world";ui.game.world_node=32;ui.game.save_path="/private/tmp/equipment-preview-capture.json"
	for id in ["fula","lena","lance","beck","hervi"]:ui.game.recruit(id)
	ui.world_actor=Vector2(ui.world.nodes["32"].position[0],ui.world.nodes["32"].position[1])*16
	ui.view="world";ui.game.convoy.alm=[20];ui._camp_action("withdraw_item:0")
	await shot("01-members-wide")
	ui.game.roster.daan.item_id=64;open_for(20,"daan");await shot("02-bow-gains-and-losses")
	open_for(62,"hunapu");await shot("03-incompatible")
	open_for(49,"hunapu");await shot("04-shield-tradeoff")
	ui.game.roster.hervi.item_id=65;open_for(66,"hervi");await shot("05-focus-tradeoff")
	open_for(55,"hunapu");ui.equipment_screen.more=true;await shot("06-special-effects")
	viewport.size=Vector2i(768,720);viewport.size_2d_override=Vector2i(256,240)
	ui.view="world";ui.game.convoy.alm=[20];ui._camp_action("withdraw_item:0");await shot("07-members-compact")
	ui.equipment_screen.selected=7;ui.equipment_screen.first=3;await shot("08-members-second-page")
	open_for(20,"daan");await shot("09-comparison-compact")
	open_for(62,"hunapu");await shot("10-incompatible-compact")
	open_for(55,"hunapu");ui.equipment_screen.more=true;await shot("11-effects-compact")
	# All available roster/equipment combinations exercise real text and values
	# at the narrowest viewport, including long personal names and large rings.
	var probes=0
	for item_id in [7,14,15,17,18,20,49,51,52,53,55,56,57,58,65,66]:
		for id in ui.game.party:
			open_for(item_id,str(id));ui.equipment_screen.more=true;ui.queue_redraw()
			await process_frame;await RenderingServer.frame_post_draw
			for error in ui.layout_errors:errors.append(str(item_id)+"/"+str(id)+": "+error)
			probes+=1
	var report={"passed":errors.is_empty(),"errors":errors,"background_guard":true,"visible_windows":false,"fixtures":true,"user_saves_touched":false,"compact_details_probes":probes,"shots":shots}
	var file=FileAccess.open(OUT+"visual.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("EQUIPMENT_VISUAL ",JSON.stringify({"passed":errors.is_empty(),"errors":errors,"shots":shots.size(),"probes":probes}));ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
