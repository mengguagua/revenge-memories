extends SceneTree
const OUT="res://reports/tactical-expansion-20261025/visual/"
var screen
var phone
var ui
var checks=[]
var errors=[]
var shots=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label)
func frame():
	ui.dialogue_reveal=10000;ui.notice_time=0;ui.phase_time=0
	phone._sync_controls();ui.queue_redraw();phone.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func shot(name:String):
	await frame()
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+": safe text and controls")
	if not ui.layout_errors.is_empty():errors.append_array(ui.layout_errors)
	var path=OUT+name+".png";screen.get_texture().get_image().save_png(path)
	shots.append({"name":name,"path":path,"view":ui.view,"text":ui.text_checks.duplicate(true),"audit":ui.presentation_audit.duplicate(true)})
func load_case(path:String):
	ui.game.save_path=path;check(ui.game.load_game(),"load display source "+path)
	ui.game.save_path="/private/tmp/tactical-visual-working.json"
	ui.game.flags.erase("active_plot");ui.game.story_events.clear();ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui.result_sequence_running=false
	ui.ui_mode="inspect";ui._clear_menu()
func dismiss_plot():
	for i in range(40):
		if ui.view!="plot":break
		ui.dialogue_reveal=10000;ui._accept();await process_frame
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override="/private/tmp/tactical-visual-slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	load_case("res://reports/tactical-expansion-20261025/knockback-play/round1/M13-deployment.json")
	var actor=ui.game.find_unit("hunapu");var ally=ui.game.living("player").filter(func(u):return u.id!=actor.id and not u.get("neutral",false))[0]
	# Presentation fixtures only: position previews do not count as playthroughs.
	actor.position=[6,13];ally.position=[7,13];actor.acted=false;ally.acted=true;ui.game.phase="player";ui.game.selected_id=actor.id;ui.game.cursor=ui.game.pos(actor);ui._focus_battle(ui.game.cursor,true);ui.view="battle"
	ui._unit_action_menu();await shot("01-cover-menu")
	ui._clear_menu();ui._menu_action("cover:target:"+str(ally.id),"unit_action")
	await shot("03-cover-confirm")
	ui._clear_menu();ui.game.begin_cover(str(ally.id));ui.ui_mode="inspect";await shot("04-cover-active")
	load_case("res://reports/tactical-expansion-20261025/rescue-play/round1/F22-deployment.json")
	ui.view="battle";ui.game.cursor=Vector2i(17,18);ui._focus_battle(ui.game.cursor,true)
	await shot("05-crate-intact")
	actor=ui.game.find_unit("eileen");actor.position=[17,19];actor.acted=false;ui.game.selected_id=actor.id
	var choices=ui.game.Battlefield.interactions_for(ui.game,actor)
	check(not choices.is_empty(),"crate offers demolition")
	if not choices.is_empty():
		ui._menu_action("interact:"+str(choices[0].id),"unit_action");await shot("06-crate-consequences");await dismiss_plot();await shot("07-crate-confirm")
		ui._clear_menu();ui.game.interact(str(choices[0].id));ui.game.story_events.clear();ui.ui_mode="inspect";await shot("08-crate-open")
	load_case("res://reports/tactical-expansion-20261025/play/J54-round1/J54-turn-4.json")
	ui.view="battle";var marks=ui.game.Battlefield.warning_cells(ui.game)
	check(not marks.is_empty(),"actual turn-four checkpoint retains telegraph")
	if not marks.is_empty():ui.game.cursor=Vector2i(marks[0].position[0],marks[0].position[1]);ui._focus_battle(ui.game.cursor,true)
	await shot("09-final-warning")
	load_case("res://reports/tactical-expansion-20261025/knockback-play/round1/M33-deployment.json")
	actor=ui.game.units.filter(func(u):return u.side=="player" and int(u.get("item_id",0))==67)[0]
	var enemy=ui.game.living("enemy")[0]
	actor.position=[8,14];enemy.position=[9,14];ui.game.selected_id=actor.id;ui.game.cursor=ui.game.pos(enemy);ui.target_ids=[str(enemy.id)];ui.target_index=0;ui.ui_mode="target";ui.view="battle";ui._focus_battle(ui.game.cursor,true)
	await shot("10-knockback-preview")
	check(ui.battle_preview_audit.has("knockback"),"attack preview includes displacement result")
	load_case("res://reports/tactical-expansion-20261025/training/round1-early/191-entry.json")
	ui.view="battle";ui.game.cursor=Vector2i(ui.game.battle_data.training_target[0],ui.game.battle_data.training_target[1]);ui._focus_battle(ui.game.cursor,true);await shot("11-training-field")
	load_case("res://reports/tactical-expansion-20261025/training/round1-early/191-victory.json")
	ui.view="victory";await shot("12-training-result")
	ui.game.Training.leave(ui.game);ui.view=ui.game.mode;ui._open_camp_menu();await shot("13-training-entry")
	ui._clear_menu();ui._menu_action("training:detail:192","camp");await shot("14-training-detail");await dismiss_plot()
	var f=FileAccess.open(OUT+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"shots":shots,"background_guard":true,"scope":"Background-rendered phone-layout presentation fixtures and real play checkpoints. This is not an iPhone installation or device playtest."},"  "));f.close()
	print("TACTICAL_VISUAL ",checks.size()," errors=",errors)
	phone.queue_free();await process_frame;screen.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
