extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.game.save_path="res://reports/natural-0.1.3/geometry-working.json";ui.game.new_game();ui.instant_mode=true
	var records={}
	for room in ["P00","H01","H02","H03","H04","H05","H06","H07","H08","H09"]:
		ui.hub_controller.enter_room(room);var scenery=[];var objects=[]
		for d in ui.hub_controller.scenery:scenery.append({"name":d.name,"rect":[d.rect.position.x*16,d.rect.position.y*16,d.rect.size.x*16,d.rect.size.y*16]})
		for o in ui.hub_controller.objects:objects.append({"sprite":o.sprite,"position":o.position})
		records[room]={"scenery":scenery,"objects":objects,"map_cells":[14,9],"walk_rect":[16,16,192,112],"exit_rect":[80,112,48,64]}
	var f=FileAccess.open("res://reports/natural-0.1.3/hub-geometry.json",FileAccess.WRITE);f.store_string(JSON.stringify(records,"  "));f.close()
	ui.queue_free();await process_frame;quit()
