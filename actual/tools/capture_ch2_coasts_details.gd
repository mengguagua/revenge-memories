extends "res://tests/tactical_review_play.gd"
const DETAIL_OUT="res://reports/chapter2-environment-20261023/coasts/details/"
var vp:SubViewport
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(DETAIL_OUT))
 vp=SubViewport.new();vp.size=Vector2i(562,320);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
 var shots=[]
 for suffix in ["entry","object-pilot_prison"]:
  var source="res://reports/chapter2-environment-20261023/play/round1-coasts/round1-coasts-F25-"+suffix+".json"
  var original=FileAccess.get_file_as_string(source).sha256_text()
  ui=load("res://scenes/main.tscn").instantiate();vp.add_child(ui);await process_frame;ui.instant_mode=true;ui.game.save_path=source
  if not ui.game.load_game():record_failure("Cannot load prison detail checkpoint");break
  ui.game.save_path=DETAIL_OUT+"unused-working.json";ui.view=ui.game.mode;ui.ui_mode="inspect";ui._clear_menu();ui.notice_time=0;ui.phase_time=0
  ui._focus_battle(Vector2i(26,20),true);ui.queue_redraw()
  for i in range(4):await process_frame
  await RenderingServer.frame_post_draw
  var path=DETAIL_OUT+"F25-"+suffix+".png";vp.get_texture().get_image().save_png(path)
  shots.append({"path":path,"source":source,"source_sha256":original,"mode":ui.game.mode,"turn":ui.game.turn,"prison_open":ui.game.flags.quest.objects.get("pilot_prison",false),"layout_errors":ui.layout_errors.duplicate()})
  if FileAccess.get_file_as_string(source).sha256_text()!=original:record_failure("Original detail source changed")
  ui.queue_free();await process_frame;ui=null
 var f=FileAccess.open(DETAIL_OUT+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"shots":shots,"scope":"Genuine input checkpoints; camera focus only, no actor/stat/quest edits.","background_guard":true},"  "));f.close()
 vp.queue_free();await process_frame;quit(1 if abort else 0)
