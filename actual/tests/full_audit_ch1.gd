extends "res://tests/map_polish_play.gd"
# Isolated real-input first-chapter review. No live attributes or outcomes changed.

const LATE_OUT="res://reports/full-playtest-20261023/ch1/"
var late_label="audit"
var observed_texts=[]
var observed_keys={}
var late_codes:PackedStringArray=[]
var source_checkpoint=""
var late_folder=""
var late_entry_only=false
var late_records=[]
func _initialize():call_deferred("run")
func snapshot(name:String)->void:
 if abort:return
 if not (name.ends_with("-entry") or name.ends_with("-victory") or name.begins_with("after-") or name in ["chapter-end","chapter2-start","chapter3-start"]):return
 if checkpoints.any(func(c):return c.name==name):return
 var old=ui.game.save_path;var path=late_folder+late_label+"-"+name+".json";ui.game.save_path=path
 if not ui.game.save_game():record_failure("Checkpoint write failed: "+name)
 ui.game.save_path=old;checkpoints.append({"name":name,"path":path,"stage":ui.game.stage_id,"turn":ui.game.turn,"view":ui.view})
func write_progress()->void:
 var f=FileAccess.open(late_folder+late_label+"-play.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":failures.is_empty() and not late_records.is_empty() and late_records.all(func(b):return (b.outcome=="victory" or late_entry_only) and b.failures.is_empty()),"entry_only":late_entry_only,"observed_texts":observed_texts,"native_graphics":false,"screenshots":[],"failures":failures,"total_inputs":inputs,"battles":late_records,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"source_saves_modified":false,"route_trace":operations.filter(func(a):return a.get("kind","")=="route trace"),"scope":"Independent genuine deployment checkpoints, ordinary return-to-preparation and current-map reentry, actual input battles and post-battle hub actions; no live attributes, RNG, positions or win conditions edited."},"  "));f.close()
func run()->void:
 if OS.get_cmdline_user_args().has("--continuous"):
  await run_continuous();return
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
  if arg.begins_with("--codes="):late_codes=arg.trim_prefix("--codes=").split(",")
  if arg=="--entry-only":late_entry_only=true
 if late_codes.is_empty():late_codes=["M11","M12","M13","M14","M15","S11","S12"]
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 var sources=State.read_json("res://reports/chapter1-climate-20261022/sources.json")
 sources.M11="res://reports/campaign/natural-M11-deployment-save.json"
 for code in late_codes:
  abort=false;path_cache.clear();risk_cache.clear();var failures_before=failures.size();var inputs_before=inputs
  source_checkpoint=str(sources[code]);var raw=FileAccess.get_file_as_string(source_checkpoint);var source_hash=raw.sha256_text()
  var working=late_folder+"working-"+code+".json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  if not ui.game.load_game():record_failure("Genuine checkpoint failed: "+code)
  if not abort:
   ui._resume_journey();await settle()
   var target_node=ui.game.world_node
   key(KEY_S);choose("new:prepare");await settle()
   await go(target_node)
   if not abort:await prepare_current()
   if not abort:key(KEY_Z);choose("new:battle");await settle()
   if not abort and str(ui.game.battle_data.code)!=code:record_failure("Wrong battle reentered: "+str(ui.game.battle_data.code))
   if not abort:await snapshot(code+"-entry")
   if not abort and late_entry_only:
    key(KEY_S);choose("new:goal");await settle()
    if ui.view!="battle":record_failure("Goal pages did not return control to battlefield: "+code)
  var entry_hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  var b={"entry_map_sha256":entry_hash,"entry_map_revision":ui.game.battle_data.get("tactical_review_version",""),"code":code,"source":source_checkpoint,"source_sha256":source_hash,"outcome":"entry_only","failures":[],"key_inputs":0,"final_turn":0}
  if not abort and not late_entry_only:
   var battle_count=battles.size();await battle(false)
   if battles.size()>battle_count:
    b.merge(battles[-1],true);b.quest=ui.game.flags.quest.duplicate(true)
   if not abort and ui.game.stage_id!=534:
    await post_battle(ui.game.stage_id)
    b.return_view=ui.view;b.return_node=ui.game.world_node
   elif not abort:
    if ui.view!="ending":record_failure("Final victory did not enter ending")
    for page in range(160):
     if abort or ui.game.flags.get("ending_done",false):break
     key(KEY_Z);await settle()
    if not abort and not ui.game.flags.get("ending_done",false):record_failure("Ending did not complete")
    if not abort:await snapshot("ending-complete")
    b.ending_done=ui.game.flags.get("ending_done",false)
  if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Source evidence changed: "+code)
  b.failures=failures.slice(failures_before);b.key_inputs=inputs-inputs_before;b.post_flow_turn=ui.game.turn
  b.map_sha256=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text();b.map_revision=b.entry_map_revision;b.post_flow_map_revision=ui.game.battle_data.get("tactical_review_version","")
  b.final_view=ui.view;late_records.append(b);write_progress()
  print("LATE_MAP_RESULT ",code," ",b.outcome," ",JSON.stringify(b.failures))
  ui.queue_free();await process_frame;await process_frame;ui=null
 write_progress();quit(0 if late_records.all(func(b):return (b.outcome=="victory" or late_entry_only)and b.failures.is_empty())else 1)

func walk_to(at: Vector2i) -> void:
 var start=ui.game.hub_position;var blocked={}
 for o in ui.hub_controller.objects:blocked[Vector2i(o.position[0],o.position[1])]=true
 for d in ui.hub_controller.scenery:
  for y in range(d.rect.position.y,d.rect.end.y):
   for x in range(d.rect.position.x,d.rect.end.x):blocked[Vector2i(x,y)]=true
 var q: Array[Vector2i]=[start];var seen={start:start}
 while not q.is_empty() and not seen.has(at):
  var p=q.pop_front()
  for d in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
   var n=p+d
   if n.x<1 or n.x>12 or n.y<1 or n.y>7 or blocked.has(n) or seen.has(n):continue
   seen[n]=p;q.append(n)
 if not seen.has(at):record_failure("Hub destination blocked: "+str(at));return
 var path: Array=[];var p=at
 while p!=start:path.push_front(p);p=seen[p]
 for n in path:
  var d=n-ui.game.hub_position;key(KEY_RIGHT if d.x>0 else KEY_LEFT if d.x<0 else KEY_DOWN if d.y>0 else KEY_UP)
  if ui.game.hub_position!=n:record_failure("Hub input disagrees with room walk path");return

func hub_action(action: String) -> void:
 var object={}
 for o in ui.hub_controller.objects:
  if str(o.action)==action:object=o;break
 if object.is_empty():
  if action in ui.game.characters and bool(ui.game.roster.get(action,{}).get("dead",false)):
   operations.append({"kind":"dead NPC omitted","id":action});return
  record_failure("Hub object missing: "+action);return
 var at=Vector2i(object.position[0],object.position[1]);var destination=at+Vector2i.DOWN
 walk_to(destination)
 if abort:return
 key(KEY_UP);key(KEY_Z);await settle()
 operations.append({"kind":"facing hub confirmation","room":ui.game.hub_record,"action":action})

func prepare_east()->void:pass
func prepare_current()->void:
 var stage=ui.game.stage_for_node(ui.game.world_node)
 if stage==111:await equip_from_convoy("hunapu",60)
 if stage==105:
  await equip_from_convoy("hunapu",11)
  await equip_from_convoy("otto",2)

func post_battle(stage:int)->void:
 if abort:return
 if stage==104:
  await snapshot("after-"+str(stage));return
 enter_hub();await settle()
 match stage:
  101:
   await hub_action("invite")
  102:
   await hub_action("grain");await hub_action("fula")
   if ui.menu_actions.has("hub:recruit_fula"):choose("hub:recruit_fula");await settle()
  103:
   await hub_action("orders");await hub_action("lena")
   if ui.menu_actions.has("hub:recruit_lena"):choose("hub:recruit_lena");await settle()
   await hub_action("church");await hub_action("cooperate")
  105:
   await hub_action("treat");await hub_action("ceremony")
   if ui.menu_actions.has("hub:ceremony_confirm"):choose("hub:ceremony_confirm");await settle()
   if not ui.game.flags.get("chapter1_complete",false):record_failure("Chapter ceremony did not complete")
   if not abort:await snapshot("chapter-end")
   if not abort:
    key(KEY_Z);choose("new:chapter2");await settle()
    if ui.game.chapter!=2 or ui.view!="hub":record_failure("Chapter1 to Chapter2 transition did not enter eastern hub")
    else:await snapshot("chapter2-start")
   return
  111:
   await hub_action("beck")
   if ui.menu_actions.has("hub:recruit_beck"):choose("hub:recruit_beck");await settle()
  112:
   await hub_action("staff");await hub_action("hervi")
   if ui.menu_actions.has("hub:recruit_hervi"):choose("hub:recruit_hervi");await settle()
 if not abort:await snapshot("after-"+str(stage))
 for i in range(3):
  if abort or ui.view!="hub":break
  await leave_hub()

func act(id:String)->void:
 var u=ui.game.find_unit(id);var before=State.pos(u)if not u.is_empty()else Vector2i.ZERO
 await super.act(id)
 if abort:return
 u=ui.game.find_unit(id)
 if not u.is_empty():operations.append({"kind":"route trace","stage":ui.game.battle_data.code,"turn":ui.game.turn,"unit":id,"from":[before.x,before.y],"to":u.position.duplicate()})
 if ui.game.turn in [4,6,8,12]and not checkpoints.any(func(c):return c.name==str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn)):
  await snapshot(str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn))

func run_continuous()->void:
 late_label="continuous-main"
 var include_sides=OS.get_cmdline_user_args().has("--include-sides")
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/campaign/natural-M11-victory-save.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine M11 completed checkpoint failed")
 if not abort:ui._resume_journey();await settle();key(KEY_Z);choose("continue_world");await settle()
 if include_sides and not abort:
  enter_hub();await hub_action("invite");await leave_hub()
 for code in (["M12","M13","S11","S12","M14","M15"]if include_sides else ["M12","M13","M14","M15"]):
  if abort:break
  var stage={"M12":102,"M13":103,"M14":104,"M15":105,"S11":111,"S12":112}[code]
  await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var failures_before=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  await snapshot(code+"-world-before-entry")
  key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
  var n=battles.size();await battle(false)
  var b={"code":code,"source":source_checkpoint,"source_sha256":source_hash,"scope":"Continuous from genuine M11 completion; all later growth and casualties carried forward","entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
  if battles.size()>n:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(failures_before);b.return_view=ui.view;b.post_flow_turn=ui.game.turn;b.chapter_complete=ui.game.flags.get("chapter1_complete",false)
  late_records.append(b);write_progress()
  print("CH1_CONTINUOUS ",code," ",b.outcome," ",JSON.stringify(b.failures))
 if not abort and ui.view=="chapter_end":
  if ui._first_chapter_winter():record_failure("World did not change after completed ceremony")
  key(KEY_Z);choose("new:chapter2");await settle();await snapshot("chapter2-start")
  if ui.game.chapter!=2 or ui._first_chapter_winter():record_failure("Chapter two did not retain its existing world appearance")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Original M11 record changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)


func key(code:int)->void:
 if ui!=null:
  if ui.view=="plot" and ui.plot_index<ui.plot_pages.size():
   var p=ui.plot_pages[ui.plot_index]
   var fingerprint=str(ui.game.stage_id)+":"+str(p.get("speaker",""))+":"+str(p.get("text",""))
   if not observed_keys.has(fingerprint):
    observed_keys[fingerprint]=true
    var layout=ui._plot_layout(str(p.get("speaker","")))
    var text_width=ui._text_width(str(p.get("text","")));var text_height=ui._text_height(str(p.get("text","")))
    var layout_ok=text_width<=layout.text.size.x and text_height<=layout.text.size.y and layout.panel.encloses(layout.text)
    observed_texts.append({"stage":ui.game.stage_id,"view":ui.view,"speaker":p.get("speaker",""),"text":p.get("text",""),"layout_ok":layout_ok,"text_pixels":[text_width,text_height],"safe_area_pixels":[layout.text.size.x,layout.text.size.y]})
    if not layout_ok:record_failure("Plot text exceeds content safety area at stage "+str(ui.game.stage_id))
  if not ui.menu_items.is_empty():
   var fingerprint=str(ui.game.stage_id)+":"+ui.menu_context+":"+JSON.stringify(ui.menu_items)
   if not observed_keys.has(fingerprint):
    observed_keys[fingerprint]=true
    observed_texts.append({"stage":ui.game.stage_id,"view":ui.view,"menu_context":ui.menu_context,"items":ui.menu_items.duplicate(),"actions":ui.menu_actions.duplicate()})
 super.key(code)

func plan(unit:Dictionary) -> Dictionary:
 if ui.game.stage_id!=111 or ui.game.living("enemy").is_empty():return super.plan(unit)
 var origin=State.pos(unit);var west=ui.game.find_unit("S11_e4");var west_alive=not west.is_empty() and int(west.hp)>0
 var is_bow=str(unit.id)=="daan";var is_guard=str(unit.id)=="otto"
 var goal=Vector2i(6,9) if is_bow else Vector2i(8,8) if is_guard else Vector2i(12,15)
 var goals:Array=[goal]
 if (is_guard or is_bow) and west_alive:
  goals=[]
  for d in ui.game.DIRECTIONS:goals.append(State.pos(west)+d)
 elif (is_guard or is_bow) and int(ui.game.find_unit("S11_boss").hp)>0:
  goals=[]
  var threat=ui.game.find_unit("S11_boss")
  for d in ui.game.DIRECTIONS:goals.append(State.pos(threat)+d)
 elif ui.game.turn>=3:
  var closest={};var distance_=99999
  var miner=ui.game.find_unit("S11_miners0" if is_guard or is_bow else "S11_miners1")
  var anchor=State.pos(miner) if not miner.is_empty() and int(miner.hp)>0 and miner.side=="player" else origin
  for e in ui.game.living("enemy"):
   var n=distance(State.pos(e),anchor)
   if n<distance_:closest=e;distance_=n
  if not closest.is_empty():
   goals=[]
   for d in ui.game.DIRECTIONS:goals.append(State.pos(closest)+d)
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell)
  var progress=12.0*(before-int(field.get(cell,99999)))
  var formation=65.0 if ui.game.turn<=4 and cell==goal and not(is_guard and west_alive) else 0.0
  var walking=progress+formation-danger*.55
  if danger>=int(unit.hp)-2:walking-=200.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    var dist=distance(cell,State.pos(enemy));var reply=Rules.default_counter(enemy,dist)
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var strikes=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var expected=float(stats.damage*strikes)*stats.hit/100.0;var kill=expected>=int(enemy.hp)*.95
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var counter=float(response.damage)*response.hit/100.0*(2 if response.attack_speed>response.defender_attack_speed else 1) if Rules.can_attack(reply,dist) else 0.0
    if counter>=int(unit.hp)-Items.cost(weapon)-1:continue
    var miner_near=999
    for npc in ui.game.living("player"):
     if npc.get("quest_kind","")=="escort":miner_near=mini(miner_near,distance(State.pos(enemy),State.pos(npc)))
    var protected=ui.game.find_unit("S11_miners0" if is_guard or is_bow else "S11_miners1")
    var protected_distance=distance(State.pos(enemy),State.pos(protected)) if not protected.is_empty() else miner_near
    var urgency=maxf(0.0,110.0-float(protected_distance)*18.0)
    if (is_guard or is_bow) and int(ui.game.find_unit("S11_boss").hp)>0:
     urgency+=140.0 if enemy.id in ["S11_boss","S11_e6"] else -200.0
    if (is_guard or is_bow) and west_alive:urgency+=110.0 if enemy.id=="S11_e4" else -30.0
    if is_bow and int(enemy.class_id)==12:urgency+=50.0
    var after_danger=risk(candidate,cell,str(enemy.id) if kill else "")
    var score=minf(expected,enemy.hp)*3.0+(75.0 if kill else 0.0)+urgency+formation*.5+progress*.4-counter-after_danger*.5
    if after_danger+counter>=int(unit.hp)-2:score-=150.0
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best
