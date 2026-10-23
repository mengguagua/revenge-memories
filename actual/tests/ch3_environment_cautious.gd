extends "res://tests/ch3_environment_play.gd"
## Ordinary-input safer leader positioning, inherited from the recorded chapter-three review.
func refresh_threats()->void:
 risk_cache.clear();threats.clear()
 for e in ui.game.living("enemy"):
  var mobile=e.get("behavior","")!="guard" or int(e.class_id) in [12,13,15,16]
  threats.append({"unit":e,"cells":ui.game.reachable(e).costs.keys() if mobile else [State.pos(e)]})
func rank(u:Dictionary)->int:
 if u.id==ui.game.leader_id():return 9
 if u.id=="lord":return 0
 if u.id=="roan":return 1
 if int(u.class_id) in [17,18]:return 8
 return 3
func plan(u:Dictionary)->Dictionary:
 var choice=super.plan(u)
 if u.id!=ui.game.leader_id() or ui.game.living("enemy").is_empty():return choice
 var candidate=u.duplicate(true);candidate.position=[choice.cell.x,choice.cell.y]
 var danger=risk(candidate,choice.cell);var counter=0.0
 if choice.kind=="attack":
  if int(choice.spell)>=0:candidate.weapon_index=int(choice.spell)
  var enemy=ui.game.find_unit(choice.target);var gap=distance(choice.cell,State.pos(enemy));var reply=Rules.default_counter(enemy,gap)
  if Rules.can_attack(reply,gap):
   var st=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(choice.cell));counter=float(st.damage)*(2 if st.attack_speed>st.defender_attack_speed else 1)
 if danger*1.2+counter+Items.cost(int(choice.get("spell",-1)))<int(u.hp)-6:return choice
 # The leader supports from behind the active heavy infantry, never supplies the front line.
 var front=ui.game.find_unit("lord")
 if front.is_empty()or int(front.hp)<=0:front=ui.game.find_unit("carlo")
 if front.is_empty()or int(front.hp)<=0:return choice
 var graph=ui.game.reachable(u);var best={"kind":"wait","cell":State.pos(u),"score":-1.0e9,"target":"","spell":-1}
 for cell in graph.costs:
  if not ui.game.can_stop(u,cell):continue
  var score=-risk(u,cell)*8.0-abs(distance(cell,State.pos(front))-3)*1.7-float(graph.costs[cell])*.05
  if risk(u,cell)>=int(u.hp)-6:score-=500
  if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
 return best
func battle(enter_encounter:bool=true)->void:
 if enter_encounter:key(KEY_Z);choose("new:battle");await settle()
 var stage=ui.game.stage_id;var record={"stage":stage,"code":ui.game.battle_data.code,"initial_party":ui.game.party.duplicate(),"turns":[],"initial_players":ui.game.living("player").duplicate(true),"initial_enemies":ui.game.living("enemy").duplicate(true)}
 await snapshot(str(ui.game.battle_data.code)+"-deployment")
 for pass_ in range(90):
  if abort or ui.game.battle_outcome!="":break
  var round_=ui.game.turn;var members=ui.game.living("player").filter(func(u):return u.get("controllable",true));members.sort_custom(func(a,b):return rank(a)<rank(b))
  for unit in members:
   if ui.game.turn!=round_ or ui.game.battle_outcome!="" or abort:break
   await act(str(unit.id))
  if not abort and ui.game.battle_outcome.is_empty()and ui.game.phase=="player"and ui.game.turn==round_:key(KEY_S);choose("end_turn");await settle()
  record.turns.append({"turn":ui.game.turn,"enemies":ui.game.living("enemy").size(),"players":ui.game.living("player").size(),"quest":ui.game.flags.quest.duplicate(true)})
  print("CONTINUOUS_RETRY ",record.code," T",ui.game.turn," E",ui.game.living("enemy").size()," P",ui.game.living("player").size()," ",ui.game.battle_outcome)
 record.outcome=ui.game.battle_outcome;record.final_turn=ui.game.turn;record.final_players=ui.game.living("player").duplicate(true);record.final_roster=ui.game.roster.duplicate(true);battles.append(record)
 if ui.game.battle_outcome!="victory":record_failure("Natural retry continuation failed: "+str(record.code));return
 await snapshot(str(record.code)+"-victory");key(KEY_Z);choose("continue_world");await settle()
