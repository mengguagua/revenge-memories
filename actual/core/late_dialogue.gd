extends RefCounted
## Quoted script, with explicit branch selection. Stage directions are never spoken.
static var cache:Dictionary={}
static func data()->Dictionary:
 if cache.is_empty():cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/dialogue_ch2_5.json")).sections
 return cache
static func groups(area:String,heading:String)->Array:
 var matches=[]
 for key in data().get(area,{}):
  if str(key).begins_with(heading):matches.append(key)
 assert(matches.size()==1,"Ambiguous/missing dialogue: "+area+" / "+heading)
 return data()[area][matches[0]] if matches.size()==1 else []
static func lines(area:String,heading:String,index:int=0)->Array:
 var list=groups(area,heading)
 assert(index>=0 and index<list.size(),"Missing dialogue group: "+area+" / "+heading+" / "+str(index))
 return list[index].lines.duplicate() if index>=0 and index<list.size() else []
static func join_groups(area:String,heading:String,indices:Array)->Array:
 var result=[]
 for i in indices:result.append_array(lines(area,heading,int(i)))
 return result
static func pages(g,rows:Array,fallbacks:Dictionary={})->Array:
 var result=[]
 for row in rows:
  var parts=str(row).split("：",true,1)
  if parts.size()!=2:continue
  var speaker=str(parts[0]);var text=str(parts[1])
  if speaker.contains("或"):
   var names=speaker.split("或");speaker=names[0] if g.speaker_alive(names[0]) else names[-1]
  if not g.speaker_alive(speaker):
   if not fallbacks.has(speaker):continue
   speaker=str(fallbacks[speaker])
  result.append({"speaker":speaker,"text":text.replace("{获救组数}",str(g.flags.get("survivors_M41",{}).values().filter(func(v):return v).size()))})
 return result
static func narrative(rows:Array)->Array:
 # Rewards are displayed by the existing receipt, after they are actually granted.
 return rows.filter(func(s):return not (str(s).begins_with("旁白：") and (str(s).contains("已收入") or str(s).contains("战后整理"))))
static func say(h,rows:Array,callback:String="",fallbacks:Dictionary={})->void:
 await h.ui.play_pages(pages(h.ui.game,rows,fallbacks),"hub",callback)
static func queue(g,rows:Array,key:String,fallbacks:Dictionary={})->void:
 g.queue_pages(pages(g,narrative(rows),fallbacks),key)
static func member(g,name:String)->bool:
 for id in g.characters:
  if str(g.characters[id].name_zh)==name:return (g.parties.alm.has(id) or g.parties.celica.has(id)) and g.speaker_alive(name)
 return false
static func outcome(g,area:String,heading:String,maintenance:int,destroyed:int)->Array:
 var value=str(g.flags.get("prometheus_outcome",""))
 if value=="maintenance":return lines(area,heading,maintenance)
 if value=="destroyed":return lines(area,heading,destroyed)
 # A save from before this boss existed must not invent a choice the player never made.
 return []
static func finish(h,callback:String)->void:
 var g=h.ui.game
 for key in callback.trim_prefix("late:").split(",",false):
  g.flags[key]=true
  match key:
   "M33_confirmed":g.Armaments.claim(g,18,false)
   "west_tower_safe":g.ChapterFour.promote_hero(g,"hunapu")
   "island_handover_seen","D42_done":
    g.ChapterFour.promote_hero(g,"eileen");g.Armaments.claim(g,17,false)
   "H55_letters_seen":pass
 g.ensure_treatment_sources()
