extends SceneTree
const State=preload("res://core/game_state.gd")
const Compare=preload("res://core/equipment_comparison.gd")
class FailingSave extends "res://core/game_state.gd":
	func save_game() -> bool:return false
var checks: Array=[]
var errors: Array=[]
var details={}
var ui
func _initialize():call_deferred("run")
func check(ok: bool,label: String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh():
	var g=State.new();g.new_game();g.mode="world";g.save_path="/private/tmp/equipment-preview-test.json";return g
func row(data: Dictionary,key: String) -> Dictionary:
	return data.rows.filter(func(r):return r.key==key)[0]
func key(code: int):
	var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
	e=InputEventKey.new();e.physical_keycode=code;e.pressed=false;ui._input(e)
func mouse(point: Vector2):
	var e=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.position=point+ui._canvas_offset();e.pressed=true;ui._input(e)
func menu(action: String):
	check(ui.menu_actions.has(action),"menu contains "+action)
	if ui.menu_actions.has(action):ui.menu_selected=ui.menu_actions.find(action);key(KEY_Z)
func normalized(value):return JSON.parse_string(JSON.stringify(value))
func run():
	var g=fresh();g.convoy.alm=[60,48,62,66];var inventory=g.convoy.duplicate(true);var roster=g.roster.duplicate(true);var flags=g.flags.duplicate(true)
	var data=g.equipment_preview("hunapu",0)
	check(data.can_equip and data.current_name=="铜剑" and data.class_name=="战士","real current profession and equipped sword")
	check(row(data,"power").delta==1,"iron sword raises effective attack by one")
	check(g.convoy==inventory and g.roster==roster and g.flags==flags,"preview leaves inventory, roster and flags untouched")
	var archer=g._initial_character("daan");archer.item_id=64;data=Compare.compare(archer,20,g.catalog.classes)
	check(row(data,"power").delta==1 and row(data,"hit").delta==-5 and row(data,"speed").delta==-1 and row(data,"range").delta==2,"steel bow displays simultaneous power/range gains and hit/speed losses")
	check(row(data,"hit").delta_text=="-5%" and row(data,"power").delta_text=="+1","positive and negative values carry explicit signs")
	details.steel_bow=data
	var mage=g._initial_character("hervi");mage.item_id=65;data=Compare.compare(mage,66,g.catalog.classes)
	check(row(data,"power").delta==1 and row(data,"hit").delta==5 and row(data,"speed").delta==-1,"iron focus uses actual magic profile and added weight")
	check(int(data.before.hp_cost)==int(data.after.hp_cost) and data.before.reach==data.after.reach,"focus preserves existing HP cost and range")
	data=g.equipment_preview("hunapu",1)
	check(row(data,"power").delta==-1 and row(data,"defence").delta==3,"shield replacement removes weapon power and adds actual defence")
	check(data.target_description.contains("属性"),"ordinary accessory description does not fabricate a spell")
	data=g.equipment_preview("hunapu",2)
	check(not data.can_equip and data.reason.contains("不适配") and int(data.after.power)==10,"unusable lance supplies no sword-user weapon bonus")
	check(g.equipment_preview("hunapu",-1).is_empty() and g.equipment_preview("hunapu",99).is_empty(),"bad inventory indices rejected")
	check(g.equipment_preview("eileen",0).is_empty(),"other army cannot withdraw this army's inventory")
	for spec in [["otto",4,false],["otto",7,false],["otto",17,false],["hunapu",17,true]]:
		var actor=g._initial_character(spec[0]);check(Compare.compare(actor,spec[1],g.catalog.classes).compatible==spec[2],"special class and personal restriction "+str(spec))
	var hero=g.roster.hunapu.duplicate(true);hero.promoted=true
	check(Compare.compare(hero,64,g.catalog.classes).compatible,"promoted protagonist can use a bow")
	hero=g.roster.hunapu.duplicate(true);data=Compare.compare(hero,55,g.catalog.classes)
	check(row(data,"luck").after==40 and row(data,"critical").after==11,"angel ring updates effective luck and actual critical formula")
	data=Compare.compare(hero,56,g.catalog.classes)
	check(row(data,"speed").after==40 and row(data,"move").delta==5,"speed ring changes effective attack speed and movement")
	data=Compare.compare(hero,51,g.catalog.classes)
	check(row(data,"defence").delta==0 and data.target_description.contains("仅对魔物"),"holy shield conditional bonus is explained rather than made universal")
	data=Compare.compare(hero,53,g.catalog.classes)
	check(row(data,"defence").delta==13 and row(data,"resistance").delta==13,"dragon shield actual defence and resistance")
	hero.strength=50;data=Compare.compare(hero,15,g.catalog.classes)
	check(row(data,"power").after==15,"lightning sword keeps fixed magic power instead of adding strength")
	var healer=g._initial_character("fula");healer.magic_flags=0;healer.item_id=65;data=Compare.compare(healer,66,g.catalog.classes)
	check(int(data.after.power)==0 and int(data.after.range)==0 and data.target_description.contains("不增加法术"),"focus never grants an attack spell to a healer without one")
	g.roster.otto.dying=true;data=g.equipment_preview("otto",2)
	check(not data.can_equip and data.reason.contains("濒死"),"dying party member previews blocked allocation")
	g=fresh();g.convoy.alm=[60];inventory=g.convoy.duplicate(true);roster=g.roster.duplicate(true)
	check(not g.equip_from_convoy("hunapu",0,62).valid and g.convoy==inventory and g.roster==roster,"stale selected item cannot transfer another item")
	check(not g.equip_from_convoy("otto",0,60).valid and g.convoy==inventory and g.roster==roster,"incompatible commit preserves all inventory")
	check(g.equip_from_convoy("hunapu",0,60).valid and int(g.roster.hunapu.item_id)==60 and g.convoy.alm==[59],"confirmed replacement returns old sword to same inventory slot")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game() and int(loaded.roster.hunapu.item_id)==60 and int(loaded.convoy.alm[0])==59,"confirmed replacement persists across reload")
	g=fresh();g.roster.hunapu.item_id=0;g.convoy.alm=[60]
	check(g.equip_from_convoy("hunapu",0,60).valid and g.convoy.alm.is_empty(),"empty-handed recipient removes exactly one item")
	g=fresh();g.convoy.alm.resize(40);g.convoy.alm.fill(60)
	check(g.equip_from_convoy("hunapu",39,60).valid and g.convoy.alm.size()==40 and int(g.convoy.alm[39])==59,"full forty-item inventory can swap without loss or overflow")
	var failed=FailingSave.new();failed.new_game();failed.mode="world";failed.convoy.alm=[60]
	inventory=failed.convoy.duplicate(true);roster=failed.roster.duplicate(true);flags=failed.flags.duplicate(true)
	check(not failed.equip_from_convoy("hunapu",0,60).valid and failed.convoy==inventory and failed.roster==roster and failed.flags==flags,"save failure rolls back equipment, inventory and flags")
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.game=fresh();ui.game.convoy.alm=[60];ui.view="world";ui.busy=false
	ui._open_camp_menu();menu("camp:convoy");menu("camp:withdraw");menu("camp:withdraw_item:0")
	check(ui.view=="equipment_members" and ui.equipment_screen.member_label("otto").contains("士兵 · 铜枪"),"real preparation path opens annotated character list")
	inventory=ui.game.convoy.duplicate(true);roster=ui.game.roster.duplicate(true)
	key(KEY_Z);check(ui.view=="equipment_preview","first confirmation only opens comparison")
	check(ui.game.convoy==inventory and ui.game.roster==roster,"opening comparison does not equip")
	key(KEY_TAB);check(ui.equipment_screen.more,"Tab opens special equipment effects")
	key(KEY_X);check(ui.view=="equipment_members" and ui.game.convoy==inventory and ui.game.roster==roster,"cancel comparison retains every item")
	mouse(ui.equipment_screen.row_rect(0).get_center());check(ui.view=="equipment_preview","clicking character opens comparison")
	mouse(ui.equipment_screen.button_rect(1).get_center())
	check(ui.view=="world" and int(ui.game.roster.hunapu.item_id)==60 and ui.game.convoy.alm==[59],"explicit mouse confirmation commits one replacement")
	ui._clear_menu();ui.game.convoy.alm=[62];ui._camp_action("withdraw_item:0");key(KEY_Z)
	check(not ui.equipment_screen.preview().can_equip,"sword user sees incompatible lance preview")
	mouse(ui.equipment_screen.button_rect(1).get_center())
	check(ui.view=="equipment_preview" and int(ui.game.roster.hunapu.item_id)==60 and ui.game.convoy.alm==[62],"disabled confirm cannot equip incompatible weapon")
	key(KEY_X);key(KEY_DOWN);key(KEY_DOWN);key(KEY_Z);check(ui.equipment_screen.preview().can_equip,"choose compatible soldier through ordinary keyboard input")
	key(KEY_Z)
	check(ui.view=="world" and int(ui.game.roster.otto.item_id)==62 and ui.game.convoy.alm==[61],"keyboard confirmation returns soldier's old lance")
	ui._clear_menu()
	for id in ["fula","lena","lance","beck","hervi"]:ui.game.recruit(id)
	ui.game.convoy.alm=[20];ui._camp_action("withdraw_item:0");mouse(ui.equipment_screen.page_rect(1).get_center())
	check(ui.equipment_screen.first==3 and ui.equipment_screen.members.size()==8,"mouse page arrow exposes remaining full-party members")
	while ui.equipment_screen.first+ui.equipment_screen.page_size()<ui.equipment_screen.members.size():mouse(ui.equipment_screen.page_rect(1).get_center())
	mouse(ui.equipment_screen.row_rect(ui.equipment_screen.page_size()-1).get_center())
	check(ui.view=="equipment_preview" and ui.equipment_screen.preview().name=="赫维","last visible row previews the actual eighth party member")
	key(KEY_X);key(KEY_DOWN)
	check(ui.equipment_screen.selected==0 and ui.equipment_screen.first==0,"keyboard wrap returns to first member and visible first page")
	ui.queue_free();await process_frame
	var report={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"details":details,"scope":"Actual preparation keyboard/mouse path, read-only forecasts, formula edges, compatibility, inventory conservation, persistence and failed-save rollback; independent saves"}
	var file=FileAccess.open("res://reports/equipment-preview-20261020/checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("EQUIPMENT_PREVIEW ",JSON.stringify({"passed":errors.is_empty(),"checks":checks.size(),"errors":errors}));quit(0 if errors.is_empty() else 1)
