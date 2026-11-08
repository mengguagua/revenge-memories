extends RefCounted
const L=preload("res://core/late_dialogue.gd")
const FALLBACKS={"米蕾":"船医","莉莎":"甲板护卫","卡洛":"固定舵手","洛德":"引航者","罗恩":"舵手","希雅":"留守骑士","蕾娜":"城外军官","达恩":"居民","兰斯":"运输工","芙拉":"工匠","奥托":"村民"}
static func begin(g,code:String)->Array:
 var rows=L.lines(code,"开场")
 if code in ["F23","F25","M32","F32","F33","F42","F51"]:rows+=L.lines(code,"开场",1)
 if code=="F21":
  if g.units.any(func(u):return g.Mechanical.is_water(u)):rows+=L.lines(code,"开场",1)
  rows+=L.lines(code,"开场",2)
 if code=="S21" and not g.speaker_alive("米蕾"):rows=L.lines(code,"开场",1)
 if code=="S22" and not g.speaker_alive("卡洛"):rows=L.lines(code,"开场",1)
 if code=="F22" and not g.speaker_alive("卡洛"):
  for i in range(rows.size()):
   if str(rows[i]).begins_with("艾琳：卡洛"):rows[i]=L.lines(code,"开场",1)[0]
 if code=="M42" and not g.speaker_alive("兰斯"):
  rows=rows.filter(func(s):return not str(s).begins_with("兰斯：") and not str(s).begins_with("胡纳普：去吧"))
 if code=="S31" and not g.speaker_alive("蕾娜"):rows=L.lines(code,"开场",1)
 if code in ["M31","M41","M43","S41"]:
  var who={"M31":"蕾娜","M41":"奥托","M43":"芙拉","S41":"奥托"}[code]
  if not g.speaker_alive(who):
   for i in range(rows.size()):
    if str(rows[i]).begins_with(who+"："):rows[i]=L.lines(code,"开场",1)[0]
 if code=="M32" and not g.speaker_alive("兰斯"):
  rows[0]=L.lines(code,"开场",2)[0];rows[2]=L.lines(code,"开场",2)[1]
 if code=="F32":
  if not g.speaker_alive("罗恩"):rows[0]=L.lines(code,"开场",2)[0]
  if not g.speaker_alive("卡洛"):rows[3]=L.lines(code,"开场",2)[1]
  rows+=L.lines(code,"开场",2).slice(2)
 if code=="F43":
  if not g.speaker_alive("米蕾"):rows[3]=L.lines(code,"开场",1)[0]
  if not g.speaker_alive("卡洛"):rows[4]=L.lines(code,"开场",1)[1]
 return rows
static func ending(g,code:String)->Array:
 var index=0
 if code=="F23" and not g.speaker_alive("罗恩"):index=1
 if code=="F25":index=1
 if code=="S32" and not g.speaker_alive("诺娅"):index=1
 if code=="S41" and not g.flags.get("S41_register_saved",false):index=1
 if code=="S42" and not g.speaker_alive("赛琳"):index=1
 if code=="S22":
  index=(0 if g.speaker_alive("卡洛") else 1)+(0 if g.flags.get("old_sailor_rescued",false) else 2)
 var rows=L.lines(code,"胜利",index)
 # Armament presentation is queued by the actual reward transaction.
 if code in ["F24","F33","S42","S51"]:rows=rows.slice(0,1)
 if code=="F24" and not g.speaker_alive("希雅"):rows=L.lines(code,"胜利",1)
 if code=="M52":rows=rows.slice(0,2)
 if code in ["S21","M31"]:rows+=L.lines(code,"胜利",1)
 if code=="F33":rows+=L.lines(code,"医舍")
 if code=="F42":rows+=L.lines(code,"维瑟")
 # A dead guide cannot supply a route; the mandatory well conversation reads his notes.
 return L.narrative(rows)
static func resolve(g,original:Array,key:String)->Array:
 if g.chapter<2 or key.is_empty():return original
 var code=str(g.battle_data.get("code",""));var rows=[];var found=true
 if not L.data().has(code):return original
 if code=="F44" and not g.Mechanical.is_prometheus(g.find_unit(str(g.battle_data.boss_id))):return original
 if key==code+"-BEGIN":rows=begin(g,code)
 elif key==code+"-END":rows=ending(g,code)
 elif key.ends_with("-ENEMY-ROLES") or key in ["D41","M42-LANCE","411-ACCESSORY-HINT","501-ACCESSORY-HINT","M52-ARMAMENT-HINT","S51-ARMAMENT-HINT"]:return []
 elif key.ends_with("-VISIT"):
  for heading in L.data().get(code,{}):
   if str(heading).begins_with("战场访问"):rows=L.lines(code,heading);break
  if rows.is_empty():return original
 elif key in ["F21-MID","F22-MID","F23-MID","F25-MID","S21-MID","S22-MID"]:
  var i=0
  if code=="F22" and not g.speaker_alive("洛德"):i=1
  if code in ["S21","S22"] and not g.speaker_alive("米蕾" if code=="S21" else "卡洛"):i=1
  if code=="S22" and not g.ChapterThree.alive(g,"old_sailor"):return []
  rows=L.lines(code,"战中推进",i)
 elif key=="F24-MID":rows=L.lines(code,"战中推进",2 if not g.ChapterThree.alive(g,"islanders") else (1 if g.speaker_alive("希雅") else 3))
 elif key=="F26-MID":rows=L.lines(code,"战中推进",1 if g.speaker_alive("卡洛") else 2)
 elif key=="D22-FIRST":rows=L.lines("F25","D22_FIRST")
 elif key=="D22-DEFEAT":rows=L.lines("F25","胜利",0)
 elif key=="F44-SNAPSHOT":
  var list=L.lines("F44","开场",1)
  rows=list.slice(2) if g.flags.quest.get("transfer_cut_snapshot",false) else list.slice(0,2)
 elif key=="S32-BROTHER":rows=[L.lines("S32","战中交互")[0 if g.ChapterThree.alive(g,"noya_brother") else 1]]
 elif key.begins_with("old_unit:"):rows=L.lines("S31","战中交互")
 elif key.begins_with("ward_") and key.ends_with("-OPEN"):rows=L.lines("M51","战中交互")
 elif key.begins_with("repair_") and key.ends_with("-WORK"):rows=L.lines("F51","战中交互",0)
 elif key.begins_with("repair_") and key.ends_with("-COMPLETE"):rows=L.lines("F51","战中交互",1)
 elif key=="CH4-FIRE-FIRST":rows=L.lines(code,"战中交互",1 if code=="S41" else 4)
 elif key.ends_with("-FIRE-WARNING") and code in ["S41","F42"]:rows=L.lines(code,"战中交互",2 if code=="S41" else 5)
 else:
  var events={"F24-BEACON-WARNING":["F24",0],"F26-BOAT-HIT":["F26",0],"M31-MID":["M31",0],"M32-MID":["M32",0],"M32-RELEASE":["M32",1],"M33-SURRENDER":["M33",0],"M33-OFFER":["M33",1],"F31-MID":["F31",0],"F32-MID":["F32",0],"F33-MID":["F33",0],"F33-RECORD":["F33",1],"M42-PARLEY":["M42",0],"M42-CUT":["M42",1],"M43-CONTROL":["M43",0],"F42-ORDER":["F42",0],"F42-RECORD":["F42",1],"F42-MYTH":["F42",2],"F42-NOYA":["F42",3],"S41-TRUTH":["S41",0],"S42-TRUTH":["S42",0],"M44-MID":["M44",0],"M44-SURRENDER":["M44",1],"F43-ORDER":["F43",0],"F43-SUMMON":["F43",1],"F44-TEST":["F44",1],"M52-ORDER":["M52",0],"S51-ORDER":["S51",0],"S51-TRUTH":["S51",1],"J54-PHASE":["J54",0]}
  if events.has(key):rows=L.lines(events[key][0],"战中交互",events[key][1])
  else:found=false
 if not found:return original
 return L.pages(g,rows,FALLBACKS)

static func after_action(g)->void:
 if g.stage_id!=206 or g.flags.get("seen_F26-OWL-CHASE",false):return
 for u in g.units:
  if not g.Mechanical.is_owl(u) or int(u.hp)<=0 or u.get("escaped",false):continue
  for boat in g.flags.quest.get("boats",[]):
   if int(boat.hp)<=0 or boat.get("arrived",false) or int(boat.path_index)>=boat.path.size()/2:continue
   var cell=Vector2i(boat.position[0],boat.position[1])
   if maxi(absi(g.pos(u).x-cell.x),absi(g.pos(u).y-cell.y))<=3:
    L.queue(g,L.lines("F26","战中推进",0),"F26-OWL-CHASE");return
