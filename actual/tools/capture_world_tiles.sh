#!/bin/bash
set -euo pipefail
tile_root=$(cd "$(dirname "$0")/.." && pwd)
tile_capture_tmp=$(mktemp -d /private/tmp/revenge-world-tiles.XXXXXX)
trap 'rm -rf "$tile_capture_tmp"' EXIT
xcrun clang -dynamiclib -framework Cocoa "$tile_root/tools/background_guard.m" -o "$tile_capture_tmp/guard.dylib"
export DYLD_INSERT_LIBRARIES="$tile_capture_tmp/guard.dylib"
cat > "$tile_capture_tmp/probe.gd" <<'PROBE'
extends SceneTree
func _initialize():
	quit(0 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") == "1" else 1)
PROBE
/Applications/Godot.app/Contents/MacOS/Godot --headless --path "$tile_root" --log-file "$tile_capture_tmp/probe.log" --script "$tile_capture_tmp/probe.gd"
/Applications/Godot.app/Contents/MacOS/Godot --path "$tile_root" --audio-driver Dummy --rendering-method gl_compatibility --log-file "$tile_root/reports/world-tiles-b/render.log" --script res://tools/capture_world_tiles.gd
