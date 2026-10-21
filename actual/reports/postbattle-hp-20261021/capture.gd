extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="/Users/gcc/gaocc/project/revenge-memories/actual/reports/postbattle-hp-20261021/"
var viewport
var ui
var shots=[]
var errors=[]
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func shot(name:String,view:String,id:String):
 ui.view=view;ui.status_id=id;ui.ui_mode="status" if view=="battle" else "inspect";ui.game.selected_id="";ui._clear_menu();ui.layout_errors.clear();ui.queue_redraw()
 for i in range(3):await process_frame
 await RenderingServer.frame_post_draw
 var unit=ui._status_unit(id)
 var hp_bars=ui.health_checks.duplicate(true)
 var text=ui.text_checks.duplicate(true)
 var layout=ui.layout_errors.duplicate()
 var status_text="生命"+str(int(unit.hp))+"/"+str(int(unit.max_hp))
 if not text.any(func(t):return t.text==status_text):layout.append("Missing actual status HP: "+status_text)
 if not hp_bars.any(func(h):return h.hp==int(unit.hp) and h.maximum==int(unit.max_hp)):layout.append("HP cells differ from actual status HP")
 viewport.get_texture().get_image().save_png(OUT+name+".png")
 shots.append({"name":name,"size":[viewport.size.x,viewport.size.y],"view":view,"id":id,"hp":unit.hp,"max_hp":unit.max_hp,"text":status_text,"health":hp_bars,"errors":layout})
 errors.append_array(layout)
func run():
 viewport=SubViewport.new();viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=3
 # A validated old world checkpoint reproduces the reported 16/28 status.
 var raw=State.read_json("/private/tmp/revenge-postbattle-hp-20261021/checkpoint-5.json")
 raw.mode="world";raw.roster.hunapu.level=3;raw.roster.hunapu.exp=45;raw.roster.hunapu.max_hp=28;raw.roster.hunapu.hp=16
 for unit in raw.units:
  if unit.id=="hunapu":unit.level=3;unit.exp=45;unit.max_hp=28;unit.hp=16
 var path="/private/tmp/revenge-postbattle-hp-20261021/visual-checkpoint.json"
 var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(raw));f.close()
 ui.game.save_path=path
 if not ui.game.load_game():errors.append("fixture failed validation");quit(1);return
 ui.game.roster.hunapu.hp=16
 await shot("01-before-world-16-of-28","camp_status","hunapu")
 if not ui.game.load_game():errors.append("world reload failed");quit(1);return
 await shot("02-after-world-28-of-28","camp_status","hunapu")
 await shot("03-dying-remains-zero","camp_status","daan")
 viewport.size=Vector2i(768,720);viewport.size_2d_override=Vector2i(256,240)
 await shot("04-after-compact-28-of-28","camp_status","hunapu")
 raw.mode="battle";raw.battle_settled=false;raw.battle_outcome=""
 f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(raw));f.close()
 if not ui.game.load_game():errors.append("active fixture failed validation");quit(1);return
 await shot("05-active-battle-retains-16-of-28","battle","hunapu")
 f=FileAccess.open(OUT+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"fixture":true,"before_reproduces_old_checkpoint":true,"background_guard":true,"visible_windows":false},"  "));f.close()
 print("POSTBATTLE_HP_LAYOUT ",shots.size()," screenshots; errors: ",errors)
 ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
