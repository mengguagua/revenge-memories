extends "res://tests/ch3_redesign_play.gd"
## Ordinary result-menu retry of an authentic F32 defeat, then continuous input.
const RETRY_SOURCE="res://reports/chapter3-redesign-20261022/play/continuous-delivery/working-journey.json"
const PREDECESSOR="res://reports/chapter3-redesign-20261022/play/continuous-delivery/continuous-delivery-play.json"
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
func run()->void:
 late_label="continuous-retry";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder));source_checkpoint=RETRY_SOURCE
 var source_hash=FileAccess.get_file_as_string(RETRY_SOURCE).sha256_text();var prior_hash=FileAccess.get_file_as_string(PREDECESSOR).sha256_text();var prior=State.read_json(PREDECESSOR);var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(RETRY_SOURCE),ProjectSettings.globalize_path(working));ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Authentic failed journey failed to load")
 if not abort and(ui.game.stage_id!=305 or ui.game.battle_outcome!="defeat"or ui.game.turn!=9):record_failure("Source is not recorded F32 T9 defeat")
 if not abort:
  ui._resume_journey();await settle();await snapshot("F32-real-defeat-before-retry");key(KEY_Z);choose("retry");await settle();await snapshot("F32-normal-retry-entry")
  operations.append({"kind":"ordinary result-menu retry","action":"retry","source":RETRY_SOURCE,"source_turn":9,"retry_turn":ui.game.turn,"retained_prior_casualties":["mireille","lisa"]})
 for code in ["F32","S32","F33","M32","S31","M33"]:
  if abort:break
  var stage={"M32":302,"M33":303,"F32":305,"F33":306,"S31":311,"S32":312}[code];path_cache.clear();risk_cache.clear()
  if code!="F32":
   if ui.game.route!=ui.game.stages[stage].route:await switch_team()
   if not abort:await go(int(ui.game.stages[stage].node));await prepare_current()
   if not abort:key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
  if abort:break
  var before=inputs;var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text();var count=battles.size();await battle(false)
  var b={"code":code,"source":RETRY_SOURCE,"source_sha256":source_hash,"entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
  if battles.size()>count:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.duplicate();b.final_turn=ui.game.turn;b.return_view=ui.view;late_records.append(b);write_progress()
 if not abort:
  await go(9);enter_hub();await settle();await hub_action("third_council");await leave_hub();await switch_team();await go(9);enter_hub();await settle();await hub_action("third_council");await snapshot("D33-council")
  await hub_action("third_relations");await hub_action("third_messenger");choose("hub:third_finish");await settle();await snapshot("chapter-end")
  if not ui.game.flags.get("chapter3_complete",false):record_failure("Third chapter did not complete after genuine retry")
  if not abort:
   key(KEY_Z);choose("new:chapter4");await settle()
   if ui.game.chapter!=4:record_failure("Fourth chapter did not open")
   else:await snapshot("chapter4-start")
 if FileAccess.get_file_as_string(RETRY_SOURCE).sha256_text()!=source_hash:record_failure("Authentic defeat source modified")
 write_progress();var chain={"passed":not abort,"predecessor_report":PREDECESSOR,"predecessor_report_sha256":prior_hash,"inherited_victories":prior.battles.filter(func(b):return b.outcome=="victory"),"retained_failed_attempt":prior.battles.filter(func(b):return b.code=="F32"),"resumed_battles":late_records,"retry_count":1,"source":RETRY_SOURCE,"source_sha256":source_hash,"source_unchanged":FileAccess.get_file_as_string(RETRY_SOURCE).sha256_text()==source_hash,"chapter":ui.game.chapter,"chapter3_complete":ui.game.flags.get("chapter3_complete",false),"checkpoints":checkpoints,"operations":operations,"failures":failures,"no_state_rng_or_outcome_edits":true}
 var f=FileAccess.open(late_folder+"continuous-chain.json",FileAccess.WRITE);f.store_string(JSON.stringify(chain,"  "));f.close();print("CONTINUOUS_RETRY_FINAL ",JSON.stringify({"passed":not abort,"chapter":ui.game.chapter,"failures":failures}));ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
