extends SceneTree
const State=preload("res://core/game_state.gd")
var errors=[]
var checks=0
var compat_present=[]
func check(ok:bool,label:String):
 checks+=1
 if not ok:errors.append(label);push_error(label)
func texture_check(path:String,expected_size:Array=[])->Array:
 var texture=load(path)
 check(texture is Texture2D and texture.get_width()>0 and texture.get_height()>0,"package texture loads: "+path)
 if not texture is Texture2D:return []
 var size=[texture.get_width(),texture.get_height()]
 # JSON numbers are floats; compare normalized integer dimensions.
 if not expected_size.is_empty():check(size==[int(expected_size[0]),int(expected_size[1])],"package native texture size: "+path)
 return size
func _initialize():
 var expected=State.read_json(OS.get_environment("CH5_ENV_PACKAGE_EXPECTED"));var game=State.new();var maps={};var loaded_atlases={};var textures={};var json_hashes={}
 check(bool(expected.get("frozen",false)),"final runtime snapshot frozen before export")
 check(str(ProjectSettings.get_setting("application/config/version"))=="0.10.3","software version unchanged 0.10.3")
 check(ProjectSettings.globalize_path("res://")!="/Users/gcc/gaocc/project/revenge-memories/actual/","package resource root is not the source project")
 var nature={}
 for n in State.read_json("res://assets/nature/nature.json").get("sprites",[]):nature[str(n.key)]=n
 for code in expected.maps:
  var m=expected.maps[code];var path="res://data/stages/"+str(code)+".json";var raw=FileAccess.get_file_as_string(path)
  check(raw.sha256_text()==str(m.sha256),str(code)+" exact map data in exported app")
  var d=State.read_json(path);check(str(d.get("tactical_review_version",""))==str(m.revision),str(code)+" correct map revision")
  check(str(d.get("material_review_version",""))==str(m.get("material_revision","")),str(code)+" correct material revision")
  loaded_atlases[str(d.art_atlas)]=texture_check(str(d.art_atlas))
  for p in d.art_props:texture_check(str(p.path))
  for p in d.get("natural_props",[]):
   check(nature.has(str(p.key)),str(code)+" natural key exists: "+str(p.key))
   if nature.has(str(p.key)):texture_check(str(nature[str(p.key)].path),nature[str(p.key)].size)
  for obj in d.objects:
   if not obj.has("sprite"):continue
   var obj_path=str(obj.get("sprite_path","res://assets/battle_tiles/modules/"+str(obj.sprite)+".png"));check(ResourceLoader.exists(obj_path),str(code)+" object sprite in exported app "+obj_path)
  maps[code]={"sha256":raw.sha256_text(),"revision":d.get("tactical_review_version",""),"material_revision":d.get("material_review_version",""),"atlas":d.art_atlas}
 check(game.stages.size()==40 and maps.size()==40,"all forty runtime stages retained")
 for path in expected.environment_json:
  var hash_value=FileAccess.get_file_as_string(str(path)).sha256_text()
  check(hash_value==str(expected.environment_json[path]),"exact environment and retained climate JSON: "+str(path));json_hashes[path]=hash_value
 for path in expected.environment_textures:
  textures[path]=texture_check(str(path),expected.environment_textures[path].size)
  var native_image=load(str(path)).get_image();native_image.convert(Image.FORMAT_RGBA8)
  var pixels=native_image.get_data()
  for index in range(0,pixels.size(),4):
   if pixels[index+3]==0:pixels[index]=0;pixels[index+1]=0;pixels[index+2]=0
  var hash_context=HashingContext.new();hash_context.start(HashingContext.HASH_SHA256);hash_context.update(pixels)
  check(hash_context.finish().hex_encode()==str(expected.environment_textures[path].visible_rgba_sha256),"imported visible pixels exact "+str(path))
 for n in expected.retained_winter_nature:
  check(nature.has(str(n.key)) and nature[str(n.key)].path==n.path and nature[str(n.key)].size==n.size,"unique shared winter rock registered: "+str(n.key))
 var world=State.read_json("res://data/chapter1_world_climate.json")
 check(str(world.version)=="0.10.11-climate","winter world climate revision")
 texture_check(str(world.atlas));texture_check(str(world.overview))
 for p in world.get("natural_props",[]):
  check(nature.has(str(p.key)),"winter world natural key exists: "+str(p.key))
  if nature.has(str(p.key)):texture_check(str(nature[str(p.key)].path),nature[str(p.key)].size)
 var hubs=State.read_json("res://data/chapter1_hub_climate.json")
 check(str(hubs.version)=="0.10.11-climate","winter hub climate revision")
 for room in hubs.rooms:texture_check(str(hubs.rooms[room].atlas))
 for path in hubs.scenery_paths.values():texture_check(str(path))
 for key in hubs.nature_keys.values():check(nature.has(str(key)),"winter hub nature key exists: "+str(key))
 var eastern_hubs=State.read_json("res://data/chapter2_hubs.json")
 var eastern_art=State.read_json("res://data/chapter2_hub_environment.json")
 check(str(eastern_art.version)=="0.10.12-environment","eastern hub environment revision")
 check(eastern_hubs.rooms.size()==7,"all seven chapter2 hubs retained")
 texture_check(str(eastern_art.atlas))
 for room in eastern_hubs.rooms:
  for prop in eastern_hubs.rooms[room].get("scenery",[]):
   if prop.has("sprite_path"):texture_check(str(prop.sprite_path))
  for obj in eastern_hubs.rooms[room].get("objects",[]):
   if obj.has("sprite_path"):texture_check(str(obj.sprite_path))
 texture_check("res://assets/chapter2-environment-20261023/world/overview-blackday.png",[896,1024])
 # Exercise the exported renderer, including the completed-western-save rewind.
 var ui=load("res://scenes/main.tscn").instantiate();ui.world=game.formal_world
 for phase in [[1,false,false,true],[1,true,false,false],[2,true,false,true],[2,true,true,false],[3,true,true,false]]:
  ui.game.chapter=int(phase[0]);ui.game.flags.chapter1_complete=phase[1];ui.game.flags.F22_confirmed=phase[2]
  check(ui._world_uses_winter()==phase[3],"exported renderer story-time winter phase "+str(phase))
  var visual=ui._world_visual_data()
  check(str(visual.get("version",""))=="0.10.13-environment"if int(phase[0])==3 else str(visual.get("version",""))=="0.10.11-climate"if phase[3]else JSON.stringify(visual)==JSON.stringify(ui.world),"exported renderer matching world data "+str(phase))
  var overview=ui._world_overview_texture()
  var wanted="res://assets/chapter3-environment-20261023/world/overview.png"if int(phase[0])==3 else "res://assets/chapter1-climate-20261022/world/overview-winter.png"if phase[3]else "res://assets/chapter2-environment-20261023/world/overview-blackday.png"if int(phase[0])==2 and phase[2]else ui.OVERVIEW_IMAGE.resource_path
  check(overview.resource_path==wanted,"exported renderer matching overview "+str(phase))
 ui.game.chapter=3
 ui.game.flags.quest={"objects":{}}
 for sample in [[305,Vector2i(9,1),"盐地"],[311,Vector2i(8,7),"室内石地"],[306,Vector2i(8,15),"室内石地"],[303,Vector2i(14,6),"室外石铺"]]:
  ui.game.stage_id=int(sample[0]);ui.game.battle_data=game.stages[int(sample[0])].duplicate(true)
  check(ui._terrain_name(sample[1])==sample[2],"exported material tooltip "+str(sample))
 var third=ui._world_visual_data()
 check(third.ground[28][51]=="salt","third chapter salt camp uses salt surface")
 for cell in [Vector2(36,29),Vector2(37,23),Vector2(51,28)]:check(ui._second_chapter_world_tint(cell).is_equal_approx(Color(.80,.84,.92)),"third chapter eastern salt-region tint "+str(cell))
 for cell in [Vector2(25,34),Vector2(31,25)]:check(ui._second_chapter_world_tint(cell).is_equal_approx(Color.WHITE),"western city and common camp retain daylight "+str(cell))
 var hub_visual=State.read_json("res://data/chapter3_hub_environment.json")
 check(hub_visual.rooms.size()==9,"all nine third chapter room renderings retained")
 texture_check(str(hub_visual.atlas))
 for path in expected.get("new_offline_source_paths",[]):check(not FileAccess.file_exists(str(path)) and not ResourceLoader.exists(str(path)),"new generated offline source excluded "+str(path))
 for prefix in expected.get("excluded_prefixes",[]):check(not DirAccess.dir_exists_absolute(str(prefix)),"offline/tool directory excluded "+str(prefix))
 for path in expected.existing_compat_paths:
  if FileAccess.file_exists(str(path)):compat_present.append(path)
 ui.game.chapter=4
 var fourth=ui._world_visual_data()
 check(str(fourth.version)=="0.10.14-environment","exported fourth world display variant")
 for sample in [[10,"snow"],[11,"grass"],[12,"snow"],[13,"grass"],[26,"sand"],[27,"salt"],[28,"marsh"],[29,"stone"],[37,"snow"],[38,"marsh"]]:
  var cell=ui.world.nodes[str(sample[0])].position
  check(fourth.ground[cell[1]][cell[0]]==sample[1],"exported fourth biome "+str(sample))
 for phase in ["before","trial","verified"]:
  ui.game.flags.island_loop_safe=phase!="before";ui.game.flags.D42_done=phase=="verified"
  check(ui._world_overview_texture().resource_path=="res://assets/chapter4-environment-20261023/world/overview-"+phase+".png","exported fourth phase overview "+phase)
  check(ui._second_chapter_world_tint(Vector2(44,15)).is_equal_approx(Color.WHITE if phase!="before"else Color(.8,.84,.92)),"exported repaired shrine light "+phase)
  check(ui._second_chapter_world_tint(Vector2(44,19)).is_equal_approx(Color.WHITE if phase=="verified"else Color(.8,.84,.92)),"exported neighboring marsh light "+phase)
  check(ui._second_chapter_world_tint(Vector2(48,23)).is_equal_approx(Color(.8,.84,.92)),"exported distant salt still dark "+phase)
 var fourth_hubs=State.read_json("res://data/chapter4_hub_environment.json")
 check(fourth_hubs.rooms.size()==11,"eleven fourth-chapter hub appearances retained")
 texture_check(str(fourth_hubs.atlas))
 for room in fourth_hubs.rooms:
  var visual=fourth_hubs.rooms[room]
  for replacement in visual.scenery_paths.values():texture_check(str(replacement))
  for prop in visual.get("props",[]):texture_check(str(prop.path))
 check(fourth_hubs.rooms.H43.has("wall_frame")and fourth_hubs.rooms.H46.has("wall_frame"),"both indoor hubs have native cutaway boundary walls")
 check(fourth_hubs.rooms.H45.background=="sand","sand-city hub uses sand instead of salt")
 ui.game.chapter=5;ui.game.flags.chapter4_complete=true;ui.game.flags.campaign_complete=false;ui.game.flags.east_network_ready=false
 check(str(ui._world_visual_data().version)=="0.10.15-environment","exported fifth chapter opening inherits fourth world")
 check(ui._world_overview_texture().resource_path=="res://assets/chapter5-environment-20261023/world/overview-arrival.png","exported fifth chapter opening keeps verified protection")
 check(ui._world_visual_data().ground[16][14]=="snow","exported fifth opening keeps highland snow")
 var fifth_geography=JSON.stringify(ui._world_visual_data())
 for phase in ["arrival","network","clear"]:
  ui.game.flags.east_network_ready=phase!="arrival";ui.game.flags.campaign_complete=phase=="clear"
  check(ui._world_overview_texture().resource_path=="res://assets/chapter5-environment-20261023/world/overview-"+phase+".png","exported fifth overview phase "+phase)
  check(JSON.stringify(ui._world_visual_data())==fifth_geography,"exported ending retains climate/geography "+phase)
  check(ui._second_chapter_world_tint(Vector2(40,11)).is_equal_approx(Color.WHITE)==(phase!="arrival"),"exported local palace network light "+phase)
  check(ui._second_chapter_world_tint(Vector2(48,23)).is_equal_approx(Color.WHITE)==(phase=="clear"),"exported distant salt final daylight "+phase)
 var fifth_hubs=State.read_json("res://data/chapter5_hub_environment.json")
 check(fifth_hubs.rooms.size()==6,"six fifth-chapter hub appearances")
 texture_check(str(fifth_hubs.atlas))
 for room in fifth_hubs.rooms:
  for replacement in fifth_hubs.rooms[room].scenery_paths.values():texture_check(str(replacement))
 for room in ["H53","H54","H56"]:check(fifth_hubs.rooms[room].has("wall_frame"),"indoor hub has continuous cutaway walls "+room)
 ui.game.flags.quest={"objects":{}}
 for sample in [{"cell": [15, 9], "foot_movement": 1, "name": "室外石铺", "passed": true, "stage": 501}, {"cell": [4, 9], "foot_movement": 1, "name": "病房石地", "passed": true, "stage": 501}, {"cell": [5, 4], "foot_movement": 1, "name": "露天石桥", "passed": true, "stage": 502}, {"cell": [5, 2], "foot_movement": 1, "name": "室内石地", "passed": true, "stage": 503}, {"cell": [14, 13], "foot_movement": 1, "name": "检修木桥", "passed": true, "stage": 503}, {"cell": [16, 3], "foot_movement": 1, "name": "神宫大理石地", "passed": true, "stage": 504}, {"cell": [3, 3], "foot_movement": 1, "name": "室内木地", "passed": true, "stage": 511}, {"cell": [13, 6], "foot_movement": 1, "name": "室内石地", "passed": true, "stage": 511}, {"cell": [13, 7], "foot_movement": 1, "name": "庭院石铺", "passed": true, "stage": 533}, {"cell": [11, 7], "foot_movement": 1, "name": "神宫大理石地", "passed": true, "stage": 534}]:
  ui.game.stage_id=int(sample.stage);ui.game.battle_data=game.stages[int(sample.stage)].duplicate(true)
  check(ui._terrain_name(Vector2i(sample.cell[0],sample.cell[1]))==sample.name,"exported fifth material label "+str(sample.stage)+" "+str(sample.name))
 for sample in [{"cell": [16, 1], "foot_movement": 255, "name": "人工水渠", "passed": true, "stage": 503}, {"cell": [14, 13], "foot_movement": 255, "name": "室内蓄水池", "passed": true, "stage": 504}, {"cell": [4, 4], "foot_movement": 255, "name": "庭院水池", "passed": true, "stage": 501}, {"cell": [12, 13], "foot_movement": 255, "name": "庭院水池", "passed": true, "stage": 533}, {"cell": [12, 21], "foot_movement": 255, "name": "庭院水池", "passed": true, "stage": 534}]:
  ui.game.stage_id=int(sample.stage);ui.game.battle_data=game.stages[int(sample.stage)].duplicate(true)
  check(ui._terrain_name(Vector2i(sample.cell[0],sample.cell[1]))==sample.name,"exported fifth indoor/yard water label "+str(sample.stage))
 ui.free()
 for version in expected.forbidden_new_compat_versions:
  for code in expected.maps:check(not FileAccess.file_exists("res://data/compat/"+str(version)+"/"+str(code)+".json"),"no newly retained compatibility copy "+str(version)+"/"+str(code))
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"software_version":ProjectSettings.get_setting("application/config/version"),"map_revision":"0.10.15-environment","stage_count":game.stages.size(),"maps":maps,"atlases":loaded_atlases,"environment_json":json_hashes,"environment_textures":textures,"retained_winter_rock_count":expected.retained_winter_nature.size(),"generated_source_exclusion_checks":expected.get("new_offline_source_paths",[]).size(),"excluded_prefixes":expected.get("excluded_prefixes",[]),"existing_compatibility_count":compat_present.size(),"existing_compatibility_paths":compat_present,"new_compatibility_copies":0,"resource_root":ProjectSettings.globalize_path("res://"),"command_line":OS.get_cmdline_args(),"scope":"Independent exported app/PCK probe from isolated /private/tmp. Exact forty-map hashes, all chapter5 environment JSON and imported visible pixels, retained first-chapter winter keys, and offline source/report/test/tool exclusion. No new compatibility copies."}
 var f=FileAccess.open(OS.get_environment("CH5_ENV_PACKAGE_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("CH3_ENVIRONMENT_PACKAGE ",JSON.stringify({"passed":report.passed,"checks":checks,"errors":errors}));call_deferred("quit",0 if errors.is_empty()else 1)
