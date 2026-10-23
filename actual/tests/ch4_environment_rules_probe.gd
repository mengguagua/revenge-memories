extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/chapter4-environment-20261023/"
const CODES={"M41":401,"M42":402,"M43":403,"M44":404,"F41":405,"F42":406,"F43":407,"F44":408,"S41":411,"S42":412}
var sources={}
var checks=[]
var errors=[]
var info={}
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func setup(code:String,overrides:Dictionary={}):
 var g=State.new();g.save_path=sources[code]
 check(g.load_game(),code+" genuine source loads");g.save_path=OUT+"fixtures/working-"+code+".json"
 if g.mode in ["battle","victory","defeat"]:check(g.retry_battle(),code+" real preparation restores")
 else:check(g.mode in ["world","hub","deployment"],code+" genuine source already in peaceful preparation")
 for key in overrides:g.flags[key]=overrides[key]
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
 g.save_path="res://reports/chapter4-environment-20261023/fixtures/"+code+"-"+suffix+".json"
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
 check(str(restored.battle_data.tactical_review_version)==str(g.battle_data.tactical_review_version),code+" current revision retained "+suffix)
 for obj in restored.battle_data.objects:
  if obj.has("follows_unit"):check(obj.position==restored.find_unit(str(obj.follows_unit)).position,code+" reloaded following marker matches actual unit "+suffix)

func layouts():
 var records=[]
 for code in CODES:
  var g=setup(code);var origin=State.pos(g.find_unit(g.leader_id()));var closed=static_flood(g,origin,false);var d=g.battle_data;var occupied={}
  check(g.check_outcome()=="",code+" no initial outcome")
  for p in d.player_positions:
   check(p[0]>0 and p[1]>0 and p[0]<d.map.width-1 and p[1]<d.map.height-1,code+" every candidate deployment strictly interior "+str(p));check(closed.has(Vector2i(p[0],p[1])),code+" connected candidate deployment "+str(p));check(not occupied.has(str(p)),code+" candidate slot unique "+str(p));occupied[str(p)]=true
  for u in g.stages[CODES[code]].enemies+g.stages[CODES[code]].npc_units+g.stages[CODES[code]].reinforcements:
   var p=State.pos(u);check(p.x>0 and p.y>0 and p.x<d.map.width-1 and p.y<d.map.height-1,code+" every enemy NPC reserve interior "+u.id)
   if g.movement_cost({"class_id":6},p)<255:check(closed.has(p),code+" ordinary unit/reserve connected "+u.id)
   else:check(g.movement_cost(u,p)<255,code+" own class has legal terrain "+u.id)
  var exit=Vector2i(d.exit[0],d.exit[1]);check(closed.has(exit),code+" exit inside movement flood")
  var saved=g.units.duplicate(true)
  for obj in d.objects:
   var p=Vector2i(obj.position[0],obj.position[1]);check(p.x>0 and p.y>0 and p.x<d.map.width-1 and p.y<d.map.height-1,code+" object interior "+obj.id)
   var legal=fronts(g,obj).filter(func(at):return closed.has(at));check(not legal.is_empty(),code+" interaction reachable "+obj.id)
   for at in legal:
    var actor=position_actor(g,at);check(g.interactions_for(actor).any(func(o):return o.id==obj.id),code+" actual interaction exposed "+obj.id+" "+str(at))
   if obj.has("approach"):check(closed.has(Vector2i(obj.approach[0],obj.approach[1])),code+" dedicated doorway reachable "+obj.id)
  g.units=saved;g.selected_id="";assert_saved(g,code,"entry")
  for obj in d.objects:interact_named(g,obj.id)
  g.selected_id="";assert_saved(g,code,"interacted")
  if d.has("burn_target"):
   var b=Vector2i(d.burn_target[0],d.burn_target[1]);check(closed.has(b),code+" burner can reach actual document doorway")
   check(d.objects.any(func(o):return o.get("approach",[])==d.burn_target),code+" burn target equals record front")
  records.append({"code":code,"size":[d.map.width,d.map.height],"connected":closed.size(),"revision":d.tactical_review_version})
 info.layouts=records

func rescue_routes():
 var traces={}
 for code in ["M41","F43","S42"]:
  var g=setup(code);clear_enemies(g);g.battle_data.reinforcements=[];g.flags.quest.reinforced=true
  var ids=["snow_group0","snow_group1","snow_group2"]if code=="M41"else["marsh_group0","marsh_group1","marsh_group2"]if code=="F43"else["island_group0","island_group1"]
  for u in g.units:
   if not ids.has(u.id):u.hidden=true
  traces[code]={}
  for id in ids:traces[code][id]=[g.find_unit(id).position.duplicate()]
  var poison=[]
  for iteration in range(100):
   var pending=false
   for id in ids:
    if g.flags.quest.evacuated.has(id):continue
    pending=true;var u=g.find_unit(id);u.acted=false;var action=g.ai_action(u);var cell:Vector2i=action.destination
    for step in g.path_to(u,cell):
     if g.category(step)==16:poison.append([id,step.x,step.y])
    check(g.can_stop(u,cell),code+" escort no stacked landing "+id+" "+str(iteration));g.selected_id=id;g.move_origin=State.pos(u);check(g.move_selected(cell),code+" ordinary AI move valid "+id+" "+str(iteration));g.mark_wait(id);traces[code][id].append(u.position.duplicate())
   if not pending:break
  for id in ids:check(g.flags.quest.evacuated.has(id),code+" real escort AI reaches actual exit "+id)
  check(poison.is_empty(),code+" escort route never traverses poison")
  g=setup(code)
  if code=="S42":
   g.find_unit("island_group0").hp=0;check(g.check_outcome()=="defeat","S42 either patient loss makes two impossible")
   g=setup(code);g.find_unit("island_group1").hp=0;check(g.check_outcome()=="defeat","S42 other patient loss also fails")
  else:
   var prefix="snow_group"if code=="M41"else"marsh_group";g.find_unit(prefix+"0").hp=0;check(g.check_outcome()=="",code+" one casualty still permits two survivors");g.find_unit(prefix+"1").hp=0;check(g.check_outcome()=="defeat",code+" fewer than two survivors fails")
 info.cleared_map_escort_traces=traces

func west_rules():
 var g=setup("M41");boss_dead(g)
 for id in ["snow_group0","snow_group1"]:evacuate_at(g,id,g.battle_data.exit)
 check(g.check_outcome()=="","M41 two evacuees still require both road tasks");interact_named(g,"south_gate");check(g.check_outcome()=="","M41 injured rest station remains necessary");interact_named(g,"rest_station");check(g.check_outcome()=="victory","M41 two evacuees south gate rest station and boss win")
 g=setup("M42");interact_named(g,"transfer_station");check(g.flags.transfer_cut,"M42 station immediately writes cross-route cut flag");check(g.check_outcome()=="","M42 station alone still needs commander");boss_dead(g);check(g.check_outcome()=="victory","M42 optional camp and parley not required")
 g=setup("M42");var lance=g.find_unit("lance");var comrade=g.find_unit("old_comrade")
 if not lance.is_empty()and int(lance.hp)>0:
  var legal=[];var field=static_flood(g,State.pos(lance),false)
  for delta in g.DIRECTIONS:
   var p=State.pos(comrade)+delta
   if field.has(p):legal.append(p)
  check(not legal.is_empty(),"M42 Lance has reachable parley neighbor")
  if not legal.is_empty():
   for u in g.units:
    if u.id!=lance.id and State.pos(u)==legal[0]:u.hidden=true
   lance.position=[legal[0].x,legal[0].y];lance.acted=false;g.selected_id=lance.id;g.move_origin=State.pos(lance);check(g.interact("lance_parley"),"M42 normal optional Lance parley")
   check(g.units.filter(func(u):return u.get("old_comrade_group",false)).all(func(u):return u.surrendered and u.side=="neutral"),"M42 only old-comrade group lays down arms")
 else:info.M42_parley_note="Authentic source lacks deployable Lance; optional parley not required for victory."
 g=setup("M43",{"west_tower_safe":false});boss_dead(g);interact_named(g,"outer_court");check(g.check_outcome()=="","M43 control room remains required");interact_named(g,"tower_control");check(g.check_outcome()=="victory","M43 two control objectives plus priest win");g.ChapterFour.on_victory(g);check(g.flags.m43_seized and not g.flags.west_tower_safe,"M43 seizure alone does not perform safe shutdown")
 g=setup("M44");var boss=g.find_unit(str(g.battle_data.boss_id));boss.hp=int(boss.max_hp)/2;g.check_outcome();check(g.flags.quest.mid_done,"M44 half HP triggers wounded retreat scene");boss.hp=0;g.check_outcome();check(boss.hp==1 and boss.surrendered and boss.side=="neutral","M44 defeated Herlan survives surrender at one HP");check(g.living("enemy").is_empty()and g.battle_data.reinforcements.is_empty(),"M44 surrender stops enemy army and reserves");check(g.check_outcome()=="","M44 surrendered boss still requires gatehouse");interact_named(g,"gatehouse");check(g.check_outcome()=="victory","M44 gatehouse plus surrender wins");check(not g.party.has(boss.id),"M44 no unrequested Herlan recruitment")

func well_rules():
 var g=setup("F41");boss_dead(g);g.turn=5;check(g.check_outcome()=="","F41 cannot win before sixth player turn");g.turn=6;g.phase="player";check(g.check_outcome()=="victory","F41 sixth player turn plus boss wins")
 for well in ["well_n","well_s"]:
  g=setup("F41");var obj=g.battle_data.objects.filter(func(o):return o.id==well)[0];var enemy=g.find_unit("F41_e1");enemy.position=obj.position.duplicate();g.phase="player";g.turn=2;g.ChapterFour.after_phase(g);check(g.flags.quest.wells[well],"F41 first arrival only starts occupation warning "+well);g.turn=3;g.ChapterFour.after_phase(g);check(not g.flags.quest.wells[well],"F41 uninterrupted whole round loses well "+well);check(g.check_outcome()=="","F41 one lost well remains recoverable "+well)
  enemy.hp=0;position_actor(g,Vector2i(obj.position[0],obj.position[1]));g.phase="enemy";g.ChapterFour.after_phase(g);check(g.flags.quest.wells[well],"F41 normal friendly occupation recaptures "+well)
 g=setup("F41");g.flags.quest.wells={"well_n":false,"well_s":false};check(g.check_outcome()=="defeat","F41 both wells lost fails")

func fire_rules():
 for code in ["F42","S41"]:
  var record="observatory_record"if code=="F42"else"black_register";var g=setup(code);var burner=g.units.filter(func(u):return u.get("ch4_burner",false))[0]
  g.turn=int(g.battle_data.burn_start)-1;check(g.ai_action(burner).destination==State.pos(burner),code+" burner waits before original departure")
  burner.position=g.battle_data.burn_target.duplicate();g.turn=int(g.battle_data.burn_start);g.ChapterFour.after_wait(g,burner);check(g.flags.quest.burn_count==1 and not g.flags.quest.record_lost,code+" first ignition warns without destroying")
  var original=burner.position.duplicate();burner.position=[original[0]+1,original[1]];g.ChapterFour.after_wait(g,burner);check(g.flags.quest.burn_count==0,code+" interruption resets consecutive ignition")
  burner.position=original;g.ChapterFour.after_wait(g,burner);g.ChapterFour.after_wait(g,burner);check(g.flags.quest.record_lost,code+" two consecutive ignitions destroy record")
  var actor=position_actor(g,Vector2i(original[0],original[1]));check(not g.interact(record),code+" destroyed record cannot be recovered through original doorway");boss_dead(g);check(g.check_outcome()==("defeat"if code=="F42"else"victory"),code+" destruction has correct main-versus-side severity")
  if code=="S41":g.ChapterFour.on_victory(g);check(not g.flags.S41_register_saved,"S41 destroyed branch records loss honestly")
  g=setup(code);interact_named(g,record);burner=g.units.filter(func(u):return u.get("ch4_burner",false))[0];burner.position=g.battle_data.burn_target.duplicate();g.turn=int(g.battle_data.burn_start);g.ChapterFour.after_wait(g,burner);g.ChapterFour.after_wait(g,burner);check(not g.flags.quest.record_lost,code+" protected record cannot subsequently burn")
  if code=="S41":boss_dead(g);check(g.check_outcome()=="victory","S41 saved record and boss win");g.ChapterFour.on_victory(g);check(g.flags.S41_register_saved,"S41 saved branch retained")
 var g=setup("F42");interact_named(g,"observation_device");check(not g.ChapterFour.done(g,"observation_device"),"F42 device refuses before protecting records");interact_named(g,"observatory_record");interact_named(g,"observation_device");check(g.check_outcome()=="","F42 ordered records and device still require boss");boss_dead(g);check(g.check_outcome()=="victory","F42 ordered objectives and boss win")

func eastern_rescue_and_repair():
 var g=setup("F43");interact_named(g,"dry_3");check(not g.ChapterFour.done(g,"dry_3"),"F43 third dry ground refuses out of order");interact_named(g,"dry_2");check(not g.ChapterFour.done(g,"dry_2"),"F43 second dry ground refuses out of order")
 for id in ["dry_1","dry_2","dry_3"]:interact_named(g,id);check(g.ChapterFour.done(g,id),"F43 sequential dry-ground confirmation "+id)
 boss_dead(g);check(g.check_outcome()=="","F43 dry route and priest still require evacuees");evacuate_at(g,"marsh_group0",g.battle_data.exit);check(g.check_outcome()=="","F43 one evacuee insufficient");evacuate_at(g,"marsh_group1",g.battle_data.exit);check(g.check_outcome()=="victory","F43 two evacuees route and priest win")
 g=setup("F43");g.turn=2;g.phase="enemy";g.ChapterFour.after_phase(g);check(not g.flags.quest.summon_wave,"F43 no summon before third turn");g.turn=3;g.phase="player";g.ChapterFour.after_phase(g);check(not g.flags.quest.summon_wave,"F43 wave waits for enemy phase");g.phase="enemy";g.ChapterFour.after_phase(g)
 var summons=g.units.filter(func(u):return u.has("summoner_id"));check(summons.size()==3,"F43 original bounded wave spawns three")
 var occupied={}
 for u in g.living("enemy")+g.living("player"):check(not occupied.has(State.pos(u)),"F43 spawned units never overlap "+u.id);occupied[State.pos(u)]=true
 for u in summons:check(g.movement_cost(u,State.pos(u))<255 and g.category(State.pos(u))!=16,"F43 full fixed-origin wave on dry legal shrine ground "+u.id)
 g.ChapterFour.after_phase(g);check(g.units.filter(func(u):return u.has("summoner_id")).size()==3,"F43 summon wave occurs only once");boss_dead(g);g.check_outcome();check(summons.all(func(u):return u.hidden and u.side=="evacuated"),"F43 priest defeat removes only linked summons");check(g.living("enemy").size()==9,"F43 nine original natural enemies remain")
 for cut in [false,true]:
  g=setup("F44",{"transfer_cut":cut});check(g.flags.quest.transfer_cut_snapshot==cut,"F44 entry military snapshot "+str(cut));check(g.battle_data.reinforcements.size()==(0 if cut else 2),"F44 entry snapshot controls exactly two reserves "+str(cut));g.flags.transfer_cut=not cut;check(g.battle_data.reinforcements.size()==(0 if cut else 2),"F44 late cross-route flag does not rewrite current wave "+str(cut));assert_saved(g,"F44","transfer-cut-"+str(cut))
  g=setup("F44",{"transfer_cut":cut});g.find_unit("repairer0").hp=0;check(g.check_outcome()=="","F44 one surviving repairer sufficient "+str(cut));g.find_unit("repairer1").hp=0;check(g.check_outcome()=="defeat","F44 no repairers fails "+str(cut))
 g=setup("F44");boss_dead(g)
 for id in ["regulator_1","regulator_2","regulator_3"]:interact_named(g,id)
 check(g.check_outcome()==""and int(g.flags.quest.repair_since)==g.turn,"F44 final handoff starts mandatory observation round");g.turn+=1;g.phase="player";check(g.check_outcome()=="victory","F44 next player turn after three handoffs and boss wins")
 g=setup("S42")
 for u in g.units:
  if u.has("advance_after"):g.turn=2;check(g.ai_action(u).destination==State.pos(u),"S42 northern flier waits through turn two "+u.id)
 boss_dead(g);evacuate_at(g,"island_group0",g.battle_data.exit);evacuate_at(g,"island_group1",g.battle_data.exit);check(g.check_outcome()=="","S42 both patients still need landing confirmation");interact_named(g,"landing");check(g.check_outcome()=="victory","S42 both patients landing and commander win");g.ChapterFour.on_victory(g);check(g.flags.celine_ready and g.flags.S42_settled,"S42 living Celine becomes invitation-ready only")
 g=setup("S42");g.find_unit("celine").hp=0;interact_named(g,"landing");boss_dead(g);evacuate_at(g,"island_group0",g.battle_data.exit);evacuate_at(g,"island_group1",g.battle_data.exit);check(g.check_outcome()=="victory","S42 Celine loss does not erase patients rescued");g.ChapterFour.on_victory(g);check(not g.flags.celine_ready,"S42 Celine death never produces recruitment")

func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+"fixtures"));sources=State.read_json(OUT+"sources.json");var source_hashes={};var map_hashes={}
 for c in CODES:source_hashes[c]=FileAccess.get_file_as_string(sources[c]).sha256_text();map_hashes[c]=FileAccess.get_file_as_string("res://data/stages/"+c+".json").sha256_text()
 layouts();rescue_routes();west_rules();well_rules();fire_rules();eastern_rescue_and_repair()
 info.escort_combat_review={"path":OUT+"rescue/escort-combat-review.json","note":"Cleared-map no-poison routing is not a combat guarantee. Genuine F43 input lost two residents when the party abandoned its rear; the identical map won after normal rear-guard tactics. These independent play reports remain separate from fixtures."}
 for c in CODES:check(FileAccess.get_file_as_string(sources[c]).sha256_text()==source_hashes[c],c+" original source untouched");check(FileAccess.get_file_as_string("res://data/stages/"+c+".json").sha256_text()==map_hashes[c],c+" map untouched by fixture")
 var f=FileAccess.open(OUT+"rules-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"check_count":checks.size(),"checks":checks,"failures":errors,"errors":errors,"map_hashes":map_hashes,"source_hashes":source_hashes,"observations":info,"fixture":true,"is_actual_playthrough":false,"scope":"Isolated current-map spawn, connectivity, interaction/checkpoint and objective fixtures. Cleared-map escort routing uses actual AI/movement; fixture actor placement, HP/death, turn and military flags are in-memory only and not real play. Production map/core and genuine source checkpoints are untouched."},"  "));f.close();print("CH4_RULES ",checks.size()," ",JSON.stringify(errors));quit(0 if errors.is_empty()else 1)
