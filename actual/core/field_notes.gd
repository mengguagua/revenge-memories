extends RefCounted
const Tasks=preload("res://core/current_task.gd")
const Review=preload("res://core/promotion_review.gd")
const Cast=preload("res://core/campaign_art.gd")
const PAPER=Color("463729")
const PAPER_MUTED=Color("796349")
const GREEN=Color("aed6bd")
const WARNING=Color("efbd9e")
const PAGE_ROWS=3
var ui
var art
var mode="tasks"
var return_view="world"
var selected=0
var choice=0
var entries=[]
var record={}
var lines=[]
var page=0
var message=""
var body_crops={}
var bodies=[]
var text_surfaces=[]

func _init(owner):ui=owner;art=load("res://core/journey_art.gd").new(ui)
func width():return minf(368,ui._visible_native_rect().size.x-16)
func compact():return width()<320
func centered(size:Vector2)->Rect2:return Rect2((ui._visible_native_rect().get_center()-size/2).floor(),size)
func panel():return centered(Vector2(width(),232))
func journal_rect():
	var w=minf(344,ui._visible_native_rect().size.x-8)
	return centered(Vector2(w,w*0.625))
func journal_safe():
	var r=journal_rect()
	var at=(r.position+r.size*Vector2(.12,.17)).ceil()
	return Rect2(at,(r.position+r.size*Vector2(.88,.81)).floor()-at)
func journal_rows():return maxi(1,floori((journal_safe().size.y-55)/18))
func journal_pages():return maxi(1,ceili(lines.size()/float(journal_rows())))
func list_rect():return centered(Vector2(minf(260,width()),82+mini(PAGE_ROWS,entries.size())*38))
func confirm_rect():return centered(Vector2(minf(288,width()),194))

func open_tasks():
	return_view=ui.view;mode="tasks";page=0;record=Tasks.entry(ui.game);_open()
func open_promotions():
	return_view="hub";selected=0;message="";_list();_open()
func _open():ui._clear_menu();ui.view="field_notes";ui.busy=false;ui.held_direction=Vector2i.ZERO;ui.queue_redraw()
func _list():
	mode="list";entries=[]
	for id in ui.game.party:
		var options=Review.choices(ui.game.roster[id])
		if options.is_empty():entries.append({"id":id,"target":-1})
		for o in options:entries.append({"id":id,"target":int(o.class_id)})
	selected=clampi(selected,0,maxi(0,entries.size()-1))
func _detail():
	if entries.is_empty():return
	var e=entries[selected];record=Review.preview(ui.game,e.id,e.target);mode="preview";choice=0
func direction(d:Vector2i):
	if mode=="list":selected=posmod(selected+(d.x if d.x!=0 else d.y),maxi(1,entries.size()))
	elif mode in ["preview","confirm"]:choice=1-choice
	elif mode=="tasks":page=clampi(page+(d.x if d.x!=0 else d.y),0,journal_pages()-1)
	ui.queue_redraw()
func accept():
	if mode=="tasks":cancel();return
	if mode=="list":_detail()
	elif mode=="preview":
		if choice==1 or not record.valid:_list()
		else:mode="confirm";choice=0
	elif mode=="confirm":
		if choice==0:mode="preview"
		else:
			var result=Review.commit(ui.game,record);message=str(result.reason);_list()
	ui.queue_redraw()
func cancel():
	if mode=="confirm":mode="preview"
	elif mode=="preview":_list()
	else:ui.view=return_view;ui.held_direction=Vector2i.ZERO
	ui.queue_redraw()
func row_rect(slot:int):
	var r=list_rect();return Rect2(r.position+Vector2(10,42+slot*38),Vector2(r.size.x-20,36))
func button(index:int):
	var r=confirm_rect() if mode=="confirm" else panel()
	var w=(r.size.x-32)/2
	return Rect2(r.position+Vector2(12+index*(w+8),r.size.y-40),Vector2(w,30))
func page_button(index:int):
	var r=list_rect() if mode=="list" else journal_safe()
	return Rect2(r.position.x+(8 if index==0 else r.size.x-56),r.end.y-38 if mode=="list" else r.end.y-20,48,22)
func mouse(at:Vector2):
	if mode=="list":
		for n in range(PAGE_ROWS):
			if row_rect(n).has_point(at):
				var index=int(selected/PAGE_ROWS)*PAGE_ROWS+n
				if index<entries.size():selected=index;_detail();break
		if mode=="list":
			for n in range(2):
				if page_button(n).has_point(at):selected=posmod(selected+(-PAGE_ROWS if n==0 else PAGE_ROWS),maxi(1,entries.size()))
	elif mode in ["preview","confirm"]:
		for n in range(2):
			if button(n).has_point(at):choice=n;accept();break
	else:
		for n in range(2):
			if page_button(n).has_point(at):direction(Vector2i.LEFT if n==0 else Vector2i.RIGHT);return
		# Reading the page never dismisses it; use the explicit return control.
	ui.queue_redraw()
func profession_name(cid:int)->String:return str(ui.game.catalog.classes.get(str(cid),{}).get("name_zh","无进阶路线"))
func label(value:String,r:Rect2,small:bool=false,color:Color=Color.WHITE,center:bool=true):
	art.material_safe=Rect2()
	for safe in text_surfaces:
		if safe.has_point(r.get_center()) and (not art.material_safe.has_area() or safe.get_area()<art.material_safe.get_area()):art.material_safe=safe
	art.text(value,r,small,color,center)
func wrapped(value:String,r:Rect2,small:bool=false,color:Color=Color.WHITE,center:bool=false):
	var parts=ui._small_lines(value,r.size.x) if small else ui._wrapped_lines(value,r.size.x)
	var step=12 if small else 16
	for n in range(parts.size()):label(parts[n],Rect2(r.position+Vector2(0,n*step),Vector2(r.size.x,step)),small,color,center)
	if parts.size()*step>r.size.y:ui.layout_errors.append("Field notes paragraph exceeds safe area: "+value)

func backdrop():
	if return_view=="hub":ui.hub_controller.draw()
	elif return_view=="world":ui._draw_world()
	else:art.background()
	ui.draw_rect(ui._visible_native_rect(),Color(.025,.035,.06,.82))

func draw_journal():
	var r=journal_rect();var safe=journal_safe()
	text_surfaces=[safe]
	ui.draw_texture_rect(ui._tex("res://assets/field-notes-20261030/diary.webp"),r,false)
	label("旅程日记 · 当前任务",Rect2(safe.position,Vector2(safe.size.x,16)),false,PAPER)
	label("第%d章 · %s"%[ui.game.chapter,"西队" if ui.game.route=="alm" else "东队"],Rect2(safe.position+Vector2(0,20),Vector2(safe.size.x,10)),true,PAPER_MUTED)
	lines=[]
	for sentence in str(record.text).split("。",false):
		var line="";var clauses=sentence.split("，")
		for i in range(clauses.size()):
			var phrase=clauses[i]+("，" if i<clauses.size()-1 else "。")
			if not line.is_empty() and ui._text_width(line+phrase)>safe.size.x:
				lines.append_array(ui._wrapped_lines(line,safe.size.x));line=""
			line+=phrase
		if not line.is_empty():lines.append_array(ui._wrapped_lines(line,safe.size.x))
	page=clampi(page,0,journal_pages()-1)
	for n in range(journal_rows()):
		var i=page*journal_rows()+n
		if i<lines.size():label(lines[i],Rect2(safe.position+Vector2(0,39+n*18),Vector2(safe.size.x,16)),false,PAPER,false)
	var footer=Rect2(safe.position.x,safe.end.y-12,safe.size.x,12)
	label("%d/%d · 返回合上"%[page+1,journal_pages()],footer,true,PAPER_MUTED)
	if journal_pages()>1:
		label("上页",Rect2(footer.position,Vector2(32,12)),true,PAPER_MUTED)
		label("下页",Rect2(footer.end.x-32,footer.position.y,32,12),true,PAPER_MUTED)

func draw_list():
	var r=list_rect();art.panel(r);text_surfaces=[r.grow(-8)]
	label("教堂祭台 · 职业进阶",Rect2(r.position+Vector2(12,10),Vector2(r.size.x-24,16)),false,art.GOLD)
	label(message if not message.is_empty() else "选择同伴，查看条件与变化",Rect2(r.position+Vector2(12,28),Vector2(r.size.x-24,14)),false,GREEN if not message.is_empty() else art.INK)
	for n in range(PAGE_ROWS):
		var i=int(selected/PAGE_ROWS)*PAGE_ROWS+n
		if i>=entries.size():break
		var e=entries[i];var u=ui.game.roster[e.id];var data=Review.preview(ui.game,e.id,e.target)
		var row=row_rect(n);art.panel(row,i==selected);text_surfaces.append(row.grow(-8))
		var target=profession_name(e.target) if e.target>0 else "剧情进阶" if e.id in ["hunapu","eileen"] else "最终职业"
		label(str(u.name_zh)+" → "+target,Rect2(row.position+Vector2(12,12),Vector2(row.size.x-88,12)),false,art.INK,false)
		var status="可进阶" if data.valid else "%d/%d级"%[u.level,data.required] if data.required>0 else "查看条件"
		label(status,Rect2(row.end.x-72,row.position.y+12,60,12),true,GREEN if data.valid else art.MUTED)
	label("%d/%d · 确认预览"%[selected+1,entries.size()],Rect2(r.position.x+56,r.end.y-32,r.size.x-112,16),false,art.INK)
	if entries.size()>PAGE_ROWS:
		label("上页",page_button(0),false,art.INK);label("下页",page_button(1),false,art.INK)

func draw_body(actor:Dictionary,r:Rect2,tag:String):
	var sprite=Cast.battle(actor);var frame=int(sprite.sequences.idle[0]);var key=str(sprite.path)+":"+str(frame)
	var fs=Vector2i(sprite.frame_size[0],sprite.frame_size[1]);var columns=int(sprite.get("columns",1))
	var origin=Vector2i(frame%columns,frame/columns)*fs
	if not body_crops.has(key):
		var im=ui._tex(sprite.path).get_image()
		if im.is_compressed():im.decompress()
		body_crops[key]=im.get_region(Rect2i(origin,fs)).get_used_rect()
	var crop:Rect2i=body_crops[key]
	if not crop.has_area():return
	var scale_=minf(r.size.x/crop.size.x,r.size.y/crop.size.y)
	var size=Vector2(crop.size)*scale_
	var at=Vector2(r.get_center().x-size.x/2,r.end.y-size.y)
	ui.draw_texture_rect_region(ui._tex(sprite.path),Rect2(at,size),Rect2(Vector2(origin+crop.position),Vector2(crop.size)))
	bodies.append({"tag":tag,"class_id":actor.class_id,"path":sprite.path,"frame":frame,"bounds":Rect2(at,size),"safe":r})

func draw_preview():
	var r=panel();art.panel(r);text_surfaces=[r.grow(-8)]
	label(str(record.before.name_zh)+" · 进阶预览",Rect2(r.position+Vector2(12,8),Vector2(r.size.x-24,16)),false,art.GOLD)
	var has_target=not record.rows.is_empty()
	label(profession_name(record.before.class_id)+" → "+profession_name(record.target),Rect2(r.position+Vector2(12,27),Vector2(r.size.x-24,16)),false,art.INK)
	var condition=str(record.reason)
	if record.required>0 and int(record.before.level)<int(record.required):condition="需%d级，当前%d级，差%d级"%[record.required,record.before.level,int(record.required)-int(record.before.level)]
	wrapped(condition,Rect2(r.position+Vector2(16,46),Vector2(r.size.x-32,32)),false,GREEN if record.valid else WARNING,true)
	if not has_target:
		draw_body(record.before,Rect2(r.position+Vector2(r.size.x/2-40,78),Vector2(80,74)),"before")
		wrapped("祭台提供普通职业进阶。\n这位同伴没有可预览的祭台路线。",Rect2(r.position+Vector2(16,160),Vector2(r.size.x-32,28)),true,art.MUTED,true)
	elif compact():
		var cw=(r.size.x-40)/2
		for i in range(2):
			var x=r.position.x+16+i*(cw+8)
			label("当前兵种" if i==0 else "进阶后",Rect2(x,r.position.y+67,cw,12),false,art.MUTED if i==0 else art.GOLD)
			draw_body(record.before if i==0 else record.after,Rect2(x+12,r.position.y+82,cw-24,44),"before" if i==0 else "after")
		for n in range(record.rows.size()):
			var stat=record.rows[n];var x=r.position.x+14+int(n/4)*(r.size.x-24)/2;var y=r.position.y+132+(n%4)*14
			var w=(r.size.x-28)/2
			label("生命" if n==0 else str(stat.label),Rect2(x,y,26,12),false,art.INK,false)
			label("%d→%d%s"%[stat.before,stat.after,(" +%d"%stat.delta) if stat.delta>0 else (" %d"%stat.delta) if stat.delta<0 else ""],Rect2(x+28,y,w-28,12),true,GREEN if stat.delta>0 else WARNING if stat.delta<0 else art.MUTED)
		label("等级归1 · 经验归0",Rect2(r.position.x+12,r.position.y+184,r.size.x-24,12),false,art.INK)
	else:
		for i in range(2):
			var well=Rect2(r.position+Vector2(12+i*78,72),Vector2(74,100));art.panel(well);text_surfaces.append(well.grow(-8))
			label("当前兵种" if i==0 else "进阶后",Rect2(well.position+Vector2(8,9),Vector2(58,10)),true,art.MUTED if i==0 else art.GOLD)
			draw_body(record.before if i==0 else record.after,Rect2(well.position+Vector2(10,23),Vector2(54,50)),"before" if i==0 else "after")
			label(profession_name(record.before.class_id if i==0 else record.target),Rect2(well.position+Vector2(8,78),Vector2(58,14)),false,art.INK)
		var x=r.position.x+178;var w=r.size.x-190
		label("属性",Rect2(x,r.position.y+69,48,10),true,art.MUTED,false)
		label("当前 → 进阶后",Rect2(x+48,r.position.y+69,w-48,10),true,art.MUTED)
		for n in range(record.rows.size()):
			var stat=record.rows[n];var y=r.position.y+83+n*13
			label("生命" if n==0 else str(stat.label),Rect2(x,y,30,12),false,art.INK,false)
			label("%d → %d"%[stat.before,stat.after],Rect2(x+32,y,w-62,12),false,art.INK)
			label(("+%d"%stat.delta) if stat.delta>0 else str(stat.delta) if stat.delta<0 else "—",Rect2(x+w-28,y,28,12),false,GREEN if stat.delta>0 else WARNING if stat.delta<0 else art.MUTED)
		label("等级归1 · 经验归0",Rect2(r.position.x+12,r.position.y+176,154,12),false,art.INK)
	var labels=["继续确认" if record.valid else "查看其他成员","返回"]
	if mode=="preview":
		for i in range(2):
			var b=button(i);art.panel(b,choice==i);text_surfaces.append(b.grow(-8));label(labels[i],b.grow(-8),false,art.INK)

func draw_confirmation():
	ui.draw_rect(ui._visible_native_rect(),Color(.025,.035,.06,.78))
	var r=confirm_rect();art.panel(r);text_surfaces=[r.grow(-8)]
	label("确认职业进阶？",Rect2(r.position+Vector2(14,12),Vector2(r.size.x-28,16)),false,art.GOLD)
	label(str(record.before.name_zh)+" · "+profession_name(record.target),Rect2(r.position+Vector2(14,35),Vector2(r.size.x-28,16)),false,art.INK)
	var rules="等级归1，经验归0，生命回满。\n高于职业下限的属性保留。\n不消耗道具；确认后保存进阶结果。"
	if int(record.target)==15:rules="等级归1，经验归0，生命回满。\n法术与个人训练重新起步。\n不消耗道具；确认后保存进阶结果。"
	wrapped(rules,Rect2(r.position+Vector2(18,61),Vector2(r.size.x-36,80)),false,art.INK,true)
	for i in range(2):
		var b=button(i);art.panel(b,choice==i);text_surfaces.append(b.grow(-8));label("返回预览" if i==0 else "确认进阶",b.grow(-8),false,art.INK)

func draw():
	art.audit.clear();bodies.clear();text_surfaces.clear();backdrop()
	match mode:
		"tasks":draw_journal()
		"list":draw_list()
		_:draw_preview()
	if mode=="confirm":draw_confirmation()
	ui.presentation_audit.field_notes={"mode":mode,"record":record,"selected":selected,"panel":list_rect() if mode=="list" else journal_rect() if mode=="tasks" else panel(),"bodies":bodies.duplicate(true),"text":art.audit.duplicate(true)}
