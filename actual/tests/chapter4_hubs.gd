extends "res://tests/chapter4_play.gd"
## Geometry and alternate-order fixtures driven through actual walking and confirmation.
var checks=[]
func ensure(ok,label):
 checks.append(label)
 if not ok:record_failure(label)
func run():
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.save_path="res://reports/chapter3/play/round1final-chapter-end.json";ensure(ui.game.load_game(),"authentic source loads")
 ui.game.save_path="res://reports/chapter4/hub-fixture-working.json";ui.game.begin_chapter_four()
 var visits=0
 for room in ui.game.ChapterFour.ROOMS:
  ui.hub_controller.enter_room(room);await settle()
  for object in ui.hub_controller.objects:
   var point=Vector2i(object.position[0],object.position[1]);var found=false
   for d in ui.game.DIRECTIONS:
    var path=_hub_route(point+d)
    if not path.is_empty():walk_to(point+d);found=true;visits+=1;break
   ensure(found,room+" reachable facing "+str(object.action))
  walk_to(Vector2i(6,7));ensure(ui.game.hub_position==Vector2i(6,7),room+" exit connected")
 ui.game.route="alm";ui.game.party=ui.game.parties.alm.duplicate()
 ui.game.world_node=12;ui.game.route_positions.alm=12;ui.game.cleared_stages.append(402);ui.game.cleared_stages.append(403);ui.game.flags.m43_seized=true
 ui.hub_controller.enter_room("H42");await hub_action("fourth_letters")
 ensure(ui.game.flags.get("seen_R02",false) and ui.game.flags.get("seen_R06_care",false),"fourth chapter letters respect injured companion branch")
 ui.hub_controller.enter_room("H43");await hub_action("fourth_tower_shutdown")
 ensure(not ui.game.flags.get("west_tower_safe",false),"tower waiting dialogue does not falsely finish")
 ensure(ui.game.can_switch_route(),"waiting room permits menu switch")
 ui.game.cleared_stages.append(406);ui.game.flags.obs_steps_ready=true
 var before=ui.game.roster.hunapu.duplicate(true);await hub_action("fourth_tower_shutdown")
 ensure(ui.game.flags.west_tower_safe and ui.game.allowed_world_nodes().has(13),"received steps open capital without replay")
 ensure(ui.game.roster.hunapu.level==before.level and ui.game.roster.hunapu.hp==before.hp,"story advancement retains level and HP")
 await hub_action("fourth_tower_shutdown");ensure(ui.game.roster.hunapu.level==before.level,"repeat shutdown no growth reset")
 ui.game.route="celica";ui.game.party=ui.game.parties.celica.duplicate();ui.game.world_node=29;ui.game.route_positions.celica=29;ui.game.cleared_stages.append(408);ui.game.flags.island_loop_safe=true
 ui.hub_controller.enter_room("H48");var count=ui.game.treatment_remaining();var wounds=ui.game.roster.lisa.duplicate(true)
 await hub_action("fourth_island_verify");await hub_action("fourth_d42")
 ensure(ui.game.flags.D42_done and ui.game.treatment_remaining()==count+1,"D42 through real dialog grants fourth resource")
 ensure(ui.game.roster.lisa==wounds,"D42 does not heal injured Lisa or make her speak")
 await hub_action("fourth_d42");ensure(ui.game.treatment_remaining()==count+1,"repeat D42 cannot duplicate source")
 var strength=int(ui.game.roster.eileen.strength)
 for i in range(3):await hub_action("fourth_spring");choose("hub:fourth_strength_eileen");await settle()
 await hub_action("fourth_spring");ensure(int(ui.game.roster.eileen.strength)==strength+3 and int(ui.game.flags.fourth_strength_uses)==3,"strength spring limited three real selections")
 ui.game.cleared_stages.append(412);ui.game.flags.S42_settled=true;ui.game.flags.celine_ready=true;ui.game.world_node=38;ui.game.route_positions.celica=38;ui.hub_controller.enter_room("H50")
 await hub_action("fourth_celine");choose("hub:fourth_recruit_celine");await settle();await hub_action("fourth_celine")
 ensure(ui.game.party.count("celine")==1 and ui.game.roster.celine.name_zh=="赛琳","Celine joins once after consent")
 ui.game.world_node=9;ui.game.route_positions.celica=9;ui.hub_controller.enter_room("H10")
 await hub_action("third_messenger");ensure(ui.game.mode!="chapter_end","missing capital prevents closure with explicit progress")
 ui.game.cleared_stages.append(404);await hub_action("third_messenger");choose("hub:fourth_finish");await settle()
 ensure(ui.game.flags.chapter4_closed and ui.view=="chapter_end","chapter closes after all four main requirements")
 var f=FileAccess.open("res://reports/chapter4/hub-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"checks":checks,"inputs":inputs,"visited_objects":visits,"failures":failures,"fixture":true},"  "));f.close()
 print("CH4_HUB_RESULT ",checks.size()," ",failures);ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
