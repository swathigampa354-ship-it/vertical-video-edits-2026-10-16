# Troubleshooting quick reference

Read the full [error log](../ERRORS_AND_SOLUTIONS.md) before retrying a failure.

| Symptom | Evidence / next safe action | Do not assume |
|---|---|---|
| `pdftotext: command not found` | Original PDF is retained. Use an authorized installed PDF parser; historic PyMuPDF extraction worked. | That Poppler is installed or a superficial page-count description is authoritative. |
| YouTube `Sign in to confirm you’re not a bot` | Use the supplied original MP4 / reachable file host. Previous yt-dlp and Browserless normal playback were blocked. | That transcripts or HTTP 200 mean playable footage, or a new API key bypasses the requirement. |
| Browserless screenshot works but video time stays 0 | Authentication proof and target-page playability are different checks. Read the saved sanitized report. | That a successful account test proves YouTube download access. |
| Filebin 200 + `text/html` | Keep a single Requests session through its normal warning/proceed flow, then check `video/mp4` and `ftyp`. | That an HTML warning saved as `.mp4` is video. |
| Faster Whisper `metadata_errors` TypeError | Load mono 16kHz float32 samples with SoundFile and pass the NumPy array. | A precise upstream version cause; no historic dependency lock was retained. |
| `ModuleNotFoundError` in restored environment | Read the observed environment and declared dependencies; install only when authorized for actual rendering. | Package/model/cache persistence between sessions. |
| Missing V2/V3 intermediate WAV/MP4 | Regenerate only for an approved reproduction. Final exports/source/input remain. | That missing cache means the delivered video never existed. |
| “not a git repository” | Inspect the real workspace and documented remote. Prior deliveries used REST. Metadata-only attachment was done during this archive. | Permission to reset or overwrite files, or to create another GitHub repository. |
| Archive validator fails on link | Check actual filename/case/path and `FILE_CHANGE_LOG.md`; fix only archive-owned references. | That moving unrelated source files is an acceptable link fix. |
| Secret-like value detected | Stop staging/pushing; remove/redact the value, rerun scan, rotate exposed credentials. | That `.gitignore` alone removes secrets already staged/committed. |
| Push authentication fails | Report sanitized status, use current secure authentication if authorized, keep validated local files. | That a local commit equals a successful push, or that old chat tokens are safe credentials to reuse indefinitely. |
| Remote advanced / non-fast-forward | Stop and inspect both sides; reconcile without losing either side. | Authorization for force push or hard reset. |
| Flick starter has no rendered composition | It intentionally starts with `Root.tsx` returning `null`; an agent must write/register approved scenes. | That installing Flick is itself a completed video. |
| A claim of “1,000 videos” | Distinguish repeatable scene renders from a proven end-to-end thousand-reel pipeline. | That the historical read-only audit benchmarked Flick or mass production. |

## Reproduction without losing evidence

1. Load the [source snapshot README](source-snapshot/README.md).
2. Choose a separate authorized working copy/output location; do not overwrite evidence.
3. Check Python imports, font files, raw video, transcript, FFmpeg binary and writable cache paths.
4. Skip retranscription unless correcting the saved transcript intentionally.
5. Inspect stills before full rendering; preserve 9:16 and voice timing.
6. Decode the entire final file and check actual audio measurements before reporting success.

This document does not authorize installing anything, opening services, rendering, or accessing accounts by itself.
