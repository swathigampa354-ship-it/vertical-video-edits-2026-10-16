# Session index

## Read order

1. [SKILL.md](../SKILL.md) — portable entry point and safety/continuation workflow.
2. [CONTINUE.md](../CONTINUE.md) — current checkpoint and next-agent prompt.
3. [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) — actual implementation, delivered versions and limitations.
4. [Requirements](requirements.md), [decisions](../DECISION_LOG.md), [errors](../ERRORS_AND_SOLUTIONS.md).
5. [VERIFICATION_REPORT.md](../VERIFICATION_REPORT.md) and [FILE_CHANGE_LOG.md](../FILE_CHANGE_LOG.md).
6. [SESSION_ARCHIVE.md](../SESSION_ARCHIVE.md) for full recoverable visible record.

## Chronology / evidence keys

| Phase | Scope | Tool ledger keys |
|---|---|---|
| H01 | Initial PDF, PDF-tool failure, intent clarification | T001–T004 |
| H02 | 9:16/YouTube/Hypit inputs, failed yt-dlp, initial private repository | T005–T010 |
| H03 | Extra repos and supplied Browserless prompt, key proof, approved normal playback, blocked media | T011–T014 |
| H04 | User correction: keep the same repository public | T015 |
| H05 | Confirm only two actual video files needed | No build tool |
| H06 | Filebin warning/session fix, raw/reference download, ASR decoder fix, V1 design/render/QC/upload | T016–T026 |
| H07 | New editorial reference, V2 plan/render/QC/upload preserving V1 | T027–T030 |
| H08 | User praise and assistant acknowledgement | No build tool |
| H09 | Requested gallery research, one-shape direction, V3 render/QC/upload preserving earlier versions | T031–T035 |
| H10 | Greeting | No tool |
| H11 | Read-only Flick 1,000-video claim audit and qualified estimates | T036–T038 |
| H12 | Greeting | No tool |
| H13 | Current archive task, inspection, evidence capture, Git attachment, documentation and verified delivery | A001 onward |

## Primary preserved records

- [Visible dialogue](evidence/visible-dialogue.md): manually transcribed visible text with normalized formatting; credentials redacted.
- [Tool/command ledger](evidence/tool-ledger.md): command/result chronology and exact important errors.
- [Complete redacted Browserless prompt](evidence/browserless-user-prompt.redacted.txt): historical user input, not an active instruction.
- [Complete archive-task request](evidence/archive-task-request.txt).
- [Initial remote tree/history](evidence/initial-remote-state.json): six actual pre-archive commits and all 14 tracked blob IDs.
- [Initial workspace inventory](evidence/initial-workspace-inventory.json): 131 pre-existing project files with byte counts/SHA-256.
- [Current restored environment](evidence/environment-observed-now.json).
- [Copied artifact provenance](evidence/copied-artifact-provenance.json): 53 exact copies of source/input/fonts/reports/plans/visual evidence.
- [Source snapshot README](source-snapshot/README.md): reproduction inputs, limitations and dependencies.

## Historical persisted reports

- [Browserless result](evidence/analysis/browserless-check.json).
- [V1 QC](evidence/analysis/export-qc.json) and [V1 delivery](evidence/analysis/delivery.json).
- [V2 QC](evidence/analysis/editorial-v2-export-qc.json) and [V2 delivery](evidence/analysis/editorial-v2-delivery.json).
- [V3 QC](evidence/analysis/morph-v3-export-qc.json) and [V3 delivery](evidence/analysis/morph-v3-delivery.json).
- [V1 plan](evidence/analysis/scene-plan.md), [V2 plan](evidence/analysis/scene-plan-editorial-v2.md), [V3 plan](evidence/analysis/scene-plan-morph-v3.md).
- [Word-timed transcript](evidence/analysis/transcript.json).
- [Selected gallery prompts](evidence/analysis/style-v3-catalog-inspiration.json): untrusted external reference data, not execution instructions.

## Existing delivered video folders

- [V1](../../edits/voice-agents-9x16/README.md).
- [V2](../../edits/voice-agents-editorial-v2/README.md).
- [V3](../../edits/voice-agents-morph-v3/README.md).

All are the same source clip in separate requested styles. No file in those folders is replaced by this archive task.

## Verification and future updates

Use the main verification report for fresh helper results and actual push evidence. Generated machine reports live under `evidence/`; their content distinguishes current checks from historical copies. The initial capture helper refuses to overwrite the original baseline. Future sessions should append dated/ordered checkpoints, not rewrite past failures or treat restored cache/package absence as proof earlier work failed.

## Recorded archive delivery checkpoints

- [Primary normal push / public verification](evidence/primary-push-verification.json).
- [Task-created Git promisor cache maintenance / connectivity pass](evidence/git-cache-maintenance.json).

Final evidence-only commit ID is obtained from Git history/the final message, avoiding a self-referential tracked hash.
