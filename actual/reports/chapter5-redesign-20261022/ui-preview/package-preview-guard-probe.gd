extends SceneTree
var errors=[]
var checks=0
func check(ok:bool,label:String):
 checks+=1
 if not ok:errors.append(label)
func _initialize():
 check(ProjectSettings.globalize_path("res://")!="/Users/gcc/gaocc/project/revenge-memories/actual/","isolated package resource root")
 var ui=load("res://scenes/main.tscn").instantiate()
 ui.game.units=[{"id":"actor"},{"id":"target"}]
 var cases=[{"name":"empty-selected","selected":"","ids":["target"],"index":0},{"name":"removed-actor","selected":"__removed__","ids":["target"],"index":0},{"name":"removed-target","selected":"actor","ids":["__removed__"],"index":0},{"name":"past-end","selected":"actor","ids":["target"],"index":1},{"name":"negative-index","selected":"actor","ids":["target"],"index":-1},{"name":"empty-target-list","selected":"actor","ids":[],"index":0}]
 for c in cases:
  ui.game.selected_id=c.selected;ui.target_ids=c.ids;ui.target_index=c.index;ui.battle_preview_audit={"stale":true}
  ui._draw_preview()
  check(ui.battle_preview_audit.is_empty(),"packed current guard returns before actor geometry access: "+c.name)
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"cases":cases,"resource_root":ProjectSettings.globalize_path("res://"),"scene":"res://scenes/main.tscn","core":"res://core/main.gd","scope":"Runtime invalid-preview calls on scene loaded only from exported PCK, using intentionally geometry-free actors so old core cannot pass. Genuine valid menu preview tested separately in source."}
 var f=FileAccess.open(OS.get_environment("CH5_PACKAGE_GUARD_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("PACKED_PREVIEW_GUARD ",JSON.stringify({"passed":report.passed,"checks":checks,"errors":errors}));ui.free();quit(0 if errors.is_empty()else 1)
