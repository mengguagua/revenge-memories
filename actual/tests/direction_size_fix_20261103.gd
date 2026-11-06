extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/direction-size-fix-20261103/"
const CACHE="/private/tmp/direction-size-fix-20261103/"
var checks=[];var errors=[];var evidence={};var shots=[];var visual=false;var screen;var phone;var ui
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func physical(rect:Rect2):return Rect2(phone.safe_area.position+rect.position*phone.pixel_scale,rect.size*phone.pixel_scale)
func frame(name:String,capture:bool=true):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(phone.layout_errors.is_empty() and ui.layout_errors.is_empty(),name+" material, glyph and touch safe areas: "+str(phone.layout_errors)+str(ui.layout_errors))
  if capture:screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func material_check():
 var source=phone.MATERIAL.get_image()
 if source.is_compressed():source.decompress()
 var left=source.get_width();var top=source.get_height();var right=-1;var bottom=-1
 for y in range(source.get_height()):
  for x in range(source.get_width()):
   if source.get_pixel(x,y).a*255<10:continue
   left=mini(left,x);top=mini(top,y);right=maxi(right,x);bottom=maxi(bottom,y)
 var start=Vector2(left,top);var end=Vector2(source.get_width()-right-1,source.get_height()-bottom-1)
 check(start==phone.DIRECTION_MATERIAL_START and end==phone.DIRECTION_MATERIAL_END,"visible bounds match actual bitmap alpha, including asymmetric transparent padding")
 evidence.material={"size":str(source.get_size()),"start":str(start),"end":str(end),"threshold":10}
func geometry(label:String):
 var keys=phone.buttons.filter(func(b):return phone.DIRECTION_KEYS.has(b.key));check(keys.size()==4,label+" all four directions present")
 var bounds=keys[0].visible_rect;var rows=[]
 for b in keys:bounds=bounds.merge(b.visible_rect)
 check(bounds.size.x==bounds.size.y,label+" actual visible periphery is square")
 for i in range(keys.size()):
  var b=keys[i];var face:Rect2=b.visible_rect
  check(face.size.x==face.size.y,label+" individual visible button is square")
  if label!="minimum":check(b.rect.size==Vector2(43,45) and face.size==Vector2(33,33),label+" original bitmap width restored, not the shrunken35px version")
  check(phone.safe_area.encloses(physical(face)) and phone.safe_area.encloses(physical(b.hit_rect)),label+" visible material and touch both stay safe")
  check(not phone.game_rect.intersects(physical(face)) and not phone.game_rect.intersects(physical(b.hit_rect)),label+" visible material and touch both clear central content")
  check(b.hit_rect.encloses(face),label+" all visible button pixels are clickable")
  var hit=physical(face).get_center();check(phone._button_at(hit)==int(b.key),label+" visible center dispatches correct direction")
  for j in range(i):check(not face.intersects(keys[j].visible_rect) and not b.hit_rect.intersects(keys[j].hit_rect),label+" adjacent visible buttons and touch rectangles do not overlap")
  rows.append({"key":b.key,"bitmap":str(b.rect),"visible":str(face),"touch":str(b.hit_rect)})
 evidence[label]={"visible_bounds":str(bounds),"visible_physical_size":str(bounds.size*phone.pixel_scale),"buttons":rows}
func run():
 DirAccess.make_dir_recursive_absolute(CACHE+"slots");visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
 var g=State.new();g.new_game();g.save_path=CACHE+"battle.json";g.world_node=6;g.route_positions.alm=6;g.previous_world_node=5;check(g.start_battle(105),"isolated M15 starts for real layout")
 g.story_events=[];g.selected_id="hunapu";g.find_unit("hunapu").position=[15,21];g.find_unit("M15_e1").position=[16,21];g.cursor=Vector2i(16,21)
 ui.game=g;ui.view="battle";ui.ui_mode="target";ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.target_ids=["M15_e1"];ui.target_index=0;ui._focus_battle(g.cursor,true);material_check()
 for spec in [[Vector2i(2556,1179),Rect2(177,0,2202,1116),"wide"],[Vector2i(1334,750),Rect2(0,0,1334,750),"compact"],[Vector2i(442,240),Rect2(0,0,442,240),"minimum"]]:
  screen.size=spec[0];phone.safe_area_override=spec[1];phone._layout();await frame(spec[2]+"-restored-size");geometry(spec[2])
  var keys=phone.buttons.filter(func(b):return phone.DIRECTION_KEYS.has(b.key))
  for b in keys:
   var point=physical(b.visible_rect).get_center();phone._finger(12,point,true)
   check(phone.fingers.get(12,0)==int(b.key),spec[2]+" touch press enters correct held direction")
   await frame(spec[2]+"-pressed-"+str(b.arrow),spec[2]=="wide" and b.arrow=="right")
   phone._finger(12,point,false);check(not phone.fingers.has(12) and ui.held_direction==Vector2i.ZERO,spec[2]+" release clears held direction")
  ui.ui_mode="status";ui.status_id="hunapu";await frame(spec[2]+"-status",false)
  var right_key=keys.filter(func(b):return int(b.key)==KEY_RIGHT)[0];var point=physical(right_key.visible_rect).get_center();phone._finger(13,point,true);phone._finger(13,point,false)
  check(ui.ui_mode=="status" and ui.status_id!="hunapu",spec[2]+" right touch cycles status without dismissing central panel")
  ui.ui_mode="target";ui.status_id="";ui.queue_redraw()
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;await create_timer(.25).timeout
 var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks.size(),"errors":errors,"labels":checks,"evidence":evidence,"screenshots":shots},"  "));file.close()
 print("DIRECTION_SIZE_FIX ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
