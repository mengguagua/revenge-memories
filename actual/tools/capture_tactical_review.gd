extends "res://tests/tactical_review_play.gd"
## Runtime captures from genuine saves and normal menu/route inputs.
var shots: Array=[]
var capture_viewport: SubViewport
const SHOT_OUT="res://reports/review-0.2.1/screenshots/"
func _initialize() -> void:
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func load_checkpoint(path: String) -> bool:
 ui.game.save_path=path
 if not ui.game.load_game():record_failure("Screenshot source does not load: "+path);return false
 ui.game.save_path=SHOT_OUT+"working-save.json";ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui._clear_menu();ui.phase_time=0;ui.notice_time=0;ui.held_direction=Vector2i.ZERO
 ui._focus_battle(ui.game.cursor,true);return true
func shot(name: String,source_path: String,scope: String) -> void:
 if abort:return
 ui.queue_redraw()
 for frame in range(4):await process_frame
 await RenderingServer.frame_post_draw
 var path=SHOT_OUT+name+".png";capture_viewport.get_texture().get_image().save_png(path)
 shots.append({"name":name,"path":path,"source":source_path,"scope":scope,"fixture":false,"view":ui.view,"stage":ui.game.battle_data.code,"turn":ui.game.turn,"canvas":[capture_viewport.size.x,capture_viewport.size.y],"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(true),"map_revision":ui.game.battle_data.get("tactical_review_version","0.2.0")})
 print("TACTICAL_SHOT ",name," ",ui.layout_errors)
func run() -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SHOT_OUT))
 capture_viewport=SubViewport.new();capture_viewport.size=Vector2i(1024,576);capture_viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(capture_viewport)
 ui=load("res://scenes/main.tscn").instantiate();capture_viewport.add_child(ui);await process_frame;ui.instant_mode=true
 for code in ["M11","M12","M13","M14","M15","S11","S12","F21","F22","F23","F24","F25","F26","S21","S22"]:
  var source=("res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/")+"natural-"+code+"-deployment-save.json"
  if not load_checkpoint(source):break
  var target_node=ui.game.world_node
  key(KEY_S);choose("new:prepare");await settle();await go(target_node)
  key(KEY_Z);choose("new:battle");await settle();ui.phase_time=0
  capture_viewport.size=Vector2i(1024,576);await process_frame
  cursor_to(Vector2i(0,0));ui._focus_battle(ui.game.cursor,true)
  await shot(code+"-whole",source,"Actual roster, fresh current-map entry through preparation and world-route input, wide viewport")
  capture_viewport.size=Vector2i(426,240);await process_frame
  var focus=Vector2i(ui.game.battle_data.map.width/2,ui.game.battle_data.map.height/2)
  cursor_to(focus);ui._focus_battle(ui.game.cursor,true)
  await shot(code+"-layout",source,"Actual current battle layout and terrain information, landscape viewport")
  cursor_to(State.pos(ui.game.find_unit(ui.game.leader_id())));ui._focus_battle(ui.game.cursor,true)
  await shot(code+"-unit-card",source,"Current portrait-free tactical card includes original HP/experience and real terrain avoidance")
  if code in ["M11","M14"]:
   var id="lance" if code=="M14" else ui.game.leader_id();var unit=ui.game.find_unit(id)
   cursor_to(State.pos(unit));key(KEY_Z)
   var closest=Vector2i(-1,-1);var best_distance=999
   for y in range(ui.game.battle_data.map.height):
    for x in range(ui.game.battle_data.map.width):
     var at=Vector2i(x,y)
     if ui.game.category(at)==1 and distance(State.pos(unit),at)<best_distance:closest=at;best_distance=distance(State.pos(unit),at)
   if closest.x>=0:
    cursor_to(closest);ui._focus_battle(ui.game.cursor,true);await shot(code+"-forest-cost",source,"Normal unit selection and cursor keys show actual forest avoidance and class movement cost")
   key(KEY_X)
  if code=="F25":
   cursor_to(Vector2i(16,8));ui._focus_battle(ui.game.cursor,true)
   await shot("F25-warehouse-blocking",source,"New complete warehouse footprint and actual ground obstruction tooltip")
  if code=="M13":
   key(KEY_S);choose("new:goal");await process_frame;key(KEY_Z)
   # Show the authored tactical explanation after the objective page.
   key(KEY_Z);await process_frame;key(KEY_Z)
   await shot("M13-tactical-notes",source,"Actual battle-objective menu explains two defended entrances and eastern bypass")
   await settle()
 var details=[
  ["round1-naval-F21-field","F21-real-boarding",Vector2i(12,11)],
  ["round2-intercept-M13-field","M13-real-courtyard",Vector2i(12,12)],
  ["round2-F25-field","F25-real-assault",Vector2i(17,15)],
  ["round2-intercept-S22-field","S22-real-flanking",Vector2i(10,9)],
  ["round2-F26-boats","F26-real-escort",Vector2i(14,18)],
  ["round2-tower-M15-field","M15-real-advance",Vector2i(14,15)]
 ]
 for item in details:
  var source="res://reports/review-0.2.1/"+str(item[0])+".json"
  if not FileAccess.file_exists(source):continue
  if not load_checkpoint(source):break
  cursor_to(item[2]);ui._focus_battle(ui.game.cursor,true)
  await shot(item[1],source,"Actual input-play checkpoint from this review; only cursor/camera changed")
 for size_ in [Vector2i(256,240),Vector2i(426,266),Vector2i(562,260)]:
  capture_viewport.size=size_;await process_frame
  var source="res://reports/review-0.2.1/round2-F25-field.json"
  if not load_checkpoint(source):break
  cursor_to(Vector2i(18,8));ui._focus_battle(ui.game.cursor,true)
  await shot("F25-layout-"+str(size_.x)+"x"+str(size_.y),source,"Landscape size check for complete warehouse, impassable ground and text padding")
 var bad=[]
 for item in shots:bad.append_array(item.layout_errors)
 var report={"passed":not abort and bad.is_empty(),"shots":shots,"layout_errors":bad,"failures":failures,"background_guard":true,"visible_windows":false,"scope":"Actual runtime captures from unchanged genuine roster checkpoints and legal menu/cursor inputs; no painted map mockups"}
 var f=FileAccess.open(SHOT_OUT+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 await settle();ui.queue_free();await process_frame;ui=null;capture_viewport.queue_free();await process_frame;quit(0 if report.passed else 1)
