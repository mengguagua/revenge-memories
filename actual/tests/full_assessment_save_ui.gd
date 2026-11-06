extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/full-assessment-20261025/save/"
var ui
var screen
var checks=[]
var failures=[]
var layouts=[]
var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func key(code:int):
	var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
	e=InputEventKey.new();e.physical_keycode=code;e.pressed=false;ui._input(e)
func run():
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	var cache="/private/tmp/revenge-save-ui-"+str(Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(cache);DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var g=State.new();g.slot_directory=cache;g.new_game();g.flags.recovery_marker=31;check(g.save_to_slot(1),"seed first UI journal")
	g.flags.recovery_marker=32;check(g.save_game(),"rotate first UI recovery copy")
	var damaged="interrupted outside the atomic writer";var f=FileAccess.open(g.save_path,FileAccess.WRITE);f.store_string(damaged);f.close()
	screen=SubViewport.new();screen.size=Vector2i(256,240);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=cache;screen.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.elapsed=4;ui.instant_mode=true
	ui._show_title();check(ui.title_selected==1,"valid recovery copy enables Continue on homepage")
	key(KEY_Z);check(ui.view=="journal" and ui.journey.records[0].get("recovered",false),"normal confirm opens slot picker with visible recovery record")
	for width in [256,364]:
		screen.size=Vector2i(width,240);ui.set_meta("phone",width==364);ui.elapsed=8
		ui.queue_redraw();await process_frame;await process_frame
		if visual:await RenderingServer.frame_post_draw
		if visual:
			check(ui.layout_errors.is_empty(),"recovery row glyphs stay in content-safe area at "+str(width))
			check(ui.journey.audit.any(func(item):return str(item.text).begins_with("恢复副本")),"recovery provenance is actually drawn at "+str(width))
			layouts.append({"width":width,"audit":ui.journey.audit.duplicate(true),"errors":ui.layout_errors.duplicate()})
			screen.get_texture().get_image().save_png(OUT+"recovery-"+str(width)+".png")
	ui.journey.selected=0;key(KEY_Z);await process_frame
	check(ui.game.active_slot==1 and int(ui.game.flags.get("recovery_marker",0))==31,"normal slot confirmation restores exactly the recovery checkpoint")
	check(ui.notice.contains("恢复副本"),"successful recovery has explicit player feedback")
	check(FileAccess.get_file_as_string(g.save_path)==damaged,"reading the backup leaves primary bytes intact")
	check(ui.game.save_game(),"first normal save after recovery succeeds")
	check(FileAccess.get_file_as_string(g.save_path+".damaged-"+damaged.sha256_text().left(16))==damaged,"first normal save retains damaged original")
	var report={"passed":failures.is_empty(),"checks":checks,"failures":failures,"visual":visual,"layouts":layouts,"isolated_directory":cache,"scope":"Actual homepage and slot input plus native 256/364px layouts; no device touch or install."}
	f=FileAccess.open(OUT+("ui-visual-checks.json" if visual else "ui-checks.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("SAVE_UI ",checks.size()," checks; failures: ",failures)
	ui.queue_free();screen.queue_free();await process_frame;quit(0 if failures.is_empty() else 1)
