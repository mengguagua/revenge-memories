extends RefCounted
## A journal remains in the ordinary hub checkpoint while this introduction runs.
## Character offsets survive changes in width without skipping any source text.
const SCRIPT_PATH="res://data/story_intro.json"
const LETTERS_PER_SECOND=30.0
const TEXT_REVISION=2
const ORIGINAL_SCENE_STARTS=[0,32,85,121]
var ui
var scenes:Array=[]
var rows:Array=[]
var index := -1
var reveal := 0.0
var scene := 0
var previous_scene := -1
var fade := 1.0
var width := 0.0
var tick_left := 0.0
var audit:Dictionary={}

func _init(owner) -> void:
	ui=owner;scenes=ui.GameState.read_json(SCRIPT_PATH).scenes

func narration_lines(text:String,maximum:float) -> Array:
	# Prefer complete sentences, then complete clauses on compact screens.
	# Retain every punctuation mark and never trim or rewrite the script.
	var lines:Array=[];var line="";var clause=""
	for character in text:
		clause+=character
		if character not in ["，","。","！","？","；","："]:continue
		if not line.is_empty() and ui._text_width(line+clause)>maximum:lines.append(line);line=""
		if ui._text_width(clause)>maximum:
			var wrapped=ui._wrapped_lines(clause,maximum)
			for n in range(wrapped.size()-1):lines.append(wrapped[n])
			line+=wrapped[-1]
		else:line+=clause
		clause=""
		if character in ["。","！","？"]:lines.append(line);line=""
	if not clause.is_empty():
		if not line.is_empty() and ui._text_width(line+clause)>maximum:lines.append(line);line=""
		line+=clause
	if not line.is_empty():lines.append_array(ui._wrapped_lines(line,maximum))
	return lines

func reflow() -> void:
	var available=ui.get_viewport_rect().size.x-32.0
	if available==width:return
	width=available;rows.clear();var offset=0
	for n in range(scenes.size()):
		for line in narration_lines(str(scenes[n].text),width):
			rows.append({"text":line,"scene":n,"start":offset})
			offset+=line.length()
	index=-1
	var cursor=int(ui.game.flags.get("story_intro_offset",-1))
	for n in range(rows.size()):
		if int(rows[n].start)<=cursor:index=n
	if index>=0:scene=int(rows[index].scene)

func start() -> void:
	ui.view="story_intro";ui.game.mode="hub";ui.busy=false;ui.held_direction=Vector2i.ZERO
	var flags: Dictionary=ui.game.flags
	if int(flags.get("story_intro_text_revision",1))<TEXT_REVISION:
		var saved_offset=int(flags.get("story_intro_offset",-1))
		var current_start=0
		# Edited paragraphs resume at their own start so the old offset cannot skip new text.
		for n in range(1,mini(scenes.size(),ORIGINAL_SCENE_STARTS.size())):
			current_start+=str(scenes[n-1].text).length()
			if saved_offset<ORIGINAL_SCENE_STARTS[n]:break
			flags.story_intro_offset=current_start
	flags.story_intro_text_revision=TEXT_REVISION
	ui._clear_menu();scene=0;width=0;reflow();reveal=0;fade=0;previous_scene=-1;tick_left=0
	ui.audio.play_music("opening");ui.game.save_game();ui.queue_redraw()

func process(delta:float) -> void:
	reflow();fade=minf(1.0,fade+delta/0.65)
	if index>=0 and reveal<str(rows[index].text).length():
		var before=int(reveal);reveal=minf(str(rows[index].text).length(),reveal+delta*LETTERS_PER_SECOND)
		tick_left=maxf(0.0,tick_left-delta)
		if int(reveal)>before and tick_left<=0.0:
			ui.audio.play_sfx("story_type");tick_left=0.055
	ui.queue_redraw()

func accept() -> void:
	reflow()
	if index>=0 and reveal<str(rows[index].text).length():
		reveal=str(rows[index].text).length();ui.queue_redraw();return
	index+=1;reveal=0;tick_left=0
	if index>=rows.size():
		ui.game.flags.erase("story_intro_pending");ui.game.flags.erase("story_intro_offset");ui.game.flags.erase("story_intro_index")
		ui.game.flags.erase("story_intro_text_revision")
		ui.game.flags.story_intro_done=true;ui.hub_controller.enter_room("P00");return
	var next=int(rows[index].scene)
	if next!=scene:previous_scene=scene;scene=next;fade=0
	ui.game.flags.story_intro_offset=int(rows[index].start);ui.game.save_game();ui.queue_redraw()

func _picture(n:int,area:Rect2,alpha:float) -> Rect2:
	var texture=ui._tex(str(scenes[n].image));var scale=minf(area.size.x/texture.get_width(),area.size.y/texture.get_height())
	var size=texture.get_size()*scale;var rect=Rect2(area.get_center()-size/2.0,size)
	ui.draw_texture_rect(texture,rect,false,Color(1,1,1,alpha));return rect

func draw() -> void:
	reflow();var bounds=ui._visible_native_rect();ui.draw_rect(bounds,Color.BLACK)
	var art_area=Rect2(bounds.position+Vector2(4,4),Vector2(bounds.size.x-8,156))
	if previous_scene>=0 and fade<1.0:_picture(previous_scene,art_area,1.0)
	var picture=_picture(scene,art_area,fade)
	var text_area=Rect2(bounds.position.x+16,176,bounds.size.x-32,20)
	var line=str(rows[index].text) if index>=0 and index<rows.size() else ""
	# Center using the complete row so letters appear without horizontal jitter.
	var ink=Rect2(Vector2(text_area.get_center().x-ui._text_width(line)/2.0,180),Vector2(ui._text_width(line),12))
	if not text_area.encloses(ink):ui.layout_errors.append("opening narration outside content safe area")
	if not line.is_empty():ui._text(line.substr(0,int(reveal)),ink.position,Color("eee8d2"))
	ui._center_text("确认 · 开始故事" if index<0 else "确认 · 进入序章" if index==rows.size()-1 else "确认 · 下一行",Rect2(bounds.position.x+16,216,bounds.size.x-32,16),Color("a7a19a"))
	audit={"picture":picture,"art_area":art_area,"text_area":text_area,"ink":ink,"scene":scene,"row":index,"row_count":rows.size(),"fade":fade}
