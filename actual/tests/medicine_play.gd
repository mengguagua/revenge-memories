extends "res://tests/round3.gd"
## Targeted re-play after correcting cargo identity; earlier victories preserved.
func run() -> void:
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.game.save_path="res://reports/campaign/natural-S12-deployment-save.json"
	if not ui.game.load_game():record_failure("Cannot load real S12 deployment")
	ui.game.save_path="res://reports/campaign/medicine-progress.json";ui.instant_mode=true;ui.view=ui.game.mode
	ui._focus_battle(ui.game.cursor,true)
	var cargo=ui.game.find_unit("medicine_wagon")
	if not cargo.get("event_object",false) or not cargo.get("no_counter",false):record_failure("Cargo classification missing")
	await battle(false)
	var report={"scope":"Actual S12 input replay after cargo rendering/counter correction, from its real first-turn save","passed":not abort,"failures":failures,"inputs":inputs,"battles":battles,"operations":operations,"stat_edits":false,"forced_victories":false}
	var f=FileAccess.open("res://reports/campaign/medicine-play.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("MEDICINE_PLAY ",JSON.stringify({"passed":not abort,"turn":ui.game.turn,"inputs":inputs,"failures":failures}))
	ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
