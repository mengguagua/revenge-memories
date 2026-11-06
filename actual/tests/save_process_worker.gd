extends SceneTree
const State=preload("res://core/game_state.gd")
func _initialize():call_deferred("run")
func run():
	var args=OS.get_cmdline_user_args()
	if args.size()!=2 or not str(args[1]).begins_with("/private/tmp/revenge-save-process-"):quit(2);return
	var directory=str(args[1])
	if args[0]=="verify":
		var result=[];var passed=true
		for name in DirAccess.get_directories_at(directory):
			var g=State.new();var folder=directory.path_join(name)
			var entry={"case":name}
			for suffix in ["", ".bak"]:
				g.save_path=folder.path_join("journey-slot-1.json")+suffix
				var valid=g.load_game();entry["primary" if suffix.is_empty() else "backup"]=valid
				passed=passed and valid
			result.append(entry)
		print("PROCESS_VERIFICATION ",JSON.stringify({"passed":passed,"cases":result}));quit(0 if passed else 1);return
	DirAccess.make_dir_recursive_absolute(directory)
	var g=State.new();g.new_game();g.slot_directory=directory;g.save_path=directory.path_join("journey-slot-1.json")
	g.flags.process_serial=0
	# A deliberately enlarged checkpoint makes the write/copy interruption
	# windows observable. It is test data, never a shipped or player save.
	g.flags.process_padding="checkpoint-stress-fixture-".repeat(20000)
	if not g.save_game() or not g.save_game():quit(3);return
	var ready=FileAccess.open(directory.path_join("ready"),FileAccess.WRITE);ready.store_string("seeded");ready.close()
	for serial in range(1,10000):
		g.flags.process_serial=serial
		if not g.save_game():quit(4);return
		OS.delay_msec(1)
	quit(5)
