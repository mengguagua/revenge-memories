extends "res://tests/cursor_healing_exp.gd"
const REPORT="res://reports/healing-speed-menu-20261027/"
var sfx_ticks=0
var captured_healing=false
var feedback_samples={}
func frame(name:String,capture:bool=true):
 phone._sync_controls();ui.queue_redraw();phone.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
 check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),"safe areas: "+name)
 if capture:
  var path=REPORT+name+".png";screen.get_texture().get_image().save_png(path);shots.append(path)
func formulas():
 var g=fresh()
 var otto=g.find_unit("otto").duplicate(true);otto.speed=4;otto.item_id=49
 var cavalry=g.stages[103].enemies.filter(func(e):return str(e.id)=="M13_e6")[0].duplicate(true)
 # Historical 2026-10-27 comparison fixture; current M13 cavalry was raised to speed5 on2026-10-28.
 cavalry.speed=3
 var sequence=Rules.strike_sequence(otto,cavalry)
 check(Rules.attack_speed(otto)==4 and Rules.attack_speed(cavalry)==3 and sequence==["attacker","defender","attacker"],"4-speed Otto follows up against 3-speed cavalry")
 var equal=otto.duplicate(true);equal.speed=3
 check(Rules.strike_sequence(equal,cavalry)==["attacker","defender"],"equal effective speed gives no follow-up")
 var rows=[]
 for level in [5,6,7,8]:
  for id in ["hunapu","hervi","otto","daan","beck","fula"]:
   var u=g._initial_character(id);u.level=level;u.hp=u.max_hp
   rows.append({"id":id,"name":u.name_zh,"level":level,"class_id":u.class_id,"kill_value35":Rules.experience_gain(u,{"exp_value":35,"max_hp":22},22,0,true),"clear":Rules.victory_experience_gain(u)})
 var caster=g.find_unit("fula").duplicate(true);caster.hp=18;caster.strength=9;caster.speed=2;caster.luck=4
 var target={"id":"ally","hp":6,"max_hp":26}
 var normal=ui_items().support_effect(caster,target,40,99)
 var repeated=ui_items().support_effect(caster,target,40,0)
 check(normal.heal==9 and normal.repeat_heal==0 and normal.hp_cost==1,"Recover heals caster strength and costs1 HP")
 check(repeated.heal==9 and repeated.repeat_heal==9 and repeated.repeat_cost==1,"Recover can repeat with luck+speed roll and extra HP cost")
 var f=FileAccess.open(REPORT+"formula-results.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"otto_base_speed":otto.speed,"otto_weapon_weight":ui_items().weapon_profile(otto,Rules.weapon_index(otto)).get("weight",0),"cavalry":cavalry,"cavalry_effective_speed":Rules.attack_speed(cavalry),"sequence":sequence,"experience":rows,"M13_clear_extra":g.stages[103].get("clear_training_exp",0),"M11_clear_extra":g.stages[101].get("clear_training_exp",0),"recovery_normal":normal,"recovery_repeat":repeated},"  "));f.close()
func ui_items():return preload("res://core/item_rules.gd")
func start_cast(spell:int,target:String):
 cursor_to(ui.game.pos(ui.game.find_unit("fula")));key(KEY_Z);key(KEY_Z)
 check(ui.menu_actions[0]=="wait" and ui.menu_items[0]=="待机","post-move action menu defaults to Wait")
 choose("magic");choose("spell:"+str(spell))
 if not target.is_empty():
  for n in range(30):
   if ui.target_ids[ui.target_index]==target:break
   key(KEY_RIGHT)
  check(ui.target_ids[ui.target_index]==target,"normal menu selects healing recipient")
  key(KEY_Z)
func sample_hp(id:String,initial:int):
 if not feedback_samples.has(id):feedback_samples[id]=[initial]
 var value=int(ui.combat_hp.get(id,initial))
 if value!=int(feedback_samples[id][-1]):feedback_samples[id].append(value)
func observe_cast(wounds:Dictionary,shot:String):
 var until=Time.get_ticks_msec()+45000
 while ui.view!="reward" and Time.get_ticks_msec()<until:
  if ui.view=="combat":
   for id in wounds:sample_hp(id,int(wounds[id]))
   if not captured_healing and ui.combat_message.begins_with("恢复 +"):
    captured_healing=true;await frame(shot)
  await process_frame
 check(ui.view=="reward" and not ui.busy,"healing animation completes and opens EXP")
 for id in wounds:
  var end=int(ui.game.find_unit(id).hp);var samples=feedback_samples.get(id,[])
  check(samples.size()==end-int(wounds[id])+1,"every restored HP cell rendered for "+id)
  for i in range(1,samples.size()):
   if int(samples[i])!=int(samples[i-1])+1:check(false,"non-sequential HP feedback: "+id)
 check(sfx_ticks==wounds.keys().reduce(func(n,id):return n+int(ui.game.find_unit(id).hp)-int(wounds[id]),0),"one HP sound per restored cell")
 key(KEY_Z);check(ui.view=="battle" and not ui.busy,"reward confirmation returns battle control")
func visuals():
 await setup();ui.instant_mode=false;ui.animation_speed=1.0
 ui.audio.sfx_played.connect(func(key):
  if key=="hp_tick":sfx_ticks+=1)
 var c=ui.game.find_unit("fula");var t=ui.game.find_unit("daan")
 c.hp=c.max_hp;c.exp=0;c.acted=false;t.hp=int(t.max_hp)-8
 var wounds={"daan":int(t.hp)}
 start_cast(40,"daan");await observe_cast(wounds,"01-recover-cells-and-amount")
 check(sfx_ticks==8 and int(c.exp)==10,"real recovery feedback preserves healing and one EXP award")
 await frame("02-after-recovery")
 await setup();ui.instant_mode=false;ui.animation_speed=1.0;sfx_ticks=0;feedback_samples={};captured_healing=false
 ui.audio.sfx_played.connect(func(key):
  if key=="hp_tick":sfx_ticks+=1)
 c=ui.game.find_unit("fula");c.magic_flags=255;c.hp=c.max_hp;c.exp=0;c.acted=false
 for u in ui.game.living("player"):u.hp=u.max_hp
 t=ui.game.find_unit("daan");t.hp=int(t.max_hp)-5
 var h=ui.game.find_unit("hunapu");h.hp=int(h.max_hp)-3
 wounds={"daan":int(t.hp),"hunapu":int(h.hp)}
 var caster_before=int(c.hp)
 start_cast(44,"");await observe_cast(wounds,"03-fortify-healing-feedback")
 check(int(c.hp)==caster_before-12 and int(c.exp)==10,"Fortify charges once and awards EXP once for multiple recipients")
 # The ordinary after-movement menu and status use the current layout.
 cursor_to(ui.game.pos(h));key(KEY_Z);key(KEY_Z);await frame("04-wait-first")
 check(ui.menu_actions[0]=="wait" and ui.menu_selected==0,"Wait remains first with interactions/tactics appended")
 key(KEY_X)
 cursor_to(ui.game.pos(ui.game.find_unit("otto")));key(KEY_A);await frame("05-status-speed-label")
 check(ui.text_checks.any(func(t):return str(t.get("text",""))=="速度"),"status draws unified speed label")
func run():
 cache="/private/tmp/healing-speed-menu-20261027/"
 DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT))
 var rendered=DisplayServer.get_name()!="headless"
 if rendered:
  if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
  await visuals()
 else:formulas()
 var f=FileAccess.open(REPORT+("native-checks.json" if rendered else "logic-checks.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"HP_samples":feedback_samples,"hp_sounds":sfx_ticks,"screenshots":shots,"iphone_updated":false},"  "));f.close()
 print("HEALING_FEEDBACK ",checks.size()," errors=",JSON.stringify(errors))
 if screen!=null:
  screen.queue_free();await process_frame;ui=null;phone=null;screen=null
 quit(0 if errors.is_empty() else 1)
