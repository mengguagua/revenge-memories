#!/bin/bash
set -euo pipefail
repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
healer_tmp=$(mktemp -d /private/tmp/revenge-healer-map-guard.XXXXXX)
trap 'rm -rf "$healer_tmp"' EXIT
xcrun clang -dynamiclib -framework Cocoa "$repo_root/actual/tools/background_guard.m" -o "$healer_tmp/guard.dylib"
export DYLD_INSERT_LIBRARIES="$healer_tmp/guard.dylib"
cat > "$healer_tmp/probe.gd" <<'PROBE'
extends SceneTree
func _initialize():
	quit(0 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1" else 1)
PROBE
/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file "$healer_tmp/probe.log" --path "$repo_root/actual" --script "$healer_tmp/probe.gd"
/Applications/Godot.app/Contents/MacOS/Godot --path "$repo_root/actual" --audio-driver Dummy --rendering-method gl_compatibility --log-file "$repo_root/art-review/healer-map-20261104/integration/render.log" --script "$repo_root/art-review/healer-map-20261104/tools/integration_capture.gd"
if rg -q 'SCRIPT ERROR|^ERROR:' "$repo_root/art-review/healer-map-20261104/integration/render.log"; then exit 1; fi
