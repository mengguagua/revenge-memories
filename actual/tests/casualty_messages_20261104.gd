extends SceneTree
const State=preload("res://core/game_state.gd")
const Portraits=preload("res://core/portrait_library.gd")
const OUT="res://reports/casualty-messages-20261104/"
const CACHE="/private/tmp/casualty-messages-20261104/"
const EAST=["eileen","mireille","lisa","carlo","lord","roan","shia","noya","celine"]
var errors=[];var checks=[];var evidence={};var cases={};var shots=[];var visual=false;var screen;var phone;var ui
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func battle(id:String):
 var g=State.new();g.new_game();g.save_path=CACHE+id+".json";var stage=105
 if id in EAST:
  g.flags.chapter1_complete=true;g.cleared_stages=[105];check(g.begin_chapter_two(),"east setup begins normally "+id);g.flags.east_departure_ready=true;stage=201;g.hub_record="H21"
 else:g.hub_record="H05"
 if not g.party.has(id):g.party.append(id);g.roster[id]=g._initial_character(id)
 g.parties[g.route]=g.party.duplicate();g.world_node=int(g.stages[stage].node);g.route_positions[g.route]=g.world_node;g.previous_world_node=17 if stage==201 else 5
 check(g.start_battle(stage),"real battle fixture starts "+id);g.story_events=[];return g
func pages(g)->Array:
 var result=[]
 for event in g.story_events:result.append_array(event.get("pages",[]))
 return result
func personal(g)->Array:return pages(g).filter(func(p):return not str(p.get("casualty_id","")).is_empty())
func domain():
 var index=State.new();var lines=State.read_json("res://data/casualty_messages_20261104.json")
 check(lines.size()==index.characters.size(),"all18 formal identities have an authored short message")
 for id in index.characters:
  var g=battle(id);var u=g.find_unit(id);var actor=g.living("enemy")[0]
  g.commit_strike({"attacker":actor.id,"defender":id,"hp_after":0})
  var queued=pages(g);var face=Portraits.speaker(g,str(u.name_zh));var expected=Portraits.phase_key(g,id)
  check(queued.size()==2 and queued[0].get("casualty_id","")==id and queued[0].speaker==u.name_zh and queued[0].text==lines[id],"fatal callback queues personal line before care notice "+id)
  check(str(lines[id]).length()<=18 and not str(lines[id]).is_empty(),"personal text is brief "+id)
  check(face.get("key","")==expected and not face.get("campaign_fallback",false) and ResourceLoader.exists(face.path),"correct portrait still resolves at zero HP "+id)
  check(g.is_dying(u) and not u.dead and queued[1].speaker=="战场提示", "injury and system care notice preserved "+id)
  g.Casualties.enter_dying(g,u);check(pages(g).size()==2,"repeat casualty handling cannot repeat line "+id)
  if id in ["daan","mireille"]:
   check(g.save_game(),"pending injury queue saves "+id);var loaded=State.new();loaded.save_path=g.save_path
   check(loaded.load_game() and personal(loaded).size()==1 and personal(loaded)[0].casualty_id==id,"pending personal cue survives normal load "+id)
   loaded.Casualties.enter_dying(loaded,loaded.find_unit(id));check(personal(loaded).size()==1,"load plus callback cannot append duplicate cue "+id)
  if id in ["hunapu","eileen"]:check(g.check_outcome()=="defeat","hero injury still fails battle "+id)
  cases[id]={"game":g,"page":queued[0].duplicate(true)}
 evidence.messages=lines
 var g=battle("daan");var foe=g.living("enemy").filter(func(u):return not u.get("objective_boss",false))[0];var victim=g.find_unit("daan")
 g.apply_tactical_damage(foe,victim,999,"audit_map_damage");check(personal(g).size()==1 and personal(g)[0].casualty_id=="daan","map damage uses same personal message route")
 g=battle("hunapu");var hero=g.find_unit("hunapu");foe=g.living("enemy")[1];hero.hp=1
 g.commit_strike({"attacker":hero.id,"defender":foe.id,"hp_after":foe.hp,"source_hp_before":1,"source_hp_after":0})
 check(personal(g).size()==1 and personal(g)[0].casualty_id=="hunapu","self damage uses same personal message route")
 g=battle("daan");g.commit_strike({"attacker":"hunapu","defender":"M15_e1","hp_after":0})
 check(personal(g).is_empty(),"enemy death never receives friendly injury message")
 g=State.new();g.new_game();g.save_path=CACHE+"npc.json";g.world_node=4;g.route_positions.alm=4;check(g.start_battle(103),"unrecruited NPC fixture starts");g.story_events=[];g.commit_strike({"attacker":g.battle_data.boss_id,"defender":"lena","hp_after":0})
 check(personal(g).is_empty() and not g.party.has("lena"),"unrecruited NPC death does not claim ordinary party retreat")
 g=State.new();g.new_game();g.save_path=CACHE+"training.json";g.cleared_stages=[101,102,103];g.mode="world";g.flags.prologue_done=true;g.flags.village_ready=true;g.flags.grain_shared=true;g.flags.orders_collected=true;g.story_events=[]
 check(g.Training.start(g,191),"ordinary training fixture starts");g.story_events=[];g.commit_strike({"attacker":g.living("enemy")[0].id,"defender":"daan","hp_after":0})
 check(personal(g).is_empty() and not g.roster.daan.dying,"training knockout has no real injury cue")
func frame(name:String,capture:bool=false):
 ui.notice_time=0;ui.phase_time=0;ui.dialogue_reveal=999;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" glyph, frame and touch safe areas: "+str(ui.layout_errors))
  if capture:screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func advance_plot():
 ui.dialogue_reveal=999;ui._advance_plot();await process_frame;await process_frame
func presentation_all():
 for spec in [[Vector2i(2556,1179),Rect2(177,0,2202,1116),"wide"],[Vector2i(1334,750),Rect2(0,0,1334,750),"compact"]]:
  screen.size=spec[0];phone.safe_area_override=spec[1];phone._layout()
  for id in cases:
   var c=cases[id];ui.game=c.game;ui.view="battle";ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui._clear_menu();ui.play_pages([c.page],"battle","",false)
   await frame(spec[2]+"-"+id,id in ["daan","mireille","carlo","noya"])
   check(ui.plot_pages.all(func(p):return Array(str(p.text).split("\n")).all(func(line):return not str(line).replace("…","").strip_edges().is_empty())),"no punctuation-only line "+spec[2]+" "+id)
   if visual:
    check(ui.plot_layout_audit.has_portrait and ui.plot_layout_audit.portrait_key==Portraits.phase_key(c.game,id),"personal portrait shown for "+spec[2]+" "+id)
    check(ui.text_checks.any(func(row):return str(row.text).replace("\n","")==str(c.page.text)),"complete short text rendered for "+spec[2]+" "+id)
   await advance_plot();check(ui.view=="battle" and not ui.busy,"ordinary line confirms and returns "+spec[2]+" "+id)
 # Existing story-phase portraits must be kept for both heroes.
 for row in [["hunapu",1,"hunapu_victory"],["hunapu",3,"hunapu_present"],["eileen",2,"eileen_chart"],["eileen",3,"eileen_present"]]:
  var g=cases[row[0]].game;g.chapter=row[1];g.flags.korlan_defeated=true;g.flags.sea_chart_collected=true
  check(Portraits.speaker(g,str(g.characters[row[0]].name_zh)).key==row[2],"injury portrait preserves existing story phase "+str(row))
func ready_fatal(id:String,cover:bool=false):
 var g=battle(id);var target=g.find_unit("daan" if cover else id);var foes=g.living("enemy").filter(func(u):return int(u.class_id) in [1,2,4,6,7,22] and not u.get("objective_boss",false));var foe=foes[0]
 for direction in g.DIRECTIONS:
  var at=g.pos(target)+direction
  if g.in_bounds(at) and g.unit_at(at).is_empty() and g.movement_cost(foe,at)<255:foe.position=[at.x,at.y];break
 target.item_id=0;target.speed=0;target.defence=0;target.resistance=0;target.hp=target.max_hp if cover else 1
 foe.skill=40;foe.strength=1 if cover else 40;foe.speed=0;foe.item_id=0;foe.erase("weapon_index")
 if cover:
  var guard=g.find_unit(id);guard.hp=1
  for direction in g.DIRECTIONS:
   var at=g.pos(target)+direction
   if g.in_bounds(at) and g.unit_at(at).is_empty() and g.movement_cost(guard,at)<255:guard.position=[at.x,at.y];break
  target.acted=true;g.selected_id=id;check(g.begin_cover(str(target.id)),"real cover action starts")
 check(g.save_game(),"pre-exchange checkpoint saves "+id+str(cover));return {"game":g,"foe":str(foe.id),"target":str(target.id)}
func real_combat(id:String,cover:bool=false):
 var pair=ready_fatal(id,cover);var g=pair.game;ui.game=g;ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.battle_animation.reset();var saved=FileAccess.get_file_as_string(g.save_path)
 ui._play_combat(pair.foe,pair.target)
 for n in range(100):
  if ui.view=="plot" and ui.plot_pages[ui.plot_index].get("casualty_id","")==id:break
  await process_frame
 check(ui.view=="plot" and ui.plot_pages[ui.plot_index].get("casualty_id","")==id,"real combat pauses on matching personal cue "+id+str(cover))
 check(ui.plot_return=="combat" and not ui.plot_persistent and not g.flags.has("active_plot"),"mid-strike overlay cannot save partial combat "+id+str(cover))
 check(FileAccess.get_file_as_string(g.save_path)==saved,"mid-strike dialogue preserves pre-exchange checkpoint "+id+str(cover))
 check(g.find_unit(id).hp==0 and float(ui.combat_fades.get(id,1))==1,"personal line precedes casualty exit fade "+id+str(cover))
 await frame("combat-before-exit-"+id+("-cover" if cover else ""),true)
 if visual:check(ui.presentation_audit.get("combat_weapons",{}).is_empty(),"portrait cue hides HUD rows beneath dialogue "+id+str(cover))
 if cover:check(g.find_unit(pair.target).hp==g.find_unit(pair.target).max_hp,"guard message appears even when protected target loses no HP")
 await advance_plot();var notices=0
 for n in range(100):
  if ui.view=="plot":
   var p=ui.plot_pages[ui.plot_index]
   check(not p.has("casualty_id"),"personal cue is not replayed after combat "+id+str(cover))
   if p.speaker=="战场提示" and str(p.text).contains("已撤至照护处"):
    notices+=1;await frame("withdrawal-notice-"+id+str(cover),id=="daan")
    check(g.flags.has("active_plot"),"withdrawal notice uses settled persistent dialogue")
    var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game() and loaded.roster[id].dying,"settled injury notice reloads normally "+id+str(cover))
   await advance_plot()
  elif not ui.busy and ui.view in ["battle","defeat","reward"]:break
  else:await process_frame
 check(notices==1 and g.roster[id].dying,"one care notice follows personal message "+id+str(cover))
 if id in ["hunapu","eileen"]:check(g.battle_outcome=="defeat","personal cue preserves real hero defeat")
func run():
 DirAccess.make_dir_recursive_absolute(CACHE+"slots");visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1";domain()
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;await presentation_all()
 screen.size=Vector2i(2556,1179);phone.safe_area_override=Rect2(177,0,2202,1116);phone._layout()
 for id in ["daan","mireille","hunapu"]:await real_combat(id)
 await real_combat("otto",true)
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;await create_timer(.25).timeout
 var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks.size(),"errors":errors,"labels":checks,"evidence":evidence,"screenshots":shots},"  "));file.close()
 print("CASUALTY_MESSAGES ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
