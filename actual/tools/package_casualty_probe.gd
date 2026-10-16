extends SceneTree
## Copy outside the project and run against only the delivered embedded PCK.
const ROOT="/Users/gcc/gaocc/project/revenge-memories/actual/"
const WORK="/private/tmp/revenge-casualty-package/"
var checks: Array=[]
var failures: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func run() -> void:
	DirAccess.make_dir_recursive_absolute(WORK)
	check(ProjectSettings.get_setting("application/config/version","")=="0.4.0","Embedded version is 0.4.0")
	check(DisplayServer.get_name()=="headless","Delivered app probe has no visible window")
	check(not ResourceLoader.exists("res://tests/casualty_treatment.gd"),"Development tests excluded from runtime pack")
	check(ResourceLoader.exists("res://core/casualty_rules.gd"),"Injury rules included in runtime pack")
	var State=load("res://core/game_state.gd")
	var g=State.new();g.new_game()
	check(g.treatment_remaining()==0,"Packaged new game has no premature share")
	g.save_path=ROOT+"reports/campaign/natural-chapter-end-save.json"
	check(g.load_game(),"Packaged runtime loads genuine schema-1 western checkpoint")
	g.save_path=WORK+"west.json"
	check(g.party.has("fula") and g.is_dying(g.roster.fula) and not g.roster.fula.dead,"Packaged migration retains western casualty")
	var exp=g.roster.fula.exp;var level=g.roster.fula.level;var convoy=g.convoy.duplicate(true)
	g.mode="hub";g.hub_record="H04"
	check(g.treatment_remaining()==1 and g.treat_member("fula").valid,"Packaged western spring works")
	check(g.roster.fula.exp==exp and g.roster.fula.level==level and g.convoy==convoy,"Packaged treatment retains EXP growth and equipment quantities")
	check(g.save_game() and g.load_game() and g.treatment_remaining()==0,"Packaged schema-3 checkpoint roundtrips used share")
	check(not g.treat_member("fula").valid,"Packaged duplicate treatment rejected")
	g.save_path=ROOT+"reports/chapter2/play/natural-after-204-save.json"
	check(g.load_game(),"Packaged runtime loads genuine schema-2 eastern checkpoint")
	g.save_path=WORK+"east.json"
	check(g.party.has("lisa") and g.is_dying(g.roster.lisa) and g.is_dying(g.roster.mireille),"Packaged eastern casualties retained")
	exp=g.roster.lisa.exp
	check(g.treat_member("lisa").valid and g.roster.lisa.exp==exp and g.is_dying(g.roster.mireille),"Packaged eastern spring treats only chosen member")
	g.mode="world";g.world_node=22
	check(g.start_battle(205) and not g.find_unit("lisa").is_empty() and g.find_unit("mireille").is_empty() and g.party.has("mireille"),"Packaged deployment separates restored and dying members")
	var hubs=State.read_json("res://data/chapter2_hubs.json")
	check(hubs.rooms.H25.objects.any(func(o):return o.action=="treatment" and o.position==[5.0,6.0]),"Packaged lighthouse contains new spring at actual runtime position")
	check(ResourceLoader.exists("res://assets/battle_tiles/modules/well.png"),"Reused spring bitmap available")
	check(g.flags.treatment_sources.size()==2,"No future chapter source granted in delivered app")
	var report={"version":"0.4.0","passed":failures.is_empty(),"checks":checks.size(),"labels":checks,"failures":failures,"scope":"External headless probe against delivered signed app and embedded PCK; historical checkpoints are read only, writes use isolated scratch files."}
	var f=FileAccess.open(ROOT+"reports/casualty-0.4.0/package-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("PACKAGE_CASUALTY ",checks.size()," FAILURES ",failures);quit(0 if failures.is_empty() else 1)
