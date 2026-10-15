extends RefCounted
## Current renderer uses scene-authored world-space props. The old rectangle
## helper below remains only for the archived 0.1.2 geometry checks.
static func visible_props(props: Array,sprites: Dictionary,origin: Vector2,visible: Rect2) -> Array:
	var out: Array=[]
	for p in props:
		var sprite: Dictionary=sprites.get(str(p.key),{})
		if sprite.is_empty():continue
		var at=Vector2(p.position[0],p.position[1])+origin
		var size=p.get("size",sprite.size)
		var rect=Rect2(at,Vector2(size[0],size[1]))
		if visible.encloses(rect):out.append(p)
	return out
## Border decorations are complete objects, never modulo-selected fragments.
## Coordinates and visibility are in the same native-pixel space as the map.
static func module_rects(origin: Vector2,map_cells: Vector2i,module_cells: Vector2i,visible: Rect2) -> Array[Rect2]:
	var result: Array[Rect2]=[]
	var size=Vector2(module_cells)*16.0
	var map_size=Vector2(map_cells)*16.0
	if size.x<=0 or size.y<=0:return result
	var top=clampf(origin.y,visible.position.y,visible.end.y)
	var bottom=clampf(origin.y+map_size.y,visible.position.y,visible.end.y)
	var left=clampf(origin.x,visible.position.x,visible.end.x)
	var right=clampf(origin.x+map_size.x,visible.position.x,visible.end.x)
	var regions=[Rect2(visible.position,Vector2(visible.size.x,top-visible.position.y)),
		Rect2(Vector2(visible.position.x,bottom),Vector2(visible.size.x,visible.end.y-bottom)),
		Rect2(Vector2(visible.position.x,top),Vector2(left-visible.position.x,bottom-top)),
		Rect2(Vector2(right,top),Vector2(visible.end.x-right,bottom-top))]
	for side in range(regions.size()):
		var area: Rect2=regions[side]
		var xs=_positions(area.position.x,area.end.x,size.x)
		var ys=_positions(area.position.y,area.end.y,size.y)
		# Draw the module adjacent to the playable boundary last. End caps
		# overlap by transparent silhouettes, never by chopping a source image.
		if side==3:xs.reverse()
		if side==1:ys.reverse()
		for y in ys:
			for x in xs:result.append(Rect2(Vector2(x,y),size))
	return result

static func _positions(start: float,end: float,length: float) -> Array[float]:
	var out: Array[float]=[]
	if end-start<length:return out
	var at=start
	while at+length<=end:
		out.append(at);at+=length
	if not is_equal_approx(out[-1]+length,end):out.append(end-length)
	return out
