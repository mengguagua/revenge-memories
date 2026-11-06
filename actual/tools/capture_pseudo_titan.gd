extends SceneTree
const State=preload("res://core/game_state.gd")
const M=preload("res://core/mechanical_puppets.gd")
const XP=preload("res://core/campaign_experience.gd")
const FIXTURE="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F25-deployment.json"
const OUT="res://reports/pseudo-titan-20261105/"
var ui;var viewport;var checks=[];var errors=[];var shots=[]
var reflection_done=false
func fatal_contact(event:Dictionary):
 await ui._contact(event)
 reflection_done=true
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":push_error("Background guard required");quit(1);return
 call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func fresh():
 ui.game=State.new();ui.game.save_path=FIXTURE
 check(ui.game.load_game(),"Actual existing F25 checkpoint loads")
 ui.game.save_path="/private/tmp/pseudo-titan-visual.json";check(ui.game.start_battle(205),"Actual new F25 deploys")
 ui.game.story_events.clear();ui.game.flags.erase("active_plot")
 ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.instant_mode=true
 ui.phase_time=0;ui.notice_time=0;ui.held_direction=Vector2i.ZERO;ui._clear_menu()
 ui.mechanical_target_confirmed=false;ui.mechanical_target_part=""
 ui.battle_animation.reset();ui.combat.clear();ui.combat_hit_time=0
 ui._focus_battle(Vector2i(18,9),true)
func shot(name:String):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw()
 for i in range(4):await process_frame
 await RenderingServer.frame_post_draw
 var image=viewport.get_texture().get_image();check(image!=null and not image.is_empty(),"Rendered "+name)
 if image==null or image.is_empty():return
 image.save_png(OUT+name+".png");check(ui.layout_errors.is_empty(),"Text safe regions "+name+": "+str(ui.layout_errors))
 shots.append({"file":name+".png","size":[image.get_width(),image.get_height()],"layout_errors":ui.layout_errors.duplicate(),"audit":ui.presentation_audit.duplicate(true),"preview":ui.battle_preview_audit.duplicate(true)})
func stage_combat(broken:bool=false,player_attack:bool=false,life:int=52):
 fresh();var t=ui.game.find_unit("F25_pseudo_titan_1");var p=ui.game.find_unit("eileen")
 t.position=[18,9];p.position=[17,9];p.hp=life;p.max_hp=52;p.strength=12;p.skill=40;p.speed=8;p.luck=0;p.defence=6
 if broken:t.parts.protective_core.hp=0
 ui.game.rng_state=0
 var plan=ui.game.plan_combat(p.id if player_attack else t.id,t.id if player_attack else p.id)
 check(not plan.is_empty(),"Actual exchange planned "+str(broken)+" / "+str(player_attack))
 ui.combat=plan;ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_hp.clear();ui.combat_fades.clear()
 for id in [str(plan.attacker),str(plan.defender)]:
  var u=ui.game.find_unit(id);ui.combat_poses[id]=int(ui.battle_animation.sprite(u).sequences.idle[0]);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_hp[id]=int(u.hp);ui.combat_fades[id]=1.0
 ui.view="combat"
 return plan.events[0]
func target():
 fresh();var t=ui.game.find_unit("F25_pseudo_titan_1");var p=ui.game.find_unit("eileen")
 p.position=[17,9];p.hp=52;p.max_hp=52;p.strength=40;p.skill=40;p.speed=8;p.luck=0;p.weapon_index=0
 ui.game.selected_id=p.id;ui.target_ids=[t.id];ui.target_index=0;ui.game.cursor=Vector2i(18,9);ui.ui_mode="target"
func run():
 viewport=SubViewport.new();viewport.size=Vector2i(406,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false);fresh()
 await shot("01-f25-deployment")
 ui.ui_mode="status";ui.status_id="F25_pseudo_titan_1";await shot("02-intact-status")
 check(ui.presentation_audit.status_stats.defence==14 and ui.presentation_audit.status_stats.resistance==12,"Status displays core armour14/12")
 target();var rng=ui.game.rng_state;ui._accept()
 check(ui.menu_context=="mechanical_part","Real confirm opens body/core menu");await shot("03-core-choice")
 ui._cancel();check(ui.game.rng_state==rng and not ui.game.find_unit("eileen").acted,"Cancel spends no action or RNG")
 ui._accept();ui.menu_selected=0;ui._accept();await shot("04-body-preview")
 ui.mechanical_target_confirmed=false;ui._accept();ui.menu_selected=1;ui._accept()
 check(ui.mechanical_target_part==M.CORE,"Real input selects protective core");await shot("05-core-preview")
 check(ui.battle_preview_audit.mechanical_target.part==M.CORE,"Preview displays independent core HP")
 ui._accept()
 for i in range(16):await process_frame
 var t=ui.game.find_unit("F25_pseudo_titan_1")
 check(t.hp==42 and M.part_hp(t)==0 and ui.game.kills==0,"Real confirm breaks core without killing body")
 ui.view="battle";ui.ui_mode="status";ui.status_id=t.id;ui.busy=false;ui._clear_menu();await shot("06-broken-status")
 check(ui.presentation_audit.status_stats.defence==4 and ui.presentation_audit.status_stats.resistance==2,"Broken status immediately shows4/2")
 for broken in [false,true]:
  var event=stage_combat(broken)
  for tick in [0,42,88,100,210]:
   check(ui.battle_animation.show_frame(event,tick),"Actual native melee frame "+str(tick))
   await shot(("broken" if broken else "intact")+"-melee-"+str(tick))
 var event=stage_combat(false,true)
 await ui._contact(event)
 check(ui.game.find_unit("eileen").hp==int(event.source_hp_after),"Reflection commits HP once through real controller")
 ui.combat_hit_id="eileen";ui.combat_hit_time=.4;ui.combat_message="反伤2HP";await shot("17-reflection-feedback")
 fresh();var p=ui.game.find_unit("eileen");p.level=3;p.exp=80
 ui.reward=XP.award(ui.game,p,180);ui.view="reward";ui.reward_elapsed=100;await shot("18-exp180-two-levels")
 check(p.level==5 and p.exp==60,"Real reward panel shows180 and two levels with60 remaining")
 viewport.size=Vector2i(256,240)
 fresh();ui.ui_mode="status";ui.status_id="F25_pseudo_titan_1";await shot("19-mobile-intact-status")
 target();ui._accept();await shot("20-mobile-core-choice")
 ui.menu_selected=1;ui._accept();await shot("21-mobile-core-preview")
 target();ui._accept();ui.menu_selected=0;ui._accept();await shot("22-mobile-body-preview")
 fresh();p=ui.game.find_unit("eileen");p.level=3;p.exp=80;ui.reward=XP.award(ui.game,p,180);ui.view="reward";ui.reward_elapsed=100;await shot("23-mobile-exp180")
 fresh();t=ui.game.find_unit("F25_pseudo_titan_1");p=ui.game.find_unit("eileen");p.position=[17,9];ui.game.selected_id=p.id;ui.ui_mode="map_target"
 ui.hero_map_animation.forecast=ui.game.MapSkills.preview(ui.game,p.id,Vector2i(18,9),Vector2i.RIGHT);await shot("24-mobile-map-reflection-preview")
 var receipt=ui.game.MapSkills.apply(ui.game,p.id,Vector2i(18,9),Vector2i.RIGHT)
 ui.hero_map_animation.prepare(receipt);ui.hero_map_animation._step(.65);await shot("25-mobile-map-reflection-hit");ui.hero_map_animation.reset()
 event=stage_combat(false,true,2)
 fatal_contact(event)
 for n in range(100):
  if ui.view=="plot":break
  await process_frame
 check(ui.view=="plot" and ui.plot_pages[ui.plot_index].get("casualty_id","")=="eileen","Reflected death pauses on the existing personal casualty cue")
 check(ui.combat_hp.eileen==0 and ui.combat_fades.eileen==1,"Reflected HP reaches0 before the casualty portrait and exit fade")
 ui.dialogue_reveal=999;await shot("26-mobile-reflection-casualty")
 ui._advance_plot()
 for n in range(100):
  if ui.view=="plot":ui.dialogue_reveal=999;ui._advance_plot()
  if reflection_done:break
  await process_frame
 check(reflection_done,"Fatal reflection feedback coroutine completes before cleanup")
 check(ui.game.find_unit("eileen").hp==0 and ui.combat_hp.eileen==0,"Real reflected death feedback reaches0 without a second gameplay commit")
 check(ui.game.finish_exchange(ui.combat).is_empty() and ui.game.battle_outcome=="defeat","Real controller reflection uses normal leader-failure rules")
 ui.combat_message="反伤2HP · 艾琳濒死";await shot("27-mobile-reflection-fatal")
 var f=FileAccess.open(OUT+"visual-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks.size(),"passed":errors.is_empty(),"errors":errors,"labels":checks,"shots":shots,"background_guard":true,"device_updated":false},"\t"));f.close()
 ui.audio.stop_all();viewport.queue_free()
 for i in range(3):await process_frame
 print("PSEUDO_TITAN_VISUAL ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
