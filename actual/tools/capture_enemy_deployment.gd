extends SceneTree
const OUT="res://reports/enemy-deployment-20261023/"
const CACHE="/private/tmp/revenge-enemy-integration-20261023/"
var viewport
var ui
var shots=[]
var errors=[]
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func shot(name:String):
 ui.queue_redraw()
 for i in range(3):await process_frame
 await RenderingServer.frame_post_draw
 viewport.get_texture().get_image().save_png(OUT+"screenshots/"+name+".png")
 var problems=ui.layout_errors.duplicate();errors.append_array(problems)
 shots.append({"name":name,"file":"screenshots/"+name+".png","view":ui.view,"width":viewport.size_2d_override.x,"errors":problems,"text":ui.text_checks.duplicate(true)})
 print("ENEMY_PHOTO ",name," ",problems)
func fixture(code:String):
 ui.game.save_path=CACHE+code+".json"
 if not ui.game.load_game():errors.append("load failed "+code);return
 ui.game.save_path="/private/tmp/enemy-capture-working.json";ui.game.story_events.clear();ui.view="battle";ui.ui_mode="inspect";ui._clear_menu();ui.notice_time=0;ui.phase_time=0;ui.busy=false;ui.batch_running=false;ui.combat.clear()
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+"screenshots"))
 viewport=SubViewport.new();viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/enemy-capture-slots";viewport.add_child(ui);await process_frame;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
 for pair in [["S11","S11_e4"],["M32","M32_e1"],["F32","F32_e1"],["M33","M33_e9"],["F33","F33_e9"],["F42","F42_e3"],["F43","F43_e8"],["F43","F43_e3"],["S42","S42_e1"],["J53","J53_e14"],["J54","J54_boss"],["S21","S21_boss"],["S22","S22_boss"]]:
  fixture(pair[0]);var enemy=ui.game.find_unit(pair[1])
  if enemy.is_empty():errors.append("missing "+pair[1]);continue
  ui.game.cursor=ui.game.pos(enemy);ui._focus_battle(ui.game.cursor,true)
  await shot(pair[0]+"-map-"+str(enemy.class_id))
  ui.ui_mode="status";ui.status_id=enemy.id
  await shot(pair[0]+"-status-"+str(enemy.class_id))
 for probe in [["S22","S22_boss",1001,1],["S21","S21_boss",1002,2],["S42","S42_e1",1003,1],["S42","S42_e1",1004,2],["J54","J54_boss",1005,1],["J54","J54_boss",1006,2]]:
  fixture(probe[0]);var enemy=ui.game.find_unit(probe[1]);var hero=ui.game.roster.hunapu.duplicate(true)
  hero.side="player";hero.position=[4+int(probe[3]),4];enemy.position=[4,4]
  ui.game.units=[enemy,hero];ui.view="combat"
  ui.combat=ui.game.plan_combat(hero.id,enemy.id) if int(probe[2])==1005 else ui.game.plan_combat(enemy.id,hero.id)
  if ui.combat.is_empty():errors.append("empty real combat preview "+str(probe[2]));continue
  ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.battle_animation.reset()
  var event={"attacker":enemy.id,"defender":hero.id,"weapon_index":probe[2],"distance":probe[3],"critical":false,"hit":true,"visual_only":true}
  var selected=ui.battle_animation.selection(event)
  if selected.is_empty():errors.append("missing animation "+str(probe[2]));continue
  var contact=int(selected.variant.contact_tick)
  for tick in [0,contact,contact+15]:
   if not ui.battle_animation.show_frame(event,tick):errors.append("missing frame "+str(probe[2]))
   await shot("attack-"+str(probe[2])+"-"+str(tick))
  if int(probe[2])==1006:
   viewport.size=Vector2i(768,720);viewport.size_2d_override=Vector2i(256,240)
   enemy.hp=int(enemy.max_hp)/2
   ui.battle_animation.show_frame(event,contact);await shot("256-sun-crown-contact")
 var f=FileAccess.open(OUT+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"background_guard":true,"fixture":"Fresh deployed isolated saves for maps/status; controlled show_frame for combat contact and recovery; no player journals."},"  "));f.close()
 ui.queue_free();viewport.queue_free();await process_frame
 print("ENEMY_VISUAL ",shots.size()," screenshots; ",errors)
 quit(0 if errors.is_empty() else 1)
