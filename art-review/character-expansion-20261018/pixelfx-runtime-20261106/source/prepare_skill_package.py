"""Use the bundled Skill Installer's downloader, validation, and copy helpers."""
from pathlib import Path
import importlib.util,sys,shutil,tempfile,json
HERE=Path(__file__).resolve().parent
INSTALLER=Path('/Users/gcc/.codex/skills/.system/skill-installer/scripts')
sys.path.insert(0,str(INSTALLER))
spec=importlib.util.spec_from_file_location('pixelfx_skill_installer',INSTALLER/'install-skill-from-github.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
DEST=HERE/'skill-package/pixelfx'
REV='a84159688af3ca37a4be05a0d422b94451b2e24e'
with tempfile.TemporaryDirectory(prefix='pixelfx-install-',dir='/private/tmp') as work:
 repo=Path(module._download_repo_zip('patch-gg','pixelfx',REV,work))
 skill=repo/'skills/pixelfx';module._validate_skill(str(skill),str(repo))
 if not DEST.exists():module._copy_skill(str(skill),str(DEST))
 refs=DEST/'references';refs.mkdir(exist_ok=True)
 shutil.copy2(skill/'SKILL.md',refs/'upstream-skill.md')
 toolkit=DEST/'toolkit';toolkit.mkdir(exist_ok=True)
 for folder in ['src','tools']:shutil.copytree(repo/folder,toolkit/folder,dirs_exist_ok=True)
 (toolkit/'docs').mkdir(exist_ok=True)
 for name in ['AUTHORING.md','CATALOG.md']:shutil.copy2(repo/'docs'/name,toolkit/'docs'/name)
 for name in ['package.json','LICENSE','NOTICE.md']:shutil.copy2(repo/name,toolkit/name)
 shutil.copy2(repo/'LICENSE',DEST/'LICENSE');shutil.copy2(repo/'NOTICE.md',DEST/'NOTICE.md')
 (DEST/'upstream.json').write_text(json.dumps({'repository':'https://github.com/patch-gg/pixelfx','commit':REV,'version':'0.3.0','scope':'MIT source and CLI only; gallery fonts and demo media omitted.'},indent=2))
print('Prepared',DEST)
print('Effects:',sum(1 for p in (DEST/'toolkit/src/fx').glob('*/*.js') if not p.name.startswith('_')))
