extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const OUT="res://reports/cursor-healing-exp-20261027/"
const SOURCE="res://reports/campaign/natural-M13-deployment-save.json"
var checks=[]
var errors=[]
var shots=[]
var ui
var phone
var screen
var cache="/private/tmp/cursor-healing-exp/"
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append({"label":label,"passed":ok})
 if not ok:errors.append(label);push_error(label)
func fresh():
 var g=State.new();g.save_path=SOURCE;check(g.load_game(),"real M13 record loads")
 g.save_path=cache+"working.json"
 return g
func domain():
 var g=fresh();var c=g.find_unit("fula");var t=g.find_unit("daan")
 c.hp=c.max_hp;c.acted=false;c.exp=0;c.level=1;t.hp=int(t.max_hp)-8
 var result=g.use_support("fula",40,"daan")
 check(not result.is_empty() and int(c.exp)==10 and int(result.reward.gain)==10,"effective Recover awards10 at cleric level1")
 check(int(c.hp)==int(c.max_hp)-1 and int(t.hp)==int(t.max_hp),"spell cost and actual healing are preserved")
 check(g.use_support("fula",40,"daan").is_empty() and int(c.exp)==10,"consumed action cannot award twice")
 check(g.save_game(),"healing action and EXP save atomically")
 var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"healing EXP checkpoint reloads")
 check(int(loaded.find_unit("fula").exp)==10 and loaded.use_support("fula",40,"daan").is_empty(),"reload preserves EXP and consumed action")
 g=fresh();c=g.find_unit("fula");t=g.find_unit("daan");c.hp=c.max_hp;c.acted=false;c.exp=0;t.hp=t.max_hp
 var hp=int(c.hp);check(g.use_support("fula",40,"daan").is_empty() and int(c.exp)==0 and int(c.hp)==hp,"full-HP empty cast gives no EXP or cost")
 t.hp=int(t.max_hp)-1;result=g.use_support("fula",40,"daan");check(int(c.exp)==10,"a real one-HP heal is an effective action")
 g=fresh();c=g.find_unit("fula");c.magic_flags=255;c.hp=c.max_hp;c.acted=false;c.exp=0
 for u in g.living("player"):
  if str(u.id)!="fula":u.hp=maxi(1,int(u.max_hp)-5)
 result=g.use_support("fula",44)
 check(not result.is_empty() and result.changed.size()>1 and int(c.exp)==10,"Fortify gives one10-EXP award for the whole cast")
 g=fresh();c=g.find_unit("fula");t=g.find_unit("daan");c.hp=c.max_hp;c.acted=false;c.exp=95;c.level=1;t.hp=int(t.max_hp)-8
 result=g.use_support("fula",40,"daan")
 check(result.reward.leveled and int(c.level)==2 and int(c.exp)==5,"healing crosses100 and uses normal level-up growth")
 check(result.reward.growths.size()==6 and result.reward.get("support_training",false) and not result.reward.victory_training,"healing receipt has standard growth and its own source")
 g=fresh();c=g.find_unit("fula");t=g.find_unit("daan");t.hp=int(t.max_hp)-5;c.level=20;c.exp=0;c.acted=false
 result=g.use_support("fula",40,"daan");check(not result.has("reward") and int(c.exp)==0,"level20 can heal but gains no EXP")
 c.level=1;c.acted=false;c.no_experience=true;t.hp=int(t.max_hp)-5
 result=g.use_support("fula",40,"daan");check(not result.has("reward") and int(c.exp)==0,"no-experience actors remain excluded")
 check(Rules.healing_experience_gain({"class_id":18,"level":5,"hp":18},8)==7 and Rules.healing_experience_gain({"class_id":18,"level":6,"hp":18},8)==6,"same original class/level multipliers: level5→7, level6→6")
 check(Rules.healing_experience_gain({"class_id":18,"level":1,"hp":18},0)==0,"zero effective recovery earns nothing")
func analysis_tables():
 var g=fresh();var stage=g.stages[103];var roster=[];var enemy_cases=[]
 for level in [5,6]:
  for id in ["hunapu","daan","otto","beck","hervi","fula"]:
   var u=g._initial_character(id);u.level=level;u.hp=u.max_hp
   var regular=stage.enemies.filter(func(e):return e.id=="M13_e1")[0].duplicate(true)
   var elevated=regular.duplicate(true);elevated.level=2
   var cavalry=stage.enemies.filter(func(e):return e.id=="M13_e6")[0]
   var entry={"unit":id,"name":u.name_zh,"class_id":u.class_id,"level":level,"soldier_kill":Rules.experience_gain(u,regular,22,0,true),"soldier_kill_if_level2":Rules.experience_gain(u,elevated,22,0,true),"soldier_half_damage":Rules.experience_gain(u,regular,22,11,false),"miss":Rules.experience_gain(u,regular,22,22,false),"cavalry_kill":Rules.experience_gain(u,cavalry,24,0,true),"clear":Rules.victory_experience_gain(u),"heal":Rules.healing_experience_gain(u,8)}
   check(entry.soldier_kill==entry.soldier_kill_if_level2,"enemy level alone cannot change EXP: "+id+str(level));roster.append(entry)
 for u in stage.enemies:enemy_cases.append({"id":u.id,"name":u.name_zh,"level":u.level,"class_id":u.class_id,"exp_value":u.exp_value})
 var f=FileAccess.open(OUT+"experience-analysis.json",FileAccess.WRITE);f.store_string(JSON.stringify({"cases":roster,"M13_enemies":enemy_cases,"reinforcements":stage.get("reinforcements",[]),"clear_training_exp":stage.get("clear_training_exp",0),"note":"Fixed recipient levels for formula comparisons; not a simulated full-map distribution."},"  "));f.close()
func key(code:int):
 var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
 e=InputEventKey.new();e.physical_keycode=code;ui._input(e)
func choose(action:String):
 check(ui.menu_actions.has(action),"actual menu contains "+action)
 if not ui.menu_actions.has(action):return
 for n in range(40):
  if ui.menu_actions[ui.menu_selected]==action:break
  key(KEY_DOWN)
 key(KEY_Z)
func frame(name:String,capture:bool=true):
 phone._sync_controls();ui.queue_redraw();phone.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
 check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),"text and buttons inside safe areas: "+name)
 if capture:
  var path=OUT+name+".png";screen.get_texture().get_image().save_png(path);shots.append(path)
func setup(source:String=SOURCE):
 if screen!=null:screen.queue_free();await process_frame;ui=null
 screen=SubViewport.new();screen.size=Vector2i(1278,590);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(88,0,1102,558);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.game.save_path=source;check(ui.game.load_game(),"visual fixture loads");ui.game.save_path=cache+"visual.json";ui._resume_journey();ui.instant_mode=true
 var target_node=int(ui.game.stages[ui.game.stage_id].node)
 key(KEY_S);choose("new:prepare")
 for n in range(8):await process_frame
 if ui.game.world_node!=target_node:
  key(KEY_Z);choose("travel:"+str(target_node))
  for n in range(8):await process_frame
 key(KEY_Z);choose("new:battle")
 var until=Time.get_ticks_msec()+12000
 while (ui.busy or ui.view=="plot" or ui.phase_time>0) and Time.get_ticks_msec()<until:
  if ui.view=="plot":key(KEY_Z)
  await process_frame
 check(ui.view=="battle" and not ui.busy,"normal preparation reenters current map geometry")
func cursor_to(at:Vector2i):
 var guard=0
 while ui.game.cursor!=at and guard<100:
  var d=at-ui.game.cursor;key(KEY_RIGHT if d.x>0 else KEY_LEFT if d.x<0 else KEY_DOWN if d.y>0 else KEY_UP);guard+=1
 check(ui.game.cursor==at,"keyboard cursor reaches unit")
func cast_with_input():
 var c=ui.game.find_unit("fula");cursor_to(ui.game.pos(c));key(KEY_Z);key(KEY_Z);choose("magic");choose("spell:40")
 for n in range(20):
  if not ui.target_ids.is_empty() and ui.target_ids[ui.target_index]=="daan":break
  key(KEY_RIGHT)
 check(not ui.target_ids.is_empty() and ui.target_ids[ui.target_index]=="daan","support preview targets ally")
 key(KEY_Z)
 var until=Time.get_ticks_msec()+45000
 while ui.view!="reward" and Time.get_ticks_msec()<until:await process_frame
 check(ui.view=="reward" and not ui.busy,"actual heal animation returns to experience screen")
func visual():
 await setup()
 cursor_to(ui.game.pos(ui.game.find_unit("daan")));await frame("01-snow-map-pointer")
 check(ui.presentation_audit.map_indicator.rect.size==Vector2(12,12),"map pointer has enlarged10px fill and silhouette")
 cursor_to(ui.game.pos(ui.game.find_unit("fula")));key(KEY_A);await frame("02-fula-current-profession")
 check(ui.presentation_audit.status_profession==str(ui.game.catalog.classes["18"].name_zh),"friendly detail shows the current class")
 key(KEY_X)
 var c=ui.game.find_unit("fula");var t=ui.game.find_unit("daan")
 c.exp=0;c.level=1;c.hp=c.max_hp;c.acted=false;t.hp=int(t.max_hp)-8
 ui.instant_mode=false;await cast_with_input();await frame("03-healing-experience-10")
 check(int(ui.reward.gain)==10 and int(c.exp)==10 and not ui.reward.leveled,"healing EXP is visible and committed exactly once")
 key(KEY_Z);check(ui.view=="battle" and not ui.busy,"confirming heal EXP returns control to battle")
 await setup();c=ui.game.find_unit("fula");t=ui.game.find_unit("daan");c.exp=95;c.level=1;c.hp=c.max_hp;c.acted=false;t.hp=int(t.max_hp)-8
 await cast_with_input();await frame("04-healing-level-up")
 check(ui.reward.leveled and int(c.level)==2 and int(c.exp)==5,"healing level-up is presented correctly")
 key(KEY_Z);check(ui.view=="battle" and not ui.busy,"level-up confirmation releases control")
 c.class_id=17;ui.status_id="fula";ui.ui_mode="status";await frame("promoted-class-check",false)
 check(ui.presentation_audit.status_profession==str(ui.game.catalog.classes["17"].name_zh),"profession follows current class after promotion")
 key(KEY_X)
 await setup();c=ui.game.find_unit("fula");t=ui.game.find_unit("daan");c.exp=0;c.hp=c.max_hp;c.acted=false;t.hp=int(t.max_hp)-8
 for u in ui.game.living("player"):
  if ui.game.party.has(str(u.id)):u.acted=str(u.id)!="fula"
 await cast_with_input();key(KEY_Z)
 var until=Time.get_ticks_msec()+45000
 while (ui.busy or ui.game.phase!="player" or int(ui.game.turn)<2) and Time.get_ticks_msec()<until:
  if ui.view in ["plot","reward"]:key(KEY_Z)
  await process_frame
 check(ui.game.phase=="player" and int(ui.game.turn)==2 and not ui.busy,"last-action heal EXP does not block automatic enemy phase or next turn")
 await setup("res://reports/dialogue-sync-20261026/play/S11-entry.json")
 cursor_to(ui.game.pos(ui.game.find_unit("daan")));await frame("05-cave-map-pointer")
func run():
 DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
 var rendered=DisplayServer.get_name()!="headless"
 if rendered:
  if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
  await visual()
 else:domain();analysis_tables()
 var f=FileAccess.open(OUT+("native-checks.json" if rendered else "logic-checks.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"failures":errors,"native_graphics":rendered,"screenshots":shots,"iphone_updated":false,"fixture_scope":"Controlled injuries and threshold EXP for healing boundary cases; ordinary keyboard spell selection and native animation. Not a full-map playthrough."},"  "));f.close()
 print("CURSOR_HEAL_EXP ",checks.size()," errors=",JSON.stringify(errors))
 if screen!=null:screen.queue_free();await process_frame;ui=null
 quit(0 if errors.is_empty() else 1)
