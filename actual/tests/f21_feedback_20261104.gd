extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Panels=preload("res://core/battle_panel_layout.gd")
const OUT="res://reports/f21-feedback-20261104/"
const CACHE="/private/tmp/f21-feedback-20261104/"
const FIXTURE="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F21-deployment.json"
var checks=[];var errors=[];var evidence={};var screenshots=[]
var phone;var screen;var ui;var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func fresh():
 var g=State.new();g.save_path=FIXTURE;check(g.load_game(),"real F21 journal fixture loads")
 g.save_path=CACHE+"journal.json"
 for id in g.party:g.roster[id]=g._initial_character(id)
 check(g.start_battle(201),"fresh F21 starts");g.story_events.clear();return g
func comparison():
 var g=fresh();var enemy=g.find_unit("F21_e8").duplicate(true);enemy.exp_value=35;var rows=[]
 for id in ["eileen","mireille","lisa","carlo","lord","roan","shia","noya","celine"]:
  for level in [1,5,10]:
   var u=g._initial_character(id);u.level=level
   var old=u.duplicate(true);old.erase("id")
   var before=Rules.experience_gain(old,enemy,19,0,true);var after=Rules.experience_gain(u,enemy,19,0,true)
   rows.append({"name":u.name_zh,"level":level,"before":before,"after":after,"clear_before":Rules.victory_experience_gain(old)+35,"clear_after":Rules.victory_experience_gain(u)+35})
   check(after>=before,"no east character loses XP "+id+str(level))
   if id in ["mireille","carlo","roan","celine"]:check(after==before,"already adequate class coefficient retained "+id+str(level))
 check(rows[0].before==18 and rows[0].after==28,"Eileen level1 kill18→28")
 check(Rules.experience_gain({"id":"eileen","side":"enemy","class_id":11,"level":1},enemy,19,0,true)==18,"enemy identity cannot receive campaign modifier")
 for id in ["hunapu","otto","lena","hervi","fula","daan"]:
  var u=g._initial_character(id);var old=u.duplicate(true);old.erase("id")
  check(Rules.experience_gain(u,enemy,19,0,true)==Rules.experience_gain(old,enemy,19,0,true),"west XP unchanged "+id)
 var hero=g.find_unit("eileen");hero.strength=40;hero.skill=40;hero.position=[9,7];hero.speed=10;g.rng_state=0
 var exchange=g.plan_combat("eileen","F21_e8")
 for event in exchange.events:g.commit_strike(event)
 check(g.finish_exchange(exchange).gain==48,"real full exchange uses current arcanist B50, level3 V60, Eileen coefficient8")
 hero.level=20;check(Rules.experience_gain(hero,enemy,19,0,true)==0,"max level still gains no combat XP")
 check(Rules.healing_experience_gain(g._initial_character("mireille"),8)==10,"Mireille healing XP retained")
 evidence.experience=rows
func passenger_checks():
 var g=fresh();var p=g.find_unit("injured_passengers")
 check(p.hp==19 and p.max_hp==24 and not p.no_counter,"passenger starts19/24 (80% rounded) and can defend")
 var initial=g.pos(p);var action=g.ai_action(p)
 check(action.destination!=initial and g.ShipInterception.left_deck(g,action.destination),"passenger follows left-deck formation")
 var graph=g.reachable(p,true)
 for cell in graph.costs:check(g.ShipInterception.left_deck(g,cell),"all passenger reachable cells stay on left deck "+str(cell))
 for cell in [Vector2i(12,18),Vector2i(14,19),Vector2i(21,14),Vector2i(16,14)]:check(g.movement_cost(p,cell)==255,"passenger cannot traverse planks, enemy deck or water "+str(cell))
 for e in g.living("enemy"):e.hp=0
 var enemy=g.find_unit("F21_e1");enemy.hp=19;enemy.position=[9,20];enemy.strength=1;enemy.speed=1;enemy.skill=0
 p.position=[8,20];p.hp=19;p.acted=false
 action=g.ai_action(p);check(str(action.target)==enemy.id,"healthy passenger can volunteer a conservative ordinary attack")
 g.rng_state=0
 var assisted=g.plan_combat(str(p.id),str(enemy.id))
 check(not assisted.is_empty() and not assisted.events.is_empty(),"passenger assistance uses an actual ordinary combat plan")
 for event in assisted.get("events",[]):g.commit_strike(event)
 check(enemy.hp<19 and g.finish_exchange(assisted).is_empty(),"assistance actually damages enemy and grants no NPC experience")
 enemy.hp=19;p.acted=false
 p.hp=12;action=g.ai_action(p);check(str(action.target)==enemy.id,"exact50 percent may still volunteer a safe attack")
 p.hp=11;var origin=g.pos(p);action=g.ai_action(p)
 check(str(action.target).is_empty() and action.reason=="passenger_retreat" and action.destination!=origin,"below50 percent stops attacking and retreats")
 var path=g.path_to(p,action.destination)
 check(not path.is_empty() and path.all(func(c):return g.ShipInterception.left_deck(g,c)),"retreat uses a real path confined to left deck")
 evidence.passenger={"initial_hp":19,"maximum":24,"retreat_from":str(origin),"retreat_to":str(action.destination)}
 # Migrate a genuine old-style ongoing save without resetting HP/action/position.
 g=fresh();p=g.find_unit("injured_passengers");p.hp=11;p.acted=true;p.no_counter=true
 g.flags.quest.objects.plank_1=true
 for u in g.battle_start_snapshot.units:
  if str(u.id)==p.id:u.hp=24;u.no_counter=true
 check(g.save_game(),"old-style F21 checkpoint writes")
 var restored=State.new();restored.save_path=g.save_path
 check(restored.load_game(),"old-style F21 checkpoint loads")
 var old=restored.find_unit("injured_passengers")
 check(old.hp==11 and old.acted and restored.pos(old)==g.pos(p) and not old.no_counter,"migration preserves live wounds, action and position; enables duty")
 check(restored.retry_battle() and restored.find_unit("injured_passengers").hp==19,"old retry starts at revised80 percent rather than full HP")
 check(not restored.flags.quest.objects.has("plank_1"),"retired inspection flag is cleaned after legacy restoration")
 restored.turn=2
 for u in restored.units:
  if u.side=="player":u.acted=false
 restored.Rewind.record(restored);old=restored.find_unit("injured_passengers");old.hp=9;old.position=[7,20]
 restored.turn=3;restored.Rewind.record(restored)
 check(restored.Rewind.commit(restored) and restored.turn==2 and restored.find_unit("injured_passengers").hp==19,"rewind restores real passenger state at prior turn boundary")
 check(restored.movement_cost(restored.find_unit("injured_passengers"),Vector2i(12,19))==255,"deck bound remains enforced after rewind")
func reward_checks():
 var snapshots=[]
 for alive in [false,true]:
  var g=fresh();g.find_unit("injured_passengers").hp=19 if alive else 0;g.find_unit("F21_boss").hp=0
  check(g.check_outcome()=="victory","passenger life is bonus, not a new failure condition "+str(alive))
  check(g.complete_battle(),"ordinary victory settles "+str(alive))
  snapshots.append({"xp":g.victory_rewards.duplicate(true),"convoy":g.convoy.duplicate(true)})
  check(not g.complete_battle(),"settlement cannot repeat "+str(alive))
  check(g.save_game(),"settled result saves "+str(alive))
  var loaded=State.new();loaded.save_path=g.save_path
  check(loaded.load_game() and not loaded.complete_battle(),"settled save never repeats reward "+str(alive))
 for id in ["eileen","mireille","lisa","carlo"]:
  var totals=[]
  for s in snapshots:
   var total=0
   for row in s.xp:
    if row.unit==id:total+=int(row.gain)
   totals.append(total)
  check(totals[1]-totals[0]==20,"living passenger adds exactly20 to "+id)
 check(snapshots[0].convoy==snapshots[1].convoy,"survival XP does not copy equipment")
 var g=fresh()
 for id in ["lord","shia","noya"]:g.roster[id]=g._initial_character(id);g.party.append(id)
 g.parties.celica=g.party.duplicate();g.roster.lord.hp=0;g.roster.lord.dying=true;g.roster.lord.ever_dying=true;g.roster.lord.exp=95;g.roster.shia.level=20
 g.find_unit("F21_boss").hp=0;g.check_outcome();g.complete_battle()
 check(g.roster.lord.level==2 and g.roster.lord.exp==15 and g.roster.lord.hp==0 and g.roster.lord.dying,"injured reserve gains20 and ordinary level growth without revival")
 check(g.roster.noya.exp==20,"undeployed reserve receives20")
 check(not g.victory_rewards.any(func(r):return r.unit=="shia"),"max-level reserve excluded")
 var count=g.victory_rewards.size();g.ShipInterception.award_survival(g)
 check(g.victory_rewards.size()==count,"independent persistent flag prevents duplicate bonus")
func terrain_checks():
 var g=fresh();var hero=g.find_unit("eileen")
 check(not g.battle_data.objects.any(func(o):return str(o.id).begins_with("plank_")),"both useless inspection objects removed")
 var plank_art=g.battle_data.art_props.filter(func(p):return p.get("tag","")=="boarding_plank")
 check(plank_art.size()==2 and plank_art.all(func(p):return ResourceLoader.exists(p.path)),"both original plank images remain visible scenery")
 for connection in g.battle_data.boarding_connections:
  var b=connection.bounds
  for y in range(b[1],b[3]+1):
   for x in range(b[0],b[2]+1):
    var p=Vector2i(x,y)
    check(g.terrain_avoid(p)==20 and g.movement_cost(hero,p)==1,"whole jumpboard gives20 avoid and normal movement "+str(p))
    check(g.Items.phase_effect(hero,208,g.category(p)).heal==0,"jumpboard grants no accidental healing "+str(p))
 hero.position=[14,11];g.selected_id=hero.id
 check(not g.interact("plank_1") and not hero.acted,"removed inspection never consumes turn")
 var enemy=g.find_unit("F21_e1")
 check(Rules.attack_stats(enemy,hero,0).hit-Rules.attack_stats(enemy,hero,20).hit==20,"terrain avoidance affects actual physical hit prediction")
 var puppet=g.find_unit("F21_water_monkey_1")
 check(g.movement_cost(puppet,Vector2i(16,14))==255,"water monkey ordinary water movement unchanged")
 puppet.mechanical_retreating=true
 check(g.movement_cost(puppet,Vector2i(16,14))==1,"water monkey retreat water movement unchanged")
 check(not str(g.battle_data.before).contains("上层跳板旁") and str(g.battle_data.before).contains("药车右边"),"opening identifies nearby actual supply position")
 var graph=g.reachable(hero,true)
 for point in g.battle_data.recovery_sites:
  var cell=Vector2i(point.position[0],point.position[1])
  check(graph.costs.has(cell),"nearby recovery reachable "+str(cell))
 for canvas in [Rect2(0,0,256,240),Rect2(-110,0,476,240)]:
  for y in [20,50,100,160,220]:
   for x in [20,128,236]:
    var anchor=Vector2(x,y);var arrow=Rect2(anchor+Vector2(2,-18),Vector2(14,14))
    var result=Panels.place(anchor,Vector2(224,64),canvas,[],[arrow])
    check(result.valid and not result.panel.intersects(result.focus) and not result.panel.intersects(arrow),"support popup excludes actor and arrow "+str(canvas)+str(anchor))
 for revision in ["0.2.1","0.3.0"]:
  g=fresh();g.battle_data=State.read_json("res://data/compat/"+revision+"/F21.json")
  var before=[]
  for y in range(int(g.battle_data.map.height)):
   for x in range(int(g.battle_data.map.width)):before.append(g.movement_cost(hero,Vector2i(x,y))<255)
  g.ShipInterception.restore(g)
  var after=[]
  for y in range(int(g.battle_data.map.height)):
   for x in range(int(g.battle_data.map.width)):after.append(g.movement_cost(hero,Vector2i(x,y))<255)
  check(before==after,"retired legacy plank inspections preserve actual land/water geometry "+revision)
  check(not g.battle_data.objects.any(func(o):return str(o.id).begins_with("plank_")),"legacy inspection menus removed "+revision)
func frame(name:String,capture:bool=true):
 ui.notice_time=0;ui.phase_time=0;phone._sync_controls();ui.queue_redraw();phone.queue_redraw();await process_frame;await process_frame
 if not visual:return
 await RenderingServer.frame_post_draw
 check(ui.layout_errors.is_empty(),name+" glyphs inside measured panel safe area "+str(ui.layout_errors))
 check(phone.layout_errors.is_empty(),name+" phone material content safe area")
 if capture:screen.get_texture().get_image().save_png(OUT+name+".png");screenshots.append(name+".png")
func interface_checks():
 for spec in [[Vector2i(2556,1179),Rect2(177,0,2202,1116),"wide"],[Vector2i(1334,750),Rect2(0,0,1334,750),"compact"]]:
  screen.size=spec[0];phone.safe_area_override=spec[1];phone._layout()
  var g=fresh();ui.game=g;ui.view="battle";ui._clear_menu();ui.busy=false;ui.batch_running=false
  g.find_unit("mireille").position=[5,10];g.find_unit("lisa").position=[6,10];g.find_unit("lisa").hp=10
  g.selected_id="mireille";g.cursor=Vector2i(6,10);ui.chosen_spell=40;ui.target_ids=["lisa"];ui.target_index=0;ui.ui_mode="support_target"
  for y in [40,120,210]:
   ui.battle_camera=Vector2(0,160-y);await frame(spec[2]+"-heal-"+str(y))
   if visual:
    var p=ui.presentation_audit.support_preview
    check(p.valid and not p.panel.intersects(p.focus) and not p.panel.intersects(p.arrow),spec[2]+" actual support preview protects target and arrow "+str(y))
  ui.ui_mode="warp";ui.support_target="lisa";ui.chosen_spell=39;ui.battle_camera=Vector2(0,120);await frame(spec[2]+"-warp")
  ui.ui_mode="inspect";g.cursor=g.pos(g.find_unit("injured_passengers"));ui._focus_battle(g.cursor,true);await frame(spec[2]+"-passenger")
  g.find_unit("injured_passengers").hp=11;await frame(spec[2]+"-passenger-hurt")
  ui.ui_mode="status";ui.status_id="F21_water_monkey_1";await frame(spec[2]+"-monkey-details")
  if visual:
   check(ui.text_checks.any(func(r):return str(r.text).contains("移动5→8")) and ui.text_checks.any(func(r):return str(r.text).contains("可穿过水面")),"monkey details expose existing retreat rule "+spec[2])
   var last=[]
   for row in ui.text_checks:
    if row.bounds.position.y>=120:last.append(row)
   for a in range(last.size()):
    for b in range(a+1,last.size()):check(not last[a].bounds.intersects(last[b].bounds),"monkey detail text rows do not overlap "+spec[2]+str(a)+"/"+str(b))
  ui.ui_mode="inspect";g.cursor=Vector2i(14,19);ui._focus_battle(g.cursor,true);await frame(spec[2]+"-jumpboard")
  ui.view="plot";ui.plot_pages=[{"speaker":"战场提示","text":"受伤乘客平安获救。本队全体正式成员额外获得20点经验，未出阵成员也可获得；满级成员不再获得经验。"}];ui.plot_index=0;ui.plot_return="battle";ui.dialogue_reveal=200;await frame(spec[2]+"-survival-reward")
func run():
 DirAccess.make_dir_recursive_absolute(CACHE+"slots")
 visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
 comparison();passenger_checks();reward_checks();terrain_checks()
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
 await interface_checks()
 screen.queue_free();await process_frame
 var report={"checks":checks.size(),"errors":errors,"labels":checks,"evidence":evidence,"screenshots":screenshots,"scope":"Targeted F21 XP, NPC, reward/save/rewind and support HUD; no full campaign or device update"}
 var f=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("F21_FEEDBACK ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
