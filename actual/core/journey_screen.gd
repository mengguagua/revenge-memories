extends RefCounted
## Homepage / slot selection state machine. Rendering is shared by design boards
## and the game, so their geometry, text and animation remain identical.
var ui
var intent := "load"
var return_view := "title"
var selected := 0
var confirm_choice := 0
var records: Array=[]
var message := ""
var opened_at := 0.0
var audit: Array=[]

func _init(owner) -> void:ui=owner

func refresh() -> void:records=ui.game.slot_records()

func open(action: String) -> void:
	intent=action;return_view=ui.view;selected=0;confirm_choice=0;message=""
	refresh()
	if intent=="new":
		for i in range(records.size()):
			if not records[i].exists:selected=i;break
	elif intent=="save":selected=ui.game.active_slot-1
	else:
		var latest=-1
		for i in range(records.size()):
			if records[i].valid:
				var modified=FileAccess.get_modified_time(records[i].path)
				if modified>latest:latest=modified;selected=i
	ui._clear_menu();ui.view="journal";ui.held_direction=Vector2i.ZERO;opened_at=ui.elapsed

func direction(d: Vector2i) -> void:
	if ui.view=="journal_confirm":confirm_choice=1-confirm_choice
	else:selected=posmod(selected+(d.x if d.x!=0 else d.y),5);message=""
	ui.audio.play_sfx("menu_move")

func accept() -> void:
	if ui.view=="journal_confirm":
		if confirm_choice==0:ui.view="journal";return
		commit();return
	var record=records[selected]
	if intent=="load":
		if not record.exists:message="尚无记录，请选择其他槽位";return
		if not record.valid:message="记录无法读取，原件已保留";return
		if ui.game.load_slot(selected+1):ui._resume_journey()
		else:message="读取失败，原件已保留"
	elif record.exists:
		confirm_choice=0;ui.view="journal_confirm"
	else:commit()

func commit() -> void:
	if intent=="new":
		# Reserve and write the new journal before allowing the story controller
		# to auto-save. Failure keeps the slot screen open for another choice.
		var old=ui.game;var fresh=ui.GameState.new()
		fresh.slot_directory=old.slot_directory;fresh.new_game()
		if not fresh.save_to_slot(selected+1):message="保存失败，请另选槽位";ui.view="journal";return
		ui.game=fresh;ui._new_journey_in_slot();return
	if ui.game.save_to_slot(selected+1):
		ui.view=return_view;saved_left=3.0;saved_time=ui.game.Journals.timestamp(int(Time.get_unix_time_from_system()));ui.held_direction=Vector2i.ZERO
	else:message="保存失败，已有记录保留";ui.view="journal"

func cancel() -> void:
	if ui.view=="journal_confirm":ui.view="journal";confirm_choice=0
	else:ui.view=return_view;message="";ui.held_direction=Vector2i.ZERO
	ui.audio.play_sfx("menu_cancel")

var art
var saved_left := 0.0
var saved_time := ""
func prepare_art() -> void:
	if art==null:art=load("res://core/journey_art.gd").new(ui)
func title_button(index: int) -> Rect2:
	prepare_art();return art.title_button(index)
func mouse(point: Vector2) -> void:
	prepare_art()
	if ui.view=="journal_confirm":
		for i in range(2):
			if art.confirm_button(i).has_point(point):confirm_choice=i;accept();return
		return
	for i in range(5):
		if art.row_rect(i).has_point(point):selected=i;accept();return
func draw() -> void:
	prepare_art();art.draw(self);audit=art.audit.duplicate(true)
func draw_saved() -> void:
	if saved_left<=0:return
	prepare_art();art.saved(self)
