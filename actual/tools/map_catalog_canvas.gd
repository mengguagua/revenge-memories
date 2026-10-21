extends "res://core/main.gd"
## Read-only scene-art renderer. Uses the game's current terrain/architecture drawing methods.
const PAD=32
func _ready() -> void:
 world=game.formal_world;battle_pack=GameState.read_json("res://assets/battle_tiles/battle-tiles.json")
 nature_layouts=GameState.read_json("res://data/nature-layouts.json")
 for sprite in GameState.read_json("res://assets/nature/nature.json").get("sprites",[]):nature_sprites[str(sprite.key)]=sprite
 set_process(false);set_process_input(false);game.mode="battle";view="catalog"
func _canvas_offset() -> Vector2:return Vector2.ZERO
func prepare(id:int) -> void:
 game.stage_id=id;game.battle_data=game.stages[id].duplicate(true);game.chapter=int(game.battle_data.chapter);game.route="celica" if game.battle_data.route=="celica" else "alm"
 game.units=game.battle_data.enemies.duplicate(true)+game.battle_data.npc_units.duplicate(true)
 game.turn=1;game.phase="player";game.flags={"quest":{"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}}
 game.ChapterTwo.initialize(game)
 if game.chapter==3:game.ChapterThree.initialize(game)
 if game.chapter==4:game.ChapterFour.initialize(game)
 if game.chapter==5:game.ChapterFive.initialize(game)
 queue_redraw()
func info() -> Dictionary:
 var d=game.battle_data;var cells=[]
 for y in range(int(d.map.height)):
  for x in range(int(d.map.width)):
   var at=Vector2i(x,y)
   cells.append({"name":_terrain_name(at),"category":game.category(at),"avoid":game.terrain_avoid(at),"foot":game.movement_cost({"class_id":6},at),"horse":game.movement_cost({"class_id":1},at),"fly":game.movement_cost({"class_id":3},at)})
 var classes={}
 for u in d.enemies+d.npc_units+d.reinforcements:
  classes[str(int(u.class_id))]=str(game.catalog.classes[str(int(u.class_id))].get("name_zh","未知职业"))
 return {"code":d.code,"stage_id":game.stage_id,"width":int(d.map.width)*16+PAD*2,"height":int(d.map.height)*16+PAD*2,"padding":PAD,"cells":cells,"objective_status":game.objective_status(),"exit_marker":game.exit_marker(),"classes":classes}
func _draw() -> void:
 if game.battle_data.is_empty() or not is_node_ready():return
 var d=game.battle_data;var origin=Vector2(PAD,PAD);var values=d.get("map_tint",[1.0,1.0,1.0,1.0]);var tint=Color(values[0],values[1],values[2],values[3])
 draw_set_transform(Vector2.ZERO)
 _draw_battle_surroundings(origin,tint)
 _draw_layers(d.art_layers,int(d.get("art_columns",32)),_tex(str(d.art_atlas)),origin,tint)
 _draw_nature_props(d.get("natural_props",[]),origin,tint)
 _draw_art_props(d.get("art_props",[]),origin,tint)
 for obj in d.objects:
  if obj.get("kind","")=="visit":continue
  var at=origin+Vector2(obj.position[0],obj.position[1])*16
  if obj.kind=="control":_draw_camp_control_flag(at,game.stage_id==405);continue
  var name=str(obj.sprite);var path=str(obj.get("sprite_path","res://assets/battle_tiles/modules/"+name+".png"));var shelter=obj.kind=="shelter" and name=="clinic_door"
  if shelter:path="res://assets/battlefield-0.3.0/modules/tactical_house.png"
  var texture=_tex(path);var offset=Vector2(0,texture.get_height()-16)
  if obj.has("sprite_offset"):offset=-Vector2(obj.sprite_offset[0],obj.sprite_offset[1])
  draw_texture(texture,at-offset)
 # Solid event objects are scenery; characters are described by optional browser markers.
 for u in d.npc_units:
  var at=origin+Vector2(u.position[0],u.position[1])*16
  if u.has("sprite_path"):
   var texture=_tex(str(u.sprite_path));var offset=Vector2((texture.get_width()-16)/2,texture.get_height()-16)
   if u.has("sprite_offset"):offset=-Vector2(u.sprite_offset[0],u.sprite_offset[1])
   draw_texture(texture,at-offset)
  elif u.id=="medicine_wagon":draw_texture(_tex("res://assets/battle_tiles/modules/medicine_wagon.png"),at-Vector2(8,0))
 for boat in game.event_boats():
  if boat.get("waiting",false):continue
  var texture=_tex(str(d.get("event_boat_sprite","res://assets/world_tiles/modules/galleon.png")));var at=origin+Vector2(boat.position[0],boat.position[1])*16
  draw_texture(texture,at-Vector2((texture.get_width()-16)/2,texture.get_height()-16))
