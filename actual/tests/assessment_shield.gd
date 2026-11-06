extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")
const Compare=preload("res://core/equipment_comparison.gd")
var checks=[]
var errors=[]
var rows=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label)
func run():
 var g=State.new();g.save_path="res://reports/full-assessment-20261025/ai/shield-corrected/shield-J54-field.json"
 check(g.load_game(),"old thirteen-defence build's legitimately exchanged shield save loads")
 g.save_path="/private/tmp/revenge-shield-current-effects.json"
 var holder=g.find_unit("eileen");var untouched=holder.duplicate(true)
 check(int(holder.item_id)==53,"old save retains shield ownership")
 check(Items.physical_defence_bonus(holder)==5 and Items.magic_defence(holder)==int(holder.resistance)+5,"old held-item save uses current campaign bonuses")
 check(Compare.description(holder).contains("增加5物防与5魔防"),"equipment explanation derives both current bonuses from metadata")
 for i in range(3):Compare.stats(holder)
 check(holder==untouched,"repeated stat display never writes the bonus into permanent attributes")
 check(g.save_game(),"shield-bearing old progress can be saved without a base-attribute migration")
 var reloaded=State.new();reloaded.save_path=g.save_path;check(reloaded.load_game(),"updated shield progress reloads")
 check(reloaded.find_unit("eileen").defence==holder.defence and reloaded.find_unit("eileen").resistance==holder.resistance,"save round trip preserves permanent physical and magical defence")
 for id in ["eileen","lord","noya"]:
  var base=g.roster[id].duplicate(true);var base_copy=base.duplicate(true)
  for item_id in [0,49,50,53]:
   var u=base.duplicate(true);u.item_id=item_id;u.erase("weapon_index")
   var entry={"unit":id,"class_id":u.class_id,"item":item_id,"base_defence":u.defence,"base_resistance":u.resistance,"effective_defence":int(u.defence)+Items.physical_defence_bonus(u),"effective_resistance":Items.magic_defence(u),"matchups":[]}
   for phase in [1,2]:
    var boss=g.stages[534].enemies.filter(func(e):return e.id=="J54_boss")[0].duplicate(true)
    if phase==2:boss.strength=int(boss.strength)+3
    for distance in [1,2]:
     var attack=Rules.default_counter(boss,1) if distance==1 else Rules.attack_context(boss,2)
     var stats=Rules.attack_stats(attack,u,0)
     entry.matchups.append({"phase":phase,"distance":distance,"weapon":Rules.weapon_index(attack),"damage_per_hit":stats.damage,"hit":stats.hit})
   rows.append(entry)
   if item_id==53:
    check(entry.effective_defence==int(base.defence)+5 and entry.effective_resistance==int(base.resistance)+5,id+" receives exactly five to both defences")
    var wounded=u.duplicate(true);wounded.hp=maxi(1,int(wounded.max_hp)-10)
    check(Items.phase_effect(wounded,0).heal==5,id+" retains five-point phase recovery")
  check(base==base_copy,id+" formula comparisons leave the source attributes unchanged")
 # Body threat forecasts must choose the same physical/magic profile as combat.
 var beast=g.stages[412].enemies.filter(func(e):return e.id=="S42_e1")[0]
 var celine=g.characters.celine
 var adjacent=Rules.attack_context(beast,1)
 check(Rules.weapon_index(adjacent)==1003 and Rules.attack_stats(adjacent,celine,0).damage==9,"bone-wing melee threat is nine physical damage to Celine, not default breath magic")
 g.stage_id=412;g.battle_data=g.stages[412].duplicate(true);g.turn=3
 var fixed_beast=beast.duplicate(true);fixed_beast.position=[20,17];fixed_beast.move=0;fixed_beast.acted=false
 var subject=celine.duplicate(true);subject.position=[20,18];subject.side="player";subject.hp=subject.max_hp;subject.acted=false
 g.units=[fixed_beast,subject]
 check(g.RefugeeTactics.evaluate(g,subject,g.pos(subject)).incoming==9,"actual threat evaluator uses the physical profile at adjacent distance")
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"comparisons":rows,"scope":"Current campaign metadata, real old shield-bearing save round trip, and hypothetical held-item comparisons for genuine roster attributes. Per-hit formula analysis is not a separate playthrough."}
 var f=FileAccess.open("res://reports/full-assessment-20261025/ai/shield-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("ASSESSMENT_SHIELD ",checks.size()," errors=",errors);quit(0 if errors.is_empty() else 1)
