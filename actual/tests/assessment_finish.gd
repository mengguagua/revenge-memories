extends SceneTree
const State=preload("res://core/game_state.gd")
const SOURCE="res://reports/full-assessment-20261025/campaign-final-r5/ch5/chain-ending-complete.json"
const OUT="res://reports/full-assessment-20261025/"
var checks=[]
var failures=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String)->void:
 checks.append({"label":label,"passed":ok})
 if not ok:failures.append(label);push_error(label)
func key(ui,code:int)->void:
 var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
 e=InputEventKey.new();e.physical_keycode=code;ui._input(e)
func run()->void:
 var folder="/private/tmp/revenge-assessment-ending-"+str(Time.get_ticks_usec())
 DirAccess.make_dir_recursive_absolute(folder)
 var before=State.read_json(SOURCE);var hash=FileAccess.get_sha256(SOURCE)
 var destination=folder+"/journey-slot-1.json"
 check(DirAccess.copy_absolute(ProjectSettings.globalize_path(SOURCE),destination)==OK,"Final lineage copied into isolated journal")
 var ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=folder;ui.game.save_path=destination
 root.add_child(ui);await process_frame;ui.instant_mode=true
 check(ui.view=="title" and ui.title_selected==1,"Homepage selects continue for valid final journal")
 key(ui,KEY_Z);check(ui.view=="journal" and ui.journey.intent=="load","Ordinary continue opens journal list")
 key(ui,KEY_Z)
 for frame in range(5):await process_frame
 check(ui.view=="ending","Completed journal resumes ending through actual menu")
 check(ui.game.flags.get("campaign_complete",false) and ui.game.flags.get("ending_done",false),"Campaign and viewed-ending completion survive reload")
 check(ui.game.cleared_stages.size()==40,"All 40 victories retained")
 check(JSON.parse_string(JSON.stringify(ui.game.roster))==before.roster,"Final growth, casualties and equipment unchanged")
 check(JSON.parse_string(JSON.stringify(ui.game.convoy))==before.convoy,"Final stored rewards unchanged")
 check(ui.game.save_game(),"Completed state can be saved again")
 var restored=State.new();restored.save_path=destination
 check(restored.load_game(),"New completed save is loadable")
 check(JSON.parse_string(JSON.stringify(restored.roster))==before.roster and JSON.parse_string(JSON.stringify(restored.convoy))==before.convoy,"Repeated completed load does not duplicate rewards or growth")
 check(FileAccess.get_sha256(SOURCE)==hash,"Original final lineage evidence remains untouched")
 var f=FileAccess.open(OUT+"ending-reload-checks.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"source":SOURCE,"source_sha256":hash},"  "));f.close()
 print("ENDING_RELOAD ",checks.size()," ",JSON.stringify(failures));ui.queue_free();await process_frame;quit(0 if failures.is_empty() else 1)
