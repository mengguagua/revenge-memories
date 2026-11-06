extends SceneTree
## Fault and restart tests. Every mutation uses generated fixtures or copied
## historical checkpoints; no player journal or source checkpoint is written.
const State=preload("res://core/game_state.gd")
var checks=[]
var failures=[]
var sources=[]
var cache=""
var out="res://reports/full-assessment-20261025/save/"

func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func same(a,b)->bool:return JSON.parse_string(JSON.stringify(a))==JSON.parse_string(JSON.stringify(b))
func bytes(path:String):return FileAccess.get_file_as_bytes(path)
func write(path:String,value):
	var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(value if value is String else JSON.stringify(value));f.close()
func fresh(name:String):
	var g=State.new();g.slot_directory=cache.path_join(name)
	DirAccess.make_dir_recursive_absolute(g.slot_directory)
	g.new_game();g.save_path=g.Journals.path_for(g.slot_directory,1);return g
func restored(path:String):
	var g=State.new();g.save_path=path
	check(g.load_game(),"read isolated checkpoint "+path.get_file());return g
func io_checks():
	var g=fresh("atomic");g.flags.marker=1
	check(g.save_game(),"initial checkpoint saves")
	var first=bytes(g.save_path);g.flags.marker=2
	check(g.save_game(),"replacement checkpoint saves")
	check(bytes(g.save_path+".bak")==first,"backup retains exact previous complete checkpoint")
	var second=bytes(g.save_path)
	write(g.save_path+".tmp",'{"schema":3,"flags":')
	check(restored(g.save_path).flags.marker==2,"incomplete temporary write is ignored on restart")
	DirAccess.remove_absolute(g.save_path+".tmp")
	DirAccess.make_dir_absolute(g.save_path+".tmp")
	g.flags.marker=3
	check(not g.save_game() and bytes(g.save_path)==second,"temporary-file open failure preserves primary")
	DirAccess.remove_absolute(g.save_path+".tmp")
	DirAccess.remove_absolute(g.save_path+".bak")
	DirAccess.make_dir_absolute(g.save_path+".bak")
	check(not g.save_game() and bytes(g.save_path)==second,"backup replacement failure preserves primary")
	DirAccess.remove_absolute(g.save_path+".bak")
	check(g.save_game(),"saving recovers after filesystem obstruction is removed")
	var good=bytes(g.save_path)
	g.flags.active_plot={"pages":[{"speaker":"旁白","text":"测试"}],"index":0}
	check(not g.save_game() and bytes(g.save_path)==good,"writer rejects invalid dialogue state before replacing good checkpoint")
	g.flags.erase("active_plot")
	var original_path=g.save_path;var original_slot=g.active_slot
	g.slot_directory=cache.path_join("missing/parent")
	check(not g.save_to_slot(2) and g.save_path==original_path and g.active_slot==original_slot,"failed save-as preserves active destination")

func recovery_checks():
	var g=fresh("recovery");g.flags.marker=7;check(g.save_game(),"recovery seed saves")
	var first=bytes(g.save_path);g.flags.marker=8;check(g.save_game(),"recovery seed rotates backup")
	var damaged='{"schema":3,"cut_during_external_write":'
	write(g.save_path,damaged)
	var record=g.slot_records()[0]
	check(record.valid and record.get("recovered",false) and record.path==g.save_path+".bak","corrupt primary exposes validated recovery copy")
	var r=State.new();r.slot_directory=g.slot_directory
	var recovered=r.load_slot(1)
	check(recovered and int(r.flags.get("marker",0))==7,"slot load resumes previous complete checkpoint")
	check(FileAccess.get_file_as_string(g.save_path)==damaged,"recovery read never changes damaged original")
	if recovered:
		check(r.save_game(),"recovered progress can be saved normally")
		var preserved=g.save_path+".damaged-"+damaged.sha256_text().left(16)
		check(FileAccess.get_file_as_string(preserved)==damaged,"first recovery save archives damaged bytes without overwriting evidence")
		check(bytes(g.save_path+".bak")==first,"recovery save never promotes damaged primary to backup")
		check(r.save_game() and r.load_game() and r.flags.marker==7,"recovery remains stable after repeated save and load")
	var missing=fresh("missing-primary");missing.flags.marker=12;missing.save_game();missing.flags.marker=13;missing.save_game()
	DirAccess.remove_absolute(missing.save_path)
	check(missing.slot_records()[0].valid and missing.slot_records()[0].get("recovered",false),"missing primary also exposes validated backup")
	var broken=fresh("both-broken");write(broken.save_path,"broken");write(broken.save_path+".bak","also broken")
	check(not broken.slot_records()[0].valid and not broken.load_slot(1),"no fallback when both primary and backup fail validation")
	check(FileAccess.get_file_as_string(broken.save_path)=="broken" and FileAccess.get_file_as_string(broken.save_path+".bak")=="also broken","failed recovery preserves both originals")

func validation_checks():
	var g=fresh("validation");g.save_game();var base=State.read_json(g.save_path)
	for value in [null,"invalid",[],{"pages":[{"speaker":"旁白","text":"测试"}],"index":0},{"pages":[{"speaker":"旁白","text":"测试"}],"index":0,"return":"void"},{"pages":[{"speaker":"旁白","text":"测试"}],"index":0,"return":"hub","callback":123}]:
		var malformed=base.duplicate(true);malformed.flags.active_plot=value
		check(not g.SaveValidation.campaign_valid(g,malformed,g.SAVE_FIELDS),"reject malformed dialogue continuation: "+JSON.stringify(value))
	for field in ["schema","chapter","route","parties","convoy","roster","units","flags","rng_state","battle_start_snapshot"]:
		for bad in [null,[],"broken"]:
			if field=="units" and bad is Array:continue # Peaceful checkpoints legitimately have no actors.
			var malformed=base.duplicate(true);malformed[field]=bad
			write(g.save_path,malformed);var before=g.roster.duplicate(true)
			check(not g.load_game() and same(g.roster,before),"reject malformed "+field+" without partial live mutation: "+JSON.stringify(bad))

func retry_and_exchange_checks():
	var g=fresh("retry");g.flags.historical_marker=true;g.roster.otto.exp=37;g.world_node=2
	check(g.start_battle(101),"retry fixture enters battle through normal entry")
	g.story_events.clear();g.save_game();var snapshot=g.battle_start_snapshot.duplicate(true)
	var victim=g.living("enemy")[0]
	g.commit_strike({"attacker":"hunapu","defender":victim.id,"hp_after":0})
	check(g.kills==1,"real strike increments kill count before retry")
	g.find_unit("hunapu").exp+=19;g.flags.current_battle_marker=true;g.convoy.alm.append(11);g.random_bounded(100)
	g.turn=7;g.phase="enemy";check(g.save_game(),"mutated battle fixture can save")
	var r=restored(g.save_path)
	check(r.retry_battle(),"loaded battle retries normally")
	check(r.kills==0 and r.turn==1 and r.phase=="player","retry resets turn phase and current-battle kill count")
	check(same(r.units,snapshot.units) and same(r.roster,snapshot.roster),"retry restores pre-battle HP growth injury and equipment")
	check(same(r.convoy,snapshot.convoy) and r.flags.get("historical_marker",false) and not r.flags.has("current_battle_marker"),"retry reverses current loot and flags but keeps historical progress")
	check(r.rng_state==snapshot.rng_state and r.frame_counter==snapshot.frame_counter,"retry restores opening random state")
	check(r.save_game() and r.load_game() and r.kills==0,"retry state remains valid across next restart")
	# Interrupted animations must resume the last completed checkpoint. No
	# lifecycle handler is allowed to persist an individual strike mid-exchange.
	var a=g.find_unit("hunapu");var b=g.living("enemy")[0]
	g.retry_battle();a=g.find_unit("hunapu");b=g.living("enemy")[0]
	a.position=[3,10];b.position=[4,10];g.story_events.clear();g.save_game()
	var before=State.read_json(g.save_path);var exchange=g.plan_combat(a.id,b.id)
	check(not exchange.is_empty() and not exchange.events.is_empty(),"interruption fixture creates genuine combat plan")
	if not exchange.events.is_empty():
		g.commit_strike(exchange.events[0])
		var interrupted=restored(g.save_path)
		check(same(interrupted.units,before.units) and interrupted.rng_state==int(before.rng_state),"restart during an uncommitted animation rolls back the entire exchange")
		for event in exchange.events.slice(1):g.commit_strike(event)
		g.finish_exchange(exchange);g.save_game()
		var completed=State.read_json(g.save_path);var after=restored(g.save_path)
		check(same(after.units,completed.units) and after.find_unit(a.id).acted,"completed exchange restarts with damage EXP and acted flag together")

func historical_roundtrips():
	var paths=["campaign/natural-chapter-end-save.json","full-playtest-20261023/ch2/audit/audit-chapter3-start.json","full-playtest-20261023/ch3/followup/followup-chapter4-start.json","full-playtest-20261023/ch4/boundary-retry/boundary-retry-chapter5-start.json","full-playtest-20261023/ch5/current/current-J54-victory.json"]
	for source in paths:
		var path="res://reports/"+source;var fingerprint=bytes(path).hex_encode().sha256_text()
		var g=State.new();g.save_path=path
		check(g.load_game(),"historical boundary loads: "+source)
		g.save_path=cache.path_join(source.get_file());check(g.save_game(),"boundary writes to isolated copy: "+source)
		var first=State.read_json(g.save_path)
		for repeat in range(3):
			check(g.load_game() and g.save_game(),"boundary repeated reload "+str(repeat)+": "+source)
			var current=State.read_json(g.save_path)
			for field in ["roster","convoy","parties","route_positions","cleared_stages","battle_start_snapshot","rng_state","frame_counter","battle_settled"]:
				check(same(first[field],current[field]),"stable "+field+" after reload "+str(repeat)+": "+source)
		if int(g.chapter) in [3,4,5] and g.can_switch_route():
			var route_before=g.route;var roster_before=g.roster.duplicate(true);var convoy_before=g.convoy.duplicate(true)
			check(g.switch_route() and g.switch_route() and g.route==route_before and same(g.roster,roster_before) and same(g.convoy,convoy_before),"two route switches preserve ownership growth and supplies: "+source)
		if g.battle_settled:
			var roster_before=g.roster.duplicate(true);var convoy_before=g.convoy.duplicate(true)
			check(not g.complete_battle() and same(g.roster,roster_before) and same(g.convoy,convoy_before),"reloaded settled victory cannot grant EXP or loot again")
		check(bytes(path).hex_encode().sha256_text()==fingerprint,"historical source remains byte unchanged: "+source)
		sources.append({"path":path,"sha256_of_hex_bytes":fingerprint})

func run():
	cache="/private/tmp/revenge-save-assessment-"+str(Time.get_ticks_usec())+"/"
	if not OS.get_environment("SAVE_ASSESSMENT_OUT").is_empty():out=OS.get_environment("SAVE_ASSESSMENT_OUT")
	DirAccess.make_dir_recursive_absolute(cache);DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	io_checks();recovery_checks();validation_checks();retry_and_exchange_checks();historical_roundtrips()
	write(out.path_join("checks.json"),{"passed":failures.is_empty(),"count":checks.size(),"checks":checks,"failures":failures,"cache":cache,"sources":sources,"scope":"Controlled fault/restart fixtures and historical boundary copies; no natural full-playthrough claim and no iPhone operations."})
	print("SAVE_ASSESSMENT ",checks.size()," checks; failures: ",failures)
	quit(0 if failures.is_empty() else 1)
