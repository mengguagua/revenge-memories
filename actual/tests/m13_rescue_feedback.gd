extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/M13-rescue-20261028/"
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append({"passed":ok,"label":label})
 if not ok:errors.append(label);push_error(label)
func fresh():
 var g=State.new();g.new_game();g.world_node=4;g.save_path="/private/tmp/M13-rescue-domain.json"
 check(g.start_battle(103),"fresh M13 starts");return g
func open_door(g,id:String):
 var door=g.battle_data.objects.filter(func(o):return str(o.id)==id)[0]
 var actor=g.find_unit("hunapu");actor.position=[door.position[0],int(door.position[1])+1];actor.acted=false
 check(g.select_unit("hunapu") and g.interact(id),"normal door interaction: "+id)
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
 var g=fresh();var lena=g.find_unit("lena");var before=State.pos(lena)
 check(lena.locked and g.ai_action(lena).destination==before,"captive Lena stays in closed prison")
 open_door(g,"M13_door_0")
 check(not lena.locked and lena.quest_kind=="escort" and not lena.controllable and not g.party.has("lena"),"opening west cell releases automatic escort; recruitment remains post-battle")
 # Isolate a cleared corridor to distinguish a stale witness state from safe-AI waiting.
 for u in g.units:
  if u.side=="enemy":u.hp=0
 var action=g.ai_action(lena)
 check(action.destination!=before,"released Lena plans real movement along a safe corridor")
 var path=g.path_to(lena,action.destination)
 check(not path.is_empty(),"released Lena movement uses a valid ordinary path")
 lena.position=[action.destination.x,action.destination.y];g.mark_wait("lena")
 check(State.pos(lena)!=before and lena.acted,"automatic escort can commit a normal turn action")
 # A genuine pre-fix save had the cell open but kept quest_kind=witness.
 lena.quest_kind="witness";lena.hp=13;lena.acted=false
 var position=State.pos(lena);var turn=g.turn;var rng=g.rng_state
 g.battle_start_snapshot.units.filter(func(u):return str(u.id)=="lena")[0].quest_kind="witness"
 check(g.save_game(),"open-cell legacy witness fixture saves")
 var read=State.new();read.save_path=g.save_path;check(read.load_game(),"open-cell save migrates")
 lena=read.find_unit("lena")
 check(lena.quest_kind=="escort" and not lena.locked and lena.hp==13 and State.pos(lena)==position and read.turn==turn and read.rng_state==rng,"load repairs role without resetting HP/position/turn/RNG")
 var saved=JSON.stringify(read.units);check(read.save_game() and read.load_game() and JSON.parse_string(JSON.stringify(read.units))==JSON.parse_string(saved),"second load is stable")
 check(read.battle_start_snapshot.units.filter(func(u):return str(u.id)=="lena")[0].locked,"load keeps retry snapshot captive locked")
 check(read.retry_battle() and read.find_unit("lena").locked and read.find_unit("lena").quest_kind=="escort","retry restores closed prison with corrected role")
 g=fresh();g.find_unit("lena").hp=0;g.story_on_death(g.find_unit("lena"));open_door(g,"M13_door_0");open_door(g,"M13_door_1");g.find_unit("M13_boss").hp=0
 check(g.check_outcome()=="victory" and g.find_unit("lena").hp==0 and g.roster.lena.dead,"Lena casualty does not block victory or resurrect her")
 g=fresh()
 for u in g.units:
  if str(u.id).begins_with("M13_workers"):u.hp=0
 open_door(g,"M13_door_0");open_door(g,"M13_door_1");g.find_unit("M13_boss").hp=0
 check(g.check_outcome()=="defeat","Lena escort does not replace mandatory surviving laborers")
 g=fresh();g.turn=5
 # Old-map compatibility may retain old reinforcement templates; spawn also migrates them.
 for u in g.battle_data.reinforcements:u.level=1;u.strength=8
 g.next_phase()
 for id in ["M13_r0","M13_r1"]:
  var u=g.find_unit(id);check(not u.is_empty() and u.level==3 and u.strength==9,"scheduled reinforcement uses level3 strength9: "+id)
  u.enemy_balance_revision=7;u.level=1;u.strength=8;u.hp=7;u.acted=true
  g.EnemyBalance.prepare(103,[u]);check(u.level==3 and u.strength==9 and u.hp==7 and u.acted,"already-spawned reinforcement migrates without resetting action/HP: "+id)
 var f=FileAccess.open(OUT+"domain-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"fixture_scope":"Isolated release/save/retry/casualty/spawn boundaries; not a full playthrough.","iphone_updated":false},"  "));f.close()
 print("M13_RESCUE ",checks.size()," errors=",JSON.stringify(errors));quit(0 if errors.is_empty() else 1)
