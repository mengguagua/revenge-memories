extends SceneTree
var viewport
var phone
var errors: Array = []
var shots: Array = []
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1": quit(1);return
	call_deferred("run")
func shot(name: String):
	await process_frame
	phone.queue_redraw();phone.game_ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("res://reports/ios-20261022/"+name+".png")
	var issues = phone.layout_errors.duplicate() + phone.game_ui.layout_errors.duplicate()
	shots.append({"name":name,"errors":issues,"game_rect":str(phone.game_rect),"pixel_scale":phone.pixel_scale,"buttons":phone.buttons.size()})
	errors.append_array(issues)
func run():
	viewport = SubViewport.new();viewport.size = Vector2i(2556,1179)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	phone = load("res://scenes/phone.tscn").instantiate();viewport.add_child(phone);await process_frame
	var ui = phone.game_ui;ui.game.slot_directory = "/private/tmp/revenge-ios-capture-slots"
	ui.game.save_path = "/private/tmp/revenge-ios-capture-unused.json";ui.journey.refresh()
	await shot("phone-title")
	ui.journey.open("new");await shot("phone-slots")
	ui.game.new_game();ui.game.slot_directory = "/private/tmp/revenge-ios-capture-slots"
	ui.game.save_path = "/private/tmp/revenge-ios-capture-unused.json"
	ui.hub_controller.enter_room("P00",false,false);await shot("phone-prologue")
	ui.game.world_node = int(ui.game.stages[101].node);ui.game.start_battle(101)
	ui.game.story_events.clear();ui.view = "battle";ui.ui_mode = "inspect";ui.busy = false;ui.notice_time = 0;ui.phase_time = 0
	ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true);await shot("phone-battle")
	viewport.size = Vector2i(1334,750);await process_frame;phone._layout();await shot("phone-small-landscape")
	var f = FileAccess.open("res://reports/ios-20261022/visual-checks.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors},"  "));f.close()
	print("PHONE_VISUAL ",shots.size()," ",errors)
	phone.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
