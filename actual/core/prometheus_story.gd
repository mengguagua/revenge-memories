extends RefCounted
const L=preload("res://core/late_dialogue.gd")
const PANEL=Vector2i(8,12)
static func applies(g)->bool:return g.stage_id==408 and g.Mechanical.is_prometheus(g.find_unit(str(g.battle_data.boss_id)))
static func captured(g)->bool:return bool(g.flags.quest.get("viser_captured",false))
static func tested(g)->bool:
 var q:Dictionary=g.flags.quest
 return ["regulator_1","regulator_2","regulator_3"].all(func(id):return q.objects.get(id,false)) and int(q.get("repair_since",-1))>=0 and g.phase=="player" and g.turn>int(q.repair_since)
static func death(g,u:Dictionary)->void:
 if not applies(g):return
 if str(u.id)=="F44_viser" and not captured(g):
  u.hp=1;u.dead=false;u.side="neutral";u.surrendered=true;u.no_counter=true;u.acted=true
  g.flags.quest.viser_captured=true
  for guard in g.units:
   if guard.get("viser_guard",false) and int(guard.hp)>0:guard.side="neutral";guard.surrendered=true;guard.no_counter=true;guard.acted=true
  L.queue(g,L.lines("F44","战中交互",0),"F44-VISER")
 elif str(u.id)==str(g.battle_data.boss_id) and int(u.hp)<=0:
  g.flags.prometheus_outcome="destroyed"
  L.queue(g,L.lines("F44","两条",0),"F44-DESTROYED")
static func action(g,u:Dictionary)->Dictionary:
 if not applies(g) or not str(u.id).begins_with("repairer"):return {}
 if not captured(g):return {"destination":g.pos(u),"target":""}
 var destination=Vector2i(8,13) if str(u.id)=="repairer0" else Vector2i(9,12)
 return g._safe_escort_move(u,destination)
static func interact(g,id:String)->bool:
 if not applies(g) or id!="maintenance_panel":return false
 if not captured(g):g.queue_lines("战场提示：先制服维瑟，取得检修门的钥匙。","F44-KEY-NEEDED");return true
 if str(g.flags.get("prometheus_outcome",""))=="destroyed":g.queue_lines("工匠：它已经醒不过来了。病房还有人，我们先去接。","F44-TOO-LATE");return true
 if not tested(g):g.queue_lines("战场提示：三处装置都接管后，保护工匠至下一己方回合。","F44-TEST-NEEDED");return true
 var nearby=false
 for id2 in ["repairer0","repairer1"]:
  var u=g.find_unit(id2)
  if not u.is_empty() and int(u.hp)>0 and g.pos(u).distance_to(PANEL)<=1.1:nearby=true
 if not nearby:g.queue_lines("战场提示：工匠还没到检修台。清出西侧通道，让存活工匠抵达。","F44-WORKER-NEEDED");return true
 if g.flags.quest.get("maintenance_pending",false):return true
 g.flags.quest.maintenance_pending=true
 g.story_events.append({"kind":"new_story","key":"F44-MAINTENANCE","pages":L.pages(g,L.lines("F44","两条",1)),"callback":"prometheus_maintenance"})
 return true
static func accept(g)->void:
 if not applies(g) or not captured(g) or not g.flags.quest.get("maintenance_pending",false) or not tested(g):return
 var boss=g.find_unit(str(g.battle_data.boss_id))
 if int(boss.hp)<=0 or str(g.flags.get("prometheus_outcome",""))=="destroyed":return
 boss.side="neutral";boss.no_counter=true;boss.surrendered=true;boss.maintenance=true;boss.acted=true
 boss.mechanical_retreating=false;boss.move=6;boss.erase("innate_attack_index");boss.erase("innate_counter")
 g.flags.prometheus_outcome="maintenance";g.flags.quest.objects.maintenance_panel=true
 g.flags.quest.maintenance_pending=false
 g.check_outcome()
static func ready(g)->bool:
 return captured(g) and tested(g) and str(g.flags.get("prometheus_outcome","")) in ["destroyed","maintenance"] and g.living("enemy").is_empty() and (g.battle_data.reinforcements.is_empty() or g.flags.quest.get("reinforced",false))
