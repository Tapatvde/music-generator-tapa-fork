"""Generate or check the source-only manifest. Run only in the publication folder."""
import hashlib,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
excluded={'PACKAGE-CONTENTS.json','SHA256SUMS.txt'}
def files():
    output=[]
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(root)
        if rel.parts[0] in ('engine','data','.venv','.git') or '__pycache__' in rel.parts:continue
        if rel.as_posix() in excluded:continue
        output.append({'path':rel.as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return output
current=files()
if '--write' in sys.argv:
    for directory in ('engine','data','.venv','.git'):
        if (root/directory).exists():raise ValueError('Create the publication manifest only in a clean source folder: '+directory)
    for entry in current:
        path=root/entry['path']
        if path.suffix.lower() in ('.exe','.dll','.pth','.pt','.index','.gguf','.wav','.mp3','.m4a','.flac','.db','.sqlite'):
            raise ValueError('Runtime/private file in source package: '+entry['path'])
        if path.stat().st_size>50*1024*1024:raise ValueError('Unexpected large source file')
        text=path.read_text(encoding='utf-8-sig',errors='ignore') if path.suffix!='.png' else ''
        if path.name=='.env':raise ValueError('Do not distribute environment files')
        if re.search(r'[A-Za-z]:[/\\]Users[/\\][^/\\\s]+',text):raise ValueError('Personal Windows path in source: '+entry['path'])
        if re.search(r'github_pat_[A-Za-z0-9_]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----',text):raise ValueError('Credential-looking data')
    report={'schema_version':1,'package':'Music Generator – Tapa Fork','date':'2026-10-13','files':current,'total_bytes':sum(row['bytes'] for row in current),'private_data_included':False,'runtime_binaries_included':False}
    (root/'PACKAGE-CONTENTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'SHA256SUMS.txt').write_text('\n'.join(row['sha256']+'  '+row['path'] for row in current)+'\n',encoding='utf-8')
else:
    expected=json.loads((root/'PACKAGE-CONTENTS.json').read_text(encoding='utf-8'))
    if expected['files']!=current:raise ValueError('Source package differs from its manifest')
print('Source package verified:',len(current),'files;',sum(row['bytes'] for row in current),'bytes')
