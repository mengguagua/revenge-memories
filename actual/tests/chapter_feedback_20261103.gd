extends SceneTree
const State=preload("res://core/game_state.gd")
const Tasks=preload("res://core/current_task.gd")
const OUT="res://reports/chapter-feedback-20261103/"
const CACHE="/private/tmp/chapter-feedback-20261103/"
var errors=[];var checks=[];var shots=[];var evidence={};var comparisons=[]
var phone;var screen;var ui;var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func same(a,b):return JSON.stringify(a)==JSON.stringify(b)
func fresh():
 var g=State.new();g.new_game();g.save_path=CACHE+"fixture.json";g.world_node=6;g.previous_world_node=5;g.route_positions.alm=6
 check(g.start_battle(105),"enter M15 isolated fixture");g.story_events=[];return g
func domain():
 var g=fresh();var worker=g.find_unit("M15_workers1")
 check(g.escort_hint(worker)=="等待开门解救","locked worker hover explains gate requirement")
 var actor=g.find_unit("hunapu");actor.position=[27,23];g.selected_id=actor.id
 check(g.interact("M15_rescue_1") and not worker.locked,"real gate action unlocks second worker immediately")
 var origin=g.pos(worker);var action=g._campaign_ai_action(worker);var hint=g.escort_hint(worker)
 evidence.worker_initial={"position":str(origin),"action":str(action),"hint":hint}
 # Remove all threats without advancing the turn: only the tactical situation changes.
 for enemy in g.living("enemy"):enemy.hp=0
 var safe=g._safe_escort_move(worker,Vector2i(28,2))
 evidence.worker_safe={"position":str(origin),"destination":str(safe.destination),"hint":g.escort_hint(worker)}
 check(safe.destination!=origin,"unlocked worker can advance as soon as route is safe, no fixed-turn delay")
 check(g.escort_hint(worker)!="等待开门解救","worker hover updates after opening and enemy changes")
 worker.acted=true;check(g.escort_hint(worker)=="本阶段已自动行动","already acted worker explains phase wait")
 worker.acted=false
 var rewards=[]
 for count in [1,2]:
  g=fresh()
  for n in range(count):g.find_unit("M15_workers"+str(n)).locked=false;g.flags.quest.objects["M15_rescue_"+str(n)]=true
  g.find_unit("M15_boss").hp=0
  check(g.check_outcome()=="victory","rescue "+str(count)+" groups permits victory without reaching exit")
  check(g.complete_battle(),"settle rescue "+str(count)+" groups")
  rewards.append({"rewards":g.victory_rewards.duplicate(true),"convoy":g.convoy.duplicate(true),"items":g.roster.values().map(func(u):return u.item_id)})
 check(same(rewards[0].convoy,rewards[1].convoy) and same(rewards[0].items,rewards[1].items),"full rescue changes XP only, equipment settlement unchanged")
 for id in g.party:
  var totals=[]
  for settlement in rewards:
   var total=0
   for receipt in settlement.rewards:
    if receipt.unit==id:total+=int(receipt.gain)
   totals.append(total)
  check(totals[1]-totals[0]==20,"two rescued groups grant extra20 XP: "+id)
 evidence.rescue_rewards=rewards
 # Existing copied iPhone checkpoint, never write the original backup.
 var source="res://../dist/iphone-save-backups/20261102-222348/after/Documents/journey-slot-1.json"
 var file=FileAccess.open(CACHE+"copied-phone.json",FileAccess.WRITE);file.store_string(FileAccess.get_file_as_string(source));file.close()
 g=State.new();g.save_path=CACHE+"copied-phone.json";check(g.load_game(),"load copied existing phone turn4 checkpoint")
 for unit in g.units:
  if str(unit.id).begins_with("M15_workers"):
   evidence[unit.id]={"position":str(g.pos(unit)),"locked":unit.locked,"acted":unit.acted,"hint":g.escort_hint(unit),"action":str(g._campaign_ai_action(unit))}
 # Same characters and targets, changing the equipped weapon only.
 for spec in [["hunapu",[59,60,11]],["otto",[61,62,2]],["daan",[63,64,20]]]:
  if not g.roster.has(spec[0]):continue
  var a=g.roster[spec[0]].duplicate(true)
  for target_id in ["M15_e1","M15_e6"]:
   var b=g.find_unit(target_id).duplicate(true)
   for avoid in [0,20,40]:
    for item_id in spec[1]:
     a.item_id=item_id;a.erase("weapon_index")
     var distance=1 if spec[0]!="daan" else 2
     var attack=g.Rules.attack_context(a,distance);var reply=g.Rules.default_counter(b,distance)
     var stats=g.Rules.attack_stats(attack,reply,avoid);var sequence=g.Rules.strike_sequence(attack,reply,distance)
     comparisons.append({"actor":a.name_zh,"level":a.level,"strength":a.strength,"skill":a.skill,"speed":a.speed,"weapon":g.Rules.weapon_name(a),"target":b.name_zh,"avoid":avoid,"hit":stats.hit,"damage":stats.damage,"attack_speed":stats.attack_speed,"strikes":sequence.count("attacker"),"expected":snappedf(float(stats.damage)*stats.hit/100*sequence.count("attacker"),.01)})
 check(comparisons.filter(func(r):return r.weapon.begins_with("钢")).size()==18,"comparison exercises real equipped steel attacks")
 evidence.hit_comparisons=comparisons
 var slow=g.roster.hunapu.duplicate(true);slow.speed=6;slow.item_id=60;slow.erase("weapon_index");var knight=g.find_unit("M15_e6").duplicate(true)
 var iron=g.Rules.strike_sequence(slow,knight).count("attacker");slow.item_id=11;var steel=g.Rules.strike_sequence(slow,knight).count("attacker")
 check(iron==2 and steel==1,"one point of steel weight can remove follow-up at equal attack speed")
 var all=State.read_json("res://data/current_tasks_20261103.json")
 check(all.size()==26,"all main routes after chapter1 have explicit task context")
 g=State.new();g.new_game();g.chapter=2;g.route="celica";g.flags={};g.cleared_stages=[]
 check(Tasks.entry(g).text.contains("母亲") and Tasks.entry(g).text.contains("卡洛"),"chapter2 departure explains motivation and person to find")
 g.flags.east_departure_ready=true
 check(Tasks.entry(g).text.contains("风灯岛") and not Tasks.entry(g).text.contains("前往海上拦截"),"chapter2 destination is a real sea location")
 check(g.formal_world.nodes["18"].name_zh=="风灯岛外海","world map names sea location separately from battle title")
 for key in all:
  check(not str(all[key]).is_empty() and not str(all[key]).begins_with("下一步：前往"),"explicit motive for main stage "+key)
func frame(name:String,capture:bool=true):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(ui.layout_errors.is_empty(),name+" content safe areas "+str(ui.layout_errors))
  check(phone.layout_errors.is_empty(),name+" phone safe areas "+str(phone.layout_errors))
  if capture:screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func drain_pages(prefix:String):
 var total=ui.plot_pages.size()
 for n in range(total):
  ui.dialogue_reveal=str(ui.plot_pages[ui.plot_index].text).length();await frame(prefix+"-p"+str(n+1));ui._advance_plot()
 await process_frame;await process_frame
 check(ui.view!="plot" and not ui.busy,prefix+" completes normal dialogue flow")
func forecast(g,name:String):
 ui.game=g;ui.view="battle";ui.busy=false;ui.batch_running=false;ui.ui_mode="target";ui._clear_menu();g.selected_id="hunapu";g.find_unit("hunapu").position=[15,21];g.find_unit("M15_e1").position=[16,21];g.cursor=Vector2i(16,21)
 ui.target_ids=["M15_e1"];ui.target_index=0;ui._focus_battle(g.cursor,true);await frame(name)
 if visual:
  check(ui.battle_preview_audit.valid,"forecast has a safe placement "+name)
  var fields=ui.battle_preview_audit.factions
  check(fields.size()==2 and fields[0].side=="enemy" and fields[0].tint.r>fields[0].tint.b and fields[1].side=="player" and fields[1].tint.b>fields[1].tint.r,"forecast places red enemy first and blue ally second "+name)
  for f in fields:check(ui.battle_preview_audit.panel.grow(-7).encloses(f.bounds),"faction fill clears original bitmap frame "+name)
  check(not fields[0].bounds.intersects(fields[1].bounds),"forecast color fields cannot overlap "+name)
func tasks_frame(g,name:String,capture:bool=true):
 ui.game=g;ui.view="world";ui._clear_menu();ui.field_notes.open_tasks();await frame(name,capture)
 var count=ui.field_notes.journal_pages()
 for n in range(1,count):ui.field_notes.direction(Vector2i.RIGHT);await frame(name+"-p"+str(n+1),capture)
 ui._mouse_accept(ui._canvas_offset()+ui.field_notes.journal_safe().get_center());check(ui.view=="field_notes",name+" diary body tap stays open")
 ui._cancel();check(ui.view=="world",name+" explicit return closes diary")
func interface_checks():
 var g=fresh();await forecast(g,"forecast-factions")
 var stored=ui.game
 var copy=State.new();copy.save_path=CACHE+"copied-phone.json";check(copy.load_game(),"read existing turn4 copy for hover screenshot");ui.game=copy;ui.view="battle";ui.ui_mode="inspect";copy.cursor=copy.pos(copy.find_unit("M15_workers1"));ui._focus_battle(copy.cursor,true);await frame("worker-waits-for-clear-route")
 if visual:check(ui.text_checks.any(func(row):return str(row.text)==copy.escort_hint(copy.find_unit("M15_workers1"))),"worker hover actually renders live danger reason")
 ui.game=stored
 ui.ui_mode="status";ui.status_id="hunapu";await frame("status-touch-safe")
 ui._mouse_accept(ui._canvas_offset()+Vector2(120,100));check(ui.ui_mode=="status","battle status body tap stays open")
 var prior=ui.status_id;ui._mouse_accept(ui._canvas_offset()+Vector2(228,30));check(ui.status_id!=prior and ui.ui_mode=="status","status explicit arrow still cycles")
 ui._cancel();check(ui.ui_mode!="status","battle status explicit return closes")
 ui._menu_action("new:goal","");await drain_pages("rescue-rules")
 ui.view="world";ui._open_camp_menu();await frame("preparation-menu")
 check(not ui.menu_actions.has("camp:save") and not ui.menu_items.has("保存进度"),"preparation no longer duplicates outer save")
 ui._clear_menu();ui._open_system_menu()
 check(ui.menu_actions.has("new:save"),"outer world menu retains save progress")
 ui._clear_menu()
 for context in ["world","hub"]:
  ui.camp_context=context;ui.view="camp_status";ui.status_id="hunapu";ui._mouse_accept(ui._canvas_offset()+Vector2(128,100));check(ui.view=="camp_status",context+" status body stays open");ui._cancel();check(ui.view==context,context+" status return works")
 ui.game=g;g.mode="hub";g.hub_position=Vector2i(6,7);ui.hub_controller.enter_room("H06",false,false);await frame("sea-city-medic")
 var hub=ui.hub_controller;var doctor=hub.objects.filter(func(o):return o.action=="treat")
 check(doctor.size()==1 and doctor[0].sprite=="actor" and doctor[0].name=="女医者","treatment belongs to visible female medic")
 check(not hub.objects.any(func(o):return o.sprite=="medicine_wagon") and hub.scenery.any(func(o):return o.name=="medicine_wagon"),"cart is scenery and cannot be interacted with")
 check(ui._party_hub_sprite(doctor[0],{}).path.contains("class-18"),"female medic uses healer class art")
 g.hub_position=Vector2i(6,5);hub.enter_room("H06",false,false)
 check(not hub.objects.any(func(o):return hub.object_occupies(o,g.hub_position)) and not hub.scenery.any(func(o):return o.rect.has_point(g.hub_position)),"old hub checkpoint cannot overlap new medic or cart")
 g.hub_position=Vector2i(6,4);hub.facing=Vector2i.DOWN;hub.accept();check(g.flags.get("workers_treated",false),"interacting with female medic still treats rescued workers");await drain_pages("medic-dialogue")
 ui.view="hub";ui.busy=false;g.flags.chapter1_complete=true;g.cleared_stages.append(105);ui._menu_action("new:chapter2","");check(g.chapter==2 and g.route=="celica","ordinary transition creates east party");await drain_pages("chapter2-intro")
 hub.enter_room("H21",false,false);await frame("chapter2-class-cast")
 for entry in [["east_departure","carlo"],["east_mireille","mireille"],["east_lisa","lisa"]]:
  var o=hub.objects.filter(func(x):return x.action==entry[0])[0];var art=ui._party_hub_sprite(o,{})
  check(art.path==ui.PartySprites.Reviewed.metadata().maps[ui.PartySprites.Reviewed.key(g.roster[entry[1]])]["tactical-idle"].path,"class sprite matches current profession "+entry[1])
  check(ResourceLoader.exists(art.path),"class sprite resource exists "+entry[1])
 await tasks_frame(g,"chapter2-departure-task")
 g.flags.east_departure_ready=true;await tasks_frame(g,"chapter2-sea-task")
 if visual:
  # Audit every authored main task at both supported phone ratios.
  for spec in [[Vector2i(2556,1179),Rect2(177,0,2202,1116),"wide"],[Vector2i(1334,750),Rect2(0,0,1334,750),"compact"]]:
   screen.size=spec[0];phone.safe_area_override=spec[1];phone._layout()
   for id in State.read_json("res://data/current_tasks_20261103.json"):
    ui.game=g;ui.view="world";ui.field_notes.open_tasks();ui.field_notes.record.text=Tasks.route_task(int(id));await frame(spec[2]+"-task-"+id,false)
    for n in range(1,ui.field_notes.journal_pages()):ui.field_notes.direction(Vector2i.RIGHT);await frame(spec[2]+"-task-"+id+"-p"+str(n),false)
   await forecast(fresh(),spec[2]+"-forecast")
   for context in ["world","battle","overview"]:
    ui.view=context;phone._sync_controls();await frame(spec[2]+"-controls-"+context,false)
   await tasks_frame(g,spec[2]+"-sea-task")
func run():
 DirAccess.make_dir_recursive_absolute(CACHE+"slots");visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
 domain()
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
 await interface_checks()
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;await create_timer(.25).timeout
 var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks.size(),"labels":checks,"errors":errors,"evidence":evidence,"screenshots":shots},"  "));file.close()
 print("CHAPTER_FEEDBACK ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
