extends "res://tests/full_audit_ch1.gd"
## Two targeted native runs, with real touch/keyboard paths and isolated journals.
const FIELD_OUT="res://reports/field-feedback-20261026/"
var screen
var phone
var round_id=1
var checks=[]
var shots=[]
var rounds=[]
var clicks=[]
var jingles=[]
var audio_failures=[]
var records=[]
var rendered=false
var real_combat_seen=false
var skip_capture=false
var cache=""
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append({"round":round_id,"label":label,"passed":ok})
 if not ok:record_failure(label)
func write_progress()->void:
 var f=FileAccess.open(FIELD_OUT+"two-rounds.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":not abort and rounds.size()==2,"native_graphics":rendered,"physical_iphone_tested":false,"iphone_updated":false,"checks":checks,"failures":failures,"rounds":rounds,"screenshots":shots,"jingles":jingles,"audio_failures":audio_failures,"touch_clicks":clicks,"inputs":inputs,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"scope":"Two targeted native runs: grain wagon, plaque depth, touch sounds, new-journal recruitment pause, old-save migration, normal M13 combat and post-battle handovers."},"  "));f.close()
func snapshot(name:String)->void:
 if abort or not name.ends_with("-victory"):return
 var old=ui.game.save_path;var path=FIELD_OUT+"round"+str(round_id)+"-"+name+".json";ui.game.save_path=path
 check(ui.game.save_game(),"actual victory checkpoint saves");ui.game.save_path=old
 checkpoints.append({"name":name,"round":round_id,"path":path})
func settle()->void:
 var until=Time.get_ticks_msec()+120000
 while Time.get_ticks_msec()<until:
  if abort:return
  if not ui.recruitment_paused():
   if ui.view in ["plot","reward"]:key(KEY_Z)
   elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
   if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:
    await process_frame
    if not ui.recruitment_paused() and not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:return
  await process_frame
 record_failure("Control did not return in 120 seconds: "+ui.view)
func shot(name:String)->void:
 if abort or not rendered or skip_capture or shots.any(func(s):return s.name==name):return
 phone._sync_controls();ui.queue_redraw();phone.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
 check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),"safe rendered content: "+name)
 if abort:return
 var path=FIELD_OUT+name+".png";screen.get_texture().get_image().save_png(path);shots.append({"name":name,"path":path,"round":round_id})
func tap(code:int)->void:
 phone._sync_controls()
 for b in phone.buttons:
  if int(b.key)!=code:continue
  var at=phone.safe_area.position+b.hit_rect.get_center()*phone.pixel_scale
  phone._finger(89,at,true);phone._finger(89,at,false);return
 record_failure("Touch button missing: "+str(code))
func walk_to(at:Vector2i)->void:
 var start=ui.game.hub_position;var blocked={}
 for o in ui.hub_controller.objects:
  var size=o.get("footprint",[1,1])
  for y in range(int(o.position[1]),int(o.position[1])+int(size[1])):
   for x in range(int(o.position[0]),int(o.position[0])+int(size[0])):blocked[Vector2i(x,y)]=true
 for d in ui.hub_controller.scenery:
  for y in range(d.rect.position.y,d.rect.end.y):
   for x in range(d.rect.position.x,d.rect.end.x):blocked[Vector2i(x,y)]=true
 var q=[start];var seen={start:start}
 while not q.is_empty() and not seen.has(at):
  var p=q.pop_front()
  for d in ui.game.DIRECTIONS:
   var n=p+d
   if n.x<1 or n.x>12 or n.y<1 or n.y>7 or blocked.has(n) or seen.has(n):continue
   seen[n]=p;q.append(n)
 if not seen.has(at):record_failure("No hub walking path: "+str(at));return
 var path=[];var p=at
 while p!=start:path.push_front(p);p=seen[p]
 for n in path:
  var d=n-ui.game.hub_position;key(KEY_RIGHT if d.x>0 else KEY_LEFT if d.x<0 else KEY_DOWN if d.y>0 else KEY_UP)
  if ui.game.hub_position!=n:record_failure("Actual hub movement disagrees with collision path");return
func setup()->void:
 if screen!=null:
  screen.queue_free();await process_frame;ui=null
 cache="/private/tmp/field-feedback-"+str(Time.get_ticks_usec())+"/"
 DirAccess.make_dir_recursive_absolute(cache)
 screen=SubViewport.new();screen.size=Vector2i(1278,590);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(88,0,1102,558);phone.journal_directory_override=cache;screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.instant_mode=true;clicks=[]
 ui.audio.sfx_played.connect(func(k):clicks.append(k))
 ui.audio.jingle_started.connect(func(k):jingles.append({"round":round_id,"key":k,"ms":Time.get_ticks_msec()}))
 ui.audio.playback_failed.connect(func(k,reason):audio_failures.append({"key":k,"reason":reason}))
func load_own(source:String)->void:
 ui.game.save_path=source;check(ui.game.load_game(),"genuine record loads: "+source.get_file())
 ui.game.save_path=cache+"working.json";ui._resume_journey();await settle()
func touch_and_hub()->void:
 key(KEY_Z);choose("continue_world");await settle();enter_hub();await settle()
 check(ui.game.hub_record=="H02","M12 victory enters grain-station hub")
 walk_to(Vector2i(6,4));key(KEY_UP);check(ui.game.hub_position==Vector2i(6,4),"left wagon half blocks movement")
 walk_to(Vector2i(7,4));var before=clicks.size();tap(KEY_UP)
 check(ui.game.hub_position==Vector2i(7,4),"right wagon half blocks movement")
 check(clicks.size()==before+1,"blocked direction touch still clicks exactly once")
 if round_id==1:await shot("01-wagon-both-cells")
 before=clicks.size();tap(KEY_S);check(clicks.size()==before+1,"menu touch clicks once")
 before=clicks.size();tap(KEY_X);check(clicks.size()==before+1,"back touch does not double its native menu sound")
 before=clicks.size();tap(KEY_LEFT);check(clicks.size()==before+1,"free direction touch clicks once")
 walk_to(Vector2i(10,2));key(KEY_DOWN)
 if round_id==1:await shot("02-plaque-covers-player-behind")
 walk_to(Vector2i(10,4));key(KEY_UP)
 if round_id==2:await shot("06-player-in-front-of-plaque")
 walk_to(Vector2i(7,4));key(KEY_UP);tap(KEY_Z);await settle()
 check(ui.game.flags.get("grain_shared",false),"right half of wagon can also complete grain handover")
 await hub_action("fula")
 check(ui.menu_actions.has("hub:recruit_fula"),"Fula invitation is available after grain handover")
 var count=jingles.size();var at=Time.get_ticks_msec();choose("hub:recruit_fula")
 check(ui.game.party.has("fula") and ui.recruitment_paused() and ui.view=="hub","successful invitation freezes scene before acceptance dialogue")
 check(jingles.size()==count+1 and jingles[-1].key=="rm_jingle_recruit","fresh or loaded game plays exclusive recruitment cue once")
 check(ui.audio._jingle_player.playing and is_equal_approx(ui.audio._jingle_player.stream.get_length(),2.0),"real two-second music stream is playing")
 var position=ui.game.hub_position;var page=ui.plot_index;var clock=ui.hub_controller.clock
 key(KEY_S);key(KEY_UP);key(KEY_Z);tap(KEY_DOWN)
 await create_timer(.35).timeout
 check(ui.game.hub_position==position and ui.view=="hub" and ui.plot_index==page and ui.menu_items.is_empty(),"pause blocks movement, confirmation and menus")
 check(ui.hub_controller.clock==clock,"hub picture animation remains frozen")
 if round_id==1:await shot("03-fula-recruitment-pause")
 while ui.recruitment_paused():await process_frame
 var elapsed=Time.get_ticks_msec()-at
 check(elapsed>=2000 and elapsed<2400,"pause lasts two real seconds: "+str(elapsed)+"ms")
 await settle();await create_timer(.12).timeout
 check(not ui.busy and ui.view=="hub" and not ui.audio._jingle_active and not ui.audio._music_player.stream_paused,"dialogue and map music resume without a stuck busy state: "+str({"busy":ui.busy,"view":ui.view,"jingle":ui.audio._jingle_key,"paused":ui.audio._music_player.stream_paused}))
 ui.game.recruit("fula");check(jingles.size()==count+1,"repeated recruit does not replay success cue")
 await leave_hub();check(ui.view=="world","grain hub remains escapable after invitation")
func equip_from_convoy(id:String,item:int)->void:
 var u=ui.game.roster.get(id,{})
 if u.is_empty() or not ui.game.can_deploy(u) or int(u.get("item_id",0))==item:return
 var index=-1
 for i in range(ui.game.convoy[ui.game.route].size()):
  if int(ui.game.convoy[ui.game.route][i])==item:index=i;break
 if index<0:return
 key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:withdraw");choose("camp:withdraw_item:"+str(index))
 if abort:return
 for i in range(ui.equipment_screen.members.size()):
  if str(ui.equipment_screen.members[ui.equipment_screen.selected])==id:break
  key(KEY_DOWN)
 key(KEY_Z);key(KEY_Z);await settle()
 check(int(ui.game.roster[id].item_id)==item,"normal convoy equipment: "+id)
 if not ui.menu_items.is_empty():key(KEY_X)
func rank(unit:Dictionary)->int:return 4 if int(unit.class_id) in [17,18] else super.rank(unit)
func act(id:String)->void:
 var count=operations.size();ui.instant_mode=real_combat_seen
 await super.act(id)
 for operation in operations.slice(count):
  if operation.get("action",{}).get("kind","") in ["attack","heal"]:real_combat_seen=true
 ui.instant_mode=true
func show_enemy(id:String,filename:String)->void:
 key(KEY_S);choose("enemy_roster")
 for n in range(ui.game.living("enemy").size()+1):
  if ui.status_id==id:break
  key(KEY_RIGHT)
 check(ui.status_id==id,"enemy quick view reaches "+id)
 await shot(filename);key(KEY_X);await settle()
func check_units()->void:
 var boss=ui.game.find_unit("M13_boss")
 check(int(boss.strength)==12 and int(boss.defence)==6 and int(boss.resistance)==2 and int(boss.level)==5 and int(boss.speed)==6,"commander level5 speed6 attack12 physical6 magic2")
 for id in ["M13_e6","M13_e7"]:
  var u=ui.game.find_unit(id)
  check(u.name_zh=="骑兵" and int(u.class_id)==1 and int(u.level)==4 and int(u.speed)==5 and int(u.move)==7 and int(u.strength)==10 and int(u.resistance)==4,"level4 cavalry name/class/speed/move/stats: "+id)
  var graph=ui.game.reachable(u)
  check(graph.costs.values().all(func(v):return int(v)<=7),"cavalry move costs are bounded by seven")
func run()->void:
 rendered=DisplayServer.get_name()!="headless"
 if rendered and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FIELD_OUT))
 if OS.get_environment("FIELD_RESUME")=="2":
  var previous=State.read_json(FIELD_OUT+"first-pass-and-pause-race.json")
  rounds=previous.rounds;checks=previous.checks.filter(func(c):return int(c.round)==1);shots=previous.screenshots;checkpoints=previous.checkpoints;inputs=int(previous.inputs)
 for pass_ in ([2] if OS.get_environment("FIELD_RESUME")=="2" else [1,2]):
  round_id=pass_;real_combat_seen=false;await setup()
  if round_id==1:
   var old=ui.game;key(KEY_Z);key(KEY_Z)
   check(ui.game!=old and ui.game.character_recruited.is_connected(ui._on_character_recruited),"new journal rebinds recruitment signal on replacement game state")
  await load_own("res://reports/dialogue-sync-20261026/play/M12-victory.json")
  if abort:break
  await touch_and_hub()
  if abort:break
  var source="res://reports/dialogue-sync-20261026/play/M13-entry.json" if round_id==1 else "res://reports/campaign/natural-M13-deployment-save.json"
  await load_own(source);check_units()
  var old_hp=int(ui.game.find_unit("M13_boss").hp);check(ui.game.save_game(),"upgraded in-progress battle saves")
  check(ui.game.load_game(),"upgraded battle reloads");check_units();check(int(ui.game.find_unit("M13_boss").hp)==old_hp,"migration keeps wounds and never stacks boosts")
  ui._resume_journey();await settle();key(KEY_S);choose("new:prepare");await settle()
  await go(4);await equip_from_convoy("hunapu",49);await equip_from_convoy("daan",64)
  key(KEY_Z);choose("new:battle");await settle();check_units()
  if round_id==1:await show_enemy("M13_boss","04-commander-new-stats")
  else:await show_enemy("M13_e6","05-level4-cavalry-seven-move")
  if abort:break
  var n=battles.size();await battle(false)
  if abort:break
  check(battles.size()==n+1 and battles[-1].outcome=="victory","normal M13 battle wins in round "+str(round_id))
  await post_battle(103)
  check(ui.game.flags.get("orders_collected",false) and ui.game.flags.get("cooperation_done",false) and ui.game.party.has("lance") and ui.view=="world","orders, invitations, church cooperation and onward route remain unblocked")
  rounds.append({"round":round_id,"source":source,"outcome":battles[-1].outcome,"turn":battles[-1].final_turn,"party":ui.game.party.duplicate(),"real_combat_sample":real_combat_seen,"onward_world":ui.view=="world"});write_progress()
  print("FIELD_ROUND ",round_id," ",JSON.stringify(rounds[-1]))
 if not abort and OS.get_environment("FIELD_RESUME")=="2":
  round_id=1;skip_capture=true;await setup();var old=ui.game;key(KEY_Z);key(KEY_Z)
  check(ui.game!=old and ui.game.character_recruited.is_connected(ui._on_character_recruited),"fresh-journal signal binding rechecked after pause handoff fix")
  await load_own("res://reports/dialogue-sync-20261026/play/M12-victory.json");await touch_and_hub()
  if not abort:rounds[0].post_fix_hub_rechecked=true
 check(audio_failures.is_empty(),"all requested audio paths load and play")
 write_progress();print("FIELD_FEEDBACK ",checks.size()," checks; failures=",JSON.stringify(failures))
 if screen!=null:screen.queue_free();await process_frame;ui=null
 quit(0 if not abort and rounds.size()==2 else 1)
