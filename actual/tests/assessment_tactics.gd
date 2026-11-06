extends RefCounted
## Test-driver decisions only: protect injured units and account for spell HP.
## Does not change the game, RNG, hidden enemies, growth or objective conditions.
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")

static func threat_loss(d,u:Dictionary,cell:Vector2i,skip:String="")->float:
 var g=d.ui.game;var occupied={};var total=0.0
 for actor in g.units:
  if int(actor.hp)>0 and actor.side!="evacuated" and not actor.get("hidden",false) and actor.id!=u.id:occupied[State.pos(actor)]=actor
 occupied[cell]=u
 for enemy in g.living("enemy"):
  if enemy.id==skip or enemy.get("locked",false) or enemy.get("hidden",false) or enemy.get("offering_surrender",false):continue
  var graph=g.RefugeeTactics._enemy_reach(g,enemy,occupied);var loss=0.0
  for at in graph:
   if occupied.has(at) and occupied[at].id!=enemy.id:continue
   var distance=d.distance(at,cell);var attack=Rules.attack_context(enemy,distance)
   if not Rules.can_attack(attack,distance) or Rules.attack_blocked(attack,u):continue
   var reply=Rules.default_counter(u,distance);var stats=Rules.attack_stats(attack,reply,g.terrain_avoid(cell))
   var count=Rules.strike_sequence(attack,reply,distance).count("attacker")
   loss=maxf(loss,float(stats.damage*count))
  total+=loss
 return total

static func exposed_cost(d,u:Dictionary,p:Dictionary)->float:
 var actor=u.duplicate(true);actor.position=[p.cell.x,p.cell.y];actor.erase("weapon_index")
 var spent=0.0;var counter=0.0;var skip=""
 if p.kind=="heal":spent=Items.cost_for(actor,int(p.spell))
 if p.kind=="attack":
  if int(p.spell)>=0:actor.weapon_index=int(p.spell)
  var target=d.ui.game.find_unit(str(p.target))
  if target.is_empty():return 99999
  var reply=Rules.default_counter(target,d.distance(p.cell,State.pos(target)))
  var a=Rules.attack_stats(actor,reply,d.ui.game.terrain_avoid(State.pos(target)))
  var strikes=2 if a.attack_speed>a.defender_attack_speed else 1
  spent=Rules.magic_cost(actor)*strikes
  if Rules.can_attack(reply,d.distance(p.cell,State.pos(target))):
   var b=Rules.attack_stats(reply,actor,d.ui.game.terrain_avoid(p.cell))
   counter=float(b.damage)*(2 if b.attack_speed>b.defender_attack_speed else 1)
   if int(a.damage)>=int(target.hp) and int(a.hit)>=95:counter*=1.0-float(a.hit)/100.0
  if int(a.hit)==100 and int(a.damage)>=int(target.hp):skip=str(target.id)
 return spent+counter+maxf(d.risk(actor,p.cell,skip),threat_loss(d,actor,p.cell,skip))

static func safe_plan(d,u:Dictionary,p:Dictionary)->Dictionary:
 if p.is_empty():return p
 var reserve=3.0 if str(u.id) in ["hunapu","eileen"] else 2.0
 if exposed_cost(d,u,p)<float(u.hp)-reserve:return p
 var g=d.ui.game;var origin=State.pos(u);var goals=[]
 if int(u.hp)<int(u.max_hp)*.8:
  for y in range(g.battle_data.map.height):
   for x in range(g.battle_data.map.width):
    var at=Vector2i(x,y)
    if g.category(at)==15 and (g.unit_at(at).is_empty() or g.unit_at(at).id==u.id):goals.append(at)
  for ally in g.living("player"):
   if ally.id!=u.id and int(ally.class_id) in [17,18] and not ally.get("neutral",false):
    for step in g.DIRECTIONS:goals.append(State.pos(ally)+step)
 var field=d.distance_map(u,goals) if not goals.is_empty() else {}
 var best={"kind":"wait","cell":origin,"target":"","spell":-1,"score":-1.0e9}
 var candidates=[]
 for cell in g.reachable(u).costs:
  if not g.can_stop(u,cell):continue
  var danger=d.risk(u,cell)
  var score=-danger*6.0-float(d.distance(cell,p.cell))*.3
  if field.has(cell):score-=float(field[cell])*.8
  if g.category(cell)==15 and int(u.hp)<int(u.max_hp)-3:score+=35.0
  if danger>=float(u.hp)-reserve:score-=500
  candidates.append({"kind":"wait","cell":cell,"target":"","spell":-1,"score":score})
 candidates.sort_custom(func(a,b):return a.score>b.score)
 for option in candidates.slice(0,12):
  var exact=threat_loss(d,u,option.cell)
  option.score-=exact*3.0
  if exact>=float(u.hp)-reserve:option.score-=1000
  if option.score>best.score:best=option
 return best

static func equipment_score(g,u:Dictionary,item:int)->float:
 var v=u.duplicate(true);v.item_id=item;v.erase("weapon_index")
 if not Items.can_use(v,item):return -99999
 var s=g.EquipmentComparison.stats(v)
 var healer=int(v.class_id) in [17,18]
 return float(s.power)*(0.2 if healer else 1.7)+float(s.speed)*1.1+float(s.defence)*(2.2 if healer else 1.4)+float(s.resistance)*.7+float(s.range)*(0.2 if healer else 1.5)+float(s.hit)*.04+float(s.move)*.8+(3.0 if int(Items.item(item).get("effect_kind",0))==10 else 0.0)

static func equip(d,id:String,item:int)->void:
 var g=d.ui.game;var u=g.roster.get(id,{})
 if u.is_empty() or not g.can_deploy(u) or int(u.get("item_id",0))==item:return
 if equipment_score(g,u,item)<=equipment_score(g,u,int(u.get("item_id",0)))+.1:return
 var index=-1
 for slot in range(g.convoy[g.route].size()):
  if int(g.convoy[g.route][slot])==item:index=slot;break
 if index<0:return
 d.key(KEY_S);d.choose("new:camp");d.choose("camp:convoy");d.choose("camp:withdraw");d.choose("camp:withdraw_item:"+str(index))
 if d.abort:return
 if d.ui.view!="equipment_members" or not d.ui.equipment_screen.members.has(id):d.record_failure("Assessment equipment member unavailable: "+id);return
 for step in range(d.ui.equipment_screen.members.size()):
  if str(d.ui.equipment_screen.members[d.ui.equipment_screen.selected])==id:break
  d.key(KEY_DOWN)
 d.key(KEY_Z)
 if d.ui.view!="equipment_preview" or not d.ui.equipment_screen.preview().can_equip:d.record_failure("Assessment equipment preview incompatible");return
 var previous=int(u.get("item_id",0));d.key(KEY_Z);await d.settle()
 if int(g.roster[id].item_id)!=item:d.record_failure("Assessment equipment confirmation failed");return
 d.operations.append({"kind":"ordinary equipment upgrade","unit":id,"before":previous,"after":item,"stage":g.stage_id})
 if not d.ui.menu_items.is_empty():d.key(KEY_X)

static func improve_equipment(d)->void:
 for id in d.ui.game.party:
  if d.abort:return
  var u=d.ui.game.roster[id]
  if not d.ui.game.can_deploy(u):continue
  var best=int(u.get("item_id",0));var score=equipment_score(d.ui.game,u,best)
  for item in d.ui.game.convoy[d.ui.game.route]:
   var candidate=equipment_score(d.ui.game,u,int(item))
   if candidate>score+.1:best=int(item);score=candidate
  await equip(d,str(id),best)

static func promotions(d,action:String)->void:
 for repeat in range(16):
  if d.abort:return
  var desired=""
  for id in d.ui.game.party:
   var u=d.ui.game.roster[id]
   if not d.ui.game.can_deploy(u):continue
   var options=d.ui.Progression.promotion_options(u)
   if not options.is_empty():desired="hub:promote_"+str(id)+"_"+str(int(options[0].class_id));break
  if desired.is_empty():return
  await d.hub_action(action)
  if action=="east_training":d.choose("hub:east_promotions")
  if action=="third_training":d.choose("hub:third_promotions")
  if not d.ui.menu_actions.has(desired):d.record_failure("Promotion menu missing earned option: "+desired);return
  var parts=desired.trim_prefix("hub:").split("_")
  var member=str(parts[1]);var target_class=int(parts[2]);var before=d.ui.game.roster[member].duplicate(true)
  d.choose(desired);await d.settle()
  var after=d.ui.game.roster[member]
  if int(after.class_id)!=target_class or int(after.level)!=1:d.record_failure("Visible promotion action had no effect: "+desired);return
  d.operations.append({"kind":"ordinary earned promotion","action":desired,"stage":d.ui.game.stage_id,"before_class":int(before.class_id),"after_class":int(after.class_id),"verified":true})

static func treat_priority(d)->void:
 for id in ["fula","mireille","hervi","lisa","otto","lena","daan","lance","roan","carlo","shia","beck","german","noya","celine"]:
  var g=d.ui.game
  if d.abort or g.treatment_remaining()<=0:return
  if not g.party.has(id) or not g.is_dying(g.roster[id]) or int(g.roster[id].get("treatment_count",0))>0:continue
  await d.hub_action("treatment")
  if not d.ui.menu_actions.has("hub:treat_choose_"+id):
   if not d.ui.menu_items.is_empty():d.key(KEY_X)
   continue
  var before=g.treatment_remaining()
  d.choose("hub:treat_choose_"+id);d.choose("hub:treat_confirm_"+id);await d.settle()
  if g.is_dying(g.roster[id]) or g.treatment_remaining()!=before-1:d.record_failure("Ordinary treatment did not settle: "+id);return
  d.operations.append({"kind":"ordinary injury treatment","unit":id,"remaining":g.treatment_remaining()})

static func escort_priority(d,u:Dictionary,original:Dictionary)->Dictionary:
 var g=d.ui.game;var escorts=g.living("player").filter(func(v):return v.get("quest_kind","")=="escort" and v.get("neutral",false))
 if escorts.is_empty():return original
 var best=original.duplicate(true);var weapons=[-1]
 for spell in Items.spells(u):
  if not Items.is_support(spell) and Items.can_use(u,spell):weapons.append(spell)
 for cell in g.reachable(u).costs:
  if not g.can_stop(u,cell):continue
  for weapon in weapons:
   var candidate=u.duplicate(true);candidate.position=[cell.x,cell.y];candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for target in g.targets(candidate):
    var near=999
    for escort in escorts:near=mini(near,d.distance(State.pos(target),State.pos(escort)))
    var distance=d.distance(cell,State.pos(target));var counter=Rules.default_counter(target,distance)
    var stats=Rules.attack_stats(candidate,counter,g.terrain_avoid(State.pos(target)))
    var strikes=Rules.strike_sequence(candidate,counter,distance).count("attacker")
    var damage=float(stats.damage*strikes)*float(stats.hit)/100.0
    var action={"kind":"attack","cell":cell,"target":str(target.id),"spell":weapon,"score":0.0}
    var loss=exposed_cost(d,u,action)
    var score=minf(damage,float(target.hp))*2.0+(50.0 if damage>=float(target.hp) else 0.0)+maxi(0,8-near)*14.0-loss*2.0
    if loss>=float(u.hp)-2:score-=200.0
    if score>float(best.score):action.score=score;best=action
 return best

static func intercept(d,u:Dictionary,target_id:String)->Dictionary:
 var g=d.ui.game;var target=g.find_unit(target_id)
 if target.is_empty() or int(target.hp)<=0:return d.combat_plan(u)
 var origin=State.pos(u);var goals=[]
 var reach=Rules.attack_range(u).y
 for y in range(maxi(1,State.pos(target).y-reach),mini(int(g.battle_data.map.height)-1,State.pos(target).y+reach+1)):
  for x in range(maxi(1,State.pos(target).x-reach),mini(int(g.battle_data.map.width)-1,State.pos(target).x+reach+1)):
   var cell=Vector2i(x,y)
   if d.distance(cell,State.pos(target)) in range(1,reach+1) and g.movement_cost(u,cell)<255:goals.append(cell)
 var field=d.distance_map(u,goals);var before=int(field.get(origin,99999))
 var best={"kind":"wait","cell":origin,"target":"","spell":-1,"score":-1.0e9}
 for cell in g.reachable(u).costs:
  if not g.can_stop(u,cell):continue
  var walking=float(before-int(field.get(cell,99999)))*10.0-d.risk(u,cell)*2.0
  if d.risk(u,cell)>=float(u.hp)-2:walking-=200
  if walking>best.score:best={"kind":"wait","cell":cell,"target":"","spell":-1,"score":walking}
  var options=[-1]
  for spell in Items.spells(u):
   if not Items.is_support(spell) and Items.can_use(u,spell):options.append(spell)
  for weapon in options:
   var actor=u.duplicate(true);actor.position=[cell.x,cell.y];actor.erase("weapon_index")
   if weapon>=0:actor.weapon_index=weapon
   for enemy in g.targets(actor):
    var response=Rules.default_counter(enemy,d.distance(cell,State.pos(enemy)))
    var stats=Rules.attack_stats(actor,response,g.terrain_avoid(State.pos(enemy)))
    var damage=float(stats.damage)*float(stats.hit)/100.0*Rules.strike_sequence(actor,response,d.distance(cell,State.pos(enemy))).count("attacker")
    var plan={"kind":"attack","cell":cell,"target":str(enemy.id),"spell":weapon,"score":0.0}
    var loss=exposed_cost(d,u,plan)
    var score=walking+minf(damage,float(enemy.hp))*2.0+(100 if str(enemy.id)==target_id else 0)-loss
    if loss>=float(u.hp)-2:score-=250
    if score>best.score:plan.score=score;best=plan
 return best
