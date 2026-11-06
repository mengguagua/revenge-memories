extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/training-guide-20261101/"
const CACHE="/private/tmp/training-guide-20261101/"
var checks=[];var errors=[];var shots=[];var screen;var phone;var ui;var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func same(a,b):return JSON.parse_string(JSON.stringify(a))==JSON.parse_string(JSON.stringify(b))
func fixture():
 var g=State.new();g.save_path="res://reports/full-assessment-20261025/campaign-final-r1/ch1/chain-M13-victory.json"
 check(g.load_game(),"read historical M13 victory without changing source")
 g.save_path=CACHE+"domain.json";return g
func domain():
 var g=State.new();g.new_game();g.save_path=CACHE+"fresh.json"
 check(not g.Training.queue_unlock(g) and g.story_events.is_empty(),"no prompt before M13 clear")
 g.world_node=4;g.previous_world_node=3;g.route_positions.alm=4
 check(g.start_battle(103),"new M13 enters through actual battle entry")
 g.story_events.clear();g.battle_outcome="victory"
 check(g.complete_battle(),"M13 completion invokes ordinary settlement")
 var key=g.Training.UNLOCK_KEY;var seen="seen_"+key
 var events=g.story_events.filter(func(e):return e.key==key)
 check(events.size()==1 and g.flags.get(seen,false),"M13 victory queues exactly one introduction")
 check(g.story_events.find(events[0])>g.story_events.find(g.story_events.filter(func(e):return e.key=="M13-END")[0]),"introduction follows M13 story dialogue")
 check(str(events[0].pages).contains("部队整备") and str(events[0].pages).contains("60经验") and str(events[0].pages).contains("2次"),"introduction names entry, reward and quota")
 check(not g.Training.queue_unlock(g,true),"same victory cannot enqueue a second introduction")
 check(g.save_game(),"queued one-time introduction saves")
 var r=State.new();r.save_path=g.save_path;check(r.load_game(),"queued introduction loads")
 check(r.flags.get(seen,false) and r.story_events.filter(func(e):return e.key==key).size()==1,"reload retains same pending introduction without duplication")
 g=fixture();g.story_events=[];g.flags.erase("active_plot");g.mode="battle";g.battle_outcome="";g.battle_settled=false
 check(not g.Training.queue_unlock(g),"old battle is not interrupted by introduction")
 g.mode="world";var before=g.roster.duplicate(true);var counts=g.flags.get("training_counts",{}).duplicate(true)
 check(g.Training.queue_unlock(g),"old cleared M13 journal receives one backfill in peaceful mode")
 check(same(before,g.roster) and same(counts,g.flags.get("training_counts",{})),"backfill changes neither rewards, roster nor training counts")
 check(g.save_game(),"backfill seen flag saves in old journal copy")
 r=State.new();r.save_path=g.save_path;check(r.load_game() and not r.Training.queue_unlock(r),"old journal reload cannot enqueue backfill again")
 var rules=g.Training.rules_pages();var text=str(rules)
 check(rules.size()==2 and text.contains("60经验") and text.contains("未满级") and text.contains("倒地者"),"rules explain reward eligibility including knockouts")
 check(text.contains("没有战斗经验") and text.contains("没有掉落"),"rules disclose no combat XP or loot")
 check(text.contains("每章每队") and text.contains("2次") and text.contains("共用") and text.contains("不结转"),"rules explain per-chapter per-team shared quota and expiry")
 check(text.contains("失败") and text.contains("退出") and text.contains("重试") and text.contains("不扣次数") and text.contains("最终合军"),"rules cover failed attempts and final merge")
 check(not text.contains("回合") and not text.contains("白旗"),"rule page stays within requested reward and quota scope")
func frame(name:String):
 ui.notice_time=0;ui.phase_time=0;ui.dialogue_reveal=9999;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" glyph/background safe areas: "+str(ui.layout_errors)+str(phone.layout_errors))
  screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func finish_plot():
 var cap=0
 while ui.view=="plot" and cap<80:
  ui.dialogue_reveal=9999;ui._accept();cap+=1;await process_frame
 check(cap<80,"dialogue closes within bounded confirmations")
func run():
 DirAccess.make_dir_recursive_absolute(CACHE+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
 visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1";domain()
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.game=fixture();ui.game.save_path=CACHE+"ui.json";ui.game.story_events=[];ui.game.flags.erase("active_plot");ui.game.mode="world";ui.game.battle_outcome="";ui.view="world";ui.busy=false;ui.result_sequence_running=false;ui.held_direction=Vector2i.ZERO;ui._clear_menu()
 var key=ui.game.Training.UNLOCK_KEY;var seen="seen_"+key
 ui.busy=true;ui._maybe_training_unlock();check(not ui.game.flags.get(seen,false),"busy UI defers old-save prompt");ui.busy=false
 ui._open_camp_menu();ui._maybe_training_unlock();check(not ui.game.flags.get(seen,false),"open menu defers old-save prompt");ui._clear_menu()
 ui.game.flags.active_plot={"pages":[{"speaker":"提示","text":"旧对白"}],"index":0,"return":"world"};ui._maybe_training_unlock();check(not ui.game.flags.get(seen,false),"saved dialogue continuation is not overwritten");ui.game.flags.erase("active_plot")
 ui.view="battle";ui.game.mode="battle";ui._maybe_training_unlock();check(not ui.game.flags.get(seen,false),"battle view defers old-save prompt")
 ui.view="world";ui.game.mode="world";ui._maybe_training_unlock();check(ui.view=="plot" and ui.game.flags.get(seen,false),"idle peaceful UI automatically starts backfill")
 await frame("unlock-page-1")
 var disk=State.read_json(ui.game.save_path);check(disk.flags.get(seen,false) and disk.flags.has("active_plot"),"visible introduction has resumable persisted page and seen flag")
 var resumed=State.new();resumed.save_path=ui.game.save_path;check(resumed.load_game() and resumed.flags.active_plot["return"]=="world","interrupted introduction resumes original world view")
 ui.dialogue_reveal=9999;ui._accept();await frame("unlock-page-2");await finish_plot();check(ui.view=="world" and not ui.busy,"backfill restores idle world after reading")
 ui._maybe_training_unlock();check(ui.view=="world" and ui.game.story_events.is_empty(),"idle check does not repeat completed prompt")
 ui.game=resumed;ui._resume_journey();check(ui.view=="plot" and ui.game.flags.get(seen,false),"actual resume controller continues interrupted unlock page")
 await finish_plot();ui._maybe_training_unlock();check(ui.view=="world" and ui.game.story_events.is_empty(),"resumed introduction finishes once without repeating")
 ui._menu_action("training:open","camp");check(ui.menu_items[0]=="收益与次数" and ui.menu_actions[0]=="training:rules" and ui.menu_items.size()==4,"rules are first item alongside both drills and return")
 await frame("training-menu")
 var roster=ui.game.roster.duplicate(true);var counts=ui.game.flags.get("training_counts",{}).duplicate(true)
 ui._clear_menu();ui._menu_action("training:rules","training_choices");check(ui.view=="plot" and not ui.plot_persistent,"rules open as repeatable information")
 await frame("rules-reward");ui.dialogue_reveal=9999;ui._accept();await frame("rules-quota");await finish_plot()
 check(ui.view=="world" and ui.menu_context=="training_choices" and ui.menu_items[0]=="收益与次数","closing rules returns to training menu")
 check(same(roster,ui.game.roster) and same(counts,ui.game.flags.get("training_counts",{})),"reading rules never grants rewards or consumes quota")
 ui._clear_menu();ui._menu_action("training:rules","training_choices");await finish_plot();check(ui.menu_context=="training_choices","rules can be read repeatedly")
 ui.game.flags.training_counts={"1:alm":2};ui._clear_menu();ui._open_camp_menu();check(ui.menu_actions.has("training:open"),"exhausted training still exposes rules entry")
 ui._clear_menu();ui._menu_action("training:open","camp");ui._clear_menu();ui._menu_action("training:rules","training_choices");await frame("rules-exhausted");await finish_plot()
 ui._clear_menu();ui.hub_controller.enter_room("H03",true,false);ui._menu_action("training:open","camp");ui._clear_menu();ui._menu_action("training:rules","training_choices");await finish_plot();check(ui.view=="hub" and ui.menu_context=="training_choices","rules return to hub training menu")
 if visual:
  screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout();ui._clear_menu();ui._menu_action("training:rules","training_choices")
  var index=0
  while ui.view=="plot" and index<12:
   await frame("compact-rules-"+str(index));ui.dialogue_reveal=9999;ui._accept();await process_frame;index+=1
  check(index<12 and ui.menu_context=="training_choices","compact paginated rules close back to menu")
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;await create_timer(0.25).timeout
 var f=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks.size(),"labels":checks,"errors":errors,"screenshots":shots},"  "));f.close();print("TRAINING_GUIDE ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
