extends RefCounted
## Logical canvas coordinates; the selected sprite and arrow are hard exclusions.
static func forecast(anchor: Vector2,canvas: Rect2,neighbours: Array=[],combatants: Array=[]) -> Dictionary:
	# Preserve native type in both horizontal and side-mounted forecasts.
	# The narrow side card keeps both combatants visible on phone landscapes.
	for size in [Vector2(240,112),Vector2(240,86),Vector2(128,180)]:
		var result=place(anchor,size,canvas,neighbours,combatants)
		if result.valid:
			result.compact=size.y!=112;result.stacked=size.x==128
			result.combatants_protected=true
			return result
	if not combatants.is_empty():
		# At the minimum desktop canvas, separated ranged combatants can use
		# every remaining card location. Keep the forecast and target visible.
		var result=forecast(anchor,canvas,neighbours)
		result.combatants_protected=false;result.fallback_reason="minimum_canvas_combatants_do_not_fit"
		return result
	return {"valid":false,"panel":Rect2(),"focus":Rect2(),"compact":true,"stacked":false,"combatants_protected":false}

static func place(anchor: Vector2, size: Vector2, canvas: Rect2, neighbours: Array=[], exclusions: Array=[]) -> Dictionary:
	var safe=canvas.grow(-8)
	var focus=Rect2(anchor+Vector2(-10,-26),Vector2(36,48))
	var candidates=[]
	for x in [focus.end.x+10,focus.position.x-size.x-10]:
		for y in [anchor.y-size.y/2,focus.position.y,focus.end.y-size.y]:candidates.append(Vector2(x,y))
	for y in [focus.position.y-size.y-8,focus.end.y+8]:
		for x in [anchor.x-size.x/2,focus.position.x,focus.end.x-size.x]:candidates.append(Vector2(x,y))
	# On the minimum 256x240 canvas the 2-row HP card sometimes needs
	# the smaller gap. The focus rectangle already includes arrow/sprite margins.
	for y in [focus.position.y-size.y-2,focus.end.y+2]:
		candidates.append(Vector2(anchor.x-size.x/2,y))
	for other in exclusions:
		for x in [other.position.x-size.x-2,other.end.x+2]:candidates.append(Vector2(x,anchor.y-size.y/2))
		for y in [other.position.y-size.y-2,other.end.y+2]:candidates.append(Vector2(anchor.x-size.x/2,y))
	var best=Rect2();var best_score=INF;var clear=Rect2();var clear_score=INF
	for point in candidates:
		point.x=clampf(point.x,safe.position.x,safe.end.x-size.x)
		point.y=clampf(point.y,safe.position.y,safe.end.y-size.y)
		var panel=Rect2(point,size)
		if not safe.encloses(panel) or panel.intersects(focus):continue
		if exclusions.any(func(other):return panel.intersects(other)):continue
		var distance=panel.get_center().distance_to(focus.get_center());var score=distance;var overlaps=false
		for other in neighbours:
			var overlap=panel.intersection(other)
			score+=overlap.get_area()*0.15
			if overlap.has_area():overlaps=true
		if not overlaps and distance<clear_score:clear_score=distance;clear=panel
		if score<best_score:best_score=score;best=panel
	if clear.has_area():best=clear
	return {"panel":best,"focus":focus,"valid":best.has_area() and not best.intersects(focus)}
