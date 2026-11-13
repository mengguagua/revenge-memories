extends "res://core/phone_shell.gd"
const RecordedMain=preload("/Users/gcc/gaocc/project/revenge-memories/art-review/phantom-20261113/source/preview_main.gd")
func _ready()->void:
 game_view=SubViewport.new();game_view.size=Vector2i(1704,960);game_view.size_2d_override=Vector2i(426,240);game_view.size_2d_override_stretch=true;game_view.render_target_update_mode=SubViewport.UPDATE_ALWAYS;game_view.handle_input_locally=true
 add_child(game_view)
 game_ui=RecordedMain.new();game_ui.set_meta("phone",true)
 game_ui.game.slot_directory=journal_directory_override;game_ui.game.save_path=journal_directory_override+"/working.json"
 game_view.add_child(game_ui);game_ui.set_process_input(false);_layout()
