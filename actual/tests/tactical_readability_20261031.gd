extends SceneTree
const OUT="res://reports/tactical-readability-20261031/"
var checks=[];var errors=[];var shots=[];var screen;var phone;var ui;var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func shot(name):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" text safe: "+str(ui.layout_errors))
  screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name)
func run():
 DirAccess.make_dir_recursive_absolute("/private/tmp/tactical-readability/slots")
 visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override="/private/tmp/tactical-readability/slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.game.new_game();ui.game.save_path="/private/tmp/tactical-readability/state.json"
 for id in ["fula","lance","lena","hervi"]:ui.game.roster[id]=ui.game._initial_character(id);ui.game.party.append(id)
 ui.game.parties.alm=ui.game.party.duplicate();ui.game.roster.otto.level=7;ui.hub_controller.enter_room("H04");ui.field_notes.open_promotions();await shot("promotion-list")
 ui.field_notes.selected=ui.field_notes.entries.find({"id":"otto","target":2});ui.field_notes.accept();await shot("promotion-preview");ui.field_notes.accept();await shot("promotion-confirm")
 if visual:
  var text=ui.presentation_audit.field_notes.text
  check(text.filter(func(t):return t.text.contains("生命回满")).all(func(t):return t.font==12),"confirmation explanation uses clear 12px type")
 ui.field_notes.cancel();ui.field_notes.cancel();ui.field_notes.cancel();ui.game.roster.otto.class_id=2
 ui.game.world_node=5;check(ui.game.start_battle(104),"M14 fixture started with registered party");ui.view="battle";ui.ui_mode="whole_capture";ui.game.cursor=Vector2i(12,21);ui._focus_battle(ui.game.cursor,true)
 await shot("allies-ready")
 var healer=ui.TacticalIdle.data()["18_ally"]
 check(healer.poses.all(func(p):return p.bounds[3]-p.bounds[1]>=56 and p.bounds[3]-p.bounds[1]<=64 and p.bounds[2]-p.bounds[0]>=40),"healer retains full-size readable body within one tile")
 ui.moving_id="fula";ui.moving_direction=Vector2i.RIGHT
 var walking=ui._map_unit_sprite(ui.game.find_unit("fula"));check(not walking.has("idle_alignment") and str(walking.path).contains("walk"),"directional walking remains separate from idle alignment")
 ui.moving_id=""
 var audits=[]
 for key in ui.TacticalIdle.data():
  var parts=key.split("_");var actor={"id":"eileen" if key.begins_with("eileen") else "probe","class_id":24 if key=="eileen_promoted" else 11 if key=="eileen" else int(parts[0]),"side":"enemy" if key.ends_with("enemy") else "player","acted":false}
  if key=="eileen_promoted":actor.promoted=true
  for time in [0.0,.25,.5,.75]:
   ui.elapsed=time;var art=ui._map_unit_sprite(actor)
   if not art.has("idle_alignment"):continue
   var align=art.idle_alignment;var f=int(align.frame);var spec=ui.TacticalIdle.data()[key];var density=float(art.native_density)
   check(absf(float(spec.poses[f].bottom)/density-float(art.tile_origin[1])-16)<.01,key+" frame "+str(f)+" feet on tile bottom")
   check(align.facing==("left" if actor.side=="enemy" else "right"),key+" correct faction-facing policy")
   actor.acted=true;var resting=ui._map_unit_sprite(actor);check(resting.tile_origin==art.tile_origin and resting.idle_flip==art.idle_flip,key+" acted pose retains alignment and facing");actor.acted=false
  audits.append({"profile":key,"source_facing":ui.TacticalIdle.data()[key].source_facing,"target_facing":"left" if actor.side=="enemy" else "right"})
 for unit in ui.game.units:
  if unit.side=="player":unit.acted=true
 ui.elapsed=0;await shot("allies-waiting")
 for unit in ui.game.units:unit.acted=false
 ui.ui_mode="inspect";ui.game.cursor=ui.game.pos(ui.game.find_unit("M14_e9"));ui._focus_battle(ui.game.cursor,true);ui._accept();await shot("enemy-red-range")
 check(ui.ui_mode=="inspect" and ui.game.selected_id=="","confirm on enemy keeps map range visible")
 if visual:
  var red=ui.presentation_audit.enemy_range
  check(not red.is_empty(),"enemy reachable tiles drawn red")
  check(not ui.battle_card_audit.valid or red.all(func(c):return not ui.battle_card_audit.panel.intersects(Rect2(ui._battle_cell_screen(c),Vector2(16,16)))),"enemy card cannot cover any red movement tile")
 ui.ui_mode="move";ui.game.selected_id="hunapu";ui._accept();await shot("enemy-from-player-move")
 check(ui.ui_mode=="inspect" and ui.game.selected_id=="","enemy selection clears only proposed player movement")
 if visual:check(not ui.presentation_audit.has("player_movement"),"enemy selection removes friendly blue and green overlays")
 ui._show_status();await shot("enemy-status");check(ui.ui_mode=="status","status button still opens enemy details")
 ui.ui_mode="whole_capture";ui.game.cursor=Vector2i(23,11);ui._focus_battle(ui.game.cursor,true);await shot("enemies-ready")
 for unit in ui.game.units:
  if unit.side=="enemy":unit.acted=true
 await shot("enemies-waiting")
 if visual:
  screen.size=Vector2i(884,480);phone.safe_area_override=Rect2(0,0,884,480);phone._layout();ui.hub_controller.enter_room("H04");ui.field_notes.open_promotions();await shot("compact-list")
  ui.game.roster.otto.level=10;ui.field_notes.selected=ui.field_notes.entries.find({"id":"otto","target":22});ui.field_notes.accept();await shot("compact-preview");ui.field_notes.accept();await shot("compact-confirm")
 var f=FileAccess.open(OUT+"profiles.json",FileAccess.WRITE);f.store_string(JSON.stringify(audits,"  "));f.close()
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
 f=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks.size(),"errors":errors,"screenshots":shots},"  "));f.close();print("TACTICAL_READABILITY ",checks.size()," ",errors);quit(0 if errors.is_empty() else 1)
