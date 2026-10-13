#!/bin/zsh
set -e
project_dir="${0:A:h}"
campaign_app="$project_dir/dist/FE2Campaign.app/Contents/MacOS/FE2Campaign"
if [[ -x "$campaign_app" ]]; then
  exec "$campaign_app"
fi
exec /Applications/Godot.app/Contents/MacOS/Godot --path "$project_dir"
