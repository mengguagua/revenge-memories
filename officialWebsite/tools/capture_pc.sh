#!/bin/bash
set -euo pipefail
repo_root=$(cd "$(dirname "$0")/../.." && pwd)
capture_tmp=$(mktemp -d /private/tmp/revenge-website.XXXXXX)
trap 'rm -rf "$capture_tmp"' EXIT
xcrun clang -dynamiclib -framework Cocoa "$repo_root/actual/tools/background_guard.m" -o "$capture_tmp/guard.dylib"
export DYLD_INSERT_LIBRARIES="$capture_tmp/guard.dylib"
cat > "$capture_tmp/probe.gd" <<'PROBE'
extends SceneTree
func _initialize():
	quit(0 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1" else 1)
PROBE
/Applications/Godot.app/Contents/MacOS/Godot --headless --path "$repo_root/actual" --log-file "$capture_tmp/probe.log" --script "$capture_tmp/probe.gd"
/Applications/Godot.app/Contents/MacOS/Godot --path "$repo_root/actual" --audio-driver Dummy --rendering-method gl_compatibility --log-file "$repo_root/officialWebsite/reports/godot-capture.log" --script "$repo_root/officialWebsite/tools/${1:-capture_pc.gd}"
