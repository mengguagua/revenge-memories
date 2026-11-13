extends "/Users/gcc/gaocc/project/revenge-memories/art-review/phantom-20261113/source/round2.gd"
func snapshot(_name:String)->void:pass
func run()->void:
 var source="res://reports/phantom-20261113/round2-S51-object-old_record.json";var hash=FileAccess.get_sha256(source)
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path="/private/tmp/phantom-completion-working.json";root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.save_path=source;assert(ui.game.load_game());ui.game.save_path="/private/tmp/phantom-completion-working.json"
 assert(ui.game.battle_outcome.is_empty() and not ui.game.battle_settled and ui.game.flags.quest.objects.get("old_record",false))
 ui._resume_journey();await settle();await battle(false)
 assert(not abort and battles[-1].outcome=="victory")
 assert(ui.game.units.all(func(u):return not ui.game.Phantoms.is_phantom(u)))
 assert(ui.game.flags.phantom_maps["511"] and ui.game.save_game())
 var g=State.new();g.save_path=ui.game.save_path;assert(g.load_game())
 var f=FileAccess.open(PHANTOM_OUT+"completion.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":true,"source_unchanged":FileAccess.get_sha256(source)==hash,"ordinary_inputs":inputs,"natural_archive_handover":true,"temporary_units_removed":true,"save_reload":true},"  "));f.close()
 print("PHANTOM_COMPLETION natural handover,cleanup,save/reload PASS")
 ui.queue_free();await process_frame;quit()
