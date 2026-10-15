extends "res://tools/capture_real.gd"
var shots: Array=[]
func shot(name: String,source: String,fixture: bool) -> void:
	ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path="res://reports/border-fixes/"+name+".png";viewport.get_texture().get_image().save_png(path)
	shots.append({"path":path,"source":source,"fixture":fixture,"layout_errors":ui.layout_errors.duplicate(),"canvas":viewport.size})
	print("BORDER_SHOT ",name," ",ui.layout_errors)
func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/border-fixes"))
	viewport=SubViewport.new();viewport.size=Vector2i(384,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	ui.game.save_path="res://reports/campaign/border-visual-fixture-save.json";ui.game.new_game()
	for room in ["P00","H01","H02","H03","H04","H05","H06","H07","H08","H09"]:
		ui.hub_controller.enter_room(room);await shot("hub-"+room,"Directed room-entry fixture",true)
	for code in ["M11","M12","M13","M14","M15","S11","S12"]:
		viewport.size=Vector2i(562,260) if code in ["S11","S12"] else Vector2i(426,240)
		load_checkpoint(code+"-deployment");cursor_to(Vector2i(5,4))
		await shot("battle-"+code,"Real natural-play opening checkpoint; cursor input only",false)
	viewport.size=Vector2i(426,240);load_checkpoint("world-start")
	for node in [1,6,17]:
		ui.game.world_node=node;ui.view="world";ui.game.mode="world"
		ui.world_actor=Vector2(ui.world.nodes[str(node)].position[0],ui.world.nodes[str(node)].position[1])*16
		await shot("world-"+str(node),"Directed camera fixture, actual map layers and node "+str(node),true)
	var errors=[]
	for item in shots:errors.append_array(item.layout_errors)
	var f=FileAccess.open("res://reports/border-fixes/captures.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty() and not abort,"shots":shots,"failures":failures,"background_guard":true,"visible_windows":false,"scope":"Spot checks of 10 hubs, all 7 battle openings, 3 world viewpoints; fixtures explicitly labelled"},"  "));f.close()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit(0 if errors.is_empty() and not abort else 1)
