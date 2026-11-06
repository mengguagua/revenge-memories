extends SceneTree
const Phone=preload("res://core/phone_shell.gd")
const OUT="res://reports/iphone16-audit-20261024/layout-probe-checks.json"
var checks=[]
var errors=[]
var phone
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
	check(not Phone.wants_layout_probe(PackedStringArray()),"ordinary launch does not enable probe")
	check(not Phone.wants_layout_probe(PackedStringArray(["--phone-layout-probe=false"])),"similar argument cannot accidentally enable probe")
	check(Phone.wants_layout_probe(PackedStringArray(["--phone-layout-probe"])),"exact opt-in flag enables probe")
	if not Phone.wants_layout_probe(OS.get_cmdline_user_args()):push_error("Run this fixture with -- --phone-layout-probe");quit(1);return
	var viewport=SubViewport.new();viewport.size=Vector2i(2556,1179);root.add_child(viewport)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116)
	phone.layout_probe_completed.connect(done);viewport.add_child(phone)
	check(phone.game_ui==null and phone.get_child_count()==0,"probe intercepts ready before main game or journal reader exists")
	check(not phone.is_processing() and not phone.is_processing_input(),"diagnostic branch cannot process gameplay or player inputs")
func done(report:Dictionary):
	check(phone.game_ui==null and not report.game_instantiated,"main game stays uninstantiated through entire probe")
	check(phone.get_child_count()==1 and phone.get_child(0) is SubViewport,"probe contains only the measuring viewport, no game/audio/journal nodes")
	check(phone.game_view.get_child_count()==0,"measurement viewport never owns game scene")
	check(report.logical_size==[364,240] and report.integer_scale==4,"probe reuses actual phone geometry")
	check(report.contexts.size()==4 and report.geometry_errors.is_empty(),"probe measures all four control contexts with no geometry errors")
	check(not report.player_records_read and not report.player_records_written,"probe report declares no journal access")
	var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"report":report,"note":"Only this test harness writes its report; shipping opt-in branch only prints stdout and exits."},"  "));f.close()
	print("PHONE_LAYOUT_PROBE_CHECKS ",checks.size()," checks; errors: ",errors)
	# The diagnostic routine exits the tree after its signal; fail loudly before it does.
	if not errors.is_empty():OS.set_environment("PHONE_LAYOUT_PROBE_TEST_FAILED","1")
