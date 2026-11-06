extends SceneTree
const State=preload("res://core/game_state.gd")
var checks=[]
var failures=[]
const OUT="res://reports/full-assessment-20261025/story/"
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append({"label":label,"passed":ok})
 if not ok:failures.append(label);push_error(label)
func fixture(code:String):
 var source="res://reports/campaign/natural-M15-deployment-save.json" if code=="M15" else State.read_json("res://reports/chapter3-environment-20261023/sources.json")[code]
 var g=State.new();g.save_path=source
 check(g.load_game(),code+" historical copy loads")
 g.save_path=OUT+"fixture.json"
 g.battle_data=g.stages[g.stage_id].duplicate(true)
 g.battle_outcome="";g.find_unit(g.battle_data.boss_id).hp=0
 return g
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
 var g=fixture("M15")
 check(g.check_outcome()=="","M15 boss defeated alone is insufficient")
 var workers=g.units.filter(func(u):return str(u.id).begins_with("M15_workers"))
 workers[0].locked=false
 check(g.check_outcome()=="victory","M15 one living released worker group meets stated minimum")
 g=fixture("M15")
 for u in g.units:
  if str(u.id).begins_with("M15_workers"):u.hp=0
 check(g.check_outcome()=="defeat","M15 both worker groups lost is defeat")
 g=fixture("F31");g.flags.quest.objects={"ship_lock":true,"mooring":true}
 g.flags.quest.evacuated=["dock_patients0"]
 check(g.check_outcome()=="","F31 cannot abandon a living unreturned group")
 g.find_unit("dock_patients1").hp=0
 check(g.check_outcome()=="victory","F31 all survivors returned permits one lost group")
 g=fixture("F31")
 g.find_unit("dock_patients0").hp=0;g.find_unit("dock_patients1").hp=0
 check(g.check_outcome()=="defeat","F31 no survivors is defeat")
 g=fixture("F32");g.flags.quest.objects.guide_notes=true
 check(g.check_outcome()=="","F32 route notes do not skip escorting a living guide")
 g.find_unit("salt_guide").hp=0
 check(g.check_outcome()=="victory","F32 lost guide plus recovered notes allows continuation")
 g=fixture("F32");g.find_unit("salt_guide").hp=0
 check(g.check_outcome()=="","F32 lost guide without notes cannot win")
 var f=FileAccess.open(OUT+"objective-checks.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"scope":"Isolated rule fixtures, not playthroughs; source checkpoints never saved."},"  "));f.close()
 print("OBJECTIVE_ASSESSMENT ",checks.size()," ",JSON.stringify(failures));quit(0 if failures.is_empty() else 1)
