extends SceneTree
## Unit fixture only: probe read-only draw selectors, without saving gameplay state.
var ui
var checks=[]
func _initialize():call_deferred("run")
func check(id:String,value:bool,detail={}) -> void:checks.append({"id":id,"passed":value,"detail":detail})
func run():
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
 var base_world=JSON.stringify(ui.world);var base_nature=JSON.stringify(ui.nature_layouts)
 var base_nodes=JSON.stringify(ui.world.nodes)
 var phases=[{"chapter":0,"done":false,"winter":false},{"chapter":1,"done":false,"winter":true},{"chapter":1,"done":true,"winter":false},{"chapter":2,"done":false,"winter":false},{"chapter":3,"done":false,"winter":false},{"chapter":4,"done":false,"winter":false},{"chapter":5,"done":false,"winter":false}]
 for phase in phases:
  ui.game.chapter=phase.chapter;ui.game.flags.chapter1_complete=phase.done
  var label="chapter-%s-done-%s"%[phase.chapter,phase.done]
  check(label+"-world",ui._first_chapter_winter()==phase.winter)
  var selected=ui._world_visual_data()
  check(label+"-world-data",str(selected.get("version",""))=="0.10.11-climate" if phase.winter else JSON.stringify(selected)==base_world)
  var overview=ui._world_overview_texture()
  check(label+"-overview",overview.resource_path==str(selected.overview) if phase.winter else overview==ui.OVERVIEW_IMAGE)
  for room in ["H02","H03","H05","H06","H07","H09"]:
   var visual=ui.hub_controller.winter_visual(room);var base=ui.nature_layouts.hubs[room];var out=ui.hub_controller.climate_surroundings(room,base)
   check(label+"-"+room,(not visual.is_empty())==phase.winter and (out.biome=="snow" if phase.winter else out==base))
   if phase.winter:
    var shape_ok=out.props.size()==base.props.size()
    for i in range(base.props.size()):
     var a=base.props[i].duplicate(true);var b=out.props[i].duplicate(true);a.erase("key");b.erase("key");shape_ok=shape_ok and a==b
    check(label+"-"+room+"-nature-geometry",shape_ok)
  for room in ["P00","H01","H04","H08","H21","H31","H41","H51"]:
   check(label+"-excluded-"+room,ui.hub_controller.winter_visual(room).is_empty())
 check("original-world-data-unchanged",JSON.stringify(ui.world)==base_world)
 check("original-nature-layouts-unchanged",JSON.stringify(ui.nature_layouts)==base_nature)
 check("world-route-nodes-unchanged",JSON.stringify(ui.world.nodes)==base_nodes)
 var result={"passed":checks.all(func(c):return c.passed),"scope":"Unit fixture for chapter0, chapter1 before/after ceremony, chapters2–5 renderer selection. Fixture state is not saved and is not presented as gameplay.","checks":checks,"count":checks.size(),"save_game_called":false,"stats_routes_inputs_edited":false}
 var f=FileAccess.open("res://reports/chapter1-climate-20261022/side/hubs/phase-fixture.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
 for c in checks:
  if not c.passed:push_error(c.id)
 print("CLIMATE_PHASE_FIXTURE ",result.passed," ",checks.size())
 ui.queue_free();await process_frame;quit(0 if result.passed else 1)
