# Motion-aware source, logo and overlay placement

## Evidence boundary

**No added brand logo was present in the original V1/V2/V3.** Their labels are editorial text, not a supplied brand mark. There was no documented logo tracking, camera stabilization or moving-background visibility experiment. Existing source lettering was not replaced. A style-reference Cartesia logo was explicitly excluded.

Rules below codify safe future behavior. Geometry/background-switch behavior was tested with a synthetic `TEST` mark only. That is not evidence that any real logo or object-tracking solution has been approved.

## Coordinate conventions

Output default is1080×1920. Layer/source ROI rectangles are **[x,y,width,height]**, normalized0..1. Safe bounds are **[left,top,right,bottom]**. Do not confuse these forms.

- New-production critical default: `[.07,.08,.88,.86]`, i.e. x75.6..950.4, y153.6..1651.2 at1080×1920.
- Historical canvas comparison: `[.05,.05,.95,.94]`. Only use it deliberately; it is not a modern platform guarantee.
- Actual publishing app UI, native ad safe zones, subtitles and user-provided prohibited regions take precedence. The defaults are conservative layout policy, not a claim of current Instagram/TikTok specification.

## Source framing procedure

1. Inspect decoded orientation and aspect, not just encoded width/height. Inspect each shot and source motion extrema.
2. Mark the essential subjects: face/hair/chin/mouth, hands where meaningful, second speaker, demonstration object and embedded text/attribution.
3. Fit proportionally with `contain` by default. Deliberate black bars are preferable to stretched heads or amputated context.
4. For `cover`, select an inspected normalized ROI in source coordinates; use crop keyframes when the subject changes position. Smooth between deliberate positions; do not jitter a crop using noisy face detections.
5. Never reuse the old wide→split cut4.9049 s on a new file. Source boundaries and important regions are new data.
6. No global stabilization was used in the successful source. Handheld material may need stabilization only after a real motion analysis and crop-budget check; do not falsely call a fixed panel “stabilized.”

The portable renderer supports source ROI and `roi_keyframes`; object tracking, homography, optical flow, stabilization, HDR mapping and VFR conversion are not automatically solved by this skill. If needed, implement/test the extra source-specific step explicitly. Keep original speech/audio time aligned.

## Logo decision procedure

- No logo requested/supplied: omit it. Do not ask for optional branding or invent a company.
- Required logo missing: ask only for the asset/approved variant.
- Read actual RGBA bounds, padding, intrinsic ratio, resolution and brand clearspace. Preserve aspect; do not crop brand-required clearspace or use an unlicensed reference watermark.
- Prefer top-left or top-right only after checking every shot. There is no universally correct corner.
- Choose approximate height48–80 px at1080 wide as a starting range, width usually≤22% (long wordmarks may need up to30%). Judge **visible mark/letter size**, not a padded PNG box, at phone scale. Resize/reflow if illegible; ask for a better-resolution variant if necessary. These are starting rules, not observed settings from the logo-free baseline.
- Use an approved solid light/dark plate or alternate logo variant to maintain contrast on changing backgrounds. Never auto-recolour the logo or introduce a frame-to-frame colour switch that flickers.
- Keep visible graphics at least roughly3:1 contrast against their backing; aim4.5:1 for small critical lettering. The code only rejects transparency/obvious absence of contrasting pixels; manual examination of the whole mark remains mandatory.

## Correct compositing order

1. Select/crop/scale/position the actual source.
2. Draw scene graphics and animation.
3. Apply connected scene transitions/camera movement.
4. Composite the screen-anchored logo and backing **last**.
5. Check its full envelope, including the helper's8 px backing expansion and any animation overshoot.

This prevents a logo being cut by source masks, drifting with a footage zoom or fading out with a scene wipe. A logo intentionally tracked to a moving object is a different workflow; the baseline and helper do not prove that tracking.

## Collision / visibility checks

Create edit-time protected regions for faces/mouths, hands, subtitles, important graphics, embedded attribution and prohibited platform UI. Use timed/keyframed regions when those objects move. Review first/last frame, each cut±one frame, every crop/animation extremum and every background/transition change.

The helper logs every frame in `placements.jsonl`, checks text canvas/safe bounds and logo collisions with visible critical text/protected rectangles, and records failures in `placement-qc.json`. Rectangles supplied by the agent are not ground-truth face detections. **Incorrect or incomplete protected regions can make a machine PASS misleading.** Actual decoded-frame inspection is required.

A required logo must be scheduled throughout the film. It should remain fully visible and not be obscured by masks, fullscreen effects, a cursor, outro or overlays. If no candidate is safe, redesign the layout; do not silently remove the mark, shrink it into illegibility or cover a face.

## Tested limits

Tested: static screen mark stays identical through all90 pre-encode frames of a three-second black→cream→orange edit; late animated boundary crossing, protected-region/text overlap and white-on-white absence of contrast are detected by targeted tests. The placeholder is explicitly a test asset, not final branding.

Not tested: real brand guide approval, complex occlusion, real-world moving-object logo tracking, all platform UI versions or perceptual legibility of arbitrary logos. State these limits rather than implying the synthetic test certified them.
