extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui)
	await process_frame
	ui.game.save_path="res://reports/campaign/probe-save.json"
	print("PROBE_TITLE=",ui.view," STAGES=",ui.game.stages.size()," NODES=",ui.world.nodes.size())
	ui.game.new_game();ui._new_journey_in_slot();await process_frame
	print("PROBE_NEW=",ui.view," ROOM=",ui.game.hub_record," PARTY=",ui.game.party)
	ui.queue_free();await process_frame;quit()
