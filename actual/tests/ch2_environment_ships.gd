extends "res://tests/ch2_environment_continuous.gd"
## Normal-input boarding policy: cover the near end of the upper gangplank
## before advancing into the escort ship. No live state changes are made.
func plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id!=202:return super.plan(unit)
 var hold=ui.game.turn<=5
 for enemy in ui.game.living("enemy"):
  if enemy.get("behavior","")!="guard":hold=true
 if not hold:return super.plan(unit)
 var origin=State.pos(unit);var id=str(unit.id);var front=id=="carlo"
 var goals={"carlo":Vector2i(11,12),"lisa":Vector2i(10,13),"eileen":Vector2i(9,12),"mireille":Vector2i(9,14)}
 var goal:Vector2i=goals.get(id,Vector2i(9,14))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1};var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  if cell.x<5 or cell.x>12 or cell.y<10 or cell.y>17:continue
  if not front and cell.x>11:continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell);var formation=-float(distance(cell,goal))*4.0
  var walking=formation-danger*(1.3 if front else 2.5)
  if danger>=int(unit.hp)-4:walking-=300.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for spell in Items.spells(unit):
   if spell not in [40,41] or not Items.can_use(unit,spell):continue
   candidate.erase("weapon_index")
   for ally in ui.game.support_targets(candidate,spell):
    var missing=int(ally.max_hp)-int(ally.hp)
    if missing<4:continue
    var urgency=60.0 if int(ally.hp)<int(ally.max_hp)*.6 else 0.0
    var score=mini(missing,int(unit.strength))*5.0+urgency+formation*.3-danger*2.0-Items.cost(spell)*2.0
    if danger>=int(unit.hp)-Items.cost(spell)-3:score-=300.0
    if score>best.score:best={"kind":"heal","cell":cell,"score":score,"target":str(ally.id),"spell":spell}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    var dist=distance(cell,State.pos(enemy));var reply=Rules.default_counter(enemy,dist)
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var strikes=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var expected=float(stats.damage*strikes)*stats.hit/100.0;var kill=expected>=int(enemy.hp)*.95
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var counter=float(response.damage)*(2 if response.attack_speed>response.defender_attack_speed else 1) if Rules.can_attack(reply,dist) else 0.0
    if counter>=int(unit.hp)-Items.cost(weapon)-3:continue
    var after=risk(candidate,cell,str(enemy.id) if kill else "")
    if after+counter>=int(unit.hp)-Items.cost(weapon)-4:continue
    var score=minf(expected,enemy.hp)*3.0+(55.0 if kill else 0.0)+formation*.4-counter-after*(1.2 if front else 2.0)-Items.cost(weapon)
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best
