extends "res://tests/ch1_redesign_play.gd"
# Two real-input escorts hold separate mine passages; all ordinary game rules apply.
func plan(unit:Dictionary) -> Dictionary:
 if ui.game.stage_id!=111 or ui.game.living("enemy").is_empty():return super.plan(unit)
 var origin=State.pos(unit);var west=ui.game.find_unit("S11_e4");var west_alive=not west.is_empty() and int(west.hp)>0
 var is_bow=str(unit.id)=="daan";var is_guard=str(unit.id)=="otto"
 var goal=Vector2i(6,9) if is_bow else Vector2i(8,8) if is_guard else Vector2i(12,15)
 var goals:Array=[goal]
 if (is_guard or is_bow) and west_alive:
  goals=[]
  for d in ui.game.DIRECTIONS:goals.append(State.pos(west)+d)
 elif (is_guard or is_bow) and int(ui.game.find_unit("S11_boss").hp)>0:
  goals=[]
  var threat=ui.game.find_unit("S11_boss")
  for d in ui.game.DIRECTIONS:goals.append(State.pos(threat)+d)
 elif ui.game.turn>=3:
  var closest={};var distance_=99999
  var miner=ui.game.find_unit("S11_miners0" if is_guard or is_bow else "S11_miners1")
  var anchor=State.pos(miner) if not miner.is_empty() and int(miner.hp)>0 and miner.side=="player" else origin
  for e in ui.game.living("enemy"):
   var n=distance(State.pos(e),anchor)
   if n<distance_:closest=e;distance_=n
  if not closest.is_empty():
   goals=[]
   for d in ui.game.DIRECTIONS:goals.append(State.pos(closest)+d)
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell)
  var progress=12.0*(before-int(field.get(cell,99999)))
  var formation=65.0 if ui.game.turn<=4 and cell==goal and not(is_guard and west_alive) else 0.0
  var walking=progress+formation-danger*.55
  if danger>=int(unit.hp)-2:walking-=200.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    var dist=distance(cell,State.pos(enemy));var reply=Rules.default_counter(enemy,dist)
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var strikes=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var expected=float(stats.damage*strikes)*stats.hit/100.0;var kill=expected>=int(enemy.hp)*.95
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var counter=float(response.damage)*response.hit/100.0*(2 if response.attack_speed>response.defender_attack_speed else 1) if Rules.can_attack(reply,dist) else 0.0
    if counter>=int(unit.hp)-Items.cost(weapon)-1:continue
    var miner_near=999
    for npc in ui.game.living("player"):
     if npc.get("quest_kind","")=="escort":miner_near=mini(miner_near,distance(State.pos(enemy),State.pos(npc)))
    var protected=ui.game.find_unit("S11_miners0" if is_guard or is_bow else "S11_miners1")
    var protected_distance=distance(State.pos(enemy),State.pos(protected)) if not protected.is_empty() else miner_near
    var urgency=maxf(0.0,110.0-float(protected_distance)*18.0)
    if (is_guard or is_bow) and int(ui.game.find_unit("S11_boss").hp)>0:
     urgency+=140.0 if enemy.id in ["S11_boss","S11_e6"] else -200.0
    if (is_guard or is_bow) and west_alive:urgency+=110.0 if enemy.id=="S11_e4" else -30.0
    if is_bow and int(enemy.class_id)==12:urgency+=50.0
    var after_danger=risk(candidate,cell,str(enemy.id) if kill else "")
    var score=minf(expected,enemy.hp)*3.0+(75.0 if kill else 0.0)+urgency+formation*.5+progress*.4-counter-after_danger*.5
    if after_danger+counter>=int(unit.hp)-2:score-=150.0
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best
