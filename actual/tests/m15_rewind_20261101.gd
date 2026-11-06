extends SceneTree
const State=preload("res://core/game_state.gd")
const Tasks=preload("res://core/current_task.gd")
const OUT="res://reports/m15-rewind-20261101/"
var checks=[];var errors=[];var shots=[];var visual=false;var screen;var phone;var ui
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func same(a,b)->bool:return JSON.stringify(a)==JSON.stringify(b)
func battle(id:int=105):
 var g=State.new();g.new_game();g.save_path="/private/tmp/m15-rewind-20261101/domain.json";g.world_node=int(g.stages[id].node);g.previous_world_node=5 if id==105 else 3;g.route_positions.alm=g.world_node
 check(g.start_battle(id),"start battle "+str(id));g.story_events.clear();return g
func advance(g):
 g.story_events.clear();g.next_phase();g.story_events.clear();g.next_phase();g.story_events.clear()
func frame(name:String):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" glyph and border safe areas: "+str(ui.layout_errors)+str(phone.layout_errors))
  screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func data_checks():
 var g=battle();var s=g.stages[105];var boss=g.find_unit("M15_boss")
 check(s.enemies.size()==15,"M15 still has fifteen enemies")
 check(boss.class_id==22 and boss.level==5 and boss.max_hp==40 and boss.strength==16 and boss.skill==4 and boss.speed==3 and boss.luck==0 and boss.defence==11 and boss.resistance==5 and boss.move==4,"Korlan has exact requested base stats and bastion movement")
 var heavy=g.find_unit("M15_e1")
 check(heavy.class_id==2 and heavy.level==5 and heavy.max_hp==28 and heavy.strength==12 and heavy.skill==2 and heavy.speed==2 and heavy.luck==0 and heavy.defence==9 and heavy.resistance==2,"one soldier is genuine armored infantry with exact stats")
 for id in ["M15_e6","M15_e7","M15_e8"]:
  var u=g.find_unit(id)
  check(u.name_zh=="骑士" and u.class_id==4 and u.level==4 and u.max_hp==30 and u.strength==8 and u.skill==2 and u.speed==5 and u.luck==0 and u.defence==4 and u.resistance==3 and u.move==8,id+" corrected from gold knight to requested knight")
 check(not s.enemies.any(func(u):return u.class_id==7),"no gold knights remain in M15")
 var old_stage=State.read_json(OUT+"before/actual/data/stages/M15.json");var old=old_stage.enemies+old_stage.reinforcements
 var ledger=State.read_json(OUT+"enemy-changes.json")
 for growth in ledger.bonus:
  var u=(s.enemies+s.reinforcements).filter(func(x):return x.id==growth.id)[0];var base=old.filter(func(x):return x.id==growth.id)[0];var delta=0
  for k in ["max_hp","strength","skill","speed","defence","resistance"]:delta+=int(u[k])-int(base[k])
  check(delta==3 and u.level==5 and u.luck==base.luck and u.move==base.move,growth.id+" gets exactly three fixed random points, level5, exclusions intact")
 old[0].hp=20;old[1].hp=0
 for u in old:u.enemy_balance_revision=9
 var original=old.duplicate(true);g.EnemyBalance.prepare(105,old)
 check(old[0].hp==28 and old[0].max_hp==40 and old[0].class_id==22,"migration preserves twelve missing HP on Korlan")
 check(old[1].hp==0 and old[1].class_id==2,"migration preserves dead soldier while correcting class")
 var once=old.duplicate(true);g.EnemyBalance.prepare(105,old);check(same(old,once),"repeat migration cannot stack stats")
 g.units=g.units.filter(func(u):return u.side=="player")+original.slice(0,15);g.battle_start_snapshot.units=g.units.duplicate(true);g.battle_rewind={}
 var locations=g.units.map(func(u):return u.position.duplicate());g.turn=4;g.flags.quest.reinforced=true
 check(g.save_game(),"legacy in-progress M15 fixture saves")
 var loaded=State.new();loaded.save_path=g.save_path
 check(loaded.load_game(),"legacy in-progress M15 loads")
 check(loaded.turn==4 and same(loaded.units.map(func(u):return u.position),locations) and loaded.find_unit("M15_boss").hp==28,"load preserves turn, formation and wounds while applying stats")
 check(loaded.battle_start_snapshot.units.filter(func(u):return u.id=="M15_boss")[0].class_id==22,"retry checkpoint receives identical enemy migration")
 check(not loaded.Rewind.reason(loaded).is_empty(),"legacy turn4 does not fabricate turn3 history")
 advance(loaded);check(not loaded.Rewind.reason(loaded).is_empty(),"first new boundary cannot invent missing old turn")
 advance(loaded);check(loaded.Rewind.reason(loaded).is_empty(),"second new boundary makes actual previous turn available")
 g=State.new();g.new_game();g.flags.prologue_done=true;g.flags.village_ready=true;g.flags.grain_shared=true;g.flags.orders_collected=true;g.flags.cooperation_done=true;g.cleared_stages=[101,102,103]
 check(Tasks.entry(g).text.contains("旧塔外营") and not Tasks.entry(g).text.contains("骑兵营"),"task before M14 uses actual camp name")
 g.cleared_stages.append(104);g.world_node=5;g.mode="world"
 check(Tasks.entry(g).text.contains("海峡城") and Tasks.entry(g).text.contains("旧塔堡") and not Tasks.entry(g).text.contains("前往旧塔外营"),"M14 victory journal points to M15 in strait city")
 check(g.world_neighbors().has(6) and g.stage_for_node(6)==105,"journal target agrees with unlocked world route")
 check(not g.Training.choices(g).is_empty() and g.Training.remaining(g)==2,"chapter1 training available after M13 with two successes")
 check(not g.world_has_battle(2) and g.world_armies.is_empty(),"cleared map points have no formal campaign roaming encounter")
func rewind_checks():
 var g=battle();check(g.Rewind.reason(g).contains("第1回合"),"turn1 cannot rewind or consume a use")
 check(not g.Rewind.commit(g) and g.Rewind.remaining(g)==2,"invalid rewind consumes nothing")
 var start=g.battle_rewind.starts[0].duplicate(true);var original_map=g.battle_data.map.tiles.duplicate()
 var hero=g.find_unit("hunapu");hero.hp-=3;hero.acted=true;hero.exp=47;hero.position=[15,19]
 g.find_unit("M15_e2").hp=0;g.kills=1;g.rng_state=137;g.frame_counter=88;g.convoy.alm.append(11)
 g.flags.pending_loot=[{"kind":"loot","unit_id":"M15_e2","item_id":11,"route":"alm"}]
 var door=g.battle_data.objects.filter(func(o):return o.kind in ["door","rescue"])[0]
 g.flags.quest.objects[str(door.id)]=true;g.battle_data.map.tiles[int(door.position[1])*int(g.battle_data.map.width)+int(door.position[0])]=int(door.get("open_tile",208))
 advance(g);check(g.turn==2 and g.battle_rewind.starts.size()==2,"phase boundary records turn2 after resets and effects")
 var recorded=g.battle_rewind.starts[1].duplicate(true);g.find_unit("hunapu").acted=true;g.find_unit("hunapu").hp-=1;g.Rewind.record(g)
 check(same(recorded,g.battle_rewind.starts[1]),"duplicate capture cannot overwrite untouched boundary")
 check(g.Rewind.commit(g),"rewind turn2 to genuine turn1 persists atomically")
 check(g.turn==1 and g.phase=="player" and g.living("player").all(func(u):return not u.acted),"rewind restores previous player start with no action spent")
 for field in ["units","roster","convoy","flags","kills","rng_state","frame_counter"]:check(same(g.get(field),start[field]),"rewind restores "+field)
 check(same(g.battle_data.map.tiles,original_map),"rewind closes opened door and restores map tiles")
 check(g.Rewind.remaining(g)==1 and g.battle_rewind.starts.size()==1,"rewind consumes one use and discards abandoned future")
 var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game() and loaded.Rewind.remaining(loaded)==1 and loaded.turn==1,"load preserves used count and restored round")
 advance(loaded);loaded.find_unit("hunapu").hp-=2
 check(loaded.Rewind.commit(loaded) and loaded.Rewind.remaining(loaded)==0,"second rewind works after replayed round")
 advance(loaded);var before=loaded.Rewind._capture(loaded)
 check(not loaded.Rewind.commit(loaded) and same(before,loaded.Rewind._capture(loaded)),"third rewind is rejected without mutating battle")
 check(loaded.save_game(),"spent rewind budget saves")
 var again=State.new();again.save_path=loaded.save_path;check(again.load_game() and again.Rewind.remaining(again)==0,"reload cannot refund spent budget")
 g=battle();advance(g);advance(g);advance(g);g.next_phase()
 check(g.find_unit("M15_r0").get("level",0)==5 and g.find_unit("M15_r1").get("level",0)==5,"M15 actual fourth enemy phase spawns level5 reinforcements")
 check(g.save_game(),"spawned reinforcements and rewind history save together")
 g=battle();advance(g);advance(g);advance(g)
 check(g.battle_rewind.starts.map(func(s):return int(s.turn))==[2,3,4],"history bounded to three genuine starts")
 check(g.Rewind.commit(g) and g.turn==3 and g.Rewind.commit(g) and g.turn==2,"consecutive rewinds step back one round each")
 check(g.retry_battle() and g.turn==1 and g.Rewind.remaining(g)==2 and g.battle_rewind.starts.size()==1,"whole-battle retry starts new two-use attempt")
 g=battle();advance(g);g.save_path="/private/tmp/m15-rewind-20261101/missing/path/save.json";before=g.Rewind._capture(g);var history=g.battle_rewind.duplicate(true)
 check(not g.Rewind.commit(g) and same(before,g.Rewind._capture(g)) and same(history,g.battle_rewind),"failed save restores battle and budget")
 g.save_path="/private/tmp/m15-rewind-20261101/valid.json";check(g.save_game(),"rewind history survives ordinary save validation")
 var disk=State.read_json(g.save_path)
 for kind in ["bad_used","wrong_stage","acted_start","invalid_hp","future_turn","nested_history"]:
  var bad=disk.duplicate(true)
  match kind:
   "bad_used":bad.battle_rewind.used=3
   "wrong_stage":bad.battle_rewind.stage=104
   "acted_start":bad.battle_rewind.starts[0].units[0].acted=true
   "invalid_hp":bad.battle_rewind.starts[0].units[0].hp=-1
   "future_turn":bad.battle_rewind.starts[0].turn=99
   "nested_history":bad.battle_rewind.starts[0].battle_rewind={}
  check(not g.SaveValidation.campaign_valid(g,bad,g.SAVE_FIELDS),"corrupt rewind rejected: "+kind)
 disk.erase("battle_rewind");check(g.SaveValidation.campaign_valid(g,disk,g.SAVE_FIELDS),"old checkpoint without history remains valid")
 var f=FileAccess.open(g.save_path,FileAccess.WRITE);f.store_string(JSON.stringify(disk));f.close()
 loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game() and loaded.Rewind.reason(loaded).is_empty(),"old turn2 can use genuine original turn1 retry boundary")
 g=battle(101);g.battle_outcome="";g.mode="world";g.units.clear();g.battle_start_snapshot={};g.cleared_stages=[101,102,103];g.world_node=4;g.route_positions.alm=4
 check(g.Training.start(g,191),"training enters through actual rules")
 g.story_events.clear();advance(g)
 check(g.Rewind.commit(g) and g.Training.active(g) and g.Rewind.remaining(g)==1,"training rewind restores its own battle without affecting story")
 check(g.Training.leave(g) and g.battle_rewind.is_empty() and g.Training.remaining(g)==2,"leaving training clears battle history and preserves training quota")
func cross_chapter_checks():
 var cases=["campaign-final-r4/ch2/chain-F22-victory.json","campaign-final-r4/ch3/chain-M32-victory.json","campaign-final-r4/ch4/chain-F43-victory.json","campaign-final-r5/ch5/chain-J54-victory.json"]
 for source in cases:
  var g=State.new();g.save_path="res://reports/full-assessment-20261025/"+str(source)
  check(g.load_game(),"cross chapter source loads: "+source)
  g.save_path="/private/tmp/m15-rewind-20261101/cross-"+str(g.stage_id)+".json"
  check(g.retry_battle(),"cross chapter ordinary retry starts fresh: "+str(g.stage_id))
  g.story_events.clear();advance(g);var start=g.battle_rewind.starts[-1].duplicate(true);var tiles=g.battle_data.map.tiles.duplicate()
  var target=int(g.turn);advance(g);g.find_unit(g.leader_id()).hp-=1
  check(g.Rewind.commit(g) and g.turn==target,"cross chapter rewind persists: "+str(g.stage_id))
  check(same(g.units,start.units) and same(g.flags,start.flags) and same(g.battle_data.map.tiles,tiles),"cross chapter restores units, quest, transport/summons and geometry: "+str(g.stage_id))
  var r=State.new();r.save_path=g.save_path
  check(r.load_game() and r.Rewind.remaining(r)==1 and r.turn==target,"cross chapter rewind reloads: "+str(g.stage_id))
 var g=battle(101);var a=g.find_unit("hunapu");var b=g.living("enemy")[0];a.position=[3,10];b.position=[4,10]
 var initial=g.battle_rewind.starts[0].duplicate(true)
 var exchange=g.plan_combat(a.id,b.id);check(not exchange.is_empty() and not exchange.events.is_empty(),"rewind combat fixture uses genuine combat plan")
 for event in exchange.get("events",[]):g.commit_strike(event)
 g.finish_exchange(exchange);check(a.acted,"genuine exchange spends player action")
 advance(g);check(g.Rewind.commit(g) and same(g.units,initial.units) and g.rng_state==int(initial.rng_state),"rewind reverses genuine combat damage, EXP, action and random consumption")
func run():
 DirAccess.make_dir_recursive_absolute("/private/tmp/m15-rewind-20261101/slots")
 visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
 data_checks();rewind_checks();cross_chapter_checks()
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override="/private/tmp/m15-rewind-20261101/slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.game=battle();ui.game.save_path="/private/tmp/m15-rewind-20261101/ui.json";ui.game.story_events.clear();ui.view="battle";ui.ui_mode="inspect";ui.busy=false
 ui._open_system_menu();check(ui.menu_actions[1]=="new:rewind" and ui.menu_items[1].contains("剩余2次"),"battle menu places rewind directly below end turn");await frame("menu-turn1")
 ui._clear_menu();advance(ui.game);ui.game.find_unit("hunapu").acted=true;ui._open_system_menu();await frame("menu-turn2")
 ui._clear_menu();ui._menu_action("new:rewind","system");check(ui.menu_context=="rewind_confirm" and ui.game.turn==2,"rewind opens confirmation without changing state");await frame("rewind-confirm")
 ui._clear_menu();ui._menu_action("new:rewind_cancel","rewind_confirm");check(ui.game.turn==2 and ui.game.Rewind.remaining(ui.game)==2,"cancel preserves round and budget")
 ui._clear_menu();ui._menu_action("new:rewind_commit","rewind_confirm");await process_frame
 check(ui.game.turn==1 and ui.ui_mode=="inspect" and ui.game.Rewind.remaining(ui.game)==1,"actual UI commit restores inspect mode and remaining counter");await frame("rewound")
 for id in ["M15_boss","M15_e1","M15_e6","M15_e9"]:
  ui._clear_menu();ui.ui_mode="status";ui.status_id=id;await frame("status-"+id)
  var profession=ui.game.catalog.classes[str(int(ui.game.find_unit(id).class_id))].name_zh
  check(not visual or ui.presentation_audit.get("status_profession")==profession,"status profession matches actual class: "+id)
 ui.ui_mode="inspect";ui.view="world";ui.game.mode="world";ui.game.flags.prologue_done=true;ui.game.flags.village_ready=true;ui.game.flags.grain_shared=true;ui.game.flags.orders_collected=true;ui.game.flags.cooperation_done=true;ui.game.cleared_stages=[101,102,103,104]
 ui._menu_action("new:tasks","world_system");await frame("task-after-M14");check(ui.field_notes.record.text.contains("海峡城"),"actual journal UI points to strait city");ui.field_notes.cancel()
 ui._open_camp_menu();check(ui.menu_items.any(func(x):return str(x).contains("补练")),"actual preparation menu exposes training");await frame("training-entry")
 if visual:
  screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout();ui._clear_menu();ui.view="battle";ui.game.mode="battle";ui._open_system_menu();await frame("compact-menu")
  ui._clear_menu();ui.ui_mode="status";ui.status_id="M15_boss";await frame("compact-status")
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;await create_timer(0.25).timeout
 var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks.size(),"labels":checks,"errors":errors,"screenshots":shots},"  "));file.close();print("M15_REWIND ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
