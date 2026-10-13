import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();patch=Path(sys.argv[2]);marker=json.loads((root/'.source-revision.json').read_text())
assert marker['revision']=='81eed5e8f68b6bed1789f682fe78cdd324495afc'
assert marker['patch_sha256']==hashlib.sha256(patch.read_bytes()).hexdigest(),'RVC patch changed'
for name,expected in marker['files'].items():
    path=(root/name).resolve();assert path.is_relative_to(root)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Patched RVC file differs: '+name
print('Patched RVC source verified')
