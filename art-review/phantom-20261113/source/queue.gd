extends "/Users/gcc/gaocc/project/revenge-memories/art-review/phantom-20261113/source/round1.gd"
func run()->void:
 phantom_screen=SubViewport.new();phantom_screen.size=Vector2i(1334,750);phantom_screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(phantom_screen)
 phantom_phone=Phone.new();phantom_phone.journal_directory_override="/private/tmp/phantom-preview-20261113";phantom_screen.add_child(phantom_phone);await process_frame
 ui=phantom_phone.game_ui;ui.instant_mode=true;ui.game.save_path="/private/tmp/phantom-preview-20261113/rank3-capacity.json";assert(ui.game.load_game());ui.game.save_path="/private/tmp/phantom-queue-20261113.json"
 assert(ui.game.living("player").size()==26);ui._resume_journey();await settle();ui.set_physics_process(false)
 key(KEY_S);choose("end_turn");await settle();assert(not abort and ui.game.turn==2)
 assert(ui.phantom_queue_checks.is_empty())
 key(KEY_S);choose("end_turn");await settle();assert(not abort)
 var checks=ui.phantom_queue_checks.filter(func(row):return row.turn==2)
 assert(checks.size()==6 and checks.all(func(row):return row.acted and row.turn>row.born))
 var f=FileAccess.open(PHANTOM_OUT+"queue.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":true,"normal_friends_at_start":20,"phantoms_at_start":6,"birth_turn_no_actions":true,"ordinary_key_inputs":inputs,"six_next_turn_actions":checks},"  "));f.close()
 print("PHANTOM_26_QUEUE six wait on birth, six act next turn PASS")
 phantom_phone.queue_free();await process_frame;quit()
