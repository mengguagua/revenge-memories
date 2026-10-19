extends SceneTree
const State=preload("res://core/game_state.gd")
const Tactics=preload("res://core/refugee_tactics.gd")
const Panels=preload("res://core/battle_panel_layout.gd")
class ObservedMain extends "res://core/main.gd":
 var attacks:Array=[]
 func _play_combat(a:String,b:String)->void:
  attacks.append([a,b]);await super._play_combat(a,b)
var checks=0
var errors=[]
var details={}
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks+=1
 if not ok:errors.append(label);push_error(label)
func fresh():
 var g=State.new();g.new_game();g.world_node=2;g.save_path="/private/tmp/playtest-fixes-independent.json";g.start_battle(101);g.story_events.clear();return g
func isolated():
 var g=fresh();var u=g.find_unit("M11_refugees0");var e=g.find_unit("M11_e1")
 e.position=[9,10];e.move=2;e.behavior="guard_exit"
 g.units=[u,e];return g
func crowded():
 var g=isolated();var e=g.find_unit("M11_e1")
 e.move=6;e.erase("behavior")
 for point in [[8,10],[10,11]]:
  var other=e.duplicate(true);other.id="crowd"+str(point);other.position=point;g.units.append(other)
 return g
func run():
 check(ProjectSettings.get_setting("application/config/version")=="0.8.12","0.8.12 version")
 for width in [256,384,426,560]:
  var canvas=Rect2(-(width-256)/2.0,0,width,240)
  for x in range(8,width-8,32):
   for y in [16,64,112,128,176,224]:
    var placement=Panels.forecast(canvas.position+Vector2(x,y),canvas)
    check(placement.valid and canvas.grow(-8).encloses(placement.panel) and not placement.panel.intersects(placement.focus),"forecast clears target and arrow %s/%s/%s"%[width,x,y])
 var g=isolated();var u=g.find_unit("M11_refugees0");var before=g.units.duplicate(true);var rng=g.rng_state
 var action=g.ai_action(u)
 check(not str(action.target).is_empty(),"healthy escort still initiates a safe attack")
 check(g.units==before and g.rng_state==rng,"risk evaluation changes no real positions, stats or RNG")
 check(g.reachable(u).costs.has(action.destination) and g.can_stop(u,action.destination),"safe attack uses a legal reachable landing tile")
 check(int(action.risk.hp_reserve)>=9,"safe attack keeps the promised HP reserve")
 details.safe_action=action
 u.hp=14;action=g.ai_action(u)
 check(str(action.get("target","")).is_empty(),"escort below 60 percent HP does not initiate")
 u.hp=15;action=g.ai_action(u)
 check(not str(action.get("target","")).is_empty(),"healthy threshold does not disable all attacks")
 g=isolated();u=g.find_unit("M11_refugees0");var enemy=g.find_unit("M11_e1")
 enemy.strength=25;enemy.speed=20
 check(str(g.ai_action(u).get("target","")).is_empty(),"lethal counter and follow-up prevent the attack")
 g=crowded();u=g.find_unit("M11_refugees0")
 check(str(g.ai_action(u).get("target","")).is_empty(),"three approaching enemies prevent a surrounded attack")
 details.crowd_risk=Tactics.evaluate(g,u,Vector2i(9,11))
 check(int(details.crowd_risk.threats)>=3,"threats include enemies that can move before attacking")
 g=isolated();u=g.find_unit("M11_refugees0");enemy=g.find_unit("M11_e1")
 enemy.class_id=12;enemy.weapon_index=1;enemy.position=[11,11];enemy.strength=30
 var risk=Tactics.evaluate(g,u,Vector2i(9,11))
 check(int(risk.threats)==1 and int(risk.incoming)>0,"stationary archer's ranged threat is counted")
 check(str(g.ai_action(u).get("target","")).is_empty(),"dangerous ranged coverage prevents an advance")
 enemy.position=[19,1];risk=Tactics.evaluate(g,u,Vector2i(9,11))
 check(int(risk.threats)==0,"distant enemies outside their move and weapon range are excluded")
 g=isolated();u=g.find_unit("M11_refugees0");u.locked=true
 check(str(g.ai_action(u).get("target","")).is_empty(),"locked escort stays passive")
 u.locked=false
 check(str(g.ai_action(u,true).get("target","")).is_empty(),"gather mode keeps its existing routing")
 u.id="other-escort"
 check(str(g.ai_action(u).get("target","")).is_empty(),"other escort IDs keep their existing rules")
 u.id="M11_refugees0";g.stage_id=111
 check(str(g.ai_action(u).get("target","")).is_empty(),"other stages keep their existing rules")
 g=fresh()
 for e in g.living("enemy"):e.hp=0
 u=g.find_unit("M11_refugees0")
 check(str(g.ai_action(u).get("target","")).is_empty() and g.ai_action(u).destination!=g.pos(u),"clear route still advances to evacuation")
 u.position=g.battle_data.exit.duplicate();g.mark_wait(str(u.id))
 check(g.flags.quest.evacuated.has(u.id),"arrival still records evacuation")
 g=fresh();g.find_unit("M11_refugees0").hp=0
 check(g.check_outcome()=="defeat","refugee death still fails the escort goal")
 var ui=load("res://scenes/main.tscn").instantiate();ui.set_script(ObservedMain);root.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false);ui.game=isolated();ui.view="battle";ui.ui_mode="inspect";ui.instant_mode=true;ui.busy=true;ui.batch_running=true
 await ui._run_ai_unit(ui.game.find_unit("M11_refugees0"))
 check(ui.attacks.size()==1,"real automatic unit controller executes a safe attack")
 ui.game=crowded();ui.attacks.clear();ui.busy=true;ui.batch_running=true
 await ui._run_ai_unit(ui.game.find_unit("M11_refugees0"))
 check(ui.attacks.is_empty() and ui.game.find_unit("M11_refugees0").acted,"real automatic unit controller safely waits in the dangerous case")
 ui.game=fresh()
 for cid in [6,8,12]:
  for side in ["enemy","player"]:
   var actor=ui.game.find_unit("hunapu").duplicate(true);actor.class_id=cid;actor.side=side;actor.acted=false
   var active=ui._map_unit_sprite(actor);actor.acted=true
   var resting=ui._map_unit_sprite(actor)
   var image=ui._tex(resting.path).get_image();image.convert(Image.FORMAT_RGBA8)
   var source=ui._tex(active.path).get_image();source.convert(Image.FORMAT_RGBA8)
   var warm=true;var alpha=true
   for y in range(image.get_height()):
    for x in range(image.get_width()):
     var c=image.get_pixel(x,y);alpha=alpha and is_equal_approx(c.a,source.get_pixel(x,y).a)
     if c.a>0:warm=warm and c.r>c.g and c.r>c.b
   check(alpha,"resting palette preserves alpha "+str(cid)+side)
   check(warm if side=="enemy" else not warm,"enemy resting red and allied resting grey "+str(cid)+side)
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"details":details,"version":ProjectSettings.get_setting("application/config/version"),"scope":"Targeted forecast-placement grid, actual resting textures, M11 safe/risky decisions and real automatic unit controller; fixtures, independent saves"}
 var f=FileAccess.open(OS.get_environment("PLAYTEST_FIX_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("PLAYTEST_FIXES ",JSON.stringify(report));ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
