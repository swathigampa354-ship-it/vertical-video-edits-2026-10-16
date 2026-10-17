# Portable video-editing skill

This is a production workflow, **not another session archive**. Start with [SKILL.md](SKILL.md). It tells an independent coding/vision agent how to inspect new raw footage, derive speech-led scene timing, apply the established craft, render, inspect and validate the result.

## Use in a fresh Arena chat / another ID

1. Download **[portable-skill.zip](https://raw.githubusercontent.com/swathigampa354-ship-it/vertical-video-edits-2026-10-16/main/video-editing-skill/portable-skill.zip)** and upload it with your new raw video.
2. Add your actual logo/brand assets only if you want them used.
3. Say:

> Extract this skill bundle. Read `video-editing-skill/SKILL.md` and its required references. Edit the attached raw video using the documented default quality/style. Inspect this new source, generate its own timing/scene plan, render, inspect the encoded output and fix problems before delivering the finished MP4. Preserve its original speech. Do not ask me to repeat the documented defaults.

Default profile: **editorial-v2** (black/orange/cream serif treatment, the version explicitly praised). Say **“morph-v3”** for the latest off-white/black/cobalt one-shape style, or **“sports-v1”** for the red/lime alternative. These are small profile choices, not a request to repeat the full brief.

A lone Markdown file cannot physically contain font binaries, images and executables. Its core rules are self-contained, but transfer the ZIP/folder for the tested tools/reference assets. If permitted, a new agent can fetch this public folder instead:

https://github.com/swathigampa354-ship-it/vertical-video-edits-2026-10-16/tree/main/video-editing-skill

## Package contents

- `SKILL.md`: portable Agent Skills YAML + operational instructions; no client-specific registration assumed.
- `references/`: execution order, recovered visual settings, motion-aware placement, plan schema, QC and setup/troubleshooting; actual final/source reference images.
- `scripts/edit.py`: source inspection, optional transcription, source-bound plan validation, general editorial composition, voice/SFX mix, all-frame logo/overlay geometry and encoded-file QC.
- `scripts/replay_baseline.py`: regression-only reconstruction of exact original V1/V2/V3 templates, guarded by the known input hash. Not a new-footage renderer.
- `templates/`: preset, original seven code files, comparison manifest and new-job examples. Immutable original code retains historical numbers; the agent must not blindly run it on new footage.
- `assets/fonts/`: original fonts with their OFL licences.
- `tests/`: small fixtures, executable adaptation/negative tests, provenance and actual test results.
- `requirements*.txt`: core imports, observed tested direct versions, optional ASR dependency.
- `TEST_REPORT.md`: actual regression/adaptation/review evidence and limits.

## What this does not promise

It does not install itself automatically, recover another chat's memory, produce 1,000 finished reels in one click, remove watermarks, clone faces, fabricate a brand, or turn 360p footage into native 1080p detail. No original edit had an added brand logo. Logo geometry is a newly codified, tested extension using a clearly synthetic test mark; real logos/complex tracking need inspection.

The reference method is proven on the original fixtures and a controlled new geometry/duration case. Unrelated footage, HDR/VFR conversions, new languages/fonts, complex occlusion/tracking and other OS/dependency versions need their own checks. Never substitute a technical render PASS for a visual quality review.
