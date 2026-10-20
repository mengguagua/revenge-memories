extends RefCounted
## Read-only selection/forecast; only the explicit confirmation moves equipment.
const Comparison=preload("res://core/equipment_comparison.gd")
const Art=preload("res://core/journey_art.gd")
const INK=Color("eee8d2")
const MUTED=Color("a8b6c6")
const GOLD=Color("d6ba80")
const UP=Color("a5ddb0")
const DOWN=Color("edaaa1")
const PAGE_SIZE=5
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
var message=""
var audit: Array=[]

func _init(owner):ui=owner;art=Art.new(ui)
func active() -> bool:return ui.view in ["equipment_members","equipment_preview"]
func open(index: int) -> void:
	var stored: Array=ui.game.convoy.get(ui.game.route,[])
	if index<0 or index>=stored.size():ui._notice("道具已变化，请重新选择");return
	return_view=ui.view;item_index=index;target_id=int(stored[index]);selected=0;first=0;button=1;more=false;message=""
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
		first=clampi(first,selected-PAGE_SIZE+1,selected)
	else:button=posmod(button+(d.x if d.x!=0 else d.y),3)
	ui.audio.play_sfx("menu_move")

func accept() -> void:
	if ui.view=="equipment_members":
		var data=preview()
		if data.is_empty():message="道具已变化，请返回重新选择";return
		ui.view="equipment_preview";more=false;button=1 if data.can_equip else 0;message="";return
	if button==0:cancel();return
	if button==2:more=not more;message="";return
	var receipt=ui.game.equip_from_convoy(str(members[selected]),item_index,target_id)
	if not receipt.valid:message=str(receipt.message);return
	ui.view=return_view;ui.held_direction=Vector2i.ZERO;ui._open_camp_menu();ui._notice(str(receipt.message),3.0)

func cancel() -> void:
	if ui.view=="equipment_preview":ui.view="equipment_members";message="";more=false
	else:
		ui.view=return_view;ui.held_direction=Vector2i.ZERO;ui._camp_action("withdraw")
	ui.audio.play_sfx("menu_cancel")

func toggle_details() -> void:
	if ui.view=="equipment_preview":more=not more;message=""

func panel_rect() -> Rect2:
	var bounds=ui._visible_native_rect();var width=minf(360,bounds.size.x-16)
	return Rect2(bounds.get_center().x-width/2,4,width,232)
func row_rect(slot: int) -> Rect2:
	var r=panel_rect();return Rect2(r.position.x+8,48+slot*28,r.size.x-16,28)
func back_rect() -> Rect2:
	var r=panel_rect();return Rect2(r.position.x+40,204,r.size.x-80,24)
func button_rect(index: int) -> Rect2:
	var r=panel_rect();var width=(r.size.x-32)/3
	return Rect2(r.position.x+8+index*(width+8),200,width,28)
func page_rect(step: int) -> Rect2:
	var r=panel_rect();return Rect2(r.position.x+16 if step<0 else r.end.x-32,190,16,14)

func mouse(point: Vector2) -> void:
	if ui.view=="equipment_members":
		for slot in range(mini(PAGE_SIZE,members.size()-first)):
			if row_rect(slot).has_point(point):selected=first+slot;accept();return
		if back_rect().has_point(point):cancel();return
		for step in [-1,1]:
			if page_rect(step).has_point(point):
				selected=clampi(selected+step*PAGE_SIZE,0,members.size()-1);first=clampi(selected,0,maxi(0,members.size()-PAGE_SIZE));return
	else:
		for index in range(3):
			if button_rect(index).has_point(point):button=index;accept();return

func text(value: String,r: Rect2,color: Color=INK,small: bool=true,center: bool=true) -> void:
	art.text(value,r,small,color,center)

func draw_members(r: Rect2) -> void:
	text("领取："+str(ui.Items.item(target_id).name_zh),Rect2(r.position.x+16,14,r.size.x-32,16),GOLD,false)
	text(message if not message.is_empty() else "姓名 · 当前职业 · 当前装备武器",Rect2(r.position.x+16,34,r.size.x-32,8),DOWN if not message.is_empty() else MUTED)
	for slot in range(mini(PAGE_SIZE,members.size()-first)):
		var index=first+slot;var row=row_rect(slot);var id=str(members[index]);var unit: Dictionary=ui.game.roster[id]
		art.panel(row,index==selected)
		text(member_label(id),row.grow(-8),INK if ui.game.can_deploy(unit) else DOWN)
	art.material_safe=r.grow(-8)
	text("%d至%d / %d"%[first+1,mini(first+PAGE_SIZE,members.size()),members.size()],Rect2(r.position.x+40,192,r.size.x-80,8),MUTED)
	for step in [-1,1]:
		if (step<0 and first>0) or (step>0 and first+PAGE_SIZE<members.size()):ui._draw_indicator("left" if step<0 else "right",page_rect(step).position+Vector2(4,2))
	var back=back_rect();art.panel(back);text("X返回行囊 · Z查看",back.grow(-8))

func draw_details(data: Dictionary,r: Rect2) -> void:
	var lines: Array[String]=[]
	for value in ["当前特性："+str(data.current_description),"目标特性："+str(data.target_description),"换装规则：确认后原装备退回本队行囊。","数值说明：按当前生命计算，攻击力不含特效，命中不含目标回避。"]:
		lines.append_array(ui._small_lines(value,r.size.x-32));lines.append("")
	if not lines.is_empty():lines.pop_back()
	var height=mini(11,floori(120.0/maxi(1,lines.size())))
	if height<8:ui.layout_errors.append("Equipment details need another page")
	for i in range(lines.size()):text(lines[i],Rect2(r.position.x+16,74+i*height,r.size.x-32,8),MUTED if lines[i].begins_with("数值说明") else INK,true,false)

func draw_preview(r: Rect2) -> void:
	var data=preview()
	if data.is_empty():
		text("道具已变化，请返回重新选择",Rect2(r.position.x+16,80,r.size.x-32,48),DOWN)
		for i in range(3):
			var box=button_rect(i);art.panel(box,i==button);text(["返回角色","无法换装","装备特性"][i],box.grow(-8),MUTED)
		return
	text(str(data.name)+" · "+str(data.class_name),Rect2(r.position.x+16,12,r.size.x-32,16),GOLD,false)
	text("当前："+str(data.current_name),Rect2(r.position.x+16,34,r.size.x-32,8),MUTED)
	text("目标："+str(data.target_name),Rect2(r.position.x+16,45,r.size.x-32,8))
	text(str(data.reason),Rect2(r.position.x+16,57,r.size.x-32,10),UP if data.can_equip else DOWN)
	if more:draw_details(data,r)
	else:
		var x=r.get_center().x-104
		var columns=[Rect2(x,72,64,8),Rect2(x+72,72,32,8),Rect2(x+116,72,32,8),Rect2(x+160,72,48,8)]
		for i in range(4):text(["属性","当前","换装" if data.compatible else "未生效","增减"][i],columns[i],MUTED,true,i!=0)
		for i in range(data.rows.size()):
			var row: Dictionary=data.rows[i];var y=84+i*10;var color=UP if int(row.delta)>0 else DOWN if int(row.delta)<0 else MUTED
			text(str(row.label),Rect2(x,y,64,8),INK,true,false)
			text(str(row.before_text),Rect2(x+72,y,32,8),MUTED)
			text(">",Rect2(x+106,y,8,8),MUTED)
			text(str(row.after_text),Rect2(x+116,y,32,8),color)
			text(str(row.delta_text),Rect2(x+160,y,48,8),color)
		text("原装备将退回本队行囊" if int(data.held_id)>0 else "空手领取后自动生效",Rect2(r.position.x+16,178,r.size.x-32,8),MUTED)
		text(message if not message.is_empty() else "Tab查看特性 · 命中不含目标回避",Rect2(r.position.x+16,189,r.size.x-32,8),DOWN if not message.is_empty() else MUTED)
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
