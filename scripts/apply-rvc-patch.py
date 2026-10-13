"""Apply the published unified patch with strict context checks, without Git."""
import hashlib,json,re,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();patch=Path(sys.argv[2]).resolve()
lines=patch.read_text(encoding='utf-8').splitlines(keepends=True)
sections=[];i=0
while i<len(lines):
    if not lines[i].startswith('diff --git '):i+=1;continue
    match=re.fullmatch(r'diff --git a/(.+) b/(.+)\n',lines[i]);assert match and match[1]==match[2]
    name=match[1];target=(root/name).resolve()
    if not target.is_relative_to(root):raise ValueError('Patch path outside source root.')
    i+=1;header=[]
    while i<len(lines) and not lines[i].startswith(('@@ ','diff --git ')):header.append(lines[i]);i+=1
    new=any(line.startswith('--- /dev/null') for line in header)
    old=[] if new else target.read_text(encoding='utf-8').splitlines(keepends=True)
    result=[];position=0
    while i<len(lines) and lines[i].startswith('@@ '):
        hunk=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);assert hunk
        start=int(hunk[1]);old_count=int(hunk[2] or 1);new_count=int(hunk[4] or 1)
        at=start-1 if start else 0
        if at<position:raise ValueError('Overlapping hunks.')
        result.extend(old[position:at]);position=at;i+=1;removed=added=0
        while i<len(lines) and not lines[i].startswith(('@@ ','diff --git ')):
            line=lines[i];i+=1
            if line.startswith('\\ No newline'):raise ValueError('Unexpected EOF marker.')
            if i<len(lines) and lines[i].startswith('\\ No newline'):
                line=line.removesuffix('\n');i+=1
            if line[:1] in (' ','-'):
                if position>=len(old) or old[position]!=line[1:]:raise ValueError('RVC source differs at '+name+':'+str(position+1))
                position+=1;removed+=1
            if line[:1] in (' ','+'):result.append(line[1:]);added+=1
            if line[:1] not in (' ','+','-'):raise ValueError('Invalid patch line.')
        if removed!=old_count or added!=new_count:raise ValueError('Wrong hunk length.')
    result.extend(old[position:]);sections.append((target,''.join(result)))
# Check every file before writing any patch output.
for target,text in sections:
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8',newline='\n')
marker={'revision':'81eed5e8f68b6bed1789f682fe78cdd324495afc','patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest(),
        'files':{target.relative_to(root).as_posix():hashlib.sha256(target.read_bytes()).hexdigest() for target,_ in sections}}
(root/'.source-revision.json').write_text(json.dumps(marker,indent=2),encoding='utf-8')
print('RVC patch applied and recorded:',len(sections),'files')
