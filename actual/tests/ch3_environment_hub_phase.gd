extends SceneTree
var checks=[]
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append({"passed":ok,"label":label})
 if not ok:push_error(label)
func run():
 var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
 var h=ui.hub_controller;var raw=FileAccess.get_file_as_string("res://data/chapter3_hubs.json")
 check(raw.sha256_text()==FileAccess.get_file_as_string("res://reports/chapter3-environment-20261023/baseline/chapter3_hubs.json").sha256_text(),"all original hub geometry/objects/definitions byte-identical")
 var snapshot=JSON.stringify(h.chapter2_rooms);var atlas=load(str(h.chapter3_environment.atlas));check(atlas is Texture2D,"third chapter native atlas loads")
 for room in h.chapter3_environment.rooms:
  var visual=h.chapter3_environment.rooms[room];var original=h.chapter2_rooms[room]
  for y in range(9):
   for x in range(14):
    var tile=visual.tiles[y][x]
    check((tile==null)==(str(original.floor[y])[x]=="~")and(tile==null or int(tile)>=0 and int(tile)<32),room+" original walking domain "+str(Vector2i(x,y)))
  for chapter in range(6):
   ui.game.chapter=chapter;h.room=room;h.east_data=original.duplicate(true)
   var tint=visual.get("tint",[1,1,1])if chapter==3 else original.get("environment_tint",[1,1,1])
   check(h._east_environment_tint().is_equal_approx(Color(tint[0],tint[1],tint[2])),room+" actual tint selector chapter "+str(chapter))
  for before_path in visual.get("scenery_paths",{}):
   var after_path=str(visual.scenery_paths[before_path]);check(load(str(before_path)).get_size()==load(after_path).get_size(),room+" replacement architecture dimensions exact")
 check(JSON.stringify(h.chapter2_rooms)==snapshot,"render metadata never mutates room definitions")
 var result={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"save_game_called":false,"scope":"Native material tile domain matches original floor and renderer tint for chapters0–5; no game state saved or gameplay inputs claimed."}
 var f=FileAccess.open("res://reports/chapter3-environment-20261023/hubs/phase-fixture.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
 print("CH3_HUB_PHASE ",result.passed," ",checks.size());ui.queue_free();await process_frame;ui=null;call_deferred("quit",0 if result.passed else 1)
