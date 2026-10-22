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
 var expected=State.read_json(OS.get_environment("CH1_PACKAGE_EXPECTED"));var game=State.new();var maps={};var loaded_atlases={};var textures={};var json_hashes={}
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
 for path in expected.climate_json:
  var hash_value=FileAccess.get_file_as_string(str(path)).sha256_text()
  check(hash_value==str(expected.climate_json[path]),"exact chapter1 climate JSON: "+str(path));json_hashes[path]=hash_value
 for path in expected.climate_textures:textures[path]=texture_check(str(path),expected.climate_textures[path].size)
 for n in expected.winter_nature:
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
 for path in expected.get("new_offline_source_paths",[]):check(not FileAccess.file_exists(str(path)) and not ResourceLoader.exists(str(path)),"new generated offline source excluded "+str(path))
 for prefix in expected.get("excluded_prefixes",[]):check(not DirAccess.dir_exists_absolute(str(prefix)),"offline/tool directory excluded "+str(prefix))
 for path in expected.existing_compat_paths:
  if FileAccess.file_exists(str(path)):compat_present.append(path)
 for version in expected.forbidden_new_compat_versions:
  for code in expected.maps:check(not FileAccess.file_exists("res://data/compat/"+str(version)+"/"+str(code)+".json"),"no newly retained compatibility copy "+str(version)+"/"+str(code))
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"software_version":ProjectSettings.get_setting("application/config/version"),"map_revision":"0.10.11-climate","stage_count":game.stages.size(),"maps":maps,"atlases":loaded_atlases,"climate_json":json_hashes,"climate_textures":textures,"winter_rock_count":expected.winter_nature.size(),"generated_source_exclusion_checks":expected.get("new_offline_source_paths",[]).size(),"excluded_prefixes":expected.get("excluded_prefixes",[]),"existing_compatibility_count":compat_present.size(),"existing_compatibility_paths":compat_present,"new_compatibility_copies":0,"resource_root":ProjectSettings.globalize_path("res://"),"command_line":OS.get_cmdline_args(),"scope":"Independent exported app/PCK probe from isolated /private/tmp. Exact forty-map hashes, all climate JSON, actual textures, shared winter rock keys, and offline source/report/test/tool exclusion. No new compatibility copies."}
 var f=FileAccess.open(OS.get_environment("CH1_PACKAGE_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("CH1_PACKAGE ",JSON.stringify({"passed":report.passed,"checks":checks,"errors":errors}));quit(0 if errors.is_empty()else 1)
