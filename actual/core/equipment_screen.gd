extends RefCounted
## Read-only selection/forecast; only the explicit confirmation moves equipment.
const Comparison=preload("res://core/equipment_comparison.gd")
const Art=preload("res://core/journey_art.gd")
const INK=Color("eee8d2")
const MUTED=Color("c2ccd8")
const GOLD=Color("d6ba80")
const UP=Color("a5ddb0")
const DOWN=Color("edaaa1")
const PAGE_SIZE=5
const DETAILS_PAGE_SIZE=6
var ui
var art
var return_view="world"
var item_index=-1
var target_id=0
var members: Array=[]
var selected=0
var first=0
var button=1
var more=false
var details_page=0
var message=""
var audit: Array=[]

func _init(owner):ui=owner;art=Art.new(ui)
func active() -> bool:return ui.view in ["equipment_members","equipment_preview"]
func open(index: int) -> void:
	var stored: Array=ui.game.convoy.get(ui.game.route,[])
	if index<0 or index>=stored.size():ui._notice("道具已变化，请重新选择");return
	return_view=ui.view;item_index=index;target_id=int(stored[index]);selected=0;first=0;button=1;more=false;details_page=0;message=""
	members=ui.game.party.filter(func(id):return ui.game.roster.has(id))
	if members.is_empty():ui._notice("没有可分配的队员");return
	ui._clear_menu();ui.view="equipment_members";ui.held_direction=Vector2i.ZERO

func preview() -> Dictionary:
	if members.is_empty():return {}
	var result=ui.game.equipment_preview(str(members[selected]),item_index)
	if result.is_empty() or int(result.target_id)!=target_id:return {}
	return result

func member_label(id: String) -> String:
	var unit: Dictionary=ui.game.roster[id]
	return str(unit.name_zh)+" · "+Comparison.profession_name(unit,ui.game.catalog.classes)+" · "+Comparison.held_name(unit)

func direction(d: Vector2i) -> void:
	message=""
	if ui.view=="equipment_members":
		selected=posmod(selected+(d.y if d.y!=0 else d.x),members.size())
		first=clampi(first,selected-page_size()+1,selected)
	elif more and d.y!=0:
		details_page=clampi(details_page+d.y,0,details_page_count()-1)
	else:button=posmod(button+(d.x if d.x!=0 else d.y),3)
	ui.audio.play_sfx("menu_move")

func accept() -> void:
	if ui.view=="equipment_members":
		var data=preview()
		if data.is_empty():message="道具已变化，请返回重新选择";return
		ui.view="equipment_preview";more=false;details_page=0;button=1 if data.can_equip else 0;message="";return
	if button==0:cancel();return
	if button==2:toggle_details();return
	var receipt=ui.game.equip_from_convoy(str(members[selected]),item_index,target_id)
	if not receipt.valid:message=str(receipt.message);return
	ui.view=return_view;ui.held_direction=Vector2i.ZERO;ui._open_camp_menu();ui._notice(str(receipt.message),3.0)

func cancel() -> void:
	if ui.view=="equipment_preview":ui.view="equipment_members";message="";more=false
	else:
		ui.view=return_view;ui.held_direction=Vector2i.ZERO;ui._camp_action("withdraw")
	ui.audio.play_sfx("menu_cancel")

func toggle_details() -> void:
	if ui.view=="equipment_preview":more=not more;details_page=0;message=""

func panel_rect() -> Rect2:
	var bounds=ui._visible_native_rect();var width=minf(360,bounds.size.x-16)
	return Rect2(bounds.get_center().x-width/2,4,width,232)
func two_line_members() -> bool:
	var width=panel_rect().size.x-32
	return width<288 or members.any(func(id):return ui._text_width(member_label(str(id)))>width)
func page_size() -> int:return 3 if two_line_members() else PAGE_SIZE
func row_rect(slot: int) -> Rect2:
	var r=panel_rect();var height=44 if two_line_members() else 28
	return Rect2(r.position.x+8,48+slot*height,r.size.x-16,height)
func back_rect() -> Rect2:
	var r=panel_rect();return Rect2(r.position.x+40,200,r.size.x-80,28)
func button_rect(index: int) -> Rect2:
	var r=panel_rect();var width=(r.size.x-32)/3
	return Rect2(r.position.x+8+index*(width+8),200,width,28)
func page_rect(step: int) -> Rect2:
	var r=panel_rect();return Rect2(r.position.x+16 if step<0 else r.end.x-32,184,16,14)
func details_page_rect(step: int) -> Rect2:
	var r=panel_rect();return Rect2(r.position.x+12 if step<0 else r.end.x-36,176,24,20)

func mouse(point: Vector2) -> void:
	if ui.view=="equipment_members":
		for slot in range(mini(page_size(),members.size()-first)):
			if row_rect(slot).has_point(point):selected=first+slot;accept();return
		if back_rect().has_point(point):cancel();return
		for step in [-1,1]:
			if page_rect(step).has_point(point):
				selected=clampi(selected+step*page_size(),0,members.size()-1);first=clampi(selected,0,maxi(0,members.size()-page_size()));return
	else:
		if more:
			for step in [-1,1]:
				if details_page_rect(step).has_point(point):direction(Vector2i(0,step));return
		for index in range(3):
			if button_rect(index).has_point(point):button=index;accept();return

func text(value: String,r: Rect2,color: Color=INK,center: bool=true) -> void:
	# Native 12px Chinese glyphs preserve strokes; no downscaling to 8px.
	art.text(value,r,false,color,center)

func draw_members(r: Rect2) -> void:
	# Keep the selection visible when a resized window changes page capacity.
	first=clampi(clampi(first,selected-page_size()+1,selected),0,maxi(0,members.size()-page_size()))
	text("领取："+str(ui.Items.item(target_id).name_zh),Rect2(r.position.x+16,12,r.size.x-32,16),GOLD)
	text(message if not message.is_empty() else "姓名 · 当前职业 · 当前武器",Rect2(r.position.x+16,32,r.size.x-32,12),DOWN if not message.is_empty() else MUTED)
	for slot in range(mini(page_size(),members.size()-first)):
		var index=first+slot;var row=row_rect(slot);var id=str(members[index]);var unit: Dictionary=ui.game.roster[id]
		art.panel(row,index==selected)
		var color=INK if ui.game.can_deploy(unit) else DOWN
		if two_line_members():
			text(str(unit.name_zh)+" · "+Comparison.profession_name(unit,ui.game.catalog.classes),Rect2(row.position+Vector2(8,8),Vector2(row.size.x-16,12)),color)
			text("当前："+Comparison.held_name(unit),Rect2(row.position+Vector2(8,24),Vector2(row.size.x-16,12)),color)
		else:text(member_label(id),row.grow(-8),color)
	art.material_safe=r.grow(-8)
	text("%d至%d / %d"%[first+1,mini(first+page_size(),members.size()),members.size()],Rect2(r.position.x+40,184,r.size.x-80,12),MUTED)
	for step in [-1,1]:
		if (step<0 and first>0) or (step>0 and first+page_size()<members.size()):ui._draw_indicator("left" if step<0 else "right",page_rect(step).position+Vector2(4,2))
	var back=back_rect();art.panel(back);text("X返回行囊 · Z查看",back.grow(-8))

func detail_lines(data: Dictionary,r: Rect2) -> Array:
	var lines=[]
	for value in ["当前特性："+str(data.current_description),"目标特性："+str(data.target_description),"换装规则：确认后原装备退回本队行囊。","数值说明：按当前生命计算，攻击力不含特效，命中不含目标回避。"]:
		for line in ui._wrapped_lines(value,r.size.x-32):lines.append({"text":line,"color":MUTED if value.begins_with("数值说明") else INK})
		lines.append({"text":"","color":INK})
	if not lines.is_empty():lines.pop_back()
	return lines

func details_page_count() -> int:
	var data=preview()
	return maxi(1,ceili(float(detail_lines(data,panel_rect()).size())/DETAILS_PAGE_SIZE)) if not data.is_empty() else 1

func draw_details(data: Dictionary,r: Rect2) -> void:
	var lines=detail_lines(data,r);var pages=details_page_count();details_page=clampi(details_page,0,pages-1)
	var start=details_page*DETAILS_PAGE_SIZE
	for i in range(mini(DETAILS_PAGE_SIZE,lines.size()-start)):
		text(str(lines[start+i].text),Rect2(r.position.x+16,76+i*16,r.size.x-32,12),lines[start+i].color,false)
	text("%d/%d页"%[details_page+1,pages]+(" · 上下翻页" if pages>1 else ""),Rect2(r.position.x+40,180,r.size.x-80,12),MUTED)
	for step in [-1,1]:
		if (step<0 and details_page>0) or (step>0 and details_page+1<pages):ui._draw_indicator("left" if step<0 else "right",details_page_rect(step).get_center()-Vector2(4,4))

func draw_preview(r: Rect2) -> void:
	var data=preview()
	if data.is_empty():
		text("道具已变化\n请返回重新选择",Rect2(r.position.x+16,80,r.size.x-32,48),DOWN)
		for i in range(3):
			var box=button_rect(i);art.panel(box,i==button);text(["返回角色","无法换装","装备特性"][i],box.grow(-8),MUTED)
		return
	text(str(data.name)+" · "+str(data.class_name),Rect2(r.position.x+16,10,r.size.x-32,16),GOLD)
	text("当前："+str(data.current_name),Rect2(r.position.x+16,30,r.size.x-32,12),MUTED)
	text("目标："+str(data.target_name),Rect2(r.position.x+16,44,r.size.x-32,12))
	text(str(data.reason),Rect2(r.position.x+16,58,r.size.x-32,12),UP if data.can_equip else DOWN)
	if not message.is_empty():text("\n".join(ui._wrapped_lines(message,r.size.x-32)),Rect2(r.position.x+16,76,r.size.x-32,104),DOWN)
	elif more:draw_details(data,r)
	else:
		var x=r.get_center().x-104
		var columns=[Rect2(x,74,64,12),Rect2(x+72,74,32,12),Rect2(x+116,74,36,12),Rect2(x+160,74,48,12)]
		for i in range(4):text(["属性","当前","换装" if data.compatible else "未生效","增减"][i],columns[i],MUTED,i!=0)
		for i in range(data.rows.size()):
			var row: Dictionary=data.rows[i];var y=88+i*12;var color=UP if int(row.delta)>0 else DOWN if int(row.delta)<0 else MUTED
			text(str(row.label),Rect2(x,y,64,12),INK,false)
			text(str(row.before_text),Rect2(x+72,y,32,12),MUTED)
			text("→",Rect2(x+104,y,12,12),MUTED)
			text(str(row.after_text),Rect2(x+116,y,36,12),color)
			text(str(row.delta_text),Rect2(x+160,y,48,12),color)
		# Explanations live on the paginated details page; no tiny footnotes.
	for i in range(3):
		var box=button_rect(i);var enabled=i!=1 or bool(data.can_equip)
		art.panel(box,i==button)
		text(["返回角色","确认换装" if enabled else "无法换装","属性对比" if more else "装备特性"][i],box.grow(-8),INK if enabled else MUTED)

func draw() -> void:
	art.audit.clear();art.material_safe=Rect2()
	if return_view.begins_with("hub"):ui.hub_controller.draw()
	else:ui._draw_world()
	ui.draw_set_transform(ui._canvas_offset());ui.draw_rect(ui._visible_native_rect(),Color(.025,.035,.06,.8))
	var r=panel_rect();art.panel(r)
	if ui.view=="equipment_members":draw_members(r)
	else:draw_preview(r)
	audit=art.audit.duplicate(true)
	for i in range(audit.size()):
		if not audit[i].bounds.has_area():continue
		for j in range(i):
			if audit[j].bounds.has_area() and audit[i].bounds.intersects(audit[j].bounds):ui.layout_errors.append("Equipment text overlaps: "+str(audit[i].text)+" / "+str(audit[j].text))
