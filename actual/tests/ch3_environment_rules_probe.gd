extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/chapter3-environment-20261023/"
const CODES={"M31":301,"M32":302,"M33":303,"F31":304,"F32":305,"F33":306,"S31":311,"S32":312}
var sources={}
var checks=[]
var errors=[]
var info={}
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func setup(code:String):
 var g=State.new();g.save_path=sources[code]
 check(g.load_game(),code+" genuine source loads");g.save_path=OUT+"fixtures/working-"+code+".json"
 if g.mode in ["battle","victory","defeat"]:check(g.retry_battle(),code+" real preparation restores")
 else:check(g.mode in ["world","hub","deployment"],code+" genuine source already in peaceful preparation")
 check(g.start_battle(CODES[code]),code+" current battle enters")
 var occupied={}
 for u in g.units:
  check(not occupied.has(State.pos(u)),code+" unique unit "+u.id);occupied[State.pos(u)]=u.id
  check(g.in_bounds(State.pos(u)) and g.movement_cost(u,State.pos(u))<255,code+" legal unit cell "+u.id)
 return g
func boss_dead(g):g.find_unit(str(g.battle_data.boss_id)).hp=0
func clear_enemies(g):
 for u in g.living("enemy"):u.hp=0
func static_flood(g,start:Vector2i,opened:bool)->Dictionary:
 var prior=g.battle_data.map.tiles.duplicate();var width=int(g.battle_data.map.width)
 if opened:
  for obj in g.battle_data.objects:
   if obj.kind in ["door","rescue","bridge"]:
    for p in obj.get("opens",[obj.position] if obj.kind in ["door","rescue"] else []):
     g.battle_data.map.tiles[int(p[1])*width+int(p[0])]=int(obj.get("open_tile",208))
 var seen={start:0};var todo=[start]
 while not todo.is_empty():
  var p=todo.pop_front()
  for delta in g.DIRECTIONS:
   var n=p+delta
   if n.x<=0 or n.y<=0 or n.x>=width-1 or n.y>=int(g.battle_data.map.height)-1 or seen.has(n):continue
   if g.movement_cost({"class_id":6},n)>=255:continue
   seen[n]=int(seen[p])+1;todo.append(n)
 g.battle_data.map.tiles=prior;return seen
func fronts(g,obj)->Array:
 var p=Vector2i(obj.position[0],obj.position[1]);var result=g.visit_fronts(obj)
 if not result.is_empty():return result
 if not obj.get("adjacent",false):return [p]
 result=[p]
 for delta in g.DIRECTIONS:result.append(p+delta)
 return result
func position_actor(g,cell:Vector2i):
 var hero=g.find_unit(g.leader_id())
 for unit in g.units:
  if unit.id!=hero.id and State.pos(unit)==cell:unit.hidden=true
 hero.position=[cell.x,cell.y];hero.acted=false;g.selected_id=hero.id;g.move_origin=cell;return hero
func interact_named(g,id:String)->void:
 var found=false
 for obj in g.battle_data.objects:
  if obj.id!=id:continue
  found=true;var closed=static_flood(g,State.pos(g.find_unit(g.leader_id())),false);var legal=fronts(g,obj).filter(func(p):return closed.has(p))
  check(not legal.is_empty(),str(g.battle_data.code)+" object has reachable front "+id)
  if legal.is_empty():return
  position_actor(g,legal[0]);check(g.interact(id),str(g.battle_data.code)+" normal interaction "+id)
 check(found,"object identity exists "+id)
func evacuate_at(g,id:String,at:Array)->void:
 var u=g.find_unit(id);u.position=at.duplicate();u.acted=false;g.mark_wait(id)
func assert_saved(g,code:String,suffix:String)->void:
 g.save_path="res://reports/chapter3-environment-20261023/fixtures/"+code+"-"+suffix+".json"
 var units=JSON.stringify(g.units);var roster=JSON.stringify(g.roster);var flags=JSON.stringify(g.flags.quest);var tiles=JSON.stringify(g.battle_data.map.tiles);var size=[g.battle_data.map.width,g.battle_data.map.height]
 check(g.save_game(),code+" current checkpoint saved "+suffix)
 var restored=State.new();restored.save_path=g.save_path;check(restored.load_game(),code+" current checkpoint reloads "+suffix)
 check(restored.units==JSON.parse_string(units),code+" reloaded units exact "+suffix)
 check(restored.roster==JSON.parse_string(roster),code+" reloaded roster exact "+suffix)
 check(restored.flags.quest==JSON.parse_string(flags),code+" reloaded quest exact "+suffix)
 var parsed_tiles=JSON.parse_string(tiles);var differences=[]
 for i in range(parsed_tiles.size()):
  if float(restored.battle_data.map.tiles[i])!=float(parsed_tiles[i]):differences.append({"index":i,"before":parsed_tiles[i],"after":restored.battle_data.map.tiles[i]})
 if not info.has("reload_terrain_differences"):info.reload_terrain_differences={}
 info.reload_terrain_differences[code+"-"+suffix]=differences
 check(differences.is_empty() and JSON.parse_string(JSON.stringify(restored.battle_data.map.tiles))==parsed_tiles,code+" reloaded open-door terrain exact "+suffix)
 check([restored.battle_data.map.width,restored.battle_data.map.height]==size,code+" reloaded current dimensions "+suffix)
 check(str(restored.battle_data.tactical_review_version)=="0.10.7-ch3",code+" current revision retained "+suffix)
 for obj in restored.battle_data.objects:
  if obj.has("follows_unit"):check(obj.position==restored.find_unit(str(obj.follows_unit)).position,code+" reloaded following marker matches actual unit "+suffix)

func layouts():
 var records=[]
 for code in CODES:
  var g=setup(code);var origin=State.pos(g.find_unit(g.leader_id()));var closed=static_flood(g,origin,false);var opened=static_flood(g,origin,true)
  check(g.check_outcome()=="",code+" no initial outcome")
  for p in g.battle_data.player_positions:
   check(closed.has(Vector2i(p[0],p[1])),code+" connected deployment "+str(p));check(p[0]>0 and p[1]>0 and p[0]<g.battle_data.map.width-1 and p[1]<g.battle_data.map.height-1,code+" deployment inside playable border "+str(p))
  for u in g.battle_data.enemies+g.battle_data.reinforcements:
   if g.movement_cost({"class_id":6},State.pos(u))<255:check(closed.has(State.pos(u)),code+" ordinary enemy route "+u.id)
  for u in g.battle_data.npc_units:check(opened.has(State.pos(u)),code+" NPC connected after openings "+u.id)
  var exit=Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]);check(opened.has(exit),code+" real exit inside movement flood")
  var saved=g.units.duplicate(true)
  for obj in g.battle_data.objects:
   var legal=fronts(g,obj).filter(func(p):return closed.has(p));check(not legal.is_empty(),code+" object reachable "+obj.id)
   for at in legal:
    var actor=position_actor(g,at);check(g.interactions_for(actor).any(func(o):return o.id==obj.id),code+" actual interaction exposed "+obj.id+" "+str(at))
   if obj.kind=="door":
    for id in obj.get("unlock_units",[]):
     var captive=g.find_unit(id);check(captive.get("locked",false),code+" designated captive initially locked "+id);check(not closed.has(State.pos(captive)),code+" closed door physically isolates "+id)
     for enemy in g.living("enemy"):check(not g.can_attack(enemy,captive),code+" held captive excluded from targeting "+id+" "+enemy.id)
  g.units=saved;g.selected_id="";assert_saved(g,code,"entry")
  var changed=false
  for obj in g.battle_data.objects:
   if obj.kind not in ["door","rescue","bridge"]:continue
   var locked_before={}
   for u in g.units:
    if u.get("locked",false):locked_before[u.id]=true
   interact_named(g,obj.id);changed=true
   for id in obj.get("unlock_units",[]):
    check(not g.find_unit(id).locked,code+" intended captive unlocked "+id);check(static_flood(g,origin,false).has(State.pos(g.find_unit(id))),code+" unlocked captive now physically connected "+id)
   for id in locked_before:
    if not obj.get("unlock_units",[]).has(id):check(g.find_unit(id).locked,code+" unrelated captive stays locked "+obj.id+" "+id)
   for p in obj.get("opens",[]):check(g.movement_cost({"class_id":6},Vector2i(p[0],p[1]))<255,code+" actual opens tile passable "+str(p))
   for a in obj.get("open_art_cells",[]):
    var at=Vector2i(a.position[0],a.position[1]);var nearby=obj.get("opens",[obj.position]).any(func(p):return absi(p[0]-at.x)+absi(p[1]-at.y)<=1)
    check(nearby and g.movement_cost({"class_id":6},at)<255,code+" visible door footprint clears opened or walkable neighbor "+str(a.position))
   for id in obj.get("unlock_units",[]):
    var npc=g.find_unit(id)
    for enemy in g.living("enemy"):
     if enemy.get("behavior","")!="guard":continue
     var distance=absi(State.pos(enemy).x-State.pos(npc).x)+absi(State.pos(enemy).y-State.pos(npc).y);var range=g.Rules.attack_range(enemy)
     if code=="M31" and distance>=range.x and distance<=range.y:
      var approaches=[];var actor=g.find_unit(g.leader_id()).duplicate(true)
      for cell in closed:
       actor.position=[cell.x,cell.y]
       if g.can_attack(actor,enemy):approaches.append([cell.x,cell.y])
      check(not approaches.is_empty(),code+" threatening jail archer can be attacked from outside before opening "+enemy.id)
      if not info.has("opening_risks"):info.opening_risks=[]
      info.opening_risks.append({"code":code,"npc":id,"enemy":enemy.id,"npc_position":npc.position,"enemy_initial_position":enemy.position,"distance":distance,"range":[range.x,range.y],"preopen_attack_cells":approaches,"assessment":"Intentional clear-guards-before-release choice: captive cannot be attacked while locked; archer is accessible outside. Initial firing radius is a warning, not an unavoidable failure. Actual AI may reposition the archer."})
     else:check(distance<range.x or distance>range.y,code+" released captive outside initial guard-post direct range "+id+" "+enemy.id)
  if changed:g.selected_id="";assert_saved(g,code,"opened")
  records.append({"code":code,"size":[g.battle_data.map.width,g.battle_data.map.height],"closed_connected":closed.size(),"opened_connected":opened.size()})
 info.layouts=records

func run_evacuation(g,ids:Array,label:String):
 clear_enemies(g)
 # Only fixture isolation: clear stationary allies from the path, retain real escort AI/movement.
 for u in g.units:
  if not ids.has(u.id):u.hidden=true
 var traces={}
 for id in ids:traces[id]=[g.find_unit(id).position.duplicate()]
 for step in range(100):
  var pending=false
  for id in ids:
   var u=g.find_unit(id)
   if g.flags.quest.evacuated.has(id):continue
   pending=true;u.acted=false;var action=g.ai_action(u);var destination:Vector2i=action.destination
   check(g.reachable(u).costs.has(destination),label+" AI destination legally reachable "+id+" "+str(step))
   check(g.can_stop(u,destination),label+" AI destination no overlap "+id+" "+str(step))
   g.selected_id=id;g.move_origin=State.pos(u);check(g.move_selected(destination),label+" ordinary movement API accepts "+id+" "+str(step));g.mark_wait(id);traces[id].append(u.position.duplicate())
  if not pending:break
 for id in ids:check(g.flags.quest.evacuated.has(id),label+" actual AI reaches actual exit "+id)
 if not info.has("escort_traces"):info.escort_traces={}
 info.escort_traces[label]=traces

func west_objectives():
 var g=setup("M31");boss_dead(g);check(g.check_outcome()=="","M31 boss alone insufficient");interact_named(g,"court");check(g.check_outcome()=="","M31 open gate alone does not evacuate");run_evacuation(g,["detained0","detained1"],"M31 detained escape");check(g.check_outcome()=="victory","M31 two actual AI evacuations plus boss wins")
 for id in ["detained0","detained1"]:
  g=setup("M31");g.find_unit(id).hp=0;check(g.check_outcome()=="defeat","M31 either required detained death fails "+id)
 g=setup("M31");interact_named(g,"court");var npc=g.find_unit("detained0");var enemy=g.find_unit(str(g.battle_data.boss_id));enemy.position=g.battle_data.objects[0].position.duplicate();check(g.ai_action(npc).destination==State.pos(npc),"M31 released civilian waits when enemy is within safety radius")
 for branch in ["german_accept","german_disarm","killed"]:
  g=setup("M33");interact_named(g,"dock_control");interact_named(g,"workshop");var german=g.find_unit("german");check(g.check_outcome()=="","M33 objectives require boss and German resolution "+branch)
  if branch=="killed":german.hp=0
  else:
   check(not g.ChapterThree.extra_interactions(g,g.find_unit(g.leader_id())).any(func(o):return o.id==branch),"M33 surrender not exposed before boss falls "+branch)
  boss_dead(g);g.check_outcome()
  if branch!="killed":
   check(german.get("offering_surrender",false) and german.get("no_counter",false),"M33 living German offers surrender after boss "+branch)
   var legal=[]
   for delta in g.DIRECTIONS:
    var p=State.pos(german)+delta
    if g.in_bounds(p) and g.movement_cost(g.find_unit(g.leader_id()),p)<255:legal.append(p)
   check(not legal.is_empty(),"M33 surrender has physical adjacent approach "+branch)
   if not legal.is_empty():position_actor(g,legal[0]);check(g.interact(branch),"M33 ordinary surrender choice "+branch)
   check(german.surrendered and german.side=="neutral", "M33 surrender removes enemy combat "+branch)
  check(g.check_outcome()=="victory","M33 resolution and required objects win "+branch);g.ChapterThree.on_victory(g);check(g.flags.chapter3_recruits.german==(branch=="german_accept"),"M33 recruit decision recorded exactly "+branch)

func transport():
 var g=setup("M32");var cart=g.find_unit("transport_cart");var path=g.battle_data.transport_path;var bounds=[]
 check(path[0]==cart.position,"M32 cart begins at path start");check(path[-1]==g.battle_data.exit,"M32 path ends at declared exit")
 var texture=load(cart.sprite_path);var size=Vector2i(texture.get_width(),texture.get_height());check(size==Vector2i(32,16),"M32 native wagon has 2x1 footprint")
 for i in range(path.size()):
  var p=Vector2i(path[i][0],path[i][1]);check(g.movement_cost(cart,p)<255,"M32 route center walkable "+str(i))
  if i>0:check(absi(path[i][0]-path[i-1][0])+absi(path[i][1]-path[i-1][1])==1,"M32 route contiguous step "+str(i))
  var footprint=[]
  for x in range(2):
   var cell=p+Vector2i(x,0);check(g.in_bounds(cell) and g.movement_cost(cart,cell)<255,"M32 full wagon footprint walkable "+str(i)+" "+str(cell));footprint.append([cell.x,cell.y])
  bounds.append(footprint)
 for u in g.units:
  if u.id!="transport_cart":u.hidden=true
 g.turn=5;g.phase="player";g.ChapterThree.after_phase(g);check(int(g.flags.quest.transport_index)==0,"M32 does not depart on turn five player phase")
 g.turn=6;g.phase="enemy";g.ChapterThree.after_phase(g);check(int(g.flags.quest.transport_index)==0,"M32 no departure on enemy phase")
 g.phase="player";g.ChapterThree.after_phase(g);check(int(g.flags.quest.transport_index)==1 and cart.position==path[1],"M32 turn six player phase moves exactly one cell")
 for o in g.battle_data.objects:
  if o.get("follows_unit","")==cart.id:check(o.position==cart.position,"M32 release marker follows moving wagon")
 g.selected_id="";assert_saved(g,"M32","cart-moved")
 for step in range(path.size()+1):
  if g.battle_outcome=="defeat":break
  var previous=int(g.flags.quest.transport_index);g.turn+=1;g.ChapterThree.after_phase(g);check(int(g.flags.quest.transport_index)==previous+1,"M32 continues one cell each eligible player phase "+str(step))
  for o in g.battle_data.objects:
   if o.get("follows_unit","")==cart.id:check(o.position==cart.position,"M32 marker remains synchronized "+str(step))
 check(g.battle_outcome=="defeat","M32 cart escaping north fails")
 for id in ["station_w","station_n","cart_release"]:
  g=setup("M32");interact_named(g,id);var previous=g.find_unit("transport_cart").position.duplicate();g.turn=6;g.phase="player";g.ChapterThree.after_phase(g);check(g.flags.quest.transport_stopped and g.find_unit("transport_cart").position==previous,"M32 each control or release independently stops cart "+id)
 g=setup("M32");g.find_unit("transport_cart").hp=0;check(g.check_outcome()=="defeat","M32 destroyed cart fails")
 g=setup("M32");boss_dead(g);interact_named(g,"station_w");interact_named(g,"station_n");check(g.check_outcome()=="","M32 two stations still need release");interact_named(g,"cart_release");check(not g.find_unit("transport_cart").locked,"M32 release truly unlocks cart");check(g.check_outcome()=="victory","M32 two stations plus release and boss win")
 g=setup("M32");interact_named(g,"cart_release");interact_named(g,"station_w");boss_dead(g);check(g.check_outcome()=="","M32 north station remains necessary")
 g=setup("M32");interact_named(g,"cart_release");interact_named(g,"station_n");boss_dead(g);check(g.check_outcome()=="","M32 west station remains necessary")
 g=setup("M32");interact_named(g,"cart_release");interact_named(g,"station_w");interact_named(g,"station_n");check(g.check_outcome()=="","M32 all controls still require boss defeat")
 info.transport={"native_sprite_size":[size.x,size.y],"path_steps":path.size()-1,"footprints":bounds,"first_eligible_phase":"turn 6 player phase; rule is turn > 5","tested_markers":"actual follows_unit position updates and save/reload"}

func east_objectives():
 var g=setup("F31");interact_named(g,"ship_lock");check(not g.find_unit("dock_patients0").locked and g.find_unit("dock_patients1").locked,"F31 north lock releases only northern patients");interact_named(g,"mooring");check(not g.find_unit("dock_patients1").locked,"F31 south lock releases southern patients");boss_dead(g);check(g.check_outcome()=="","F31 unlocked patients still need evacuation");run_evacuation(g,["dock_patients0","dock_patients1"],"F31 both patients escape");check(g.check_outcome()=="victory","F31 both survivors actually reach ship")
 g=setup("F31");g.find_unit("dock_patients0").hp=0;interact_named(g,"ship_lock");interact_named(g,"mooring");boss_dead(g);check(g.check_outcome()=="","F31 surviving group still must leave");run_evacuation(g,["dock_patients1"],"F31 one survivor escape");check(g.check_outcome()=="victory","F31 one living evacuated group can win")
 g=setup("F31");g.find_unit("dock_patients0").hp=0;g.find_unit("dock_patients1").hp=0;check(g.check_outcome()=="defeat","F31 both patient groups dead fails")
 g=setup("F32");interact_named(g,"guide_notes");boss_dead(g);check(g.check_outcome()=="","F32 notes do not substitute for living guide escort");run_evacuation(g,["salt_guide"],"F32 living guide escape");check(g.check_outcome()=="victory","F32 living guide reaches exit and wins");g.ChapterThree.on_victory(g);check(g.flags.salt_guide_survived,"F32 survival outcome recorded")
 g=setup("F32");g.find_unit("salt_guide").hp=0;boss_dead(g);check(g.check_outcome()=="","F32 dead guide requires route notes");interact_named(g,"guide_notes");check(g.check_outcome()=="victory","F32 route notes enable dead-guide branch");g.ChapterThree.on_victory(g);check(not g.flags.salt_guide_survived,"F32 guide loss remains recorded")
 g=setup("F32");var guide=g.find_unit("salt_guide");var guard=g.find_unit(str(g.battle_data.boss_id));guard.position=[guide.position[0]+1,guide.position[1]];check(g.ai_action(guide).destination==State.pos(guide),"F32 guide pauses for nearby enemy")
 for id in ["ritual_worker0","ritual_worker1"]:
  g=setup("F33");g.find_unit(id).hp=0;check(g.check_outcome()=="defeat","F33 each maintenance worker required "+id)
 for missing in ["workers_gate","regulation_record","control_array"]:
  g=setup("F33");boss_dead(g)
  for id in ["workers_gate","regulation_record","control_array"]:
   if id!=missing:interact_named(g,id)
  check(g.check_outcome()=="","F33 required objective cannot be skipped "+missing)
 g=setup("F33");interact_named(g,"workers_gate");check(not g.find_unit("ritual_worker0").locked and not g.find_unit("ritual_worker1").locked,"F33 workshop frees both workers");interact_named(g,"regulation_record");interact_named(g,"control_array");check(g.check_outcome()=="","F33 objectives still require priest defeat");boss_dead(g);check(g.check_outcome()=="victory","F33 living workers and three objectives plus priest win")

func sides():
 var g=setup("S31");boss_dead(g);interact_named(g,"family_w");check(g.check_outcome()=="","S31 eastern gate remains necessary");interact_named(g,"family_e");check(g.check_outcome()=="victory","S31 both families open and boss win without Lena interaction")
 for id in ["family0","family1"]:
  g=setup("S31");g.find_unit(id).hp=0;interact_named(g,"family_w");interact_named(g,"family_e");boss_dead(g);check(g.check_outcome()=="victory","S31 single survivor can win "+id);g.ChapterThree.on_victory(g);check(not g.flags.S31_families[id],"S31 deceased family remains recorded "+id)
 g=setup("S31");g.find_unit("family0").hp=0;g.find_unit("family1").hp=0;check(g.check_outcome()=="defeat","S31 both groups lost fails")
 for lost in ["none","noya","noya_brother","both"]:
  g=setup("S32")
  if lost in ["noya","both"]:g.find_unit("noya").hp=0
  if lost in ["noya_brother","both"]:g.find_unit("noya_brother").hp=0
  interact_named(g,"mage_barrack");boss_dead(g);check(g.check_outcome()=="","S32 civilian gate remains required "+lost);g.flags.erase("seen_S32-BROTHER");g.story_events.clear();interact_named(g,"civilian_barrack");check(JSON.stringify(g.story_events).contains("没能救下" if lost in ["noya_brother","both"] else "还活着"),"S32 dialogue follows brother real life state "+lost);check(g.check_outcome()=="victory","S32 both barracks and boss permit recorded outcome "+lost);g.ChapterThree.on_victory(g)
  check(g.flags.chapter3_recruits.noya==(lost not in ["noya","both"]),"S32 Noya real survival recorded "+lost);check(g.flags.noya_brother_survived==(lost not in ["noya_brother","both"]),"S32 brother survival independently recorded "+lost)

func external_m31_evidence():
 var path=OUT+"play/round1-west/round1-west-play.json";var victory_path=OUT+"play/round1-west/round1-west-M31-victory.json";var report=State.read_json(path);var victory=State.read_json(victory_path)
 var battles=report.battles.filter(func(b):return b.code=="M31")
 check(report.passed and not report.forced_victories and not report.stat_edits and not report.source_saves_modified,"M31 separate real-input report passed without intervention")
 check(battles.size()==1 and battles[0].entry_map_sha256==FileAccess.get_file_as_string("res://data/stages/M31.json").sha256_text(),"M31 separate real-input evidence matches current map")
 check(victory.battle_outcome=="victory","M31 separate genuine snapshot records victory")
 var residents=[]
 for id in ["detained0","detained1"]:
  var matches=victory.units.filter(func(u):return u.id==id);check(matches.size()==1 and int(matches[0].hp)>0 and matches[0].side=="evacuated" and victory.flags.quest.evacuated.has(id),"M31 separate actual play saved living evacuee "+id)
  if not matches.is_empty():residents.append({"id":id,"hp":matches[0].hp,"position":matches[0].position,"side":matches[0].side})
 info.external_real_play_evidence={"report":path,"victory_snapshot":victory_path,"sha256":FileAccess.get_file_as_string(path).sha256_text(),"turn":victory.turn,"residents":residents,"independently_generated_by_root":true,"not_counted_as_fixture_playthrough":true}

func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+"fixtures"));sources=State.read_json(OUT+"sources.json");var source_hashes={};var map_hashes={}
 for c in CODES:source_hashes[c]=FileAccess.get_file_as_string(sources[c]).sha256_text();map_hashes[c]=FileAccess.get_file_as_string("res://data/stages/"+c+".json").sha256_text()
 layouts();west_objectives();transport();east_objectives();sides();external_m31_evidence()
 for c in CODES:
  check(FileAccess.get_file_as_string(sources[c]).sha256_text()==source_hashes[c],c+" original source untouched");check(FileAccess.get_file_as_string("res://data/stages/"+c+".json").sha256_text()==map_hashes[c],c+" map untouched by fixture")
 var f=FileAccess.open(OUT+"rules-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"check_count":checks.size(),"checks":checks,"failures":errors,"errors":errors,"map_hashes":map_hashes,"source_hashes":source_hashes,"observations":info,"fixture":true,"is_actual_playthrough":false,"scope":"Isolated in-memory rule fixtures: legal spawns, physical closed/open connectivity, ordinary interaction API, checkpoint reload, real escort AI on cleared maps, objective success/failure branches. Enemy removal, actor positioning and branch deaths are fixture setup; these are NOT real playthrough results. No production map/core or genuine source checkpoint modified."},"  "));f.close()
 print("CH3_RULES ",checks.size()," ",JSON.stringify(errors));quit(0 if errors.is_empty()else 1)
