extends SceneTree
## Copy outside the project; execute against the signed app's embedded PCK.
const ROOT="/Users/gcc/gaocc/project/revenge-memories/actual/"
const WORK="/private/tmp/revenge-polish-package/"
var checks=[]
var failures=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func run() -> void:
	DirAccess.make_dir_recursive_absolute(WORK)
	check(ProjectSettings.get_setting("application/config/version","")=="0.5.0","Embedded version is 0.5.0")
	check(DisplayServer.get_name()=="headless","No visible package-test window")
	check(not ResourceLoader.exists("res://tests/polish_play.gd"),"Development playback excluded")
	check(not FileAccess.file_exists("res://source/portraits-0.5.0/jobs.json"),"Raw generation sources excluded")
	var State=load("res://core/game_state.gd");var Portraits=load("res://core/portrait_library.gd");var Panels=load("res://core/battle_panel_layout.gd")
	check(Portraits.data().assets.size()==48,"All 48 campaign identities embedded")
	for key in Portraits.data().assets:
		var face=Portraits.entry(key)
		check(not face.is_empty() and load(face.path).get_size()==Vector2(48,48),"Embedded native portrait: "+key)
	var g=State.new();g.new_game();g.save_path=WORK+"new.json";g.world_node=2
	check(g.start_battle(101),"Packaged ordinary first battle starts")
	check(g.battle_data.map.width==22 and g.battle_data.map.height==18 and g.living("enemy").size()==10,"Compact first battle and ten foes embedded")
	var boss=g.find_unit("M11_boss")
	check(boss.name_zh=="追击队长" and boss.hp==32 and boss.strength==10 and boss.item_id==2,"Captain identity strength and iron lance embedded")
	check(g.exit_marker().position==[16.0,3.0],"Packaged flag points at actual exit")
	var hero=g.find_unit("hunapu");g.units=[hero,boss]
	check(not g.reachable(hero,true).costs.has(Vector2i(16,3)),"Living captain blocks unique exit route")
	boss.hp=0;check(g.reachable(hero,true).costs.has(Vector2i(16,3)),"Defeated captain opens exit route")
	g=State.new();g.new_game();g.world_node=2;g.start_battle(101)
	var archer=g.find_unit("M11_e5");var action=g.ai_action(archer)
	check(action.destination!=g.pos(archer) or not str(action.target).is_empty(),"Packaged archer moves or attacks")
	hero=g.find_unit("hunapu");hero.exp=70;g.battle_outcome="victory"
	check(g.complete_battle() and g.roster.hunapu.level==2,"Packaged clear reward levels with normal growth")
	var prior=g.roster.duplicate(true);check(not g.complete_battle() and g.roster==prior,"Package settlement cannot repeat")
	g=State.new();g.save_path=ROOT+"reports/campaign/natural-M11-deployment-save.json"
	check(g.load_game() and g.battle_data.map.width==24,"Genuine old active save retains old map")
	g.save_path=WORK+"legacy.json";check(g.retry_battle() and g.battle_data.map.width==22,"Explicit retry adopts new map")
	check(g.save_game() and g.load_game(),"Packaged new tactical revision roundtrips")
	g.save_path=ROOT+"reports/campaign/natural-chapter-end-save.json"
	check(g.load_game() and g.is_dying(g.roster.fula) and g.party.has("fula"),"Old casualty remains in party")
	g.save_path=WORK+"care.json";var exp=g.roster.fula.exp;var level=g.roster.fula.level;var items=g.convoy.duplicate(true)
	g.mode="hub";g.hub_record="H04"
	check(g.treat_member("fula").valid and g.roster.fula.exp==exp and g.roster.fula.level==level and g.convoy==items,"Packaged spring preserves growth EXP and gear")
	check(g.save_game() and g.load_game() and not g.is_dying(g.roster.fula) and g.treatment_remaining()==0,"Care and stock survive package reload")
	check(g.stages[202].exit==[29.0,16.0] and g.stages[212].npc_units[0].position==[23.0,17.0],"Short rescue routes embedded")
	var placement=Panels.place(Vector2(128,120),Vector2(144,92),Rect2(0,0,256,240))
	check(placement.valid and not placement.panel.intersects(placement.focus),"Packaged minimum-width popup protects cursor")
	var report={"version":"0.5.0","passed":failures.is_empty(),"checks":checks.size(),"labels":checks,"failures":failures,"scope":"External headless script loading only signed-app embedded PCK. Genuine old checkpoints read only; all writes in /private/tmp. No natural victory claim."}
	var f=FileAccess.open(ROOT+"reports/playtest-0.5.0/package-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("PACKAGE_POLISH ",checks.size()," FAILURES ",failures);quit(0 if failures.is_empty() else 1)
