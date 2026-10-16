# Decision log

Evidence categories: **V** = observed tool/file/Git result; **D** = documented user/assistant decision; **I** = inference, explicitly not an observed root cause; **E** = estimate; **U** = unresolved.

## D01 — Clarify the ambiguous original attachment

- Problem: user said “I want this” and attached a PDF containing both AI resources and a video brief.
- Evidence: PDF text extraction revealed resource lists plus a detailed VybeSchool motion-design specification.
- Options offered: motion-graphics video; ready-to-use video prompt; organized AI resource guide.
- Decision: follow the user-selected **video** option. **D/V**
- Trade-off: do not generate unrelated newsletters/resources or assume the long PDF itself is a video asset.
- Outcome: assistant asked for actual source/reference/voiceover assets; user supplied 9:16 and source/style links.

## D02 — Keep source audio as master timeline

- Evidence: source link exposed a 21-second spoken interview clip; later raw MP4 contained the corresponding original audio.
- Decision: no separate generated narrator or script required; preserve source speech order/timing and map original graphics to it. **D/V**
- Trade-off: fillers remain audible; emphasis text may condense them. Separate captions preserve the automatic full transcript rather than implying all visual text is verbatim subtitles.
- Risk: ASR is not a human-verified transcript. See remaining issues in [ERRORS_AND_SOLUTIONS.md](ERRORS_AND_SOLUTIONS.md).

## D03 — Stop unchanged YouTube attempts after access evidence

- Tested: page retrieval/transcripts; yt-dlp metadata extraction; a modified runtime/component attempt; normal Browserless browser playback.
- Observed: transcripts/page HTML accessible, but actual media requests reported login/bot confirmation and zero playable formats. Browserless account test succeeded independently. **V**
- Decision: request accessible raw/reference MP4s instead of treating API-key availability as playback permission. **D**
- Rejected: claim that page HTTP 200 means video playback; pretend footage was downloaded; consume extra paid proxy/CAPTCHA features not approved.
- Outcome: user supplied Filebin files; download succeeded after normal warning/cookie handling.

## D04 — Repository visibility follows the user's correction

- Initial choice: create one private video-storage repository as a privacy-conscious default; authorized GitHub token was used transiently. **D/V**
- User correction: “Keep the repo public.”
- Decision: change **that same** repository to public, with file contents unchanged; confirm unauthenticated access. **D/V**
- Current effect: all later edits and this archive target this existing public repository. Do not create another repository.
- Risk: all committed content is public; shared credentials must never be copied into documentation.

## D05 — Use latest actual style files, not an unrelated brand identity

- Evidence: initial PDF described clean white VybeSchool branding; no logo/colors were supplied. User later explicitly supplied an IShowSpeed reference, then a different editorial reference, then a gallery.
- Decision: retain format/audio/storytelling constraints, but follow each latest requested style for a separate version. Do not paste VybeSchool, Cartesia, reference watermarks, or invented speaker/company identities into the raw clip. **D**
- Outcome: V1 sports energy; V2 editorial; V3 single-shape UI motion. Each version has its own folder. **V**

## D06 — Filebin download should validate actual media

- Failure: a 200 response was HTML, not MP4.
- Evidence: warning page set a `verified` cookie and linked “Proceed to download.”
- Decision: keep one `requests.Session`, continue normally through the service warning, inspect content type and `ftyp` signature before saving. **D/V**
- Trade-off: one extra read, no authentication workaround. A 200 response alone is insufficient evidence.

## D07 — Use code-rendered original graphics and original sounds

- Evidence: raw footage is low-resolution, and the brief forbids copying reference scenes/footage or substituting generic AI imagery.
- Decision: author typography, diagrams, masks, source reframing, UI concepts and synthesized SFX/quiet beats with deterministic Python code. **D/V**
- Tools: Pillow, OpenCV, NumPy, SciPy, SoundFile, FFmpeg. No image-generation model, new voice audition, video-generation API, reference soundtrack or face regeneration was used.
- Trade-off: source footage detail remains 360p; new type/graphics are native 1080 × 1920.

## D08 — Bypass the observed Faster Whisper decoder incompatibility

- Failure: `TypeError: open() got an unexpected keyword argument 'metadata_errors'` when passing a WAV path to Faster Whisper/PyAV.
- Evidence: final source and subsequent successful transcription logs.
- Decision: load mono 16 kHz float32 samples with SoundFile and pass the NumPy array to `model.transcribe`. **D/V**
- Root-cause wording: the traceback proves an API incompatibility on this code path; exact historical package versions and upstream cause were not captured. **I/U**
- Outcome: base.en CPU/int8 transcription completed and wrote the timestamped transcript.

## D09 — Render stills before complete films

- Evidence: V1 draft frame revealed a small opening label overlapping the large GO type. Later stills revealed vertical audience labels/footer needed safer margins.
- Decision: inspect representative stills/contact sheets, change layout/motion, then perform final encode. **D/V**
- Concrete fixes: remove the V1 redundant label; move globe/path and product cards through connected transitions; add a synchronized listener cutaway during a pause; reposition/resize V2 vertical words/footer; improve V3 final audience labels and cursor exit.
- Trade-off: screenshots validate layout, not final sound or every animated frame. Full-file decode and timing checks supplement them.

## D10 — Preserve earlier versions

- User asked to “try” additional styles, not replace the approved edit.
- Decision: separate output folders: `voice-agents-9x16`, `voice-agents-editorial-v2`, `voice-agents-morph-v3`. **D**
- Verification: REST upload transactions preserved prior video blob hashes; fresh pre-archive inspection found all 14 remote files identical to local copies. **V**

## D11 — Choose a concrete gallery direction for V3

- Evidence: researched the requested `yihui-dev/awesome-opus5-5-videos` gallery, prompts, posters, and the public 14-second @twoclipping one-shape video.
- Options encountered: general SaaS launch films; dark developer-tool effects; kinetic spoken-word architecture; continuous UI morphing.
- Decision: warm off-white/black/cobalt single-container motion; analytic critically damped responses; cursor interactions; 60 fps new graphics. Source voice, not the examples' music/claims/brands, drives timing. **D/V**
- Trade-off: deliberately more motion-graphics-led and less continuously face-dominant than V2. It is not a copied app demo or an assertion of actual product features.

## D12 — Distinguish Flick feasibility from a real benchmark

- User explicitly requested verification only, no videos and no 1,000-video run.
- Evidence: 39 canonical text/source files inspected, 14 reusable patterns, one-composition render helper, approval gates, independent scene outputs; no batch/bulk/1,000-video textual claim found.
- Decision: report repeated/custom-automated use as technically plausible, not a verified one-prompt 1,000-polished-reel feature. Clearly state Flick was not installed/run and earlier clips used custom code. **D/V**
- Estimates: setup 10–30 min; a new 20–30 s custom clip 15–45 min after setup; approved-template variants 2–10 min each including basic checks. These were **E**, not measured Flick timings.
- Comparison: V3's own visual render was approximately 45 s; 1,000 such serial renders would be approximately 12.5 h of render time only. This arithmetic is not an end-to-end/Flick throughput test.

## D13 — Archive in one folder and do not republish unnecessary binaries

- User's current task: all documentation/skill deliverables inside root `ai-work-session/`, same existing repository; preserve all existing work.
- Decision: keep the required Markdown files, portable skill, read-only validation/capture helpers, exact source snapshots, raw input, original PDF, fonts/licenses, metadata and representative visual evidence together. Link existing final videos rather than duplicate them. **D**
- Full third-party reference MP4s and derived intermediates remain inventoried, not republished. This reduces unnecessary redistribution/size without falsely claiming their bytes are archived.
- Redact all three shared credential values and authenticated request details. Keep only technically useful public repository/source identifiers.

## D14 — Portable skill format without native installation assumptions

- Evidence: current Agent Skills specification requires YAML `name` and `description`, with name matching directory; recommends a short entry point plus references.
- Decision: `name: ai-work-session`, descriptive metadata and documented prerequisites; manual loading through the existing file. No unrelated client configuration or duplicate skill directory. **D/V**
- Trade-off: syntactic compatibility and explicit invocation are verified; automatic discovery in any particular client is not.

## D15 — Attach Git without overwriting workspace files

- Evidence: local workspace had no Git metadata, remote history existed and all remote files matched local blobs, many valuable local source/analysis files were untracked.
- Options: clone elsewhere (additional checkout), checkout into the existing folder (risks overwriting untracked files), or attach remote metadata/index only.
- Decision: initialize local metadata, add the existing public remote, filtered fetch, initialize the unborn `main` ref from `origin/main`, and `git read-tree HEAD` **without `-u`**. No worktree checkout, reset, clean, force push, or user-file deletion. **D/V**
- Outcome: `main` tracks `origin/main`; tracked diff empty; pre-existing untracked paths remain. New archive files alone are staged.

## D16 — Record verification without self-referential commit claims

- Problem: a tracked file cannot contain the hash of the exact commit that introduces itself without a circular dependency.
- Decision: validate and push the primary archive, then add a small evidence follow-up recording the actual primary commit/push result. The final tip hash is verified remotely and reported in the final response/Git history, not guessed inside its own commit. **D**
- Require fresh evidence for each success claim. If push fails, document the blocker and do not label it successful.
