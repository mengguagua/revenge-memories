extends "res://tests/map_polish_play.gd"
## Independent real-input F22 policy: maintain a protected boarding formation,
## use the existing convoy sword, heal beside the front line, then release captives.
func _initialize() -> void:
 var label="polish-f22-formation"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):label=arg.split("=")[1]
 review_out="res://reports/map-polish-20261022/play/"+label+"/"
 call_deferred("run")

func go(node:int) -> void:
 await super.go(node)
 if not abort and ui.game.mode=="world" and ui.game.stage_id==202:
  await equip_from_convoy("eileen",60)

func rank(unit:Dictionary) -> int:
 var carlo=ui.game.find_unit("carlo")
 if str(unit.id)=="mireille" and not carlo.is_empty() and int(carlo.hp)<int(carlo.max_hp)*.55:return -1
 if str(unit.id)=="carlo":return 0
 if str(unit.id)=="lisa":return 1
 if str(unit.id)=="mireille":return 2
 return 3

func plan(unit:Dictionary) -> Dictionary:
 if ui.game.stage_id!=202:return super.plan(unit)
 var enemies=ui.game.living("enemy");var origin=State.pos(unit);var graph=ui.game.reachable(unit)
 var tank=ui.game.find_unit("carlo");var healer=ui.game.find_unit("mireille")
 var is_tank=str(unit.id)=="carlo";var is_healer=str(unit.id)=="mireille";var commander=str(unit.id)=="eileen"
 var vulnerable=is_healer or commander or int(unit.hp)<int(unit.max_hp)*.5
 # Once the boarding wave has been thinned, recover at the nearest real deck
 # post before approaching a guarded survivor. This is an ordinary wait on
 # existing recovery terrain, not a health edit or an artificial checkpoint.
 if not enemies.is_empty() and enemies.size()<=3 and int(unit.hp)<int(unit.max_hp)*.9:
  var recovery:Array=[]
  for y in range(ui.game.battle_data.map.height):
   for x in range(ui.game.battle_data.map.width):
    var at=Vector2i(x,y)
    if ui.game.category(at)==15 and (ui.game.unit_at(at).is_empty() or State.pos(unit)==at):recovery.append(at)
  if not recovery.is_empty():
   var recovery_field=distance_map(unit,recovery);var recovery_before=int(recovery_field.get(origin,99999))
   var rest={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
   for cell in graph.costs:
    if not ui.game.can_stop(unit,cell):continue
    var danger=risk(unit,cell);var score=8.0*(recovery_before-int(recovery_field.get(cell,99999)))-danger*5.0
    if recovery.has(cell):score+=150.0
    if danger>0 and danger>=int(unit.hp)-3:score-=1000.0
    if score>rest.score:rest={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
   return rest
 var goals:Array=[]
 if enemies.is_empty():
  var remaining=[]
  for object in ui.game.battle_data.objects:
   if object.get("optional",false) or ui.game.flags.quest.objects.get(object.id,false):continue
   remaining.append(object)
  for cell in graph.costs:
   if not ui.game.can_stop(unit,cell):continue
   var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
   for object in ui.game.interactions_for(candidate):
    if object.get("optional",false):continue
    return {"kind":"interact","cell":cell,"score":1000.0,"target":str(object.id),"spell":-1}
  if not remaining.is_empty():
   var object=remaining[0]
   for dir in ui.game.DIRECTIONS:goals.append(Vector2i(object.position[0],object.position[1])+dir)
  else:goals=[Vector2i(25,14),Vector2i(26,15),Vector2i(27,14)]
 else:
  var nearest={};var best_distance=99999
  for enemy in enemies:
   var d=distance(State.pos(tank) if not tank.is_empty() and int(tank.hp)>0 else origin,State.pos(enemy))
   if d<best_distance:best_distance=d;nearest=enemy
  if is_tank or tank.is_empty() or int(tank.hp)<=0:
   if not nearest.is_empty():
    for dir in ui.game.DIRECTIONS:goals.append(State.pos(nearest)+dir)
  elif is_healer:
   var ally=tank;var missing=-1
   for friend in ui.game.living("player"):
    if friend.id==unit.id or not friend.get("controllable",true):continue
    var amount=int(friend.max_hp)-int(friend.hp)+(10 if friend.id=="eileen" and int(friend.hp)<12 else 0)
    if amount>missing:missing=amount;ally=friend
   for dir in ui.game.DIRECTIONS:goals.append(State.pos(ally)+dir)
  else:
   var at=State.pos(tank)
   goals=[at+Vector2i.LEFT,at+Vector2i.LEFT*2,at+Vector2i.DOWN,at+Vector2i.UP]
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell);var progress=before-int(field.get(cell,99999)) if before<99999 else 0
  var walking=progress*(2.5 if is_tank else 2.0)-danger*(3.0 if vulnerable else 1.5)-float(graph.costs[cell])*.05
  if not enemies.is_empty() and not tank.is_empty() and int(tank.hp)>0 and not is_tank:
   walking-=maxi(0,distance(cell,State.pos(tank))-(1 if is_healer else 3))*5.0
   if cell.x>State.pos(tank).x:walking-=float(cell.x-State.pos(tank).x)*20.0
  if danger>0 and danger>=int(unit.hp)-4:walking-=500.0
  if ui.game.category(cell)==15 and int(unit.hp)<int(unit.max_hp):walking+=14.0
  if enemies.is_empty() and ui.game.flags.quest.objects.get("prison_door",false) and distance(cell,Vector2i(29,16))<=2:walking-=150.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for spell in Items.spells(unit):
   if spell not in [40,41] or not Items.can_use(unit,spell):continue
   candidate.erase("weapon_index")
   for target in ui.game.support_targets(candidate,spell):
    if target.get("locked",false) or not target.get("controllable",true):continue
    var missing=int(target.max_hp)-int(target.hp)
    if missing<2:continue
    var score=mini(missing,int(unit.strength))*7.0+(70.0 if int(target.hp)<int(target.max_hp)*.55 else 15.0)-danger*5.0
    if danger>=int(unit.hp)-Items.cost(spell)-3:score-=1000.0
    if score>best.score:best={"kind":"heal","cell":cell,"score":score,"target":str(target.id),"spell":spell}
  if is_healer:continue
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    var d=distance(cell,State.pos(enemy));var reply=Rules.default_counter(enemy,d)
    var attack=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var strikes=2 if int(attack.attack_speed)>int(attack.defender_attack_speed) else 1
    var expected=float(attack.damage*strikes)*float(attack.hit)/100.0
    var guaranteed_kill=int(attack.damage)>=int(enemy.hp) and int(attack.hit)>=95
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var counter=int(response.damage)*(2 if int(response.attack_speed)>int(response.defender_attack_speed) else 1) if Rules.can_attack(reply,d) and not guaranteed_kill else 0
    var cost=Items.cost(weapon) if weapon>=0 else 0
    if counter+cost>=int(unit.hp):continue
    var after=risk(candidate,cell,str(enemy.id) if guaranteed_kill else "")
    var score=minf(expected,enemy.hp)*4.0+(45.0 if guaranteed_kill else 0.0)-float(counter)*2.0-after*(3.0 if vulnerable else 1.5)-cost*3.0
    if not is_tank and not tank.is_empty() and cell.x>State.pos(tank).x:score-=float(cell.x-State.pos(tank).x)*20.0
    if after+counter+cost>=int(unit.hp)-3:score-=1000.0
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best
