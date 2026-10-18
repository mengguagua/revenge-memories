#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
campaign_engine=/Applications/Godot.app/Contents/MacOS/Godot
campaign_app=dist/.RevengeMemories-build.app
mkdir -p "$campaign_app/Contents/MacOS" "$campaign_app/Contents/Resources"
"$campaign_engine" --headless --quiet --audio-driver Dummy --path "$PWD" --log-file "$PWD/reports/campaign/package-engine.log" --export-pack macOS "$PWD/dist/RevengeMemories.pck"
cp "$campaign_engine" "$campaign_app/Contents/MacOS/RevengeMemories"
cp dist/RevengeMemories.pck "$campaign_app/Contents/Resources/RevengeMemories.pck"
python3 - <<'PY'
from pathlib import Path
import plistlib
p={'CFBundleName':'复仇与回忆','CFBundleDisplayName':'复仇与回忆 · 第三章','CFBundleIdentifier':'local.revenge-memories.actual','CFBundleExecutable':'RevengeMemories','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.8.0','CFBundleVersion':'0.8.0','NSHighResolutionCapable':True,'LSMinimumSystemVersion':'11.0','LSApplicationCategoryType':'public.app-category.games'}
Path('dist/.RevengeMemories-build.app/Contents/Info.plist').write_bytes(plistlib.dumps(p))
PY
chmod +x "$campaign_app/Contents/MacOS/RevengeMemories"
codesign --force --sign - "$campaign_app/Contents/MacOS/RevengeMemories"
codesign --force --sign - "$campaign_app"

if [ -d dist/RevengeMemories.app ]; then
  campaign_backup="dist/RevengeMemories-previous.app"
  if [ -d "$campaign_backup" ]; then rm -rf "$campaign_backup"; fi
  mv dist/RevengeMemories.app "$campaign_backup"
fi
mv "$campaign_app" dist/RevengeMemories.app
