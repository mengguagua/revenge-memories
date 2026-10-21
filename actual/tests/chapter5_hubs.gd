extends "res://tests/chapter5_play.gd"
## Targeted menu/room fixtures, separate from the two actual campaign playthroughs.
var checks=[]
func ensure(ok,label):
 checks.append(label)
 if not ok:record_failure(label)
func run():
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.save_path="res://reports/chapter4/play/round2-chapter-end.json";ensure(ui.game.load_game(),"source loads")
 ui.game.save_path="res://reports/chapter5/hub-working.json";ui.game.begin_chapter_five()
 var visits=0
 for room in ui.game.ChapterFive.ROOMS:
  ui.hub_controller.enter_room(room);await settle()
  for object in ui.hub_controller.objects:
   var point=Vector2i(object.position[0],object.position[1]);var found=false
   for d in ui.game.DIRECTIONS:
    if not _hub_route(point+d).is_empty():walk_to(point+d);found=true;visits+=1;break
   ensure(found,room+" object reachable "+str(object.action))
  walk_to(Vector2i(6,7));ensure(ui.game.hub_position==Vector2i(6,7),room+" return path")
 ui.game.cleared_stages.append_array([501,502,503,504]);ui.game.flags.west_palace_gate=true;ui.game.flags.east_palace_gate=true;ui.game.flags.S51_invited=true;ui.game.flags.east_network_ready=true;ui.game.flags.M51_confirmed=true
 ui.game.world_node=15;ui.game.route_positions.alm=15;ui.hub_controller.enter_room("H55")
 await hub_action("fifth_merge");ensure(not ui.game.flags.get("chapter5_merged",false),"one team cannot merge")
 await hub_action("fifth_prepare");choose("hub:fifth_toggle_hunapu");ensure(ui.game.ChapterFive.selection(ui.game,"alm").has("hunapu"),"mandatory hero cannot be removed")
 choose("hub:fifth_ready");await settle()
 ui.game.route_positions.celica=15;ui.game.flags.chapter5_ready.celica=true;ui.game.ChapterFive.selection(ui.game,"celica")
 await hub_action("fifth_merge");ensure(ui.menu_actions.has("hub:fifth_confirm_merge"),"unplayed library gets explicit closing confirmation")
 choose("close");ensure(ui.game.allowed_world_nodes().has(14) and not ui.game.flags.get("chapter5_merged",false),"cancel retains return route")
 await hub_action("fifth_merge");choose("hub:fifth_confirm_merge");await settle()
 ensure(ui.game.flags.chapter5_merged and ui.game.flags.S51_closed,"skip optional library is permitted")
 ensure(not ui.game.allowed_world_nodes().has(39) and ui.game.stage_for_node(39)==0,"library closes after explicit merge")
 await hub_action("fifth_prepare");choose("hub:fifth_toggle_daan");choose("hub:fifth_ready");await settle();ensure(ui.game.save_game(),"joint revised deployment saves")
 var loaded=State.new();loaded.save_path=ui.game.save_path;ensure(loaded.load_game(),"joint revised deployment reloads")
 # Prior R01/R02 plus actual healthy participants are required for R03.
 ui.game.roster.mireille.dying=false;ui.game.roster.mireille.hp=ui.game.roster.mireille.max_hp;ui.game.flags.seen_R01=true;ui.game.flags.seen_R02=true
 await hub_action("fifth_relationship");ensure(ui.game.flags.get("seen_R03",false),"R03 follows established relationship")
 var ending=preload("res://core/chapter5_endings.gd").entries(ui.game)
 ensure(ending.filter(func(p):return p.title=="达恩")[0].text.contains("诊室"),"relationship affects ending")
 # Resume genuine completed ending through the title and existing journal controller.
 var source="res://reports/chapter5/play/round2-ending-complete.json"
 var slots="res://reports/chapter5/ending-slots/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(slots));DirAccess.copy_absolute(ProjectSettings.globalize_path(source),ProjectSettings.globalize_path(slots+"journey-slot-1.json"))
 ui.game.slot_directory=slots;ui._show_title();key(KEY_DOWN);key(KEY_Z);key(KEY_Z);await settle()
 ensure(ui.view=="ending" and ui.game.flags.get("ending_done",false),"title continue resumes completed ending")
 var inventory=ui.game.convoy.duplicate(true);var roster=ui.game.roster.duplicate(true);var last=ui.ending_index
 key(KEY_Z);choose("new:replay_ending");await settle()
 ensure(ui.ending_index==0 and last>0,"ending replay returns to first page")
 ensure(ui.game.convoy==inventory and ui.game.roster==roster,"ending replay cannot duplicate experience equipment or heal")
 var f=FileAccess.open("res://reports/chapter5/hub-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"checks":checks,"inputs":inputs,"visited_objects":visits,"failures":failures,"fixture":true},"  "));f.close()
 print("CH5_HUB ",checks.size()," ",failures);ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
