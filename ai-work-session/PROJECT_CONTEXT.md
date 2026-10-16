# Project context

## Purpose

Create original short-form motion-graphics edits around a user-supplied interview clip about startups going international, investing early, and helping people, businesses, developers and governments build voice agents. The user requested **9:16** delivery and storage in the **same GitHub repository**, later explicitly requiring that repository to be public.

The initial attachment, [original-brief.pdf](references/inputs/original-brief.pdf), combined AI-news resources with a long VybeSchool motion-design brief. The user clarified that the desired deliverable was a video. Later concrete raw/reference files and explicit style choices superseded the generic white/VybeSchool direction. No brand assets were supplied; no unrelated company branding or speaker identity was invented.

## Existing repository and initial Git state

- Repository: `swathigampa354-ship-it/vertical-video-edits-2026-10-16`.
- URL: https://github.com/swathigampa354-ship-it/vertical-video-edits-2026-10-16
- Remote: `https://github.com/swathigampa354-ship-it/vertical-video-edits-2026-10-16.git`.
- Branch: `main`; public and not protected when inspected for this archive.
- Pre-archive tip: `fec3027a03a64c2c3f56995a1bb445db7d3b84e6`.
- The initial local workspace was `/home/user/video-project` **without `.git` metadata**. Earlier uploads used authenticated GitHub REST blobs/trees/commits/ref updates, not a shell `git push`.
- Fresh inspection found 14 remote tracked files and six commits. All 14 files matched their local Git blob hashes. There was no tracked root `.gitignore` or `.gitattributes` and no existing skill-discovery directory.
- For this archive, Git metadata/index were attached to that same remote without a worktree checkout. Existing untracked analysis, source, fonts, raw/reference media, and an old `.gitkeep` were preserved. This is not a second GitHub repository.

See [initial remote state](references/evidence/initial-remote-state.json), [initial inventory](references/evidence/initial-workspace-inventory.json), and [FILE_CHANGE_LOG.md](FILE_CHANGE_LOG.md).

## Delivered versions

| Version | Existing folder | Visual direction | Video bytes | Export |
|---|---|---|---:|---|
| V1 | [voice-agents-9x16](../edits/voice-agents-9x16/README.md) | Red/lime sports-edit energy: bold italic type, punch-ins, low-intensity flashes, diagrams and quiet original beat/SFX | 10,688,724 | 1080 × 1920, 30 fps, 641 frames |
| V2 | [voice-agents-editorial-v2](../edits/voice-agents-editorial-v2/README.md) | Black/orange/cream editorial: serif captions, bold grid quote, circular video cutout, rounded panels and audience icons | 4,415,601 | 1080 × 1920, 30 fps, 641 frames |
| V3 | [voice-agents-morph-v3](../edits/voice-agents-morph-v3/README.md) | Off-white/black/cobalt: one continuously morphing UI container, globe, effort slider, early toggle, audience network and voice player | 5,902,296 | 1080 × 1920, 60 fps graphics, 1,282 frames |

Each video lasts 21.3667 s (displayed as 21.37 s). Each folder also has `poster.jpg`, `captions.srt`, and `README.md`. V2 and V3 are additional versions, not replacements. Historical upload scripts checked earlier MP4 blob hashes remained unchanged.

## Inputs and constraints

- Raw video: `assets/raw.mp4`, 1,101,889 bytes, 640 × 360 H.264, approximately 29.97 fps, 620 source video frames; audio duration approximately 20.7354 s, AAC stereo 44.1 kHz.
- Original source link: https://www.youtube.com/watch?v=FcvFNbcCL98
- Actual accessible raw input arrived through Filebin. An exact copy is preserved in [source-snapshot/assets/raw.mp4](references/source-snapshot/assets/raw.mp4).
- First usable style: IShowSpeed WWE edit, 360 × 480, approximately 56.82 s, 4,317,118 bytes.
- Second usable style: `InShot_20261016_064447731.mp4`, 720 × 1218, approximately 34.27 s, 27,117,601 bytes.
- V3 gallery inspiration: https://github.com/yihui-dev/awesome-opus5-5-videos, primarily `twoclipping-402193` (a 14 s, 60 fps one-shape UI study).
- Original narration stays chronological and on its original timeline. No reference footage/audio/music was used, no synthetic replacement narrator was generated, no generative face changes or optical-flow interpolation were used.
- A 1080p container does not turn 360p source footage into native 1080p detail. V3's graphics animate at 60 fps; its source footage retains native approximately 29.97 fps sampling.
- Public reference-video binaries are not republished in this documentation folder. Their known metadata, links, hashes, scene plans, and contact-sheet evidence are retained. Derived audio/visual intermediates are likewise inventoried, not all duplicated.

## Architecture

This is a file-based, custom **Python + FFmpeg** media project, not a deployed web app or a native Flick project.

1. **Acquisition:** public HTTP Filebin downloads with persistent session/cookie handling and MP4 signature validation.
2. **Speech timing:** `transcribe.py` extracts mono 16 kHz WAV using imageio's bundled FFmpeg, then runs `WhisperModel('base.en', device='cpu', compute_type='int8', cpu_threads=2)`. Final working code passes a SoundFile-loaded NumPy array to avoid the observed PyAV decoder incompatibility.
3. **Scene planning:** three explicit Markdown plans map speech timestamps to visuals, transitions and sounds.
4. **Visual rendering:** Pillow text/masks/vector drawing, OpenCV source sampling/resizing, NumPy geometry, font assets, and a raw RGB pipe to FFmpeg/libx264.
5. **Audio:** original speech normalized with a 65 Hz high-pass and FFmpeg loudness processing; original synthesized effects/quiet bed as appropriate; SoundFile/SciPy produce stereo WAV.
6. **Mux:** H.264 visual stream copied into MP4; new audio encoded AAC 192 kbit/s, 48 kHz stereo; `+faststart` and `-shortest` used.
7. **Validation:** full decode; OpenCV dimensions/frame count/FPS; source/encoded voice correlation; loudness/true-peak analysis; public GitHub byte/signature and prior-version checks.
8. **Delivery:** originally GitHub REST API object creation and non-force ref update. This archive uses normal Git staging, commit, and push for only `ai-work-session/`.

Full exact final source is retained under [source-snapshot](references/source-snapshot/README.md). [Technical details](references/technical_details.md) document paths, cache behavior, versions, and commands.

## Current environment versus historical environment

Fresh observation: Git 2.47.3, Node v20.20.2, Python 3.13.16, two CPU cores, Linux. Installed package versions are in [environment-observed-now.json](references/evidence/environment-observed-now.json). Several packages that were installed during video production are absent after workspace restoration: `imageio-ffmpeg`, `faster-whisper`, `ctranslate2`, `av`, PyMuPDF and yt-dlp. Cached V2/V3 visual/audio files and model downloads are absent. Shell history files are absent. The final outputs, original source scripts, key input assets, analysis and persisted QC/delivery reports remain accessible.

Historical package resolution was not pinned. Current package versions must not be presented as a validated historical lockfile. The archive task does not silently install packages or rerender videos.

## Flick feasibility audit

The latest video-related request was read-only: verify a reported claim that `Creatorberry/flick` can create 1,000 videos, assess whether this assistant could use it, and estimate time. No videos were requested for that audit.

Observed repository structure: agent skill + helper scripts + Remotion starter + reusable scene library. The audit read 39 canonical text/source files, found 14 catalog patterns, and no textual 1,000-video/batch/bulk claim. `render-scene.mjs` accepts one composition/name and synchronously runs one Remotion command. The starter `Root.tsx` returns `null`; an agent must author/register approved scene components. Documentation requires approval and review and explicitly keeps scenes independent rather than creating an all-scenes composition.

Conclusion: repeated use/custom orchestration can plausibly make many outputs, but no native 1,000-finished-reel batch mode or published benchmark was verified. Flick was **not installed, run end-to-end, or stress-tested**. Earlier videos are not Flick benchmarks. Timing estimates were explicitly planning estimates, not promises or measured Flick results.

## Completed / incomplete

Confirmed completed before this task: three separate edits, captions/posters/notes, public repository delivery, preserved earlier versions, and a read-only Flick code/documentation audit.

Not completed or not verified: stock Flick installation/render, a 1,000-video test, third-party posting integration, native client registration of this skill, replacement of inaccessible YouTube media by authenticated playback, and any further video request. Credential rotation status is unknown. Final archive push status is recorded only after evidence exists; consult [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) and [CONTINUE.md](CONTINUE.md).
