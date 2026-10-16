extends SceneTree
## External PCK probe. Copy this script outside the project before invocation.
const WORK="/private/tmp/revenge-battlefield-package-probe/"
const OUTPUT="/Users/gcc/gaocc/project/revenge-memories/actual/reports/battlefield-0.3.0/package-check.json"
var checks: Array=[]
var failures: Array=[]
var ui
var keys=0
var result={}
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func key(code: int) -> void:
	keys+=1;var event=InputEventKey.new();event.physical_keycode=code;event.pressed=true;ui._input(event)
	event=InputEventKey.new();event.physical_keycode=code;ui._input(event)
func choose(action: String) -> void:
	check(ui.menu_actions.has(action),"menu action available: "+action)
	if not ui.menu_actions.has(action):return
	for i in range(50):
		if str(ui.menu_actions[ui.menu_selected])==action:break
		key(KEY_DOWN)
	key(KEY_Z)
func settle() -> void:
	for i in range(1000):
		if ui.view in ["plot","reward"]:key(KEY_Z)
		if not ui.busy and not ui.batch_running and ui.view not in ["plot","reward"]:return
		await process_frame
	check(false,"pending UI input released")
func open_copy(path: String) -> void:
	ui=load("res://scenes/main.tscn").instantiate();ui.instant_mode=true;root.add_child(ui);await process_frame
	ui.game.save_path=path
	check(ui.view=="title","fresh packaged scene opens at title")
	key(KEY_Z);key(KEY_DOWN);key(KEY_Z);await settle()
func close_copy() -> void:
	ui.queue_free();await process_frame;ui=null
func run() -> void:
	result.version=ProjectSettings.get_setting("application/config/version","")
	check(result.version=="0.3.6","package version 0.3.6")
	check(DisplayServer.get_name()=="headless","headless display, no GPU/window launch")
	check(not FileAccess.file_exists("res://tests/chapter2_state.gd"),"excluded test sources are not used by packaged runtime")
	for path in ["res://assets/chapter2/chapter2-tiles.png","res://assets/chapter2/modules/rowboat.png","res://assets/chapter2/modules/lighthouse.png","res://assets/nature/pine_tall.png","res://assets/nature/ridge_bent.png","res://assets/world_tiles/formal-world-overview.png"]:
		check(load(path)!=null,"packaged art resource loads: "+path.get_file())
	for name in ["coastal_keep","hill_granary","tactical_fort","visit_door"]:
		check(load("res://assets/battlefield-0.3.0/modules/"+name+".png")!=null,"new packaged architecture loads: "+name)
	check(FileAccess.file_exists("res://data/compat/0.2.1/F26.json"),"0.2.1 active sea route compatibility included")
	await open_copy(WORK+"chapter1.json")
	check(ui.view=="chapter_end" and ui.game.chapter==1,"title continue opens actual chapter-one completion")
	check(ui.game.stages.size()==15 and ui.game.formal_world.nodes.size()==39,"15 real stages and 39 world nodes")
	check(ui.nature_sprites.size()>=20,"20 reusable nature sprites present")
	var west=ui.game.roster.duplicate(true);var western_party=ui.game.party.duplicate()
	key(KEY_Z);choose("new:chapter2");await settle()
	check(ui.game.chapter==2 and ui.game.route=="celica" and ui.view=="hub" and ui.game.hub_record=="H21" and ui.hub_controller.room=="H21","actual chapter-end menu enters chapter two at H21")
	check(ui.game.party==["eileen","mireille","lisa","carlo"],"new eastern party has four original starters")
	for id in western_party:check(ui.game.roster[id]==west[id],"chapter transition preserves western member: "+id)
	result.chapter1_to_2={"room":ui.game.hub_record,"world_node":ui.game.world_node,"party":ui.game.party.duplicate()}
	await close_copy()
	await open_copy(WORK+"chapter2.json")
	check(ui.view=="chapter_end" and ui.game.chapter==2 and ui.game.flags.get("chapter2_complete",false),"title continue opens actual final chapter-two save")
	var actual_party=ui.game.party.duplicate();var actual_roster=ui.game.roster.duplicate(true);var actual_convoy=ui.game.convoy.duplicate(true)
	check(ui.game.world_node==6 and ui.game.route_positions.celica==6,"completed eastern fleet is at Strait City")
	check(int(ui.game.roster.roan.item_id)==21 and int(ui.game.roster.shia.item_id)==49,"actual exchanged holy bow and steel shield retained")
	check(ui.game.roster.mireille.dead and ui.game.roster.lisa.dead,"actual eastern casualties retained")
	key(KEY_Z);check(not ui.menu_actions.has("new:chapter2"),"completed chapter-two menu cannot reset east party")
	choose("new:world");await settle();check(ui.view=="world" and ui.game.world_neighbors().is_empty(),"world return is bounded before chapter three")
	key(KEY_Z);choose("new:hub");await settle()
	check(ui.view=="hub" and ui.game.hub_record=="H27" and ui.hub_controller.room=="H27","Strait City enters eastern arrival hub H27, not western H06")
	key(KEY_S);choose("new:camp");choose("camp:roster")
	check(ui.menu_context=="camp_members" and ui.menu_actions.size()==actual_party.size(),"actual preparation roster lists the full eastern party")
	for id in actual_party:check(ui.menu_actions.has("camp:status:"+str(id)),"preparation roster member present: "+id)
	choose("camp:status:roan")
	check(ui.view=="camp_status" and ui.status_id=="roan" and int(ui.game.camp_unit("roan").item_id)==21,"actual roster status opens archer with holy bow")
	check(ui.game.roster==actual_roster and ui.game.convoy==actual_convoy,"inspection never mutates army equipment or convoy")
	result.chapter2_resume={"room":ui.game.hub_record,"world_node":ui.game.world_node,"party":actual_party,"roan_item":ui.game.roster.roan.item_id,"shia_item":ui.game.roster.shia.item_id}
	await close_copy()
	await open_copy(WORK+"old-battle.json")
	check(ui.game.stage_id==105 and not ui.game.battle_data.has("tactical_review_version"),"old active tower battle retains original geometry")
	check(FileAccess.file_exists("res://data/compat/0.2.0/M15.json"),"compatibility geometry included in standalone pack")
	key(KEY_S);choose("new:prepare");await settle()
	key(KEY_Z);choose("travel:6");await settle();key(KEY_Z);choose("new:battle");await settle()
	check(ui.game.battle_data.get("tactical_review_version","")=="0.3.4","normal preparation re-entry upgrades to reviewed layout")
	check(not ui.game.battle_data.get("tactical_notes",[]).is_empty(),"packaged objective menu has tactical explanation")
	await close_copy()
	await open_copy(WORK+"new-battle.json")
	check(ui.game.stage_id==105 and ui.game.battle_data.get("tactical_review_version","")=="0.3.4","new actual field save resumes reviewed geometry")
	check(int(ui.game.find_unit("hunapu").item_id)==11,"actual prepared steel sword remains equipped in pack")
	for unit in ui.game.units:
		if int(unit.hp)>0:check(ui.game.movement_cost(unit,ui.game.pos(unit))<255,"current field unit remains on legal terrain: "+str(unit.id))
	await close_copy()
	result.scope="Standalone exported PCK, external script, headless Dummy, title/menu inputs against isolated copies of actual chapter-end saves"
	result.checks=checks.size();result.inputs=keys;result.failures=failures;result.passed=failures.is_empty();result.test_sources_in_pack=false
	var f=FileAccess.open(OUTPUT,FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close();print("PACKAGE_CHAPTER2 ",JSON.stringify(result));quit(0 if failures.is_empty() else 1)
