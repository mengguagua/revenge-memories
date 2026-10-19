extends RefCounted
## Frozen design renderer. All geometry is in the game's native logical pixels.
const ASSET := "res://assets/journey-home/"
const INK := Color("eee8d2")
const MUTED := Color("a8b6c6")
const GOLD := Color("d6ba80")
var ui
var audit: Array=[]
var center_tile: AtlasTexture

func _init(owner):
 ui=owner
 center_tile=AtlasTexture.new();center_tile.atlas=ui._tex(ASSET+"journal-panel.png");center_tile.region=Rect2(40,40,16,16)

func bounds() -> Rect2:return ui._visible_native_rect()
func compact() -> bool:return bounds().size.x<360
func title_button(index: int) -> Rect2:
 var b=bounds()
 return Rect2(b.position.x+(b.size.x-180)/2.0 if compact() else b.position.x+30,128+index*37,180,30)
func row_rect(index: int) -> Rect2:
 var b=bounds();var inset=12 if compact() else 24
 return Rect2(b.position.x+inset,52+index*33,b.size.x-inset*2,31)
func confirm_rect() -> Rect2:
 var w=minf(bounds().size.x-24,320)
 return Rect2(bounds().get_center().x-w/2,46,w,148)
func confirm_button(index: int) -> Rect2:
 var d=confirm_rect();var w=(d.size.x-42)/2
 return Rect2(d.position.x+16+index*(w+10),d.end.y-44,w,28)

func panel(r: Rect2, selected: bool=false) -> void:
 if selected:
  var glow=StyleBoxFlat.new();glow.bg_color=Color(0,0,0,0);glow.shadow_color=Color(0.74,0.58,0.32,0.22+sin(ui.elapsed*2.2)*0.05);glow.shadow_size=5
  ui.draw_style_box(glow,r.grow(-3))
 var t=ui._tex(ASSET+"journal-panel.png")
 var color=Color(1.12,1.07,.95) if selected else Color(.68,.76,.85)
 ui.draw_texture_rect(center_tile,Rect2(r.position+Vector2(8,8),r.size-Vector2(16,16)),true,color)
 var dx=[r.position.x,r.position.x+8,r.end.x-8];var dy=[r.position.y,r.position.y+8,r.end.y-8]
 var dw=[8.0,r.size.x-16,8.0];var dh=[8.0,r.size.y-16,8.0]
 for y in range(3):
  for x in range(3):
   if x==1 and y==1:continue
   var sx=40 if x==1 else x*44;var sy=40 if y==1 else y*44
   ui.draw_texture_rect_region(t,Rect2(dx[x],dy[y],dw[x],dh[y]),Rect2(sx,sy,1 if x==1 else 8,1 if y==1 else 8),color)

func text(value: String, r: Rect2, small: bool=false, color: Color=INK, align_center: bool=true) -> void:
 var size=Vector2(ui._small_text_width(value),8) if small else Vector2(ui._text_width(value),ui._text_height(value))
 var at=Vector2(r.position.x+(r.size.x-size.x)/2.0 if align_center else r.position.x,r.position.y+(r.size.y-size.y)/2.0).round()
 var ink=Rect2(at,size)
 audit.append({"text":value,"bounds":ink,"safe":r,"font":8 if small else 12})
 if not r.encloses(ink):ui.layout_errors.append("Journal text outside safe area: "+value)
 var previous=ui.safe_panels.duplicate();ui.safe_panels.clear();ui.safe_panels.append(r)
 if small:ui._small_text(value,at,color)
 else:ui._text(value,at,color)
 ui.safe_panels.assign(previous)

func shortened(value: String, width: float) -> String:
 var result=value
 while ui._small_text_width(result)>width and not result.is_empty():result=result.left(result.length()-1)
 if result!=value and result.length()>1:result=result.left(result.length()-1)+"…"
 return result

func background(dim: bool=false) -> void:
 var b=bounds();var texture=ui._tex(ASSET+"snow-coast.png")
 var scale=maxf(b.size.x/426.0,b.size.y/240.0)
 var sz=Vector2(426,240)*scale;var at=b.get_center()-sz/2
 ui.draw_texture_rect(texture,Rect2(at,sz),false)
 if compact():ui.draw_rect(b,Color(.025,.045,.085,.28))
 # Distant lamp light breathes; flakes fall before any content is drawn.
 var light=at+Vector2(398,91)*scale
 for i in range(7,0,-1):ui.draw_circle(light,float(i)*scale,Color(1,.72,.32,(.004+sin(ui.elapsed*1.4)*.001)*float(8-i)))
 for i in range(27):
  var x=fposmod(i*67.0+ui.elapsed*(2+i%3),b.size.x)
  var y=fposmod(i*43.0+ui.elapsed*(5+i%4),b.size.y)
  ui.draw_rect(Rect2(b.position+Vector2(floorf(x),floorf(y)),Vector2.ONE),Color(.77,.83,.9,.15+float(i%3)*.06))
 if dim:ui.draw_rect(b,Color(.025,.035,.07,.68))

func home(screen) -> void:
 var b=bounds();var x=b.position.x+(b.size.x-208)/2 if compact() else b.position.x+16
 text("序章 · 第一章至第三章",Rect2(x+8,23,192,12),true,MUTED)
 # 2x native pixel title, with bounds audited after scaling.
 var value="复仇与回忆";var at=Vector2(x+44,48)
 ui.draw_set_transform(ui._canvas_offset()+at,0,Vector2(2,2));ui._text(value,Vector2.ZERO,INK,false)
 ui.draw_set_transform(ui._canvas_offset())
 var title_ink=Rect2(at,Vector2(ui._text_width(value)*2,24));var title_safe=Rect2(x+12,43,184,34)
 audit.append({"text":value,"bounds":title_ink,"safe":title_safe,"font":24})
 if not title_safe.encloses(title_ink):ui.layout_errors.append("Title outside safe area")
 text("雪下的名字",Rect2(x+12,82,184,18),false,GOLD)
 text("雪路未尽，灯火犹存",Rect2(x+12,106,184,10),true,MUTED)
 var has_save=screen.records.any(func(r):return r.valid)
 for i in range(2):
  var r=title_button(i);panel(r,ui.title_selected==i)
  text("开始游戏" if i==0 else "继续游戏",r.grow(-7),false,INK if i==0 or has_save else MUTED)
 text("方向选择   Z确认   X返回",Rect2(b.position.x+8,218,b.size.x-16,14),true,MUTED)
 if not has_save:text("暂无记录",Rect2(title_button(1).position.x,199,180,12),true,MUTED)

func records_screen(screen) -> void:
 var b=bounds();var inset=4 if compact() else 12
 panel(Rect2(b.position.x+inset,8,b.size.x-inset*2,216))
 var heading={"new":"开始游戏","load":"继续游戏","save":"保存旅程"}[screen.intent]
 text(heading,Rect2(b.position.x+24,17,b.size.x-48,16),false,GOLD)
 var hint={"new":"选择一个记录槽，写下新的旅程","load":"选择记录，回到上次停下的地方","save":"选择记录槽，保存当前旅程"}[screen.intent]
 text(hint,Rect2(b.position.x+16,35,b.size.x-32,10),true,MUTED)
 for i in range(5):
  var r=row_rect(i);var entry=screen.records[i];var active=i==screen.selected
  panel(r,active)
  text("%02d"%(i+1),Rect2(r.position+Vector2(7,7),Vector2(22,17)),true,GOLD if active else MUTED)
  var tx=r.position.x+36;var tw=r.size.x-45
  var name="空槽位";var detail="可在此记录新的旅程"
  if entry.exists:
   name=entry.chapter+" · "+entry.location if entry.valid else "记录无法读取 · 原件保留"
   detail=entry.time
   if entry.valid and not compact():detail+="   "+entry.route+"   "+ui.game.Journals.duration(entry.seconds)
   if entry.legacy and entry.valid:name+=" · 旧记录"
  text(shortened(name,tw),Rect2(tx,r.position.y+5,tw,9),true,INK if entry.valid or not entry.exists else Color("d3a39c"),false)
  text(shortened(detail,tw),Rect2(tx,r.position.y+18,tw,8),true,MUTED,false)
 var footer=screen.message if not screen.message.is_empty() else "方向选择   Z确认   X返回"
 text(footer,Rect2(b.position.x+8,228,b.size.x-16,12),true,GOLD if not screen.message.is_empty() else MUTED)

func confirmation(screen) -> void:
 ui.draw_rect(bounds(),Color(.025,.035,.06,.78))
 var r=confirm_rect();panel(r,true)
 text("覆盖记录 %02d？"%(screen.selected+1),Rect2(r.position.x+16,r.position.y+14,r.size.x-32,18),false,GOLD)
 var entry=screen.records[screen.selected]
 text(entry.time,Rect2(r.position.x+16,r.position.y+42,r.size.x-32,12),true,MUTED)
 text("原记录将由本次旅程替换。",Rect2(r.position.x+16,r.position.y+65,r.size.x-32,12),true,INK)
 for i in range(2):
  var button=confirm_button(i);panel(button,screen.confirm_choice==i)
  text("返回" if i==0 else "确认覆盖",button.grow(-7))

func saved(screen) -> void:
 var b=bounds();var r=Rect2(b.get_center().x-116,b.end.y-60,232,44)
 panel(r,true)
 text("记录 %02d 已保存"%ui.game.active_slot,Rect2(r.position+Vector2(10,7),Vector2(212,14)),false,GOLD)
 text(screen.saved_time,Rect2(r.position+Vector2(10,26),Vector2(212,9)),true,MUTED)

func draw(screen) -> void:
 audit.clear();background(ui.view!="title")
 if ui.view=="title":home(screen)
 else:
  records_screen(screen)
  if ui.view=="journal_confirm":confirmation(screen)
