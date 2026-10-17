# Reproduce the tests

Install/check core requirements first; commands run from any CWD with explicit paths. Workdirs must be new. Generated videos/WAVs stay in disposable workdirs, not inside the transferable templates.

## Original editorial fixture

```bash
python "$SKILL/scripts/replay_baseline.py" --style v2 --workdir "$FRESH_V2_TEST" --reference "$APPROVED_V2_MP4"
```

The reference must match `templates/baseline-manifest.json`. If a local reference is unavailable, retrieve its public URL only when permitted and verify its hash. The bundle includes the small original raw/transcript/fonts needed to recreate the fixture; it does not duplicate all three full final MP4s.

## Original latest morph fixture

```bash
python "$SKILL/scripts/replay_baseline.py" --style v3 --workdir "$FRESH_V3_TEST" --reference "$APPROVED_V3_MP4"
```

`--style v1` is implemented from preserved source but was not freshly rendered in the skill-creation test. Do not label it tested merely because it is an option.

## Controlled different-aspect/duration fixture

```bash
python "$SKILL/tests/test_workflow.py" --workdir "$FRESH_ADAPTATION_TEST" --phase prepare
# Inspect source-contact and stills-contact with image tools.
python "$SKILL/tests/test_workflow.py" --workdir "$FRESH_ADAPTATION_TEST" --phase render
```

This derives a portrait excerpt from the same original source, not a truly unrelated camera/video. It uses actual source word timings rebased to that excerpt. The explicit TEST mark is a synthetic fixture, never real user branding.

`--phase negative` runs the targeted source/transcript mismatch, boundary/collision, late-motion, phrase endpoint, constant-logo and contrast checks on an already prepared workdir. Actual results are in [evidence/negative-tests.json](evidence/negative-tests.json).

## Executable bundled example

```bash
python "$SKILL/scripts/edit.py" validate-plan --input "$SKILL/examples/portrait/source.mp4" --plan "$SKILL/examples/portrait/plan.json" --workdir "$NEW_JOB"
python "$SKILL/scripts/edit.py" stills --input "$SKILL/examples/portrait/source.mp4" --plan "$SKILL/examples/portrait/plan.json" --workdir "$NEW_JOB"
# Inspect, then:
python "$SKILL/scripts/edit.py" render --input "$SKILL/examples/portrait/source.mp4" --plan "$SKILL/examples/portrait/plan.json" --workdir "$NEW_JOB"
python "$SKILL/scripts/edit.py" qc --workdir "$NEW_JOB"
```

For new user footage, **the agent must author a new inspected, source-bound transcript/plan**, not run this example unchanged. The two fingerprints deliberately reject unrelated assets.

## Package validation / ZIP

```bash
python "$SKILL/scripts/build_bundle.py"
python "$SKILL/scripts/validate_package.py" --verify-zip
```

The ZIP excludes itself, temporary/cache/environment files and project-only initial-state/delivery/validator records. `BUILD_MANIFEST.json` binds its other distribution members. Extract into another path, run the validator there, then exercise the example; this checks actual path independence rather than assuming the old workspace exists.

`--check-existing-workspace` is only for the original skill-creation workspace with its saved initial-state record. A fresh user/clone intentionally need not have those original untracked files. Do not use that flag to claim a fresh environment has the same terminal/model caches.

## What PASS means

Read [TEST_REPORT.md](../TEST_REPORT.md) for precise evidence/limitations. Pixel/PCM identity on exact original fixtures is strong regression evidence. It is not a benchmark of arbitrary new creative stories, model IDs, ASR languages, HDR/VFR conversion, complex brand tracking or perceptual listening. Keep a real post-encode review separate from the machine report.
