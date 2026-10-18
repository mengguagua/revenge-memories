#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
campaign_engine=/Applications/Godot.app/Contents/MacOS/Godot
campaign_name=${CAMPAIGN_PACKAGE_NAME:-RevengeMemories}
campaign_app="dist/.$campaign_name-build.app"
export CAMPAIGN_BUILD_APP="$campaign_app"
mkdir -p "$campaign_app/Contents/MacOS" "$campaign_app/Contents/Resources"
"$campaign_engine" --headless --quiet --audio-driver Dummy --path "$PWD" --log-file "$PWD/reports/campaign/package-engine.log" --export-pack macOS "$PWD/dist/RevengeMemories.pck"
cp "$campaign_engine" "$campaign_app/Contents/MacOS/RevengeMemories"
cp dist/RevengeMemories.pck "$campaign_app/Contents/Resources/RevengeMemories.pck"
python3 - <<'PY'
from pathlib import Path
import plistlib
import os, re
version=re.search(r'config/version="([^"]+)"',Path('project.godot').read_text()).group(1)
p={'CFBundleName':'复仇与回忆','CFBundleDisplayName':'复仇与回忆 · 动画测试 '+version,'CFBundleIdentifier':'local.revenge-memories.actual','CFBundleExecutable':'RevengeMemories','CFBundlePackageType':'APPL','CFBundleShortVersionString':version,'CFBundleVersion':version,'NSHighResolutionCapable':True,'LSMinimumSystemVersion':'11.0','LSApplicationCategoryType':'public.app-category.games'}
(Path(os.environ['CAMPAIGN_BUILD_APP'])/'Contents/Info.plist').write_bytes(plistlib.dumps(p))
PY
chmod +x "$campaign_app/Contents/MacOS/RevengeMemories"
codesign --force --sign - "$campaign_app/Contents/MacOS/RevengeMemories"
codesign --force --sign - "$campaign_app"

if [ -d "dist/$campaign_name.app" ]; then
  campaign_backup="dist/$campaign_name-previous.app"
  if [ -d "$campaign_backup" ]; then rm -rf "$campaign_backup"; fi
  mv "dist/$campaign_name.app" "$campaign_backup"
fi
mv "$campaign_app" "dist/$campaign_name.app"
