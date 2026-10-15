extends SceneTree
var ui
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(ok: bool,label: String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func run():
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
 var font=Image.load_from_file(ProjectSettings.globalize_path(ui.chinese_font.path))
 for symbol in ["+","-"]:
  var glyph=ui._zh_glyph(symbol);check(not glyph.is_empty(),"operator resolves without question-mark fallback: "+symbol)
  if glyph.is_empty():continue
  check(int(glyph.advance)==8 and int(glyph.rect[2])==8,"original ASCII spacing retained: "+symbol)
  var r=glyph.rect;var rows=[];var columns=[];var ink=0
  for y in range(12):
   var count=0
   for x in range(8):
    if font.get_pixel(int(r[0])+x,int(r[1])+y).a>0:count+=1;ink+=1
   rows.append(count)
  for x in range(8):
   var count=0
   for y in range(12):
    if font.get_pixel(int(r[0])+x,int(r[1])+y).a>0:count+=1
   columns.append(count)
  check(rows.max()==7,"complete horizontal operator stroke: "+symbol)
  check(columns.max()==(7 if symbol=="+" else 1),"correct vertical operator stroke: "+symbol)
  check(ink==(13 if symbol=="+" else 7),"actual bitmap has complete expected operator ink: "+symbol)
 check(ui._text_width("回避+20")==ui._text_width("回避20")+8,"avoidance label keeps original total spacing")
 check(ui._text_width("-1")==16,"negative numbers keep two ASCII advances")
 check(ui._zh_glyph("A").is_empty() and ui.graphics.font.char_codes.has("A"),"existing original Latin glyph routing unchanged")
 var d={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"scope":"Targeted operator bitmap ink and runtime font routing; no combat replay"}
 var f=FileAccess.open("res://reports/glyph-fix-0.2.2/font-check.json",FileAccess.WRITE);f.store_string(JSON.stringify(d,"  "));f.close();print("FONT_SYMBOLS ",JSON.stringify(d))
 ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
