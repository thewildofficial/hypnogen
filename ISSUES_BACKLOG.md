# GitHub Issues Backlog

This file tracks issue drafts ready to open on GitHub.
Source references are in `.sisyphus/plans/` and `.sisyphus/notepads/`.

## 1) Run full TTS benchmark matrix and publish evidence pack

- Suggested labels: `benchmarks`, `coreml`, `performance`
- Scope:
  - Run `hypnogen/benchmarks/bench_tts_only.py` for `pytorch` and `coreml` compute-unit variants.
  - Save benchmark JSONs to `.sisyphus/benchmarks/`.
  - Refresh `.sisyphus/evidence/tts-accel-report.md` with measured deltas.
- Done when:
  - Artifacts exist and are linked in report.
  - Report clearly states winner per machine and run date.

## 2) Stabilize and verify macOS UI test execution

- Suggested labels: `macos`, `tests`, `ui`
- Scope:
  - Run `xcodebuild test -project macos/Hypnogen.xcodeproj -scheme Hypnogen -destination 'platform=macOS'`.
  - Fix remaining runtime assertion failures (if any) and preserve dark-only checks.
- Done when:
  - Test suite passes in a non-interactive automation run.
  - Failures and follow-up risks are documented if any tests are intentionally skipped.

## 3) Decide default local TTS runtime path for macOS packaging

- Suggested labels: `architecture`, `macos`, `coreml`
- Scope:
  - Compare Python `coremltools` path vs Swift-native decoder benchmark outputs.
  - Decide default runtime path and fallback behavior.
  - Document decision in `ROADMAP.md` and `.sisyphus/notepads/.../decisions.md`.
- Done when:
  - Default path is codified and testable.
  - Decision record cites benchmark artifacts.

## 4) Normalize completion reporting across .sisyphus docs

- Suggested labels: `docs`, `process`
- Scope:
  - Reconcile conflicting completion summaries in:
    - `.sisyphus/notepads/macos-ui-coreml-tts-accel/COMPLETION_STATUS.md`
    - `.sisyphus/notepads/macos-ui-coreml-tts-accel/FINAL_COMPLETION_REPORT.md`
    - `.sisyphus/notepads/macos-ui-coreml-tts-accel/issues.md`
  - Keep one canonical status snapshot and mark superseded reports.
- Done when:
  - Status counts and blockers are internally consistent.
  - Contributors can identify next tasks without ambiguity.
