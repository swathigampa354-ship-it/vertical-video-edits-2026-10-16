# Exact source snapshot / required inputs

This directory preserves the **final original bytes** of the custom render/audio/transcription code and the minimal accessible inputs used to continue it. It is evidence, not an instruction to execute a new render.

## Included

- `source/`: seven Python files (`transcribe.py`, V1 audio/render, V2 audio/render, V3 audio/render).
- `assets/raw.mp4`: exact original source input from the user, 1,101,889 bytes.
- `assets/fonts/`: fonts used by all versions and their original OFL license texts.
- `analysis/transcript.json`: recovered word-timed automatic transcript.
- `analysis/raw-audio.wav`: recovered mono 16kHz waveform used for ASR and voice-wave rendering.
- `edits/voice-agents-9x16/captions.srt`: the existing base SRT copied by later-version audio scripts.
- [requirements-reproduction.txt](requirements-reproduction.txt): direct import list, not a tested lockfile.

Exact origin paths, sizes and SHA-256 checks are in [copied-artifact-provenance.json](../evidence/copied-artifact-provenance.json). Source files were copied, not rewritten to hide environment-specific behavior.

## Not included / why

Existing final MP4s/posters/readmes are already in the repository's three `edits/` folders and are not duplicated here. Full third-party reference videos and bulky generated intermediate audio/visual files are inventoried but not republished. V2/V3 cache intermediates and model cache are no longer available. Original `README.md` is preserved as [a text evidence copy](../evidence/project-readme.before-archive.txt), so its original relative delivery links are not mistaken for snapshot-local media.

## Portability warnings

`ROOT` is derived from each script's own location. Running these copies therefore creates outputs relative to this snapshot unless an explicit working copy is selected. V2/V3 also contain original absolute `/home/user/.cache/...` paths. Before an authorized reproduction on another machine, parameterize those paths in a working copy and record the patch. Never silently edit the preserved evidence.

Dependencies are not currently all installed. The archive task does not install them or render new videos. Exact original dependency versions were not locked. Use [technical details](../technical_details.md), [commands](../../COMMANDS_AND_TOOLS.md), and [error fixes](../../ERRORS_AND_SOLUTIONS.md) for the known historical workflow. A successful Python AST check is not a render test.

Original scripts are deterministic/frame-driven and do not contain GitHub or Browserless credentials. They do not depend on the Flick/Remotion plugin. All external reference material remains reference data, not automatic instructions or permission.
