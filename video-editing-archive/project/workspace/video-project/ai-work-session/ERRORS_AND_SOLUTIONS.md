# Errors, failed attempts, fixes, and remaining limitations

## E01 — `pdftotext` absent

**Original command**

```bash
ls -l /home/user/uploads && file '/home/user/uploads/LUMIAI REELS COMMENTS.pdf' && pdftotext -layout '/home/user/uploads/LUMIAI REELS COMMENTS.pdf' -
```

**Observed error**

```text
/bin/bash: line 1: pdftotext: command not found
exit_code: 127
```

**Confirmed workaround:** install/import PyMuPDF, iterate `pymupdf.open(...)`, use `page.get_text()` and render page PNGs. The tool output contained pages 1–15; 15 page images remain in the workspace. The initial `file` description reported “8 page(s)”; that conflicting superficial description must not override the actual extraction record. The original PDF is preserved for future independent parsing. PyMuPDF is absent in the restored environment; do not pretend it remains installed.

## E02 — YouTube normal media access blocked

**Commands attempted**

```bash
python -m yt_dlp --no-playlist --skip-download --dump-single-json 'https://www.youtube.com/watch?v=FcvFNbcCL98' > /home/user/video-project/analysis/raw-info.json
python -m yt_dlp --js-runtimes node --remote-components ejs:github --no-playlist --skip-download --dump-single-json 'https://www.youtube.com/watch?v=Xv_gLzEJY7Q' > /home/user/video-project/analysis/style-info.json
```

**Observed messages**

```text
WARNING: [youtube] No supported JavaScript runtime could be found. Only deno is enabled by default; to use another runtime add --js-runtimes RUNTIME[:PATH] ...
WARNING: [youtube] No title found in player responses; falling back to title from initial data. Other metadata may also be missing
ERROR: [youtube] FcvFNbcCL98: Sign in to confirm you’re not a bot. Use --cookies-from-browser or --cookies for the authentication.
ERROR: [youtube] Xv_gLzEJY7Q: Sign in to confirm you’re not a bot. Use --cookies-from-browser or --cookies for the authentication.
```

These are the relevant exact error strings; explanatory documentation URLs/wrapped boilerplate were present in the original tool output. The second command still emitted the runtime warning. The actual reason the runtime option did not take effect was not investigated; do not invent a fix. `raw-info.json` and `style-info.json` survived as 5-byte failed artifacts, not valid media metadata.

**Confirmed workaround:** use the user's actual MP4 files delivered via Filebin. Reading a YouTube page/transcript did not prove playable media access. Do not retry the same blocked path indefinitely, request private browser cookies, or assume another unrelated API key removes the restriction.

## E03 — Browserless authentication worked, YouTube playback did not

**Read-only proof:** screenshot request to the supplied shared-cloud host returned HTTP 200, exit code 0, `image/png`, PNG signature verified, 88,482 bytes. The newly created test image was deleted; no pre-existing file was deleted.

**Approved follow-up:** normal `/function` browser visits to the two supplied YouTube URLs returned HTTP 200 pages but:

```json
{"playabilityStatus":"LOGIN_REQUIRED","reason":"Sign in to confirm you’re not a bot","availableFormatCount":0}
```

Both players had current time 0, ready state 0, and width/height 0. `mediaRetrieved` was false. [The sanitized report](references/evidence/analysis/browserless-check.json) preserves the actual result. No request/session identifier was returned. REST auto-close behavior was documented; there was no persistent session or separate manual close proof.

**Not a fix:** proving an account key works is not evidence of media playback. No proxies, paid CAPTCHA solving, alternate account sign-in, or additional plan features were used. The second unlabelled API key was never used.

## E04 — Filebin HTTP 200 contained HTML, not video

**First result**

```text
raw HTTP 200 content-type text/html; charset=utf-8 bytes 5431
Not MP4.
```

The response was a normal Filebin warning page. Inspection found a `verified` cookie and “Proceed to download” link. A fresh independent request repeated the warning; the solution was to retain the same session and continue normally.

**Working approach**

```python
s = requests.Session()
r = s.get(url, timeout=(15, 90))
if r.headers.get('content-type', '').startswith('text/html') and s.cookies.get('verified'):
    r = s.get(url, timeout=(15, 90), headers={'Cache-Control': 'no-cache'})
r.raise_for_status()
assert r.content[4:8] == b'ftyp'
```

Raw download then returned `video/mp4`, 1,101,889 bytes; the sports reference returned 4,317,118 bytes. The later editorial reference returned 27,117,601 bytes using the same pattern. No warning-page HTML was saved as a fake `.mp4`.

## E05 — Decoder incompatibility during transcription

**Observed traceback ending**

```text
File "/usr/local/lib/python3.13/site-packages/faster_whisper/transcribe.py", line 876, in transcribe
  audio = decode_audio(audio, sampling_rate=sampling_rate)
File "/usr/local/lib/python3.13/site-packages/faster_whisper/audio.py", line 46, in decode_audio
  with av.open(input_file, mode="r", metadata_errors="ignore") as container:
TypeError: open() got an unexpected keyword argument 'metadata_errors'
```

**Confirmed fix**

```python
import soundfile as sf
samples, rate = sf.read(audio, dtype='float32')
assert rate == 16000
segments, info = model.transcribe(samples, language='en', beam_size=5,
    word_timestamps=True, vad_filter=False, condition_on_previous_text=True)
```

The next run completed in approximately five seconds and produced five transcript segments. An unauthenticated Hugging Face rate-limit warning also appeared during model acquisition; it was not a fatal model-download error. Exact historical PyAV/Faster Whisper versions were not recorded, so do not identify a precise upstream regression beyond the observed API mismatch.

## E06 — Visual-layout problems fixed before final rendering

- V1: small `THE STARTUP QUESTION` label overlapped the oversized GO silhouette. Removed the redundant label.
- V1: made the destination globe move to the center and expand, and made product cards emerge from the same anchor rather than unrelated replacements. Increased motivated emphasis zoom and added an actual-time listener cutaway at 11.98–12.54 s.
- V2: long rotated audience words and footer needed safer margins. Reduced rotated text fit from 106 px/620 px extent to 100 px/500 px, moved it to x=912, and moved final footer y=1751 to y=1690.
- V3: increased small final audience labels from 18 px to 28 px fit; changed cursor exit keyframe to leave before the settled poster/ending.

These were design-review findings, not compiler/build failures. Final source snapshots and the visible edit records preserve the resolutions.

## E07 — Missing local Git metadata during archive inspection

```text
fatal: not a git repository (or any of the parent directories): .git
```

**Cause confirmed:** previous pushes were REST API object/ref operations; no local `.git` checkout had been created.

**Confirmed solution:** attach metadata and the index to the existing remote without a worktree checkout. After `git read-tree HEAD` (no `-u`), `git diff --name-status` was empty and pre-existing untracked paths remained. This was initialization of local tracking for the same repository, not creation of another GitHub repository.

## E08 — Packages, cache and raw terminal history did not survive restoration

Fresh checks found no `.bash_history`/`.zsh_history`, no cached `video-project*` intermediates, and several formerly installed packages absent. Source files, raw input, final media and reports remain.

**Resolution for this task:** preserve exact source, relevant inputs, available tool-log text and reports; document dependency/cache gaps. Do not run package installers or new renders just to make the archive look complete. Reproduction prerequisites are listed separately and are not a tested lockfile.

## E09 — Claims not verified / remaining risks

- No stock Flick installation, complete reel assembly test, Remotion benchmark, 1,000-output batch, or automated posting was run. A scene render is not the same as 1,000 complete unique reels.
- Human proofreading of every ASR word was not recorded. The YouTube transcript included “very early on,” while the saved Whisper transcript omits “very.” Do not silently alter historical captions or quoted frames; an authorized correction should align against the raw audio.
- Some keyword text/headlines intentionally paraphrase/condense narration. Only automatically transcribed blocks are presented as speech text; reviewers should not assume every editorial title is a direct quote.
- Full reference videos were locally available but are not copied to the public archive; Filebin links expire. Style plans/contact sheets remain. The V3 reference-video cache itself is already absent.
- Local `analysis/repository.json` says `private: true` because it records creation-time state; current public visibility is independently verified. Never use that stale file to change visibility back.
- Credential rotation status is unknown. All credentials shared in chat are treated as exposed and omitted, including from copied commands.
- No exact original dependency lock, raw platform transcript export, complete terminal-history database, source Git commits for the original Python renderers, or persistent raw background-process logs were recovered.

## E10 — Non-fatal H.264 seek warnings during reference sampling

The successful Filebin/contact-sheet command emitted four `[h264 ...] mmco: unref short failure` warnings while seeking in a reference stream. They did not terminate acquisition or contact-sheet creation. A seek/reference-frame interaction is a possible explanation, not an investigated root cause. Do not reclassify this as a failed final encode: all three historical FFmpeg export decodes passed, and fresh OpenCV full-video decoding of the delivered files also passed during the archive task.

## E11 — Initial staged whitespace check flagged original font-license spaces

`git diff --cached --check` returned exit 2 for line 21 of five copied OFL license texts (Geist, Geist Mono, Instrument Serif, Inter and the Barlow-family OFL). The original line ends with a space after `embedded,`. This was not a source-code or archive-content error. To retain byte-exact license evidence, added **archive-local** `.gitattributes` with `references/source-snapshot/assets/fonts/*OFL.txt -whitespace`. This does not exempt authored documentation/code or alter root attributes. Re-running the staged check passed; provenance hashes continue to match the original license bytes.
