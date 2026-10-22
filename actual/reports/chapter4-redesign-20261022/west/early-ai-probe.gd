extends SceneTree
const State=preload("res://core/game_state.gd")
const ROOT="res://reports/chapter4-redesign-20261022/"
var checks=0
var errors=[]
var records={}
func check(ok,label):
 checks+=1
 if not ok:errors.append(label);push_error(label)
func _initialize():call_deferred("run")
func setup(code):
 var g=State.new();g.save_path=ROOT+"play/first-west/first-west-"+code+"-entry.json";check(g.load_game(),code+" real roster checkpoint loads")
 g.save_path=ROOT+"west/unused-simulation-save.json";check(g.retry_battle(),code+" resets through actual preparation");check(g.start_battle(402 if code=="M42"else 404),code+" current map starts");return g
func move(g,u,to,label):
 var act=g._toward(u,to);g.selected_id=u.id;g.move_origin=State.pos(u);check(g.move_selected(act.destination),label+" ordinary movement accepted");return u.position.duplicate()
func scenario(code,defend):
 var g=setup(code);var trace=[];var npc_targets=[];var npc_ids=["old_comrade","station_worker"]if code=="M42"else["church_wounded0","church_wounded1"]
 for turn in range(1,4):
  g.turn=turn;g.phase="player"
  for u in g.units:u.acted=false
  var allied=[]
  if defend and code=="M42" and turn==1:
   var lance=g.find_unit("lance");var friend=g.find_unit("old_comrade");var options=[]
   for p in g.reachable(lance).costs:
    if g.can_stop(lance,p) and absi(p.x-friend.position[0])+absi(p.y-friend.position[1])==1:options.append(p)
   check(not options.is_empty(),"M42 Lance reaches parley front on first turn")
   if not options.is_empty():
    g.selected_id=lance.id;g.move_origin=State.pos(lance);check(g.move_selected(options[0]),"M42 ordinary first-turn parley move");check(g.interact("lance_parley"),"M42 normal parley interaction succeeds");allied.append({"id":lance.id,"position":lance.position,"action":"lance_parley"})
  if defend and code=="M44":
   var lance=g.find_unit("lance");allied.append({"id":lance.id,"position":move(g,lance,Vector2i(5,9)if turn==1 else Vector2i(5,8),"M44 medical-lane guard turn "+str(turn)),"action":"guard western ward door"})
   var hunapu=g.find_unit("daan");allied.append({"id":hunapu.id,"position":move(g,hunapu,Vector2i(6,11)if turn==1 else Vector2i(6,8),"M44 second ward guard turn "+str(turn)),"action":"guard eastern ward door; remaining units free for main gate"})
  g.phase="enemy";var actions=[]
  for enemy in g.living("enemy"):
   var before=enemy.position.duplicate();var action=g.ai_action(enemy);g.selected_id=enemy.id;g.move_origin=State.pos(enemy);check(g.move_selected(action.destination),code+" enemy legal AI move "+enemy.id+" t"+str(turn))
   actions.append({"id":enemy.id,"behavior":enemy.behavior,"from":before,"to":enemy.position.duplicate(),"target":action.get("target",""),"reason":action.get("reason","")})
   if npc_ids.has(action.get("target","")) and g.can_attack(enemy,g.find_unit(str(action.target))):npc_targets.append({"turn":turn,"enemy":enemy.id,"target":action.target})
   enemy.acted=true
  trace.append({"turn":turn,"allied_action":allied,"enemy_actions":actions})
 if defend:check(npc_targets.is_empty(),code+(" defended"if defend else" held deployment")+" no NPC attack intent in first three enemy phases")
 return {"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"npc_attack_intents":npc_targets,"trace":trace}
func run():
 for code in ["M42","M44"]:
  records[code+"-hold"]=scenario(code,false);records[code+"-defend"]=scenario(code,true)
 var f=FileAccess.open(ROOT+"west/early-ai-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"records":records,"scope":"Three-round movement/target-intent fixtures use genuine checkpoint roster, current map, actual AI and ordinary movement APIs. Enemies are kept alive and combat damage is not resolved; this is a conservative route/target pressure review, not a completed playthrough. Defended M42 uses genuine first-turn Lance parley; defended M44 assigns Lance and Daan to the two-cell medical entrance so the remaining units can attack main gate. Original save and stage files are never saved or changed."},"  "));f.close();print("CH4_EARLY_AI ",JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors}));quit(0 if errors.is_empty()else 1)
