#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
campaign_engine=/Applications/Godot.app/Contents/MacOS/Godot
campaign_app=dist/RevengeMemories.app
mkdir -p "$campaign_app/Contents/MacOS" "$campaign_app/Contents/Resources"
"$campaign_engine" --headless --audio-driver Dummy --path "$PWD" --log-file "$PWD/reports/campaign/package-engine.log" --export-pack macOS "$PWD/dist/RevengeMemories.pck"
cp "$campaign_engine" "$campaign_app/Contents/MacOS/RevengeMemories"
cp dist/RevengeMemories.pck "$campaign_app/Contents/Resources/RevengeMemories.pck"
python3 - <<'PY'
from pathlib import Path
import plistlib
p={'CFBundleName':'复仇与回忆','CFBundleDisplayName':'复仇与回忆 · 第二章','CFBundleIdentifier':'local.revenge-memories.actual','CFBundleExecutable':'RevengeMemories','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.3.9','CFBundleVersion':'0.3.9','NSHighResolutionCapable':True,'LSMinimumSystemVersion':'11.0','LSApplicationCategoryType':'public.app-category.games'}
Path('dist/RevengeMemories.app/Contents/Info.plist').write_bytes(plistlib.dumps(p))
PY
chmod +x "$campaign_app/Contents/MacOS/RevengeMemories"
codesign --force --sign - "$campaign_app/Contents/MacOS/RevengeMemories"
codesign --force --sign - "$campaign_app"
