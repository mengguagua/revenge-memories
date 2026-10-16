extends "res://tests/chapter2_hubs.gd"
## Two rounds of actual keyboard interaction, guarded offscreen rendering.
var round_number := 1
var audit_shots: Array = []
var audit_records: Array = []
var work_path := ""
var shots_path := ""

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	if not OS.get_environment("REVENGE_CASUALTY_ROUND").is_empty():round_number=int(OS.get_environment("REVENGE_CASUALTY_ROUND"))
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--round="):round_number=int(argument.get_slice("=",1))
	work_path="res://.cache/casualty-0.4.0/round"+str(round_number)+".json"
	shots_path="res://reports/casualty-0.4.0/round"+str(round_number)+"/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(shots_path))
	call_deferred("run")

func load_source(path: String) -> void:
	ui.game.save_path=path
	var loaded=ui.game.load_game();ui.game.save_path=work_path
	ensure(loaded,"Source checkpoint loads: "+path)
	ui.view=ui.game.mode;ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.notice_time=0;ui.held_direction=Vector2i.ZERO
	ui.instant_mode=true
	if ui.view=="hub":ui.hub_controller.resume()
	elif ui.view in ["victory","defeat"]:ui._show_result()
	elif ui.view=="battle":ui._focus_battle(ui.game.cursor,true)
	audit_records.append({"kind":"loaded","source":path,"schema":State.read_json(path).get("schema"),"party":ui.game.party.duplicate(),"dying":ui.game.party.filter(func(id):return ui.game.is_dying(ui.game.roster[id]))})

func walk_to(at: Vector2i) -> void:
	var start=ui.game.hub_position;var blocked={}
	for object in ui.hub_controller.objects:blocked[Vector2i(object.position[0],object.position[1])]=true
	for decor in ui.hub_controller.scenery:
		if not decor.get("blocking",true):continue
		for y in range(decor.rect.position.y,decor.rect.end.y):
			for x in range(decor.rect.position.x,decor.rect.end.x):blocked[Vector2i(x,y)]=true
	var pending: Array[Vector2i]=[start];var seen={start:start}
	while not pending.is_empty() and not seen.has(at):
		var point=pending.pop_front()
		for direction in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
			var next=point+direction
			if next.x<1 or next.x>12 or next.y<1 or next.y>7 or seen.has(next) or blocked.has(next) or not ui.hub_controller.east_walkable(next):continue
			seen[next]=point;pending.append(next)
	if not seen.has(at):record_failure("No legal hub route: "+str(at));return
	var path=[];var point=at
	while point!=start:path.push_front(point);point=seen[point]
	for next in path:
		var direction=next-ui.game.hub_position
		key(KEY_RIGHT if direction.x>0 else KEY_LEFT if direction.x<0 else KEY_DOWN if direction.y>0 else KEY_UP)
		ensure(ui.game.hub_position==next,"Actual hub key matches legal path")
		if abort:return

func shot(name: String,context: String,fixture: bool=false) -> void:
	ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path=shots_path+name+".png"
	var pixels=viewport.get_texture().get_image();var glyph_errors=[]
	for record in ui.text_checks:
		if record.text not in ["攻击","技巧","速度","幸运","防御","移动"] or record.get("font_px",12)!=8:continue
		for index in range(record.text.length()):
			var at: Vector2i=Vector2i(record.bounds.position+ui._canvas_offset())+Vector2i(index*8,0)
			var ink=0
			for y in range(at.y,at.y+8):
				for x in range(at.x,at.x+8):
					var color=pixels.get_pixel(x,y)
					if minf(color.r,minf(color.g,color.b))>.7:ink+=1
			if ink<4:glyph_errors.append("Invisible status glyph: "+record.text[index])
	ui.layout_errors.append_array(glyph_errors)
	pixels.save_png(path)
	audit_shots.append({"path":path,"context":context,"fixture":fixture,"view":ui.view,"status_id":ui.status_id,"layout_errors":ui.layout_errors.duplicate(),"glyph_pixel_errors":glyph_errors,"text_checks":ui.text_checks.duplicate(true),"size":[viewport.size.x,viewport.size.y]})
	ensure(ui.layout_errors.is_empty(),"Content-safe text and glyph checks: "+name)
	print("CASUALTY_SHOT ",round_number," ",name," ",ui.layout_errors)

func open_status(id: String) -> void:
	key(KEY_TAB);choose("camp:status:"+id);await settle()
	ensure(ui.view=="camp_status","Keyboard opens retained member status: "+id)

func visit_spring() -> void:
	await visit("treatment")
	ensure(ui.menu_context=="treatment","Facing input opens treatment selection")

func finish_round() -> void:
	var report={"round":round_number,"passed":not abort and failures.is_empty(),"checks":checks,"real_key_inputs":inputs,"records":audit_records,"shots":audit_shots,"failures":failures,"background_guard":true,"visible_windows":false,"scope":"Actual key-driven spring, preparation, status, save/reload and battle-entry spot checks from historical saves. One second-injury boundary fixture is explicitly labeled; no claim of a new full-chapter natural playthrough."}
	var f=FileAccess.open(shots_path+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("CASUALTY_UI_ROUND ",round_number," ",checks," CHECKS ",inputs," INPUTS ",failures)
	ui.set_process(false);ui.set_process_input(false);viewport.remove_child(ui)
	ui.hub_controller.dispose();ui.hub_controller=null;ui.free();ui=null
	viewport.queue_free();await process_frame;quit(0 if report.passed else 1)

func run() -> void:
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	if round_number==1:await round_one()
	else:await round_two()
	await finish_round()

func round_one() -> void:
	load_source("res://reports/campaign/natural-M13-victory-save.json")
	await settle()
	ensure(ui.game.treatment_remaining()==0,"Real M13 victory keeps western source locked before D12")
	key(KEY_Z);choose("continue_world");await settle()
	key(KEY_Z);choose("new:hub");await settle();await visit("church")
	await visit("cooperate")
	ensure(ui.game.treatment_remaining()==1 and ui.game.flags.get("cooperation_done",false),"Actual D12 dialogue unlocks one western share")
	await visit("cooperate")
	ensure(ui.game.treatment_remaining()==1,"Repeated D12 cooperation cannot replenish western share")
	load_source("res://reports/campaign/natural-chapter-end-save.json")
	ensure(ui.game.party.has("fula") and ui.game.is_dying(ui.game.roster.fula),"Real western casualty remains in party")
	key(KEY_Z);choose("new:world");await settle();await travel(5);await travel(4)
	key(KEY_Z);choose("new:hub");await settle();await visit("church")
	ensure(ui.game.hub_record=="H04","Ordinary world routes and church entry reach western spring")
	key(KEY_TAB)
	ensure(ui.menu_actions.has("camp:status:fula") and ui.menu_actions.has("camp:status:lena"),"Dying people are present in full roster menu")
	await shot("01-west-retained-roster","Real schema-1 chapter-end save; world travel and church entrance through keys")
	choose("camp:status:fula");await settle()
	await shot("02-west-dying-status","Actual historical Fula: existing level, EXP and stats visible with dying status")
	key(KEY_X)
	var exp_before=ui.game.roster.fula.exp;var quota=ui.game.treatment_remaining();var convoy=ui.game.convoy.duplicate(true)
	await visit_spring();choose("hub:treat_choose_fula")
	await shot("03-west-confirmation","Facing the real well opens a one-share confirmation")
	choose("hub:treatment")
	ensure(ui.game.treatment_remaining()==quota and ui.game.roster.fula.exp==exp_before,"Cancel preserves stock and EXP")
	choose("hub:treat_choose_fula");choose("hub:treat_confirm_fula");await settle()
	ensure(not ui.game.is_dying(ui.game.roster.fula) and ui.game.roster.fula.exp==exp_before and ui.game.treatment_remaining()==0,"Keyboard western treatment consumes one share and preserves EXP")
	ensure(ui.game.convoy==convoy,"Western treatment leaves real equipment quantities unchanged")
	await open_status("fula");await shot("04-west-treated-status","Same real Fula after treatment; level and EXP unchanged")
	key(KEY_X);ensure(ui.game.save_game(),"Western treated checkpoint persists")
	audit_records.append({"kind":"west_treated","member":"fula","exp":ui.game.roster.fula.exp,"treatment_count":ui.game.roster.fula.treatment_count,"remaining":ui.game.treatment_remaining()})
	load_source("res://reports/chapter2/play/natural-after-204-save.json")
	ensure(ui.game.is_dying(ui.game.roster.lisa) and ui.game.is_dying(ui.game.roster.mireille),"Both real eastern casualties remain dying in their original party")
	await open_status("lisa");await shot("05-east-migrated-status","Real schema-2 Lisa after F24; prior growth and EXP retained")
	key(KEY_X);var east_exp=ui.game.roster.lisa.exp
	await visit_spring();choose("hub:treat_choose_lisa");choose("hub:treat_confirm_lisa");await settle()
	ensure(ui.game.roster.lisa.exp==east_exp and ui.game.treatment_remaining()==0 and ui.game.is_dying(ui.game.roster.mireille),"Eastern share rescues only chosen member")
	key(KEY_Z);await settle()
	ensure(ui.menu_items.is_empty() and ui.game.treatment_remaining()==0,"Repeated spring interaction cannot refill")
	await shot("06-east-used-well","The actual H25 spring records zero remaining shares")
	ensure(ui.game.save_game(),"Round-one east checkpoint saves")

func round_two() -> void:
	load_source("res://.cache/casualty-0.4.0/round1.json")
	ensure(not ui.game.is_dying(ui.game.roster.lisa) and ui.game.is_dying(ui.game.roster.mireille) and ui.game.treatment_remaining()==0,"Saved treatment and untreated injury survive a new engine session")
	await open_status("mireille");await shot("01-reloaded-untreated-status","Second process reload; untreated Mireille remains in party, forbidden from deployment")
	key(KEY_X)
	key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:withdraw")
	if ui.menu_context=="stored_items":
		choose(str(ui.menu_actions[0]));ensure(not ui.menu_actions.has("camp:withdraw_member:mireille"),"Gear recipients exclude dying members")
		key(KEY_X)
	key(KEY_X);ui._clear_menu()
	ui.hub_controller.enter_room("H25",true);walk_to(Vector2i(6,7));key(KEY_DOWN);choose("new:world");await settle()
	await travel(22);key(KEY_Z);choose("new:battle");await settle()
	ensure(not ui.game.find_unit("lisa").is_empty() and ui.game.find_unit("mireille").is_empty() and ui.game.party.has("mireille"),"Actual F25 entry deploys rescued Lisa and retains absent Mireille in roster")
	cursor_to(State.pos(ui.game.find_unit("lisa")));key(KEY_TAB)
	await shot("02-restored-member-deployed","Normal world travel and F25 deployment; rescued Lisa appears on the real battlefield")
	key(KEY_X);key(KEY_E)
	ensure(str(ui.game.unit_at(ui.game.cursor).get("id",""))!="mireille","Unacted-unit keyboard navigation cannot select absent dying member")
	var preserved_exp=ui.game.roster.lisa.exp
	key(KEY_S);choose("new:prepare");await settle()
	ensure(ui.game.roster.lisa.exp==preserved_exp and ui.game.treatment_remaining()==0 and ui.game.is_dying(ui.game.roster.mireille),"Returning to preparation preserves previous treatment and untreated injury")
	# A boundary fixture tests the personal limit after a second injury; no
	# natural casualty or victory is claimed for this deliberate state.
	ui.game.roster.lisa.hp=0;ui.game.story_on_death(ui.game.roster.lisa);ui.game.story_events.clear()
	ui.game.save_game();ui.hub_controller.enter_room("H25")
	await open_status("lisa");await shot("03-second-injury-personal-limit","Explicit second-injury fixture after a genuine treatment",true)
	ensure(ui.game.party.has("lisa") and ui.game.is_dying(ui.game.roster.lisa) and ui.game.roster.lisa.treatment_count==1,"Second injury remains in party with exhausted personal opportunity")
	key(KEY_X)
	load_source("res://reports/chapter2/play/natural-F24-victory-save.json")
	ensure(ui.game.treatment_remaining()==0,"Fresh real F24 victory has not yet settled islanders")
	key(KEY_Z);choose("continue_world");await settle()
	if ui.view=="world":key(KEY_Z);choose("new:hub");await settle()
	ensure(ui.game.hub_record=="H25","Real F24 result proceeds to lighthouse room")
	await visit("islanders_settle")
	ensure(ui.game.treatment_remaining()==1,"Actual islander-settlement dialogue opens exactly one eastern share")
	await visit_spring();choose("hub:treat_choose_mireille");choose("hub:treat_confirm_mireille");await settle()
	ensure(not ui.game.is_dying(ui.game.roster.mireille) and ui.game.is_dying(ui.game.roster.lisa) and ui.game.treatment_remaining()==0,"Second round exercises other actual casualty without curing both")
	await open_status("mireille");await shot("04-alternate-treatment-target","Second-round actual key path rescues Mireille instead of Lisa")
	key(KEY_X);await visit("islanders_settle")
	ensure(ui.game.treatment_remaining()==0,"Repeating settlement after rescue cannot grant another share")
