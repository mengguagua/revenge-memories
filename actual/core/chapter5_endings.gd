extends RefCounted
## Ending facts come from the real final roster and recorded choices, never a repaired cast.
static func entries(g) -> Array:
 var result=[{"title":"日光仍在","text":"神座的实体倒下，晨光仍照着海峡。各地已经接手的循环继续运转。裂开的土地没有合拢，失去的人也没有回来。","source_id":0},{"title":"回到岸边","text":"先回去的是接应的船。人们清点伤者、姓名与物资，再修屋顶和渡口。两岸交换记录；早年的救援和后来的伤害，都没有从档案中删去。","source_id":0}]
 var stories={
 "hunapu":"胡纳普回到凯尔的墓前，讲起这一趟路上听到的证言。他继续训练，也学习照看粮道。几年后，人们再见到他时，他正在护送重建的车队。",
 "eileen":"艾琳把新航线画在母亲的旧图旁。她继续学习风向与各地循环。几年后，往返两岸的航路稳定了，她与同伴开设航海课堂。",
 "daan":"达恩把沿途欠下的物资逐一登记。他开始寻找靠近道路的店面，学着把交易写得更清楚。",
 "otto":"奥托回到雪原，帮助修路与分粮。他保存自己执行过的命令，也继续听被迫离乡的人说话。",
 "beck":"贝克把军旅中学到的本领用在新的护送工作中。他仍会向老同伴请教，职业的变化没有替他决定要成为什么人。",
 "fula":"芙拉参与整理两岸的药物与诊疗记录。地方诊所开始互通消息，治疗不再只依赖一座神殿。",
 "hervi":"赫维把观测步骤交给各地的学堂和工匠。他与芙拉继续交换笔记，让后来的人能核对、修正他们的办法。",
 "lena":"蕾娜留下监督王都安置与问责。赫兰协助照护伤兵、交代军令；投降没有免除责任，也没有被写成新的英雄事迹。",
 "lance":"兰斯护送孩子与教师回到村庄。遇到旧同袍时，他仍问起那些未完成的交代。",
 "german":"格曼参与工房重建，补还拖欠的物资。押送名单上仍有他的名字，受害者可以继续向他问责。",
 "mireille":"米蕾帮助沿路诊所整理药物。她把信件与货单放在一起，留出时间学习新的治疗记录。",
 "lisa":"莉莎参与训练年轻护卫，也继续救援失船。经过诊所时，她会停下来看看米蕾，把港口的近况带给她。",
 "carlo":"卡洛回到船上，继续做护航和接应的工作。每次离港，他都会重新清点救生物资和船上的人。",
 "lord":"洛德回到海边，帮助修复航路与村落。他仍在寻找失散者的消息，没有把未经证实的音信写成团聚。",
 "roan":"罗恩恢复村庄间的小规模贸易。船上的药物和粮食都有清单，价格也会交给村民共同核对。",
 "shia":"希雅继续在岛间巡航。她把获救者送往各地照护处，再教新的护卫辨认危险的海面。",
 "noya":"诺娅交出完整路线与泄密经过。她帮助旧船团恢复航行，也继续接受幸存者的追问。",
 "celine":"赛琳回到孤岛诊疗处，与留下的医者轮流出航。病人的名字和转运去向仍逐项登记。"}
 var order=["hunapu","eileen","daan","otto","beck","fula","hervi","lena","lance","german","mireille","lisa","carlo","lord","roan","shia","noya","celine"]
 var romance=g.flags.get("seen_R01",false) and g.flags.get("seen_R02",false) and g.flags.get("seen_R03",false)
 for id in order:
  var u:Dictionary=g.roster.get(id,{});var owned=g.parties.alm.has(id) or g.parties.celica.has(id);var text=str(stories[id])
  if not owned:
   text="这次同行名册中没有"+str(g.characters[id].name_zh)+"。"+("当地记录保留了未能获救的消息；结局没有改写那场伤亡。" if not u.is_empty() and u.get("dead",false) else "重建者会继续登记散落各地的消息，没有把未发生的同行写进这段旅程。")
  elif g.is_dying(u):
   text=str(u.name_zh)+"仍在原队的照护名册中，暂时无法恢复原来的工作。"+("此前已经使用过一次救治，" if int(u.get("treatment_count",0))>0 else "")+"同伴和地方人员接手了眼前的事务。重建开始了，照护也继续。"
   if id=="lena":text+="投降军官与居民代表代为监督王都问责。"
   if id in ["daan","mireille"] and romance:text+="靠路的店与诊所仍是两人共同说过的打算，先照顾好眼前的人。"
  else:
   if int(u.get("treatment_count",0))>0:text="接受救治后，"+str(u.name_zh)+"活着走到了旅程终点。"+text
   if id in ["daan","mireille"] and romance:text+="两人后来在靠路的地方找到店面，旁边留了一间诊室。" if g.can_deploy(g.roster.daan) and g.can_deploy(g.roster.mireille) else "两人说过的店与诊室仍留在计划里，眼下先陪伴需要休养的那个人。"
   if id=="noya":text+="弟弟已经交给照护处。" if g.flags.get("noya_brother_survived",false) else "弟弟未能归来，他的名字仍留在那份名册上。"
   if id=="carlo":text+="交还遗物时许下的送信约定，仍写在他的航程里。" if g.flags.get("carlo_promise_completed",false) else "没能完成的交接仍是遗憾，他没有替遗属写下原谅。"
  if owned and id=="beck" and g.can_deploy(u):
   var work={12:"他带着弓守护粮车，也教村里的年轻人辨认目标与距离。",13:"他带着弓守护粮车，也教村里的年轻人辨认目标与距离。",20:"他沿长路巡行，为往返车队探查险处。",6:"他参与修路和护送，让伤者能平安抵达村庄。"}
   text+=str(work.get(int(u.class_id),"他把现有职业的本领用在地方护卫与重建中。"))
  if owned and id=="hervi" and g.can_deploy(u) and g.roster.has("fula") and g.is_dying(g.roster.fula):text="赫维把观测步骤交给学堂和工匠，托诊疗人员保存他与芙拉的旧笔记。芙拉仍需照护，眼前的研究与教学由他和地方人员接手。"
  if owned and id=="noya" and g.is_dying(u):text+="她弟弟已经交给照护处。" if g.flags.get("noya_brother_survived",false) else "弟弟未能归来，他的名字仍在那份名册上。"
  if owned and id=="carlo" and g.is_dying(u) and g.flags.get("carlo_promise_completed",false):text+="船员继续代送他许诺带出的信件。"
  result.append({"title":str(g.characters[id].name_zh),"text":text,"source_id":int(g.characters[id].get("character_id",0))})
 result.append({"title":"仍会相见","text":"几年后，胡纳普与艾琳又约好在眠谷见面。两人各有自己的道路，也愿意走到对方的岸边。日光之下，生活仍需要人们亲手照看。","source_id":0})
 result.append({"title":"全篇结束","text":"第五章完成。两队的成长、装备、伤情与这次结局已保存。再次继续旅程，可从保存的结局页阅读。","source_id":0})
 return result
