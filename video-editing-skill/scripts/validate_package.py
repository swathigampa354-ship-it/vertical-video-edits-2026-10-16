#!/usr/bin/env python3
"""Validate the transferable skill; never generate a movie or install anything."""
from pathlib import Path
import argparse,ast,base64,hashlib,json,os,re,zipfile
import yaml
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def is_deliverable(p):return p.is_file()and not any(x in p.relative_to(ROOT).parts for x in['.cache','.venv','__pycache__'])and p.suffix!='.pyc'
def markdown(text):
    out=[];fence=None
    for line in text.splitlines():
        m=re.match(r'^\s*(`{3,}|~{3,})',line)
        if m:
            mark=m[1]
            if fence is None:fence=(mark[0],len(mark));continue
            if mark[0]==fence[0]and len(mark)>=fence[1]:fence=None;continue
        if fence is None:out.append(line)
    return '\n'.join(out)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check-existing-workspace',action='store_true');ap.add_argument('--verify-zip',action='store_true');ap.add_argument('--write-report',action='store_true');a=ap.parse_args()
    required=['SKILL.md','README.md','TEST_REPORT.md','references/WORKFLOW.md','references/VISUAL_STANDARD.md','references/PLACEMENT.md','references/PLAN_FORMAT.md','references/SETUP.md','references/QC.md','scripts/edit.py','scripts/replay_baseline.py','scripts/build_bundle.py','scripts/validate_package.py','templates/editorial-preset.json','templates/baseline-manifest.json','templates/review.template.json','templates/new-job.plan.example.json','examples/portrait/plan.json','examples/portrait/source.mp4','examples/portrait/transcript.json','examples/portrait/test-logo.png']
    errors=[];missing=[x for x in required if not(ROOT/x).is_file()]
    if missing:errors.append('Missing required files: '+str(missing))
    text=(ROOT/'SKILL.md').read_text();meta=yaml.safe_load(text.split('---\n',2)[1]);skill_name=meta['name']
    if skill_name!=ROOT.name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',skill_name)or len(skill_name)>64:errors.append('Invalid skill name/directory')
    if not isinstance(meta.get('description'),str)or not 1<=len(meta['description'])<=1024:errors.append('Invalid description')
    if len(meta.get('compatibility',''))>500:errors.append('Compatibility too long')
    if len(text.splitlines())>=500:errors.append('Main skill exceeds recommended 500 lines')
    files=sorted(p for p in ROOT.rglob('*')if is_deliverable(p));links=0;broken=[];python_files=0
    for p in files:
        if p.is_symlink():errors.append('Symlink not allowed in portable package: '+str(p))
        if p.suffix=='.py':
            try:ast.parse(p.read_text());python_files+=1
            except SyntaxError as e:errors.append('Syntax: '+str(p.relative_to(ROOT))+': '+str(e))
        if p.suffix=='.json':
            try:json.loads(p.read_text())
            except Exception:errors.append('Invalid JSON: '+str(p.relative_to(ROOT)))
        if p.suffix=='.md':
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',markdown(p.read_text())):
                if re.match(r'^[a-zA-Z][\w+.-]*:',target)or target.startswith('#'):continue
                target=target.split('#',1)[0].split('?',1)[0];links+=1
                if not(p.parent/target).exists():broken.append([str(p.relative_to(ROOT)),target])
    if broken:errors.append('Broken local links: '+str(broken))
    copies=json.loads((ROOT/'tests/evidence/copied-assets.json').read_text());mismatches=[]
    for x in copies:
        if not(ROOT/x['bundled']).is_file()or sha(ROOT/x['bundled'])!=x['sha256']:mismatches.append(x['bundled'])
    if mismatches:errors.append('Evidence copies changed: '+str(mismatches))
    preserved=None
    if a.check_existing_workspace:
        baseline=json.loads((ROOT/'tests/evidence/initial-state.json').read_text());changed=[]
        for x in baseline['workspace_files']:
            p=ROOT.parent/x['path']
            if not p.exists()or sha(p)!=x['sha256']:changed.append(x['path'])
        preserved={'checked':len(baseline['workspace_files']),'changed':changed}
        if changed:errors.append('Existing workspace changed')
    values=[os.environ.get('SKILL_SECRET_'+str(i),'')for i in range(1,4)];values=[v for v in values if v];findings=[]
    pat=re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')
    def scan(data,name):
        if pat.search(data):findings.append(name+' pattern')
        for i,v in enumerate(values):
            if v.encode()in data or base64.b64encode(v.encode())in data:findings.append(name+' known credential '+str(i+1))
    for p in files:
        if p.suffix!='.zip':scan(p.read_bytes(),p.relative_to(ROOT).as_posix())
    zip_count=None
    if a.verify_zip:
        with zipfile.ZipFile(ROOT/'portable-skill.zip')as z:
            if z.testzip()is not None:errors.append('ZIP CRC failure')
            names=z.namelist();zip_count=len(names)
            for name in names:
                if not name.startswith('video-editing-skill/')or'..'in Path(name).parts:errors.append('Unsafe ZIP path')
                scan(z.read(name),'ZIP/'+name)
            manifest=json.loads(z.read('video-editing-skill/BUILD_MANIFEST.json'))
            for item in manifest['files']:
                name='video-editing-skill/'+item['path'];data=z.read(name)
                if hashlib.sha256(data).hexdigest()!=item['sha256']:errors.append('ZIP manifest mismatch: '+name)
                if sha(ROOT/item['path'])!=item['sha256']:errors.append('Distribution file changed after ZIP build: '+name)
    if findings:errors.append('Possible secrets; stop: '+str(findings))
    report={'result':'PASS'if not errors else'FAIL','filesChecked':len(files),'skillFormat':'Agent Skills YAML + Markdown','skillName':skill_name,'skillLines':len(text.splitlines()),'localLinksChecked':links,'brokenLinks':broken,'pythonAstChecked':python_files,'exactCopiesChecked':len(copies),'copyMismatches':mismatches,'existingWorkspace':preserved,'knownSecretValuesChecked':len(values),'secretFindings':findings,'zipMembersChecked':zip_count,'errors':errors,'nativeClientRegistrationTested':False,'note':'Structure/integrity test, not a guarantee of creative quality on a new source. Exact credential values are never printed or stored.'}
    if a.write_report:(ROOT/'tests/evidence/package-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
if __name__=='__main__':main()
