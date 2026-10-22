extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/chapter5-redesign-20261022/finale/"
var checks=[]
var failures=[]
var maps=[]
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append(label)
 if not ok:failures.append(label);push_error(label)
func flood(g,start):
 var seen={start:true};var q=[start]
 while not q.is_empty():
  var p=q.pop_front()
  for delta in g.DIRECTIONS:
   var n=p+delta
   if n.x<=0 or n.y<=0 or n.x>=g.battle_data.map.width-1 or n.y>=g.battle_data.map.height-1 or seen.has(n)or g.movement_cost({"class_id":6},n)>=255:continue
   seen[n]=true;q.append(n)
 return seen
func run():
 var sources=State.read_json("res://reports/chapter5-redesign-20261022/sources.json")
 for code in ["J53","J54"]:
  var g=State.new();g.save_path=sources[code];var sha=FileAccess.get_file_as_string(g.save_path).sha256_text();check(g.load_game(),code+" genuine world source loads");g.save_path=OUT+"fixture-working-"+code+".json";check(g.start_battle(533 if code=="J53"else 534),code+" normal current joint entry")
  var used={};var positions=g.battle_data.player_positions_by_route;check(g.battle_data.player_positions==positions.alm+positions.celica,code+" flat deployment exactly agrees with two route lists")
  for side in ["alm","celica"]:
   check(positions[side].size()==10,code+" ten candidate slots "+side);var p=positions[side][0];var reachable=flood(g,Vector2i(p[0],p[1]))
   for cell in positions[side]:
    var at=Vector2i(cell[0],cell[1]);check(not used.has(at),code+" no candidate overlap "+str(at));used[at]=true;check(reachable.has(at),code+" candidate reachable within playable interior "+str(at))
   for obj in g.battle_data.objects:
    var front=obj.get("approach",obj.position);check(reachable.has(Vector2i(front[0],front[1])),code+" side can reach object front "+side+" "+obj.id)
   var boss=g.find_unit(g.battle_data.boss_id);var count=0
   for delta in g.DIRECTIONS:
    if reachable.has(State.pos(boss)+delta):count+=1
   check(count>=2,code+" at least two real melee approach cells from "+side)
  check(used.size()==20,code+" all twenty slots counted")
  for u in g.living("player"):
   check(positions[u.route].has(u.position),code+" deployed unit belongs to its own route slots "+u.id);check(g.parties[u.route].has(u.id),code+" original party owner preserved "+u.id)
  var extra={}
  if code=="J54":
   var boss=g.find_unit(g.battle_data.boss_id);var strength=int(boss.strength);boss.hp=int(boss.max_hp)/2;var before_hp=boss.hp;g.check_outcome();var summoned=g.units.filter(func(u):return str(u.id).begins_with("J54_summon"));check(summoned.size()==3,"J54 exactly three summons fit fixed source neighborhood");check(boss.hp==before_hp and boss.strength==strength+3,"J54 half-health no heal and exactly strength plus three")
   var occupied={}
   for u in g.living("player")+g.living("enemy"):check(not occupied.has(State.pos(u)),"J54 summons do not overlap "+u.id);occupied[State.pos(u)]=true
   for u in summoned:check(g.movement_cost(u,State.pos(u))<255,"J54 native spawn lands on valid platform "+u.id)
   g.check_outcome();check(g.units.filter(func(u):return str(u.id).begins_with("J54_summon")).size()==3 and boss.strength==strength+3,"J54 phase cannot repeat")
   extra={"summon_positions":summoned.map(func(u):return u.position),"half_hp":boss.hp,"strength":boss.strength}
  check(FileAccess.get_file_as_string(sources[code]).sha256_text()==sha,code+" original source untouched");maps.append({"code":code,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"observations":extra})
 var f=FileAccess.open(OUT+"geometry-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":failures.is_empty(),"check_count":checks.size(),"checks":checks,"failures":failures,"maps":maps,"fixture":true,"is_actual_playthrough":false},"  "));f.close();print("FINALE_GEOMETRY ",checks.size()," ",JSON.stringify(failures));quit(0 if failures.is_empty()else 1)
