from pathlib import Path
import importlib.util,sys,json,hashlib
HERE=Path(__file__).resolve().parent
SCRIPTS=Path('/Users/gcc/.codex/skills/.system/skill-installer/scripts')
sys.path.insert(0,str(SCRIPTS));spec=importlib.util.spec_from_file_location('pixelfx_installer',SCRIPTS/'install-skill-from-github.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
source=HERE/'skill-package/pixelfx';dest=Path('/Users/gcc/.codex/skills/pixelfx')
m._validate_skill(str(source),str(source.parent));m._copy_skill(str(source),str(dest))
files={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
assert all(hashlib.sha256((dest/k).read_bytes()).hexdigest()==v for k,v in files.items())
report={'installed':str(dest),'files':len(files),'upstream_commit':'a84159688af3ca37a4be05a0d422b94451b2e24e','effects':244,'copy_verified':True,'skill_sha256':files['SKILL.md'],'implicit_invocation':True,'toolkit_smoke':'list arrow + render projectiles/arrow --sheet passed before installation','skill_validation':'System quick_validate.py passed'}
(HERE/'skill-installation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
