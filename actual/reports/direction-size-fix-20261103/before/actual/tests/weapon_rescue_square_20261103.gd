extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/weapon-rescue-square-20261103/"
const CACHE="/private/tmp/weapon-rescue-square-20261103/"
var checks=[];var errors=[];var shots=[];var evidence={};var screen;var phone;var ui;var visual=false;var full_game
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func normalized(v):return JSON.parse_string(JSON.stringify(v))
func fixture(stage:int=105,reserves:bool=false):
 var g=State.new();g.new_game();g.save_path=CACHE+"fixture.json";g.world_node=int(g.stages[stage].node);g.route_positions.alm=g.world_node;g.previous_world_node=5 if stage==105 else 3
 if reserves:
  for id in ["hervi","fula","beck"]:g.party.append(id);g.roster[id]=g._initial_character(id)
  g.parties.alm=g.party.duplicate();g.roster.hervi.level=5;g.roster.hervi.magic_level=2;g.roster.hervi.exp=90
  g.roster.fula.level=6;g.roster.fula.magic_level=5;g.roster.fula.exp=99;g.roster.fula.hp=0;g.roster.fula.dying=true;g.roster.fula.ever_dying=true
  g.roster.beck.level=20;g.roster.beck.exp=14
  # Deterministic deployment-cap fixture: real start_battle leaves healthy
  # reserves in the party, while the injured member is never deployed.
  g.stages[stage].player_positions=g.stages[stage].player_positions.slice(0,3)
 check(g.start_battle(stage),"ordinary isolated battle starts "+str(stage));g.story_events=[];return g
func open_workers(g,count:int):
 for n in range(count):
  var o=g.battle_data.objects[n];var p=Vector2i(o.position[0],o.position[1]);var actor=g.find_unit("hunapu");actor.position=[p.x,p.y+1];actor.acted=false;g.selected_id=actor.id
  check(g.interact(str(o.id)),"real rescue interaction opens group "+str(n))
 g.story_events=[]
func win(g):
 g.find_unit(str(g.battle_data.boss_id)).hp=0
 check(g.check_outcome()=="victory","boss defeated with rescued workers permits victory");g.mode="victory"
 check(g.complete_battle(),"ordinary victory settlement completes")
func bonus(g,id:String)->Array:return g.victory_rewards.filter(func(r):return r.unit==id and int(r.get("full_rescue_bonus",0))==20)
func domain():
 var g=fixture();var original=State.read_json("res://data/legacy/rules_full.json")
 check(int(original.items[11].hit)==80 and int(original.items[20].hit)==70,"extracted source data stays unchanged; campaign overlay owns balance")
 for row in [[11,85,21,"钢剑"],[63,90,12,"铜弓"],[64,85,12,"铁弓"],[20,75,12,"钢弓"]]:
  var actor=g._initial_character("hunapu");actor.class_id=row[2];actor.item_id=row[0];actor.skill=7
  var target=g.find_unit("M15_e6");var profile=g.Items.weapon_profile(actor,g.Rules.weapon_index(actor));var stats=g.Rules.attack_stats(actor,target,20)
  check(profile.hit==row[1] and g.Rules.weapon_name(actor)==row[3],"equipped runtime profile has new hit: "+row[3])
  check(stats.hit==clampi(7+int(row[1])-20-g.Rules.attack_speed(target),0,100),"combat calculation uses new hit: "+row[3])
 for row in [[2,80],[21,100],[59,95],[60,90],[61,90],[62,85]]:check(g.Items.item(row[0]).hit==row[1],"other weapon hit unchanged "+str(row[0]))
 g=fixture(105,true);open_workers(g,1);win(g)
 check(not g.flags.get("M15_full_rescue_reward",false) and not g.victory_rewards.any(func(r):return r.has("full_rescue_bonus")),"one rescued group receives no extra20")
 var one=g.roster.hunapu.exp
 g=fixture(105,true);open_workers(g,2);win(g);full_game=g
 check(g.flags.get("M15_full_rescue_reward",false) and int(g.roster.hunapu.exp)==int(one)+20,"both rescued groups give exactly twenty extra XP")
 var announcements=g.story_events.filter(func(e):return e.get("key","")=="M15-FULL-RESCUE-REWARD")
 check(announcements.size()==1 and str(announcements[0].pages[0].text).contains("20点经验"),"actual settlement queues its once-only rescue announcement")
 evidence.announcement=announcements[0].pages.duplicate(true)
 for id in ["hunapu","daan","otto","hervi","fula"]:check(bonus(g,id).size()==1,"one20 XP bonus receipt per formal member "+id)
 check(bonus(g,"beck").is_empty() and g.roster.beck.exp==14 and g.roster.beck.level==20,"level20 member respects existing cap")
 check(g.victory_rewards.all(func(r):return not str(r.unit).begins_with("M15_workers")),"temporary workers never receive party XP")
 check(g.find_unit("hervi").is_empty() and g.roster.hervi.level==6 and g.roster.hervi.exp==10 and bonus(g,"hervi")[0].learned==[24],"healthy reserve learns Thunder through extra20 and keeps receipt")
 check(g.roster.fula.hp==0 and g.roster.fula.dying and g.roster.fula.level==7 and bonus(g,"fula")[0].learned==[43],"injured reserve gains XP and spell without being healed")
 check(g.convoy.alm==[11,20],"normal steel sword and bow rewards unchanged")
 for actor in g.units:
  if g.party.has(str(actor.id)):check(actor.level==g.roster[actor.id].level and actor.exp==g.roster[actor.id].exp,"deployed and persistent XP agree "+str(actor.id))
 var frozen=normalized({"roster":g.roster,"rewards":g.victory_rewards,"rng":g.rng_state})
 check(not g.complete_battle() and normalized({"roster":g.roster,"rewards":g.victory_rewards,"rng":g.rng_state})==frozen,"repeated victory callback cannot duplicate XP or growth")
 check(g.save_game(),"settled bonus and spell receipts save")
 var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"settled reserve bonus loads through normal save validation")
 check(not loaded.complete_battle() and normalized(loaded.victory_rewards)==normalized(g.victory_rewards) and loaded.roster.hervi.exp==10,"reload cannot grant extra20 again")
 for kind in ["dead","locked","evacuated","defeat"]:
  g=fixture();open_workers(g,2)
  if kind=="dead":g.find_unit("M15_workers1").hp=0
  elif kind=="locked":g.find_unit("M15_workers1").locked=true
  elif kind=="evacuated":
   for n in range(2):g.find_unit("M15_workers"+str(n)).side="evacuated";g.find_unit("M15_workers"+str(n)).hidden=true
  if kind=="defeat":
   g.battle_outcome="defeat";check(not g.complete_battle() and not g.flags.get("M15_full_rescue_reward",false),"defeat cannot award rescue bonus");continue
  win(g);check(bool(g.flags.get("M15_full_rescue_reward",false))==(kind=="evacuated"),"full rescue condition handles "+kind)
 g=fixture();open_workers(g,2);g.find_unit("M15_boss").hp=0;g.check_outcome();g.mode="victory"
 check(g.save_game(),"pending unprocessed M15 victory saves")
 loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game() and loaded.complete_battle() and bonus(loaded,"hunapu").size()==1,"old unprocessed victory awards once after load")
 g=fixture(103);open_workers(g,2);win(g);check(not g.flags.get("M15_full_rescue_reward",false),"other rescue stages do not receive M15-only bonus")
 evidence.rewards=full_game.victory_rewards.duplicate(true);evidence.roster=full_game.roster.duplicate(true)
func frame(name:String,capture:bool=true):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" text, bitmap and touch safe areas: "+str(ui.layout_errors)+str(phone.layout_errors))
  if capture:screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func square_controls(label:String):
 var keys=phone.buttons.filter(func(b):return phone.DIRECTION_KEYS.has(b.key));check(keys.size()==4,label+" four direction controls")
 var bounds=keys[0].rect
 for button in keys:bounds=bounds.merge(button.rect)
 check(bounds.size.x==bounds.size.y,label+" outside bounds form an exact square")
 for i in range(keys.size()):
  var b=keys[i];check(b.rect.size.x==b.rect.size.y,label+" each direction bitmap remains square")
  var physical=Rect2(phone.safe_area.position+b.hit_rect.position*phone.pixel_scale,b.hit_rect.size*phone.pixel_scale)
  check(phone.safe_area.encloses(physical) and not phone.game_rect.intersects(physical),label+" direction stays inside safe rail")
  for j in range(i):check(not b.hit_rect.intersects(keys[j].hit_rect),label+" direction touch targets do not overlap")
 evidence[label]={"bounds":str(bounds),"physical_size":str(bounds.size*phone.pixel_scale),"button_size":str(keys[0].rect.size*phone.pixel_scale)}
func interface_checks():
 ui.game=full_game;ui.view="battle";ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="target";full_game.selected_id="hunapu";full_game.find_unit("hunapu").item_id=11;full_game.find_unit("hunapu").position=[15,21];full_game.find_unit("M15_e1").position=[16,21];full_game.find_unit("M15_e1").hp=28;ui.target_ids=["M15_e1"];ui.target_index=0;full_game.cursor=Vector2i(16,21);ui._focus_battle(full_game.cursor,true)
 for spec in [[Vector2i(2556,1179),Rect2(177,0,2202,1116),"wide"],[Vector2i(1334,750),Rect2(0,0,1334,750),"compact"],[Vector2i(852,480),Rect2(0,0,852,480),"small"]]:
  screen.size=spec[0];phone.safe_area_override=spec[1];phone._layout();await frame(spec[2]+"-square-directions");square_controls(spec[2])
 # Reward UI must also resolve non-deployed members from roster.
 screen.size=Vector2i(2556,1179);phone.safe_area_override=Rect2(177,0,2202,1116);phone._layout()
 ui.game=full_game;ui.ui_mode="inspect";ui.view="victory";ui.play_victory_rewards()
 var n=0
 while ui.training_reward_open and n<12:
  var id=str(ui.reward.unit);await frame("rescue-level-"+id)
  if visual and not ui.reward.get("learned",[]).is_empty():check(not ui.presentation_audit.get("learned_spells",{}).get("names",[]).is_empty(),"rescue level-up visibly names new spell "+id)
  ui._accept();await process_frame;await process_frame;n+=1
 check(n>=2 and not ui.training_reward_open and ui.view=="victory","normal victory reward flow completes reserve spell notifications")
 var plain=bonus(full_game,"hervi")[0].duplicate(true);plain.leveled=false;plain.learned=[];ui.reward=plain;ui.view="reward";ui.reward_elapsed=1
 await frame("reserve-plain-experience")
 # Show the concrete rule and the actual system receipt in their normal panels.
 ui.view="battle";ui.busy=false;ui._menu_action("new:goal","");var text="";var total=ui.plot_pages.size()
 for i in range(total):
  text+=str(ui.plot_pages[ui.plot_index].text);ui.dialogue_reveal=str(ui.plot_pages[ui.plot_index].text).length();await frame("rescue-rule-p"+str(i),false);ui._advance_plot()
 await process_frame;check(text.contains("20经验") and not text.contains("没有额外经验"),"battle target explains new full rescue reward")
 ui.busy=false;ui.play_pages(evidence.announcement,"victory","",false)
 ui.dialogue_reveal=999;await frame("full-rescue-bonus-message");ui._advance_plot();await process_frame
func run():
 DirAccess.make_dir_recursive_absolute(CACHE+"slots");visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1";domain()
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;await interface_checks()
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;await create_timer(.25).timeout
 var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks.size(),"labels":checks,"errors":errors,"evidence":evidence,"screenshots":shots},"  "));file.close()
 print("WEAPON_RESCUE_SQUARE ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
