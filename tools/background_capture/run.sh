#!/bin/bash
# Every graphics process is guarded BEFORE launch: no windows and no focus.
set -euo pipefail
cd "$(dirname "$0")/../.."
capture_tmp=$(mktemp -d /tmp/fe2-offscreen.XXXXXX)
trap 'rm -rf "$capture_tmp"' EXIT
xcrun clang -dynamiclib -framework Cocoa tools/background_capture/guard.m -o "$capture_tmp/guard.dylib"
cat > "$capture_tmp/probe.gd" <<'PROBE'
extends SceneTree
func _initialize():
	print("BACKGROUND_GUARD=", OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE"))
	quit(0 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") == "1" else 1)
PROBE
export DYLD_INSERT_LIBRARIES="$capture_tmp/guard.dylib"
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --log-file "$capture_tmp/probe.log" --script "$capture_tmp/probe.gd"
/Applications/Godot.app/Contents/MacOS/Godot --path . --audio-driver Dummy --rendering-method gl_compatibility --log-file /private/tmp/fe2-offscreen-render.log --script "${1:-res://tools/capture_flow.gd}" "${@:2}"
