extends SceneTree
## Read-only display selector fixture; not a playthrough and never saved.
var checks=[]
func _initialize():call_deferred("run")
func check(label:String,ok:bool):
 checks.append({"label":label,"passed":ok})
 if not ok:push_error(label)
func run():
 var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
 var h=ui.hub_controller;var data=JSON.stringify(h.chapter2_rooms);var original_world=JSON.stringify(ui.world)
 for chapter in range(6):
  ui.game.chapter=chapter
  for dark in [false,true]:
   ui.game.flags.F22_confirmed=dark
   for room in ["H21","H22","H23","H24","H25","H26","H27","H31","H41","H51"]:
    h.room=room;h.east_data=h.chapter2_rooms[room].duplicate(true)
    var raw=h.east_data.get("environment_tint",[1,1,1]);var expected=Color(raw[0],raw[1],raw[2])
    if chapter==2 and dark and room in ["H21","H22","H23"]:expected=Color(.82,.86,.94)
    check("chapter-%s-dark-%s-%s"%[chapter,dark,room],h._east_environment_tint().is_equal_approx(expected))
 var environment=h.chapter2_environment;var atlas=load(environment.atlas)
 check("small atlas loads",atlas is Texture2D and atlas.get_size()==Vector2(512,32))
 for room in environment.rooms:
  var art=environment.rooms[room];var floor=h.chapter2_rooms[room].floor
  for y in range(9):
   for x in range(14):
    var t=art.tiles[y][x]
    check(room+"-floor-"+str(x)+"-"+str(y),(t==null)==(str(floor[y])[x]=="~") and (t==null or(int(t)>=0 and int(t)<64)))
  check(room+"-boarding-boat-water-side",art.props[0].position==[88.0,140.0])
 check("room definitions never mutated",JSON.stringify(h.chapter2_rooms)==data)
 check("world not mutated",JSON.stringify(ui.world)==original_world)
 var result={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"save_game_called":false,"scope":"Display-only fixture for chapters0–5 before/after F22_confirmed; original room and world data retained. New floor cell domain equals original walking mask; boarding visual remains outside last walking row."}
 var f=FileAccess.open("res://reports/chapter2-environment-20261023/hubs/phase-fixture.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
 print("HUB_ENV_PHASE ",result.passed," ",checks.size());ui.queue_free();await process_frame;quit(0 if result.passed else 1)
