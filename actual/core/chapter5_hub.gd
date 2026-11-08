extends RefCounted
const L=preload("res://core/late_dialogue.gd")
const Prior=preload("res://core/chapter3_hub.gd")
static func action(h,key:String) -> void:
 var ui=h.ui;var g=ui.game
 if key.begins_with("fifth_toggle_"):
  var id=key.substr(13);var selected=g.ChapterFive.selection(g,g.route)
  if id==g.leader_id():ui._notice("两位主角必须出阵")
  elif selected.has(id):selected.erase(id);g.flags.chapter5_ready[g.route]=bool(g.flags.get("chapter5_merged",false))
  elif g.party.has(id) and g.can_deploy(g.roster[id]) and selected.size()<10:selected.append(id);g.flags.chapter5_ready[g.route]=bool(g.flags.get("chapter5_merged",false))
  open_selection(h);return
 match key:
  "fifth_shield_keeper":await g.Accessories.talk(h,53)
  "fifth_ward_report":
   await L.say(h,L.lines("H51","D51"),"late:M51_confirmed")

  "fifth_west_report":
   await L.say(h,L.lines("H52","西门"))

  "fifth_repair_report":
   await L.say(h,L.lines("H53","地方",0)+L.outcome(g,"H53","地方",1,2)+L.lines("H53","地方",3),"late:F51_handover_seen")

  "fifth_east_report","fifth_archive_invite":
   await L.say(h,L.lines("H54","旧书库",1 if g.Armaments.claimed(g,7) else 0))

  "fifth_archive_report":
   await L.say(h,L.lines("H56","旧事"))

  "fifth_prepare":open_selection(h)
  "fifth_ready":
   g.flags.chapter5_ready[g.route]=true;ui._notice("本队名单已确认；从菜单切换另一队确认",6)
  "fifth_merge":
   if g.flags.get("chapter5_merged",false):await L.say(h,L.lines("H55","合军",1 if g.flags.get("final_access",false) else 3));return
   if int(g.route_positions.alm)!=15 or int(g.route_positions.celica)!=15:await L.say(h,L.lines("H55","合军",4));return
   if not g.flags.get("H55_letters_seen",false):
    await L.say(h,L.lines("H55","两队",0)+L.outcome(g,"H55","两队",1,2)+L.lines("H55","两队",3),"late:H55_letters_seen")
   if not g.flags.chapter5_ready.alm or not g.flags.chapter5_ready.celica:ui._notice("请先分别确认两队出阵名册",6);return
   await L.say(h,L.lines("H55","合军",0 if g.stage_cleared(511) else 2).filter(func(row):return not str(row).begins_with("界面提示：")))
   var reminder=g.Accessories.closing_reminder(g,53)
   if not reminder.is_empty():ui._notice(reminder,6)
   ui._open_menu("fifth_merge",["返回整理","确认合流出发"],["close","hub:fifth_confirm_merge"],Vector2(24,96))

  "fifth_confirm_merge":
   if g.ChapterFive.merge(g):h.enter_room("H55",true);ui._notice("两军已合流；南口返回地图进入战场",6)
   else:ui._notice("名单或抵达状态已变化，请重新确认",6)
  "fifth_relationship":
   var active=g.speaker_alive("达恩") and g.speaker_alive("米蕾")
   if g.flags.get("seen_R03",false):await L.say(h,L.lines("H55","R03",1 if active else 3));return
   if not active or not g.flags.get("seen_R01",false) or not g.flags.get("seen_R02",false) or int(g.route_positions.alm)!=15 or int(g.route_positions.celica)!=15:await L.say(h,L.lines("H55","R03",0));return
   await L.say(h,L.lines("H55","R03",2),"late:seen_R03")

static func open_selection(h) -> void:
 var g=h.ui.game;var selected=g.ChapterFive.selection(g,g.route);var labels=[];var actions=[]
 for id in g.party:
  if not g.can_deploy(g.roster[id]):continue
  labels.append(("出阵 · " if selected.has(id) else "留守 · ")+str(g.roster[id].name_zh));actions.append("hub:fifth_toggle_"+str(id))
 labels.append(("确认西队名单" if g.route=="alm" else "确认东队名单")+"（%d/10）"%selected.size());actions.append("hub:fifth_ready")
 h.ui._open_menu("fifth_selection",labels,actions,Vector2(32,48))
