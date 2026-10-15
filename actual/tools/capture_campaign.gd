extends SceneTree
var ui
var viewport
var shots=[]
func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name: String) -> void:
	ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path="res://reports/campaign/qa-"+name+".png"
	viewport.get_texture().get_image().save_png(path)
	shots.append({"path":path,"view":ui.view,"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(),"fixture":true})
func run() -> void:
	viewport=SubViewport.new();viewport.size=Vector2i(256,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.game.save_path="res://reports/campaign/qa-capture-save.json";ui.instant_mode=true
	await shot("title")
	ui._new_game();await shot("prologue")
	ui.hub_controller.enter_room("H01");await shot("snow-village")
	ui.game.flags.village_ready=true;ui._continue_world();await shot("world-start")
	ui.game.world_node=2;ui.game.start_battle(101);ui.view="battle";ui.ui_mode="inspect";ui._focus_battle(ui.game.cursor,true);await shot("M11-deploy")
	ui._battle_accept();await shot("M11-move")
	ui.game.selected_id="";ui.game.world_node=4;ui.game.start_battle(103);ui.view="battle";ui.ui_mode="inspect";ui.game.cursor=Vector2i(6,4);ui._focus_battle(ui.game.cursor,true);await shot("M13-jail")
	ui.game.world_node=6;ui.game.start_battle(105);ui.view="battle";ui.ui_mode="inspect";ui.game.cursor=Vector2i(16,5);ui._focus_battle(ui.game.cursor,true);await shot("M15-citadel")
	ui.game.hub_record="H06";ui.hub_controller.resume();await shot("tower-altar")
	ui.view="chapter_end";await shot("chapter-end")
	var f=FileAccess.open("res://reports/campaign/round2-visual.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"round":2,"scope":"Actual Godot rendering from declared QA scene fixtures, not natural combat saves","shots":shots,"background_guard":true,"visible_windows":false},"  "));f.close()
	ui.queue_free();await process_frame;quit()
