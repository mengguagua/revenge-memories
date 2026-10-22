extends RefCounted
## Prefer the lower empty area; every character and interaction marker is protected.
static func place(size:Vector2,canvas:Rect2,protected:Array,previous:Rect2=Rect2()) -> Rect2:
	var safe=canvas.grow(-8)
	if size.x>safe.size.x or size.y>safe.size.y:return Rect2()
	var candidates=[]
	if previous.has_area():candidates.append(Vector2(previous.position.x,previous.end.y-size.y))
	candidates.append_array([Vector2(safe.position.x,safe.end.y-size.y),safe.end-size,safe.position,Vector2(safe.end.x-size.x,safe.position.y)])
	for y in range(floori(safe.end.y-size.y),ceili(safe.position.y)-1,-4):
		for x in range(ceili(safe.position.x),floori(safe.end.x-size.x)+1,4):candidates.append(Vector2(x,y))
	for point in candidates:
		var rect=Rect2(point,size)
		if safe.encloses(rect) and not protected.any(func(actor):return rect.intersects(actor)):return rect
	return Rect2()
