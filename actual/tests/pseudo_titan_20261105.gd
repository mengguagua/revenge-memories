extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const M=preload("res://core/mechanical_puppets.gd")
const Art=preload("res://core/mechanical_art.gd")
const XP=preload("res://core/campaign_experience.gd")
const FIXTURE="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F25-deployment.json"
const OUT="res://reports/pseudo-titan-20261105/"
var checks=[];var errors=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func fresh():
 var g=State.new();g.save_path=FIXTURE
 check(g.load_game(),"Existing real F25 checkpoint loads")
 check(g.units.all(func(u):return not M.is_titan(u)),"Ongoing old F25 does not inject a new enemy")
 g.save_path="/private/tmp/pseudo-titan-current.json"
 check(g.start_battle(205),"Fresh F25 deployment uses current data")
 g.story_events.clear();g.flags.erase("active_plot")
 return g
func arrange(g,distance:int=1):
 var t=g.find_unit("F25_pseudo_titan_1");var p=g.find_unit("eileen")
 t.position=[18,9];p.position=[18-distance,9]
 p.hp=52;p.max_hp=52;p.strength=12;p.skill=40;p.speed=8;p.luck=0;p.defence=30;p.resistance=20;p.acted=false;p.weapon_index=0
 t.hp=42;t.parts.protective_core.hp=16;t.acted=false;g.rng_state=0;g.battle_outcome=""
 return [p,t]
func run():
 var g=fresh();var t=g.find_unit("F25_pseudo_titan_1")
 check(g.battle_data.enemies.size()==16 and g.pos(t)==Vector2i(18,9),"Exactly one nonboss elite at approved F25 position")
 check(t.hp==42 and t.strength==12 and t.speed==1 and t.move==4 and t.exp_value==98,"Approved Lv5 stats and B70→V98")
 check(g.EnemyExperience.base_for(205,t)==70,"Enemy base value70 is not kill EXP")
 check(g.catalog.classes["26"].name_zh=="伪泰坦傀儡","Independent registered profession")
 var titan_count=0
 for stage in g.stages.values():
  for u in stage.get("enemies",[]):
   if M.is_titan(u):titan_count+=1;check(stage.code in ["F25","F33","F41"],"Titan only in approved F25/F33/F41")
 check(titan_count==3,"Three approved story titans")
 check(Rules.weapon_index(t)==1009 and Rules.attack_speed(t)==1 and Rules.attack_range(t)==Vector2i(1,1),"Hammer physical range1, AS1")
 check(Rules.Items.weapon_profile(t,1009).might==2,"Innate hammer might2")
 check(Rules._defence(t)==14 and Rules.Items.magic_defence(t)==12,"Intact body DEF14 RES12")
 var core=M.defence_context(t,M.CORE)
 check(Rules._defence(core)==3 and Rules.Items.magic_defence(core)==2,"Core independent DEF3 RES2; no self armour")
 check(t.defence==4 and t.resistance==2 and not t.has("mechanical_part_context"),"Forecast does not mutate baseline/save fields")
 check(core.hp==16 and core.max_hp==16,"HP-based part forecasts use durability rather than body HP")
 var a=arrange(g);var p=a[0];t=a[1]
 var snapshot=JSON.stringify(g.units);var plan=g.plan_combat(p.id,t.id)
 check(not plan.is_empty() and snapshot==JSON.stringify(g.units),"Planner snapshots body/parts/HP without mutating units")
 var attack=plan.events.filter(func(e):return e.attacker==p.id)[0]
 check(attack.reflection_damage==2 and attack.source_hp_after==50,"Ordinary body attack reflects exactly2")
 for event in plan.events:g.commit_strike(event)
 check(p.hp==52-plan.events.reduce(func(total,e):return total+(int(e.damage) if e.defender==p.id else int(e.get("reflection_damage",0))),0),"Two permitted body strikes reflect twice alongside ordinary counter damage")
 a=arrange(g);p=a[0];t=a[1];p.strength=40
 plan=g.plan_combat(p.id,t.id,M.CORE)
 var player_hits=plan.events.filter(func(e):return e.attacker==p.id)
 check(player_hits.size()==1 and player_hits[0].part_hp_after==0 and player_hits[0].hp_after==42,"Core break caps damage16, cancels followup, no overflow")
 check(plan.events.all(func(e):return not e.has("reflection_damage")),"Core strikes do not reflect")
 var kills=g.kills
 for event in plan.events:g.commit_strike(event)
 check(t.hp==42 and M.part_hp(t)==0 and g.kills==kills,"Core break never kills or adds kill count")
 check(Rules._defence(t)==4 and Rules.Items.magic_defence(t)==2 and t.strength==12 and t.move==4,"Break immediately removes only defensive effects")
 check(not g.flags.get("inventory_processed_deaths",{}).has(t.id),"Core break does not issue kill loot")
 var reward=g.finish_exchange(plan)
 check(reward.gain>0 and reward.gain<180,"Core break grants only damage XP")
 check(g.save_game(),"Broken-core battle saves")
 var restored=State.new();restored.save_path=g.save_path
 check(restored.load_game() and M.part_hp(restored.find_unit(t.id))==0,"Strict load preserves broken core")
 check(restored.retry_battle() and M.part_hp(restored.find_unit(t.id))==16,"Retry restores starting core")
 var bad=t.duplicate(true);bad.parts.protective_core.hp=17
 check(not M.valid_unit(bad),"Invalid core durability rejected")
 bad=t.duplicate(true);bad.mechanical_base_move=4.5
 check(not M.valid_unit(bad),"Fractional Titan move rejected")
 bad=core.duplicate(true);check(not M.valid_unit(bad),"Ephemeral part context cannot be saved")
 a=arrange(g);p=a[0];t=a[1];p.skill=0;t.speed=100;g.rng_state=255
 plan=g.plan_combat(p.id,t.id)
 attack=plan.events.filter(func(e):return e.attacker==p.id)[0]
 check(not attack.hit and attack.reflection_damage==2,"Missed direct attack still reflects2")
 a=arrange(g);p=a[0];t=a[1];p.strength=0
 plan=g.plan_combat(p.id,t.id);attack=plan.events.filter(func(e):return e.attacker==p.id)[0]
 check(attack.hit and attack.reflection_damage==2,"Minimum/zero damage is independent of reflection trigger")
 var zero={"attacker":p.id,"defender":t.id,"hit":true,"damage":0,"source_hp_after":52};M.reflect(zero,p,t)
 check(zero.source_hp_after==50,"Exactly zero damage directly reflects2")
 a=arrange(g,2);p=a[0];t=a[1];p.weapon_index=23
 plan=g.plan_combat(p.id,t.id)
 check(not plan.is_empty() and plan.events.all(func(e):return e.attacker==p.id and e.reflection_damage==2),"Range2 magic cannot be countered but still reflects")
 a=arrange(g);p=a[0];t=a[1]
 plan=g.plan_combat(t.id,p.id)
 check(plan.events.any(func(e):return e.attacker==t.id and e.weapon_index==1009),"Titan still performs normal hammer attacks")
 check(plan.events.any(func(e):return e.attacker==p.id and e.get("reflection_damage",0)==2),"Enemy-phase player counters also receive core reflection")
 a=arrange(g);p=a[0];t=a[1];p.hp=2;p.strength=40;t.hp=1
 plan=g.plan_combat(p.id,t.id)
 check(plan.events.size()==1 and plan.events[0].hp_after==0 and plan.events[0].source_hp_after==0,"Fatal strike reflects from pre-hit core, cancels remaining attacks")
 for event in plan.events:g.commit_strike(event)
 check(p.hp==0 and t.hp==0 and g.kills==kills+1,"Both can die, only actual body kill counts")
 check(g.finish_exchange(plan).is_empty() and g.battle_outcome=="defeat","Reflected leader death uses normal failure and gets no XP")
 g=fresh();a=arrange(g);p=a[0];t=a[1]
 var event=g.apply_tactical_damage(p,t,1,"poison")
 check(p.hp==52 and not event.has("reflection_damage"),"Poison/environment damage does not reflect")
 t.hp=42
 event={"attacker":p.id,"defender":t.id,"hit":true,"damage":0,"hp_before":42,"hp_after":42,"kind":"hero_map"};g.commit_strike(event)
 check(p.hp==50 and event.reflection_damage==2,"MAP body contact reflects once even at zero damage")
 # Actual MAP confirms one event per target, rather than one per affected tile.
 a=arrange(g);p=a[0];t=a[1];p.hero_profession="";p.erase("weapon_index");p.map_uses=0
 var preview=g.MapSkills.preview(g,p.id,g.pos(t),Vector2i.RIGHT)
 check(preview.valid,"Actual hero MAP can target Titan body")
 if preview.valid:
  var hp=int(p.hp);var receipt=g.MapSkills.apply(g,p.id,g.pos(t),Vector2i.RIGHT)
  var hit=receipt.targets.filter(func(h):return h.id==t.id)
  check(hit.size()==1 and int(hit[0].reflection_damage)==2,"One MAP release contacts Titan once")
  check(p.hp==hp-int(receipt.cost)-2 and receipt.hp_after==p.hp,"MAP cost and reflection both settle and display correctly")
  check(M.part_hp(t)==16,"MAP body damage leaves independent core unchanged")
 # Shared experience cap and order, including an ordinary value over100 before x1.5.
 var novice={"class_id":14,"level":1,"hp":20}
 var ordinary={"class_id":6,"exp_value":110,"max_hp":42}
 var mechanical=t.duplicate(true);mechanical.exp_value=110
 check(Rules.experience_gain(novice,ordinary,42,0,true)==110,"Ordinary enemy reward can exceed old100")
 check(Rules.experience_gain(novice,mechanical,42,0,true)==165,"Uncapped110 ×1.5 =165 before final cap")
 ordinary.exp_value=255;mechanical.exp_value=255
 check(Rules.experience_gain(novice,ordinary,42,0,true)==180 and Rules.experience_gain(novice,mechanical,42,0,true)==180,"Global enemy combat cap180")
 check(Rules.experience_gain(novice,mechanical,42,28,false)==65,"Damage XP uses uncapped value, rounds then multiplies")
 check(Rules.victory_experience_gain(novice)==20,"Fixed clear reward formula preserved")
 g=fresh();p=g.find_unit("eileen");p.level=3;p.exp=80
 var train=int(p.get("magic_level",0));var rng=int(g.rng_state)
 var mirror=State.new();mirror.rng_state=rng
 for i in range(12):mirror.random_bounded(99)
 reward=XP.award(g,p,180)
 check(p.level==5 and p.exp==60 and reward.levels_gained==2 and reward.level_steps.size()==2,"EXP80+180 yields two levels, remainder60")
 check(g.rng_state==mirror.rng_state and int(p.magic_level)==train+2,"Every level rolls six growths and checks spell learning")
 check(g.save_game(),"Continuous-level state saves")
 restored=State.new();restored.save_path=g.save_path
 check(restored.load_game() and restored.find_unit(p.id).exp==60 and restored.find_unit(p.id).level==5,"Save/reload preserves both levels and exact remainder")
 p.exp=99;p.level=3;reward=XP.award(g,p,180)
 check(p.level==5 and p.exp==79,"EXP99+180 preserves79 remainder")
 p.exp=99;p.level=19;reward=XP.award(g,p,180)
 check(p.level==20 and p.exp==99 and reward.levels_gained==1,"Level20 cap prevents extra growth or invalid EXP bank")
 g=fresh();a=arrange(g);p=a[0];t=a[1];t.parts.protective_core.hp=0;t.hp=1;p.level=1;p.exp=80;p.strength=40
 plan=g.plan_combat(p.id,t.id)
 for hit in plan.events:g.commit_strike(hit)
 reward=g.finish_exchange(plan)
 check(reward.gain==119 and p.level==2 and p.exp==99,"Actual kill settlement applies V98×friendly coefficient then1.5, above old100")
 g=fresh();t=g.find_unit("F25_pseudo_titan_1")
 for u in g.units:
  if u.side=="enemy" and not M.is_puppet(u):u.hp=0
 M.refresh(g);check(t.move==7 and t.mechanical_retreating,"Only mechanical side gets4+3 movement")
 M.refresh(g);check(t.move==7,"Repeated refresh does not stack retreat bonus")
 check(g.movement_cost(t,Vector2i(0,0))==255,"Titan does not acquire water walking")
 var move=g.ai_action(t)
 check(move.target=="" and str(move.reason)=="mechanical_escape","Retreat action abandons attacks")
 var path=g.path_to(t,move.destination)
 check(path.size()>1 and path.all(func(cell):return g.movement_cost(t,cell)<255),"Retreat follows legal traversable cells")
 t.position=[move.destination.x,move.destination.y];t.acted=false;M.part(t).hp=0
 move=g.ai_action(t);t.position=[move.destination.x,move.destination.y];M.refresh(g)
 check(t.get("escaped",false) and t.hidden and t.hp==42 and g.kills==0,"Broken Titan reaches nearest edge, disappears without kill")
 check(not g.flags.get("inventory_processed_deaths",{}).has(t.id),"Escape issues no loot")
 g=fresh();t=g.find_unit("F25_pseudo_titan_1")
 for u in g.units:
  if u.side=="enemy" and not M.is_puppet(u):u.hp=0
 M.refresh(g);g.find_unit("F25_boss").hp=1;M.refresh(g)
 check(t.move==4 and not t.mechanical_retreating,"Living nonmechanical ally cancels retreat")
 g.find_unit("F25_boss").hp=0;g.flags.quest.objects.myth_box=true;g.flags.quest.objects.pilot_prison=true
 check(g.check_outcome()=="victory" and int(t.hp)>0,"Original F25 boss, box and prison goals win without chasing Titan")
 for key in ["intact","broken"]:
  var actor=t.duplicate(true);actor.parts.protective_core.hp=16 if key=="intact" else 0
  var art=Art.data(actor);var map=Art.map_sprite("map_idle",actor)
  check(map.native_cycle.map(func(v):return int(v))==[0,1,2,1] and map.cycle_ticks.map(func(v):return int(v))==[14,8,14,8],key+" map idle matches enemy spearman cadence")
  check(Art.battle(actor).frame_size.map(func(v):return int(v))==[96,88] and map.native_density==2,key+" approved coarse-pixel density")
  check(art.variants["melee" if key=="intact" else "broken-melee"].frames.size()==246,key+" full approach, contact and return motion")
 check(load("res://scenes/main.tscn")!=null,"Actual game controller and art pipelines parse")
 var out=FileAccess.open(OUT+"logic-checks.json",FileAccess.WRITE);out.store_string(JSON.stringify({"checks":checks.size(),"passed":errors.is_empty(),"errors":errors,"labels":checks},"\t"));out.close()
 print("PSEUDO_TITAN ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
