extends SceneTree
## Declared turn-three reproduction fixture based on the observed checkpoint.
const State=preload("res://core/game_state.gd")
var viewport
var ui
var shots=[]
var errors=[]
var output="res://reports/m11-overlap-20261020/"
var observed={
	"hunapu":[[9,10],26],"daan":[[10,11],20],"otto":[[10,10],20],
	"M11_boss":[[16,4],32],"M11_e1":[[10,11],0],"M11_e2":[[10,11],0],
	"M11_e3":[[11,11],0],"M11_e4":[[10,9],0],"M11_e5":[[9,9],20],
	"M11_e6":[[9,9],0],"M11_e7":[[10,7],20],"M11_e8":[[11,11],11],
	"M11_e9":[[10,9],12],"M11_refugees0":[[9,12],24],"M11_refugees1":[[9,12],21]}
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name: String):
	ui.layout_errors.clear();ui.text_checks.clear();ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var img=viewport.get_texture().get_image();img.save_png(output+name+".png")
	shots.append({"name":name,"size":[viewport.size.x,viewport.size.y],"layout_errors":ui.layout_errors.duplicate(),"units":ui.game.units.filter(func(u):return u.get("neutral",false)).map(func(u):return {"id":u.id,"position":u.position,"hp":u.hp})})
	errors.append_array(ui.layout_errors)
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(1152,744);viewport.size_2d_override=Vector2i(384,248);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=2
	ui.game.new_game();ui.game.world_node=2;ui.game.start_battle(101)
	for u in ui.game.units:
		if not observed.has(str(u.id)):continue
		u.position=observed[str(u.id)][0].duplicate();u.hp=observed[str(u.id)][1];u.acted=false
	ui.game.turn=3;ui.game.phase="player";ui.game.flags.quest.reinforced=false;ui.game.story_events.clear()
	ui.game.cursor=Vector2i(14,11);ui.game.save_path="/private/tmp/m11-overlap-visual-checkpoint.json";ui.game.save_game()
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.phase_time=0;ui.notice_time=0;ui._clear_menu();ui._focus_battle(ui.game.cursor,true)
	await shot("01-before-overlap")
	if not ui.game.load_game():errors.append("Reproduction checkpoint could not reload")
	await shot("02-after-recovery")
	ui.game.cursor=State.pos(ui.game.find_unit("M11_refugees1"));ui._focus_battle(ui.game.cursor,true)
	await shot("03-recovered-escort-card")
	var report={"passed":errors.is_empty(),"errors":errors,"background_guard":true,"visible_windows":false,"fixture":"Original turn-three observed positions/HP reconstructed in an independent checkpoint; not a live user-save edit","shots":shots}
	var file=FileAccess.open(output+"visual.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("M11_OVERLAP_VISUAL ",JSON.stringify(report));ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
