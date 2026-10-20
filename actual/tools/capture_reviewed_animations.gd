extends SceneTree
const Reviewed = preload("res://core/reviewed_animations.gd")
var ui
var viewport
var out = "res://reports/animation-test-20261018/visual/"
var shots: Array = []
var errors: Array = []
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1": quit(1);return
	call_deferred("run")
func shot(name: String):
	ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(out + name + ".png")
	shots.append({"name": name, "layout_errors": ui.layout_errors.duplicate()})
	if not ui.layout_errors.is_empty(): errors.append({"shot": name, "errors": ui.layout_errors.duplicate()})
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	viewport = SubViewport.new();viewport.size = Vector2i(1704, 960);viewport.size_2d_override = Vector2i(426, 240)
	viewport.size_2d_override_stretch = true;viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.new_game();ui.game.save_path = "/private/tmp/reviewed-animation-capture-unused.json"
	ui.game.new_game();ui._new_journey_in_slot();ui.hub_controller.facing = Vector2i.RIGHT;ui.hub_controller.clock = 0.3;ui.hub_controller.motion_left = 0.1
	await shot("hunapu-story")
	ui.game.new_game();ui.game.world_node = int(ui.game.stages[101].node)
	if not ui.game.start_battle(101): errors.append("M11 battle fixture failed");quit(1);return
	ui.game.story_events.clear();ui.view = "battle";ui.ui_mode = "whole_capture"
	ui.notice_time = 0;ui.phase_time = 0;ui._clear_menu();ui.busy = false
	ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")), true)
	await shot("M11-completed-map-idle")
	ui.moving_id = "hunapu";ui.moving_position = Vector2(ui.game.pos(ui.game.find_unit("hunapu"))) * 16
	ui.moving_direction = Vector2i.LEFT;ui.moving_frame = 1
	await shot("hunapu-native-left");ui.moving_id = ""
	for cid in [21, 2, 5, 7, 9, 12, 15, 18]:
		var side = "enemy" if cid == 12 else "ally"
		var art: Dictionary = Reviewed.data().battle[str(cid) + "_" + side]
		var actor = ui.game.characters.hunapu.duplicate(true)
		actor.id = "hunapu" if cid == 21 else "review_actor";actor.class_id = cid;actor.hp = 30;actor.max_hp = 30;actor.acted = false
		actor.side = "enemy" if side == "enemy" else "player"
		actor.position = [4, 4]
		var target = actor.duplicate(true);target.id = "review_target";target.class_id = 6;target.side = "player" if side == "enemy" else "enemy"
		target.position = [5, 4]
		target.name_zh = "士兵";actor.name_zh = "胡纳普" if cid == 21 else "弓箭手" if cid == 12 else "职业样板"
		ui.game.units = [actor, target]
		ui.combat = {"attacker": actor.id, "defender": target.id, "distance": 1, "initiative_side": actor.side}
		var weapon = 1 if cid == 12 else 23 if cid == 15 else 40 if cid == 18 else 0
		var event = {"attacker": actor.id, "defender": target.id, "weapon_index": weapon, "critical": false}
		ui.view = "combat";ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.battle_animation.reset()
		ui.battle_animation.active_event = event
		var chosen = ui.battle_animation.selection(event)
		if chosen.get("kind", "") != "source": errors.append("missing capture variant " + str(cid));continue
		ui.battle_animation.show_frame(event, int(chosen.variant.contact_tick))
		await shot("class-" + str(cid) + "-" + side + "-contact")
	var file = FileAccess.open(out + "checks.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed": errors.is_empty(), "shots": shots, "errors": errors, "fixture": true}, "  "));file.close()
	print("REVIEWED_VISUAL ", shots.size(), " screenshots; errors ", errors)
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
