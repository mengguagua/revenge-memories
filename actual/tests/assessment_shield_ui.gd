extends SceneTree
const OUT="res://reports/full-assessment-20261025/ai/"
var screen
var phone
var ui
var checks=[]
var errors=[]
var shots=[]
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label)
func frame():
 phone._sync_controls();ui.queue_redraw();phone.queue_redraw()
 for n in range(4):await process_frame
 await RenderingServer.frame_post_draw
 check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),"text and phone controls remain inside content safe areas: "+ui.view)
func shot(name:String):
 var path=OUT+name+".png";screen.get_texture().get_image().save_png(path)
 shots.append({"path":path,"size":[screen.size.x,screen.size.y],"view":ui.view,"text":ui.text_checks.duplicate(true),"equipment_text":ui.equipment_screen.audit.duplicate(true)})
func run():
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override="/private/tmp/revenge-assessment-shield-ui-slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
 ui.game.save_path="res://reports/full-assessment-20261025/ai/shield-corrected/shield-J54-field.json"
 check(ui.game.load_game(),"old genuinely shield-bearing Eileen state loads for display")
 ui.game.save_path="/private/tmp/revenge-assessment-shield-ui-unused.json";ui.game.story_events.clear();ui.view="battle";ui.busy=false;ui.batch_running=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
 var hero=ui.game.find_unit("eileen");ui.status_id="eileen";ui.ui_mode="status";ui.game.cursor=ui.game.pos(hero);ui._focus_battle(ui.game.cursor,true)
 await frame()
 check(int(ui.presentation_audit.status_stats.defence)==int(hero.defence)+5 and int(ui.presentation_audit.status_stats.resistance)==int(hero.resistance)+5,"rendered advanced status includes exactly five to both defences")
 shot("shield-status")
 # The comparison menu is a separate presentation fixture; no acceptance or save.
 ui.game.route="celica";ui.game.party=ui.game.parties.celica.duplicate();ui.game.mode="world";ui.view="world";ui.ui_mode="inspect";ui._clear_menu()
 ui.game.convoy.celica.append(53);ui.equipment_screen.open(ui.game.convoy.celica.size()-1)
 ui.equipment_screen.selected=ui.equipment_screen.members.find("eileen");ui.equipment_screen.accept();ui.equipment_screen.toggle_details()
 var found=false
 for page in range(ui.equipment_screen.details_page_count()):
  ui.equipment_screen.details_page=page;await frame()
  if ui.equipment_screen.audit.any(func(t):return str(t.text).contains("5物防") or str(t.text).contains("5魔防")):
   found=true;shot("shield-details")
 check(found,"actual equipment details renders the current five-point bonuses")
 var f=FileAccess.open(OUT+"shield-visual-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"shots":shots,"background_guard":true,"device_test":false,"fixture":true},"  "));f.close()
 print("ASSESSMENT_SHIELD_UI ",checks.size()," errors=",errors)
 phone.queue_free();await process_frame;screen.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
