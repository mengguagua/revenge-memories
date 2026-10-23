extends RefCounted
const Rules=preload("res://core/chapter4_rules.gd")
const Prior=preload("res://core/chapter3_hub.gd")
static func pages(h,lines:Array) -> void:await Prior.pages(h,lines)
static func action(h,key:String) -> void:
 var ui=h.ui;var g=ui.game
 match key:
  "fourth_snow_settle":
   g.flags.M41_confirmed=true
   var count=g.flags.get("survivors_M41",{}).values().filter(func(v):return v).size()
   var text=["医者：登记了"+str(count)+"组存活居民。遇难的人另记姓名，不会从名册上划掉。铁骑关的道路已标出来。"]
   if g.speaker_alive("奥托"):text.append("奥托：我以前也照命令封过这条路。那时我说只负责守口，没有问留下的人怎么活。")
   else:text.append("村民：奥托过去带人封过这条路。军令副本还在黑钟村，不会因他今天不在就失去证据。")
   text.append("胡纳普：我借日塔保护了这些村庄，却一直没问过另一岸发生了什么。先把他们安置好，再去关口。")
   await pages(h,text)
  "fourth_s41":g.flags.S41_invited=true;await pages(h,["村民：黑钟村正在烧失踪者名册，旧军令里有凯尔和奥托的名字。支路从雪峡村分出去。"])
  "fourth_transfer_report":await pages(h,["工匠：投送站已停止。北境日塔还依赖现有设备，先夺取控制室，等观测台给出步骤再停用。", "信使：东岸的信按战前军情登记。已经落地的敌军仍需应对，之后的船队也会因此少受一次拦截。"])
  "fourth_tower_shutdown":
   if g.flags.get("west_tower_safe",false):await pages(h,["工匠：西塔已安全停用，村庄照明稳定。王都道路已开放；要核对另一端，切到东队的祭所调节庭。"]);return
   if not g.flags.get("obs_steps_ready",false):await pages(h,["工匠：控制室由我们驻守，不必重打。缺少东岸盐原观测台的完整步骤。", "提示：按S切到东队，完成沙城与盐原观测台；信使会送来步骤，再返回本控制室确认。"]);return
   await pages(h,["工匠：依观测步骤，先隔离远端，再分段降流。南口村庄的照明仍然稳定。", "胡纳普：等病人的照护处也检查完，再撤最后一班守卫。", "工匠：三次读数相符，可以安全停用。王都的路已打开。"])
   g.flags.west_tower_safe=true;Rules.promote_hero(g,"hunapu")
   await pages(h,["旁白：胡纳普进阶为破晓勇士，基础移动由5提升至6，可装备相容的剑与弓。", "旁白：进阶按最低基底补足属性，保留已有更高值。等级、经验、当前生命与原有训练不变。"])
  "fourth_herlan":await pages(h,["赫兰：他们跟着我守住西岸。我以为只要再等到大典，就能安排剩下的人。", "胡纳普：另一岸的人已经等不下去。你先照看伤兵，把命令和名单留下。"])
  "fourth_well_report":g.flags.F41_confirmed=true;await pages(h,["居民：南北井台的水够这一批人转移。古道路线已抄成几份，就算向导不在，也能沿标记找到观测台。", "艾琳：留一份在井台。不要让后来的人再空走一趟。"])
  "fourth_obs_report":await pages(h,["技术员：停用步骤已经发给西队。祭所坐标在这份副本上，穿过亡潮沼泽就能到。", "艾琳：母亲没能验证完的部分，我们继续查。不能只因为她相信这条路，就让别人冒同样的险。"])
  "fourth_marsh_report":g.flags.F43_confirmed=true;await pages(h,["船团医者：居民已按实际获救名单交接，船分批运送，不占正式成员的物品槽。", "舵手：古道连接沉没祭所。西南孤岛还有两组病人等待接应。"])
  "fourth_s42":g.flags.S42_invited=true;await pages(h,["舵手：赛琳留在沼泽孤岛守着两组病人。支路从这里分开，船可以在西南木台靠岸。", "舵手：岛上守船人还保管着雾中护航用的定潮枪。先把病人安置好，他会把旧枪交给继续守路的人。"])
  "fourth_island_verify":
   var first=not g.flags.get("chapter4_promoted_eileen",false)
   Rules.promote_hero(g,"eileen")
   var text=["地方技术员：局部隔离试验已成功。三个调节点由留守工匠接手，不需要远征队一直站在那里。", "艾琳：先保护住这里的人。等西塔也安全停下，再读两岸的确认信。"]
   if first and g.flags.get("chapter4_promoted_eileen",false):
    text.append_array(["旁白：艾琳进阶为引光剑使，基础移动提升至5，按最低基底补足属性与抗性。等级、经验、当前生命和原有法术训练保留。", "旁白：术法精熟使已学攻击法术每次减耗1生命，正费用最低为1；辅助法术费用不变。试验不代替同伴救治。"])
   else:text.append("旁白：艾琳已掌握地方循环的调节步骤。原有法术训练保留，试验不代替同伴救治。")
   await pages(h,text)
   await deliver_light_sword(h)
  "fourth_d42":
   if g.flags.get("D42_done",false):await pages(h,["信使：两岸验证已完成。最后一份救治材料已送往H10会合营站，和早期剩余份额一起使用。"]);return
   if not g.flags.get("west_tower_safe",false):await pages(h,["信使：祭所的局部试验已成功，但还缺西塔安全停用的回信。切到西队，回北境日塔控制室确认，不必重打。"]);return
   if not g.flags.get("island_loop_safe",false):return
   var text=[("莉莎" if g.speaker_alive("莉莎") else "地方技术员")+"：日塔那边停了。这里的灯还亮着。", "艾琳：再看一会儿。别急着把船叫回来。", ("米蕾" if g.speaker_alive("米蕾") else "船团医者")+"：岸边的人已经看见了。有人在问，今晚能不能住在自己家里。", "艾琳：先让修塔的人检查。等他们说可以，我们再去告诉大家。", "技术员：两岸的读数稳定，居民可以回到已经检查过的房屋。", "运输人员：最后一份救治材料送往会合营站。伤者会与我们一起转移，不会被留在这里。"]
   await pages(h,text);g.flags.D42_done=true;Rules.promote_hero(g,"eileen");g.ensure_treatment_sources()
   await deliver_light_sword(h)
  "fourth_black_report":await pages(h,["村民：完整名册已经存档。凯尔先执行迁徙、后违令救人的前后记录都留下了。" if g.flags.get("S41_register_saved",false) else "村民：名册没能保住。在场者的证言会留下，已经烧毁的内容不能假装仍然完整。", "胡纳普：我还是想知道他最后看见了什么。但不能只记我愿意相信的那一面。"])
  "fourth_celine":
   if g.party.has("celine"):await pages(h,["赛琳：地方医者会接手病人。我跟船团走，先把照护安排写清楚。"]);return
   if not g.flags.get("celine_ready",false):await pages(h,["地方医者：赛琳没能活着离开诊疗处。病人已经按实际获救名单安置，我们继续照护。"]);return
   await pages(h,["赛琳：两组病人都安置好了，地方医者会留下。我可以跟你们同行，照护后面的船。", "艾琳：把交接记清楚，你也不必一个人负责所有人。"])
   ui._open_menu("recruit",["邀请赛琳同行","留在诊疗处"],["hub:fourth_recruit_celine","close"],Vector2(36,88))
  "fourth_recruit_celine":
   if g.flags.get("celine_ready",false):g.recruit("celine");h.enter_room(h.room,true)
  "fourth_vya":await pages(h,["地方医者：维娅当年急着证明航线，船还没备齐就出海。有几条船再也没有回来。", "艾琳：把失去的人和后来获救的人都留下。她救过我，我也不能替她删掉那些名字。"])
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
   await pages(h,["信使："+"；".join(missing)+"。"] if not missing.is_empty() else ["信使：王都、日塔与祭所均已完成。两队可回营站整理物资，准备下一段路。"])
  "third_messenger":
   if not Rules.missing(g).is_empty():await action(h,"fourth_progress");return
   var unfinished=[]
   if not g.stage_cleared(411):unfinished.append("黑钟村名册")
   if not g.stage_cleared(412):unfinished.append("沼泽孤岛救援（定潮枪尚未取得）")
   if not unfinished.is_empty():await pages(h,["信使：尚未完成："+"、".join(unfinished)+"。可先返回支路，再确认本章收束。"])
   ui._open_menu("fourth_end",["继续整备","确认第四章收束"],["close","hub:fourth_finish"],Vector2(36,88))
  "fourth_finish":
   if Rules.missing(g).is_empty():g.flags.chapter4_closed=true;g.flags.chapter4_complete=true;g.flags.chapter5_pending=true;g.mode="chapter_end";ui.view="chapter_end"
  _:
   if key.begins_with("third_transfer_"):await Prior.action(h,key)
   elif key.begins_with("fourth_strength_"):
    var id=key.substr(16)
    if g.party.has(id) and not g.is_dying(g.roster[id]) and int(g.flags.get("fourth_strength_uses",0))<3:
     g.roster[id].strength=mini(40,int(g.roster[id].strength)+1);g.flags.fourth_strength_uses=int(g.flags.get("fourth_strength_uses",0))+1
     await pages(h,["旁白："+str(g.roster[id].name_zh)+"力量提升1。祭所剩余"+str(3-int(g.flags.fourth_strength_uses))+"次。"])

static func deliver_light_sword(h) -> void:
 var g=h.ui.game
 if g.Armaments.claim(g,17,false):await h.ui.play_pages(g.Armaments.delivery_pages(17),"hub","")

static func relations(h) -> void:
 var g=h.ui.game;var text=[]
 if g.route=="alm" and g.stage_cleared(402):
  if g.party.has("daan") and g.speaker_alive("达恩") and not g.flags.get("seen_R02",false):
   if g.parties.celica.has("mireille") and g.roster.mireille.get("dying",false):
    text.append_array(["达恩：这包干净的布和纸，请交给船团医者。米蕾在照护处，也请把这封信带给她。", "信使：会一起送到。照护处会回信告诉你她的近况。"])
   elif g.parties.celica.has("mireille"):
    text.append_array(["达恩：我用自己的零钱买了些布和纸。请替我送给米蕾，她一直在找干净的。", "信使：收到。你写的这几行也放进去？", "达恩：放进去。告诉她，我还在学那些店名。"])
   else:text.append("达恩：把这些布交给当地医者。后面的船总会用得上。")
   g.flags.seen_R02=true
  if g.party.has("lena") and g.party.has("lance") and not g.flags.get("seen_R06",false):
   if g.speaker_alive("蕾娜") and g.speaker_alive("兰斯"):
    text.append_array(["蕾娜：这些遗物的名字，我都认得。你还想回原来的军队吗？", "兰斯：我想先把信送回家。旧军队也不能替我们回答今天做了什么。", "蕾娜：那就分头写。投降者的交代和遇难者的遗物，分别登记。"]);g.flags.seen_R06=true
   elif g.speaker_alive("兰斯"):
    text.append_array(["兰斯：给家属的信我先送。蕾娜还在照护处，请把她的近况单独写清楚。", "信使：会按伤情写，不会把她当作遇难者。"]);g.flags.seen_R06_care=true
   elif g.speaker_alive("蕾娜"):
    text.append("蕾娜：给家属的信我先送。兰斯留在照护处，别把他的近况和战亡名单混在一起。");g.flags.seen_R06_care=true
 if text.is_empty():text.append("信使：两岸的来信按实际情况登记。旧同袍的姓名、伤情与责任，都会留下。")
 await pages(h,text)
