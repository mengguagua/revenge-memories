extends SceneTree
const Renderer=preload("res://reports/chapter5-spatial-20261022/material-audit/dynamic-canvas.gd")
const OUT="res://reports/chapter5-spatial-20261022/material-audit/"
var errors=[]
var records=[]
func check(ok:bool,label:String):
 if not ok:errors.append(label)
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 var v=SubViewport.new();v.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(v)
 var c=Renderer.new();v.add_child(c);await process_frame
 for id in [103,111]:
  c.game.new_game();c.game.save_path="/private/tmp/west-material-unused.json";c.game.world_node=int(c.game.stages[id].node);check(c.game.start_battle(id),"normal current map initialization "+str(id))
  var d=c.game.battle_data;v.size=Vector2i(d.map.width*16+64,d.map.height*16+64);c.size=Vector2(v.size);c.game.story_events.clear()
  var actor=c.game.find_unit("hunapu")
  for obj in d.objects:
   if not (obj.kind=="door" or obj.kind=="tools"):continue
   var p=Vector2i(obj.position[0],obj.position[1])+Vector2i.DOWN
   actor.position=[p.x,p.y];actor.acted=false;c.game.selected_id=actor.id
   check(c.game.interact(obj.id),"normal object action "+obj.id)
   if obj.kind=="door":
    for cell in obj.get("open_art_cells",[]):check(int(cell.base_tile)in [16,17,18,19],"opened gate uses interior stone "+obj.id)
  c.queue_redraw()
  for i in range(3):await process_frame
  await RenderingServer.frame_post_draw
  v.get_texture().get_image().save_png(OUT+"images/"+str(d.code)+"-opened.png")
  records.append({"code":d.code,"done_objects":c.game.flags.quest.objects.duplicate(),"objects":d.objects,"image":"images/"+str(d.code)+"-opened.png"})
 var f=FileAccess.open(OUT+"dynamic-materials.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"maps":records,"scope":"In-memory ordinary object interaction + real main._draw_map after door/tools action. Fixture positions a genuine actor at the action front; no save files or gameplay source changed, not a full playthrough.","background_guard":true},"  "));f.close();print("DYNAMIC_MATERIALS ",JSON.stringify({"passed":errors.is_empty(),"errors":errors}));c.queue_free();v.queue_free();await process_frame;quit(0 if errors.is_empty()else 1)
