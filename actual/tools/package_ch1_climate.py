#!/usr/bin/env python3
"""Independent chapter1 climate app; verifies the exported PCK outside the repo."""
from pathlib import Path
import hashlib,json,os,plistlib,shutil,subprocess,tempfile,sys
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter1-climate-20261022'
engine=Path('/Applications/Godot.app/Contents/MacOS/Godot')
name='RevengeMemories-Chapter1-Climate-20261022'
app=R/'dist'/(name+'.app');build=R/'dist'/('.'+name+'-build.app')
expect_path=O/'package-expected.json';expected=json.loads(expect_path.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def source_stable():
 assert sha(R/'project.godot')==expected['project_godot_sha256']
 assert sha(R/'export_presets.cfg')==expected['export_presets_sha256']
 for path,h in expected['core_snapshot_hashes'].items():assert sha(R/path)==h,path
 for code,m in expected['maps'].items():assert sha(R/'data/stages'/(code+'.json'))==m['sha256'],code
 for path,h in expected['climate_json'].items():assert sha(R/path.removeprefix('res://'))==h,path
 for path,m in expected['climate_textures'].items():assert sha(R/path.removeprefix('res://'))==m['source_png_sha256'],path
assert expected['frozen'];source_stable()
info={'CFBundleName':'复仇与回忆','CFBundleDisplayName':'复仇与回忆 · 第一章寒地修订','CFBundleIdentifier':'local.revenge-memories.chapter1-climate','CFBundleExecutable':'RevengeMemories','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.10.3','CFBundleVersion':'0.10.3','NSHighResolutionCapable':True,'LSMinimumSystemVersion':'11.0','LSApplicationCategoryType':'public.app-category.games'}
if '--probe-only'not in sys.argv:
 assert not app.exists(),'Refuse to overwrite an already delivered app'
 assert not build.exists(),'Inspect prior incomplete build before reuse'
 (build/'Contents/MacOS').mkdir(parents=True)
 (build/'Contents/Resources').mkdir(parents=True)
 pck=build/'Contents/Resources/RevengeMemories.pck'
 with (O/'package-export-stdout.log').open('w')as log:
  subprocess.run([str(engine),'--headless','--quiet','--audio-driver','Dummy','--path',str(R),'--log-file',str(O/'package-engine.log'),'--export-pack','macOS',str(pck)],check=True,stdout=log,stderr=subprocess.STDOUT)
 binary=build/'Contents/MacOS/RevengeMemories';shutil.copy2(engine,binary);binary.chmod(0o755)
 (build/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
 subprocess.run(['codesign','--force','--sign','-',str(binary)],check=True)
 subprocess.run(['codesign','--force','--sign','-',str(build)],check=True)
 build.rename(app)
binary=app/'Contents/MacOS/RevengeMemories';pck=app/'Contents/Resources/RevengeMemories.pck'
subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
source_stable()
isolated=Path(tempfile.mkdtemp(prefix='ch1-climate-package-probe.',dir='/private/tmp'))
env=os.environ.copy();env['CH1_PACKAGE_EXPECTED']=str(expect_path);env['CH1_PACKAGE_REPORT']=str(O/'package-checks.json')
with (O/'package-probe-stdout.log').open('w')as log:
 subprocess.run([str(binary),'--headless','--audio-driver','Dummy','--path',str(isolated),'--main-pack',str(pck),'--log-file',str(O/'package-probe.log'),'--script',str(R/'tools/package_ch1_climate_probe.gd')],cwd=isolated,env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
source_stable();report=json.loads((O/'package-checks.json').read_text());assert report['passed']
report.update({'app_path':str(app),'display_name':info['CFBundleDisplayName'],'pck_bytes':pck.stat().st_size,'pck_sha256':sha(pck),'ad_hoc_signature_verified':True,'signature_verification':'codesign --verify --deep --strict exit 0','headless_only':True,'expected_current_maps_match_after_signing':True,'climate_assets_match_after_signing':True,'source_core_snapshot_stable_during_export':True,'core_snapshot_hashes':expected['core_snapshot_hashes'],'project_godot_unchanged':True,'export_presets_unchanged':True,'isolated_probe_path':str(isolated)})
(O/'package-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k]for k in ['passed','checks','software_version','map_revision','stage_count','winter_rock_count','app_path','pck_bytes','pck_sha256']},ensure_ascii=False))
