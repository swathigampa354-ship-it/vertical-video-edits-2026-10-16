# Editing-skill test report

This records actual tests, not a claim that a new Markdown file guarantees creative quality. The current test host is Python3.13.16 with the observed direct package versions and FFmpeg7.0.2. No pre-existing source/edit/archive file was intentionally modified.

## 1. Exact successful-result regression

### V2 editorial

Freshly reconstructed the approved original source, fonts, transcript and code in an isolated work directory. Only the two runtime copies' absolute cache assignment changed to a local work cache; no layout, timing, narration or SFX logic changed.

- Full21.37s film rendered/muxed and completely decoded.
- **641 decoded frames compared;640 exactly identical.**
- Mean frame RGB absolute error: **0.0000000050156** (0–255 scale).
- Maximum frame mean error: **0.0000032151**.
- This is effectively identical decoded visual reproduction of the known fixture, not identical container bytes (metadata changed).
- Decoded stereo48kHz audio also matched exactly:2,050,048 float samples, maximum sample difference0.
- [Machine record](tests/evidence/v2-replay.json), [approved-versus-replay contact](tests/evidence/v2-comparison.jpg).

### V3 latest morph style

Freshly replayed the original morph renderer/audio with the same portable cache relocation.

- Full21.37s,1080×1920,60fps graphics.
- **1,282/1,282 decoded frames exactly identical; mean/max RGB error0.**
- Full-file decode passed.
- Decoded stereo48kHz audio also matched exactly:2,050,048 float samples, maximum sample difference0.
- [Machine record](tests/evidence/v3-replay.json), [approved-versus-replay contact](tests/evidence/v3-comparison.jpg).

V1 source/fonts are included and have provenance/syntax checks. A fresh V1 render/recomparison was not run in this skill-creation task; historical completed V1 is not mislabeled as a new regression test.

## 2. New geometry/duration/clock adaptation

A controlled portrait fixture was derived from the original source (source9.54–11.93s, inspected crop202×360, CFR30). The starter generated a **new fingerprint-bound plan**, rebased word times and a3.0s1080×1920/30fps edit. This tests changed aspect, dimensions, duration and clock—not unrelated footage or fresh ASR accuracy.

- 90/90 frames decoded; no essentially all-black frames.
- All-frame text/logo safe-boundary/collision geometry passed.
- Three source-audio alignment windows measured0,−0.0625,−0.0625ms, far below10ms gate.
- Delivered file measured−16.56LUFS and−4.24dBTP for this short excerpt.
- The explicitly synthetic `TEST` mark was composited after scene/footage transforms on an approved solid backing. It is not a real brand and is never a default asset for new user footage.
-[Machine QC](tests/evidence/portrait-qc.json), [placement QC](tests/evidence/portrait-placement.json), [encoded contact](tests/evidence/portrait-encoded-contact.jpg).

Representative encoded frames0,.5,1.08,1.4,1.88,2.45s and native-size frames were inspected with image tools: face/hands remain appropriate, quote no longer includes the next sentence's “So”, typography is legible, connected transitions settle, and the logo stays visible across black/cream/orange. A140ms crossfade contains intentional transient old/new content; the settled frames do not contain that ghosting.

No independent perceptual audio-listening tool pass was performed; audio evidence is full decode, original-source preservation, multi-window alignment and actual loudness/peak analysis. Machine reports intentionally do not pretend a human/vision review was performed automatically. The separate review record states actual scope.

## 3. Negative / invariant tests

Nine negative/invariant tests passed. They cover: changed source hash rejected; old/wrong-source transcript rejected; out-of-safe logo detected; logo/protected-region collision detected; scene gap rejected; logo entering a forbidden boundary later in time detected; quote endpoint excludes next sentence; logo pixels constant through all90 pre-encode frames/background switches; white-on-white logo rejected. [Actual results](tests/evidence/negative-tests.json).

## 4. Mistakes found and fixed before release

- JSON RGB list reached a Pillow caret draw: `TypeError: color must be int or tuple`; converted to tuple.
- Inspector accidentally reported thumbnail dimensions129×230, not actual202×360; copy image before thumbnailing and assert source dimensions.
- Quote range admitted the next sentence's “So”; fixed the endpoint policy and added a content-boundary test.
- Suppressed a caret before any word becomes visible and included its envelope in geometry checks.
- Quoted/folded the YAML description after its colon caused a ScannerError; package metadata is parsed, not merely visually assumed valid.
- Preserved image alpha, backing expansion and fixed word font sizes rather than accidentally shrinking each individual word.

## 5. Portability and remaining verification

The ZIP was extracted into a different absolute directory. From a CWD outside the original project, its packaged inspector/plan validation/stills/render/QC completed with only extracted media/fonts/transcript/code plus explicitly installed host dependencies. Its90-frame result passed the same audio/geometry/black-frame checks. The custom Film subclass import and an example extension frame were checked; an explicit job-font override produced the same expected frame. [Relocation evidence](tests/evidence/relocation-test.json).

The actual encoded contact/native frames were inspected after this run. [Separate visual review](tests/evidence/manual-review.json) records the real scope; machine flags are not falsely flipped. No actual different LLM identity was tested, so filesystem portability must not be misrepresented as an artistic cross-model guarantee.

Release validation parses Agent Skills metadata, local links, Python syntax, copied-asset hashes and ZIP member hashes, checks all221 pre-existing project files and scans for secrets. The ZIP is rebuilt after final evidence/docs; runtime source/font/example hashes are verified against the tested extraction.

Not verified: an unrelated camera/source, all OS/Python versions, fresh Whisper model download/transcription, arbitrary new languages, actual brand approval, moving-object logo tracking, stabilization, HDR/VFR conversion, noncontiguous EDL or subjective equivalence from every different LLM. The skill requires inspection/revision for each new input and cannot guarantee those by assertion.
