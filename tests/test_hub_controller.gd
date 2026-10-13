extends SceneTree
const State = preload("res://core/game_state.gd")
const Controller = preload("res://core/hub_controller.gd")
class SilentAudio:
	extends RefCounted
	func play_sfx(_key): pass
	func play_music(_key): pass
	func play_request(_id): pass
	func play_hub(_id): pass
	func play_world(_id): pass
	func play_jingle(_id): pass
class TestUI:
	extends Control
	var game = State.new()
	var audio = SilentAudio.new()
	var graphics: Dictionary = State.read_json("res://data/graphics.json")
	var held_direction := Vector2i.ZERO
	var busy := false
	var menu_items: Array = []
	var view := "hub"
	var instant_mode := true
	var battle_entries := 0
	var chapter_entries := 0
	func _begin_existing_battle():
		battle_entries += 1
		view = "battle"
	func _show_campaign_chapter():
		chapter_entries += 1
		view = "chapter"
	func _wrapped_lines(text: String, width: float) -> Array[String]:
		var out: Array[String] = []
		for paragraph in text.split("\n"):
			var line := ""
			var size := 0.0
			for c in paragraph:
				var advance := 8.0 if c.unicode_at(0)<128 else 12.0
				if size+advance>width and not line.is_empty():
					out.append(line);line="";size=0
				line+=c;size+=advance
			out.append(line)
		return out
var checks := 0
var failures := 0
var ui
var hub
func _initialize() -> void:
	ui = TestUI.new()
	root.add_child(ui)
	ui.game.save_path = "res://reports/hub-controller-test-save.json"
	ui.game.new_game()
	hub = Controller.new(ui)
	hub.enter(1,Vector2i(5,10))
	_check(ui.view == "hub_choice", "Training VM opens original chapter/save dialog")
	_drain()
	_check(ui.view == "hub" and ui.game.hub_position == Vector2i(5,10), "Training walks original up/down sequence and returns")
	_check(ui.game.flags.get("source_flag_17",false), "Training enables Lukas report trigger")
	_place(Vector2i(20,8),Vector2i.LEFT)
	hub.accept()
	_check(ui.view == "hub_choice", "Back toNPC opens menu, never talks")
	hub.cancel()
	_place(Vector2i(20,8),Vector2i.RIGHT)
	hub.accept()
	_check(ui.view == "hub_dialogue", "Front-facing Lukas report shows Chinese pages")
	_drain()
	_check(ui.game.flags.get("source_flag_18",false), "Lukas report runs relocation flag")
	_check(hub._position(hub.actors[2]) == Vector2i(6,2), "Mycen relocated to source spawn template2")
	_place(Vector2i(6,3),Vector2i.UP)
	hub.accept();_drain()
	_check(ui.game.flags.get("source_flag_19",false), "Mycen refusal enables Lukas recruitment")
	_check(hub._position(hub.actors[6]) == Vector2i(16,8), "Original Lukas spawn template1")
	_place(Vector2i(15,8),Vector2i.RIGHT)
	hub.accept();_drain()
	_check(ui.game.party.has("lukas") and ui.game.party.size()==2, "Only scripted Lukas joins")
	_check(hub._actor_at(Vector2i(16,8)) == 0, "Recruited NPC disappears")
	_check(not ui.game.party.has("gray"), "Unspoken Gray not auto-recruited")
	_check(ui.game.hub_used.get("event_vm",{}).is_empty(), "Finished script clears resume checkpoint")
	# Treasure cannot duplicate and retains original tile change.
	hub.enter(2,Vector2i(17,3))
	var before: int = ui.game.convoy.alm.size()
	_place(Vector2i(17,3),Vector2i.RIGHT)
	hub.accept();_drain()
	_check(int(ui.game.roster.alm.item_id)==15, "First free carrier receives original LightningSword")
	_check(bool(ui.game.hub_used.get("2:0",false)), "Treasure marked consumed")
	_check(hub._tile(Vector2i(18,3))==236, "Opened chest uses original tile236")
	hub.accept();hub.cancel()
	_check(ui.game.convoy.alm.size()==before, "Repeated chest cannot duplicate item")
	# Shared spring count and upgrade mechanics.
	hub.enter(3,Vector2i(7,3))
	var defence := int(ui.game.roster.alm.defence)
	hub._spring(hub.room.features[0],0)
	hub.accept();_drain()
	_check(int(ui.game.roster.alm.defence)==defence+1, "Defence spring grants exactly1")
	_check(int(ui.game.hub_used.spring_0)==2, "First shrine pair shares three uses")
	hub._spring(hub.room.features[1],1);hub.accept();_drain()
	_check(int(ui.game.hub_used.spring_0)==1, "Opposite spring consumes same pool")
	hub._spring(hub.room.features[0],0);hub.accept();_drain()
	_check(bool(ui.game.hub_used["3:0"]) and bool(ui.game.hub_used["3:1"]), "Both springs dry together")
	# Shrine promotion, with explicit character/class choice.
	ui.game.recruit("kliff")
	ui.game.roster.kliff.level=3
	hub._shrine();hub.accept()
	_check(ui.view=="hub_choice" and hub.choices.size()==5, "Villager promotion offers five source professions")
	hub.choice_index=3;hub.accept();_drain()
	_check(int(ui.game.roster.kliff.class_id)==15, "Selected Mage promotion applied")
	# Courier cancellation retains NPC/event; confirmed send moves one item.
	ui.game.roster.alm.item_id=15
	hub.script_id=41;hub.program=ui.game.hubs.scripts['41'].instructions;hub.pc=1
	hub._courier();hub.cancel()
	_check(int(ui.game.roster.alm.item_id)==15 and hub.script_id<0, "Cancelled courier does not consume item/program")
	hub.script_id=41;hub.program=[];hub.pc=0
	hub._courier();hub.accept();_drain()
	_check(int(ui.game.roster.alm.item_id)==0 and ui.game.convoy.celica.has(15), "Courier sends to opposite army convoy")
	# Room50 is a genuine entry battle. Signs are never battle triggers.
	var entries := int(ui.battle_entries)
	hub.enter(50,Vector2i(8,12))
	_check(ui.battle_entries==entries+1 and ui.game.stage_id==49, "Dungeon entry invokes original map49 encounter")
	hub.resume()
	_check(ui.view=="hub", "Battle return resumes walking without retrigger")
	_check(ui.game.hub_used.dungeon_visited==1, "Dungeon traversal visit bit persists")
	hub.enter(48,Vector2i(17,5))
	entries=ui.battle_entries
	_place(Vector2i(17,5),Vector2i.RIGHT)
	hub.accept()
	_check(ui.view=="hub_dialogue" and ui.battle_entries==entries, "Feature2 is original shield-choice sign")
	_drain()
	# Last dungeon reused trigger rows should remain dormant inroom36.
	hub.enter(36,Vector2i(10,14))
	_check(ui.game.hub_script(0,Vector2i(6,21))==-1, "Room36 shared out-of-bounds trigger disabled")
	_check(hub.room.width==24 and hub.room.height==18, "Room36 keeps original background dimensions")
	# Feature kinds3/4/6 are persistent tile patterns, not interaction verbs.
	ui.game.hub_used['9:0']=true;ui.game.hub_used['9:1']=false
	hub.enter(9,Vector2i(5,8))
	_check(hub._tile(Vector2i(3,1))==207 and hub._tile(Vector2i(3,13))==80,"Original harbor north passage closed before chapter3")
	_check(not hub._feature(Vector2i(3,13)),"Harbor passage feature is not a fabricated boat interaction")
	ui.game.hub_used['9:0']=false;ui.game.hub_used['9:1']=true
	hub.resume()
	_check(hub._tile(Vector2i(3,1))==80 and hub._tile(Vector2i(3,13))==207,"Chapter3 clears north passage pattern and applies south closure")
	ui.game.hub_used['15:0']=true
	hub.enter(15,Vector2i(8,8))
	_check(hub._tile(Vector2i(11,1))==95,"Chapter4 source temple gate bit applies original open tile")
	hub.enter(19,Vector2i(5,8))
	hub._special(1)
	_check(ui.game.hub_used.get('19:0',false) and hub._tile(Vector2i(7,1))==185,"Completed sluice animation persists feature0 and source open-gate pattern")
	hub.resume()
	_check(hub._tile(Vector2i(7,1))==185,"Sluice remains open after resume")
	ui.game.roster.alm.promoted=true
	ui.game.flags.celica_promoted=true
	_check(hub._portrait_index(1)==int(ui.graphics.character_portraits['36']) and hub._portrait_index(1)==20,"Promoted Alm follows source virtual character36 portrait20")
	_check(hub._portrait_index(2)==int(ui.graphics.character_portraits['37']) and hub._portrait_index(2)==11,"Promoted Celica follows source virtual character37 portrait11")
	_check(hub._portrait_index(43)==52 and hub._portrait_index(134)==42 and hub._portrait_index(141)==31,"Named source NPCs use their verified portrait selectors")
	# Page every source dialogue using native width constraints.
	var rendered_pages := 0
	for group in hub.texts:
		hub._dialogue(int(group))
		for page in hub.pages:
			rendered_pages+=1
			var limit:=3 if page.portrait else 4
			_check(str(page.text).split("\n").size()<=limit,"Chinese source page fits dialogue line count")
	_check(rendered_pages>=495,"Every original dialogue source page is reachable")
	var report := FileAccess.open("res://reports/hub-controller-verification.json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"failures":failures,"dialogue_display_pages":rendered_pages,"scope":"native event VM/training/recruitment/facing/treasure/spring/promotion/courier/dungeon/sign/pagination"},"  "))
	if FileAccess.file_exists(ui.game.save_path):DirAccess.remove_absolute(ui.game.save_path)
	hub.dispose()
	hub = null
	ui.free()
	print("FE2 hub controller: %d checks, %d failures" % [checks,failures])
	quit(1 if failures else 0)
func _drain() -> void:
	var limit:=0
	while ui.view in ["hub_dialogue","hub_choice"] and limit<1500:
		limit+=1
		if ui.view=="hub_choice":
			if hub.script_id>=0 and hub.choice_title.contains("记录进度"):hub.choice_index=1
			else:break
		hub.reveal=9999
		hub.accept()
	_check(limit<1500,"Dialogue/script completes without input loop")
func _place(at: Vector2i,dir: Vector2i) -> void:
	ui.game.hub_position=at
	hub.render_position=Vector2(at)*16
	hub.facing=dir
func _check(ok: bool,text: String) -> void:
	checks+=1
	if not ok:
		failures+=1
		push_error(text)
