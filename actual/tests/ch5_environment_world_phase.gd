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
 var raw=FileAccess.get_file_as_string("res://data/formal_world.json").sha256_text();var before=FileAccess.get_file_as_string("res://reports/chapter5-environment-20261023/baseline/formal_world.json").sha256_text()
 check("world source exact baseline",raw==before)
 for chapter in range(6):
  for ceremony in [false,true]:
   for confirmed in [false,true]:
    ui.game.chapter=chapter;ui.game.flags.chapter1_complete=ceremony;ui.game.flags.F22_confirmed=confirmed
    var first_cold=chapter==1 and not ceremony;var dark=chapter==2 and confirmed
    var cold=first_cold or (chapter==2 and not confirmed);var label="chapter-%s-ceremony-%s-F22-%s"%[chapter,ceremony,confirmed]
    check(label+"-winter",ui._world_uses_winter()==cold and ui._first_chapter_winter()==first_cold)
    check(label+"-blackday",ui._second_chapter_blackday()==dark and ui._world_has_eastern_blackday()==(dark or chapter in [3,4,5]))
    var visual=ui._world_visual_data()
    check(label+"-data",str(visual.get("version",""))=="0.10.15-environment"if chapter==5 else str(visual.get("version",""))=="0.10.14-environment"if chapter==4 else str(visual.get("version",""))=="0.10.13-environment"if chapter==3 else str(visual.get("version",""))=="0.10.11-climate"if cold else JSON.stringify(visual)==base)
    var texture=ui._world_overview_texture();var expected="res://assets/chapter5-environment-20261023/world/overview-arrival.png"if chapter==5 else "res://assets/chapter4-environment-20261023/world/overview-before.png"if chapter==4 else "res://assets/chapter3-environment-20261023/world/overview.png"if chapter==3 else "res://assets/chapter1-climate-20261022/world/overview-winter.png"if cold else "res://assets/chapter2-environment-20261023/world/overview-blackday.png"if dark else ui.OVERVIEW_IMAGE.resource_path
    check(label+"-overview",texture is Texture2D and texture.resource_path==expected)
    var pairs=[[Vector2(51,42),Color(.66,.72,.84)],[Vector2(44,46),Color(.82,.86,.94)],[Vector2(49,34),Color(.75,.8,.9)],[Vector2(39,38),Color.WHITE],[Vector2(25,34),Color.WHITE]]
    if chapter in [3,4,5]:pairs=[[Vector2(36,29),Color(.80,.84,.92)],[Vector2(37,23),Color(.80,.84,.92)],[Vector2(51,28),Color(.80,.84,.92)],[Vector2(25,34),Color.WHITE],[Vector2(31,25),Color.WHITE]]
    for pair in pairs:
     var got=ui._second_chapter_world_tint(pair[0]);var wanted=pair[1]if dark or chapter in [3,4,5] else Color.WHITE
     check(label+"-tint-"+str(pair[0]),got.is_equal_approx(wanted),{"got":[got.r,got.g,got.b],"expected":[wanted.r,wanted.g,wanted.b]})
 ui.game.chapter=4
 for phase in ["before","trial","verified"]:
  ui.game.flags.island_loop_safe=phase!="before";ui.game.flags.D42_done=phase=="verified"
  check("fourth story overview "+phase,ui._world_overview_texture().resource_path=="res://assets/chapter4-environment-20261023/world/overview-"+phase+".png")
  check("fourth shrine light "+phase,ui._second_chapter_world_tint(Vector2(44,15)).is_equal_approx(Color.WHITE if phase!="before"else Color(.8,.84,.92)))
  check("fourth marsh light "+phase,ui._second_chapter_world_tint(Vector2(44,19)).is_equal_approx(Color.WHITE if phase=="verified"else Color(.8,.84,.92)))
  check("fourth distant salt stays dark "+phase,ui._second_chapter_world_tint(Vector2(48,23)).is_equal_approx(Color(.8,.84,.92)))
  check("fourth western pass daylight "+phase,ui._second_chapter_world_tint(Vector2(8,20)).is_equal_approx(Color.WHITE))
 var data=ui._world_visual_data()
 for sample in [[10,"snow"],[11,"grass"],[12,"snow"],[13,"grass"],[26,"sand"],[27,"salt"],[28,"marsh"],[29,"stone"],[37,"snow"],[38,"marsh"]]:
  var cell=ui.world.nodes[str(sample[0])].position
  check("fourth node material "+str(sample[0]),data.ground[cell[1]][cell[0]]==sample[1])
 ui.game.chapter=5;ui.game.flags.chapter4_complete=true;ui.game.flags.campaign_complete=false
 check("fifth chapter inherits fourth biomes",str(ui._world_visual_data().version)=="0.10.15-environment")
 check("fifth chapter inherits verified overview",ui._world_overview_texture().resource_path=="res://assets/chapter5-environment-20261023/world/overview-arrival.png")
 check("fifth chapter keeps cold highlands",ui._world_visual_data().ground[16][14]=="snow")
 check("fifth chapter keeps local protection",ui._second_chapter_world_tint(Vector2(44,19)).is_equal_approx(Color.WHITE))
 check("fifth chapter distant salt still dim",ui._second_chapter_world_tint(Vector2(48,23)).is_equal_approx(Color(.8,.84,.92)))
 var final_geography=JSON.stringify(ui._world_visual_data())
 for phase in ["arrival","network","clear"]:
  ui.game.flags.east_network_ready=phase!="arrival";ui.game.flags.campaign_complete=phase=="clear"
  check("fifth correct overview "+phase,ui._world_overview_texture().resource_path=="res://assets/chapter5-environment-20261023/world/overview-"+phase+".png")
  check("fifth ending geography unchanged "+phase,JSON.stringify(ui._world_visual_data())==final_geography)
  check("fifth highland snow retained "+phase,ui._world_visual_data().ground[16][14]=="snow")
  check("fifth network palace daylight "+phase,ui._second_chapter_world_tint(Vector2(40,11)).is_equal_approx(Color.WHITE)==(phase!="arrival"))
  check("fifth distant salt restores only after god defeated "+phase,ui._second_chapter_world_tint(Vector2(48,23)).is_equal_approx(Color.WHITE)==(phase=="clear"))
  check("fifth blackday phase "+phase,ui._world_has_eastern_blackday()==(phase!="clear"))
 check("world instance unchanged",JSON.stringify(ui.world)==base)
 check("nodes unchanged",JSON.stringify(ui.world.nodes)==nodes)
 check("routes unchanged",JSON.stringify(ui.world.routes)==routes)
 var result={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"save_game_called":false,"source_world_sha256":raw,"scope":"In-memory display-selector fixture, not a gameplay run. Chapters0–5 × ceremony before/after × F22 confirmation before/after. World data, nodes and routes remain exact."}
 var f=FileAccess.open("res://reports/chapter5-environment-20261023/world/phase-fixture.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
 print("WORLD_ENV_PHASE ",result.passed," ",checks.size());ui.queue_free();await process_frame;ui=null
 for cleanup_frame in range(3):await process_frame
 call_deferred("quit",0 if result.passed else 1)
