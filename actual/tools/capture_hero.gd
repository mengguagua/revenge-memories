extends "res://tools/capture_real.gd"
func key(code: int) -> void:
	# Walk and finish unrelated exchanges immediately; retain the actual hero
	# animation only after the player confirms its legal target preview.
	if code==KEY_Z and ui!=null and ui.view=="battle" and ui.ui_mode=="target" and ui.game.selected_id=="hunapu" and not duel_seen:
		ui.instant_mode=false
	super.key(code)
func watch_exchange() -> void:
	if ui!=null and ui.view=="combat" and not duel_seen and (ui.combat.get("attacker","")=="hunapu" or ui.combat.get("defender","")=="hunapu"):
		duel_seen=true;capture_exchange()
func capture_exchange() -> void:
	await real_shot("08-hunapu-combat","Live hero exchange reached through actual input from real S12 opening")
	ui.instant_mode=true
func run() -> void:
	viewport=SubViewport.new();viewport.size=Vector2i(256,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	load_checkpoint("S12-deployment");ui.instant_mode=true;process_frame.connect(watch_exchange)
	for pass_ in range(12):
		if duel_seen or abort:break
		var turn_=ui.game.turn
		for id in ui.game.party.duplicate():
			if duel_seen or abort or ui.game.turn!=turn_:break
			await act(str(id))
		if not duel_seen and not abort and ui.game.turn==turn_:key(KEY_S);choose("end_turn");await settle()
	process_frame.disconnect(watch_exchange)
	for i in range(6):await process_frame
	var report=State.read_json("res://reports/campaign/real-screenshots.json")
	for shot in real_shots:report.shots.append(shot)
	var f=FileAccess.open("res://reports/campaign/real-screenshots.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit(0 if duel_seen and not abort else 1)
