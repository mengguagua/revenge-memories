extends SceneTree
## Pure display-selection fixture; no gameplay state is saved.
var checks=[]
func _initialize():call_deferred("run")
func check(label:String,ok:bool,detail={}):
 checks.append({"label":label,"passed":ok,"detail":detail})
 if not ok:push_error(label)
func run():
 var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
 var base=JSON.stringify(ui.world);var nodes=JSON.stringify(ui.world.nodes);var routes=JSON.stringify(ui.world.routes)
 var raw=FileAccess.get_file_as_string("res://data/formal_world.json").sha256_text();var before=FileAccess.get_file_as_string("res://reports/chapter2-environment-20261023/baseline/formal_world.json").sha256_text()
 check("world source exact baseline",raw==before)
 for chapter in range(6):
  for ceremony in [false,true]:
   for confirmed in [false,true]:
    ui.game.chapter=chapter;ui.game.flags.chapter1_complete=ceremony;ui.game.flags.F22_confirmed=confirmed
    var first_cold=chapter==1 and not ceremony;var dark=chapter==2 and confirmed
    var cold=first_cold or (chapter==2 and not confirmed);var label="chapter-%s-ceremony-%s-F22-%s"%[chapter,ceremony,confirmed]
    check(label+"-winter",ui._world_uses_winter()==cold and ui._first_chapter_winter()==first_cold)
    check(label+"-blackday",ui._second_chapter_blackday()==dark)
    var visual=ui._world_visual_data()
    check(label+"-data",str(visual.get("version",""))=="0.10.11-climate"if cold else JSON.stringify(visual)==base)
    var texture=ui._world_overview_texture();var expected="res://assets/chapter1-climate-20261022/world/overview-winter.png"if cold else "res://assets/chapter2-environment-20261023/world/overview-blackday.png"if dark else ui.OVERVIEW_IMAGE.resource_path
    check(label+"-overview",texture is Texture2D and texture.resource_path==expected)
    for pair in [[Vector2(51,42),Color(.66,.72,.84)],[Vector2(44,46),Color(.82,.86,.94)],[Vector2(49,34),Color(.75,.8,.9)],[Vector2(39,38),Color.WHITE],[Vector2(25,34),Color.WHITE]]:
     var got=ui._second_chapter_world_tint(pair[0]);var wanted=pair[1]if dark else Color.WHITE
     check(label+"-tint-"+str(pair[0]),got.is_equal_approx(wanted),{"got":[got.r,got.g,got.b],"expected":[wanted.r,wanted.g,wanted.b]})
 check("world instance unchanged",JSON.stringify(ui.world)==base)
 check("nodes unchanged",JSON.stringify(ui.world.nodes)==nodes)
 check("routes unchanged",JSON.stringify(ui.world.routes)==routes)
 var result={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"save_game_called":false,"source_world_sha256":raw,"scope":"In-memory display-selector fixture, not a gameplay run. Chapters0–5 × ceremony before/after × F22 confirmation before/after. World data, nodes and routes remain exact."}
 var f=FileAccess.open("res://reports/chapter2-environment-20261023/world/phase-fixture.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
 print("WORLD_ENV_PHASE ",result.passed," ",checks.size());ui.queue_free();await process_frame;ui=null
 for cleanup_frame in range(3):await process_frame
 call_deferred("quit",0 if result.passed else 1)
