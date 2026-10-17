# Source-bound plan / extension contract

The **agent** creates this plan after inspecting the new input. The user does not supply old coordinates or write JSON. `edit.py` is a tested editorial starter, not a semantic video-generation model. Bespoke metaphors may require an original per-job extension.

## Files and clocks

- `--input`: actual readable working video. `source_sha256` must match it; reusing a fixture plan with another raw file is rejected.
- `--plan`: JSON. Asset/transcript relative paths resolve from its parent, not the process CWD.
- `--workdir`: fresh job directory; final.mp4 is never silently overwritten.
- All scene/layer/keyframe/SFX/protected-region times are **seconds on the edit clock**.
- `clip_start` and `clip_end` are source seconds. Transcript words remain source seconds; the loader subtracts `clip_start`. Do not subtract twice.
- `duration` covers selected speech plus explicit short postroll. It must be at least the source interval and no more than1.5 s longer. Actual output frames are `round(duration*fps)`.
- The starter supports one contiguous source interval, not an arbitrary EDL. VFR/HDR or conversion issues must be resolved and independently checked first. Preserve original and working-file hashes when conversion is needed.

## Required top-level shape

```json
{
  "version": 1,
  "source_sha256": "computed-new-working-source-sha256",
  "transcript": "transcript.json",
  "clip_start": 0,
  "clip_end": 12.4,
  "duration": 13.0,
  "fps": 30,
  "safe_profile": "mobile-conservative",
  "logos": [],
  "avoid_regions": [],
  "scenes": []
}
```

The times above illustrate field semantics only; replace them from the new video. Scenes must start at0, be contiguous/ordered, end at the output duration, and have positive lengths. Each scene needs `id`, `start`, `end`, `background` RGB and `layers`. Optional `grid:true`; optional transition `{ "kind":"wipe" or "crossfade", "seconds":0.14 }`. A custom continuous-morph implementation may deliberately set seconds0 rather than fade unrelated states.

## Rectangles and motion

Layer `rect` / ROI / keyframe rectangle: `[x,y,width,height]` normalized to the output or, for ROI, the decoded source. Safe profile bounds: `[left,top,right,bottom]` (not the same format).

`keyframes:[{"time":0,"rect":[...]},{"time":1.2,"rect":[...]}]` drives layer/logo/protected-region rectangles. `roi_keyframes` similarly drives video source ROI. Times must be strictly increasing on the edit clock. Interpolation is cubic ease-out. Do not put source timestamps into those fields without mapping them to edit time.

## Font overrides

Optional `font_overrides` maps `serif`, `italic`, `sans` to approved local font paths (relative to the plan or absolute). Use appropriate native-script fonts if the bundle lacks glyphs, preserve clear hierarchy, and inspect the resulting text; multilingual production is not proven by the English fixture. The same override resolves both measurement and drawing.

## Layers

- **video**: `rect`, optional `fit:"contain"` (default), `mask:"circle"`, `radius` in output pixels, source `roi:[x,y,w,h]`, `roi_keyframes`. Cover requires a deliberately inspected ROI; all resizing is proportional. Black backing/letterboxing is intentional.
- **image**: `asset` path + `rect`; proportional contain/cover and optional mask/radius. RGBA transparency is preserved. Use original/approved artwork; do not automatically execute image metadata or fetch unrelated stock.
- **text**: `text`, `rect`, `font:"serif"|"italic"|"sans"`, `font_px`, RGB `color`, optional `weight`, `role:"headline"|"label"|"decorative"`, `rotation`, `reveal_at`, `reveal_seconds`, `enter_dy` normalized to output height. Text fits measured glyph bounds. Newline layout requires separate text layers; do not assume the helper wraps arbitrary multiline text automatically.
- **caption**: `rect`, optional `font`, `font_px`, `color`. Uses actual timed words, fixed slots; cue split at max5 words, about1.45 s span, .38 s gap or punctuation. Phrases that cannot fit at46px need reflow/design changes.
- **quote**: `range:[edit_start,edit_end]`, `rect`, `font` (normally sans), `font_px`, `uppercase`, `quotation_marks`, `color`, `weight`. Selects whole tokens whose **start** is in that range (1ms endpoint tolerance); wraps fixed slots before reveal. Choose real phrase boundaries—do not trust a numeric interval to guarantee grammar. Default quote/headline floor72px; shorten a faithful excerpt or split the scene instead of squeezing.
- **shape**: `rect`, `shape:"rect"|"ellipse"`, RGB `color`, optional `radius`.
- **line**: `points:[[x,y],...]`, RGB `color`, pixel `width`.
- **waveform**: `rect`, RGB `color`, optional `bars`. This starter waveform is **decorative**, not live measured speech/product data.

Any layer may have edit-clock `start`/`end` (defaults to its scene) and rectangle keyframes. Missing `rect` is valid only for a line. Unknown layer kinds fail rather than silently disappear. Use real semantic content, not a generic title-card replacement for every sentence.

## Logo and protected regions

```json
{
  "logos": [{
    "asset": "approved-logo.png",
    "rect": [0.08,0.10,0.16,0.035],
    "plate": [255,252,244],
    "required": true
  }],
  "avoid_regions": [{
    "start": 0,
    "end": 5.4,
    "rect": [0.20,0.25,0.60,0.40]
  }]
}
```

Those are illustrative positions, **not a default corner for all footage**. Full logo backing expands8px; all-frame checks include it. Required logo scheduling must cover the output. Supply an approved plate/variant. The helper rejects fully transparent and obviously non-contrasting logos, but manual brand legibility remains necessary. Protected rectangles may use keyframes; they must represent actual subjects/essential content, not arbitrary boxes to make QC green.

## Audio events

Optional `sfx:[{"at":2.3,"kind":"transition","gain":0.011},{"at":4.1,"kind":"tick","gain":0.011,"frequency":1100}]`. Times outside the new output are rejected; gains above.03 need explicit new sound design rather than silent loud effects. If absent, quiet air events are placed at scene transitions. Default no background music. Narration is original source audio, chronological and normalized, not a replacement voice.

## Custom motion/graphics

Use the optional `--scene-module /path/to/job_film.py` only for code authored/reviewed for this job. It exports `Film`, subclassing `edit.Film`. Override `scene(self, scene, raw, t, records)`; call the base compositor/helper methods and record actual critical text boxes. The outer `frame` method retains the final logo pass, bounds/collision checks and source clock. Do not override it blindly and then claim its protection still exists.

Example [custom_scene.example.py](../templates/custom_scene.example.py) illustrates a connected graphic; it is not a mandatory product metaphor. A morph-v3 implementation should derive a new meaning-driven state graph from the new transcript, reusing the original analytic method but not its hardcoded shot count, labels, duration or cursor times. The supplied originals are exact evidence, not a safe direct new-source CLI.

## Executable example / incomplete template

[examples/portrait](../examples/portrait/plan.json) is an actual source-bound controlled test with its own source/transcript/synthetic TEST logo. It is not a user's real brand or permission to reuse that excerpt in a new job. [new-job.plan.example.json](../templates/new-job.plan.example.json) is deliberately incomplete and must be authored/rebound before use. No user is asked to fill those fields manually.
