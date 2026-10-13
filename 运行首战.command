#!/bin/zsh
set -e
project_dir="${0:A:h}"
godot_engine="/Applications/Godot.app/Contents/MacOS/Godot"
if [[ ! -x "$godot_engine" ]]; then
  print "请先安装 Godot 4.7，或用已安装的 Godot 打开 project.godot。"
  read -k 1
  exit 1
fi
exec "$godot_engine" --path "$project_dir"
