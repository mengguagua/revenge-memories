#!/usr/bin/env python3
"""Export the new whole-pose knight revision through the existing renderer."""
import json
import export_knight_complete as exporter
from build_gallery import ROOT

if __name__=='__main__':
    exporter.OUT=ROOT/'knight-redraw-v3-20261021'
    exporter.main()
    path=exporter.OUT/'export-report.json'
    data=json.loads(path.read_text())
    data['presentation']='User permitted work-in-progress generation and inspection previews; final answer remains text and gallery link.'
    data['browser_check']='Local file protocol blocked by browser policy; no workaround attempted. Offline frame renderer and exports checked.'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
