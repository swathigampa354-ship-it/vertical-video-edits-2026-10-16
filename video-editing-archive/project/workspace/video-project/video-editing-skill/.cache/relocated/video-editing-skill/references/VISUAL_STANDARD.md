# Visual standard: actual evidence → adaptable rules

## Which successful result?

Three finished versions exist. The user explicitly said “That's F* awesome” after **V2**. **V3** is the latest completed video. This bundle preserves both rather than guessing that one layout must apply to every future prompt. Default editorial-v2; explicit latest/morph selects morph-v3. Sports-v1 is a separate alternative. Original final-file identities are in [baseline-manifest.json](../templates/baseline-manifest.json).

The source was a 640×360, approximately 29.97 fps, 20.735 s interview clip. Its wide shot becomes a split view at **4.9049 s**. The original audio was used almost completely; no documented best-excerpt ranking, object tracking, stabilization, added brand logo or watermark-placement decision existed. New rules must not be presented as recovered historical facts.

## Editorial V2 measured anatomy (1080×1920 canvas)

Palette: orange `(251,73,8)`; black `(3,3,3)`; off-white `(255,252,244)`; cream `(237,234,230)`; ink `(11,12,12)`; gray `(153,149,146)`. These are pre-encode design values, not a promise that every decoder/JPEG sample reports identical RGB.

Typography: Instrument Serif regular/italic; variable Inter with axes optical size 32, weight 800 for bold copy. Two families, distinct roles. Label tracking about 3–7 px; short high-contrast metadata only. Do not use a thin serif for long dense proof text.

| Recovered section | Actual placement / typography | Why it worked and how to adapt |
|---|---|---|
| Opening, 0–2.98 s | THE STARTUP center (540,239), 59 px italic; PLAYBOOK center (540,369), max157 px / max920 px width; Going Global center (540,514), 132 px italic orange | Clear 3-level hierarchy and negative space. Replace the topic, not the hierarchy. No invented company/speaker identity. |
| Source strip | x0,y697,w1080,h608; source-proportional contain, very small zoom `1+.008*min(t,2.98)` | Keeps both real people and context. A portrait source cannot be forced into this wide strip; redesign its window. |
| Captions | Typically center y1492–1495, 56 px serif, max900 px width; product panel y1567,52 px,max870 | Stable full-line slots revealed by word time. Important speech remains readable without dominating the film. |
| Orange Years card, 2.98–4.905 s | Years 330 px italic center(540,823); supporting phrase 78–91 px; small MANY / THE LONG WAY labels | One dominant word gives contrast/rhythm. The old statistic-free YEARS metaphor is only relevant to the old speech. |
| Effort interview, 4.905–7.98 s | Going global y313/103 px; takes effort y431/116 px; source strip y686,1080×608 | The actual source shot change motivated the return. New shot boundaries need new times/framing. |
| Cream quote, 7.98–12.54 s | Left85; first line center-y330; Inter88; leading105; eight planned rows; circle center(540,1530),diam520 | Heavy quote contrasts with fine titles; actual word timing progressively builds proof while the live original insert sustains presence. Rewrap by new words, not the old `[3,2,2,3,2,1,3,4]` row counts. |
| Paper treatment | Grid every34 px, major170 px, seeded noise σ.65; lines approximately205/201/199, major191/187/185 | Subtle texture; not a dark graph that competes with type. The portable starter uses a simpler light grid; exact original treatment remains in the baseline template. |
| Product composition, 12.54–15.52 s | Orange ground, black rounded panels x60..1020; top127,h687,r40; lower y875..1695; source at60,926,960×540 | A concept graphic above actual footage explains the words. It is not a genuine product screenshot. Only use a comparable metaphor when the new speech warrants it. |
| Audience section, 15.52–18.66 s | Source strip y372; caption y1070; paper card x84..888,y≈1184,h516,r35; custom icon; tall word x912,y1168; font≤100 with500 px fit | Each real stakeholder word changes the icon/card at its own time. The side word was moved inward from x944 for canvas safety. It was NOT validated against every platform's UI rail. |
| Payoff, 18.66–21.37 s | Circle center(540,597),diam526; Voice264px y1102; Agents278px y1352; small footer47px y1690 | A short, legible resolution. Footer originally y1751 was moved up. For current platform-safe output, relocate decorative elements rather than claiming those historical pixels are universally safe. |

Original circle_video fitted a 16:9 source strip into a circular black backing; black letterboxing was deliberate. **The new starter uses the actual source aspect**, not a hardcoded `d*9/16` height. Never warp a portrait or cut off a face to mimic the old shape.

Original source grade: `(pixel-5)*1.015+5`, clipped to 0..255, a restrained near-original response. It is not a universal grading prescription. Preserve already-correct colour; evaluate source/HDR first. Original animation uses cubic ease-out, ~65–70 ms word reveal, ~140 ms connected wipes/crossfades, subtle 3–20 px text/card movement. No sports shake.

Original V2 waveform was a **decorative sine-based graphic**, not a measured live product/audio visualization. Do not label it a real dashboard or actual performance data. V3 used the source speech envelope.

## V3 morph profile

See [lookbook](images/v3-lookbook.jpg) and exact `render_morph_v3.original.py` / audio companion. Warm paper `(242,241,237)`, ink `(15,16,20)`, cobalt `(66,70,245)`; Geist and Geist Mono. New graphics 60 fps; source remains native ~29.97 fps sampling.

Same object changes width/height/center/radius/fill through analytic critically damped responses: interview → waiting timeline → globe → effort slider → EARLY toggle → priority player → market path → audience network → voice capsule → large blue payoff. State changes are semantic, cursor-driven and connected; not arbitrary slide replacements. `critical(t)=1-(1+ωt)exp(-ωt)` with ω≈17.5, final expansion≈15. Independent content enter/exit avoids ghosted duplicate labels.

For new speech, replace the state list, headlines, click/drag path and audio events with a new meaning-driven graph. Derive actual source frame count; never retain old `619`, `20.665`, 21.37 s or old timestamps. Use the original as code/reference material, not a generic renderer for unrelated footage. Extend the portable Film class or author a new reviewed job renderer retaining source/overlay/QC contracts.

V3 fixes worth retaining: final audience footer labels increased18→28 px; cursor leaves before the settled poster; one useful end hold; no glows/particles/template clutter. No fake product metrics were introduced.

## V1 sports alternative

See [lookbook](images/v1-lookbook.jpg) and `render_v1.original.py` / audio companion. Barlow Condensed Black Italic/SemiBold, Barlow Medium; red→lime, motivated punch-ins, controlled low-intensity flashes and original concept graphics. The real-time listener cutaway at11.98–12.54 s matched a pause; it was not a reordered quote. V1 removed a redundant opening label that collided with GO. Do not carry its shake/flashes/beat into the editorial preset.

## Quality rubric for any new footage

Fail/revise if any applies:

- The edit is only subtitles on a fixed clip, with no semantic graphics or purposeful hierarchy.
- It reuses YEARS/product/governments/voice agents on unrelated speech, or fabricates claims/branding.
- A full paragraph flashes unreadably or caption width recenters on every word.
- Graphic motion obscures a face/mouth, strains masks, stretches images, or hides a logo.
- Text/circle/card positions copied literally instead of reflowing for the new source and safe zones.
- A transition randomly replaces the scene without story continuity, or every word gets a noisy sound.
- Source detail/upscale, FPS interpolation, native logo tracking or a full perceptual review is claimed without evidence.

Passing means purposeful composition, stable legible type, speech-led events, original visual explanation, restrained coherent movement and sound, then a technically valid **inspected** export. This rubric is not a universal numeric score that certifies an agent's taste.
