extends "res://tests/tactical_review_play.gd"
## Real renderer and genuine deployment checkpoints; only viewport/HUD framing
## differs for the complete-field plate. Normal landscape views retain the UI.
var capture_viewport: SubViewport
var redesign_shots: Array=[]
const CAPTURE_OUT="res://reports/battlefield-0.3.0/screenshots/"

func _initialize() -> void:
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")

func capture_shot(name: String,source: String,whole: bool) -> void:
 ui.queue_redraw()
 for i in range(4):await process_frame
 await RenderingServer.frame_post_draw
 var path=CAPTURE_OUT+name+".png"
 capture_viewport.get_texture().get_image().save_png(path)
 redesign_shots.append({"name":name,"path":path,"source":source,"fixture":false,"view":ui.view,"stage":ui.game.battle_data.code,"turn":ui.game.turn,"canvas":[capture_viewport.size.x,capture_viewport.size.y],"layout_errors":ui.layout_errors.duplicate(),"map_revision":ui.game.battle_data.tactical_review_version,"art_revision":ui.game.battle_data.art_style_version,"whole_map":whole,"hud":"Focus cursor and terrain tooltip omitted for full-field plate" if whole else "Normal landscape battle UI; white arrow is the current input cursor","permanent_object_arrows":false})
 print("REDESIGN_SHOT ",name," ",ui.layout_errors)

func run() -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(CAPTURE_OUT))
 review_out="res://reports/battlefield-0.3.0/"
 capture_viewport=SubViewport.new();capture_viewport.size=Vector2i(426,240);capture_viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(capture_viewport)
 ui=load("res://scenes/main.tscn").instantiate();capture_viewport.add_child(ui);await process_frame;ui.instant_mode=true
 var codes: PackedStringArray=["M11","M12","M13","M14","M15","S11","S12","F21","F22","F23","F24","F25","F26","S21","S22"]
 if not OS.get_environment("BATTLEFIELD_CODES").is_empty():codes=OS.get_environment("BATTLEFIELD_CODES").split(",")
 for code in codes:
  var source=("res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/")+"natural-"+code+"-deployment-save.json"
  ui.game.save_path=source
  var loaded=ui.game.load_game();ui.game.save_path=CAPTURE_OUT+"working-save.json"
  if not loaded:record_failure("Cannot load genuine opening "+code);break
  ui.game.save_path=CAPTURE_OUT+"working-save.json";ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui.phase_time=0;ui.notice_time=0
  var target=ui.game.world_node
  key(KEY_S);choose("new:prepare");await settle();await go(target)
  key(KEY_Z);choose("new:battle");await settle();ui.phase_time=0;ui.notice_time=0
  var map=ui.game.battle_data.map
  capture_viewport.size=Vector2i((map.width+4)*16,(map.height+4)*16);await process_frame
  cursor_to(Vector2i.ZERO);ui._focus_battle(ui.game.cursor,true);ui.ui_mode="whole_capture"
  await capture_shot(code+"-whole",source,true)
  capture_viewport.size=Vector2i(426,240);await process_frame;ui.ui_mode="inspect"
  cursor_to(State.pos(ui.game.find_unit(ui.game.leader_id())));ui._focus_battle(ui.game.cursor,true)
  await capture_shot(code+"-deployment",source,false)
  var at=Vector2i(map.width/2,map.height/2)
  if code=="M11":at=Vector2i(20,10)
  if code=="M15":at=Vector2i(25,12)
  if code=="F24":at=Vector2i(ui.game.battle_data.targets[0][0],ui.game.battle_data.targets[0][1])
  cursor_to(at);ui._focus_battle(ui.game.cursor,true)
  await capture_shot(code+"-terrain",source,false)
  var surface_views={"M15":[["coast",14,1],["walkway",26,27]],"F25":[["walkway",24,7]],"F26":[["walkway",26,18]],"M11":[["bridge",25,8]],"S12":[["bridge",17,12]],"S22":[["coast",27,25]]}
  for detail in surface_views.get(code,[]):
   cursor_to(Vector2i(detail[1],detail[2]));ui._focus_battle(ui.game.cursor,true)
   await capture_shot(code+"-"+str(detail[0]),source,false)
  if code in ["F23","F24"]:
   var beach=Vector2i(-1,-1)
   for y in range(1,map.height-1):
    for x in range(1,map.width-1):
     if ui.game.battle_data.visual_ground[y][x]!="d":continue
     if [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT].any(func(d):return ui.game.battle_data.visual_ground[y+d.y][x+d.x] in [".","f"]):beach=Vector2i(x,y);break
    if beach.x>=0:break
   if beach.x>=0:
    cursor_to(beach);ui._focus_battle(beach,true)
    await capture_shot(code+"-beach",source,false)
  if code in ["M12","M15"]:
   var point=ui.game.battle_data.objects[0].position if code=="M12" else ui.game.battle_data.exit
   cursor_to(Vector2i(point[0],point[1]));ui._focus_battle(ui.game.cursor,true)
   await capture_shot(code+("-objective" if code=="M12" else "-escape"),source,false)
  if code=="F22":
   var site=ui.game.battle_data.building_sites.filter(func(s):return s.label=="甲板掩体")[0]
   cursor_to(Vector2i(site.position[0],site.position[1]));ui._focus_battle(ui.game.cursor,true)
   await capture_shot(code+"-building-terrain",source,false)
  if code=="M13":
   var post=ui.game.battle_data.building_sites[0]
   cursor_to(Vector2i(post.position[0],post.position[1]));ui._focus_battle(ui.game.cursor,true)
   await capture_shot(code+"-building-terrain",source,false)
  if code=="M14":
   var controls=ui.game.battle_data.objects.filter(func(o):return o.kind=="control")
   for i in range(controls.size()):
    cursor_to(Vector2i(controls[i].position[0],controls[i].position[1]));ui._focus_battle(ui.game.cursor,true)
    await capture_shot(code+("-south-checkpoint" if i==0 else "-east-checkpoint"),source,false)
   var fence=ui.game.battle_data.camp_checkpoints[0].fences[0]
   cursor_to(Vector2i(fence[0],fence[1]));ui._focus_battle(ui.game.cursor,true)
   await capture_shot(code+"-palisade",source,false)
  var buildings=ui.game.battle_data.objects.filter(func(o):return o.kind=="visit")
  if not buildings.is_empty():
   var entrance=Vector2i(buildings[0].approach[0],buildings[0].approach[1])
   cursor_to(entrance);ui._focus_battle(ui.game.cursor,true)
   await capture_shot(code+"-entrance",source,false)
  if code=="F24":
   var shelter=ui.game.battle_data.objects.filter(func(o):return o.id=="shelter")[0]
   cursor_to(Vector2i(shelter.position[0],shelter.position[1]));ui._focus_battle(ui.game.cursor,true)
   await capture_shot(code+"-shelter",source,false)
  if code in ["F21","F22"]:
   var object=ui.game.battle_data.objects.filter(func(o):return o.kind=="visit")[0]
   var front=Vector2i(object.approach[0],object.approach[1])
   var visitor=ui.game.unit_at(front)
   if visitor.is_empty():
    for member in ui.game.party:
     var candidate=ui.game.find_unit(member)
     if not candidate.is_empty() and ui.game.reachable(candidate).costs.has(front) and ui.game.can_stop(candidate,front):visitor=candidate;break
   if visitor.is_empty():record_failure(code+" visit approach unavailable at entry");break
   cursor_to(State.pos(visitor));key(KEY_Z);cursor_to(front);key(KEY_Z);await settle()
   await capture_shot(code+"-visit-menu",source,false)
   choose("interact:"+str(object.id))
   for i in range(4):await process_frame
   if ui.view!="plot":record_failure(code+" visit did not enter dialogue");break
   key(KEY_Z)
   await capture_shot(code+"-visit-dialogue",source,false)
   await settle()
   if not ui.game.flags.quest.objects.get(object.id,false):record_failure(code+" visit flag missing")
  if code=="M14":
   var owned_source=""
   var owned_id=""
   for id_ in ["M14_control_0","M14_control_1"]:
    var candidate="res://reports/battlefield-0.3.0/play/camp-0.3.5/camp-0.3.5-M14-controlled-"+id_+".json"
    if FileAccess.file_exists(candidate):owned_source=candidate;owned_id=id_;break
   if not owned_source.is_empty():
    ui.game.save_path=owned_source;var owned_loaded=ui.game.load_game();ui.game.save_path=CAPTURE_OUT+"working-save.json"
    if not owned_loaded:record_failure("M14 captured flag checkpoint cannot load");break
    ui.view="battle";ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui.phase_time=0;ui.notice_time=0
    var point=ui.game.battle_data.objects.filter(func(o):return o.id==owned_id)[0]
    cursor_to(Vector2i(point.position[0],point.position[1]));ui._focus_battle(ui.game.cursor,true)
    await capture_shot(code+"-controlled",owned_source,false)
   else:record_failure("M14 genuine owned-flag replay checkpoint missing")
 var bad=[]
 for item in redesign_shots:bad.append_array(item.layout_errors)
 var report={"passed":not abort and bad.is_empty(),"background_guard":true,"visible_windows":false,"shots":redesign_shots,"layout_errors":bad,"failures":failures,"scope":"Genuine saved roster; ordinary preparation/re-entry adopts redesigned field; enlarged full-field and normal landscape runtime views."}
 var report_name="captures.json"
 if not OS.get_environment("BATTLEFIELD_CODES").is_empty():report_name="captures-"+OS.get_environment("BATTLEFIELD_CODES").replace(",","-")+".json"
 var f=FileAccess.open(CAPTURE_OUT+report_name,FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 # A focused visual fix replaces only its own capture records. Keep the
 # other audited scenes instead of discarding the complete gallery manifest.
 if report_name!="captures.json" and report.passed:
  var previous=State.read_json(CAPTURE_OUT+"captures.json")
  var replacements={}
  for shot in redesign_shots:replacements[shot.name]=shot
  for i in range(previous.get("shots",[]).size()):
   var name_=str(previous.shots[i].name)
   if replacements.has(name_):previous.shots[i]=replacements[name_]
  var known={}
  for shot in previous.get("shots",[]):known[shot.name]=true
  for shot in redesign_shots:
   if not known.has(shot.name):previous.shots.append(shot)
  f=FileAccess.open(CAPTURE_OUT+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify(previous,"  "));f.close()
 ui.queue_free();await process_frame;ui=null;capture_viewport.queue_free();await process_frame
 quit(0 if report.passed else 1)
