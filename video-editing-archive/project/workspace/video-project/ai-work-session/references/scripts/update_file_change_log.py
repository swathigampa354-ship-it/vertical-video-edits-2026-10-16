#!/usr/bin/env python3
"""Regenerate this archive's path inventory; never edits other project files."""
from pathlib import Path
import json
A=Path(__file__).resolve().parents[2]
path=A/'FILE_CHANGE_LOG.md'
if not path.exists():path.touch()
prov=json.loads((A/'references/evidence/copied-artifact-provenance.json').read_text())
origins={x['archived']:x for x in prov['copies']}
core={
'SKILL.md':'Portable Agent Skills entry point; metadata, context loading, safety, known commands and continuation.',
'SESSION_ARCHIVE.md':'Detailed partial visible-session record, full redacted long prompts, chronological tools/results and visual evidence.',
'PROJECT_CONTEXT.md':'Purpose, architecture, real repository state, three delivered versions and constraints.',
'DECISION_LOG.md':'Problems, evidence, decisions, trade-offs and explicit verification/estimate labels.',
'COMMANDS_AND_TOOLS.md':'Historical/current commands versus future equivalents; tools and prerequisites.',
'ERRORS_AND_SOLUTIONS.md':'Observed failures, successful workarounds, remaining uncertainty and non-tests.',
'FILE_CHANGE_LOG.md':'Complete current archive file list and historical project change inventory.',
'VERIFICATION_REPORT.md':'Fresh validation versus historical tests and actual commit/push evidence.',
'CONTINUE.md':'Latest checkpoint, outstanding constraints and a ready-to-use next-agent prompt.',
'references/requirements.md':'Original attachment requirements, explicit user changes and archive contract.',
'references/technical_details.md':'Pipeline, paths/caches, timing, encoding, packages and Git attachment details.',
'references/troubleshooting.md':'Known failure paths, safe next actions and false assumptions to avoid.',
'references/session_index.md':'Navigation across chronology, evidence, reports and existing outputs.',
'.gitignore':'Archive-local generated-output/credential exclusions; root ignore rules unchanged.',
'.gitattributes':'Scoped whitespace-check exception only for exact copied OFL license texts; authored docs/code remain checked.',
}
files=sorted(p for p in A.rglob('*')if p.is_file()and'__pycache__'not in p.parts)
lines=['# File change log\n','## Archive task scope\n','Every new tracked deliverable from this task is under `ai-work-session/`. No existing root README, delivered video, original source or local input is edited. Operational Git metadata was initialized solely to attach the same existing remote; it is not part of the archive commit. Initial comparison found 14 remote files identical locally and 131 pre-existing workspace files. The strict validator rechecks those 131 hashes.\n','## Complete list of files created\n',f'This list contains **{len(files)} files** currently present in the archive (including this inventory). Exact copied artifact hashes are independently preserved in `references/evidence/copied-artifact-provenance.json`. Generated report dates/commit status are evidence, not guessed future outcomes.\n','| New path (repository-relative) | Actual change / reason | Verification or provenance |\n','|---|---|---|\n']
for p in files:
 rel=p.relative_to(A).as_posix();full='ai-work-session/'+rel
 if rel in origins:
  q=origins[rel];reason='Exact byte-copy of `'+q['original']+'`; preserve recoverable source/input/evidence.';verify=f"{q['bytes']:,} bytes; SHA-256 `{q['sha256']}`; checked by validator."
 else:
  reason=core.get(rel)
  if reason is None:
   if rel.startswith('references/scripts/'):reason='Archive-owned capture/inventory/validation/authentication helper; no embedded credential.'
   elif rel.startswith('references/evidence/'):reason='Recovered visible text or machine-captured archive/Git/validation evidence; redacted where needed.'
   elif rel.startswith('references/source-snapshot/'):reason='Snapshot usage/dependency documentation; no modification to original renderers.'
   else:reason='Archive-owned supporting documentation.'
  verify='Included in path/link/secret validation; see verification report.'
 lines.append(f'| `{full}` | {reason} | {verify} |\n')
lines.extend(['\n## Historical project changes recovered\n','| Historical path/group | Change and purpose | Status/evidence |\n','|---|---|---|\n','| `README.md` | Created as placeholder, then updated by each successful version upload to index final outputs. | Remote/local hash matched before archive; not edited now. |\n','| `assets/README.md` | Initial media-upload instructions. | Still tracked; not edited now. |\n','| `edits/voice-agents-9x16/.gitkeep` | Initial empty output placeholder removed from remote during V1 delivery. | Stale local untracked copy remains; not deleted/staged by archive task. |\n','| `assets/raw.mp4` | Downloaded actual source input after Filebin session fix. | Retained locally and exact archive snapshot; not modified. |\n','| `assets/style-reference.mp4`, `assets/style-reference-v2.mp4` | Downloaded style references, not final footage. | Local only, inventoried; full third-party videos not republished. |\n','| `assets/fonts/*` | Downloaded Barlow, Instrument Serif, Inter, Geist/Geist Mono and licenses. | Exact archive copies with provenance. |\n','| `source/transcribe.py` | Created; fixed path/PyAV decoder issue by passing SoundFile NumPy samples. | Exact final snapshot; historical failure/fix documented. |\n','| `source/audio.py`, `source/render.py` | V1 original motion/audio code and visual-review fixes. | Exact final snapshots; historical render/QC passed. |\n','| `source/audio_editorial_v2.py`, `source/render_editorial_v2.py` | V2 new editorial style, spacing fixes and restrained SFX. | Exact final snapshots; separate delivery preserved V1. |\n','| `source/audio_morph_v3.py`, `source/render_morph_v3.py` | V3 deterministic one-container 60 fps motion, source waveform and original sounds. | Exact final snapshots; separate delivery preserved V1/V2. |\n','| `analysis/*.json`, `analysis/*.md`, `analysis/*media-info.txt` | ASR, plans, source metadata, failed yt-dlp artifacts, Browserless status, QC and REST delivery records. | Exact text copies; stale/private and failed artifacts labeled historical. |\n','| `analysis/*contact.jpg`, source/design sample frames | Actual visual inspection artifacts. | Seven representative contact sheets archived; all remaining paths/hashes inventoried. |\n','| `analysis/*.wav`, `analysis/visuals.mp4` | Generated speech/audio/visual intermediates. | Original mono WAV included for reproduction; bulky derived files inventoried, not all duplicated. |\n','| `/home/user/.cache/video-project-*` | V2/V3 intermediate media/model/reference cache. | Absent after restore; not fabricated/recovered. |\n','| `/home/user/pdf-page-1.png` through `pdf-page-15.png` | PDF page renders from original extraction. | Still accessible outside project; original PDF is archived instead of duplicating all page images. |\n','| `/home/user/browserless-hello*.png` | Newly created read-only screenshot test image. | Verified then deleted by that test; no pre-existing file removed. |\n','| Three existing `edits/` folders | MP4, poster, captions and notes delivered in separate version folders. | Remain unchanged; current decode/hash checks and historical QC/delivery reports retained. |\n','\n## Unknown or non-recoverable change detail\n','Earlier source files were not committed individually, and no shell-history export exists. Final source bytes and visible edit deltas are available, but this file does not invent a full revision history of every intermediate file write. A broad gallery-search output was truncated. Current environment package versions are observations, not an original dependency lock.\n','\n## Git scope / preservation\n','Stage with `git add -- ai-work-session` only. Review `git diff --cached --name-status`, full staged diff and `--check`. Pre-existing untracked files outside this folder must remain untracked/unchanged. Normal push only; never reset/clean/force-push to make the archive appear clean.\n'])
path.write_text(''.join(lines));print('FILE_CHANGE_LOG.md inventories',len(files),'archive files.')
