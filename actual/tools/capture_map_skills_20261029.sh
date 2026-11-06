#!/bin/bash
set -euo pipefail
actual_root=$(cd "$(dirname "$0")/.." && pwd)
capture_tmp=$(mktemp -d /private/tmp/revenge-map-capture.XXXXXX)
trap 'rm -rf "$capture_tmp"' EXIT
xcrun clang -dynamiclib -framework Cocoa "$actual_root/tools/background_guard.m" -o "$capture_tmp/guard.dylib"
export DYLD_INSERT_LIBRARIES="$capture_tmp/guard.dylib"
cat > "$capture_tmp/probe.gd" <<'PROBE'
extends SceneTree
func _initialize():
	quit(0 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") == "1" else 1)
PROBE
/Applications/Godot.app/Contents/MacOS/Godot --headless --path "$actual_root" --log-file "$capture_tmp/probe.log" --script "$capture_tmp/probe.gd"
/Applications/Godot.app/Contents/MacOS/Godot --path "$actual_root" --audio-driver Dummy --rendering-method gl_compatibility --log-file "$actual_root/reports/map-skills-20261029/render.log" --script res://tools/capture_map_skills_20261029.gd
if rg -q 'SCRIPT ERROR|^ERROR:' "$actual_root/reports/map-skills-20261029/render.log"; then
  exit 1
fi
