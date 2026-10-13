#!/bin/bash
# Build a local self-contained macOS app without downloading export templates.
set -euo pipefail
cd "$(dirname "$0")/.."
godot_engine=/Applications/Godot.app/Contents/MacOS/Godot
app_dir=dist/FE2Campaign.app
mkdir -p "$app_dir/Contents/MacOS" "$app_dir/Contents/Resources"
"$godot_engine" --headless --path . --log-file /private/tmp/fe2-package.log --export-pack macOS dist/FE2Campaign.pck
if [[ ! -f "$app_dir/Contents/MacOS/FE2Campaign" ]]; then
  cp "$godot_engine" "$app_dir/Contents/MacOS/FE2Campaign"
fi
cp dist/FE2Campaign.pck "$app_dir/Contents/Resources/FE2Campaign.pck"
/usr/bin/python3 - <<'PY'
from pathlib import Path
import plistlib
info = {'CFBundleName':'外传复刻·全篇', 'CFBundleDisplayName':'外传复刻·全篇',
        'CFBundleIdentifier':'local.fe2.campaign', 'CFBundleExecutable':'FE2Campaign',
        'CFBundlePackageType':'APPL', 'CFBundleShortVersionString':'0.6',
        'CFBundleVersion':'0.6.0', 'NSHighResolutionCapable':True,
        'LSMinimumSystemVersion':'11.0', 'LSApplicationCategoryType':'public.app-category.games'}
Path('dist/FE2Campaign.app/Contents/Info.plist').write_bytes(plistlib.dumps(info))
PY
chmod +x "$app_dir/Contents/MacOS/FE2Campaign"
codesign --force --sign - "$app_dir/Contents/MacOS/FE2Campaign"
codesign --force --sign - "$app_dir"
