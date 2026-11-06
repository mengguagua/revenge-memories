extends SceneTree
class CountingState extends "res://core/game_state.gd":
 var evaluations=0
 func _safe_escort_move(unit:Dictionary,target:Vector2i)->Dictionary:
  evaluations+=1
  return super._safe_escort_move(unit,target)
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label)
func run():
 var g=CountingState.new();g.save_path="res://reports/full-assessment-20261025/campaign-final-r3/ch1/chain-S12-deployment.json"
 check(g.load_game(),"real S12 deployment loads")
 g.save_path="/private/tmp/revenge-escort-hint-unused.json"
 var unit=g.find_unit("medicine_wagon");var rng=g.rng_state;var before=g.units.duplicate(true)
 var text=g.escort_hint(unit);var count=g.evaluations
 for i in range(60):check(g.escort_hint(unit)==text,"unchanged tooltip text frame "+str(i))
 check(g.evaluations==count,"sixty redraw requests reuse one threat/path evaluation")
 check(g.units==before and g.rng_state==rng,"tooltip prediction changes no units or RNG")
 var enemy=g.living("enemy")[0]
 enemy.hp-=1;g.escort_hint(unit);check(g.evaluations==count+1,"enemy damage invalidates cache");count=g.evaluations
 enemy.position[0]+=1;g.escort_hint(unit);check(g.evaluations==count+1,"enemy movement invalidates cache");count=g.evaluations
 enemy.hp=0;g.escort_hint(unit);check(g.evaluations==count+1,"enemy death invalidates cache");count=g.evaluations
 unit.position[0]+=1;g.escort_hint(unit);check(g.evaluations==count+1,"escort movement invalidates cache");count=g.evaluations
 g.battle_data.targets[0][0]+=1;g.escort_hint(unit);check(g.evaluations==count+1,"delivery target invalidates cache");count=g.evaluations
 g.flags.quest.objects.hint_probe=true;g.escort_hint(unit);check(g.evaluations==count+1,"objective change invalidates cache");count=g.evaluations
 g.battle_data.map.tiles[0]=218;g.escort_hint(unit);check(g.evaluations==count+1,"terrain change invalidates cache")
 var f=FileAccess.open("res://reports/full-assessment-20261025/ai/hint-cache-checks.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"fixture":true,"scope":"Readonly tooltip repetition and controlled state mutations on a copied real S12 deployment. Does not persist fixture changes."},"  "));f.close()
 print("ASSESSMENT_ESCORT_HINT ",checks.size()," errors=",errors);quit(0 if errors.is_empty() else 1)
