extends "res://tests/polish_play.gd"
## Explicit render fixtures: all portrait slots and minimum/landscape popup positions.
## Natural key-driven battle victories are recorded separately by polish_play.gd.
const Portraits=preload("res://core/portrait_library.gd")
var visual_records=[]
func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	review_out="res://reports/playtest-0.5.0/visual/"
	call_deferred("run")
func render_image() -> Image:
	ui.queue_redraw()
	for frame in range(4):await process_frame
	await RenderingServer.frame_post_draw
	return viewport.get_texture().get_image()
func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(review_out))
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	ui.game.save_path="res://.cache/playtest-0.5.0/visual.json";ui.game.new_game();ui.game.world_node=2;ui.game.start_battle(101)
	ui.view="battle";ui.phase_time=0;ui.notice_time=0;ui.busy=false;ui.ui_mode="inspect";ui._clear_menu()
	var real_units=ui.game.units.duplicate(true)
	for key_ in Portraits.data().assets:
		var actor=real_units.filter(func(u):return u.id=="M11_boss")[0].duplicate(true)
		actor.id=key_;actor.name_zh="画像预览";ui.game.characters[key_]=actor.duplicate(true);ui.game.units=[actor];ui.status_id=key_;ui.view="battle";ui.ui_mode="status"
		var frame=await render_image();var at=Vector2i(ui._canvas_offset())+Vector2i(24,40)
		var expected=load(Portraits.entry(key_).path).get_image();var differences=0
		for y in range(48):
			for x in range(48):
				if frame.get_pixel(at.x+x,at.y+y)!=expected.get_pixel(x,y):differences+=1
		frame.save_png(review_out+key_+"-status.png")
		visual_records.append({"name":key_,"fixture":true,"kind":"actual status renderer, catalogue identity override only","pixel_differences":differences,"pixels":2304,"layout_errors":ui.layout_errors.duplicate(),"path":review_out+key_+"-status.png"})
		if differences>0:record_failure("Portrait differs from approved native asset: "+key_+" "+str(differences))
		if not ui.layout_errors.is_empty():record_failure("Status safety: "+key_)
	ui.game=State.new();ui.game.new_game();ui.game.save_path="res://.cache/playtest-0.5.0/visual.json";ui.game.world_node=2;ui.game.start_battle(101);ui.view="battle";ui.ui_mode="inspect"
	for width in [256,426]:
		viewport.size=Vector2i(width,240);await process_frame
		for actor in ui.game.living("player")+ui.game.living("enemy"):
			ui.game.cursor=State.pos(actor);ui._focus_battle(ui.game.cursor,true)
			var frame=await render_image();var audit=ui.battle_card_audit.duplicate(true)
			var path=review_out+str(width)+"-focus-"+str(actor.id)+".png";frame.save_png(path)
			visual_records.append({"name":str(width)+"-focus-"+str(actor.id),"fixture":true,"kind":"fresh deployment, real camera and card","card":audit,"layout_errors":ui.layout_errors.duplicate(),"path":path})
			if not ui.layout_errors.is_empty() or not audit.get("valid",false):record_failure("Focus safety: "+str(width)+":"+str(actor.id))
	var report={"passed":failures.is_empty(),"background_guard":true,"visible_windows":false,"failures":failures,"records":visual_records,"scope":"Explicit visual fixtures, actual status renderer with catalogue identity override; exact 2304-pixel asset comparison each. Popup checks use fresh normal deployment. Not counted as natural victories."}
	var f=FileAccess.open(review_out+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	ui.hub_controller.dispose();ui.hub_controller=null;ui.free();viewport.queue_free();await process_frame;quit(0 if report.passed else 1)
