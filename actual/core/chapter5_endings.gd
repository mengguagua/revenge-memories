extends RefCounted
const L=preload("res://core/late_dialogue.gd")
static func text_at(name:String,index:int=0)->String:
 var result=[]
 for row in L.lines(name,"正文",index):result.append(str(row).trim_prefix("结局文字："))
 return "\n".join(result)
static func entry(name:String,index:int=0,source:int=0)->Dictionary:return {"title":name,"text":text_at(name,index),"source_id":source}
static func entries(g)->Array:
 var result=[entry("日光仍在"),entry("回到岸边")]
 var romance=g.flags.get("seen_R01",false) and g.flags.get("seen_R02",false) and g.flags.get("seen_R03",false)
 for id in ["hunapu","eileen","daan","otto","beck","fula","hervi","lena","lance","german","mireille","lisa","carlo","lord","roan","shia","noya","celine"]:
  var name=str(g.characters[id].name_zh);var unit:Dictionary=g.roster.get(id,{})
  var owned=g.parties.alm.has(id) or g.parties.celica.has(id);var dying=g.is_dying(unit);var treated=int(unit.get("treatment_count",0))>0;var index=0
  var groups=L.groups(name,"正文")
  if not owned:
   var needle="且确有遇难" if unit.get("dead",false) else "未记录遇难"
   for i in range(groups.size()):
    if str(groups[i].condition).contains(needle):index=i;break
  elif id in ["daan","mireille"]:
   index=(2 if dying else 0)+(4 if treated else 0)+(1 if romance else 0)
  elif id=="carlo":
   var promised=g.flags.get("carlo_promise_completed",false)
   index=(7 if treated else 4) if dying and promised else (6 if treated else 1) if dying else (5 if treated else 3) if promised else (2 if treated else 0)
  elif id=="noya":
   var survived=g.flags.get("noya_brother_survived",false)
   index=(9 if treated else 6) if dying and survived else (8 if treated else 3) if dying else (7 if treated else 5) if survived else (4 if treated else 0)
  elif dying or treated:
   for i in range(groups.size()):
    var c=str(groups[i].condition)
    if (dying and c.contains("最终仍濒死") and (c.contains("此前已用") if treated else c.contains("未用过"))) or (not dying and c=="接受过一次救治后正常抵达"):index=i;break
  if owned and not dying:
   if id=="beck" and int(unit.class_id) in [20,6]:index=5 if int(unit.class_id)==20 else 6
   if id=="hervi" and g.parties.alm.has("fula") and g.is_dying(g.roster.fula):index=5
  var item=entry(name,index,int(g.characters[id].get("character_id",0)))
  if owned and id in ["daan","mireille"] and romance and not dying:
   var other="mireille" if id=="daan" else "daan"
   if g.is_dying(g.roster.get(other,{})):item.text=str(item.text).replace("两人后来在靠路的地方找到店面，旁边留了一间诊室。","两人商量过的店和诊室，要等伤养好再办。")
  result.append(item)
 var memorial=L.lines("墓前与医舍","正文",0)
 if g.flags.get("S41_register_saved",false):memorial+=L.lines("墓前与医舍","正文",1)
 memorial+=L.lines("墓前与医舍","正文",2)
 result.append({"title":"墓前与医舍","text":"\n".join(memorial),"source_id":0})
 var outcome=str(g.flags.get("prometheus_outcome",""))
 if outcome in ["maintenance","destroyed"]:result.append(entry("普罗米修斯",0 if outcome=="maintenance" else 1))
 result.append(entry("仍会相见"));result.append(entry("全篇结束"))
 return result
