extends SceneTree
const State=preload("res://core/game_state.gd")
const L=preload("res://core/late_dialogue.gd")
const OUT="res://reports/dialogue-ch2-5-20261107/"
var ui;var viewport;var errors=[];var shots=[];var contact_done=false
func contact(event:Dictionary):
 await ui._contact(event);contact_done=true
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":push_error("Background guard required");quit(1);return
 call_deferred("run")
func fresh(code:String,ch:int,id:int):
 ui.game=State.new();ui.game.save_path="res://reports/full-assessment-20261025/campaign-final-r4/ch%d/chain-%s-deployment.json"%[ch,code]
 if not ui.game.load_game():errors.append("load "+code)
 ui.game.save_path="/private/tmp/revenge-story-capture.json"
 if not ui.game.start_battle(id):errors.append("start "+code)
 ui.game.story_events.clear();ui.game.flags.erase("active_plot")
 ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.instant_mode=true;ui.phase_time=0;ui.notice_time=0;ui._clear_menu()
 ui.mechanical_target_confirmed=false;ui.mechanical_target_part="";ui.battle_animation.reset();ui.combat.clear();ui.combat_hit_time=0
func shot(name:String):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw()
 for i in range(3):await process_frame
 await RenderingServer.frame_post_draw
 var im=viewport.get_texture().get_image()
 if im==null or im.is_empty():errors.append("render "+name);return
 im.save_png(OUT+name+".png")
 if not ui.layout_errors.is_empty():errors.append(name+": "+str(ui.layout_errors))
 shots.append({"name":name,"layout_errors":ui.layout_errors.duplicate(),"preview":ui.battle_preview_audit.duplicate(true),"audit":ui.presentation_audit.duplicate(true)})
func dialogue(rows:Array):
 ui.plot_pages.clear()
 for page in L.pages(ui.game,rows):ui.plot_pages.append_array(ui._paginate_plot(page))
 ui.plot_index=0;ui.dialogue_reveal=999;ui.plot_return="battle";ui.view="plot"
func combat(weapon:int):
 fresh("F44",4,408)
 var boss=ui.game.find_unit("F44_boss");var p=ui.game.find_unit("eileen")
 boss.position=[24,8];p.position=[22,8];p.hp=60;p.max_hp=60;boss.innate_attack_index=weapon
 var plan=ui.game.plan_combat(boss.id,p.id);ui.combat=plan
 for id in [str(plan.attacker),str(plan.defender)]:
  var u=ui.game.find_unit(id);ui.combat_poses[id]=int(ui.battle_animation.sprite(u).sequences.idle[0]);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_hp[id]=int(u.hp);ui.combat_fades[id]=1.0
 ui.view="combat"
 return plan.events[0]
func run():
 viewport=SubViewport.new();viewport.size=Vector2i(406,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false)
 fresh("F44",4,408);ui._focus_battle(Vector2i(8,12),true);await shot("01-maintenance-route")
 ui._focus_battle(Vector2i(24,8),true);await shot("02-prometheus-map")
 viewport.size=Vector2i(256,240)
 for pair in [["F24",2,204,"F24_e10"],["F26",2,206,"F26_e3"],["F44",4,408,"F44_boss"]]:
  fresh(pair[0],pair[1],pair[2]);ui.ui_mode="status";ui.status_id=pair[3];await shot("03-mobile-status-"+str(pair[0]))
 fresh("F44",4,408)
 var boss=ui.game.find_unit("F44_boss");var p=ui.game.find_unit("eileen");p.position=[23,8];boss.position=[24,8]
 ui.game.selected_id=p.id;ui.game.cursor=Vector2i(24,8);ui.target_ids=[boss.id];ui.target_index=0;ui.ui_mode="target";ui._focus_battle(Vector2i(24,8),true)
 ui._accept();await shot("04-dual-core-menu")
 ui.menu_selected=2;ui._accept();await shot("05-life-core-preview")
 if ui.mechanical_target_part!="life" or ui.battle_preview_audit.get("mechanical_target",{}).get("part","")!="life":errors.append("life core selection/forecast")
 ui._clear_menu();ui.ui_mode="inspect";dialogue(L.lines("F44","两条",1));await shot("06-maintenance-dialogue")
 var event=combat(ui.game.Mechanical.FIRE)
 if not ui.battle_animation.show_frame(event,68):errors.append("fire animation")
 await shot("07-fire-contact")
 event=combat(ui.game.Mechanical.ANCHOR)
 if not ui.battle_animation.show_frame(event,68):errors.append("physical animation")
 await shot("08-physical-contact")
 fresh("F44",4,408)
 boss=ui.game.find_unit("F44_boss");p=ui.game.find_unit("eileen")
 boss.position=[24,8];p.position=[23,8];boss.hp=10;boss.speed=0;p.hp=60;p.max_hp=60;p.speed=0;p.strength=50;p.skill=80;p.weapon_index=23
 var revival=ui.game.plan_combat(p.id,boss.id);ui.combat=revival
 for id in [str(revival.attacker),str(revival.defender)]:
  var u=ui.game.find_unit(id);ui.combat_poses[id]=int(ui.battle_animation.sprite(u).sequences.idle[0]);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_hp[id]=int(u.hp);ui.combat_fades[id]=1.0
 ui.view="combat"
 contact_done=false;contact(revival.events[0])
 for i in range(150):
  if ui.view=="plot":ui.dialogue_reveal=999;ui._advance_plot()
  if contact_done:break
  await process_frame
 if not contact_done or ui.game.story_events.any(func(e):return e.get("key","")=="F44-REVIVE"):errors.append("revival voice must finish at its actual contact")
 await shot("09-real-revival")
 if boss.hp!=24 or ui.combat_hp[boss.id]!=24 or ui.combat_fades.get(boss.id,1)!=1:errors.append("revival must stay visible with24HP")
 fresh("F44",4,408);dialogue(["缇可：我记得病人的名字。那些也要清掉吗？我不回去。"]);await shot("09-tiko-dialogue")
 var f=FileAccess.open(OUT+"visual-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"background_guard":true,"shots":shots,"errors":errors},"  "));f.close()
 ui.audio.stop_all();ui.combat.clear();ui.game.story_events.clear();ui.hub_controller.ui=null;ui.hub_controller=null;ui.game=null;viewport.queue_free()
 for i in range(3):await process_frame
 ui=null;viewport=null
 print("STORY_VISUAL ",shots.size()," errors=",errors);quit(0 if errors.is_empty() else 1)
