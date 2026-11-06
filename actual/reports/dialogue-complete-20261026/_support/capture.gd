extends SceneTree
const Game=preload("res://reports/dialogue-complete-20261026/_support/no_save.gd")
const Hub=preload("res://reports/dialogue-complete-20261026/_support/hub_capture.gd")
const Endings=preload("res://core/chapter5_endings.gd")
const OUT="res://reports/dialogue-complete-20261026/"
class FakeUI:
 extends RefCounted
 const GameState=preload("res://core/game_state.gd")
 const Progression=preload("res://core/unit_progression.gd")
 var game
 var played=[]
 var notices=[]
 var menus=[]
 var view="hub"
 func play_pages(pages:Array,_return:String="hub",callback:String="",_persist:bool=true):played.append({"pages":pages.duplicate(true),"callback":callback})
 func _notice(text:String,_duration:float=0):notices.append(text)
 func _open_menu(id:String,labels:Array,actions:Array,_at:Vector2):menus.append({"id":id,"labels":labels.duplicate(),"actions":actions.duplicate()})
 func _continue_world():pass
var output={"hub":[],"battle":[],"endings":[]}
var completed=false
var shared_game
func _initialize():call_deferred("run")
func game(chapter:int,route:String="alm"):
 if shared_game==null:shared_game=Game.new()
 var g=shared_game;g.new_game();g.chapter=chapter;g.route=route
 g.parties={"alm":[],"celica":[]}
 for id in g.characters:
  g.roster[id]=g._initial_character(id);var side="alm" if id in ["hunapu","daan","otto","fula","lena","lance","beck","hervi","german"] else "celica"
  g.parties[side].append(id)
 g.party=g.parties[route].duplicate();g.units.clear();g.mode="hub";g.route_positions={"alm":9,"celica":9}
 for key in g.campaign.stages:g.cleared_stages.append(int(key));g.flags["clear_"+str(g.stages[int(key)].code)]=true
 g.flags.chapter3_recruits={"german":true,"noya":true};g.flags.east_recruit_ready={"lord":true,"roan":true,"shia":true}
 g.flags.chapter5_deployment={};g.flags.chapter5_ready={"alm":true,"celica":true}
 g.flags.S31_families={"family0":true,"family1":true};g.flags.survivors_M41={"village0":true,"village1":true,"village2":true}
 g.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}
 g.story_events.clear();return g
func care(g):
 for id in g.roster:
  if id in ["hunapu","eileen"]:continue
  g.roster[id].hp=0;g.roster[id].dying=true;g.roster[id].dead=false
func remove(g,id:String):
 g.party.erase(id);g.parties.alm.erase(id);g.parties.celica.erase(id)
func apply(g,spec:Dictionary):
 for k in spec.get("flags",{}):g.flags[k]=spec.flags[k]
 for id in spec.get("uncleared",[]):g.cleared_stages.erase(int(id));g.flags["clear_"+str(g.stages[int(id)].code)]=false
 if spec.get("care",false):care(g)
 for id in spec.get("injured",[]):g.roster[id].hp=0;g.roster[id].dying=true
 for id in spec.get("remove",[]):remove(g,id)
 for id in spec.get("dead",[]):
  remove(g,id);g.roster[id].hp=0;g.roster[id].dead=true
 if spec.get("not_arrived",false):g.route_positions={"alm":8,"celica":25}
 if spec.get("front",false):g.route_positions={"alm":15,"celica":15}
func capture_hubs():
 var specs=JSON.parse_string(FileAccess.get_file_as_string(OUT+"hub-specs.json"))
 for spec in specs:
  var g=game(int(spec.chapter),str(spec.route));g.hub_record=str(spec.room);g.stage_id=int(spec.get("stage",101));g.battle_data=g.stages[g.stage_id].duplicate(true)
  apply(g,spec)
  var ui=FakeUI.new();ui.game=g;var h=Hub.new(ui);h.room=str(spec.room)
  if int(spec.chapter)==2:h.east_data={"capturing":true}
  if spec.action in ["camp","guard","altar"]:h.objects=[{"action":spec.action,"name":spec.get("object_name","村民"),"text":spec.get("object_text","")}]
  await h.action(str(spec.action))
  if not ui.played.is_empty() or not ui.notices.is_empty() or not ui.menus.is_empty():output.hub.append({"action":spec.action,"room":spec.room,"label":spec.label,"chapter":spec.chapter,"route":spec.route,"played":ui.played,"notices":ui.notices,"menus":ui.menus})
  h.dispose();h=null;ui.game=null;ui=null
func battle_game(id:int,variant:String):
 var stage=shared_game.stages[id];var g=game(int(stage.chapter),str(stage.route) if str(stage.route)!="joint" else "alm")
 for key in ["D31_done","M41_confirmed","F41_confirmed","S41_invited","S42_invited","west_tower_safe","obs_steps_ready","F43_confirmed","M51_confirmed","west_palace_gate","east_network_ready","east_palace_gate","final_access"]:g.flags[key]=true
 g.world_node=int(stage.node);g.cleared_stages.erase(id);g.flags["clear_"+str(stage.code)]=false
 if id==511:g.flags.S51_invited=true
 if id in [533,534]:g.flags.chapter5_merged=true
 if variant=="transfer_cut":g.flags.transfer_cut=true
 for u in stage.npc_units:
  if str(u.id) in g.characters:remove(g,str(u.id))
 if variant in ["care","npc_dead_care"]:care(g)
 var started=g.start_battle(id)
 if not started:push_error("Cannot capture battle "+str(id));return null
 if variant in ["npc_dead","npc_dead_care"]:
  for u in g.units:
   if u.get("neutral",false) and u.side!="enemy":u.hp=0;u.dead=true
 if variant=="shia_unavailable":g.find_unit("shia").hp=0
 if variant=="no_survivors":
  for u in g.units:
   if u.side=="enemy":u.hp=0
 return g
func capture_battles():
 var draft=shared_game
 for key in draft.campaign.stages:
  var id=int(key)
  var variants=["normal","care","npc_dead","no_survivors"]
  if id==408:variants.append("transfer_cut")
  if id==411:variants.append("record_lost")
  if id==204:variants.append("shia_unavailable")
  if id==212:variants.append("npc_dead_care")
  for variant in variants:
   var g=battle_game(int(id),variant)
   if g==null:continue
   var start=g.story_events.duplicate(true);g.story_events.clear()
   var mid=[]
   if int(id)<200:g.queue_lines(str(g.battle_data.during))
   elif int(id)<300:g.queue_lines(g.ChapterTwo._mid_lines(g))
   mid=g.story_events.duplicate(true);g.story_events.clear()
   for obj in g.battle_data.objects:g.flags.quest.objects[str(obj.id)]=true
   if variant=="record_lost":g.flags.quest.record_lost=true;g.flags.quest.objects.black_register=false
   for unit in g.units:
    if int(unit.hp)>0 and unit.get("neutral",false):g.flags.quest.evacuated.append(str(unit.id))
   var boss=g.find_unit(str(g.battle_data.boss_id))
   if not boss.is_empty():boss.hp=0
   g.cleared_stages.append(int(id))
   g.battle_settled=true;g.battle_outcome="victory"
   g.story_on_victory()
   output.battle.append({"id":id,"code":g.battle_data.code,"variant":variant,"start":start,"mid":mid,"after":g.story_events.duplicate(true)})
func capture_endings():
 for profile in ["normal","romance","unrecruited","npc_death","care","care_romance","healed","healed_romance","truths","truths_romance","care_truths","healed_truths","fula_care","beck_archer","beck_rider","beck_soldier","care_used","care_used_romance","care_used_truths"]:
  var g=game(5)
  if profile.contains("romance"):
   for k in ["seen_R01","seen_R02","seen_R03"]:g.flags[k]=true
  if profile.contains("truths"):g.flags.noya_brother_survived=true;g.flags.carlo_promise_completed=true
  if profile.begins_with("care"):care(g)
  if profile.begins_with("care_used"):
   for id in g.roster:
    if id not in ["hunapu","eileen"]:g.roster[id].treatment_count=1
  if profile.begins_with("healed"):
   for id in g.roster:
    if id not in ["hunapu","eileen"]:g.roster[id].treatment_count=1
  if profile in ["unrecruited","npc_death"]:
   for id in g.characters:
    if id in ["hunapu","eileen"]:continue
    remove(g,id)
    if profile=="npc_death":g.roster[id].dead=true;g.roster[id].hp=0
  if profile=="fula_care":g.roster.fula.dying=true;g.roster.fula.hp=0
  if profile.begins_with("beck_"):g.roster.beck.class_id={"beck_archer":12,"beck_rider":20,"beck_soldier":6}[profile]
  output.endings.append({"profile":profile,"pages":Endings.entries(g)})
func run():
 await capture_hubs();capture_battles();capture_endings();completed=true
 var file=FileAccess.open(OUT+"runtime-capture.json",FileAccess.WRITE);file.store_string(JSON.stringify(output,"  "));file.close()
 print("DIALOGUE_CAPTURE_COMPLETE ",output.hub.size()," hubs ",output.battle.size()," battle states ",output.endings.size()," endings profiles");quit(0 if completed else 1)
