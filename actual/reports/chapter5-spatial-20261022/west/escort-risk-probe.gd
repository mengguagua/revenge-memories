extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/chapter5-spatial-20261022/west/"
var checks=0
var errors=[]
func check(ok,label):
 checks+=1
 if not ok:errors.append(label);push_error(label)
func _initialize():call_deferred("run")
func setup():
 var sources=State.read_json("res://reports/chapter5-redesign-20261022/sources.json");var g=State.new();g.save_path=sources.M51;check(g.load_game(),"M51 genuine chapter-five source loads");g.save_path=OUT+"unused-fixture-save.json"
 if g.mode in["battle","victory","defeat"]:check(g.retry_battle(),"M51 normal reset to preparation")
 check(g.start_battle(501),"M51 current map starts");return g
func run():
 var g=setup();var early=[];var targeted=[]
 for turn in range(1,4):
  g.turn=turn;g.phase="enemy";var actions=[]
  for e in g.living("enemy"):
   e.acted=false;var before=e.position.duplicate();var a=g.ai_action(e);g.selected_id=e.id;g.move_origin=State.pos(e);check(g.move_selected(a.destination),"legal actual AI move "+e.id+" turn "+str(turn));e.acted=true
   actions.append({"id":e.id,"from":before,"to":e.position.duplicate(),"target":a.get("target","")})
   if str(a.get("target","")).begins_with("royal_wounded"):targeted.append({"turn":turn,"enemy":e.id,"target":a.target})
  for id in["royal_wounded0","royal_wounded1"]:
   var u=g.find_unit(id);check(u.locked,"wounded remains waiting before release "+id)
   for e in g.living("enemy"):check(not g.can_attack(e,u),"locked wounded cannot be attacked "+id+" "+e.id)
  early.append({"turn":turn,"enemy_actions":actions})
 check(targeted.is_empty(),"no unreleased wounded targeted in first three phases")
 g=setup();g.phase="player";var hero=g.find_unit("hunapu")
 for o in g.battle_data.objects:
  hero.position=o.approach.duplicate();hero.acted=false;g.selected_id=hero.id;g.move_origin=State.pos(hero);check(g.interactions_for(hero).any(func(x):return x.id==o.id),"actual south-door interaction exists "+o.id);check(g.interact(o.id),"actual ward interaction releases "+o.id)
 for u in g.units:
  if str(u.id).begins_with("royal_wounded"):continue
  if u.side=="enemy"and u.id!=g.battle_data.boss_id:u.hp=0
  else:u.hidden=true
 # Keep the distant north boss alive: escort speed remains its ordinary 2 rather than the clear-map speedup.
 g.flags.quest.reinforced=true;var traces={"royal_wounded0":[],"royal_wounded1":[]};var paths={"royal_wounded0":[],"royal_wounded1":[]}
 for turn in range(1,25):
  g.turn=turn;var pending=false
  for id in traces:
   var u=g.find_unit(id)
   if g.flags.quest.evacuated.has(id):continue
   pending=true;u.acted=false;var a=g.ai_action(u);var actual=g.path_to(u,a.destination)
   for p in actual:
    paths[id].append([p.x,p.y]);check(str(g.battle_data.logic_grid[p.y]).substr(p.x,1)in["=","b"],"escort uses visible medical paving "+id+" "+str(p))
   g.selected_id=id;g.move_origin=State.pos(u);check(g.move_selected(a.destination),"actual wounded movement accepted "+id+" "+str(turn));g.mark_wait(id);traces[id].append({"turn":turn,"position":u.position.duplicate()})
  if not pending:break
 for id in traces:
  check(g.flags.quest.evacuated.has(id),"released wounded actually reaches south exit "+id)
  var x=8 if id=="royal_wounded0" else 25
  check(paths[id].has([x,16]),"patient must cross actual south door "+id)
  check(paths[id].has([x,17]),"patient crosses outdoor threshold after door "+id)
  check(paths[id].find([x,16])<paths[id].find([x,17]),"indoor to door to outdoor order "+id)
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"map_sha256":FileAccess.get_file_as_string("res://data/stages/M51.json").sha256_text(),"early_enemy_ai":early,"unreleased_npc_targets":targeted,"escort_traces":traces,"escort_path_cells":paths,"scope":"Isolated fixtures from a genuine chapter-five source. First three enemy AI phases retain current enemies and positions, recording movement/target intent without damage. A separate escort fixture releases both wards through normal interaction APIs, removes ordinary enemies and hides formal allies to isolate navigation; the distant boss stays alive so wounded use ordinary move 2. Actual AI/path_to/move_selected/mark_wait confirms both travel on visible paving to the real exit. No source save or production map is mutated; not a combat playthrough."}
 var f=FileAccess.open(OUT+"escort-risk-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("CH5_ESCORT_RISK ",JSON.stringify({"passed":report.passed,"checks":checks,"errors":errors}));quit(0 if errors.is_empty()else 1)
