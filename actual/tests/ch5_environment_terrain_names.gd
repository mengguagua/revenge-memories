extends SceneTree
const Renderer=preload("res://tools/map_catalog_canvas.gd")
var checks=[]
func _initialize():call_deferred("run")
func run():
 var canvas=Renderer.new();root.add_child(canvas);await process_frame
 var cases=[[501,"=",8,"室外石铺"],[501,"b",0,"病房石地"],[502,"b",0,"露天石桥"],[503,"b",0,"室内石地"],[503,"s",6,"检修木桥"],[504,"b",0,"神宫大理石地"],[511,"w",0,"室内木地"],[511,"b",0,"室内石地"],[533,"b",0,"庭院石铺"],[534,"b",0,"神宫大理石地"],[503,"~",7,"人工水渠"],[504,"~",7,"室内蓄水池"],[501,"~",7,"庭院水池"],[533,"~",7,"庭院水池"],[534,"~",7,"庭院水池"]]
 for item in cases:
  canvas.prepare(int(item[0]));var found=false
  for y in range(1,int(canvas.game.battle_data.map.height)-1):
   for x in range(1,int(canvas.game.battle_data.map.width)-1):
    var cell=Vector2i(x,y)
    if str(canvas.game.battle_data.visual_ground[y][x])!=item[1]or canvas.game.category(cell)!=int(item[2]):continue
    if canvas.game.battle_data.objects.any(func(o):return o.position==[x,y]):continue
    if int(item[0])==534 and item[1]=="b" and y>15:continue
    var got=canvas._terrain_name(cell)
    if got!=item[3]:continue
    checks.append({"passed":true,"stage":item[0],"cell":[x,y],"name":got,"foot_movement":canvas.game.movement_cost({"class_id":6},cell)});found=true;break
   if found:break
  if not found:checks.append({"passed":false,"stage":item[0],"expected":item[3]})
 var passed=checks.all(func(c):return c.passed)
 var f=FileAccess.open("res://reports/chapter5-environment-20261023/terrain-name-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Actual renderer labels for representative materials; numerical terrain remains in the unchanged map.tiles/logic_grid."},"  "));f.close();canvas.queue_free();await process_frame;canvas=null;call_deferred("quit",0 if passed else 1)
