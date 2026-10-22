extends "res://tests/tactical_review_play.gd"
## Captures real-input entry/field/victory checkpoints from this revision.
## The only changed state for a photograph is the cursor/camera and photo_viewport.
const PHOTO_OUT="res://reports/m41-redesign-20261022/screenshots/"
var photo_viewport:SubViewport
var photos=[]
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func picture(name:String,source:String,at:Vector2i,note_page:int=-1):
 ui.game.save_path=source;var loaded=ui.game.load_game();ui.game.save_path=PHOTO_OUT+"capture-working-save.json"
 if not loaded:record_failure("Checkpoint failed to load: "+source);return
 ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui.result_sequence_running=false;ui.ui_mode="inspect";ui._clear_menu();ui.phase_time=0;ui.notice_time=0;ui.held_direction=Vector2i.ZERO
 if ui.game.mode=="battle":cursor_to(at);ui._focus_battle(ui.game.cursor,true)
 else:ui._focus_battle(at,true) # Result screens intentionally do not accept battle cursor input.
 if note_page>=0:
  key(KEY_S);choose("new:goal")
  for i in range(30):
   if ui.view!="plot" or ui.plot_index>=mini(note_page,ui.plot_pages.size()-1):break
   key(KEY_Z)
  if ui.view=="plot":key(KEY_Z)
 ui.queue_redraw()
 for i in range(4):await process_frame
 await RenderingServer.frame_post_draw
 var file=PHOTO_OUT+name+".png";photo_viewport.get_texture().get_image().save_png(file)
 photos.append({"name":name,"path":file,"source":source,"stage":ui.game.battle_data.code,"turn":ui.game.turn,"map_revision":ui.game.battle_data.tactical_review_version,"outcome":ui.game.battle_outcome,"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(true),"size":[photo_viewport.size.x,photo_viewport.size.y]})
 print("MAP_POLISH_PHOTO ",name," ",ui.layout_errors)
 if note_page>=0:await settle()
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PHOTO_OUT))
 photo_viewport=SubViewport.new();photo_viewport.size=Vector2i(562,320);photo_viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(photo_viewport)
 ui=load("res://scenes/main.tscn").instantiate();photo_viewport.add_child(ui);await process_frame;ui.instant_mode=true
 var jobs=State.read_json("res://reports/m41-redesign-20261022/capture-jobs.json")
 for job in jobs.shots:
  photo_viewport.size=Vector2i(job.get("width",562),job.get("height",320));await process_frame
  await picture(str(job.name),str(job.source),Vector2i(job.focus[0],job.focus[1]),int(job.get("note_page",-1)))
  if abort:break
 var errors=[]
 for item in photos:errors.append_array(item.layout_errors)
 var f=FileAccess.open(PHOTO_OUT+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort and errors.is_empty(),"shots":photos,"layout_errors":errors,"failures":failures,"background_guard":true,"source":"Current real-input play checkpoints; no actor movement/stat edits for pictures."},"  "));f.close()
 ui.queue_free();await process_frame;ui=null;photo_viewport.queue_free();await process_frame;quit(0 if not abort and errors.is_empty() else 1)
