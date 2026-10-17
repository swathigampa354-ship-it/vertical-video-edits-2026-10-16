# Complete input → output workflow

The future agent executes this sequence, derives the new decisions and corrects its own render. The user supplies raw footage and any genuinely required assets, not a scene plan or old conversation.

## 0. Intake / reuse defaults

Read the complete skill and required references. Default editorial-v2/9:16/1080×1920/30fps/original speech/no background music/no invented brand. “Latest/morph-v3” selects the documented60fps profile. Ask only for an inaccessible raw file, explicitly required missing asset, or an essential scope contradiction (e.g. whether a long lecture may be cut). Do not ask the whole original creative brief again.

Record a new job slug, input filename/hash and requested overrides. Use a new revision directory; never overwrite earlier deliveries. Obtain authorized media normally; failed YouTube playback is not a reason to harvest cookies or use another key.

## 1. Inspect actual source

Run source inspection and use image tools to view `source-contact.jpg`; inspect important shot boundaries at native size. Read stream information and candidate cuts. Check speech/audio, decoded orientation, aspect, source frame rate/count, rotation, HDR, sampling uncertainty, focus/detail, noise, motion and embedded watermarks. Determine which people/objects must remain visible.

The original job had a wide shot followed by a two-person split at4.9049 s; no source-section search was used and no added logo existed. New footage needs new observations. Never copy the old min619 frame cap,20.665 s read cap, 21.37 s duration or old quote rows.

If VFR/HDR/rotation/SAR is uncertain, resolve a proper working decode/conversion before indexing source frames. Preserve A/V timestamps together and recheck sync. Do not independently zero streams or assume a phone video's reported average FPS is a precise clock. The supplied inspector samples VFR for at most1000 frames and flags suspected HDR; it does not perform colour-managed tonemapping or prove whole-file CFR.

## 2. Speech map

Extract/review word times or use the supplied trustworthy transcript. Optional ASR helper defaults to automatic language detection and passes NumPy audio to avoid the recorded filename/PyAV error. A low-confidence word, named entity or number needs source review. New language needs font coverage, not tofu boxes.

For short source, keep the whole speech. For an allowed long-source selection, choose a self-contained hook→statement→proof/payoff rather than fragments that change meaning. Snap boundaries thoughtfully; do not cut a word or leave a frozen speaking mouth. Keep an explicit source→edit mapping. The starter handles **one contiguous source interval**; noncontiguous editing needs an authored EDL/renderer and its own mapping/QC, not dishonest reuse of the starter's simple correlation.

## 3. New scene design

Author `plan.json` plus a short beat explanation. Scene boundaries are contiguous. Each visual explains its actual speech anchor. Example pattern—not mandatory content:

- opening hook + actual interview strip;
- oversized true keyword/contrast;
- return to the real speaker on a real source cut;
- progressive faithful quote + live circular insert;
- original concept diagram;
- audience/role beat only if such a list is spoken;
- legible payoff and brief end hold.

If using morph-v3, form a new continuous state graph rather than these editorial cuts. Derive shape bounds, labels, cursor actions and sound events from the new speech. The agent can implement a per-job subclass/module using the preserved source as a reference. A batch of random title cards is not this quality standard.

Write proof/reference notes for quotation text, numerical claims and simulation labels. No reference branding, invented stats, unknown speaker name or fictional “live” product readout. A decorative waveform is not measured product data.

## 4. Framing, type, overlay map

Use actual decoded aspect and protected subject regions. `contain` preserves context; cover requires inspected ROI and motion keyframes. Use the new layout safe profile, not historical right-edge coordinates. Reflow quote/caption text at measured font widths; keep hierarchy and negative space. Fixed caption slots prevent recenter jitter.

Omit absent optional branding. If provided, inspect the real logo, maintain ratio/clearspace, choose safe screen coordinates across all shots and add an approved backing. Composite it last and check all frames. See [PLACEMENT](PLACEMENT.md).

## 5. Build and still-review

The starter supports video/image panels, circle/rounded masks, text, word captions, progressive quotes, shapes, lines and decorative waveforms. Frame-driven rect/crop keyframes and short wipes/crossfades are provided. Agent-authored originals can extend it; no downloaded code is automatically trusted.

Generate representative stills and transition frames before encoding. Inspect them against the bundled lookbook. Fix clipping, dense text, bogus phrase endings, abrupt unrelated state changes and bad crops. If a quote cannot fit at readable size, split the beat or use a faithful shorter excerpt, not a tiny paragraph.

## 6. Render and sound

Render only after still review. Preserve source speech order/speed; original normalized narration remains foreground. Quiet original/approved sounds accompany actual visible events. Editorial has no background-music bed. Use settled ending, stable logo and true source clock.

The runner writes `visuals.mp4`, `voice.wav`, `mix.wav`, `placements.jsonl`, `placement-qc.json`, `final.mp4`, `captions.srt`, `poster.jpg` and `job.json` in the selected job directory. These are working artifacts; don't hand the user every intermediate.

## 7. Verify actual encoded output

Run QC. Decode the whole MP4, verify full frame count/FPS/dimensions and audio stream, scan unintended all-black frames, inspect all-frame placement and source alignment/loudness. Deliberately static graphic cards/end holds are not failed source playback; undeclared gaps/stale decoder reuse are failures.

Use image/video tools to inspect decoded first/middle/end frames, all scene boundaries, maximum crop excursions, longest words and branding/background changes. Review motion and listen where tools permit. Machine geometry cannot certify a face was protected if its supplied box was wrong. Record exactly what was viewed/heard and any limitation.

Compare the final composition, hierarchy, continuity and speech focus to the actual references. Re-render to a **new revision** until accepted by the QC/review contract. Never claim all perceptual aspects checked when only the exit code was seen.

## 8. Deliver / retain reproducibility

Present the final MP4; supporting poster/SRT if requested. Preserve the new plan, input hash, transcript, authored source and QC/review separately from disposable intermediates. Disclose upscaling/assumptions where relevant.

If repository delivery is authorized and available, use a distinct `edits/<slug>-vN/` folder in the existing repository. Reinspect branch/remote/unrelated changes, stage/upload only intended files, never expose credentials/force-push/create a new repository, and verify public folder/commit before claiming success. A future ID's missing auth is not a blocker to local video delivery.

## Required end-of-job review record

Use `templates/review.template.json` and fill only real observations: input/plan/output hashes, exact decoded timestamps inspected, timing/quote correctness, framing/face/hands checks, logo envelope/background motion, transition readability, audio verification method, remaining risks and accept/revise decision. The machine report stays separate and does not falsely toggle a human/vision review to complete.
