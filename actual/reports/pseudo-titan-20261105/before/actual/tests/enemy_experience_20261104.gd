extends SceneTree
const State=preload("res://core/game_state.gd")
const EnemyXP=preload("res://core/enemy_experience.gd")
const Rules=preload("res://core/combat_rules.gd")
const FIXTURE="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F21-deployment.json"
const OUT="res://reports/enemy-experience-20261104/"
const CACHE="/private/tmp/enemy-experience-20261104/"
const BASES={1:40,2:60,3:50,4:60,5:60,6:35,7:70,8:35,9:55,10:75,11:30,12:35,13:55,14:35,15:50,16:60,17:50,18:60,19:75,20:75,21:100,22:75,23:75,25:50}
const BOSS_GROUPS={80:["M12","S12","F21"],85:["M11","M13","F22","F23","F24","F26","S22","M31","F31","S31","S32"],90:["M14","S11","F25","S21","M32","F32","M41","M42","M43","M44","F41","F44","S41","S42"],95:["M15","M33","F33","F42","F43","M51","M52","F51","F52","S51","J53"],100:["J54"]}
var checks=[];var errors=[];var ledger=[];var bosses=[];var examples={}
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func same(a,b)->bool:return JSON.stringify(a)==JSON.stringify(b)
func fresh():
 var g=State.new();g.save_path=FIXTURE;check(g.load_game(),"real existing F21 checkpoint loads")
 g.save_path=CACHE+"journal.json";return g
func stripped(u:Dictionary)->Dictionary:
 var result=u.duplicate(true);result.erase("exp_value");return result
func expected_boss(code:String)->int:
 for value in BOSS_GROUPS:
  if BOSS_GROUPS[value].has(code):return value
 return 0
func formulas():
 var data=EnemyXP.data()
 check(data.class_bases.size()==BASES.size(),"exact approved24 defined classes, reserved princess excluded")
 for cid in BASES:check(int(data.class_bases[str(cid)].base)==BASES[cid],"approved class B "+str(cid))
 check(data.bosses.size()==40,"all40 story and side-stage bosses configured")
 for example in [[6,1,35],[6,2,38],[6,3,42],[6,5,49],[15,1,50],[15,3,60],[15,5,70],[3,3,60],[25,3,60],[2,5,84],[7,5,98],[22,5,105],[21,20,255]]:
  check(EnemyXP.value_for(0,{"class_id":example[0],"level":example[1]})==example[2],"independent integer/level/cap example "+str(example))
 check(EnemyXP.value_for(201,{"id":"F21_boss","class_id":6,"level":5})==112,"boss B80 replaces ordinary B35, not additive")
 var u={"id":"F21_e8","side":"enemy","class_id":15,"level":3,"exp_value":35,"hp":7,"acted":true,"position":[10,7]}
 var before=stripped(u);EnemyXP.prepare(201,[u]);check(u.exp_value==60 and same(stripped(u),before),"migration touches only enemy value")
 var once=u.duplicate(true);EnemyXP.prepare(201,[u]);check(same(u,once),"normalization never stacks")
 u.level=5;EnemyXP.prepare(201,[u]);check(u.exp_value==70,"level changes are reflected on next normalization")
 u.class_id=16;EnemyXP.prepare(201,[u]);check(u.exp_value==84,"class changes select their actual approved base")
 var player={"side":"player","id":"eileen","class_id":11,"level":1,"exp_value":0,"exp":28}
 before=player.duplicate(true);EnemyXP.prepare(201,[player]);check(same(player,before),"friendly experience and values remain untouched")
 var novice={"class_id":14,"level":1,"hp":20}
 var mage={"class_id":15,"level":3,"exp_value":60,"max_hp":19,"hp":19}
 check(Rules.experience_gain(novice,mage,19,0,true)==60,"V60 feeds real ordinary kill formula")
 var hero={"id":"eileen","class_id":11,"side":"player","level":1,"hp":20}
 check(Rules.experience_gain(hero,mage,19,0,true)==48,"Eileen coefficient8 retained: arcanist kill48")
 check(Rules.experience_gain(hero,mage,19,9,false)==13,"damage-only receipt uses new full value and actual10/19 damage")
 var puppet={"class_id":25,"unit_kind":"mechanical_puppet","mechanical_model":"water_monkey","level":3,"exp_value":60,"max_hp":22}
 check(Rules.experience_gain(hero,puppet,22,0,true)==72,"water monkey retains1.5 on final48:72")
 mage.exp_value=255;check(Rules.experience_gain(hero,mage,19,0,true)==100,"combat experience cap100 retained")
 check(Rules.victory_experience_gain(hero)==16 and Rules.healing_experience_gain({"id":"mireille","class_id":18,"level":1,"hp":18},8)==10,"clear and healing coefficients unchanged")
 var g=fresh();var actual=g.find_unit("eileen");var target=g.find_unit("F21_e8")
 actual.position=[9,7];actual.strength=40;actual.skill=40;actual.speed=40;actual.acted=false;target.hp=1;g.rng_state=0
 var exchange=g.plan_combat("eileen","F21_e8")
 for event in exchange.events:g.commit_strike(event)
 target.exp_value=999
 check(g.finish_exchange(exchange).gain==48 and target.exp_value==60,"real settlement refreshes stale V before awarding XP")
func all_stages():
 var g=State.new();var counts={};var total=0
 for sid in g.campaign.stages:
  var stage=g.stages[int(sid)];var code=str(stage.code);var before=State.read_json("res://reports/enemy-experience-20261104/before/actual/data/stages/"+code+".json")
  var actors=stage.enemies.duplicate(true)+stage.reinforcements.duplicate(true)
  if stage.has("summon_template"):actors.append(stage.summon_template.duplicate(true))
  var old=before.enemies+before.reinforcements
  if before.has("summon_template"):old.append(before.summon_template)
  check(actors.size()==old.size(),code+" count unchanged")
  for i in range(actors.size()):check(same(stripped(actors[i]),stripped(old[i])),code+" authored identity, position, stats and flags unchanged "+str(actors[i].id))
  g.EnemyBalance.prepare(int(sid),actors)
  var boss_count=0
  for u in actors:
   var is_boss=str(u.id)==str(stage.boss_id);var base=expected_boss(code) if is_boss else int(BASES[int(u.class_id)])
   check(EnemyXP.base_for(int(sid),u)==base,code+" correct profession or boss B "+str(u.id))
   var expected=mini(255,base+floori(float(base*(int(u.level)-1))/10.0))
   check(int(u.exp_value)==expected,code+" live V after balance patches "+str(u.id))
   var row={"stage":code,"stage_name":str(stage.name_zh),"unit":str(u.id),"name":str(u.name_zh),"class_id":int(u.class_id),"level":int(u.level),"base":base,"value":int(u.exp_value),"boss":is_boss}
   ledger.append(row);total+=1;counts[str(u.class_id)]=int(counts.get(str(u.class_id),0))+1
   if is_boss:boss_count+=1;bosses.append(row)
  check(boss_count==1 and expected_boss(code)>=80 and expected_boss(code)<=100,code+" exactly one approved80–100 boss")
  var once=actors.duplicate(true);g.EnemyBalance.prepare(int(sid),actors)
  check(same(actors,once),code+" current stat revision still refreshes V idempotently")
 examples.catalog={"stages":40,"enemies_and_templates":total,"classes":counts}
func migration():
 var original=State.read_json(FIXTURE);var g=fresh()
 for raw in original.units:
  var now=g.find_unit(str(raw.id))
  for field in ["hp","position","acted","exp","level"]:check(same(now.get(field),raw.get(field)),"old live save preserves "+str(raw.id)+" "+field)
 for u in g.units:
  if u.side=="enemy":check(u.exp_value==EnemyXP.value_for(g.stage_id,u),"old live enemy V refreshed "+str(u.id))
 for u in g.battle_start_snapshot.units:
  if u.side=="enemy":check(u.exp_value==EnemyXP.value_for(g.stage_id,u),"old retry enemy V refreshed "+str(u.id))
 var stats=g.units.map(func(u):return {"id":u.id,"hp":u.hp,"exp":u.exp,"level":u.level,"position":u.position,"acted":u.acted})
 check(g.save_game(),"normalized old checkpoint saves")
 var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"normalized checkpoint reloads")
 check(same(stats,loaded.units.map(func(u):return {"id":u.id,"hp":u.hp,"exp":u.exp,"level":u.level,"position":u.position,"acted":u.acted})),"load/save never grants or removes earned XP, level, wound or action")
 loaded.turn=2
 for u in loaded.units:
  if u.side=="player":u.acted=false
 loaded.Rewind.record(loaded)
 for snapshot in loaded.battle_rewind.starts:
  for u in snapshot.units:
   if u.side=="enemy":u.exp_value=1
 loaded.turn=3;loaded.Rewind.record(loaded)
 check(loaded.Rewind.commit(loaded) and loaded.turn==2,"rewind commits a genuine earlier turn")
 check(loaded.find_unit("F21_e8").exp_value==60 and loaded.find_unit("F21_boss").exp_value==112,"rewind refreshes historical cached V with actual class/level")
 check(loaded.retry_battle() and loaded.find_unit("F21_e8").exp_value==60,"retry preserves unified rule")
 examples.migration={"source":FIXTURE,"mage_value":60,"boss_value":112}
func spawns():
 var g=fresh();var caster=g.find_unit("F21_e8")
 var ids=g._summon(caster,17,2,{"source_template_index":3})
 check(not ids.is_empty(),"real ordinary enemy summoning creates units")
 for id in ids:
  var u=g.find_unit(str(id));check(u.exp_value==50 and not u.no_experience,"summoned skeleton uses same B50 at level1")
 ids=g._summon(caster,17,1,{"source_template_index":3,"campaign_minion":true})
 check(not ids.is_empty(),"bounded no-XP summon still spawns")
 if not ids.is_empty():
  var u=g.find_unit(str(ids[0]));check(u.exp_value==50 and u.no_experience and u.no_drop,"bounded summon retains denial flags despite normalized V")
  var hero=g.find_unit("eileen");hero.position=[7,12];hero.strength=40;hero.skill=40;hero.acted=false;hero.speed=40;u.position=[8,12];u.hp=1;g.rng_state=0
  var before=int(hero.exp);var exchange=g.plan_combat(str(hero.id),str(u.id))
  for event in exchange.events:g.commit_strike(event)
  check(g.finish_exchange(exchange).is_empty() and int(hero.exp)==before,"no-XP summoned minion still grants no actual kill XP")
 g=State.new();g.new_game();g.world_node=int(g.stages[103].node);g.save_path=CACHE+"reinforce.json"
 check(g.start_battle(103),"M13 reinforcement fixture starts")
 var expected_ids=g.battle_data.reinforcements.map(func(u):return str(u.id))
 for step in range(12):
  g.story_events.clear();g.next_phase()
  if g.flags.quest.get("reinforced",false):break
 check(g.flags.quest.reinforced,"real phase advance deploys scripted reinforcement wave")
 for id in expected_ids:
  var u=g.find_unit(str(id));check(not u.is_empty() and u.exp_value==EnemyXP.value_for(103,u),"reinforcement receives current profession and level value "+str(id))
 for stage_id in [407,534]:
  g=fresh();g.stage_id=stage_id;g.battle_data=g.stages[stage_id].duplicate(true);g.units=g.battle_data.enemies.duplicate(true);g.chapter=int(g.battle_data.chapter);g.turn=3;g.phase="enemy"
  if stage_id==407:
   g.flags.quest={"objects":{},"summon_wave":false};g.ChapterFour.after_phase(g)
  else:
   g.flags.quest={"objects":{},"final_phase":false,"summon_wave":false};g.find_unit(str(g.battle_data.boss_id)).hp=56;g.ChapterFive.check_outcome(g)
  var added=g.units.filter(func(u):return str(u.id).begins_with("F43_summon") or str(u.id).begins_with("J54_summon"))
  check(added.size()==3,"actual special event creates exactly three units "+str(stage_id))
  for u in added:check(u.exp_value==EnemyXP.value_for(stage_id,u),"event template uses common value "+str(u.id))
func exclusions():
 var g=fresh();var enemy=g.find_unit("F21_e8")
 var training=enemy.duplicate(true);training.training_opponent=true;training.no_experience=true;training.exp_value=0
 EnemyXP.prepare(201,[training]);check(training.exp_value==0 and training.no_experience,"training opponent remains zero-value and no-XP")
 # Original source templates remain separate from campaign experience tuning.
 var legacy=State.read_json("res://data/legacy/rules_full.json")
 check(legacy.promotion_bases["15"].exp_value==80 and legacy.promotion_bases["22"].exp_value==200,"original FE2 bases untouched")
 check(Rules.healing_experience_gain(g._initial_character("mireille"),8)==10,"healing XP unchanged")
 check(g.stages[201].clear_training_exp==35,"F21 fixed clear training35 unchanged")
 var donor=g._initial_character("eileen");var receipt=g.CampaignExperience.award(g,donor,20)
 check(receipt.gain==20 and donor.exp==20,"fixed20 event reward is never scaled by enemy B")
 for sid in g.stages:
  if g.stages[sid].get("training",false):check(g.stages[sid].enemies.all(func(u):return u.exp_value==0 and u.no_experience),"registered training template remains zero XP "+str(sid))
func run():
 DirAccess.make_dir_recursive_absolute(CACHE)
 formulas();all_stages();migration();spawns();exclusions()
 var report={"checks":checks.size(),"errors":errors,"labels":checks,"units":ledger,"bosses":bosses,"examples":examples,"scope":"40 stages and all enemy/reinforcement/event templates; actual combat, old-save migration, retry/rewind, enemy summons and no-XP exclusions. No full campaign simulation or device update."}
 var f=FileAccess.open(OUT+"logic.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("ENEMY_EXPERIENCE ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
