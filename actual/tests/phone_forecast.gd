extends SceneTree
const Panels=preload("res://core/battle_panel_layout.gd")
const OUT="res://reports/iphone-layout-20261022/forecast-geometry.json"
var checks=0
var errors=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks+=1
	if not ok:errors.append(label);push_error(label)
func run():
	for width in [256,320,384,406,426]:
		var canvas=Rect2(-floori(float(width-256)/2),0,width,240)
		for x in range(8,width-8,24):
			for y in [16,64,112,118,120,121,122,123,124,128,176,224]:
				var layout=Panels.forecast(canvas.position+Vector2(x,y),canvas)
				check(layout.valid and canvas.grow(-8).encloses(layout.panel) and not layout.panel.intersects(layout.focus),"full forecast clears sprite and arrow %d/%d/%d"%[width,x,y])
	for width in [256,406]:
		var canvas=Rect2(-floori(float(width-256)/2),0,width,240)
		var anchor=Vector2(128,120)
		var combatants=[Rect2(anchor+Vector2(-6,10),Vector2(28,28)),Rect2(anchor-Vector2(6,6),Vector2(28,28))]
		var layout=Panels.forecast(anchor,canvas,[],combatants)
		check(layout.valid and layout.combatants_protected and combatants.all(func(rect):return not layout.panel.intersects(rect)),"both adjacent combatants remain visible "+str(width))
	var difficult=[Rect2(90,138,28,28),Rect2(124,112,28,28)]
	var narrow=Panels.forecast(Vector2(130,118),Rect2(0,0,256,240),[],difficult)
	check(narrow.valid and not narrow.combatants_protected and narrow.has("fallback_reason") and not narrow.panel.intersects(narrow.focus),"minimum canvas reports ranged-space fallback and keeps full target forecast")
	var phone=Panels.forecast(Vector2(130,118),Rect2(-75,0,406,240),[],difficult)
	check(phone.valid and phone.combatants_protected and phone.stacked and difficult.all(func(rect):return not phone.panel.intersects(rect)),"phone side card clears difficult ranged pair")
	var ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/forecast-unused-records";root.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false)
	for ch in "0123456789%":
		var glyph=ui._preview_glyph(ch)
		check(not glyph.is_empty() and int(glyph.rect[3])==12,"native 12px glyph is present "+ch)
		var source=ui.chinese_font.glyphs["０１２３４５６７８９".substr("0123456789".find(ch),1) if ch!="%" else "％"]
		var ink=source.ink_bounds;var left=int(glyph.rect[0])-int(source.rect[0])
		check(int(ink[0])>=left and int(ink[0])+int(ink[2])<=left+int(glyph.rect[2]),"numeric glyph crop retains every ink column "+ch)
	for value in ["生命255/255","伤害254 命中100%","必杀100%","超出攻击范围","不能造成伤害"]:
		check(ui._preview_text_width(value)<=104,"worst-case forecast line fits column "+value)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT.get_base_dir()))
	var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"scope":"Targeted preview geometry and actual numeric font metadata; no gameplay mutation or campaign replay."},"  "));f.close()
	print("PHONE_FORECAST_GEOMETRY ",checks," checks; errors: ",errors)
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
