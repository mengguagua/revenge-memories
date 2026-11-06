extends SceneTree
const State=preload("res://core/game_state.gd")
const Faces=preload("res://core/portrait_library.gd")
const OUT="res://reports/ch1-story-20261026/"
const CODES={101:"M11",102:"M12",103:"M13",104:"M14",105:"M15",111:"S11",112:"S12"}
var domain_completed=false
var visual_completed=false
var checks=[]
var errors=[]
var shots=[]
var page_count=0
var cache="/private/tmp/ch1-story-feedback-20261026/"
var ui
var phone
var screen
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func fresh(id:int):
 var g=State.new();g.new_game();g.save_path=cache+"working-"+str(id)+".json";g.world_node=int(g.stages[id].node)
 check(g.start_battle(id),"normal battle entry "+str(id));return g
func domain():
 for id in CODES:
  var g=fresh(id);var d=g.battle_data
  check(str(d.before).begins_with("胡纳普："),str(CODES[id])+" opens from protagonist intention")
  check(g.story_events.any(func(e):return e.get("pages",[]).any(func(p):return str(p.speaker)=="胡纳普")),str(CODES[id])+" actual entry queues protagonist dialogue")
  check(not str(d.after).contains("按5.2") and not str(d.after).contains("D13败北段"),str(CODES[id])+" after text contains playable prose rather than author notes")
  var old=State.read_json(OUT+"before/actual/data/stages/"+str(CODES[id])+".json")
  for key in ["map","player_positions","objects","exit","targets"]:check(d[key]==old[key],str(CODES[id])+" preserves geography and objective "+key)
  if id!=102:check(d.enemies==old.enemies,str(CODES[id])+" enemy stats untouched")
 var surrendered=fresh(104);surrendered.story_events.clear();surrendered.story_on_victory()
 check(surrendered.story_events.any(func(e):return e.pages.any(func(p):return str(p.speaker)=="投降兵")),"surviving surrender branch retains its witness")
 var none=fresh(104)
 for u in none.units:
  if u.side=="enemy":u.hp=0
 none.story_events.clear();none.story_on_victory()
 check(not none.story_events.any(func(e):return e.pages.any(func(p):return str(p.speaker)=="投降兵")) and none.story_events.any(func(e):return e.pages.any(func(p):return str(p.text).contains("撤离军令"))),"no-survivor branch uses a document instead of a dead witness")
 var final=fresh(105);final.story_events.clear();final.story_on_victory()
 check(final.story_events.any(func(e):return str(e.get("key",""))=="D13") and final.story_events.any(func(e):return str(e.get("key",""))=="M15-END" and e.pages.any(func(p):return str(p.text).contains("人和粮"))),"M15 actually plays D13 then current authored aftermath")
 var g=fresh(102);var old=State.read_json(OUT+"before/actual/data/stages/M12.json")
 check(str(g.battle_data.before).contains("若敌方连续两次在粮仓门前点火，战斗失败。"),"requested failure sentence exact")
 check(str(g.battle_data.before).contains("腿上的伤才包住，现在不能挪动") and str(g.battle_data.before).contains("你留在这里照看他"),"Fula has a concrete patient and reason to stay")
 var f=g.find_unit("fula");check(not f.controllable and bool(f.neutral) and g.ai_action(f).destination==g.pos(f),"Fula remains a stationary noncontrollable witness")
 for row in old.enemies:
  var current=g.find_unit(str(row.id));var cid=int(row.class_id)
  if cid==6:check(current.max_hp==row.max_hp+2 and current.hp==current.max_hp,"soldier HP+2 including commander "+str(row.id))
  elif cid==12:check(current.max_hp==row.max_hp-2 and current.strength==row.strength+2,"archer HP-2 and strength+2 "+str(row.id))
  elif cid==8:
   check(current.level==row.level+1 and current.max_hp==row.max_hp+2 and current.exp_value==44,"mercenary genuine level/stat/experience upgrade")
   for key in ["strength","skill","speed","defence"]:check(current[key]==row[key]+1,"mercenary fixed growth "+key)
  for key in ["position","item_id","move","resistance","luck","drop_chance"]:
   if row.has(key):check(current.get(key)==row[key],"M12 preserves "+str(row.id)+" "+key)
  var loaded=row.duplicate(true);loaded.enemy_balance_revision=3;loaded.hp=5
  g.EnemyBalance.prepare(102,[loaded]);var wounds=int(row.max_hp)-5
  check(int(loaded.hp)==maxi(1,int(loaded.max_hp)-wounds),"old save preserves missing HP "+str(row.id))
  var once=loaded.duplicate(true);g.EnemyBalance.prepare(102,[loaded]);check(loaded==once,"load cannot stack bonuses "+str(row.id))
  loaded=row.duplicate(true);loaded.enemy_balance_revision=3;loaded.hp=0;loaded.dead=true;g.EnemyBalance.prepare(102,[loaded]);check(loaded.hp==0 and loaded.dead,"migration cannot revive "+str(row.id))
 check(Faces.unit(g,g.find_unit("M12_boss")).get("key","")=="m12_commander","commander unit has unique portrait")
 check(Faces.speaker(g,"指挥官").get("key","")=="m12_commander","commander dialogue uses same unique identity")
 check(Faces.unit(g,g.find_unit("M12_e2")).get("key","")=="west_infantry","ordinary soldiers retain old portrait")
 var burner=g.find_unit("M12_e1");burner.position=g.battle_data.targets[0].duplicate();g.turn=7;g.phase="enemy";g.mark_wait(str(burner.id))
 check(g.flags.quest.burn_streak==1 and g.battle_outcome.is_empty(),"first enemy fire is not defeat")
 check(g.story_events.any(func(e):return e.pages.any(func(p):return str(p.speaker)=="战场提示" and str(p.text).contains("点火一次"))),"first fire warning states the already-consumed chance clearly")
 g.turn=8;burner.acted=false;g.mark_wait(str(burner.id));check(g.battle_outcome=="defeat","second consecutive enemy fire loses battle")
 g=fresh(103);g.find_unit("lena").hp=0;g.story_events.clear();g.queue_lines(str(g.battle_data.during));g.queue_lines(str(g.battle_data.after))
 check(not g.story_events.any(func(e):return e.pages.any(func(p):return str(p.speaker)=="蕾娜" or str(p.text).contains("本该由我护送"))),"unavailable Lena does not lend her personal history to a substitute")
 g=fresh(102);g.find_unit("M12_e2").hp=7;var turn=g.turn;var rng=g.rng_state;var positions=g.units.map(func(u):return g.pos(u));check(g.save_game(),"new M12 state saves")
 var read=State.new();read.save_path=g.save_path;check(read.load_game() and read.turn==turn and read.rng_state==rng and read.units.map(func(u):return read.pos(u))==positions and read.find_unit("M12_e2").hp==7,"save/load preserves live battle wounds turn RNG and positions")
 check(read.retry_battle() and read.find_unit("M12_boss").max_hp==29 and read.find_unit("M12_e6").max_hp==20,"retry uses current M12 stats once")
 domain_completed=true
func frame(name:String,save:bool=false):
 ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
 for n in range(3):await process_frame
 await RenderingServer.frame_post_draw
 check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" runtime text/frame audit")
 if ui.view=="plot":
  var a=ui.plot_layout_audit;var safe:Rect2=a.panel.grow(-8)
  for t in ui.text_checks:check(safe.encloses(t.bounds),name+" actual glyph bounds inside panel safety inset")
  if a.has_portrait:check(safe.encloses(a.portrait) and not a.portrait.intersects(a.text),name+" complete portrait separated from text")
 if save:
  screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func presentation():
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=5
 for id in CODES:
  ui.game.new_game();ui.game.save_path=cache+"ui.json";ui.game.world_node=int(ui.game.stages[id].node);ui.game.start_battle(id);ui.game.story_events.clear()
  ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui._focus_battle(ui.game.cursor,true)
  var fields=["before","during","after"]
  if ui.game.battle_data.has("after_no_survivors"):fields.append("after_no_survivors")
  for field in fields:
   ui.game.story_events.clear();ui.game.queue_lines(str(ui.game.battle_data[field]))
   var pages=[]
   for event in ui.game.story_events:
    for page in event.pages:pages.append_array(ui._paginate_plot(page))
   ui.view="plot";ui.plot_return="battle";ui.plot_pages=pages;ui.dialogue_reveal=99999
   for index in range(pages.size()):
    ui.plot_index=index;var name=str(CODES[id])+"-"+field+"-"+str(index);page_count+=1
    var photo=id==102 and field=="before" and (index==0 or str(pages[index].text).contains("腿上的伤") or str(pages[index].text).contains("若敌方连续"))
    await frame(name,photo)
  if id==102:
   ui.view="battle";ui.ui_mode="status";ui.status_id="M12_boss";ui.game.cursor=ui.game.pos(ui.game.find_unit("M12_boss"));ui._focus_battle(ui.game.cursor,true);await frame("M12-commander-status",true)
 phone.queue_free();await process_frame;screen.queue_free();await process_frame
 visual_completed=true
func run():
 DirAccess.make_dir_recursive_absolute(cache+"slots");var visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
 if visual:
  await presentation();check(visual_completed and page_count>=90,"all authored dialogue states rendered without early script termination")
 else:
  domain();check(domain_completed and checks.size()>=170,"all domain cases completed without early script termination")
 var out=FileAccess.open(OUT+("visual-checks.json" if visual else "checks.json"),FileAccess.WRITE);out.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"screenshots":shots,"dialogue_pages":page_count,"scope":"Targeted chapter-one story, M12 numeric/save and phone dialogue safety checks. Not a full campaign playthrough.","phone_updated":false},"  "));out.close()
 print("CH1_STORY ",checks.size()," checks; ",errors.size()," errors; pages ",page_count);quit(0 if errors.is_empty() else 1)
