extends SceneTree
## Copy outside the checkout; run only against the app's embedded PCK.
const OUT="/Users/gcc/gaocc/project/revenge-memories/actual/reports/equipment-0.3.9/package-checks.json"
const WORK="/private/tmp/revenge-equipment-package-probe/"
var checks: Array=[]
var failures: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func run() -> void:
	check(ProjectSettings.get_setting("application/config/version","")=="0.3.9","packaged version is 0.3.9")
	check(DisplayServer.get_name()=="headless","independent probe cannot show a window")
	check(not FileAccess.file_exists("res://tests/equipment_progression.gd"),"test source excluded from runtime pack")
	var State=load("res://core/game_state.gd");var Items=load("res://core/item_rules.gd");var Loot=load("res://core/campaign_loot.gd")
	var g=State.new();g.new_game();g.save_path=WORK+"working-save.json"
	check(Items.data().items.size()==67,"all eight added weapon definitions are in runtime pack")
	for id in g.party:check(Items.can_use(g.roster[id],int(g.roster[id].item_id)),"starter is usable in packaged runtime: "+str(id))
	for stage in g.stages.values():
		for u in stage.enemies+stage.reinforcements:
			if int(u.item_id)>0:check(Items.can_use(u,int(u.item_id)) and int(u.drop_chance)==100,"packaged enemy guaranteed carried drop: "+str(u.id))
			else:check(Loot.chance(u)==10 and not Loot.pool(u).is_empty(),"packaged ordinary random loot: "+str(u.id))
	check(g.save_game(),"packaged new weapon save writes")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game() and int(loaded.roster.hunapu.item_id)==59,"packaged new weapon save reloads")
	var old=State.new();old.save_path=WORK+"historical-save.json"
	check(old.load_game(),"packaged runtime loads real historical checkpoint")
	check(old.begin_chapter_two(),"packaged runtime enters second chapter after migration")
	check(int(old.roster.eileen.item_id)==60 and int(old.roster.mireille.item_id)==65 and int(old.roster.lisa.item_id)==66,"packaged eastern starters use new equipment")
	var report={"version":"0.3.9","passed":failures.is_empty(),"checks":checks.size(),"failures":failures,"scope":"External headless script against only the signed embedded PCK: all enemies/reinforcements, carried guarantee, ordinary pools and historical-save migration."}
	var file=FileAccess.open(OUT,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close();print("PACKAGE_EQUIPMENT ",JSON.stringify(report));quit(0 if failures.is_empty() else 1)
