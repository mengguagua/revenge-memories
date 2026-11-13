extends "res://tests/ch5_environment_play.gd"
const Phone=preload("/Users/gcc/gaocc/project/revenge-memories/art-review/phantom-20261113/source/preview_phone.gd")
const Recorder=preload("/Users/gcc/gaocc/project/revenge-memories/art-review/phantom-20261113/source/recorder.gd")
const PHANTOM_OUT="res://reports/phantom-20261113/"
const PHANTOM_SOURCE="res://reports/chapter5-spatial-20261022/play/continuous-final/continuous-final-S51-deployment.json"
const PHANTOM_LABEL="round2"
var phantom_screen
var phantom_phone
var phantom_recorder
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func snapshot(name:String)->void:
 if abort:return
 var old=ui.game.save_path;ui.game.save_path=PHANTOM_OUT+PHANTOM_LABEL+"-"+name+".json"
 if not ui.game.save_game():record_failure("Checkpoint write failed: "+name)
 ui.game.save_path=old
func write_progress()->void:pass
func settle()->void:
 for i in range(18000):
  if abort:return
  var holding=phantom_recorder!=null and phantom_recorder.hold_reward
  if ui.menu_context=="mechanical_part" and not ui.menu_items.is_empty():
   choose("mechanical:body");await process_frame;continue
  elif ui.view=="battle" and ui.ui_mode=="target" and ui.mechanical_target_confirmed and not ui.busy:
   key(KEY_Z);await process_frame;continue
  elif ui.view in ["plot","reward"] and not holding:key(KEY_Z)
  elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
  if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:
   await process_frame
   if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"] and ui.menu_context!="mechanical_part" and ui.ui_mode!="target":return
  await process_frame
 record_failure("Phantom play did not release "+ui.view)
func run()->void:
 DirAccess.make_dir_recursive_absolute("/private/tmp/phantom-preview-20261113")
 var source_hash=FileAccess.get_sha256(PHANTOM_SOURCE)
 phantom_screen=SubViewport.new();phantom_screen.size=Vector2i(1334,750);phantom_screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(phantom_screen)
 phantom_phone=Phone.new();phantom_phone.journal_directory_override="/private/tmp/phantom-preview-20261113";phantom_screen.add_child(phantom_phone);await process_frame
 ui=phantom_phone.game_ui;ui.instant_mode=true
 ui.game.save_path=PHANTOM_SOURCE;assert(ui.game.load_game());ui.game.save_path="/private/tmp/phantom-preview-20261113/"+PHANTOM_LABEL+".json";assert(ui.game.retry_battle());assert(ui.game.stage_id==511)
 ui._resume_journey();await settle();ui.set_physics_process(false)
 phantom_recorder=Recorder.new();phantom_recorder.ui=ui;phantom_recorder.screen=phantom_screen;phantom_recorder.label=PHANTOM_LABEL;root.add_child(phantom_recorder);ui.phantom_recorder=phantom_recorder
 var caster=ui.game.find_unit("mireille");var before=caster.hp
 cursor_to(State.pos(caster));key(KEY_Z);key(KEY_Z);choose("magic")
 while str(ui.menu_actions[ui.menu_selected])!="spell:45":key(KEY_DOWN)
 await phantom_recorder.shot(PHANTOM_LABEL+"-spell")
 phantom_recorder.start(PHANTOM_LABEL+"-summon");ui.instant_mode=false;choose("spell:45");await settle()
 await create_timer(1.4).timeout
 await phantom_recorder.shot(PHANTOM_LABEL+"-summoned");phantom_recorder.stop();ui.instant_mode=true
 var phantoms=ui.game.units.filter(func(u):return ui.game.Phantoms.is_phantom(u))
 if phantoms.size()!=2 or caster.hp!=before-10 or not phantoms.all(func(u):return u.acted):record_failure("rank1 summon/count/newborn wait")
 await snapshot("after-summon")
 # Validate actual suspended save before continuing the same ordinary battle.
 var loaded=State.new();loaded.save_path=ui.game.save_path;assert(loaded.load_game())
 assert(loaded.flags.phantom_maps[str(loaded.stage_id)] and loaded.units.filter(func(u):return loaded.Phantoms.is_phantom(u)).size()==2)
 await battle(false)
 if abort:
  print("PHANTOM_DEBUG ",ui.view," ",ui.ui_mode," menu=",ui.menu_context," actions=",ui.menu_actions," confirmed=",ui.mechanical_target_confirmed," selected=",ui.game.selected_id," busy=",ui.busy," batch=",ui.batch_running)
  await phantom_recorder.shot(PHANTOM_LABEL+"-failure")
 var record={"passed":not abort and not battles.is_empty() and battles[-1].outcome=="victory","label":PHANTOM_LABEL,"source":PHANTOM_SOURCE,"source_unchanged":source_hash==FileAccess.get_sha256(PHANTOM_SOURCE),"key_inputs":inputs,"failures":failures,"battles":battles,"clips":phantom_recorder.clips,"receipts":phantom_recorder.receipts,"phantom_actions":phantom_recorder.phantom_actions,"scope":"Genuine learned-spell checkpoint; ordinary keyboard summon, battle actions and objectives. No attributes, spell unlocks, EXP, positions or victory conditions edited."}
 for action in record.phantom_actions:
  if int(action.turn)<=int(action.born):record.passed=false;record.failures.append("newborn acted in birth turn")
 var out=FileAccess.open(PHANTOM_OUT+PHANTOM_LABEL+"-play.json",FileAccess.WRITE);out.store_string(JSON.stringify(record,"  "));out.close()
 print("PHANTOM_PLAY_RESULT ",PHANTOM_LABEL," ",record.passed," inputs=",inputs," receipts=",record.receipts.size()," failures=",record.failures)
 ui.phantom_recorder=null;phantom_phone.queue_free();phantom_recorder.queue_free();await process_frame
 quit(0 if record.passed else 1)
