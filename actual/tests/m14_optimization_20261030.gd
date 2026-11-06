extends SceneTree
const State=preload("res://core/game_state.gd")
const Review=preload("res://core/promotion_review.gd")
const OUT="res://reports/m14-optimization-20261030/"
var checks=[];var errors=[];var shots=[];var ui;var phone;var screen;var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func frame(name:String):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" safe layout: "+str(ui.layout_errors))
  screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name)
func domain():
 var g=State.new();g.new_game();g.save_path="/private/tmp/m14-optimization/domain.json"
 var original=State.read_json("res://data/legacy/rules_full.json");var effective=g.Items.data()
 check(original.promotion_bases["2"].strength==16 and effective.promotion_bases["2"].strength==13,"source extraction preserved; campaign override applied")
 var u=g.roster.otto;u.level=7;u.max_hp=26;u.hp=26;u.strength=10;u.defence=6
 var result=Review.preview(g,"otto",2)
 check(result.valid and result.after.max_hp==32 and result.after.strength==13 and result.after.defence==10,"soldier promotion exactly matches confirmed 32/13/10 targets")
 u.class_id=2;u.level=10;result=Review.preview(g,"otto",22)
 check(result.after.strength==19 and result.after.defence==16,"bastion promotion exactly matches 19/16 targets")
 u.class_id=16;u.level=11;check(not Review.preview(g,"otto",11).valid,"female mage cannot promote before level12")
 u.level=12;check(Review.preview(g,"otto",11).valid,"female mage can promote at level12")
 var spear=g.Items.item(67);check(spear.weight==2 and spear.hit==g.Items.item(0).hit,"repulsion lance weight2 and no base hit loss")
 var inventory=[11,2,11,11,4,2];var groups=g.Items.inventory_groups(inventory)
 check(groups.size()==3 and groups[0].count==3 and groups[0].label.ends_with("x3"),"duplicate equipment grouped into one counted row")
 g.convoy.alm=inventory.duplicate();var held=g.roster.hunapu.item_id;g.mode="world"
 check(g.equip_from_convoy("hunapu",groups[0].index,11).valid,"grouped row equips one actual copy")
 check(g.convoy.alm.count(11)==2+(1 if held==11 else 0),"equipment group decremented once; prior item preserved")
 var old=State.read_json(OUT+"before/actual/data/stages/M14.json").enemies
 old[0].hp=20;old[1].hp=0;g.EnemyBalance.prepare(104,old)
 check(old[0].class_id==4 and old[0].level==1 and old[0].max_hp==28 and old[0].hp==21,"old battle commander migrates while preserving seven missing HP")
 check(old[1].hp==0,"migration does not revive defeated enemies")
 var once=old.duplicate(true);g.EnemyBalance.prepare(104,old);check(old==once,"enemy upgrade does not stack on repeat load")
 var stage=g.stages[104];check(stage.enemies.size()==12 and stage.enemies.filter(func(e):return e.class_id==15).size()==2 and stage.enemies.filter(func(e):return e.class_id==6).size()==4,"M14 preserves twelve enemies with four soldiers and two mages")
 check(stage.enemies.filter(func(e):return not e.get("objective_boss",false)).all(func(e):return e.level==4 and e.luck==0),"all other enemies level4 and luck unchanged")
 var ledger=State.read_json(OUT+"enemy-changes.json")
 for e in ledger.bonus:check(e.total==5 and not e.bonus.has("luck") and not e.bonus.has("move"),e.id+" gets exactly five fixed stat points")
 check(not stage.before.contains("塔里的劳工也得有路出来"),"removed requested line from current battle dialogue")
 var saved=State.new();saved.new_game();saved.world_node=5;saved.start_battle(104);saved.save_path="/private/tmp/m14-optimization/old-battle.json"
 var originals=State.read_json(OUT+"before/actual/data/stages/M14.json").enemies
 originals[0].hp=20;originals[1].hp=0
 for e in originals:e.enemy_balance_revision=8
 saved.units=saved.units.filter(func(e):return e.side=="player")+originals
 saved.battle_start_snapshot.units=saved.units.duplicate(true)
 check(saved.save_game(),"old M14 battle fixture saves")
 var loaded=State.new();loaded.save_path=saved.save_path
 check(loaded.load_game(),"old M14 battle loads through actual save validator")
 check(loaded.find_unit("M14_boss").class_id==4 and loaded.find_unit("M14_boss").hp==21,"actual load migrates commander and preserves wound")
 check(loaded.find_unit("M14_e1").hp==0 and loaded.find_unit("M14_e6").class_id==15,"actual load preserves dead enemy and replaces living soldier profession")
 check(loaded.battle_start_snapshot.units.filter(func(e):return e.id=="M14_boss")[0].class_id==4,"retry snapshot receives same migration")
 var building_audit=[]
 for s in g.stages.values():
  for o in s.get("objects",[]):
   if o.get("kind","")!="visit":continue
   var m=g.VisitBuildings.module_for(s,o)
   check(not m.is_empty(),s.code+" visit has a complete building footprint")
   for p in m.get("cells",[]):check(g.VisitBuildings.name_at(s,Vector2i(p[0],p[1]))==str(o.label).trim_prefix("访问"),s.code+" entire visit footprint has a place name")
   check(not g.VisitBuildings.props(s).is_empty() and ResourceLoader.exists(g.VisitBuildings.TENT) and ResourceLoader.exists(g.VisitBuildings.DOOR),s.code+" visit artwork loads")
   building_audit.append({"stage":s.code,"name":o.label,"module":m.name,"entrance":o.position,"fronts":o.get("approaches",[])})
 var f=FileAccess.open(OUT+"buildings.json",FileAccess.WRITE);f.store_string(JSON.stringify(building_audit,"  "));f.close()
 check(building_audit.size()==15,"all fifteen campaign visit sites audited")
 g.world_node=5;check(g.start_battle(104),"current M14 battle starts")
 var actor=g.find_unit("hunapu");actor.position=[21,8];actor.acted=false;g.selected_id="hunapu"
 check(g.interactions_for(actor).any(func(o):return o.id=="M14_visit_0"),"new blue tent uses actual front-door visit action")
 check(g.interact("M14_visit_0"),"records tent can be visited and reward claimed")
 check(not g.interact("M14_visit_0"),"repeat visit cannot duplicate reward")
 g.selected_id="hunapu";actor.acted=false;actor.position=[14,17];check(g.interact("M14_control_0"),"south checkpoint still works")
 g.selected_id="hunapu";actor.acted=false;actor.position=[26,18];check(g.interact("M14_control_1"),"east checkpoint still works")
func run():
 DirAccess.make_dir_recursive_absolute("/private/tmp/m14-optimization/slots")
 visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1";domain()
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override="/private/tmp/m14-optimization/slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.game.new_game();ui.game.save_path="/private/tmp/m14-optimization/ui.json"
 ui.hub_controller.enter_room("H04")
 for x in [1,2,3,4,5,8,9,10,11,12]:
  ui.game.hub_position=Vector2i(x,6);ui.hub_controller.direction(Vector2i.DOWN);check(ui.game.hub_position.y==6,"south wall blocks player column "+str(x))
 ui.game.hub_position=Vector2i(3,7);ui.hub_controller.enter_room("H04",true);check(ui.game.hub_position==Vector2i(6,7),"old save inside south wall moves to central doorway")
 ui.game.hub_position=Vector2i(3,6);await frame("chapel-wall")
 ui.game.hub_position=Vector2i(6,7);ui.hub_controller.direction(Vector2i.DOWN)
 check(ui.hub_controller.room=="H03" and ui.game.hub_position==Vector2i(11,3) and ui.hub_controller.facing==Vector2i.DOWN,"chapel exit arrives below northeast stairs facing front")
 await frame("chapel-exit")
 ui.game.mode="world";ui.view="world";ui.game.convoy.alm=[11,2,11,11,4,2,67];ui._camp_action("withdraw");await frame("grouped-inventory");check(ui.menu_items.size()==4,"actual inventory UI groups duplicates")
 ui._clear_menu();ui.game.roster.otto.level=7;ui.game.roster.otto.max_hp=26;ui.game.roster.otto.hp=26;ui.game.roster.otto.strength=10;ui.game.roster.otto.defence=6
 ui.field_notes.open_promotions();ui.field_notes.selected=ui.field_notes.entries.find({"id":"otto","target":2});ui.field_notes.accept();await frame("promotion-rebalanced");ui.field_notes.cancel();ui.field_notes.cancel()
 ui.view="world";ui.game.mode="world";ui.equipment_screen.open(6);ui.equipment_screen.selected=ui.equipment_screen.members.find("otto");ui.equipment_screen.accept();await frame("repulsion-lance");ui.equipment_screen.cancel();ui.equipment_screen.cancel();ui._clear_menu()
 ui.game.world_node=5;ui.game.start_battle(104);ui.view="battle";ui.ui_mode="inspect";ui.busy=false
 ui.status_id="M14_boss";ui.ui_mode="status";await frame("commander-status");check(not visual or ui.presentation_audit.get("status_profession","")=="骑士","commander detail displays knight profession")
 ui.view="battle";ui.ui_mode="inspect";ui.game.cursor=Vector2i(21,7);ui._focus_battle(ui.game.cursor,true);await frame("visitable-tent");check(ui._terrain_name(ui.game.cursor)=="营地文书帐","visitable tent never named obstacle")
 ui.game.cursor=Vector2i(24,15);ui._focus_battle(ui.game.cursor,true);await frame("closed-store");check(ui._terrain_name(ui.game.cursor)=="封闭粮料库","nonvisitable house explains closed identity")
 ui.game.cursor=Vector2i(17,13);ui._focus_battle(ui.game.cursor,true);await frame("new-mage")
 if visual:
  for sid in [101,103,112,201,301]:
   ui.game.battle_data=ui.game.stages[sid].duplicate(true);ui.game.stage_id=sid;ui.game.chapter=int(ui.game.battle_data.chapter);ui.game.units=[]
   var visit=ui.game.battle_data.objects.filter(func(o):return o.kind=="visit")[0];ui.game.cursor=Vector2i(visit.position[0],visit.position[1]);ui._focus_battle(ui.game.cursor,true);await frame("visit-"+str(ui.game.battle_data.code))
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
 var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks.size(),"labels":checks,"errors":errors,"screenshots":shots},"  "));file.close();print("M14_OPT ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
