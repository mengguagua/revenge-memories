extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/chapter4-redesign-20261022/rescue/"
var checks=[]
var failures=[]
var records=[]
func check(ok,label):
 checks.append(label)
 if not ok:failures.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
 var sources=State.read_json("res://reports/chapter4-redesign-20261022/sources.json")
 for code in ["F43","S42"]:
  var g=State.new();g.save_path=sources[code];var source_hash=FileAccess.get_file_as_string(g.save_path).sha256_text();check(g.load_game(),code+" source loads");g.save_path=OUT+"fixture-working-"+code+".json";check(g.start_battle(407 if code=="F43"else 412),code+" fresh entry")
  if code=="F43":
   g.phase="enemy";g.turn=3;g.ChapterFour.after_phase(g);var summoned=g.units.filter(func(u):return str(u.id).begins_with("F43_summon"));check(summoned.size()==3,"F43 all three native summons fit near fixed origin")
   for u in summoned:check(g.in_bounds(State.pos(u))and g.movement_cost(u,State.pos(u))<255 and g.category(State.pos(u))!=16,"F43 summoned unit lands on dry legal shrine ground "+u.id)
  else:
   for u in g.units:
    if u.has("advance_after"):
     g.turn=2;check(g.ai_action(u).destination==State.pos(u),"S42 flier waits before original third turn "+u.id)
  var ids=["marsh_group0","marsh_group1","marsh_group2"]if code=="F43"else["island_group0","island_group1"];var traces={};var poison=[]
  for u in g.units:
   if u.side=="enemy":u.hp=0
   if not ids.has(u.id):u.hidden=true
  g.phase="player";g.turn=1
  for id in ids:traces[id]=[g.find_unit(id).position.duplicate()]
  for iteration in range(100):
   var remaining=false
   for id in ids:
    if g.flags.quest.evacuated.has(id):continue
    remaining=true;var u=g.find_unit(id);u.acted=false;var action=g.ai_action(u);var p:Vector2i=action.destination
    for step in g.path_to(u,p):
     if g.category(step)==16:poison.append({"unit":id,"step":[step.x,step.y]})
    g.selected_id=id;g.move_origin=State.pos(u);check(g.move_selected(p),code+" native AI proposed legal ordinary movement "+id+" "+str(iteration));g.mark_wait(id);traces[id].append(u.position.duplicate())
   if not remaining:break
  for id in ids:check(g.flags.quest.evacuated.has(id),code+" actual AI reaches exit "+id)
  check(poison.is_empty(),code+" automatic evacuation never traverses poison terrain")
  check(FileAccess.get_file_as_string(sources[code]).sha256_text()==source_hash,code+" genuine source unchanged")
  records.append({"code":code,"traces":traces,"poison_cells":poison,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()})
 var f=FileAccess.open(OUT+"escort-path-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":failures.is_empty(),"check_count":checks.size(),"failures":failures,"maps":records,"fixture":true,"is_actual_playthrough":false,"scope":"Isolated cleared-map escort AI route, three fixed-origin summon spawn cells, original delayed flier AI; production maps/core/source checkpoints untouched."},"  "));f.close();print("RESCUE_PATH_PROBE ",checks.size()," ",JSON.stringify(failures));quit(0 if failures.is_empty()else 1)
