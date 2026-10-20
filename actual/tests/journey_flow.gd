extends SceneTree
const State=preload("res://core/game_state.gd")
var checks: Array=[]
var failures: Array=[]
var ui
var viewport
var folder="res://.cache/journey-flow-round2"
func _initialize():call_deferred("run")
func check(ok: bool,label: String):
 checks.append(label)
 if not ok:failures.append(label);push_error(label)
func key(code: int):
 var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
 e=InputEventKey.new();e.physical_keycode=code;e.pressed=false;ui._input(e)
func action(name: String):
 check(ui.menu_actions.has(name),"Menu exposes "+name)
 if ui.menu_actions.has(name):ui.menu_selected=ui.menu_actions.find(name);key(KEY_Z)
func mouse(point: Vector2):
 var e=InputEventMouseButton.new();e.position=point+ui._canvas_offset();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=true;ui._input(e)
func new_ui():
 if ui!=null:ui.queue_free();await process_frame
 ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=folder;viewport.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
func open_continue(slot: int):
 ui._show_title();key(KEY_DOWN);key(KEY_Z)
 while ui.journey.selected!=slot-1:key(KEY_DOWN)
 key(KEY_Z)
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
 for name in DirAccess.get_files_at(folder):DirAccess.remove_absolute(folder.path_join(name))
 viewport=SubViewport.new();viewport.size=Vector2i(426,240);root.add_child(viewport);await new_ui()
 check(ui.view=="title" and ui.title_menu,"Homepage immediately exposes choices")
 key(KEY_Z);check(ui.view=="journal" and ui.journey.intent=="new","Start game opens five-slot picker")
 key(KEY_UP);check(ui.journey.selected==4,"Keyboard wraps across all five slots")
 key(KEY_Z);check(ui.view=="hub" and ui.game.hub_record=="P00" and ui.game.active_slot==5,"Empty fifth slot starts genuine prologue")
 check(ui.game.slot_records()[4].valid,"Automatic first save is a valid prologue checkpoint")
 var fifth=FileAccess.get_file_as_bytes(State.Journals.path_for(folder,5))
 ui.game.flags.flow_marker=22;key(KEY_S);action("new:save")
 check(ui.view=="journal" and ui.journey.intent=="save","Actual hub S menu opens save picker")
 key(KEY_DOWN);key(KEY_DOWN);key(KEY_Z)
 check(ui.view=="hub" and ui.game.active_slot==2 and ui.journey.saved_left>0,"Save to empty slot two switches future autosaves and shows timestamp feedback")
 check(FileAccess.get_file_as_bytes(State.Journals.path_for(folder,5))==fifth,"Save-as does not touch original slot five")
 var second=FileAccess.get_file_as_bytes(ui.game.save_path)
 key(KEY_S);action("new:save");key(KEY_Z)
 check(ui.view=="journal_confirm" and ui.journey.confirm_choice==0,"Occupied save defaults to safe return choice")
 key(KEY_Z);check(ui.view=="journal" and FileAccess.get_file_as_bytes(ui.game.save_path)==second,"Confirming default choice does not overwrite")
 key(KEY_X);check(ui.view=="hub","Cancel save returns to same gameplay view")
 key(KEY_S);action("title")
 check(ui.view=="title" and ui.game.mode=="hub","Return to homepage preserves checkpoint mode")
 key(KEY_Z)
 while ui.journey.selected!=1:key(KEY_DOWN)
 key(KEY_Z);key(KEY_X)
 check(ui.view=="journal" and FileAccess.get_file_as_bytes(State.Journals.path_for(folder,2))==second,"Cancel new-game overwrite preserves existing record")
 key(KEY_X);await open_continue(5)
 check(ui.view=="hub" and not ui.game.flags.has("flow_marker"),"Continue restores chosen slot, not latest in-memory progress")
 check(FileAccess.get_file_as_bytes(State.Journals.path_for(folder,5))==fifth,"Loading a hub does not rewrite its recorded time or bytes")
 var f=FileAccess.open(State.Journals.path_for(folder,1),FileAccess.WRITE);f.store_string("broken-json");f.close()
 await open_continue(1)
 check(ui.view=="journal" and ui.journey.message.contains("无法读取"),"Corrupt record produces in-place readable feedback")
 check(FileAccess.get_file_as_string(State.Journals.path_for(folder,1))=="broken-json","Corrupt record remains byte intact")
 ui.journey.selected=3;key(KEY_Z);check(ui.journey.message.contains("尚无记录"),"Empty load selection has explicit feedback")
 var selected=ui.journey.selected;mouse(Vector2(-80,45));check(ui.journey.selected==selected and ui.view=="journal","Panel margins never activate another slot")
 mouse(ui.journey.art.row_rect(1).get_center());check(ui.view=="hub" and ui.game.active_slot==2 and int(ui.game.flags.flow_marker)==22,"Mouse selects and resumes the actual clicked row")
 # Genuine plot writer creates the checkpoint, then a fresh controller resumes it.
 ui.play_pages([{"speaker":"旁白","text":"海峡城的灯火仍在。"},{"speaker":"胡纳普","text":"我会记得。"}],"hub")
 key(KEY_Z);key(KEY_Z)
 check(ui.view=="plot" and ui.plot_index==1,"Real dialogue input reaches second page")
 await new_ui();await open_continue(2)
 check(ui.view=="plot" and ui.plot_index==1 and str(ui.plot_pages[ui.plot_index].text)=="我会记得。","Fresh controller resumes saved dialogue at exact page")
 key(KEY_Z);key(KEY_Z);await process_frame
 check(ui.view=="hub" and not ui.game.flags.has("active_plot"),"Finishing resumed dialogue returns to playable hub")
 var g=State.new();g.slot_directory=folder;g.new_game();g.world_node=2;g.hub_record="H01";g.start_battle(101);g.story_events.clear();g.phase="enemy";g.turn=3
 for enemy in g.living("enemy"):enemy.acted=true
 var hp=g.find_unit("hunapu").hp;var kills=g.kills
 check(g.save_to_slot(3),"Real enemy-phase checkpoint saved to third slot")
 await open_continue(3)
 for i in range(20):
  if not ui.busy and not ui.batch_running:break
  await process_frame
 check(ui.view=="battle" and ui.game.phase=="player" and ui.game.turn==4,"Continue executes persisted enemy phase and returns control once")
 check(ui.game.find_unit("hunapu").hp==hp and ui.game.kills==kills,"Already acted enemies never repeat damage or kills")
 var old_path=ui.game.save_path;var active=ui.game.active_slot
 ui.game.slot_directory="res://.cache/journey-flow-no-parent/missing";key(KEY_S);action("save");key(KEY_Z)
 check(ui.view=="journal" and ui.journey.message.contains("失败") and ui.game.save_path==old_path and ui.game.active_slot==active,"Disk failure keeps prior progress and active destination")
 key(KEY_X);ui.game.slot_directory=folder
 check(ui.view=="battle","Failed-save cancellation returns to battle")
 # Mouse uses the expanded native coordinates at both display proportions.
 for width in [256,426]:
  viewport.size=Vector2i(width,240);ui._show_title();await process_frame
  mouse(ui.journey.title_button(0).get_center())
  check(ui.view=="journal" and ui.journey.intent=="new","Start button mouse geometry "+str(width))
  ui.journey.selected=1;key(KEY_Z)
  check(ui.view=="journal_confirm","Existing new-game record requires confirmation "+str(width))
  mouse(ui.journey.art.confirm_button(0).get_center())
  check(ui.view=="journal","Mouse cancel is aligned with displayed button "+str(width))
  key(KEY_X)
 var untouched=FileAccess.get_file_as_bytes(State.Journals.path_for(folder,5))
 key(KEY_Z)
 while ui.journey.selected!=1:key(KEY_DOWN)
 key(KEY_Z);key(KEY_RIGHT);key(KEY_Z)
 check(ui.view=="hub" and ui.game.active_slot==2 and not ui.game.flags.has("flow_marker"),"Explicit new-game overwrite starts a fresh prologue only in chosen slot")
 ui.game.flags.flow_marker=77;key(KEY_S);action("new:save");key(KEY_Z);key(KEY_RIGHT);key(KEY_Z)
 check(ui.view=="hub" and int(State.read_json(ui.game.save_path).flags.get("flow_marker",0))==77,"Explicit manual overwrite persists current gameplay")
 check(FileAccess.get_file_as_bytes(State.Journals.path_for(folder,5))==untouched,"Both confirmed overwrites leave neighboring record untouched")
 var report={"passed":failures.is_empty(),"checks":checks.size(),"labels":checks,"failures":failures,"actual_input":true,"user_saves_touched":false,"fixture_scope":"Genuine writer/UI + isolated checkpoints. Enemy phase fixture has already-acted enemies; verifies resumability and no duplicate actions, not a natural battle victory."}
 var out=FileAccess.open("res://reports/journey-home-20261019/round2-flow.json",FileAccess.WRITE);out.store_string(JSON.stringify(report,"  "));out.close()
 print("JOURNEY_ROUND2 ",checks.size()," failures ",failures)
 ui.queue_free();await process_frame;quit(0 if failures.is_empty() else 1)
