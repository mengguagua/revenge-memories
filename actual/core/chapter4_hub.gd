extends RefCounted
const L=preload("res://core/late_dialogue.gd")
const Rules=preload("res://core/chapter4_rules.gd")
const Prior=preload("res://core/chapter3_hub.gd")
static func pages(h,lines:Array) -> void:await Prior.pages(h,lines)
static func action(h,key:String) -> void:
 var ui=h.ui;var g=ui.game
 # The training menu is shared with chapter three, including the callbacks
 # it generates. Forward confirmations as well as the menu-opening actions.
 if key.begins_with("promote_") or key.begins_with("third_transfer_"):
  await Prior.action(h,key);return
 match key:
  "fourth_snow_settle":
   var rows=L.lines("H41","安置",0)+L.lines("H41","安置",1 if g.speaker_alive("奥托") else 2)+L.lines("H41","安置",3)
   await L.say(h,rows,"late:M41_confirmed")

  "fourth_s41":
   await L.say(h,L.lines("H41","黑钟"),"late:S41_invited")

  "fourth_transfer_report":
   await L.say(h,L.lines("H42","投送"))

  "fourth_tower_shutdown":
   if g.flags.get("west_tower_safe",false):await L.say(h,L.lines("H43","等待",4));return
   if not g.flags.get("obs_steps_ready",false):await L.say(h,L.lines("H43","等待",0));return
   await L.say(h,L.join_groups("H43","等待",[1,2,3]),"late:west_tower_safe")

  "fourth_herlan":
   await L.say(h,L.lines("H44","赫兰"),"late:herlan_handover_seen")

  "fourth_well_report":
   await L.say(h,L.lines("H45","井台"),"late:F41_confirmed")

  "fourth_obs_report":
   await L.say(h,L.lines("H46","将观测"),"late:obs_steps_ready")

  "fourth_marsh_report":
   await L.say(h,L.lines("H47","沼泽"),"late:F43_confirmed")

  "fourth_s42":
   await L.say(h,L.lines("H47","赛琳"),"late:S42_invited")

  "fourth_island_verify":
   var first=not g.flags.get("island_handover_seen",false)
   var rows=L.lines("H48","局部",0 if first else 1)
   if first and g.flags.has("prometheus_outcome"):rows+=L.lines("H48","维瑟",0)+L.outcome(g,"H48","维瑟",1,2)
   await L.say(h,rows,"late:island_handover_seen")

  "fourth_d42":
   if g.flags.get("D42_done",false):await L.say(h,L.lines("H48","D42",5));return
   if not g.flags.get("west_tower_safe",false):await L.say(h,L.lines("H48","D42",0));return
   if not g.flags.get("island_loop_safe",false):return
   var rows=[]
   if not g.flags.get("island_handover_seen",false) and g.flags.has("prometheus_outcome"):rows+=L.lines("H48","维瑟",0)+L.outcome(g,"H48","维瑟",1,2)
   rows+=L.lines("H48","D42",1)
   var outcome=str(g.flags.get("prometheus_outcome",""))
   if outcome in ["maintenance","destroyed"]:rows.append(L.lines("H48","D42",2)[0 if outcome=="maintenance" else 1])
   rows+=L.lines("H48","D42",3)
   if not g.Armaments.claimed(g,17):rows+=L.lines("H48","D42",4)
   await L.say(h,rows,"late:island_handover_seen,D42_done")

  "fourth_ring_keeper":await g.Accessories.talk(h,55)
  "fourth_black_report":
   await L.say(h,L.lines("H49","名册",1 if g.flags.get("S41_register_saved",false) else 0))

  "fourth_celine":
   if g.party.has("celine"):await L.say(h,L.lines("H50","赛琳",2));return
   if not g.flags.get("celine_ready",false):await L.say(h,L.lines("H50","赛琳",0));return
   await L.say(h,L.lines("H50","赛琳",1),"late_invite:celine")

  "fourth_recruit_celine":
   if g.flags.get("celine_ready",false):g.recruit("celine");h.enter_room(h.room,true)
  "fourth_vya":
   await L.say(h,L.lines("H50","薇娅"))

  "fourth_spring":
   var left=3-int(g.flags.get("fourth_strength_uses",0));var labels=[];var actions=[]
   if left<=0:await pages(h,["旁白：祭所的三次力量泉份额已用尽。"]);return
   for id in g.party:
    if not g.is_dying(g.roster[id]):labels.append(str(g.roster[id].name_zh));actions.append("hub:fourth_strength_"+id)
   ui._open_menu("spring",labels,actions,Vector2(40,48))
  "third_training","third_promotions","third_exchange":await Prior.action(h,key)
  "third_relations","fourth_letters":await relations(h)
  "third_council","fourth_progress":
   var missing=Rules.missing(g)
   if not missing.is_empty():
    await L.say(h,L.lines("H10","D33",3));ui._notice("；".join(missing),8);return
   await L.say(h,L.lines("H10","D33",4),"late:chapter4_final_plan_seen")

  "third_messenger":
   if not Rules.missing(g).is_empty():await action(h,"fourth_progress");return
   if not g.flags.get("chapter4_final_plan_seen",false):await action(h,"fourth_progress")
   var unfinished=[]
   if not g.stage_cleared(411):unfinished.append("黑钟村名册")
   if not g.stage_cleared(412):unfinished.append("沼泽孤岛救援")
   if not unfinished.is_empty():ui._notice("未完成支线："+"、".join(unfinished)+"。本章收束后不可折返。",6)
   ui._open_menu("fourth_end",["继续整备","确认第四章收束"],["close","hub:fourth_finish"],Vector2(36,88))

  "fourth_finish":
   if Rules.missing(g).is_empty() and g.flags.get("chapter4_final_plan_seen",false):g.flags.chapter4_closed=true;g.flags.chapter4_complete=true;g.flags.chapter5_pending=true;g.mode="chapter_end";ui.view="chapter_end"

  _:
   if key.begins_with("fourth_strength_"):
    var id=key.substr(16)
    if g.party.has(id) and not g.is_dying(g.roster[id]) and int(g.flags.get("fourth_strength_uses",0))<3:
     g.roster[id].strength=mini(40,int(g.roster[id].strength)+1);g.flags.fourth_strength_uses=int(g.flags.get("fourth_strength_uses",0))+1
     await pages(h,["旁白："+str(g.roster[id].name_zh)+"力量提升1。祭所剩余"+str(3-int(g.flags.fourth_strength_uses))+"次。"])

static func deliver_light_sword(h) -> void:
 var g=h.ui.game
 if g.Armaments.claim(g,17,false):await h.ui.play_pages(g.Armaments.delivery_pages(17),"hub","")

static func relations(h) -> void:
 var g=h.ui.game;var rows=[];var flags=[]
 if g.route=="alm" and g.stage_cleared(402):
  if g.speaker_alive("达恩") and not g.flags.get("seen_R02",false):
   if not g.parties.celica.has("mireille"):rows+=L.lines("H42","R02",5).slice(0,1)
   elif not g.speaker_alive("米蕾"):rows+=L.lines("H42","R02",2).slice(0,2)
   else:rows+=L.lines("H42","R02",0).slice(0,3)
   flags.append("seen_R02")
  if g.parties.alm.has("lena") and g.parties.alm.has("lance") and not g.flags.get("seen_R06",false):
   if g.speaker_alive("蕾娜") and g.speaker_alive("兰斯"):
    rows+=L.lines("H42","R02",0).slice(3);flags.append("seen_R06")
   elif not g.flags.get("seen_R06_care",false):
    if g.speaker_alive("兰斯"):rows+=L.lines("H42","R02",3);flags.append("seen_R06_care")
    elif g.speaker_alive("蕾娜"):rows+=L.lines("H42","R02",4);flags.append("seen_R06_care")
 if rows.is_empty():rows=L.lines("H42","R02",1)
 await L.say(h,rows,"late:"+",".join(flags) if not flags.is_empty() else "")
