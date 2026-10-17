# Technical details and reproduction reference

## Evidence boundary

The exact final source files are byte-copied under `source-snapshot/source/`. Their provenance/hashes are in [copied-artifact-provenance.json](evidence/copied-artifact-provenance.json). Older in-chat edits, shell invocations and tool logs are preserved in [SESSION_ARCHIVE.md](../SESSION_ARCHIVE.md) and [COMMANDS_AND_TOOLS.md](../COMMANDS_AND_TOOLS.md). Do not treat an estimated timing or an inferred cause as a fresh test.

## Paths / file layout

Original workspace root: `/home/user/video-project`. Historical source scripts compute `ROOT = Path(__file__).resolve().parents[1]`.

```text
video-project/
  README.md                       # existing remote index; untouched by archive task
  assets/raw.mp4                  # actual input, 640x360
  assets/fonts/                   # downloaded Google Fonts and OFL licenses
  assets/style-reference.mp4      # sports reference, analysis only
  assets/style-reference-v2.mp4   # editorial reference, analysis only
  analysis/transcript.json
  analysis/raw-audio.wav          # mono 16kHz ASR / waveform input
  analysis/voice-normalized.wav   # historical generated stereo float WAV
  analysis/scene-plan*.md
  analysis/*-qc.json              # historical checks; schemas vary slightly
  analysis/*delivery.json         # historical REST uploads
  source/transcribe.py
  source/audio.py
  source/render.py
  source/audio_editorial_v2.py
  source/render_editorial_v2.py
  source/audio_morph_v3.py
  source/render_morph_v3.py
  edits/voice-agents-9x16/
  edits/voice-agents-editorial-v2/
  edits/voice-agents-morph-v3/
```

Archive-local source snapshot uses the same relative structure for the needed input/code/fonts/transcript/caption files. It deliberately excludes full third-party reference binaries, final video duplication and generated intermediate WAV/MP4 files.

## Historical cache locations

- V2: `/home/user/.cache/video-project-editorial-v2/`.
- V3: `/home/user/.cache/video-project-v3/`.
- V3's downloaded 14 s gallery reference was also in the V3 cache.

These absolute paths are present in the exact source, not secretly portable. They are absent now. Before an authorized reproduction on another host, select a writable cache location and parameterize/patch it in a working copy, preserving the archived source. Do not run old commands expecting background processes, package installs, model caches or shell exports to have survived.

## Dependencies

Direct render/audio imports: Python 3, Pillow, NumPy, OpenCV (`cv2`), SciPy, SoundFile, `imageio-ffmpeg`. Acquisition/audit: Requests. Optional transcription: `faster-whisper` and its model/dependencies. Optional PDF extraction: PyMuPDF. The historic YouTube attempt used yt-dlp and the available Node runtime.

Known host at archive inspection: Python 3.13.16, Node 20.20.2, Git 2.47.3, Linux, two CPU cores. Fresh installed/missing package observations are in [environment-observed-now.json](evidence/environment-observed-now.json). No validated historical version lock was captured. [Requirements example](source-snapshot/requirements-reproduction.txt) lists imports, not guaranteed compatible/pinned builds. Installing packages is future work requiring task-appropriate authorization.

The preserved validator itself needs Python 3, PyYAML, and Git for local state checks; it uses only AST parsing for source syntax, not imports or renders. Media metadata/decode checks use the currently available OpenCV and are reported separately.

## Source timing

- Raw video: H.264 Main, 640 × 360, limited-range BT.709, 29.97002997 fps, 620 frames, video duration about 20.6873 s.
- Raw container/audio: about 20.7354 s; AAC LC 44.1 kHz stereo at 128 kbit/s.
- Actual cut from wide view to two close-up halves: scene detection `pts_time:4.9049`.
- ASR model: `base.en`, CPU, int8, two threads, beam size 5, word timestamps, no VAD, previous-text conditioning.
- Retained transcript segment spans: 0–4.50; 4.94–9.54; 9.54–13.68; 13.68–17.90; 17.90–20.42.
- Key words: startups 1.58–1.84; years 3.24–3.52; international 4.12–4.50; effort 6.70–6.90; early 8.44–8.74; invested 11.04–11.26; product 13.68–13.84; market 14.00–14.18; people 15.52–16.00; businesses 16.60–17.04; developers 17.38–17.90; governments 18.34–18.66; voice 19.74–20.02; agents 20.02–20.42.

The saved ASR transcript and the earlier YouTube textual transcript differ in a filler (“very”). A correction needs raw-audio review; do not silently rewrite history.

## Graphics and type

V1: Barlow Condensed Black Italic / SemiBold; Barlow Medium; a dark canvas, red `(255,63,75)` to lime `(207,255,70)` progression, emphasis captions, source crops and original diagrams. Added real-time listener cutaway at 11.98–12.54 s. Original source frame preserved; no face replacement.

V2: Instrument Serif regular/italic plus variable Inter, black/orange `(251,73,8)`/cream. Independent section designs connected by short editorial reveals. Grid-backed speech text is frame-driven; circular insert contains the actual two-person source strip with black letterboxing, not warped faces. Product panel says `CONCEPT`.

V3: variable Geist and Geist Mono, paper `(242,241,237)`, ink `(15,16,20)`, cobalt `(66,70,245)`. One rounded container changes bounds/radius/fill through analytic critically damped step responses. Content changes are separately clipped/briefly blurred. Cursor paths are absolute-time functions. Projected globe uses actual trigonometric geometry, not a geocoverage map. Waveforms use the source audio envelope. No unsupported statistics or fabricated app performance are displayed.

Fonts/licenses are copied in the source snapshot; third-party fonts retain their original OFL texts.

## Render and audio commands

Read-only source inspection is safe. Do not run the following unless a new live user request authorizes reproduction.

```bash
# From an explicitly selected working project with the documented relative inputs:
python source/audio.py
python source/render.py --stills
python source/render.py --render
python source/audio_editorial_v2.py
python source/render_editorial_v2.py --stills
python source/render_editorial_v2.py --render
python source/audio_morph_v3.py
python source/render_morph_v3.py --stills
python source/render_morph_v3.py --render
```

V1 visuals: `analysis/visuals.mp4`; audio: `analysis/final-audio.wav`.
V2 visuals/audio: the V2 cache directory. V3 visuals/audio: the V3 cache directory. Mux with the exact pattern in [COMMANDS_AND_TOOLS.md](../COMMANDS_AND_TOOLS.md).

Visual encoding: raw RGB24 frames piped into bundled FFmpeg; libx264, `-preset fast -crf 18 -pix_fmt yuv420p -threads 2`, BT.709 tags, faststart. V2/V3 explicitly apply full-RGB to limited-range BT.709 scale conversion. V1 was encoded without that explicit scale filter; preserve that historical difference rather than claiming identical commands.

Speech processing: `highpass=f=65,loudnorm=I=-16:TP=-1.8:LRA=9`; output normalized float stereo PCM at 48 kHz. Audio script mixes original synthesized sound under the foreground voice; a conservative peak cap is used. Final mux uses AAC 192 kbit/s / 48 kHz, copied H.264 video, faststart, shortest. Original speech timing is unchanged.

## Validation schemas

Historical QC files differ:

- V1 `export-qc.json`: `videoDurationSeconds`, `audioAlignmentLagMilliseconds`, `decodeErrors`.
- V2/V3: `duration`, `voiceTimingOffsetMs`, SHA-256 and `referenceMediaReused:false`.

Input loudness fields in FFmpeg JSON are measurements of the delivered file. `output_*` fields describe what the analysis filter would normalize toward in its null-output pass; they are **not** a second delivered encode. Use `input_i` / `input_tp` to describe actual file loudness.

Alignment used cross-correlation of one-to-four-second source/encoded mono windows with a ±100 ms search. All reports measured lag 0. This is a specific timing check, not proof of human review of every frame/word.

## Git history / safe attachment

Original remote commits are retained in [initial remote state](evidence/initial-remote-state.json). Local Git metadata was missing. Actual metadata-only attachment:

```bash
git init -b main
git remote add origin https://github.com/swathigampa354-ship-it/vertical-video-edits-2026-10-16.git
git config remote.origin.promisor true
git config remote.origin.partialclonefilter blob:none
git -c protocol.version=2 fetch --filter=blob:none --no-tags origin main
git update-ref refs/heads/main refs/remotes/origin/main
git read-tree HEAD
git branch --set-upstream-to=origin/main main
```

This was safe only because there was no existing `.git`/local branch and all remote tracked files matched the workspace. **Do not rerun it blindly on another repository or existing working branch.** `read-tree` was used without `-u` so no worktree checkout occurred. Despite the filtered fetch, subsequent Git operations populated a large promisor blob pack; this is observed behavior, not a guaranteed bandwidth-saving result.

Do not rely on exported credentials or `.git/config` persistence. Re-inspect the remote and restore public remote configuration when legitimately needed. Any optional removal of newly downloaded promisor cache objects must preserve all user files, new archive objects, commit/tree history and connectivity; its actual outcome belongs in the archive verification record, not an assumed cleanup.
