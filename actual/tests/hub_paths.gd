extends "res://tests/round3.gd"
func run() -> void:
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.game.save_path="res://reports/campaign/hub-paths-save.json";ui.game.new_game();ui.instant_mode=true
	var count=0
	for room in ["P00","H01","H02","H03","H04","H05","H06","H07","H08","H09"]:
		ui.hub_controller.enter_room(room)
		for object in ui.hub_controller.objects:
			ui.game.hub_position=Vector2i(6,7)
			await walk_to(Vector2i(object.position[0],object.position[1])+Vector2i.DOWN)
			count+=1
			if abort:break
		if abort:break
	var f=FileAccess.open("res://reports/campaign/hub-paths.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"objects_checked":count,"failures":failures,"scope":"Directed room spawn fixtures, all movement performed with actual input; intact scenery footprints block walking"},"  "));f.close()
	print("HUB_PATHS ",JSON.stringify({"passed":not abort,"objects":count,"failures":failures}))
	ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
