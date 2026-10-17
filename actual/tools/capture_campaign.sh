#!/bin/bash
set -euo pipefail
campaign_root=$(cd "$(dirname "$0")/.." && pwd)
campaign_capture_tmp=$(mktemp -d /private/tmp/revenge-campaign.XXXXXX)
trap 'rm -rf "$campaign_capture_tmp"' EXIT
xcrun clang -dynamiclib -framework Cocoa "$campaign_root/tools/background_guard.m" -o "$campaign_capture_tmp/guard.dylib"
export DYLD_INSERT_LIBRARIES="$campaign_capture_tmp/guard.dylib"
cat > "$campaign_capture_tmp/probe.gd" <<'PROBE'
extends SceneTree
func _initialize():
	quit(0 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") == "1" else 1)
PROBE
/Applications/Godot.app/Contents/MacOS/Godot --headless --path "$campaign_root" --log-file "$campaign_capture_tmp/probe.log" --script "$campaign_capture_tmp/probe.gd"
campaign_command=(/Applications/Godot.app/Contents/MacOS/Godot --path "$campaign_root")
if [ -n "${CAMPAIGN_MAIN_PACK:-}" ]; then
  campaign_command+=(--main-pack "$CAMPAIGN_MAIN_PACK")
fi
"${campaign_command[@]}" --audio-driver Dummy --rendering-method gl_compatibility --log-file "${CAMPAIGN_CAPTURE_LOG:-$campaign_root/reports/campaign/capture-engine.log}" --script "${1:-res://tools/capture_campaign.gd}"
