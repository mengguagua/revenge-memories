extends SceneTree
const State=preload("res://core/game_state.gd")
const CACHE="/private/tmp/revenge-equipment-clarity-20261021/slots/"
var ui
var viewport
var checks=[]
var errors=[]

func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func key(code:int):
	var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
	e=InputEventKey.new();e.physical_keycode=code;e.pressed=false;ui._input(e)
func action(name:String):
	check(ui.menu_actions.has(name),"menu exposes "+name)
	if ui.menu_actions.has(name):ui.menu_selected=ui.menu_actions.find(name);key(KEY_Z)
func mouse(point:Vector2):
	var e=InputEventMouseButton.new();e.position=point+ui._canvas_offset();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=true;ui._input(e)
func bytes(slot:int):return FileAccess.get_file_as_bytes(State.Journals.path_for(CACHE,slot))

func run():
	DirAccess.make_dir_recursive_absolute(CACHE)
	for name in DirAccess.get_files_at(CACHE):DirAccess.remove_absolute(CACHE+name)
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=CACHE;viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
	ui.game.new_game();ui.game.mode="world";ui.view="world";ui.busy=false;ui.game.flags.camp_save_marker=1
	check(ui.game.save_to_slot(1),"seed independent first record")
	ui.game.flags.camp_save_marker=2;check(ui.game.save_to_slot(2),"seed independent second record")
	var first=bytes(1);var second=bytes(2)
	ui.game.flags.camp_save_marker=3
	ui._open_camp_menu()
	check(not ui.menu_actions.has("title") and not ui.menu_items.has("返回标题"),"preparation menu removes return-to-title entry")
	action("camp:save")
	check(ui.view=="journal" and ui.journey.intent=="save" and ui.journey.records.size()==5,"preparation save opens actual five-slot picker")
	check(ui.journey.selected==1 and ui.game.mode=="world","save picker selects active slot and retains world mode")
	check(bytes(1)==first and bytes(2)==second,"opening picker does not write either record")
	key(KEY_Z)
	check(ui.view=="journal_confirm" and ui.journey.confirm_choice==0,"occupied destination requires confirmation with return selected")
	check(bytes(2)==second,"opening overwrite confirmation preserves destination")
	key(KEY_Z);key(KEY_X)
	check(ui.view=="world" and ui.game.active_slot==2 and bytes(1)==first and bytes(2)==second,"cancel returns to original world without writing or changing active slot")
	ui._open_camp_menu();action("camp:save");ui.journey.prepare_art();mouse(ui.journey.art.row_rect(2).get_center())
	check(ui.view=="world" and ui.game.active_slot==3 and ui.journey.saved_left>0,"empty destination saves directly after explicit slot choice")
	check(State.read_json(ui.game.save_path).flags.camp_save_marker==3 and bytes(1)==first and bytes(2)==second,"save-as writes only chosen slot")
	var third=bytes(3)
	ui.view="hub";ui.game.mode="hub";ui.game.hub_record="P00";ui.game.flags.camp_save_marker=4
	ui._open_camp_menu();action("camp:save")
	check(ui.view=="journal" and ui.journey.return_view=="hub" and ui.game.mode=="hub","hub preparation save retains hub checkpoint and return view")
	ui.journey.selected=1;key(KEY_Z);key(KEY_RIGHT);key(KEY_Z)
	var saved=State.read_json(ui.game.save_path)
	check(ui.view=="hub" and ui.game.active_slot==2 and saved.mode=="hub" and saved.hub_record=="P00" and saved.flags.camp_save_marker==4,"confirmed overwrite saves actual hub state to selected slot")
	check(bytes(1)==first and bytes(3)==third,"confirmed overwrite leaves other records byte-identical")
	var reloaded=State.new();reloaded.save_path=ui.game.save_path
	check(reloaded.load_game() and reloaded.mode=="hub" and reloaded.hub_record=="P00","selected hub record reloads at the original location")
	second=bytes(2);var path=ui.game.save_path;var slot=ui.game.active_slot
	ui._open_camp_menu();action("camp:save");ui.game.slot_directory=CACHE+"missing/parent";ui.journey.selected=3;key(KEY_Z)
	check(ui.view=="journal" and ui.journey.message.contains("失败") and ui.game.save_path==path and ui.game.active_slot==slot,"save failure retains picker and previous active destination")
	check(bytes(1)==first and bytes(2)==second and bytes(3)==third,"save failure preserves all existing records")
	key(KEY_X);ui.game.slot_directory=CACHE
	check(ui.view=="hub","failed save cancels back to hub")
	ui.view="world";ui.game.mode="world";ui._clear_menu();ui._open_system_menu()
	check(ui.menu_actions.has("title"),"requested removal is confined to preparation menu")
	var f=FileAccess.open("res://reports/equipment-clarity-20261021/camp-save-checks.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"actual_keyboard_input":true,"actual_mouse_slot_selection":true,"isolated_saves":CACHE},"  "));f.close()
	print("CAMP_SAVE ",checks.size()," checks; errors: ",errors)
	ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
