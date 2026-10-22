extends SceneTree
const State=preload("res://core/game_state.gd")
var errors=[]
var checks=0
func check(ok:bool,label:String):
 checks+=1
 if not ok:errors.append(label);push_error(label)
func _initialize():
 var expected=State.read_json(OS.get_environment("MAP_POLISH_EXPECTED"));var game=State.new()
 for code in expected.maps:
  var m=expected.maps[code];var path="res://data/stages/"+str(code)+".json"
  check(FileAccess.get_file_as_string(path).sha256_text()==str(m.sha256),str(code)+" exact map data in app")
  var d=State.read_json(path);check(str(d.tactical_review_version)==str(m.revision),str(code)+" correct map revision")
  var texture=load(str(d.art_atlas))
  check(texture is Texture2D and texture.get_width()>0 and texture.get_height()>0,str(code)+" runtime terrain texture loads")
  for p in d.art_props:check(ResourceLoader.exists(str(p.path)),str(code)+" prop in app: "+str(p.path))
 check(game.stages.size()==40,"all forty stages retained")
 check(not FileAccess.file_exists("res://reports/map-polish-20261022/baseline/M12.json"),"offline review baseline excluded")
 check(not FileAccess.file_exists("res://data/compat/0.5.0/M12.json"),"no new old-map compatibility copies")
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"version":ProjectSettings.get_setting("application/config/version"),"map_revision":"0.10.2","stage_count":game.stages.size(),"scope":"Independent exported app exact JSON fingerprints, texture/prop availability, forty-stage retention and review-data exclusion."}
 var f=FileAccess.open(OS.get_environment("MAP_POLISH_PACKAGE_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("MAP_POLISH_PACKAGE ",JSON.stringify(report));quit(0 if errors.is_empty() else 1)
