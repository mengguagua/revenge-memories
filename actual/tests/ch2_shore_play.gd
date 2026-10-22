extends "res://tests/ch2_redesign_play.gd"
## Ordinary-input shore defence. The two front-line fighters cover the camp
## while the caster and cleric stay within mutual support range. Read-only
## combat previews select actions; the inherited input driver executes them.
var shore_turn_logged=-1

func rank(unit:Dictionary)->int:
 if ui!=null and ui.game.stage_id==203:
  return {"lord":0,"carlo":1,"lisa":2,"eileen":3,"mireille":4}.get(str(unit.id),5)
 return super.rank(unit)

func act(id:String)->void:
 if ui.game.stage_id==203 and shore_turn_logged!=ui.game.turn:
  shore_turn_logged=ui.game.turn
  var summary=[]
  for u in ui.game.units:
   if int(u.hp)>0:summary.append({"id":u.id,"pos":u.position.duplicate(),"hp":u.hp})
  print("SHORE_FORMATION ",ui.game.turn," ",JSON.stringify(summary))
  operations.append({"kind":"shore formation","turn":ui.game.turn,"units":summary})
 await super.act(id)

func write_progress()->void:
 super.write_progress()
 if late_folder.is_empty():return
 var f=FileAccess.open(late_folder+late_label+"-shore-actions.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"policy":"Hold southern camp court for incoming flyers and raiders, then advance together after the local wave is cleared.","inputs_only":true,"operations":operations},"  "));f.close()

func plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id!=203 or ui.game.living("enemy").is_empty():return super.plan(unit)
 var hold=ui.game.turn<=4
 for e in ui.game.living("enemy"):
  if e.get("behavior","")!="guard" and State.pos(e).y>=13:hold=true
 if not hold:return super.plan(unit)
 var origin=State.pos(unit);var id=str(unit.id)
 var front=id in ["lord","carlo"]
 var goals={"lord":Vector2i(15,18),"carlo":Vector2i(14,18),"lisa":Vector2i(13,20),"mireille":Vector2i(12,21),"eileen":Vector2i(12,19)}
 var goal:Vector2i=goals.get(id,Vector2i(12,19))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  if cell.x<10 or cell.x>17 or cell.y<16 or cell.y>22:continue
  # A defensive choice is a real movement limit, including attack moves.
  # The general driver's eager attack preview otherwise bypasses formation.
  if ui.game.turn<=3 and (cell.x>15 or cell.y<18):continue
  if ui.game.turn<=3 and not front and (cell.x>14 or cell.y<19):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell)
  var formation=-float(distance(cell,goal))*5.0
  if not front:formation-=float(maxi(0,18-cell.y)+maxi(0,cell.x-14))*12.0
  var walking=formation-danger*(1.2 if front else 2.3)
  if danger>=int(unit.hp)-3:walking-=250.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for spell in Items.spells(unit):
   if spell not in [40,41] or not Items.can_use(unit,spell):continue
   candidate.erase("weapon_index")
   for ally in ui.game.support_targets(candidate,spell):
    var missing=int(ally.max_hp)-int(ally.hp)
    if missing<4:continue
    var urgency=45.0 if int(ally.hp)<int(ally.max_hp)*.5 else 0.0
    var score=mini(missing,int(unit.strength))*5.0+urgency+formation*.35-danger*2.0-Items.cost(spell)*2.0
    if danger>=int(unit.hp)-Items.cost(spell)-2:score-=250.0
    if score>best.score:best={"kind":"heal","cell":cell,"score":score,"target":str(ally.id),"spell":spell}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    var dist=distance(cell,State.pos(enemy));var reply=Rules.default_counter(enemy,dist)
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var strikes=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var expected=float(stats.damage*strikes)*stats.hit/100.0
    var kill=expected>=int(enemy.hp)*.95
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var counter=float(response.damage)*response.hit/100.0*(2 if response.attack_speed>response.defender_attack_speed else 1) if Rules.can_attack(reply,dist) else 0.0
    if counter>=int(unit.hp)-Items.cost(weapon)-1:continue
    var after=risk(candidate,cell,str(enemy.id) if kill else "")
    var urgency=maxf(0.0,30.0-distance(State.pos(enemy),Vector2i(12,19))*3.0)
    # Flyers can cross the line and reach the cleric. Finish those attackers
    # before an equally exposed foot raider when both are available.
    if int(enemy.class_id)==3 and State.pos(enemy).y>=14:urgency+=35.0
    var score=minf(expected,enemy.hp)*3.0+(55.0 if kill else 0.0)+urgency+formation*.5-counter-after*(1.0 if front else 1.8)-Items.cost(weapon)
    if after+counter>=int(unit.hp)-Items.cost(weapon)-2:score-=250.0
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best
