extends SceneTree
const State=preload("res://core/game_state.gd")
var errors=[]
var checks=0
var compat_present=[]
func check(ok:bool,label:String):
 checks+=1
 if not ok:errors.append(label);push_error(label)
func _initialize():
 var expected=State.read_json(OS.get_environment("CH2_PACKAGE_EXPECTED"));var game=State.new();var maps={};var loaded_atlases={}
 check(ProjectSettings.globalize_path("res://")!="/Users/gcc/gaocc/project/revenge-memories/actual/","package resource root is not the source project")
 for code in expected.maps:
  var m=expected.maps[code];var path="res://data/stages/"+str(code)+".json";var raw=FileAccess.get_file_as_string(path)
  check(raw.sha256_text()==str(m.sha256),str(code)+" exact map data in exported app")
  var d=State.read_json(path);check(str(d.tactical_review_version)==str(m.revision),str(code)+" correct map revision")
  var texture=load(str(d.art_atlas));check(texture is Texture2D and texture.get_width()>0 and texture.get_height()>0,str(code)+" actual terrain texture loads")
  loaded_atlases[str(d.art_atlas)]=[texture.get_width(),texture.get_height()]if texture is Texture2D else[]
  for p in d.art_props:
   var prop=load(str(p.path));check(prop is Texture2D and prop.get_width()>0,str(code)+" actual prop texture loads: "+str(p.path))
  for obj in d.objects:
   if not obj.has("sprite"):continue
   var obj_path=str(obj.get("sprite_path","res://assets/battle_tiles/modules/"+str(obj.sprite)+".png"));check(ResourceLoader.exists(obj_path),str(code)+" object sprite in exported app "+obj_path)
  maps[code]={"sha256":raw.sha256_text(),"revision":d.tactical_review_version,"atlas":d.art_atlas}
 check(game.stages.size()==40 and maps.size()==40,"all forty runtime stages retained")
 check(not FileAccess.file_exists("res://reports/chapter2-redesign-20261022/baseline/F21.json"),"offline source baseline excluded")
 check(not FileAccess.file_exists("res://reports/chapter2-redesign-20261022/rules-probe.json"),"fixture reports excluded")
 check(not ResourceLoader.exists("res://tests/ch2_redesign_rules_probe.gd"),"test scripts excluded")
 check(not FileAccess.file_exists("res://source/chapter5/architecture-original.png"),"offline oversized art source excluded")
 for path in expected.existing_compat_paths:
  if FileAccess.file_exists(str(path)):compat_present.append(path)
 for version in expected.forbidden_new_compat_versions:
  for code in expected.maps:check(not FileAccess.file_exists("res://data/compat/"+str(version)+"/"+str(code)+".json"),"no newly retained compatibility copy "+str(version)+"/"+str(code))
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"software_version":ProjectSettings.get_setting("application/config/version"),"map_revision":"0.10.6-ch2","stage_count":game.stages.size(),"maps":maps,"atlases":loaded_atlases,"existing_compatibility_count":compat_present.size(),"existing_compatibility_paths":compat_present,"new_compatibility_copies":0,"resource_root":ProjectSettings.globalize_path("res://"),"command_line":OS.get_cmdline_args(),"scope":"Independent exported app probe from isolated /private/tmp using --main-pack. Exact forty-map hashes and revision, actual terrain/prop load, object assets, report/test/source exclusions. Existing historical compatibility is recorded; this task does not clean it up or add any new compatibility copies."}
 var f=FileAccess.open(OS.get_environment("CH2_PACKAGE_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("CH2_PACKAGE ",JSON.stringify({"passed":report.passed,"checks":checks,"errors":errors,"existing_compatibility_count":compat_present.size()}));quit(0 if errors.is_empty()else 1)
