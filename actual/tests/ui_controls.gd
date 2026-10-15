extends "res://tests/round3.gd"
## Additional menu/rapid-input checks using the completed natural save.
var checks: Array=[]
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:record_failure(label)
func run() -> void:
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.instant_mode=true;ui.game.save_path="res://reports/campaign/natural-chapter-end-save.json"
	key(KEY_Z);key(KEY_DOWN);key(KEY_Z);await settle()
	check(ui.view=="chapter_end","title continue restores chapter end")
	ui.game.save_path="res://reports/campaign/ui-controls-save.json"
	key(KEY_Z);choose("new:world");check(ui.view=="world","chapter menu can return to map")
	key(KEY_S);choose("new:camp");choose(str(ui.menu_actions[0]));choose(str(ui.menu_actions[0]));await settle()
	check(ui.view=="camp_status" and ui.status_id=="hunapu","camp opens actual character status")
	key(KEY_X);check(ui.view=="world","status cancel restores world")
	ui.hub_controller.enter_room("H04");await hub_action("shrine")
	check(ui.menu_actions.has("hub:promote_daan_13"),"real level7 archer meets original promotion threshold")
	choose("hub:promote_daan_13");check(int(ui.game.roster.daan.class_id)==13 and int(ui.game.roster.daan.move)==5,"promotion uses original class and movement")
	check(bool(ui.game.roster.fula.dead) and bool(ui.game.roster.lena.dead),"optional menu does not revive real casualties")
	ui.game.new_game();ui.hub_controller.enter_room("H08");await hub_action("beck");choose("hub:recruit_beck");await settle()
	await leave_hub();ui.game.world_node=32;ui.game.start_battle(112);ui._begin_existing_battle();await settle()
	for i in range(8):await process_frame
	check(ui.view=="battle" and ui.game.mode=="battle","rapid recruit transition cannot switch battle back to hub")
	var f=FileAccess.open("res://reports/campaign/ui-controls.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"errors":failures,"passed":not abort,"scope":"Menu and transition checks on QA copy of real end save; promotion does not alter original play records"},"  "));f.close()
	print("UI_CONTROLS ",JSON.stringify({"passed":not abort,"checks":checks.size(),"failures":failures}))
	ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
