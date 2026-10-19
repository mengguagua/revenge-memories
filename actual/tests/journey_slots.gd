extends SceneTree
const State=preload("res://core/game_state.gd")
var checks: Array=[]
var failures: Array=[]
var folder="res://.cache/journey-slots-round1"
func _initialize():call_deferred("run")
func check(ok: bool,label: String):
 checks.append(label)
 if not ok:failures.append(label);push_error(label)
func fresh():
 var g=State.new();g.slot_directory=folder;g.new_game();return g
func clean():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
 for name in DirAccess.get_files_at(folder):DirAccess.remove_absolute(folder.path_join(name))
func run():
 clean();var g=fresh()
 check(g.slot_records().size()==5 and g.slot_records().all(func(r):return not r.exists),"Exactly five empty independent slots")
 for slot in range(1,6):
  g.play_seconds=slot*3671.0;g.flags.slot_test=slot
  check(g.save_to_slot(slot),"Write slot "+str(slot))
  var r=g.slot_records()[slot-1]
  check(r.valid and r.time.length()==16 and r.chapter=="序章" and r.location=="海峡城庆典","Time and prologue summary "+str(slot))
  check(r.seconds==slot*3671.0,"Play time saved in slot "+str(slot))
 for slot in range(1,6):
  check(g.load_slot(slot) and int(g.flags.slot_test)==slot and g.active_slot==slot,"Load independent progress and active autosave slot "+str(slot))
 g.load_slot(3);g.flags.slot_test=33;check(g.save_game(),"Autosave to selected slot")
 check(g.load_slot(2) and int(g.flags.slot_test)==2,"Autosave leaves other records intact")
 var before=g.roster.duplicate(true);var old_path=g.save_path;var old_slot=g.active_slot
 check(not g.load_slot(0) and not g.load_slot(6) and not g.save_to_slot(-1),"Reject out-of-range slots")
 check(g.roster==before and g.save_path==old_path and g.active_slot==old_slot,"Bad selection never mutates live state")
 var file=FileAccess.open(State.Journals.path_for(folder,4),FileAccess.WRITE);file.store_string('{"schema":3,"party":[]}');file.close()
 check(not g.slot_records()[3].valid and not g.load_slot(4),"Corrupt record is visible and cannot be loaded")
 check(g.roster==before and g.save_path==old_path and g.active_slot==old_slot,"Corrupt load preserves state and active slot")
 check(not FileAccess.file_exists(State.Journals.path_for(folder,4)+".tmp"),"Listing never writes or repairs records")
 var previous=g.slot_directory;g.slot_directory="res://.cache/journey-slots-no-parent/not-created"
 check(not g.save_to_slot(1) and g.save_path==old_path and g.active_slot==old_slot,"Write failure preserves active destination")
 g.slot_directory=previous
 g.load_slot(3)
 var current=State.read_json(g.save_path);var backup=State.read_json(g.save_path+".bak")
 check(int(current.flags.slot_test)==33 and int(backup.flags.slot_test)==3,"Atomic replacement preserves validated preceding checkpoint")
 clean();g=fresh();g.save_path=folder.path_join(State.Journals.LEGACY);g.flags.legacy_marker=true;check(g.save_game(),"Write genuine old single-file fixture")
 var original=FileAccess.get_file_as_bytes(g.save_path)
 var raw=State.read_json(g.save_path);raw.erase("journal");file=FileAccess.open(g.save_path,FileAccess.WRITE);file.store_string(JSON.stringify(raw));file.close();original=FileAccess.get_file_as_bytes(g.save_path)
 check(g.slot_records()[0].legacy and g.slot_records()[0].valid,"Old file appears in slot one without migration write")
 check(g.load_slot(1) and g.flags.legacy_marker and g.save_path==State.Journals.path_for(folder,1),"Legacy resume selects new slot path")
 check(g.save_game() and FileAccess.get_file_as_bytes(folder.path_join(State.Journals.LEGACY))==original,"First autosave preserves old file byte for byte")
 var slot=State.read_json(g.save_path);slot.journal={"play_seconds":"bad","saved_unix":"bad"};file=FileAccess.open(g.save_path,FileAccess.WRITE);file.store_string(JSON.stringify(slot));file.close()
 check(g.load_slot(1) and g.play_seconds==0 and g.slot_records()[0].valid,"Optional malformed metadata cannot break genuine progress")
 # Real gameplay checkpoint: phase, action, formation, story VM and equipment
 # are serialized by the existing validator rather than UI summary data.
 g=fresh();g.world_node=2;check(g.start_battle(101),"Enter real M11")
 g.story_events.clear();g.units[0].acted=true;var snapshot=g.units.duplicate(true);g.turn=3;g.phase="enemy";g.flags.slot_test="battle"
 check(g.save_to_slot(5),"Record enemy-phase battle checkpoint")
 var resumed=fresh();check(resumed.load_slot(5) and resumed.phase=="enemy" and resumed.turn==3 and resumed.units==snapshot,"Resume exact battle units, actions and enemy phase")
 var report={"passed":failures.is_empty(),"checks":checks.size(),"labels":checks,"failures":failures,"isolated_directory":folder,"real_user_saves_touched":false}
 var out=FileAccess.open("res://reports/journey-home-20261019/round1-state.json",FileAccess.WRITE);out.store_string(JSON.stringify(report,"  "));out.close()
 print("JOURNEY_ROUND1 ",checks.size()," failures ",failures);quit(0 if failures.is_empty() else 1)
