extends SceneTree
## Run a copied external script against only the app's embedded PCK.
const ROOT="/Users/gcc/gaocc/project/revenge-memories/actual/"
const WORK="/private/tmp/revenge-hunapu-package/"
var labels=[]
var failures=[]
func _initialize():call_deferred("run")
func check(ok,label):
	labels.append(label)
	if not ok:failures.append(label);push_error(label)
func run():
	DirAccess.make_dir_recursive_absolute(WORK)
	check(ProjectSettings.get_setting("application/config/version","")=="0.5.3","Embedded version 0.5.3")
	check(DisplayServer.get_name()=="headless","No visible package-test window")
	check(not ResourceLoader.exists("res://tests/hunapu_play.gd"),"Development playback excluded")
	check(not FileAccess.file_exists("res://source/emotion-levin-0.5.3/generation-manifest.json"),"Raw art references excluded")
	var Art=load("res://core/hunapu_sprites.gd");var State=load("res://core/game_state.gd");var Portraits=load("res://core/portrait_library.gd")
	for kind in ["map","hub","battle"]:
		var art=Art.sprite(kind);check(not art.is_empty(),"Embedded personal sheet "+kind)
		if art.is_empty():continue
		var image=load(art.path).get_image();var colors={}
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var color=image.get_pixel(x,y)
				if color.a>0:colors[color.to_html(false)]=true
		check(colors.size()<=12,"Embedded twelve-color sheet "+kind)
		check(image.get_size()==Vector2i(art.frame_size[0]*art.frames,art.frame_size[1]),"Embedded native dimensions "+kind)
	check(Portraits.data().assets.size()==54 and not Portraits.entry("hunapu_memory").is_empty(),"All portraits and approved Hunapu identity retained")
	for key in ["hunapu_present_concern","hunapu_present_firm","hunapu_memory_grief","hunapu_memory_resolve","hunapu_memory_anger","hunapu_victory_relief"]:
		var face=Portraits.entry(key)
		check(not face.is_empty() and load(face.path).get_size()==Vector2(48,48),"Embedded expression "+key)
	var battle_image=load(Art.sprite("battle").path).get_image();var body_pixels=0
	for y in range(40,64):
		for x in range(40,64):
			if battle_image.get_pixel(124*80+x,y).a==1:body_pixels+=1
	check(body_pixels>=100,"Embedded Levin hold frame contains caster's full body")
	check(not FileAccess.file_exists("res://source/emotion-levin-0.5.3/hunapu_present_concern-generated.png") and not ResourceLoader.exists("res://tools/capture_emotion_levin_motion.gd"),"Generated originals and review tools excluded")
	var g=State.new();g.save_path=ROOT+"reports/campaign/natural-M11-deployment-save.json"
	check(g.load_game(),"Genuine old active save loads")
	var hero=g.find_unit("hunapu");var initial=hero.duplicate(true);var roster=g.roster.duplicate(true);var convoy=g.convoy.duplicate(true)
	check(Art.applies(hero) and not Art.applies(g.find_unit("otto")),"Personal art binds only to old-save Hunapu")
	var legacy_page={"speaker":"胡纳普","text":"……艾琳？把绳子解开。"}
	var original_hub=g.hub_record
	g.hub_record="P00"
	check(Portraits.speaker(g,"胡纳普",Portraits.dialogue_emotion(legacy_page)).key=="hunapu_present_concern","Old untagged active dialogue resolves correct expression in package")
	g.hub_record=original_hub
	for kind in ["map","hub","battle"]:Art.sprite(kind)
	check(hero==initial and g.roster==roster and g.convoy==convoy,"Cosmetic lookup preserves stats EXP equipment and roster")
	g.save_path=WORK+"legacy.json";check(g.save_game() and g.load_game() and g.roster==roster and g.convoy==convoy,"Old growth and equipment survive package reload")
	var source=State.read_json("res://data/legacy/graphics.json").battle.class_21_ally
	var selected=Art.battle(hero,source)
	check(selected.attack_schedule.native_timeline==source.attack_schedule.native_timeline and selected.sequences==source.sequences and selected.anchor==source.anchor,"Source animation timing, poses and anchors retained")
	check(selected.personal_source_programs.normal.frames.size()==203 and selected.personal_source_programs.normal.contact_tick==90 and selected.personal_source_programs.critical.frames.size()==263 and selected.personal_source_programs.critical.contact_tick==166,"Original independent critical program embedded")
	check(source.attack_schedule.native_timeline.before_contact.size()==85 and source.attack_schedule.native_timeline.after_contact.size()==104,"Original 85/104 melee ticks embedded")
	var report={"passed":failures.is_empty(),"version":"0.5.3","checks":labels.size(),"labels":labels,"failures":failures,"scope":"External headless probe of the signed app embedded PCK. Old save read only; all writes isolated in /private/tmp. Not a natural battle victory."}
	var file=FileAccess.open(ROOT+"reports/emotion-levin-0.5.3/package-checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("PACKAGE_HUNAPU ",labels.size()," FAILURES ",failures);quit(0 if failures.is_empty() else 1)
