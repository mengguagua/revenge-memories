extends SceneTree
const State=preload("res://core/game_state.gd")
const P=preload("res://core/phantom_rules.gd")
const SOURCE="res://reports/chapter2/play/natural-F22-deployment-save.json"
var failures=[]
var checks=[]
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:failures.append(label);push_error(label)
func fresh(training:int=0):
 var g=State.new();g.save_path=SOURCE;assert(g.load_game());g.save_path="/private/tmp/phantom-rules-20261113.json";assert(g.retry_battle())
 g.flags.phantom_training={"mireille":training};g.flags.phantom_maps={}
 g.battle_start_snapshot.flags.phantom_training={"mireille":training};g.battle_start_snapshot.flags.phantom_maps={}
 var c=g.find_unit("mireille");c.magic_flags=int(c.magic_flags)|32;c.hp=c.max_hp;c.acted=false
 return g
func cast(g):return g.use_support("mireille",45)
func _initialize():
 var source_hash=FileAccess.get_sha256(SOURCE)
 for progress in [0,5,6,11,12]:
  var g=fresh(progress);var c=g.find_unit("mireille");var before=c.hp;var level=P.rank(g,c);var result=cast(g)
  check(result.get("spawned",[]).size()==level*2,"fixed count at skill progress "+str(progress))
  var units=result.spawned.map(func(id):return g.find_unit(id));var classes=units.map(func(u):return int(u.class_id))
  var unique=[]
  for cid in classes:if not unique.has(cid):unique.append(cid)
  check(unique.size()==classes.size(),"distinct professions when ordinary ground available "+str(progress))
  check(c.hp==before-10 and c.acted,"one10HP action cost "+str(progress))
  check(units.all(func(u):return u.level==1 and u.exp==0 and u.acted and not u.has("player_slot") and P.valid_unit(g,u)),"newborns level1 fixed minima and independent slots "+str(progress))
  if level>1:check(classes.any(func(cid):return (P.FINAL if level==3 else P.ADVANCED).has(cid)),"promoted guarantee "+str(progress))
  if level==1:check(classes.all(func(cid):return P.BASIC.has(cid)),"rank1 basic jobs only")
  var snapshot=JSON.stringify([g.units,g.flags,g.rng_state])
  c.acted=false
  var second_snapshot=JSON.stringify([g.units,g.flags,g.rng_state])
  check(cast(g).is_empty() and second_snapshot==JSON.stringify([g.units,g.flags,g.rng_state]),"shared map lock is an atomic rejection "+str(progress))
  c.acted=true
  if progress==5:check(P.rank(g,c)==2 and units.size()==2,"sixth cast unlocks rank2 for next map")
  if progress==11:check(P.rank(g,c)==3 and units.size()==4,"twelfth cast unlocks rank3 for next map")
  check(g.save_game(),"save with summoned formation "+str(progress))
  var restored=State.new();restored.save_path=g.save_path
  check(restored.load_game(),"reload summoned formation "+str(progress))
  check(P.rank(restored,restored.find_unit("mireille"))==P.rank(g,c) and not P.reason(restored,restored.find_unit("mireille")).is_empty(),"reload retains skill and shared budget "+str(progress))
  check(g.retry_battle() and P.uses(g,g.find_unit("mireille"))==progress and not g.flags.get("phantom_maps",{}).has("202") and g.units.all(func(u):return not P.is_phantom(u)),"retry restores full pre-cast state")
 var g=fresh(12);var c=g.find_unit("mireille")
 c.hp=10;var unchanged=JSON.stringify([g.units,g.flags,g.rng_state]);check(cast(g).is_empty() and unchanged==JSON.stringify([g.units,g.flags,g.rng_state]),"cannot spend final HP")
 g=fresh(12);c=g.find_unit("mireille")
 # Fill the twenty normal slots with isolated allied NPC fixtures far from caster.
 var normal=g.units.filter(func(u):return u.side=="player").size();var cell_candidates=[]
 for y in range(g.battle_data.map.height):
  for x in range(g.battle_data.map.width):
   var at=Vector2i(x,y)
   if absi(x-g.pos(c).x)+absi(y-g.pos(c).y)>6 and g.unit_at(at).is_empty() and g.movement_cost(c,at)<255:cell_candidates.append(at)
 var n=0
 while normal<20:
  var ally=c.duplicate(true);ally.id="capacity_fixture_"+str(n);ally.neutral=true;ally.controllable=false;ally.player_slot=normal;ally.position=[cell_candidates[n].x,cell_candidates[n].y]
  g.units.append(ally);normal+=1;n+=1
 var six=cast(g)
 check(six.spawned.size()==6 and g.living("player").size()==26,"twenty normal allies do not reduce six phantoms")
 check(g.save_game(),"save26friendly formation")
 var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game() and loaded.living("player").size()==26,"reload26friendly formation")
 var broken=State.read_json(g.save_path);broken.units.filter(func(u):return P.is_phantom(u))[0].exp=1
 check(not g.SaveValidation.campaign_valid(g,broken,g.SAVE_FIELDS),"reject phantom EXP/growth in checkpoint")
 # Whole local ring blocked: no HP, action, RNG or skill consumption.
 g=fresh(0);c=g.find_unit("mireille")
 for offset in g.Items.summon_offsets():
  var cell=g.pos(c)+Vector2i(offset[1],offset[0])
  if not g.in_bounds(cell) or not g.unit_at(cell).is_empty():continue
  var block=c.duplicate(true);block.id="block_"+str(g.units.size());block.position=[cell.x,cell.y];g.units.append(block)
 unchanged=JSON.stringify([g.units,g.flags,g.rng_state]);check(cast(g).is_empty() and unchanged==JSON.stringify([g.units,g.flags,g.rng_state]),"no legal cells costs nothing")
 # A single remaining legal cell yields one real body, rather than a failed full-count roll.
 for block in g.units.duplicate():
  if str(block.id).begins_with("block_") and g.movement_cost(c,g.pos(block))<255:
   g.units.erase(block);break
 var partial=cast(g);check(partial.get("spawned",[]).size()==1 and c.hp==int(c.max_hp)-10,"partial local space yields one body and one cost")
 g=fresh(5);c=g.find_unit("mireille");g.Rewind.reset(g);cast(g);g.next_phase();g.next_phase()
 check(g.Rewind.commit(g) and P.uses(g,g.find_unit("mireille"))==5 and not g.flags.phantom_maps.has("202") and g.units.all(func(u):return not P.is_phantom(u)),"rewind restores HP, bodies, skill and shared map budget together")
 g=fresh(0);c=g.find_unit("mireille")
 # Native spell effect and body minima remain runtime-derived.
 check(g.Items.cost(45)==10,"spell menu and real cost share10HP")
 var falcon=P.body(g,c,5);check(falcon.max_hp==40 and falcon.strength==15 and falcon.skill==1 and falcon.speed==5 and falcon.defence==12 and falcon.move==8 and falcon.resistance==0,"falcon uses player minima and zero personal resistance")
 check(P.body(g,c,10).resistance==15,"swordmaster keeps player class resistance bonus")
 # Real exchange awards the summoner, never the disposable actor, exactly once.
 g=fresh(0);c=g.find_unit("mireille");var bow=g.find_unit("F22_e8");var phantom=P.body(g,c,6);phantom.id="reward_fixture";phantom.phantom_slot=0
 for offset in g.DIRECTIONS:
  var at=g.pos(bow)+offset
  if g.in_bounds(at) and g.unit_at(at).is_empty() and g.movement_cost(phantom,at)<255:phantom.position=[at.x,at.y];break
 phantom.acted=false;g.units.append(phantom);g.rng_state=182
 var ex=g.plan_combat(phantom.id,bow.id)
 for e in ex.events:g.commit_strike(e)
 var xp=c.exp;var reward=g.finish_exchange(ex)
 check(reward.get("unit","")==c.id and int(c.exp)>int(xp) and phantom.exp==0,"phantom combat EXP reaches owner")
 var awarded=c.exp;g.finish_exchange(ex);check(c.exp==awarded,"exchange cannot award twice")
 var other=P.body(g,g.find_unit("lisa"),3);other.id="other_owner";other.position=[1,1];other.phantom_slot=1;g.units.append(other)
 c.hp=0;g.Summons.cleanup(g,c)
 check(phantom.hp==0 and other.hp>0,"owner collapse clears only own mixed professions")
 # Both armies remain eligible during joint deployment, even when party is the other route.
 var joint=State.new();joint.save_path="res://reports/chapter5-spatial-20261022/play/continuous-final/continuous-final-J53-deployment.json"
 check(joint.load_game(),"authentic joint-army checkpoint loads")
 joint.save_path="/private/tmp/phantom-joint-20261113.json";check(joint.retry_battle(),"joint map reenters current geometry")
 var east=joint.find_unit("mireille")
 check(P.formal(joint,east) and P.reason(joint,east).is_empty(),"east summoner remains eligible in joint army")
 var joint_cast=joint.use_support("mireille",45)
 check(joint_cast.get("spawned",[]).size()==2 and joint.save_game(),"joint army cast and save succeeds")
 check(FileAccess.get_sha256(SOURCE)==source_hash,"original fixture unchanged")
 var out=FileAccess.open("res://reports/phantom-20261113/rules.json",FileAccess.WRITE);out.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"scope":"Isolated rule/save fixtures, not campaign completion"},"  "));out.close()
 print("PHANTOM_RULES ",checks.size()," checks failures=",failures)
 quit(0 if failures.is_empty() else 1)
