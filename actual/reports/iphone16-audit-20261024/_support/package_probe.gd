extends SceneTree
var errors=[]
var checks=[]
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func _initialize():
 var expected=JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("IPHONE_PACKAGE_EXPECTED")))
 check(str(ProjectSettings.get_setting("application/config/version",""))=="0.10.4","package version0.10.4")
 check(ProjectSettings.globalize_path("res://")!="/Users/gcc/gaocc/project/revenge-memories/actual/","package checked outside source workspace")
 for path in expected.json_hashes:
  check(FileAccess.get_sha256(str(path))==str(expected.json_hashes[path]),"current data included "+str(path))
 var score=JSON.parse_string(FileAccess.get_file_as_string("res://data/soundtrack.json"))
 check(score.tracks.size()==28,"all28new music tracks listed")
 var assets=[]
 for key in score.tracks:
  var spec=score.tracks[key];var stream=load(str(spec.path))
  check(bool(spec.asset_ready),"ready music asset "+str(key))
  check(stream is AudioStreamOggVorbis,"exported music resource loads "+str(key))
  if stream is AudioStreamOggVorbis:
   check(absf(stream.get_length()-float(spec.duration))<0.05,"exported music duration matches "+str(key))
   assets.append({"key":key,"path":spec.path,"duration":stream.get_length()})
 var script=load("res://core/phone_shell.gd")
 check(script.wants_layout_probe(PackedStringArray(["--phone-layout-probe"])),"exported phone has opt-in read-only probe")
 check(not script.wants_layout_probe(PackedStringArray()),"exported probe disabled by default")
 var ui=load("res://scenes/main.tscn").instantiate();ui.set_meta("phone",true)
 check(ui._menu_capacity()==5 and ui._menu_row_height()==34,"exported phone contains enlarged menus")
 ui.set_meta("phone",false);check(ui._menu_capacity()==10 and ui._menu_row_height()==16,"exported desktop menu behaviour retained");ui.free()
 for folder in ["res://tests","res://reports","res://tools","res://source"]:
  check(not DirAccess.dir_exists_absolute(folder),"offline directory excluded "+folder)
 var out=FileAccess.open(OS.get_environment("IPHONE_PACKAGE_REPORT"),FileAccess.WRITE)
 out.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"assets":assets,"scope":"Independent exportedPCK resource/version/data probe; no game scene enters tree and no player save access."},"  "));out.close()
 print("IPHONE_PACKAGE ",checks.size()," checks; errors: ",errors);quit(0 if errors.is_empty() else 1)
