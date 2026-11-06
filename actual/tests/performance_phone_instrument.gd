extends "res://core/phone_shell.gd"
## Test-only draw timings. No instrumentation ships in the game controller.
var draw_microseconds: Array = []
func _draw() -> void:
	var started = Time.get_ticks_usec()
	super._draw()
	draw_microseconds.append(Time.get_ticks_usec() - started)
