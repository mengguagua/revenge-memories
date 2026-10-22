extends "res://tests/m41_valley_play.gd"
## Tactical input policy for the new map: hold a rear guard against the announced
## cavalry; optionally send a mage and rider over the northern footbridge.
var flank=false
var flank_arrived={}
func _initialize():
 for arg in OS.get_cmdline_user_args():
  if arg=="--flank":flank=true
 call_deferred("run")
func plan(unit:Dictionary)->Dictionary:
 if State.pos(unit).x>=26 and State.pos(unit).y<=8:flank_arrived[str(unit.id)]=true
 var regular=super.plan(unit)
 var riders=ui.game.living("enemy").filter(func(e):return str(e.id).begins_with("M41_r"))
 var rear=["hunapu","daan","beck"]
 if str(unit.id)in rear and(not ui.game.flags.quest.reinforced or not riders.is_empty()):
  if regular.kind=="heal":return regular
  var goals=[]
  if not riders.is_empty():
   for e in riders:
    for delta in ui.game.DIRECTIONS:goals.append(State.pos(e)+delta)
  else:goals=[{"hunapu":Vector2i(9,6),"daan":Vector2i(10,8),"beck":Vector2i(8,8)}[str(unit.id)]]
  if unit.id=="fula":
   var guard=ui.game.find_unit("german");goals=[State.pos(guard)+Vector2i(0,2)]
  return directed_plan(unit,goals,riders,14.0)
 if flank and str(unit.id)in ["lance","hervi"] and not flank_arrived.has(str(unit.id)) and ui.game.turn<12:
  if regular.kind in ["heal","interact"]:return regular
  var p=State.pos(unit);var goal=Vector2i(20,6)if p.x<20 else Vector2i(26,6)
  return directed_plan(unit,[goal],[],16.0)
 return regular
func directed_plan(unit:Dictionary,goals:Array,targets:Array,pace:float)->Dictionary:
 var origin=State.pos(unit);var graph=ui.game.reachable(unit);var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1};var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell)and Items.can_use(unit,spell):weapons.append(spell)
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell);var walking=pace*(before-int(field.get(cell,99999)))-danger*2.5
  if danger>=int(unit.hp)-2:walking-=180.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    if not targets.is_empty()and not targets.any(func(e):return e.id==enemy.id):continue
    var reply=Rules.default_counter(enemy,distance(cell,State.pos(enemy)));var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell));var count=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var damage=float(stats.damage*count)*stats.hit/100.0;var counter=float(response.damage)*response.hit/100.0 if Rules.can_attack(reply,distance(cell,State.pos(enemy)))else 0.0
    if counter>=int(unit.hp)-Items.cost(weapon):continue
    var score=walking+minf(damage,enemy.hp)*3.0+(65.0 if damage>=int(enemy.hp)*.95 else 0.0)-counter-Items.cost(weapon)
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best
func act(id:String)->void:
 var unit=ui.game.find_unit(id);var before=State.pos(unit)if not unit.is_empty()else Vector2i.ZERO
 await super.act(id)
 if abort:return
 unit=ui.game.find_unit(id)
 if unit.is_empty():return
 var at=State.pos(unit)
 operations.append({"kind":"sample route trace","turn":ui.game.turn,"unit":id,"from":[before.x,before.y],"to":[at.x,at.y]})
 if ui.game.turn in [4,5,7,10]and not checkpoints.any(func(c):return c.name=="M41-turn-"+str(ui.game.turn)):
  await snapshot("M41-turn-"+str(ui.game.turn))

func write_progress()->void:
 super.write_progress()
 var path=late_folder+late_label+"-play.json";var report=State.read_json(path)
 report.strategy="leader and two archers protect rear; rider/mage northern bridge"if flank else "leader and two archers protect rear; main bridge attack"
 report.route_trace=operations.filter(func(o):return o.get("kind","")=="sample route trace")
 report.flank_arrived=flank_arrived
 var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
