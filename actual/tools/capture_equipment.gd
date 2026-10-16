extends "res://tools/capture_player_feedback.gd"
## Legal input from genuine checkpoints, rendered in a guarded offscreen viewport.
const EQUIPMENT_SHOTS = "res://reports/equipment-0.3.9/screenshots/"

func shot(name: String, source: String) -> void:
	ui.queue_redraw()
	for i in range(4): await process_frame
	await RenderingServer.frame_post_draw
	var path=EQUIPMENT_SHOTS+name+".png"
	viewport.get_texture().get_image().save_png(path)
	feedback_shots.append({"name":name,"path":path,"source":source,"fixture":false,"view":ui.view,"stage":ui.game.stage_id,"status_id":ui.status_id,"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(true)})
	for entry in ui.text_checks:
		for hidden_rule in ["必掉","随机掉落","掉落率","10%","装备池","保底","极低概率"]:
			if hidden_rule in str(entry.text): record_failure("Hidden loot rule exposed in "+name+": "+str(entry.text))
	print("EQUIPMENT_SHOT ",name," ",ui.layout_errors)

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(EQUIPMENT_SHOTS))
	review_out="res://.cache/equipment-capture/"; DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(review_out))
	viewport=SubViewport.new(); viewport.size=Vector2i(426,240); viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS; root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate(); viewport.add_child(ui); await process_frame; ui.instant_mode=true
	await current_stage("M11")
	cursor_to(State.pos(ui.game.find_unit("hunapu"))); key(KEY_TAB)
	await shot("01-west-bronze-sword","Genuine M11 deployment, ordinary preparation/re-entry, status input")
	key(KEY_X)
	var enemy=ui.game.find_unit("M11_e5"); cursor_to(State.pos(enemy)); ui._focus_battle(ui.game.cursor,true); key(KEY_TAB)
	await shot("02-enemy-bow-drop","Actual M11 archer status: current copper bow only, no loot guarantee")
	key(KEY_X)
	enemy=ui.game.find_unit("M11_e1");cursor_to(State.pos(enemy));ui._focus_battle(ui.game.cursor,true);key(KEY_TAB)
	await shot("06-unheld-random-drop","Actual M11 soldier status: no carried equipment, no drop-rate explanation")
	key(KEY_X)
	source_load("res://reports/campaign/natural-chapter-end-save.json"); key(KEY_Z); choose("new:chapter2"); await settle()
	key(KEY_TAB); choose("camp:status:eileen")
	await shot("03-east-iron-sword","Normal chapter-two transition; Eileen starts with iron sword")
	key(KEY_RIGHT)
	await shot("04-healer-copper-focus","Right-key member cycle; Mireille starts with copper focus")
	key(KEY_X)
	await current_stage("M15")
	key(KEY_S); choose("new:prepare"); await settle(); key(KEY_S); choose("new:camp"); choose("camp:convoy"); choose("camp:withdraw")
	await shot("05-west-reserve-weapons","Actual late-first-chapter save migrated at preparation boundary; real convoy menu")
	key(KEY_X); key(KEY_S); choose("new:camp"); choose("new:equipment")
	if ui.view!="plot" or ui.plot_pages.size()!=4: record_failure("Equipment help should contain four operational pages")
	for i in range(ui.plot_pages.size()):
		key(KEY_Z)
		await shot("07-equipment-help-"+str(i+1),"Equipment help reached through preparation menu; operational information only")
		key(KEY_Z)
	if ui.view!="world":record_failure("Equipment help did not return to the world")
	var layout: Array=[]
	for capture in feedback_shots: layout.append_array(capture.layout_errors)
	var report={"version":"0.3.9","presentation_revision":"hide-loot-hints","passed":not abort and layout.is_empty(),"shots":feedback_shots,"layout_errors":layout,"failures":failures,"background_guard":true,"visible_windows":false,"scope":"Text-only presentation correction. Actual keyboard status/help checks from genuine checkpoints; all four help pages checked for hidden loot rules and text safety. No new full battle playthrough and no capture-side item/stat/position edits."}
	var f=FileAccess.open("res://reports/equipment-0.3.9/captures.json",FileAccess.WRITE); f.store_string(JSON.stringify(report,"  ")); f.close()
	ui.queue_free(); await process_frame; quit(0 if report.passed else 1)
