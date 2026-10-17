#!/usr/bin/env python3
"""Independently verify an archive tree. No writes, downloads or deletion."""
from pathlib import Path
import argparse,hashlib,json,re,stat

def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def md_visible(text):
    result=[];fence=None
    for line in text.splitlines():
        m=re.match(r'^\s*(`{3,}|~{3,})',line)
        if m:
            token=m[1]
            if fence is None:fence=(token[0],len(token));continue
            if token[0]==fence[0]and len(token)>=fence[1]:fence=None;continue
        if fence is None:result.append(line)
    return '\n'.join(result)

def verify(root,expected=None):
    root=Path(root).resolve();manifest=root/'SHA256SUMS.txt';assert manifest.is_file(),'Missing SHA256SUMS'
    hashes={}
    for line in manifest.read_text().splitlines():
        if not line:continue
        assert re.match(r'^[a-f0-9]{64}  ',line),'Malformed SHA256SUMS line'
        digest,rel=line[:64],line[66:];assert not Path(rel).is_absolute()and'..'not in Path(rel).parts
        hashes[rel]=digest
    actual={p.relative_to(root).as_posix():p for p in root.rglob('*')if p.is_file()}
    assert set(actual)==set(hashes)|{'SHA256SUMS.txt'},'Archive path/count mismatch'
    errors=[]
    for rel,digest in hashes.items():
        if sha(actual[rel])!=digest:errors.append('Checksum '+rel)
    if expected:
        ex=expected['files'];assert set(ex)==set(actual),'Original frozen file count/paths differ'
        for rel,item in ex.items():
            f=actual[rel]
            if f.stat().st_size!=item['size']or sha(f)!=item['sha256']:errors.append('Original expected content '+rel)
            expected_exec=bool(int(item['mode'],8)&0o111)
            if bool(f.stat().st_mode&0o111)!=expected_exec:errors.append('Executable mode '+rel)
    mapping=json.loads((root/'configs/source-map.json').read_text());source_ids={}
    for item in mapping['copies']:
        f=root/item['archive_path']
        if not f.is_file()or f.stat().st_size!=item['size']or sha(f)!=item['sha256']:errors.append('Original copy mismatch '+item['archive_path'])
        source_ids[(item['source_group'],item['source_relative'])]=True
    layout=json.loads((root/'configs/layout.json').read_text());allowed=set(layout['allowed_markdown'])
    md={x for x in actual if x.lower().endswith(('.md','.markdown'))}
    if md!=allowed:errors.append('Markdown exception whitelist mismatch')
    links=0;broken=[];skill_entries=[]
    for rel in sorted(md):
        p=root/rel
        if p.name=='SKILL.md':
            text=p.read_text();assert text.startswith('---\n'),'Missing skill frontmatter';assert re.search(r'^name: '+re.escape(p.parent.name)+r'\s*$',text,re.M),'Skill folder/name mismatch';skill_entries.append(rel)
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',md_visible(p.read_text())):
            if re.match(r'^[a-zA-Z][\w+.-]*:',target)or target.startswith('#'):continue
            target=target.split('#',1)[0].split('?',1)[0]
            from urllib.parse import unquote
            target=unquote(target);links+=1
            if not(p.parent/target).exists():broken.append([rel,target])
    if broken:errors.append('Broken skill reference links: '+str(broken[:12]))
    lfs=[];videos=[];empty=[]
    for rel,f in actual.items():
        with f.open('rb')as stream:prefix=stream.read(128)
        if prefix.startswith(b'version https://git-lfs.github.com/spec/v1'):lfs.append(rel)
        if f.stat().st_size==0:empty.append(rel)
        if f.suffix.lower()in['.mp4','.mov','.m4v','.webm','.avi']:
            if f.suffix.lower()in['.mp4','.mov','.m4v']and prefix[4:8]!=b'ftyp':errors.append('Invalid media signature '+rel)
            videos.append(rel)
    if lfs:errors.append('Unexpected LFS pointers instead of actual objects')
    intended_empty={x['archive_path']for x in mapping['copies']if x['size']==0}
    if any(x not in intended_empty for x in empty):errors.append('Unintentionally empty generated files')
    result={'result':'PASS'if not errors else'FAIL','archive_files':len(actual),'sha256_entries':len(hashes),'sha256_manifest_sha256':sha(manifest),'source_files_covered':len(source_ids),'source_copies_checked':len(mapping['copies']),'skill_entries':skill_entries,'markdown_exceptions':len(md),'local_skill_links_checked':links,'broken_skill_links':broken,'video_paths':videos,'video_path_count':len(videos),'lfs_pointers':lfs,'intentional_empty_files':empty,'errors':errors}
    if errors:raise RuntimeError(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--expected',type=Path);a=ap.parse_args();expected=json.loads(a.expected.read_text())if a.expected else None
    print(json.dumps(verify(a.root,expected),indent=2))
