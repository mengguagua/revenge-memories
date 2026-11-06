extends SceneTree
## Reproduce through the actual chapter-four training menus. Source checkpoints
## are read-only; no level/EXP/stat/HP fixture edits are made.
const State=preload("res://core/game_state.gd")
const SOURCE="res://reports/full-assessment-20261025/campaign-final-r4/ch4/chain-chapter4-start.json"
const FIFTH_SOURCE="res://reports/full-assessment-20261025/campaign-final-r4/ch4/chain-chapter5-start.json"
var out="res://reports/full-assessment-20261025/balance/promotion-route/"
var cache=""
var checks=[]
var failures=[]
var changes=[]
var ui
var screen
var inputs=0
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append({"label":label,"passed":ok})
	if not ok:failures.append(label);push_error(label)
func same(a,b)->bool:return JSON.parse_string(JSON.stringify(a))==JSON.parse_string(JSON.stringify(b))
func key(code:int):
	inputs+=1
	var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
	e=InputEventKey.new();e.physical_keycode=code;e.pressed=false;ui._input(e)
func choose(action:String)->bool:
	check(ui.menu_actions.has(action),"actual menu exposes "+action)
	if not ui.menu_actions.has(action):return false
	for step in range(ui.menu_actions.size()):
		if str(ui.menu_actions[ui.menu_selected])==action:break
		key(KEY_DOWN)
	key(KEY_Z);return true
func enter_training()->bool:
	key(KEY_Z)
	if not choose("new:hub"):return false
	check(ui.view=="hub" and ui.hub_controller.room=="H10","normal world entry reaches shared training camp")
	for direction in [KEY_RIGHT,KEY_RIGHT,KEY_RIGHT,KEY_UP,KEY_UP,KEY_RIGHT]:key(direction)
	check(ui.game.hub_position==Vector2i(9,5) and ui.hub_controller.facing==Vector2i.RIGHT,"normal walking faces H10 training object")
	key(KEY_Z);return choose("hub:third_promotions")
func promote_and_reload(id:String,target:int):
	if not enter_training():return
	var before=ui.game.roster[id].duplicate(true)
	var inventory=ui.game.convoy.duplicate(true);var parties=ui.game.parties.duplicate(true)
	var expected=ui.game.Progression.promote(before,target)
	check(expected.valid,id+" naturally meets existing promotion requirements")
	if not choose("hub:promote_"+id+"_"+str(target)):return
	await process_frame
	var after=ui.game.roster[id].duplicate(true)
	check(int(after.class_id)==target,id+" normal confirmation actually changes class")
	var expected_unit=expected.unit.duplicate(true);expected_unit["class"]=ui.game.catalog.classes[str(target)].key
	check(same(after,expected_unit),id+" follows exact existing promotion result, including level EXP training and minima")
	check(same(ui.game.convoy,inventory) and same(ui.game.parties,parties),id+" promotion preserves inventory and army membership")
	var stored=State.read_json(ui.game.save_path)
	check(stored.get("roster",{}).get(id,{}).get("class_id",0)==target,id+" normal confirmation persists new class")
	check(ui.notice=="转职完成",id+" actual success feedback is visible")
	# Reopen the same normal UI; its obsolete choice must be gone.
	key(KEY_Z)
	choose("hub:third_promotions")
	check(not ui.menu_actions.has("hub:promote_"+id+"_"+str(target)),id+" old promotion option disappears after success")
	ui._clear_menu()
	# A stale callback replay is a separate controlled guard check, not a new
	# player-earned promotion. It must be rejected by existing progression.
	await ui.hub_controller.action("promote_"+id+"_"+str(target))
	check(same(ui.game.roster[id],after),id+" stale repeated callback cannot add stats or reset EXP again")
	var loaded=State.new();loaded.save_path=ui.game.save_path
	check(loaded.load_game() and same(loaded.roster[id],after),id+" fresh reader preserves promoted state exactly")
	changes.append({"id":id,"before":before,"after":after,"actual_keyboard_confirmation":true})

func run():
	if not OS.get_environment("PROMOTION_ROUTE_OUT").is_empty():out=OS.get_environment("PROMOTION_ROUTE_OUT")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	cache="/private/tmp/revenge-promotion-route-"+str(OS.get_process_id());DirAccess.make_dir_recursive_absolute(cache)
	var source_hash=FileAccess.get_sha256(SOURCE);var fifth_hash=FileAccess.get_sha256(FIFTH_SOURCE)
	var working=cache.path_join("working.json")
	check(DirAccess.copy_absolute(ProjectSettings.globalize_path(SOURCE),working)==OK,"historical campaign checkpoint copied without changing source")
	screen=SubViewport.new();screen.size=Vector2i(364,240);root.add_child(screen)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=cache;ui.game.save_path=working;screen.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
	check(ui.game.load_game(),"actual chapter-four starting checkpoint loads")
	ui._resume_journey();await process_frame
	check(ui.game.chapter==4 and ui.game.route=="alm" and ui.game.world_node==9,"source is a genuine accessible western camp state")
	await promote_and_reload("lance",4)
	ui._clear_menu();key(KEY_S);choose("new:switch");await process_frame
	check(ui.game.route=="celica" and ui.game.world_node==9,"ordinary menu switches to eastern camp")
	await promote_and_reload("roan",13)
	ui._clear_menu();key(KEY_Z);choose("hub:third_exchange")
	var before=ui.game.convoy.duplicate(true);var item=int(before.alm[0])
	check(ui.menu_actions.has("hub:third_transfer_0"),"chapter-four camp exposes real cross-army transfer choice")
	choose("hub:third_transfer_0");await process_frame
	var expected=before.duplicate(true);expected.alm.remove_at(0);expected.celica.append(item)
	check(same(ui.game.convoy,expected),"chapter-four third_transfer prefix already transfers exactly one item")
	key(KEY_Z)
	check(same(ui.game.convoy,expected),"another confirm opens training instead of replaying the closed transfer item")
	var reload=State.new();reload.save_path=working
	check(reload.load_game() and same(reload.convoy,expected),"transfer and promotions survive restart without duplicate items")
	var fifth=State.new();fifth.save_path=FIFTH_SOURCE
	check(fifth.load_game(),"actual chapter-five start reads for route inventory")
	var fifth_rooms=State.read_json("res://data/chapter5_hubs.json").rooms
	var shared=[]
	for room in fifth_rooms:
		for object in fifth_rooms[room].objects:
			if str(object.action).begins_with("third_") or str(object.action).begins_with("promote_") or object.action in ["east_training","east_promotions","shrine"]:shared.append({"room":room,"action":object.action})
	check(shared.is_empty() and not fifth.ChapterFive.ROOMS.has("H10"),"chapter five has no existing training/transfer menu or H10 return route to forward")
	var prior=fifth.convoy.duplicate(true)
	check(not fifth.ChapterThree.transfer_supply(fifth,0).valid and same(prior,fifth.convoy),"legacy transfer action remains unavailable outside legitimate chapter3/4 camp")
	check(FileAccess.get_sha256(SOURCE)==source_hash and FileAccess.get_sha256(FIFTH_SOURCE)==fifth_hash,"both actual campaign source checkpoints remain byte-identical")
	var f=FileAccess.open(out.path_join("checks.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"inputs":inputs,"changes":changes,"source":SOURCE,"source_sha256":source_hash,"fifth_source":FIFTH_SOURCE,"fifth_source_sha256":fifth_hash,"isolated_directory":cache,"scope":"Actual world entry, walking, training menu, promotion, team switch and transfer using copied genuine chapter-four roster; no level/stat/HP edits. Stale callback is separately controlled. Chapter-five existing menu inventory only."},"  "));f.close()
	print("PROMOTION_ROUTE ",checks.size()," failures: ",failures)
	ui.queue_free();screen.queue_free();await process_frame;quit(0 if failures.is_empty() else 1)
