extends RefCounted
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
  "fifth_ward_report":
   g.flags.M51_confirmed=true
   await Prior.pages(h,["照护者：获救组别和遇难者分别登记。赫兰留在这里交代命令、协助照护，未加入出阵队伍。","胡纳普：通往登天桥的路已经标好。"])
  "fifth_west_report":await Prior.pages(h,["守卫：西门已经打开。另一队从祭所底层与日宫下层进入东门。两队分别到达前庭后，再确认出阵。"])
  "fifth_repair_report":await Prior.pages(h,["技术员：地方循环已稳定。日宫下层的东门阵仍有守军，沿北廊过去就能找到。"])
  "fifth_east_report","fifth_archive_invite":await Prior.pages(h,["记录官：旧书库在日宫下层的侧路。前庭确认两军合流出发以后，这条支路会关闭。", "记录官：那里还封存着曾保护撤离队伍的镇关枪。记录交接后，会把它交给继续守路的人。" if not g.Armaments.claimed(g,7) else "记录官：镇关枪已经交付。记录与兵器的去向都已登记。", "艾琳：先决定是否查阅记录，再带两队去前庭。"])
  "fifth_archive_report":await Prior.pages(h,["记录官：救援与失败都留在记录里。这份档案不会替强迁、拒绝救船和清洗开脱。"])
  "fifth_prepare":open_selection(h)
  "fifth_ready":
   g.flags.chapter5_ready[g.route]=true;ui._notice("本队名单已确认；按S切换另一队确认",6)
  "fifth_merge":
   if g.flags.get("chapter5_merged",false):
    await Prior.pages(h,["守卫：前庭已成为共同整备点。可切换两队分配各自行囊与剩余救治。" ,"守卫：沿北方道路前往神座。" if g.flags.get("final_access",false) else "守卫：从南口返回地图，进入前庭战场。"]);return
   if int(g.route_positions.alm)!=15 or int(g.route_positions.celica)!=15:
    await Prior.pages(h,["守卫：两队都要先到前庭。按S切换另一队，完成对应门阵并沿地图道路抵达。"]);return
   if not g.flags.chapter5_ready.alm or not g.flags.chapter5_ready.celica:ui._notice("请先分别确认两队出阵名册",6);return
   await Prior.pages(h,["守卫：确认后，两队合流前往前庭，旧书库支路将关闭。", "守卫：记录已经取回。" if g.stage_cleared(511) else "守卫：旧书库尚未探索，镇关枪尚未取得。现在可以返回日宫下层。"])
   ui._open_menu("fifth_merge",["返回整理","确认合流出发"],["close","hub:fifth_confirm_merge"],Vector2(24,96))
  "fifth_confirm_merge":
   if g.ChapterFive.merge(g):h.enter_room("H55",true);ui._notice("两军已合流；南口返回地图进入战场",6)
   else:ui._notice("名单或抵达状态已变化，请重新确认",6)
  "fifth_relationship":
   if g.flags.get("seen_R03",false):
    await Prior.pages(h,["达恩：地方我们回来再找。" if g.speaker_alive("达恩") and g.speaker_alive("米蕾") else "照护者：那间店和诊室仍是他们一起说过的打算，眼下先照顾伤者。"]);return
   if not g.flags.get("seen_R01",false) or not g.flags.get("seen_R02",false) or not g.speaker_alive("达恩") or not g.speaker_alive("米蕾") or int(g.route_positions.alm)!=15 or int(g.route_positions.celica)!=15:
    await Prior.pages(h,["照护者：伤情与未完成的约定都保留在名册里。有人还需要休养，不能替他们说出尚未说过的话。"]);return
   g.flags.seen_R03=true
   await Prior.pages(h,["米蕾：你说过，打完之后要开店。","达恩：嗯。还没想好在哪一边。","米蕾：别开在码头最里面。病人走不到那里。","达恩：那我找一间靠路的。旁边再留一间？","米蕾：先把这里的东西收好。有人在等我们分药。","达恩：好。地方我们回来再找。"])
static func open_selection(h) -> void:
 var g=h.ui.game;var selected=g.ChapterFive.selection(g,g.route);var labels=[];var actions=[]
 for id in g.party:
  if not g.can_deploy(g.roster[id]):continue
  labels.append(("出阵 · " if selected.has(id) else "留守 · ")+str(g.roster[id].name_zh));actions.append("hub:fifth_toggle_"+str(id))
 labels.append(("确认西队名单" if g.route=="alm" else "确认东队名单")+"（%d/10）"%selected.size());actions.append("hub:fifth_ready")
 h.ui._open_menu("fifth_selection",labels,actions,Vector2(32,48))
