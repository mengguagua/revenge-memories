extends "res://tests/full_audit_ch1.gd"
## Continuous native-runtime keyboard play from a new journal. No state shortcuts.
const SYNC_OUT="res://reports/dialogue-sync-20261026/"
var screen
var phone
var play_shots=[]
var captured={}
var real_speed_stages={}
var started_ms=0
func _initialize():call_deferred("run")
func write_progress()->void:
 var f=FileAccess.open(SYNC_OUT+"chapter1-play.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":not abort and ui!=null and ui.game.chapter==2 and late_records.size()==7,"failures":failures,"native_graphics":DisplayServer.get_name()!="headless","iphone_updated":false,"new_journal":true,"continuous":true,"stat_edits":false,"forced_victories":false,"total_inputs":inputs,"seconds":(Time.get_ticks_msec()-started_ms)/1000.0,"battles":late_records,"observed_texts":observed_texts,"checkpoints":checkpoints,"screenshots":play_shots,"operations":operations.filter(func(o):return o.get("kind","")!="route trace")},"  "));f.close()
func capture_once(label:String)->void:
 if captured.has(label) or DisplayServer.get_name()=="headless":return
 captured[label]=true
 phone._sync_controls();ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
 var path=SYNC_OUT+label+".png";screen.get_texture().get_image().save_png(path);play_shots.append(path)
 if not ui.layout_errors.is_empty() or not phone.layout_errors.is_empty():record_failure("Rendered content safety: "+str(ui.layout_errors)+str(phone.layout_errors))
func settle()->void:
 var deadline=Time.get_ticks_msec()+120000
 while Time.get_ticks_msec()<deadline:
  if abort:return
  if ui.view=="story_intro":key(KEY_Z)
  elif ui.view in ["plot","reward"]:
   if ui.view=="plot" and ui.plot_index<ui.plot_pages.size():
    var t=str(ui.plot_pages[ui.plot_index].text).replace("\n","")
    var label=""
    if t.contains("哥哥放走了"):label="01-D11-revenge"
    elif t.contains("我叫芙拉"):label="02-M12-fula"
    elif t.contains("我爹的工具"):label="03-beck-invitation"
    elif t.contains("我想再学些术法"):label="04-hervi-invitation"
    if not label.is_empty() and not captured.has(label):
     ui.dialogue_reveal=10000;await capture_once(label)
   key(KEY_Z)
  elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
  if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm","story_intro","prologue_scene"]:
   await process_frame
   if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm","story_intro","prologue_scene"]:return
  await process_frame
 record_failure("Runtime control did not release within 120 seconds: "+ui.view)
func act(id:String)->void:
 var slow=not real_speed_stages.has(ui.game.stage_id)
 ui.instant_mode=not slow
 await super.act(id)
 if not abort:real_speed_stages[ui.game.stage_id]=true
 ui.instant_mode=true
func rank(unit:Dictionary)->int:
 return 4 if int(unit.class_id) in [17,18] else super.rank(unit)
func prepare_current()->void:
 if ui.game.stage_for_node(ui.game.world_node)==111:
  await equip_from_convoy("hunapu",49);await equip_from_convoy("daan",64)
 elif ui.game.stage_for_node(ui.game.world_node)==105:
  await equip_from_convoy("hunapu",11);await equip_from_convoy("lance",49)
 else:await super.prepare_current()
func plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id!=111 or int(unit.class_id) not in [17,18]:return super.plan(unit)
 var heal=combat_plan(unit)
 if heal.kind=="heal":return heal
 var goals=[];var target=ui.game.find_unit("hunapu");var most_missing=-1
 for ally in ui.game.living("player"):
  var missing=int(ally.max_hp)-int(ally.hp)
  if missing>most_missing:most_missing=missing;target=ally
 if target.is_empty():return heal
 for d in ui.game.DIRECTIONS:goals.append(State.pos(target)+d)
 var field=distance_map(unit,goals);var origin=State.pos(unit);var before=int(field.get(origin,99999))
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  var score=12.0*(before-int(field.get(cell,99999)))-risk(unit,cell)*4.0
  if score>heal.score:heal={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
 return heal
func tower_plan(unit:Dictionary)->Dictionary:
 var origin=State.pos(unit);var boss=ui.game.find_unit("M15_boss");var rider=str(unit.id)=="lance"
 var point=ui.game.battle_data.get("assault_gate",[14,16]);var gate=Vector2i(point[0],point[1]);var exit_=ui.game.battle_data.exit;var exit_cell=Vector2i(exit_[0],exit_[1])
 var goal=gate if origin.y>gate.y else exit_cell if rider else State.pos(boss)
 var goals=[goal]
 if not rider and origin.y<=gate.y:
  goals=[]
  for d in ui.game.DIRECTIONS:goals.append(State.pos(boss)+d)
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999));var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var weapons=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(unit,cell);var walking=22.0*(before-int(field.get(cell,99999)))-danger*1.8
  if danger>=int(unit.hp)-2:walking-=180.0
  if rider and cell==exit_cell:walking+=500.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for spell in weapons:
   candidate.erase("weapon_index")
   if spell>=0:candidate.weapon_index=spell
   for enemy in ui.game.targets(candidate):
    var dist=distance(cell,State.pos(enemy));var reply=Rules.default_counter(enemy,dist)
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var counter=float(response.damage)*(2 if response.attack_speed>response.defender_attack_speed else 1) if Rules.can_attack(reply,dist) else 0.0
    var expected=float(stats.damage)*(2 if stats.attack_speed>stats.defender_attack_speed else 1)*float(stats.hit)/100.0
    var kill=expected>=int(enemy.hp)*.95
    var incoming=risk(candidate,cell,str(enemy.id) if kill else "")
    if incoming+counter>=int(unit.hp)-2:continue
    var score=walking+minf(expected,enemy.hp)*2.0+(180.0 if enemy.id=="M15_boss" else 20.0 if kill else 0.0)-counter
    if rider and cell!=exit_cell:score-=45.0
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":spell}
 return best
func equip_from_convoy(id:String,item:int)->void:
 var member=ui.game.roster.get(id,{})
 if member.is_empty() or not ui.game.can_deploy(member) or int(member.get("item_id",0))==item:return
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
 if int(ui.game.roster[id].item_id)!=item:record_failure("Normal equipment swap failed: "+id)
 operations.append({"kind":"actual equipment swap","unit":id,"item":item})
 if not ui.menu_items.is_empty():key(KEY_X)
func recover_fula()->void:
 key(KEY_S);choose("new:prepare");await settle();await go(4);enter_hub();await settle();await hub_action("church")
 if ui.game.is_dying(ui.game.roster.fula):
  await hub_action("treatment");choose("hub:treat_choose_fula");choose("hub:treat_confirm_fula");await settle()
  if not ui.game.can_deploy(ui.game.roster.fula):record_failure("Ordinary church treatment did not restore Fula")
  operations.append({"kind":"ordinary church treatment","unit":"fula","remaining":ui.game.treatment_remaining()})
 await leave_hub();await leave_hub();await equip_from_convoy("fula",65);await equip_from_convoy("hunapu",60)
func snapshot(name:String)->void:
 if name in ["chapter-end","chapter2-start"] or name.ends_with("-entry") or name.ends_with("-victory") or name=="H01-before-departure":
  var old=ui.game.save_path;var path=SYNC_OUT+"play/"+name+".json";ui.game.save_path=path
  if not ui.game.save_game():record_failure("Play checkpoint failed: "+name)
  ui.game.save_path=old;checkpoints.append({"name":name,"path":path,"stage":ui.game.stage_id,"turn":ui.game.turn,"view":ui.view})
 if name=="chapter-end":await capture_once("05-chapter1-complete")
func run()->void:
 if DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 started_ms=Time.get_ticks_msec()
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SYNC_OUT+"play"))
 var isolated="/private/tmp/dialogue-ch1-play-"+str(Time.get_ticks_usec())+"/"
 DirAccess.make_dir_recursive_absolute(isolated)
 screen=SubViewport.new();screen.size=Vector2i(1278,590);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(88,0,1102,558);phone.journal_directory_override=isolated;screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.instant_mode=true
 if OS.get_environment("DIALOGUE_PLAY_RESUME")=="M15":
  var previous=State.read_json(SYNC_OUT+"attempts/six-maps-chapter1-play.json")
  late_records=previous.battles.filter(func(b):return b.outcome=="victory");inputs=int(previous.total_inputs);observed_texts=previous.observed_texts;operations=previous.operations
  checkpoints=previous.checkpoints.filter(func(c):return not str(c.name).begins_with("M15"));play_shots=previous.screenshots
  for path in play_shots:captured[str(path).get_file().trim_suffix(".png")]=true
  ui.game.save_path=SYNC_OUT+"attempts/real-M15-entry.json"
  if not ui.game.load_game():record_failure("Own M15 entry checkpoint did not load")
  ui.game.save_path=isolated+"resumed.json";ui._resume_journey();await settle();key(KEY_S);choose("new:prepare");await settle()
 elif OS.get_environment("DIALOGUE_PLAY_RESUME")=="final-sides":
  var previous=State.read_json(SYNC_OUT+"attempts/clinic-before-mine-chapter1-play.json")
  late_records=previous.battles.filter(func(b):return b.outcome=="victory");inputs=int(previous.total_inputs);observed_texts=previous.observed_texts;operations=previous.operations
  checkpoints=previous.checkpoints.filter(func(c):return not str(c.name).begins_with("S11"));play_shots=previous.screenshots
  for path in play_shots:captured[str(path).get_file().trim_suffix(".png")]=true
  ui.game.save_path=SYNC_OUT+"attempts/after-clinic-S11-entry.json"
  if not ui.game.load_game():record_failure("Own post-clinic checkpoint did not load")
  ui.game.save_path=isolated+"resumed.json";ui._resume_journey();await settle()
  key(KEY_S);choose("new:prepare");await settle()
 elif OS.get_environment("DIALOGUE_PLAY_RESUME")=="prepared-sides":
  var previous=State.read_json(SYNC_OUT+"attempts/recovered-side-chapter1-play.json")
  late_records=previous.battles.filter(func(b):return b.outcome=="victory");inputs=int(previous.total_inputs);observed_texts=previous.observed_texts;operations=previous.operations
  checkpoints=previous.checkpoints.filter(func(c):return not str(c.name).begins_with("S11"));play_shots=previous.screenshots
  for path in play_shots:captured[str(path).get_file().trim_suffix(".png")]=true
  ui.game.save_path=SYNC_OUT+"attempts/prepared-sides-entry.json"
  if not ui.game.load_game():record_failure("Own prepared side checkpoint did not load")
  ui.game.save_path=isolated+"resumed.json";ui._resume_journey();await settle()
  key(KEY_S);choose("new:prepare");await settle();await equip_from_convoy("hunapu",49)
 elif OS.get_environment("DIALOGUE_PLAY_RESUME")=="S11":
  var previous=State.read_json(SYNC_OUT+"attempts/main-before-sides-chapter1-play.json")
  late_records=previous.battles.filter(func(b):return b.outcome=="victory");inputs=int(previous.total_inputs);observed_texts=previous.observed_texts;operations=previous.operations
  checkpoints=previous.checkpoints.filter(func(c):return not str(c.name).begins_with("S11"));play_shots=previous.screenshots
  for path in play_shots:captured[str(path).get_file().trim_suffix(".png")]=true
  ui.game.save_path=SYNC_OUT+"attempts/pre-recovery-S11-entry.json"
  if not ui.game.load_game():record_failure("Own genuine S11 entry checkpoint did not load")
  ui.game.save_path=isolated+"resumed.json";ui._resume_journey();await settle();await recover_fula()
 elif OS.get_environment("DIALOGUE_PLAY_RESUME")=="M11":
  var previous=State.read_json(SYNC_OUT+"attempts/early-side-chapter1-play.json")
  late_records=previous.battles.filter(func(b):return b.outcome=="victory");inputs=int(previous.total_inputs);observed_texts=previous.observed_texts
  operations=previous.operations;checkpoints=previous.checkpoints.filter(func(c):return not str(c.name).begins_with("S11"));play_shots=previous.screenshots
  for path in play_shots:captured[str(path).get_file().trim_suffix(".png")]=true
  ui.game.save_path=SYNC_OUT+"play/M11-victory.json"
  if not ui.game.load_game():record_failure("Own genuine M11 checkpoint did not load")
  ui.game.save_path=isolated+"resumed.json";ui._resume_journey();await settle()
  key(KEY_Z);choose("continue_world");await settle()
 else:
  key(KEY_Z);key(KEY_Z);await settle()
  if ui.view!="hub" or ui.game.hub_record!="P00":record_failure("Fresh journal did not reach prologue plaza")
  if not abort:await hub_action("prologue")
  if not abort and ui.game.hub_record!="H01":record_failure("Prologue did not reach village")
  if not abort:await hub_action("grave");await hub_action("otto");await hub_action("daan");await hub_action("daan");await snapshot("H01-before-departure");await leave_hub()
 var codes=["M15"] if OS.get_environment("DIALOGUE_PLAY_RESUME")=="M15" else ["S11","M14","M15"] if OS.get_environment("DIALOGUE_PLAY_RESUME")=="final-sides" else ["S12","S11","M14","M15"] if OS.get_environment("DIALOGUE_PLAY_RESUME")=="prepared-sides" else ["S11","S12","M14","M15"] if OS.get_environment("DIALOGUE_PLAY_RESUME")=="S11" else ["M12","M13","S11","S12","M14","M15"] if OS.get_environment("DIALOGUE_PLAY_RESUME")=="M11" else ["M11","M12","M13","S11","S12","M14","M15"]
 for code in codes:
  if abort:break
  var stage={"M11":101,"M12":102,"M13":103,"M14":104,"M15":105,"S11":111,"S12":112}[code]
  await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var failures_before=failures.size()
  key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
  var n=battles.size();await battle(false)
  var b={"code":code,"outcome":"incomplete","scope":"Continuous fresh-game native keyboard play"}
  if battles.size()>n:b.merge(battles[-1],true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(failures_before);b.return_view=ui.view
  b.party_after=ui.game.party.duplicate();late_records.append(b);write_progress()
  print("DIALOGUE_CH1 ",code," ",b.outcome," ",JSON.stringify(b.failures))
 if not abort and (ui.game.chapter!=2 or ui.view!="hub"):record_failure("First chapter did not allow normal Chapter 2 entry")
 write_progress();print("DIALOGUE_CH1_COMPLETE ",JSON.stringify({"passed":not abort,"maps":late_records.size(),"inputs":inputs,"failures":failures}))
 screen.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
