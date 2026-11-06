extends "res://tests/full_audit_ch4.gd"
func run()->void:
 late_label="promotion-copy";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=LATE_OUT+"current/current-after-408.json";var copy=late_folder+"working.json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(copy))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=copy;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Promotion copy load failed")
 if not abort:ui._resume_journey();await settle()
 var changes=JSON.parse_string(FileAccess.get_file_as_string(LATE_OUT+"promotion-copy-changes.json"))
 var pages=[]
 for change in changes:pages.append({"speaker":"旁白","text":change.after})
 if not abort:
  ui.play_pages(pages,"hub","");await settle()
 var restored=""
 for page in observed_content:restored+=str(page.text).replace("\n","")
 var expected=""
 for page in pages:expected+=str(page.text)
 if pages.size()!=3 or observed_content.is_empty() or restored!=expected:record_failure("Promotion pages omitted or duplicated text")
 var f=FileAccess.open(late_folder+"pagination.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"failures":failures,"source":source_checkpoint,"content":observed_content,"inputs":inputs,"returned_view":ui.view,"text_preserved":restored==expected,"scope":"Updated real source strings passed through actual main.play_pages pagination and normal confirm input; no battle repeated or gameplay state edited."},"  "));f.close()
 print("PROMOTION_COPY ",JSON.stringify({"passed":not abort,"pages":observed_content.size(),"failures":failures}));ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
