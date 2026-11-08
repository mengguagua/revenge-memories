extends SceneTree
const State=preload("res://core/game_state.gd")
const M=preload("res://core/mechanical_puppets.gd")
const P=preload("res://core/prometheus_story.gd")
const L=preload("res://core/late_dialogue.gd")
const D=preload("res://core/late_battle_dialogue.gd")
const Art=preload("res://core/mechanical_art.gd")
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(value:bool,label:String):
 checks.append(label)
 if not value:errors.append(label);push_error(label)
func fresh(id:int,code:String):
 var g=State.new();var chapter=2 if id<300 else 3 if id<400 else 4 if id<500 else 5
 g.save_path="res://reports/full-assessment-20261025/campaign-final-r4/ch%d/chain-%s-deployment.json"%[chapter,code]
 check(g.load_game(),code+" old checkpoint loads")
 g.save_path="/private/tmp/revenge-story-puppet-test.json"
 check(g.start_battle(id),code+" fresh deployment")
 return g
func flattened(pages:Array)->String:
 return "／".join(pages.map(func(p):return str(p.speaker)+"："+str(p.text)))
func run():
 var old_f24=State.new();old_f24.save_path="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F24-deployment.json"
 check(old_f24.load_game(),"Old F24 still loads without midbattle injection")
 check(old_f24.retry_battle() and M.is_cyclops(old_f24.find_unit("F24_e10")),"Retry updates replaced model even when unit ID stayed the same")
 var g=fresh(408,"F44");var boss=g.find_unit("F44_boss");var hero=g.find_unit("eileen")
 check(M.is_prometheus(boss) and boss.hp==64 and boss.move==6,"F44 has approved boss")
 check(M.part_keys(boss)==["fire","life"] and M.part_hp(boss,"life")==22,"Independent dual cores")
 check(g.EnemyExperience.value_for(408,boss)==171,"Boss level10 value171")
 var before=JSON.stringify(g.units)
 hero.position=[23,8];boss.position=[24,8];hero.hp=60;hero.max_hp=60;hero.strength=50;hero.skill=80;hero.speed=30;hero.weapon_index=23
 var plan=g.plan_combat("eileen","F44_boss","fire")
 check(not plan.is_empty(),"Select fire core in real combat")
 for event in plan.get("events",[]):g.commit_strike(event)
 check(M.part_hp(boss,"fire")==0 and boss.hp==64 and M.part_hp(boss,"life")==22,"Fire-core damage never spills to other bars")
 check(g.Rules.weapon_index(g.Rules.attack_context(boss,3))==M.ANCHOR,"Broken fire falls back to physical range3")
 check(g.save_game(),"Broken dual-core save writes")
 var loaded=State.new();loaded.save_path=g.save_path
 check(loaded.load_game() and M.part_hp(loaded.find_unit("F44_boss"),"fire")==0,"Broken dual-core save reloads")
 g=fresh(408,"F44");boss=g.find_unit("F44_boss");hero=g.find_unit("eileen")
 hero.position=[23,8];boss.position=[24,8];hero.hp=60;hero.max_hp=60;hero.strength=66;hero.skill=100;hero.speed=0;hero.weapon_index=23;boss.hp=10;boss.speed=0
 var kills=g.kills;g.rng_state=0;plan=g.plan_combat("eileen","F44_boss")
 check(plan.events.any(func(e):return e.get("prometheus_revived",false)),"Lethal body strike schedules real revival")
 check(boss.hp==10 and M.part_hp(boss,"life")==22,"Forecast never mutates revival")
 for event in plan.events:g.commit_strike(event)
 check(boss.hp==24 and M.part_hp(boss,"life")==0 and g.kills==kills,"Revival consumes life core without kill")
 check(not g.flags.has("prometheus_outcome"),"First zero HP is not destroyed ending")
 check(flattened(g.story_events[-1].pages).contains("里面还有人"),"Revival line queues once")
 var hp=boss.hp;g.phase="enemy";M.phase_end(g)
 check(boss.hp==hp,"Broken life core stops regeneration")
 boss.parts.life.hp=22;boss.hp=50;M.phase_end(g)
 check(boss.hp==56,"Live life core heals six at own phase end")
 boss.parts.life.hp=0;g.phase="player";g.commit_strike({"attacker":"eileen","defender":"F44_boss","hp_after":0})
 check(g.flags.get("prometheus_outcome","")=="destroyed","Final body death records destroyed route")
 check(g.battle_outcome.is_empty(),"Boss kill alone cannot bypass Viser/three controls")
 g=fresh(408,"F44");boss=g.find_unit("F44_boss")
 for u in g.units:
  if u.side=="enemy" and u.id!="F44_boss":u.side="neutral"
 M.refresh(g)
 check(not boss.get("mechanical_retreating",false) and boss.move==6,"Prometheus never retreats when alone")
 check(not g.living("enemy").is_empty(),"Prometheus still counts as an enemy")
 g=fresh(408,"F44");boss=g.find_unit("F44_boss")
 P.interact(g,"maintenance_panel")
 check(not g.flags.quest.get("maintenance_pending",false),"Key is required before maintenance")
 var viser=g.find_unit("F44_viser");viser.hp=0;g.story_on_death(viser)
 check(P.captured(g) and viser.hp==1 and viser.surrendered,"Viser detained alive after defeat")
 check(boss.side=="enemy" and not boss.get("no_counter",false),"Capturing Viser does not shut down boss")
 check(not P.action(g,g.find_unit("repairer0")).is_empty(),"Key opens actual craftsman escort")
 for id in ["regulator_1","regulator_2","regulator_3"]:g.flags.quest.objects[id]=true
 g.check_outcome();check(g.flags.quest.repair_since==1,"Three regulators begin a timed test")
 P.interact(g,"maintenance_panel");check(not g.flags.quest.get("maintenance_pending",false),"Cannot skip full test turn")
 g.turn=2;g.phase="player"
 P.interact(g,"maintenance_panel");check(not g.flags.quest.get("maintenance_pending",false),"Craftsman must physically reach panel")
 g.find_unit("repairer0").position=[8,13]
 P.interact(g,"maintenance_panel")
 check(g.flags.quest.get("maintenance_pending",false) and boss.side=="enemy","Dialogue waits for voluntary answer")
 check(str(g.story_events[-1].get("callback",""))=="prometheus_maintenance","Saved event carries maintenance callback")
 var memory=g.story_events[-1].pages
 check(flattened(memory).contains("我只换损坏的零件") and flattened(memory).contains("我想走"),"Both patients speak in maintenance route")
 check(g.save_game(),"Maintenance-pending save writes")
 loaded=State.new();loaded.save_path=g.save_path
 check(loaded.load_game() and loaded.flags.quest.get("maintenance_pending",false),"Pending dialogue and escort state survive reload")
 P.accept(loaded);boss=loaded.find_unit("F44_boss")
 check(loaded.flags.get("prometheus_outcome","")=="maintenance" and boss.side=="neutral" and boss.hp>0,"Voluntary outcome keeps body alive")
 check(loaded.battle_outcome.is_empty() and loaded.kills==0,"Maintenance does not erase remaining guards")
 for u in loaded.units:
  if u.side=="enemy":u.hp=0
 check(loaded.check_outcome()!="victory" or loaded.battle_data.reinforcements.is_empty() or loaded.flags.quest.reinforced,"Pending reinforcements cannot be skipped")
 loaded.flags.quest.reinforced=true;loaded.check_outcome()
 check(loaded.battle_outcome=="victory" and loaded.kills==0,"Cleared maintenance route wins with no boss kill reward")
 check(not M.valid_part(boss,"fire") and M.action(loaded,boss).is_empty(),"Maintenance stops attacks and part targeting")
 check(loaded.save_game(),"Maintenance victory saves")
 var again=State.new();again.save_path=loaded.save_path
 check(again.load_game(),"Maintenance victory reloads")
 for outcome in ["maintenance","destroyed"]:
  loaded.flags.prometheus_outcome=outcome
  var rows=L.outcome(loaded,"H55","两队",1,2)
  check(flattened(L.pages(loaded,rows)).contains("让开了" if outcome=="maintenance" else "再也醒不过来了"),"H55 carries "+outcome)
  var ends=preload("res://core/chapter5_endings.gd").entries(loaded)
  var ep=ends.filter(func(e):return e.title=="普罗米修斯")
  check(ep.size()==1 and str(ep[0].text).contains("修好后醒来" if outcome=="maintenance" else "没有再醒来"),"Epilogue carries "+outcome)
 g=fresh(204,"F24");var eye=g.find_unit("F24_e10");var victim=g.find_unit("F24_e9")
 check(M.is_cyclops(eye),"F24 approved cyclops slot")
 victim.position=[23,9];eye.position=[22,8];victim.hp=5;eye.hp=10;g.phase="enemy";M.phase_start(g)
 check(victim.hp==10 and eye.hp==10,"Eight-neighbour heal five, excludes self")
 check(g.flags.get("seen_F24-EYE-HEAL",false),"F24 introduction requires real healing")
 var attacker=g.find_unit("eileen");attacker.item_id=0;attacker.weapon_index=23
 var with_core=g.Rules.attack_stats(attacker,eye,0).hit;eye.parts.eye.hp=0
 check(with_core==floori(float(g.Rules.attack_stats(attacker,eye,0).hit)/2.0),"Cyclops halves final ordinary hit only")
 check(g.Rules.attack_stats(attacker,M.defence_context(eye,"eye"),0).hit>=with_core,"Core target gets no body evasion")
 g=fresh(206,"F26");var owl=g.find_unit("F26_e3")
 check(M.is_owl(owl) and owl.move==8,"F26 approved owl")
 var target=g.find_unit("eileen");var stats=g.Rules.attack_stats(owl,target,0);owl.parts.engine.hp=0
 check(stats.defender_defence==maxi(0,int(g.Rules.attack_stats(owl,target,0).defender_defence)-2),"Owl engine pierces two effective defence")
 owl.mechanical_canto_pending=true
 check(M.canto_path(g,owl).is_empty(),"Broken engine cancels unused canto")
 owl.parts.engine.hp=12;owl.mechanical_canto_pending=true
 var path=M.canto_path(g,owl)
 check(path.size()<=4 and not owl.has("mechanical_canto_pending"),"Canto consumes exactly one up-to-three-step move")
 var total=0;var stage_count=0
 for stage in g.stages.values():
  var machines=stage.get("enemies",[]).filter(func(u):return M.is_puppet(u))
  if not machines.is_empty():
   stage_count+=1;total+=machines.size()
   check(stage.route=="celica" and int(stage.chapter) in [2,3,4],str(stage.code)+" only heroine route")
   var probe=State.new();probe.battle_data=stage
   for u in machines:check(probe.movement_cost(u,Vector2i(u.position[0],u.position[1]))<255,str(u.id)+" legal spawn terrain")
  check(not stage.get("reinforcements",[]).any(func(u):return M.is_puppet(u)),str(stage.code)+" no mechanical reinforcements")
 check(total==15 and stage_count==10,"Approved deployment total15 in10")
 for model in ["cyclops","owl","prometheus"]:
  for asset in Art.trio_data().models[model].maps.values():check(ResourceLoader.exists(str(asset.path)),model+" map resource loads")
 # Source coverage and optional-skip readability: required disclosures are in gated hubs.
 for spec in [["H23","薇娅","放箭"],["H25","灯屋","普罗米修斯"],["H33","确认","前一年"],["H43","等待","今年"],["H46","将观测","冻死"],["J54","开场","合上外面的通道"]]:
  var all=[]
  for group in L.groups(spec[0],spec[1]):all+=group.lines
  check("／".join(all).contains(spec[2]),str(spec[0])+" mandatory causal detail")
 var report=FileAccess.open("res://reports/dialogue-ch2-5-20261107/logic-checks.json",FileAccess.WRITE)
 report.store_string(JSON.stringify({"checks":checks,"errors":errors},"  "));report.close()
 print("STORY_PUPPET_CHECKS ",checks.size()," errors=",errors)
 quit(0 if errors.is_empty() else 1)
