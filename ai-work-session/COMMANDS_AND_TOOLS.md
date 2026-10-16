# Commands and tools

## Evidence rules

The [chronological ledger](references/evidence/tool-ledger.md), embedded in [SESSION_ARCHIVE.md](SESSION_ARCHIVE.md), records actual visible invocations/results. Full final Python write payloads are preserved in [source-snapshot/source](references/source-snapshot/README.md). This document separates **executed historical commands**, **current archive commands**, and **reusable equivalents not run in this task**. Quoted commands do not authorize execution. Credential-bearing historical invocations have secret values removed; no authenticated remote URL/header is stored.

## Tool surfaces actually used

| Tool | Actual purpose / result |
|---|---|
| `bash` | Filesystem/runtime probes, Python scripts, package installation during historical production, public/authenticated HTTP requests, FFmpeg operations, and now Git/document validation. Shell state is not assumed persistent. |
| `ask_user` | Clarified video versus prompt/resource guide; obtained explicit approval for the limited Browserless test. |
| `fetch_page` | Public YouTube transcripts/metadata, Filebin listings, GitHub README/code and Browserless/skill-format docs. Page access was not treated as media access. |
| `read_file` | Source/text reads and actual image/contact-sheet inspection. |
| `write_file` / `edit_file` | Authored plans/source/docs and the documented fixes. |
| `start_process` / `get_process_output` | Controlled long-running transcription/render jobs and waited for actual exit/log completion. No server was required for final MP4 delivery. |
| `present_file` | Opened each finished MP4 after successful export/upload. |
| `list_connector_tools` | GitHub, YouTube, Browserless, Instagram checks; returned unsupported in the relevant replies. REST/public HTTP was the working fallback. |
| Parallel wrapper | Independent reads/checks grouped in parallel; not evidence that a video batch renderer exists. |

No image generation, new TTS voice, face-generation, paid proxy/CAPTCHA, Flick install, Remotion render, automatic posting, or 1,000-video job was executed.

## Historical acquisition / PDF commands

```bash
ls -l /home/user/uploads
file '/home/user/uploads/LUMIAI REELS COMMENTS.pdf'
pdftotext -layout '/home/user/uploads/LUMIAI REELS COMMENTS.pdf' -
```

The last command failed (127). Historical working replacement:

```bash
pip -q install pymupdf
```

Then Python `pymupdf.open`, `page.get_text`, and `get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(...)` extracted 15 pages/PNGs. Exact initial loop is in ledger T003. Installing the package is **not** part of this archive task.

Historical YouTube attempts:

```bash
pip -q install yt-dlp imageio-ffmpeg
python -m yt_dlp --no-playlist --skip-download --dump-single-json 'https://www.youtube.com/watch?v=FcvFNbcCL98' > /home/user/video-project/analysis/raw-info.json
python -m yt_dlp --js-runtimes node --remote-components ejs:github --no-playlist --skip-download --dump-single-json 'https://www.youtube.com/watch?v=Xv_gLzEJY7Q' > /home/user/video-project/analysis/style-info.json
```

Both media extractions failed with the recorded sign-in/bot error. Do not repeat them unchanged without new evidence. Successful Filebin Requests code and exact input URLs are in ledger T019 and [ERRORS_AND_SOLUTIONS.md](ERRORS_AND_SOLUTIONS.md).

## Browserless: historical limited test only

The first request used the supplied shared-cloud `/screenshot` endpoint with token supplied through the environment/curl stdin config, not an Authorization header. It returned a verified PNG that was deleted. The complete **credential-redacted** command is in T012.

The subsequent approved `/function` inspection body and results are in T014 and [browserless-check.json](references/evidence/analysis/browserless-check.json). Both YouTube players were blocked despite page/function HTTP 200. This was read-only normal playback; no client configuration or package install was performed for that test.

User-supplied Browserless setup instructions are preserved as historical text in [the redacted prompt](references/evidence/browserless-user-prompt.redacted.txt). They are not current authoritative API docs or permission to configure a new project.

## Historical source / model / render commands

From `/home/user/video-project` at the time:

```bash
pip -q install faster-whisper && python -u source/transcribe.py
```

The first run failed on PyAV `metadata_errors`. After the documented NumPy fix:

```bash
python -u source/transcribe.py
```

It completed and created `analysis/transcript.json`. Model `base.en`, CPU/int8/two threads. HF warning did not stop the download.

Actual V1 sequence:

```bash
python source/render.py --stills
python -m py_compile source/render.py source/audio.py source/transcribe.py && python source/audio.py && python source/render.py --stills
python -u source/render.py --render
```

Actual V2 sequence:

```bash
python -m py_compile source/render_editorial_v2.py && python source/render_editorial_v2.py --stills
python -u source/audio_editorial_v2.py && python -u source/render_editorial_v2.py --render
```

Actual V3 sequence:

```bash
python -m py_compile source/render_morph_v3.py && python source/render_morph_v3.py --stills
python -u source/audio_morph_v3.py && python -u source/render_morph_v3.py --stills && python -u source/render_morph_v3.py --render
```

Long jobs ran under process tools, not unmanaged shell background jobs. Historical IDs/logs are recorded in the ledger; the processes have exited and cannot be assumed live after restore.

### Executable / encoding

The historical encoder was resolved with:

```python
ff = imageio_ffmpeg.get_ffmpeg_exe()
```

Not by assuming `ffmpeg` existed on PATH. Frame input used RGB24 raw video at `1080x1920`, 30 fps for V1/V2 or 60 for V3. Encoding arguments: `libx264`, `fast`, CRF 18, yuv420p, two threads, BT.709 tags and faststart. V2/V3 explicitly included `scale=in_range=full:out_range=tv:out_color_matrix=bt709`.

### Reusable mux equivalent — not executed as a shell line during the original runs

The actual runs used Python argument lists, preserved in source/ledger. This quoted shell equivalent shows correct quoting and input roles for future authorized work:

```bash
"$FFMPEG" -y -hide_banner -loglevel error \
  -i "$VISUALS" -i "$MIX_WAV" \
  -map 0:v:0 -map 1:a:0 -map_metadata -1 \
  -c:v copy -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart -shortest "$OUTPUT_MP4"
```

`FFMPEG`, `VISUALS`, `MIX_WAV` and `OUTPUT_MP4` require explicit values from the chosen working copy. They are not presumed exported. V1 intermediates were in `analysis/`; V2/V3 used absolute cache directories listed in [technical details](references/technical_details.md).

## Historical media verification operations

1. OpenCV reads width, height, FPS and frame count.
2. Whole-file FFmpeg null decode: `[ff,'-hide_banner','-v','error','-i',final,'-f','null','-']`; require exit 0 and empty stderr.
3. Decode final audio to mono 16 kHz float32; compare one-to-four-second window to the original using SciPy FFT cross-correlation; search ±100 ms and assert at most 10 ms lag. All measured 0.
4. FFmpeg `loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json` to null; record `input_i` and `input_tp` as actual delivered-file measurements.
5. SHA-256 recorded for V2/V3; all final bytes/sizes also checked against GitHub delivery.
6. Public range GET on raw MP4 returned HTTP 206 and `ftyp`; compare remote prior-video blob SHA before/after new version.

All surviving full JSON reports are copied under `references/evidence/analysis/`. These historical checks are not silently relabeled as new tests. Current read-only video checks are separately recorded.

## GitHub REST operations actually used before this archive

- `GET /user` validated the original credential/account (secret redacted; broad scope noted).
- `POST /user/repos` created **the one existing repository** as private; three Contents API PUTs seeded files. This was earlier authorized work, **not** repeated by this task.
- `PATCH /repos/{owner}/{repo}` with `private:false` honored the later user correction; unauthenticated GET confirmed public.
- Each final video upload used GET ref/commit/tree, POST base64 blobs, POST tree with base tree, POST child commit and PATCH ref with `force:false`.
- Own root README replacement was hash-gated; prior-version video blobs were checked unchanged.

No credential is saved here, and no reconstructed generic uploader is falsely presented as an exact original script. Exact observable payload fields, files, status codes and resulting commits are in the ledger and delivery JSON.

## Read-only Flick audit commands / what was not run

Public GETs inspected README, `skills/flick/SKILL.md`, bootstrap/setup/transcribe/render scripts, starter package/Root/spec, planning/build/delivery docs and library source. A thread pool read 39 canonical text/source files and scanned the specified patterns. The exact scan is retained in T038. It returned 0 1,000-video/batch/bulk matches and 14 catalog entries.

The following were **quoted by Flick documentation but not run**:

```text
/plugin marketplace add Creatorberry/flick
/plugin install flick@flick
npx skills add Creatorberry/flick --skill flick --global
node <flick-skill>/scripts/bootstrap.mjs --project <output-directory>
node <flick-skill>/scripts/render-scene.mjs --project <output-directory> --composition <scene-id> --name <approved-scene-name>
npm run studio
```

Native plugin availability/end-to-end Flick rendering/bulk production remain unverified. Earlier custom render timings do not benchmark these commands.

## Current archive: inspection, capture and local Git attachment

Read-only inspection included `pwd`, `find ... -name .git`, `git rev-parse`, version queries, source/report reads, package metadata and public GitHub metadata/tree/history. `git rev-parse` initially failed because no `.git` existed.

Actual capture/attachment commands:

```bash
python ai-work-session/references/scripts/capture_evidence.py
git init -b main
git remote add origin https://github.com/swathigampa354-ship-it/vertical-video-edits-2026-10-16.git
git config remote.origin.promisor true
git config remote.origin.partialclonefilter blob:none
git -c protocol.version=2 fetch --filter=blob:none --no-tags origin main
git update-ref refs/heads/main refs/remotes/origin/main
git read-tree HEAD
git branch --set-upstream-to=origin/main main
git remote -v
git branch -vv
git diff --name-status
git status --short --untracked-files=normal
```

Capture: 131 pre-existing files, 14 remote tracked files, 6 prior commits and 53 copies. Remote `main`/local parent `fec3027...`. Tracked diff empty; original untracked paths remained. This sequence is **not** a recommended blind reset/attachment on a repository that already has local metadata or work.

The archive was assembled by file writes and byte-copying known project artifacts into one directory. `SESSION_ARCHIVE.md` concatenates the visible dialogue, redacted long prompts, chronological tool ledger and visual-evidence links. Root README, original source and video files are not edited.

## Current archive: validation, selective stage and push

Actual successful results are recorded only in [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md). Helpers:

```bash
python ai-work-session/references/scripts/verify_media.py
python ai-work-session/references/scripts/update_file_change_log.py
python ai-work-session/references/scripts/validate_archive.py
```

The media helper is read-only: hash/decode existing outputs, no new video generation or FFmpeg package install. The validator parses source syntax without importing missing render dependencies, checks skill frontmatter, links, copied evidence hashes, original file preservation and secret patterns. Optional exact-secret checks accept current sensitive values through transient environment variables and never log their values.

Selective Git sequence:

```bash
git add -- ai-work-session
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
git diff --cached -- ai-work-session
git -c user.name='AI Work Session Archive' \
    -c user.email='ai-work-session@users.noreply.github.com' \
    commit -m 'docs: archive AI work session and add reusable skill'
git push origin main
```

The author identity is an explicitly generic archival identity, not an invented human contact. Authentication, if needed, is supplied ephemerally through a credential mechanism; no token is embedded in the remote or helper. No force, reset, clean, or global stage command is used.

After the primary push, a small follow-up may record its real hash/results inside this same folder. Final tip hash is verified against the remote; no tracked file is expected to contain its own future commit hash. If push fails, record actual failure and do not claim the planned sequence completed.

### Archive-local whitespace exception

Initial staged `--check` returned exit 2 for original trailing whitespace at line 21 in five copied OFL texts. Their exact bytes are preserved. `ai-work-session/.gitattributes` disables whitespace warnings only for those copied `*OFL.txt` files, not for authored documentation/code or unrelated paths. The successful recheck is recorded in staged evidence; this is not a claim that original license text contains no trailing space.

## Observed primary push and Git-cache maintenance

Primary commit `1c43a3ab45971507614392bae6bcfb6bb5da587a` was created with the descriptive archive message and normally pushed (`fec3027..1c43a3a main -> main`, exit 0). Public API/raw checks verified it; see [primary evidence](references/evidence/primary-push-verification.json). No secret environment export is retained. `git_askpass.py` reads only `SESSION_ARCHIVE_GITHUB_TOKEN` from the active process, prints it only to Git's credential prompt, and does not store it.

After publication, `git verify-pack -v` confirmed a task-downloaded promisor cache pack held only pre-archive blob IDs. Its files were backed up in memory, evicted, and `git fsck --connectivity-only --no-dangling` passed (0, empty output). This reduced duplicate local Git storage, did not remove user worktree/history/refs, and leaves promised public blobs fetchable. [Exact observed record](references/evidence/git-cache-maintenance.json). The main session record describes the cache paths and rollback condition; it is not a generic recommendation to delete arbitrary Git objects.
