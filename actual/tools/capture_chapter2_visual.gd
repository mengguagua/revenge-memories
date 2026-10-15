extends SceneTree
## Second-round visual review only. Directed fresh opening fixtures, not claimed
## to be natural progression, victories or player-input screenshots.
const State=preload("res://core/game_state.gd")
const East=preload("res://core/chapter2_rules.gd")
var ui
var viewport: SubViewport
var shots: Array=[]
var errors: Array=[]
var capture_filter: PackedStringArray=[]
func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func setup(code: String) -> void:
	ui.game.new_game();ui.game.save_path="res://reports/chapter2/visual-fixtures/working-save.json"
	ui.game.flags.chapter1_complete=true;ui.game.cleared_stages=[105];ui.game.begin_chapter_two()
	var id={"F21":201,"F22":202,"F23":203,"F24":204,"F25":205,"F26":206,"S21":211,"S22":212}[code]
	var members=["eileen","mireille","lisa","carlo"]
	if code in ["F23","F24","F25","F26","S22"]:members.append("lord")
	if code in ["F24","F25","F26","S22"]:members.append("roan")
	if code in ["F25","F26"]:members.append("shia")
	ui.game.party=members;ui.game.parties.celica=members.duplicate()
	for member in members:ui.game.roster[member]=ui.game._initial_character(member)
	ui.game.world_node=int(ui.game.stages[id].node);ui.game.previous_world_node=17
	if not ui.game.start_battle(id):errors.append(code+" fixture could not start")
	ui.game.story_events.clear();ui.game.flags.erase("active_plot")
	ui.view="battle";ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui.phase_time=0;ui.notice_time=0;ui._clear_menu()
	ui.game.cursor=Vector2i(0,0);ui._focus_battle(ui.game.cursor,true)
func focus(cell: Vector2i) -> void:
	ui.game.cursor=cell;ui._focus_battle(cell,true)
func shot(name: String,description: String) -> void:
	ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path="res://reports/chapter2/visual-fixtures/"+name+".png"
	viewport.get_texture().get_image().save_png(path)
	shots.append({"path":path,"fixture":true,"source":"Directed fresh chapter-two engine fixture; "+description,"canvas":[viewport.size.x,viewport.size.y],"view":ui.view,"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(true),"stage":ui.game.battle_data.code})
	errors.append_array(ui.layout_errors);print("CH2_VISUAL ",name," ",ui.layout_errors)
func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/chapter2/visual-fixtures"))
	if not OS.get_environment("CH2_CAPTURE_CODES").is_empty():
		capture_filter=OS.get_environment("CH2_CAPTURE_CODES").split(",")
		var old_path="res://reports/chapter2/visual-fixtures/captures.json"
		if FileAccess.file_exists(old_path):
			var previous=JSON.parse_string(FileAccess.get_file_as_string(old_path))
			for item in previous.get("shots",[]):
				if not str(item.stage) in capture_filter:shots.append(item)
	viewport=SubViewport.new();viewport.size=Vector2i(768,432);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	for code in ["F21","F22","F23","F24","F25","F26","S21","S22"]:
		if not capture_filter.is_empty() and not code in capture_filter:continue
		viewport.size=Vector2i(768,432);setup(code);await process_frame
		ui.battle_camera=ui._clamp_map_camera(Vector2.ZERO,Vector2(ui.game.battle_data.map.width,ui.game.battle_data.map.height)*16)
		await shot(code+"-whole-map","Wide landscape viewport covers complete map silhouette and actual units")
		viewport.size=Vector2i(426,240);await process_frame
		focus(Vector2i(ui.game.battle_data.targets[0][0],ui.game.battle_data.targets[0][1]));await shot(code+"-objective","16:9 objective viewpoint, actual runtime map layers")
		focus(ui.game.pos(ui.game.find_unit("eileen")));await shot(code+"-unit-card","Original unit/portrait renderer with current chapter card")
		if code=="F21":
			focus(ui.game.pos(ui.game.find_unit("friendly_ship")));await shot("F21-ship-card","Actual ship event flag and status card, explicit event fixture")
		if code=="F22":
			focus(Vector2i(16,13));await shot("F22-bridge-closed","Closed bridge fixture, sea and railing must be visibly impassable")
			East.interact(ui.game,"reserve_bridge");focus(Vector2i(16,13));await shot("F22-bridge-open","Actual bridge interaction applies opens and runtime bridge art")
			East.interact(ui.game,"prison_door");focus(Vector2i(16,11));await shot("F22-prison-open","Actual prison interaction removes closed gate visual")
		if code=="F26":
			focus(Vector2i(4,21));await shot("F26-boat-card","Actual boat event sprite and boat status card at its water cell")
			ui.game.turn=5;ui.game.flags.quest.boats[0].position=[18,21];ui.game.flags.quest.boats[0].path_index=14
			ui.game.flags.quest.boats[1].position=[10,21];ui.game.flags.quest.boats[1].path_index=6
			focus(Vector2i(18,21));await shot("F26-two-boats","Directed event-state fixture shows two intact boats on distinct water positions")
		if code in ["F21","F24","F25"]:
			ui._menu_action("new:goal","")
			await process_frame;ui._advance_plot()
			await shot(code+"-goal-dialogue","Actual objective menu text through UI handler")
			ui.view="battle";ui.busy=false;ui.plot_finished=true;ui.plot_pages=[]
		if code in ["F24","F25"]:
			ui.game.queue_lines(str(ui.game.battle_data.before),code+"-VISUAL-DIALOGUE")
			ui._play_story_events()
			await process_frame;ui._advance_plot()
			await shot(code+"-opening-dialogue","Actual opening dialogue with narrative scene context and original portrait rules")
			if code=="F24":
				ui._advance_plot();await process_frame;ui._advance_plot()
				await shot("F24-shia-dialogue","Actual Shia speech and portrait against the black-day lighthouse scene")
			ui.view="battle";ui.busy=false;ui.plot_finished=true;ui.plot_pages=[]
	var f=FileAccess.open("res://reports/chapter2/visual-fixtures/captures.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"fixtures":true,"background_guard":true,"visible_windows":false,"shots":shots,"errors":errors,"scope":"Second-round visual fixtures: eight whole maps/objective viewpoints/cards plus dynamic bridge, door and event boats. No natural victories claimed."},"  "));f.close()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit(0 if errors.is_empty() else 1)
