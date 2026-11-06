extends "res://tests/full_audit_ch5.gd"
## Changed text only: actual objective menus, bounded screenshot selection.
const PHOTO_OUT="res://reports/full-playtest-20261023/visual/"
var audit_viewport:SubViewport
var checked_pages=[]
var audit_shots=[]
var drawing_errors=[]
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run()->void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PHOTO_OUT))
 audit_viewport=SubViewport.new();audit_viewport.size=Vector2i(562,320)
 audit_viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(audit_viewport)
 var jobs: Array=JSON.parse_string(FileAccess.get_file_as_string("res://reports/full-playtest-20261023/visual-jobs.json"))
 for job in jobs:
  var hash=FileAccess.get_file_as_string(job.source).sha256_text()
  ui=load("res://scenes/main.tscn").instantiate();audit_viewport.add_child(ui);await process_frame;ui.instant_mode=true
  ui.game.save_path=job.source
  if not ui.game.load_game():record_failure("Visual source cannot load: "+str(job.code));break
  ui.game.save_path=PHOTO_OUT+"working.json";ui._resume_journey();await settle()
  var node=ui.game.world_node
  if ui.game.mode=="battle":key(KEY_S);choose("new:prepare");await settle()
  await go(node);key(KEY_Z);choose("new:battle");await settle()
  if str(ui.game.battle_data.code)!=job.code:record_failure("Visual entry mismatch: "+str(job.code));break
  key(KEY_S);choose("new:goal")
  var photographed=false
  for step in range(100):
   if abort or ui.view!="plot":break
   var index=ui.plot_index;var page=ui.plot_pages[index].duplicate(true)
   if int(ui.dialogue_reveal)<str(page.text).length():key(KEY_Z)
   ui.queue_redraw()
   for frame in range(3):await process_frame
   await RenderingServer.frame_post_draw
   checked_pages.append({"code":job.code,"page":index,"speaker":page.speaker,"text":page.text,"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(true)})
   drawing_errors.append_array(ui.layout_errors)
   if not photographed and not str(job.capture_keyword).is_empty() and str(page.text).contains(job.capture_keyword):
    var path=PHOTO_OUT+str(job.code)+"-guidance.png"
    var pixels=audit_viewport.get_texture().get_image();pixels.save_png(path)
    audit_shots.append({"code":job.code,"path":path,"page":page,"size":[pixels.get_width(),pixels.get_height()],"layout_errors":ui.layout_errors.duplicate()});photographed=true
   key(KEY_Z)
  if not str(job.capture_keyword).is_empty() and not photographed:record_failure("Changed guidance page not encountered: "+str(job.code))
  if FileAccess.get_file_as_string(job.source).sha256_text()!=hash:record_failure("Visual source modified: "+str(job.code))
  print("FULL_AUDIT_GUIDANCE ",job.code," pages=",ui.plot_pages.size()," errors=",drawing_errors.size())
  ui.queue_free();await process_frame;ui=null
  if abort:break
 var coverage_ok=jobs.size()==9 and checked_pages.size()>=9 and audit_shots.size()==3
 var f=FileAccess.open(PHOTO_OUT+"checks.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":not abort and drawing_errors.is_empty() and coverage_ok,"failures":failures,"layout_errors":drawing_errors,"pages":checked_pages,"shots":audit_shots,"coverage_ok":coverage_ok,"background_guard":true,"inputs":inputs,"scope":"Nine current objective menus after normal reentry; no battles repeated. Only three distinct changed-guidance screenshots saved."},"  "));f.close()
 audit_viewport.queue_free();await process_frame
 quit(1 if abort or not drawing_errors.is_empty() or not coverage_ok else 0)
