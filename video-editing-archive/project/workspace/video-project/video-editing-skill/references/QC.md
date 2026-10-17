# Quality control and release gates

## Gate A — Source/meaning

- Actual media inspected, not assumed from a link or filename.
- Source hash, aspect/orientation/FPS/audio and timing uncertainty recorded.
- Transcript checked for important words/names/numbers and phrase boundaries.
- No invented claims/quotes/brand; source order/speed preserved unless requested otherwise.
- Scene plan bound to this input; no old timestamps or face crops blindly reused.

## Gate B — Stills and placement

- Inspect opening, every settled scene, transitions, source cut±one frame, crop/overlay motion extrema, longest text and ending.
- Faces/mouths/meaningful hands/other speaker and source attribution remain appropriate.
- Captions use stable slots and enough size; no missing-glyph boxes, clipped descenders, dense flash paragraphs or overlapping hierarchy.
- Logo optional: if absent, no fake mark. If present, whole visible mark/backing inside safe/prohibited bounds, contrast/readability/clearspace checked over changing backgrounds, no text/subject collision.
- Full-frame source camera transforms cannot move a screen logo; compositing order is verified.
- Automated all-frame geometry is required for animated crop/logo/text data, but only as truthful as the supplied protected regions.

## Gate C — Machine export

The CLI's `qc` currently checks:

- FFmpeg whole-file decode succeeds.
- OpenCV full frame count,1080×1920 and configured output FPS.
- No unintended essentially all-black frame (threshold: fewer than0.01% gray pixels>3); intentional black intervals need a separately authored review/whitelist, not a blind bypass.
- Placement report passes all output frames.
- Source/encoded mono16kHz cross-correlation in up to three non-silent windows, search±100ms, measured lag≤10ms. All-silent/insufficient data is not a PASS.
- Delivered audio `input_i` within1.5LU of−16; true peak `input_tp`≤−1dBTP. The filter's `output_*` fields describe hypothetical normalization, not measured export values.
- Output SHA-256 recorded.

These tests are for one contiguous source interval. Complex EDLs, changed speed, separate replacement audio, multitrack/multicam require an explicitly correct mapping/test. VFR/HDR handling must be resolved first. The helper does not prove every arbitrary input is supported.

## Gate D — Encoded visual/creative inspection

Decode the finished MP4 and inspect the actual images; don't rely on pre-encode stills. Check moving subject/crop through its interval, transitions for ghosting/missing layers, logo/word visibility at extremes, image distortion, card/radius edges and end hold. Use video tools when available; otherwise inspect a dense frame/contact sequence plus native keyframes and document that scope.

Listen if supported. Otherwise report automated alignment/loudness checks and the absence of an independent perceptual listening pass. Do not claim to have heard audio that tools did not expose.

Compare with the bundled actual references: one intentional focal idea, serif/sans contrast, clean space, connected speech-led motion, original visual explanation, restrained SFX and stable readable overlays. This is not a numerical taste score. Fix a technically valid but aesthetically weak export.

## Regression versus new work

Baseline replay is a stringent test of the **known exact fixture only**. Matching its pixels does not prove generalization. The alternate portrait/duration fixture tests new coordinates/times, subtitle/quote rendering and optional logo safety. It is an excerpt of the same original source, not unrelated-camera footage or proof across all languages/models.

`machinePass:true` intentionally coexists with `manualInspectionComplete:false`. Record a genuine separate `review.json` with exact observations. Never change the flag just to pass a gate.

## Never deliver on these claims alone

- “Command exited0.”
- “The package installed / a plugin exists.”
- “The last agent said it was good.”
- “The source is 360p but the export is1080p, so it is native1080p.”
- “A logo box stayed in bounds, so all real brand details must be readable.”
- “One regression matched, so this different unseen clip has identical quality.”

Failed checks mean revise or report a concrete limitation; they are not permission to hide errors or silently drop branding/speech.
