extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/chapter5-spatial-20261022/"
const CODES={"M51":501,"M52":502,"F51":503,"F52":504,"S51":511,"J53":533,"J54":534}
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
 g.save_path="res://reports/chapter5-spatial-20261022/fixtures/"+code+"-"+suffix+".json"
 var units=JSON.stringify(g.units);var roster=JSON.stringify(g.roster);var flags=JSON.stringify(g.flags.quest);var tiles=JSON.stringify(g.battle_data.map.tiles);var size=[g.battle_data.map.width,g.battle_data.map.height]
 check(g.save_game(),code+" current checkpoint saved "+suffix)
 var restored=State.new();restored.save_path=g.save_path;check(restored.load_game(),code+" current checkpoint reloads "+suffix)
 check(JSON.parse_string(JSON.stringify(restored.units))==JSON.parse_string(units),code+" reloaded units exact "+suffix)
 check(JSON.parse_string(JSON.stringify(restored.roster))==JSON.parse_string(roster),code+" reloaded roster exact "+suffix)
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
  var g=setup(code);var d=g.battle_data;var closed=static_flood(g,State.pos(g.find_unit(g.leader_id())),false);check(g.check_outcome()=="",code+" no instant outcome");var used={}
  for p in d.player_positions:
   var at=Vector2i(p[0],p[1]);check(at.x>0 and at.y>0 and at.x<d.map.width-1 and at.y<d.map.height-1,code+" every deployment interior "+str(p));check(closed.has(at),code+" every deployment connected "+str(p));check(not used.has(at),code+" no candidate overlap "+str(p));used[at]=true
  for u in d.enemies+d.npc_units+d.reinforcements:
   var p=State.pos(u);check(p.x>0 and p.y>0 and p.x<d.map.width-1 and p.y<d.map.height-1,code+" unit or reserve interior "+u.id);check(g.movement_cost(u,p)<255,code+" own class legal ground "+u.id)
   if g.movement_cost({"class_id":6},p)<255:check(closed.has(p),code+" ordinary unit or reserve connected "+u.id)
  check(closed.has(Vector2i(d.exit[0],d.exit[1])),code+" exit reachable inside playable border")
  var saved=g.units.duplicate(true)
  for obj in d.objects:
   var p=Vector2i(obj.position[0],obj.position[1]);check(p.x>0 and p.y>0 and p.x<d.map.width-1 and p.y<d.map.height-1,code+" object interior "+obj.id);var legal=fronts(g,obj).filter(func(at):return closed.has(at));check(not legal.is_empty(),code+" actual object front reachable "+obj.id)
   for at in legal:
    var actor=position_actor(g,at);check(g.interactions_for(actor).any(func(o):return o.id==obj.id),code+" actual interaction exposed "+obj.id+" "+str(at))
  g.units=saved.duplicate(true);g.selected_id="";assert_saved(g,code,"entry")
  for obj in d.objects:
   if obj.id!="archive_exit":interact_named(g,obj.id)
  g.selected_id="";assert_saved(g,code,"interacted")
  if code in ["J53","J54"]:
   check(d.player_positions==d.player_positions_by_route.alm+d.player_positions_by_route.celica,code+" combined slots equal original route lists");check(used.size()==20,code+" all twenty unique slots checked")
   for side in ["alm","celica"]:
    var slots=d.player_positions_by_route[side];check(slots.size()==10,code+" ten original-route candidates "+side);var reach=static_flood(g,Vector2i(slots[0][0],slots[0][1]),false)
    for obj in d.objects:
     var p=obj.get("approach",obj.position);check(reach.has(Vector2i(p[0],p[1])),code+" both sides can reach every objective "+side+" "+obj.id)
    var count=0;var boss=g.find_unit(d.boss_id)
    for delta in g.DIRECTIONS:
     if reach.has(State.pos(boss)+delta):count+=1
    check(count>=2,code+" multiple melee approach cells from "+side)
   for u in saved.filter(func(unit):return unit.side=="player" and int(unit.hp)>0):
    check(g.parties[u.route].has(u.id),code+" deployed member retains original owner "+u.id);check(d.player_positions_by_route[u.route].has(u.position),code+" deployed member uses owner slots "+u.id)
  for m in d.art_modules:
   if m.name!="stair":continue
   for p in m.get("walk_through_cells",[]):check(g.movement_cost({"class_id":6},Vector2i(p[0],p[1]))<255,code+" visible stair tread walkable "+str(p))
  records.append({"code":code,"size":[d.map.width,d.map.height],"connected_cells":closed.size(),"revision":d.tactical_review_version})
 info.layouts=records

func wounded_and_bridge():
 var g=setup("M51");interact_named(g,"ward_1");check(not g.find_unit("royal_wounded0").locked and g.find_unit("royal_wounded1").locked,"M51 each ward unlocks only its own wounded group");interact_named(g,"ward_2");check(not g.find_unit("royal_wounded1").locked,"M51 east ward independently opens")
 clear_enemies(g)
 for u in g.units:
  if not str(u.id).begins_with("royal_wounded"):u.hidden=true
 var traces={"royal_wounded0":[],"royal_wounded1":[]}
 for step in range(100):
  var pending=false
  for id in traces:
   if g.flags.quest.evacuated.has(id):continue
   pending=true;var u=g.find_unit(id);u.acted=false;var action=g.ai_action(u);var destination:Vector2i=action.destination;check(g.can_stop(u,destination),"M51 wounded AI avoids occupied landing "+id+" "+str(step));g.selected_id=id;g.move_origin=State.pos(u);check(g.move_selected(destination),"M51 ordinary movement accepts AI destination "+id+" "+str(step));g.mark_wait(id);traces[id].append(u.position.duplicate())
  if not pending:break
 for id in traces:check(g.flags.quest.evacuated.has(id),"M51 cleared route reaches actual south exit "+id)
 info.cleared_wounded_route=traces
 g=setup("M51");g.find_unit("royal_wounded1").hp=0;interact_named(g,"ward_1");interact_named(g,"ward_2");boss_dead(g);check(g.check_outcome()=="","M51 ward flags and boss alone insufficient");evacuate_at(g,"royal_wounded0",g.battle_data.exit);check(g.check_outcome()=="victory","M51 one living evacuee plus both wards and boss wins")
 g=setup("M51");g.find_unit("royal_wounded0").hp=0;g.find_unit("royal_wounded1").hp=0;check(g.check_outcome()=="defeat","M51 both wounded lost fails")
 g=setup("M52");interact_named(g,"bridge_3");check(not g.ChapterFive.done(g,"bridge_3"),"M52 east lock refuses before earlier locks");interact_named(g,"bridge_2");check(not g.ChapterFive.done(g,"bridge_2"),"M52 middle lock refuses before west lock")
 for id in ["bridge_1","bridge_2","bridge_3"]:interact_named(g,id);check(g.ChapterFive.done(g,id),"M52 ordered lock accepted "+id)
 check(g.check_outcome()=="","M52 three locks still need commander");boss_dead(g);check(g.check_outcome()=="victory","M52 locks and commander win")

func repairs_and_records():
 var g=setup("F51")
 for u in g.battle_data.npc_units:
  for e in g.living("enemy"):check(not g.can_attack(e,g.find_unit(u.id)),"F51 unstarted locked team excluded from enemy targeting "+u.id+" "+e.id)
 interact_named(g,"repair_1");check(not g.find_unit("repair_team0").locked and g.find_unit("repair_team1").locked,"F51 first handoff exposes only working team")
 check(int(g.flags.quest.repair_since.repair_1)==g.turn,"F51 start turn recorded for each team");g.phase="player";g.ChapterFive.after_phase(g);check(not g.find_unit("repair_team0").locked,"F51 same turn does not finish protection")
 g.turn+=1;g.ChapterFive.after_phase(g);check(g.find_unit("repair_team0").locked,"F51 next player turn returns completed team to protection")
 interact_named(g,"repair_2");boss_dead(g);check(g.check_outcome()=="","F51 second team gets its own full handoff round");g.turn+=1;g.ChapterFive.after_phase(g);check(g.find_unit("repair_team1").locked and g.check_outcome()=="victory","F51 both individually protected rounds and boss win")
 for id in ["repair_team0","repair_team1"]:
  g=setup("F51");g.find_unit(id).hp=0;check(g.check_outcome()=="defeat","F51 either repair team loss fails "+id)
 for code in ["F52","J53"]:
  var ids=["lower_west","lower_east"]if code=="F52"else["court_west","court_east"]
  for missing in ids:
   g=setup(code);boss_dead(g)
   for id in ids:
    if id!=missing:interact_named(g,id)
   check(g.check_outcome()=="",code+" each wing confirmation required "+missing)
  g=setup(code)
  for id in ids:interact_named(g,id)
  check(g.check_outcome()=="",code+" two wings still need commander");boss_dead(g);check(g.check_outcome()=="victory",code+" both wings and commander win")
 g=setup("S51");interact_named(g,"archive_exit");check(not g.ChapterFive.done(g,"archive_exit"),"S51 exit refuses without original records and boss");interact_named(g,"old_record");interact_named(g,"archive_exit");check(not g.ChapterFive.done(g,"archive_exit"),"S51 taken record still requires guard defeat");boss_dead(g);check(g.check_outcome()=="","S51 guard plus record still requires physical southern handoff");interact_named(g,"archive_exit");check(g.check_outcome()=="victory","S51 original record handed to actual south exit wins")

func joint_and_finale():
 for code in ["J53","J54"]:
  for id in ["hunapu","eileen"]:
   var g=setup(code);check(not g.find_unit(id).is_empty(),code+" mandatory hero actually deployed "+id);g.find_unit(id).hp=0;check(g.check_outcome()=="defeat",code+" either leader dying fails "+id)
  var g=setup(code);var owners=g.parties.duplicate(true);var original_party=g.party.duplicate()
  for obj in g.battle_data.objects:interact_named(g,obj.id)
  boss_dead(g);check(g.check_outcome()=="victory",code+" victory fixture reaches settlement");check(g.complete_battle(),code+" ordinary settlement succeeds")
  check(g.parties==owners and g.party==original_party,code+" joint settlement preserves original party ownership")
  for u in g.units:
   if u.side=="player"and not u.get("neutral",false):check(g.roster.has(u.id)and g.roster[u.id].route==u.route,code+" result persists both armies member "+u.id)
  var inventory=g.convoy.duplicate(true);var roster=g.roster.duplicate(true);check(not g.complete_battle()and g.convoy==inventory and g.roster==roster,code+" rewards and growth cannot settle twice");g.mode="victory";g.selected_id="";assert_saved(g,code,"settled")
  if code=="J53":check(g.flags.final_access and not g.flags.get("campaign_complete",false),"J53 unlocks final access without ending campaign")
  else:
   check(g.flags.campaign_complete and g.flags.chapter5_complete,"J54 writes final campaign and chapter completion")
   var entries=preload("res://core/chapter5_endings.gd").entries(g);check(entries.size()==22,"ending source contains eighteen member entries and four world entries before UI pagination");check(entries[0].title=="日光仍在"and entries[-1].title=="全篇结束","ending opens with continuing daylight and closes whole campaign")
   for side in ["alm","celica"]:
    for id in g.parties[side]:
     if not g.is_dying(g.roster[id]):continue
     var pages=entries.filter(func(p):return p.title==g.characters[id].name_zh);check(pages.size()==1 and str(pages[0].text).contains("照护")and not str(pages[0].text).contains("遇难"),"ending retains actual dying without inventing death "+id)
 var g=setup("J54");var boss=g.find_unit("J54_boss");var original_strength=int(boss.strength);var half=int(boss.max_hp)/2;boss.hp=half+1;g.check_outcome();check(not g.flags.quest.final_phase,"J54 strictly above half does not trigger phase");boss.hp=half;g.check_outcome();var wave=g.units.filter(func(u):return str(u.id).begins_with("J54_summon"));check(wave.size()==3 and boss.hp==half and boss.strength==original_strength+3,"J54 half HP exactly three reinforcements plus3 and no heal")
 var occupied={}
 for u in g.living("player")+g.living("enemy"):check(not occupied.has(State.pos(u)),"J54 phase units no collision "+u.id);occupied[State.pos(u)]=true
 for u in wave:check(g.movement_cost(u,State.pos(u))<255 and static_flood(g,State.pos(g.find_unit("hunapu")),false).has(State.pos(u)),"J54 native free_spawn near16,10 lands on accessible platform "+u.id)
 g.check_outcome();check(g.units.filter(func(u):return str(u.id).begins_with("J54_summon")).size()==3 and boss.strength==original_strength+3,"J54 phase only once")
 assert_saved(g,"J54","half-phase");var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"J54 half-phase external reload");loaded.check_outcome();check(loaded.units.filter(func(u):return str(u.id).begins_with("J54_summon")).size()==3 and loaded.find_unit("J54_boss").strength==original_strength+3,"J54 reload cannot repeat wave or bonus")
 for id in ["hunapu","eileen"]:
  var u=g.find_unit(id).duplicate(true);u.position=[16,9];var damage=g.Rules.attack_stats(u,boss,0);check(int(damage.damage)>0,"J54 ordinary current weapon/spell can harm entity "+id)
 info.final_phase={"original_strength":original_strength,"half_hp":half,"summon_positions":wave.map(func(u):return u.position)}
 g=setup("J53");var party_snapshot=g.parties.duplicate(true);g.mode="world";g.flags.chapter5_merged=false;g.flags.chapter5_ready={"alm":false,"celica":true};check(not g.ChapterFive.merge(g),"merge requires both route preparations confirmed");g.flags.chapter5_ready.alm=true
 var choice=g.flags.chapter5_deployment.alm.duplicate();g.flags.chapter5_deployment.alm.erase("hunapu");check(not g.ChapterFive.merge(g),"merge cannot omit western hero");g.flags.chapter5_deployment.alm=choice
 choice=g.flags.chapter5_deployment.celica.duplicate();g.flags.chapter5_deployment.celica.erase("eileen");check(not g.ChapterFive.merge(g),"merge cannot omit eastern hero");g.flags.chapter5_deployment.celica=choice
 check(g.ChapterFive.merge(g),"both original parties can confirm legal merge");check(g.parties==party_snapshot and g.route_positions.alm==15 and g.route_positions.celica==15,"merge joins location without merging ownership");check(g.flags.S51_closed==not g.stage_cleared(511),"merge closes only unfinished optional library")
 g=setup("J54");var snap=g.battle_start_snapshot.roster.duplicate(true);check(g.return_to_preparation()and g.world_node==15 and g.route_positions.alm==15 and g.route_positions.celica==15,"joint preparation return uses actual shared forecourt");check(JSON.parse_string(JSON.stringify(g.roster))==JSON.parse_string(JSON.stringify(snap)),"joint preparation preserves genuine prebattle equipment growth and wounds")

func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+"fixtures"));sources=State.read_json(OUT+"sources.json");var source_hashes={};var map_hashes={}
 for c in CODES:source_hashes[c]=FileAccess.get_file_as_string(sources[c]).sha256_text();map_hashes[c]=FileAccess.get_file_as_string("res://data/stages/"+c+".json").sha256_text()
 layouts();wounded_and_bridge();repairs_and_records();joint_and_finale()
 for c in CODES:check(FileAccess.get_file_as_string(sources[c]).sha256_text()==source_hashes[c],c+" genuine original source untouched");check(FileAccess.get_file_as_string("res://data/stages/"+c+".json").sha256_text()==map_hashes[c],c+" production map untouched by fixtures")
 var f=FileAccess.open(OUT+"rules-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"check_count":checks.size(),"checks":checks,"failures":errors,"errors":errors,"map_hashes":map_hashes,"source_hashes":source_hashes,"observations":info,"fixture":true,"is_actual_playthrough":false,"scope":"Isolated current-map legal spawns, real interaction fronts, checkpoint reload, ordinary escort AI after clearing enemies, ordered objectives, independent protection rounds, twenty route-owned slots, dual-hero requirements, one-time final phase and ending ownership/real casualty records. Fixture HP/position/turn/flag setup is in-memory only; no production data/core or genuine checkpoint modified."},"  "));f.close();print("CH5_RULES ",checks.size()," ",JSON.stringify(errors));quit(0 if errors.is_empty()else 1)
