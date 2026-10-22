extends "res://tests/late_map_chapter4_play.gd"
## An escort-first input strategy: split the flyer toward the southern group,
## send the main formation over the central bridge. No live state is changed.
func plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id!=407 or ui.game.living("enemy").is_empty():return super.plan(unit)
 var regular=super.plan(unit)
 if regular.kind in ["interact","heal"]:return regular
 if ui.game.turn>9:return regular
 var origin=State.pos(unit)
 var goal=Vector2i(18,18) if str(unit.id)=="shia" else Vector2i(15,15)
 var graph=ui.game.reachable(unit);var field=distance_map(unit,[goal]);var before=int(field.get(origin,99999))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell)and Items.can_use(unit,spell):weapons.append(spell)
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell);var progress=before-int(field.get(cell,99999))
  var walking=progress*15.0-danger*2.0
  if danger>=int(unit.hp)-2:walking-=180.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    var reply=Rules.default_counter(enemy,distance(cell,State.pos(enemy)))
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var count=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var damage=float(stats.damage*count)*stats.hit/100.0
    var counter=float(response.damage)*response.hit/100.0 if Rules.can_attack(reply,distance(cell,State.pos(enemy)))else 0.0
    if counter>=int(unit.hp)-Items.cost(weapon):continue
    var nearby=999
    for npc in ui.game.living("player"):
     if npc.get("quest_kind","")=="escort":nearby=mini(nearby,distance(State.pos(enemy),State.pos(npc)))
    var score=walking+minf(damage,enemy.hp)*3.0+(55.0 if damage>=int(enemy.hp)*.95 else 0.0)+maxi(0,7-nearby)*10.0-counter-Items.cost(weapon)
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best
